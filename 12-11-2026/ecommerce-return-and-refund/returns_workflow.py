import asyncio
import json
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path
from openai import AsyncOpenAI
from agent_framework import (
    Agent,
    Executor,
    WorkflowBuilder,
    WorkflowContext,
    executor,
    handler,
    response_handler,
)
from agent_framework.openai import OpenAIChatClient


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


@dataclass
class ApprovalRequest:
    """Sent to the human manager when a request is escalated."""
    prompt: str
    r: dict

class ApprovalGateway(Executor):

    def __init__(self):
        super().__init__(id="approval_gateway")
        
    @handler
    async def review(
        self,
        r: dict,
        ctx: WorkflowContext[dict]
    ) -> None:
        condition = r["item_condition"].upper()

        # Auto-approve only when ALL policy conditions are satisfied
        auto_approved = (
            r["amount_inr"] < 25000                         # 1. below ₹25,000
            and r["days_since_delivery"] <= 30              # 2. within 30 days of delivery
            and r["invoice_available"]                      # 3. invoice available
            and (
                condition == "UNOPENED"                     # 4. unopened, or
                or (
                    condition == "DAMAGED"                  #    damaged with photos
                    and r["photo_evidence_available"]
                )
            )
            and r["previous_returns_90_days"] < 3           # 5. fewer than 3 returns in 90 days
            and "HIGH" not in r.get("risk", "").upper()     # 6. Risk Agent did not flag HIGH
        )

        # If any condition fails -> escalate for human review
        needs_approval = not auto_approved

        if not needs_approval:
            print("     Approval Gateway: AUTO_APPROVED")

            await ctx.send_message({
                **r,
                "needs_approval": False,
                "decision": "AUTO_APPROVED",
            })
            return

        print("     Approval Gateway: ESCALATED_FOR_HUMAN_REVIEW")

        # Pause the workflow and ask the human manager
        await ctx.request_info(
            ApprovalRequest(
                prompt=(
                    f"Return {r['request_id']} for {r['product']} "
                    f"(INR {r['amount_inr']}) needs manager approval."
                ),
                r={**r, "needs_approval": True},
            ),
            str,
        )

    @response_handler
    async def on_manager_decision(
        self,
        original_request: ApprovalRequest,
        answer: str,
        ctx: WorkflowContext[dict]
    ) -> None:
        decision = (
            "APPROVED_BY_MANAGER"
            if answer.strip().lower() == "approve"
            else "REJECTED_BY_MANAGER"
        )

        print(f"     Approval Gateway: {decision}")

        await ctx.send_message({
            **original_request.r,
            "decision": decision,
        })

def build_workflow(chat_client: OpenAIChatClient):
    eligibility_agent = Agent(
        client=chat_client,
        name="EligibilityAgent",
        instructions="You Review each return request against the company's return policy. Identify whether the request meets eligibility requirements and explain any exceptions. Respond in 2 sentences"
    )
    
    risk_agent = Agent(
        client=chat_client,
        name="RiskAgent",
        instructions="Analyze potential risks such as unusual return frequency, missing evidence, or high-value requests. Respond with exactly one word: LOW, MEDIUM, or HIGH."
    )
    
    customer_response_agent = Agent(
        client=chat_client,
        name="CustomerResponseAgent",
        instructions="Generate a customer-facing message based on the final workflow decision. The message must accurately communicate approval or rejection without claiming that a refund or replacement has already been completed."
    )
    
    @executor(id="eligibility_review")
    async def eligibility_review(
        r: dict,
        ctx: WorkflowContext[dict]    
    ):
        print("     Eligibility Agent: checking justification")
        
        result = await eligibility_agent.run(
            json.dumps(r)
        )
        
        await ctx.send_message({
            **r,
            "review": result.text.strip()
        })
        
    @executor(id="risk_review")
    async def risk_review(
        r: dict,
        ctx: WorkflowContext[dict]
    ):
        print("     Risk Agent: assessing risk")
        
        result = await risk_agent.run(
            json.dumps(r)
        )
        
        risk = result.text.strip().upper().strip(". ")
        
        print(f" RiskAgent: {risk}")

        await ctx.send_message({
            **r,
            "risk": risk
        })
        
    @executor(id="customer_response_agent")
    async def customer_response_review(
        r: dict,
        ctx: WorkflowContext[dict]
    ):
        print("     Customer Response Agent: Preparing decision record")
        
        result = await customer_response_agent.run(
            json.dumps(r)
        )
        
        await ctx.yield_output(
            f"{r['request_id']} -> "
            f"{r['decision']}\n"
            f"{result.text.strip()}"
        )
        
    gateway = ApprovalGateway()
    
    return (
        WorkflowBuilder(
            start_executor=eligibility_review
        )
        .add_edge(
            eligibility_review,
            risk_review
        )
        .add_edge(
            risk_review,
            gateway
        )
        .add_edge(
            gateway,
            customer_response_review
        )
        .build()
    )
        
    
async def run_one(workflow, r: dict) -> None:

    responses = None
    first_run = True

    while True:

        # Initial execution or resumed execution
        if first_run:
            stream = workflow.run(
                r,
                stream=True,
            )
            first_run = False
        else:
            stream = workflow.run(
                stream=True,
                responses=responses,
            )

        pending = {}
        completed = False

        async for event in stream:

            if event.type == "request_info":
                pending[event.request_id] = event.data

            elif event.type == "output":
                print(
                    "\nFINAL RECORD\n"
                    + str(event.data)
                )
                completed = True

        if completed:
            return

        if not pending:
            raise RuntimeError(
                "Workflow stopped without output "
                "or approval request"
            )

        responses = {}

        # Ask the human manager for a decision
        for request_id, request in pending.items():

            print("\n" + "=" * 50)
            print("MANAGER APPROVAL REQUIRED")
            print(request.prompt)

            print(
                "Eligibility review:",
                request.r["review"],
            )
            print(
                "Risk level:",
                request.r["risk"],
            )

            while True:

                answer = input(
                    "Type approve or reject: "
                ).strip().lower()

                if answer in {"approve", "reject"}:
                    break

                print("Please type approve or reject.")

            responses[request_id] = answer


async def main():
    api_key = os.environ[
        "AZURE_OPENAI_API_KEY"
    ]

    base_url = os.environ[
        "AZURE_OPENAI_BASE_URL"
    ]

    model = os.environ[
        "AZURE_OPENAI_MODEL"
    ]

    
    # Load returns requests
    with (
        BASE_DIR / "returns.json"
    ).open(encoding="utf-8") as file:

        returns = json.load(file)
        
    async with AsyncOpenAI(
        api_key=api_key,
        base_url=base_url
    ) as client:        
        chat_client = OpenAIChatClient(
            model=model,
            async_client=client,
        )
        
        for r in returns:
            print("\n" + "=" * 60)

            print(
                f"Request ID: {r['request_id']}, "
                f"Order ID: {r['order_id']}"
            )

            workflow = build_workflow(chat_client)
            
            await run_one(workflow, r)
    
    
if __name__ == "__main__":
    asyncio.run(main())
