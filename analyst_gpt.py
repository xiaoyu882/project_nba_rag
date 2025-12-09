# analyst_gpt.py
import os
from pathlib import Path

import chromadb
from sklearn.feature_extraction.text import HashingVectorizer
from openai import OpenAI


client = OpenAI(api_key="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")


def get_vectorizer():
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
    return client.get_collection(name=collection_name)


def parse_doc(doc: str):
    """Split '[header] description' into (header, description)."""
    if "] " in doc:
        header, desc = doc.split("] ", 1)
        return header.lstrip("["), desc
    return "", doc


def ask_gpt(question: str, context_events: list[str]) -> str:
    """
    Use GPT-4.1 Mini or GPT-4o to generate a commentary-style answer.
    """
    context_text = "\n".join(f"- {evt}" for evt in context_events)

    prompt = f"""
You are a professional NBA play-by-play analyst.

The user asked: "{question}"

Here are the most relevant recent events from the game:
{context_text}

Please provide:
1) A clear and correct answer to the question (based on the events)
2) Short contextual explanation when relevant
3) If the question is subjective or impossible to answer (e.g., "cutest player"), answer humorously but safely, and explain that the play-by-play record contains no such metric.
"""


    model_name = "gpt-4.1-mini"

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are an expert NBA analyst."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content


def main():
    collection = get_collection()
    vectorizer = get_vectorizer()

    print("NBA GPT Analyst CLI")
    print("Ask anything about the game (type 'exit' to quit).")

    while True:
        q = input("\nQuestion: ").strip()
        if q.lower() in {"exit", "quit"}:
            break

        # Embed question
        query_vec = vectorizer.transform([q]).toarray().tolist()

        # Retrieve relevant events
        res = collection.query(
            query_embeddings=query_vec,
            n_results=5,
        )

        docs = res.get("documents", [[]])[0]

        if not docs:
            print("No relevant events found.")
            continue

        # Extract descriptions only
        context_events = [parse_doc(doc)[1] for doc in docs[:3]]

        print("\n--- Retrieved context (top 3) ---")
        for i, evt in enumerate(context_events, start=1):
            print(f"{i}. {evt}")

        # GPT generates the final answer
        answer = ask_gpt(q, context_events)

        print("\n--- GPT Analyst Answer ---")
        print(answer)

    print("\nBye.")


if __name__ == "__main__":
    main()
