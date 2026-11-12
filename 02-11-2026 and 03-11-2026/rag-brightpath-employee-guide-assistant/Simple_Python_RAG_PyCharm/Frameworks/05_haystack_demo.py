
from pathlib import Path

from haystack import Document, Pipeline
from haystack.components.preprocessors import DocumentSplitter
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.writers import DocumentWriter
from haystack.document_stores.in_memory import InMemoryDocumentStore

from haystack_integrations.components.embedders.sentence_transformers import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder,
)


# STEP 1: READ DOCUMENTr

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCUMENT_PATH = (
    PROJECT_ROOT / "Documents" / "BrightPath_Employee_Guide.txt"
)

MODEL = "sentence-transformers/all-MiniLM-L6-v2"

text = DOCUMENT_PATH.read_text(encoding="utf-8")

document = Document(
    content=text,
    meta={"source": DOCUMENT_PATH.name}
)

print("Document loaded")


# STEP 2: CREATE DOCUMENT STORE

store = InMemoryDocumentStore(
    embedding_similarity_function="cosine"
)


# STEP 3: CREATE INDEXING PIPELINE

indexing = Pipeline()

indexing.add_component(
    "splitter",
    DocumentSplitter(
        split_by="word",
        split_length=120,
        split_overlap=20
    )
)

indexing.add_component(
    "embedder",
    SentenceTransformersDocumentEmbedder(model=MODEL)
)

indexing.add_component(
    "writer",
    DocumentWriter(document_store=store)
)

indexing.connect(
    "splitter.documents",
    "embedder.documents"
)

indexing.connect(
    "embedder.documents",
    "writer.documents"
)

indexing.run({
    "splitter": {"documents": [document]}
})

print("Stored chunks:", store.count_documents())


# STEP 4: CREATE QUERY PIPELINE

search = Pipeline()

search.add_component(
    "query_embedder",
    SentenceTransformersTextEmbedder(model=MODEL)
)

search.add_component(
    "retriever",
    InMemoryEmbeddingRetriever(
        document_store=store,
        top_k=3
    )
)

search.connect(
    "query_embedder.embedding",
    "retriever.query_embedding"
)


# STEP 5: ASK QUESTIONS

while True:

    question = input("\nQuestion (exit to stop): ").strip()

    if question.lower() == "exit":
        break

    if not question:
        continue

    result = search.run({
        "query_embedder": {"text": question}
    })

    chunks = result["retriever"]["documents"]

    for i, chunk in enumerate(chunks, start=1):

        print("\n" + "=" * 50)
        print("Result:", i)
        print("Source:", chunk.meta.get("source"))
        print("Similarity:", chunk.score)
        print("Text:", chunk.content)
