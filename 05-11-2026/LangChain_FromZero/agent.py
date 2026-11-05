

import os
from dotenv import load_dotenv

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from guardrails import contains_pii
from tools import search_workshops, calculate_workshop_fee, find_cheapest_worshop, list_all_workshops, give_group_discount


# STEP 1: Load environment
load_dotenv()

# STEP 2: Create model
model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0
)

# STEP 3: Create agent
agent = create_agent(
    model=model,
    tools=[search_workshops, calculate_workshop_fee, list_all_workshops, find_cheapest_worshop, give_group_discount],
    system_prompt=(
        "You are a Workshop AI Assistant. "
        "Only answer questions about available workshops, "
        "training details and fees and coupons. "
        "Use the tools for workshop, coupon information and calculations. "
        "Never invent workshop names or prices or coupons. "
        "For unrelated questions, say: "
        "'I can only help with workshops and their fees and coupons.' "
        "If the user says yes after viewing a workshop, "
        "ask how many participants will attend. "
        "and after this ask if he has any coupons or not. if yes than ask for coupon"
        "Remember the selected workshop and coupon when calculating fees."
        "Also consider the coupon in the total"
    ),
    checkpointer=InMemorySaver()
)

# STEP 4: Run application
if __name__ == "__main__":

    thread_number = 1
    previous_count = 0

    print("LangChain Workshop AI Agent")
    print("Type /new for a new conversation")
    print("Type exit to quit")

    while True:
        question = input("\nYou: ").strip()

        if contains_pii(question):
            print("PII detected. Please remove personal contact details")
            break

        if question.lower() == "exit":
            break

        if question.lower() == "/new":
            thread_number += 1
            previous_count = 0
            print("New conversation started.")
            continue

        if not question:
            continue

        config = {
            "configurable": {
                "thread_id": f"workshop-{thread_number}"
            }
        }

        try:
            result = agent.invoke(
                {
                    "messages": [
                        {"role": "user", "content": question}
                    ]
                },
                config=config
            )

            messages = result["messages"]
            new_messages = messages[previous_count:]
            previous_count = len(messages)

            for message in new_messages:

                if isinstance(message, AIMessage):
                    for call in message.tool_calls:
                        print("[TOOL]:", call["name"])
                        print("Arguments:", call["args"])

                if isinstance(message, ToolMessage):
                    print("[TOOL RESULT]:", message.content)

            print("\nAgent:", messages[-1].content)

        except Exception as error:
            print("Error:", error)
