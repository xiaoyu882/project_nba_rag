# analyst_cli.py
from pathlib import Path
import re

import chromadb
from sklearn.feature_extraction.text import HashingVectorizer


def get_vectorizer():
    """
    Same HashingVectorizer as in ingest_to_chroma.py and query_chroma.py.
    """
    return HashingVectorizer(
        n_features=1024,
        alternate_sign=False,
        norm="l2",
    )


def get_collection(
    db_path: Path = Path("./chroma_db"),
    collection_name: str = "nba_events",
):
    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_collection(name=collection_name)
    return collection


def parse_doc(doc: str):
    """
    Our stored document format is like:
      "[Game 22400001, Q1 PT08M05.00S, score 8-9] C. Capela alley-oop DUNK (4 PTS) (J. Johnson 1 AST)"
    We split it into (header, description).
    """
    if "] " in doc:
        header, desc = doc.split("] ", 1)
        header = header.lstrip("[")
    else:
        header, desc = "", doc
    return header, desc


def build_simple_answer(question: str, docs, metas):
    """
    Very simple rule-based "analyst" that uses the top retrieved event
    to generate an English explanation.
    """
    if not docs:
        return "I could not find any relevant play in the current memory."

    # Pick the most relevant doc (first result)
    doc = docs[0]
    meta = metas[0] if metas else {}

    header, desc = parse_doc(doc)

    game_id = meta.get("game_id", "unknown game")
    period = meta.get("period", "?")
    clock = meta.get("clock", "?")
    score = meta.get("score", "?")
    player = meta.get("player_name", "the player")
    team = meta.get("team_tricode", "the team")

    # Default explanation
    base_info = f"In game {game_id}, Q{period} at {clock}, with score {score}, the play was: {desc}"

    q_lower = question.lower()

    # Simple heuristics based on question pattern
    if "who scored" in q_lower or "who made" in q_lower or "who hit" in q_lower:
        # Try to detect if the description looks like a scoring event
        if "PTS" in desc or "Free Throw" in desc or "3PT" in desc or "Layup" in desc or "DUNK" in desc:
            return (
                f"Based on the most relevant recent play, it looks like {player} from {team} scored the last points.\n"
                f"Context: {base_info}"
            )
        else:
            return (
                "I am not fully sure who scored last, but the most relevant recent play I found is:\n"
                f"{base_info}"
            )

    if "foul" in q_lower:
        if "FOUL" in desc.upper():
            return (
                "The question is about a foul. The most relevant foul I found is:\n"
                f"{base_info}\n"
                "This foul likely explains the whistle and the change of possession or free throws."
            )
        else:
            return (
                "I could not clearly find a foul event in the top result, but here is the closest play I found:\n"
                f"{base_info}"
            )

    if "rebound" in q_lower:
        if "REBOUND" in desc.upper():
            return (
                "You asked about the rebound. The closest rebound I found is:\n"
                f"{base_info}"
            )
        else:
            return (
                "I'm not fully sure about the rebound, but the most related play I found is:\n"
                f"{base_info}"
            )

    if "timeout" in q_lower or "time out" in q_lower:
        if "Timeout" in desc or "TIMEOUT" in desc:
            return (
                "You asked about a timeout. The most relevant timeout I found is:\n"
                f"{base_info}"
            )
        else:
            return (
                "I did not clearly find a timeout event, but the closest play is:\n"
                f"{base_info}"
            )

    # Fallback: generic explanation
    return (
        "Here is the most relevant recent play I found related to your question:\n"
        f"{base_info}"
    )


def main():
    collection = get_collection()
    vectorizer = get_vectorizer()

    print("NBA live analyst CLI")
    print("Ask a question about the game (or type 'exit' to quit).")

    while True:
        q = input("\nQuestion: ").strip()
        if q.lower() in {"exit", "quit"}:
            break

        # Embed the question
        query_vec = vectorizer.transform([q]).toarray().tolist()

        # Retrieve top-k events
        res = collection.query(
            query_embeddings=query_vec,
            n_results=5,
        )

        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]

        if not docs:
            print("No results found in the vector store.")
            continue

        # Print top 3 raw docs as context
        print("\n--- Retrieved context (top 3) ---")
        for i, (doc, meta) in enumerate(zip(docs[:3], metas[:3]), start=1):
            header, desc = parse_doc(doc)
            print(f"#{i}: {desc}")
            print(f"   meta: {meta}")

        # Build and print a simple answer
        answer = build_simple_answer(q, docs, metas)
        print("\n--- Analyst answer ---")
        print(answer)

    print("\nBye.")


if __name__ == "__main__":
    main()
