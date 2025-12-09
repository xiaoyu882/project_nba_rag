# query_chroma.py
from pathlib import Path

import chromadb
from sklearn.feature_extraction.text import HashingVectorizer


def get_vectorizer():
    """
    Create the same HashingVectorizer as in ingest_to_chroma.py.
    Parameters MUST match.
    """
    vectorizer = HashingVectorizer(
        n_features=1024,
        alternate_sign=False,
        norm="l2",
    )
    return vectorizer


def get_collection(
    db_path: Path = Path("./chroma_db"),
    collection_name: str = "nba_events",
):
    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_collection(name=collection_name)
    return collection


def main():
    collection = get_collection()
    vectorizer = get_vectorizer()

    print("Type a question about the game (or 'exit' to quit).")
    while True:
        q = input("\nQuestion: ").strip()
        if q.lower() in {"exit", "quit"}:
            break

        # Embed the query using the same HashingVectorizer
        query_vec = vectorizer.transform([q]).toarray().tolist()

        res = collection.query(
            query_embeddings=query_vec,
            n_results=5,
        )

        print("\nTop results:")
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        ids = res.get("ids", [[]])[0]

        for i, (doc, meta, _id) in enumerate(zip(docs, metas, ids), start=1):
            print(f"--- #{i} ---")
            print(f"ID:      {_id}")
            print(f"Doc:     {doc}")
            print(f"Metadata:{meta}")

    print("Bye.")


if __name__ == "__main__":
    main()
