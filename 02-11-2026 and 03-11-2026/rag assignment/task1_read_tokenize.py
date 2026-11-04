from pathlib import Path
import tiktoken

DOCS_FOLDER = Path(__file__).parent / "Documents"

encoding = tiktoken.get_encoding("cl100k_base")


def read_documents(folder: Path) -> dict:
    """Return a dictionary of {filename: text} for every .txt file in the folder."""

    documents = {}

    for file_path in sorted(folder.glob("*.txt")):
        documents[file_path.name] = file_path.read_text(encoding="utf-8")

    return documents

print(read_documents(DOCS_FOLDER))

def main():
    documents = read_documents(DOCS_FOLDER)

    if not documents:
        print(f"No .txt found in {DOCS_FOLDER}")
        return

    total_token = 0

    for file_name, text in documents.items():
        tokens = encoding.encode(text)
        total_token += len(tokens)

        print("=" * 60)
        print(f"file: {file_name}")
        print("=" * 60)

        print(text)
        print("-" * 60)
        print(f"Characters: {len(text)} | Tokens: {len(tokens)}")
        print()

    print(f"Documents read: {len(documents)} | Total Tokens: {total_token}")



if __name__ == "__main__":
    main()