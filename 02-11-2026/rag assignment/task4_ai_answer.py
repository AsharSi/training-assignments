"""
Task 4 - Get an AI answer
Retrieves the top chunks from ChromaDB for a question, sends the question
and chunks to an AI model on OpenRouter, and prints the final answer.
The model is told to answer only from the provided context.
"""

import os
from openai import OpenAI

# Reuse the database and search from Task 3, and the model loader from Task 2
from task2_chunk_embed import load_model
from task3_store_search import get_collection, build_database, search

MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/free")  # any :free model works
NOT_FOUND = "I cannot find the answer in the provided documents."

SYSTEM_PROMPT = f"""You are a helpful assistant for Cedarline Systems employees.
Answer the question using ONLY the context provided.
Do not use outside knowledge and do not guess.
If the context does not contain the answer, reply exactly: "{NOT_FOUND}"
Keep the answer short and mention which document it came from."""


def get_client() -> OpenAI:
    """Create an OpenRouter client. The key is read from an environment variable."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY is not set. Add it in Run > Edit Configurations.")
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def build_context(matches: list) -> str:
    """Join the retrieved chunks into one block of text, labelled with their source."""
    return "\n\n".join(
        f"[Source: {m['source']}]\n{m['text']}" for m in matches
    )


def ask_ai(client: OpenAI, question: str, context: str) -> str:
    """Send the question plus context to the AI model and return its reply."""
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,   # factual answers, no creativity needed
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    answer = response.choices[0].message.content
    return (answer or "").strip() or "(The model returned an empty reply. Try again.)"


def main():
    client = get_client()

    print("Loading embedding model ...")
    model = load_model()
    collection = get_collection()

    if collection.count() == 0:      # database missing or empty: build it first
        print("Database is empty, building it ...")
        build_database(collection, model)
    print(f"Chunks in database: {collection.count()} | AI model: {MODEL}")

    while True:
        question = input("\nAsk a question (or press Enter to quit): ").strip()
        if not question:
            break

        matches = search(collection, model, question)

        print("\nRetrieved chunks:")
        for m in matches:
            print(f"  {m['id']}  (cosine distance: {m['distance']:.4f})")

        try:
            answer = ask_ai(client, question, build_context(matches))
        except Exception as error:   # e.g. rate limit or network problem
            print(f"\nAI request failed: {error}")
            continue

        print("\n" + "=" * 60)
        print(f"Question: {question}")
        print("-" * 60)
        print(f"Answer: {answer}")
        print("=" * 60)


if __name__ == "__main__":
    main()