"""
Task 3 - Store and search in ChromaDB
Creates a persistent ChromaDB database inside the project, saves every
chunk with its embedding and source filename, then asks a question and
displays the top 2 matching chunks with their cosine distances.
"""

from pathlib import Path
import chromadb

# Reuse chunking and the embedding model from Task 2
from task2_chunk_embed import chunk_documents, load_model

DB_FOLDER = Path(__file__).parent / "chroma_db"   # stays inside the project
COLLECTION_NAME = "company_documents"
TOP_K = 2


def get_collection():
    """Open (or create) the persistent ChromaDB collection using cosine distance."""
    client = chromadb.PersistentClient(path=str(DB_FOLDER))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # default would be L2 (euclidean)
    )


def build_database(collection, model):
    """Chunk the documents, embed them, and save everything in ChromaDB."""
    chunks = chunk_documents()
    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts).tolist()   # ChromaDB expects plain lists

    collection.upsert(                           # upsert = no duplicates on re-run
        ids=[c["id"] for c in chunks],
        documents=texts,
        embeddings=embeddings,
        metadatas=[{"source": c["source"]} for c in chunks],
    )
    return len(chunks)


def search(collection, model, question: str, top_k: int = TOP_K) -> list:
    """Embed the question and return the top_k closest chunks."""
    question_embedding = model.encode([question]).tolist()

    results = collection.query(
        query_embeddings=question_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    # Chroma returns one list per question; we sent one question, so take [0]
    return [
        {"id": id_, "text": doc, "source": meta["source"], "distance": dist}
        for id_, doc, meta, dist in zip(
            results["ids"][0],
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]


def main():
    print("Loading embedding model ...")
    model = load_model()
    collection = get_collection()

    stored = build_database(collection, model)
    print(f"Chunks saved: {stored} | Total in collection: {collection.count()}")
    print(f"Database folder: {DB_FOLDER}\n")

    question = input("Ask a question: ").strip()
    if not question:
        question = "How many annual leave days do employees receive?"
        print(f"(No question entered, using: {question})")

    matches = search(collection, model, question)

    print(f"\nTop {TOP_K} chunks for: {question}")
    for rank, match in enumerate(matches, start=1):
        print("=" * 60)
        print(f"Rank {rank} | Cosine distance: {match['distance']:.4f}")
        print(f"Source: {match['source']} | Id: {match['id']}")
        print("-" * 60)
        print(match["text"])
    print("=" * 60)


if __name__ == "__main__":
    main()