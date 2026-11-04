from sentence_transformers import SentenceTransformer
from task1_read_tokenize import read_documents, DOCS_FOLDER, encoding

CHUNK_SIZE = 120
CHUNK_OVERLAP = 20
MODEL_NAME = "all-MiniLM-L6-v2"

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list:
    tokens = encoding.encode(text)

    step = chunk_size - overlap
    chunks = []

    for i in range(0, len(tokens), step):
        chunk_tokens = tokens[i:i + chunk_size]
        chunks.append(encoding.decode(chunk_tokens))

        if i + chunk_size >= len(tokens):
            break

    return chunks

def chunk_documents() -> list:
    documents = read_documents(DOCS_FOLDER)
    all_chunks = []

    for filename, text in documents.items():
        for i, chunk in enumerate(chunk_text(text)):
            all_chunks.append({
                "id": f"{filename}_chunk_{i}",
                "text": chunk,
                "source": filename,
            })

    return all_chunks

def load_model() -> SentenceTransformer:
    """Load the local embedding model (downloaded once, then cached)."""
    return SentenceTransformer(MODEL_NAME)

def main():
    chunks = chunk_documents()

    print(f"Chunk size: {CHUNK_SIZE} tokens | Overlap: {CHUNK_OVERLAP} tokens")
    print(f"Total chunks: {len(chunks)}")

    sources = sorted({c["source"] for c in chunks})
    for source in sources:
        count = sum(1 for c in chunks if c["source"] == source)
        print(f"  {source}: {count} chunks")

    sample = chunks[0]
    print("\n" + "=" * 60)

    print(f"Sample chunk  (id: {sample['id']})")
    print(f"Tokens in chunk: {len(encoding.encode(sample['text']))}")
    print("=" * 60)

    print(sample["text"])
    print("=" * 60)

    print(f"\nLoading embedding model: {MODEL_NAME} ...")
    model = load_model()

    texts = [c["text"] for c in chunks]
    embeddings = model.encode(texts)

    print(f"Embeddings created: {len(embeddings)}")
    print(f"Vector size: {len(embeddings[0])}")
    print(f"First 5 values of sample vector: {embeddings[0][:5]}")

if __name__ == "__main__":
    main()