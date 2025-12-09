# ingest_to_chroma.py
import json
import signal
from pathlib import Path

from confluent_kafka import Consumer
import chromadb
from sklearn.feature_extraction.text import HashingVectorizer


def create_kafka_consumer(
    bootstrap_servers: str = "localhost:9092",
    group_id: str = "nba-rag-ingester",
    topic: str = "nba_pbp_raw",
) -> Consumer:
    """
    Create and configure a Kafka consumer subscribed to the given topic.
    """
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "group.id": group_id,
        "auto.offset.reset": "earliest",
        "enable.auto.commit": True,
    }
    consumer = Consumer(conf)
    consumer.subscribe([topic])
    return consumer


def create_chroma_collection(
    db_path: Path = Path("./chroma_db"),
    collection_name: str = "nba_events",
):
    """
    Create (or get) a persistent Chroma collection.
    We do NOT use an internal embedding function; we provide embeddings manually.
    """
    db_path.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(db_path))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "NBA play-by-play events for RAG (hashing embeddings)"}
    )
    return collection


def get_vectorizer():
    """
    Create a HashingVectorizer.
    HashingVectorizer is stateless and does not require fitting.
    We must use the same parameters in both ingestion and query.
    """
    vectorizer = HashingVectorizer(
        n_features=1024,        # dimension of the embedding
        alternate_sign=False,   # keep embeddings non-negative for simplicity
        norm="l2"               # normalize vectors
    )
    return vectorizer


def sanitize_metadata(meta: dict) -> dict:
    """
    Chroma does not accept None in metadata.
    Keep only values that are bool/int/float/str, drop None, and
    convert other types to str.
    """
    clean = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (bool, int, float, str)):
            clean[k] = v
        else:
            # e.g. numpy types or other objects
            clean[k] = str(v)
    return clean


def build_document_from_event(event: dict) -> tuple[str, dict]:
    """
    Build a text document and metadata from a single event payload.
    Returns (text, metadata_dict).
    """
    game_id = event.get("game_id")
    period = event.get("period")
    clock = event.get("clock")
    score_home = event.get("score_home")
    score_away = event.get("score_away")
    score_str = event.get("score")
    description = event.get("description") or "(no description)"

    text_parts = []
    if game_id is not None:
        text_parts.append(f"Game {game_id}")
    if period is not None and clock is not None:
        text_parts.append(f"Q{period} {clock}")
    if score_home is not None and score_away is not None:
        text_parts.append(f"score {score_home}-{score_away}")
    elif score_str:
        text_parts.append(f"score {score_str}")

    header = ", ".join(text_parts)
    if header:
        doc_text = f"[{header}] {description}"
    else:
        doc_text = description

    metadata = {
        "game_id": str(game_id) if game_id is not None else None,
        "period": period,
        "clock": clock,
        "score": score_str,
        "team_tricode": event.get("team_tricode"),
        "player_name": event.get("player_name"),
        "action_type": event.get("action_type"),
        "sub_type": event.get("sub_type"),
        "wallclock_ts": event.get("wallclock_ts"),
    }

    metadata = sanitize_metadata(metadata)
    return doc_text, metadata


def main():
    topic = "nba_pbp_raw"
    bootstrap_servers = "localhost:9092"
    db_path = Path("./chroma_db")
    collection_name = "nba_events"

    print(f"Connecting to Kafka at {bootstrap_servers}, topic='{topic}' ...")
    consumer = create_kafka_consumer(
        bootstrap_servers=bootstrap_servers,
        group_id="nba-rag-ingester",
        topic=topic,
    )

    print(f"Connecting to Chroma at {db_path}, collection='{collection_name}' ...")
    collection = create_chroma_collection(
        db_path=db_path,
        collection_name=collection_name,
    )

    print("Creating HashingVectorizer (no PyTorch / transformers required)...")
    vectorizer = get_vectorizer()

    print("Ready. Starting ingestion loop. Press Ctrl+C to stop.")
    running = True

    def handle_sigint(sig, frame):
        nonlocal running
        print("\nSIGINT received, stopping gracefully...")
        running = False

    signal.signal(signal.SIGINT, handle_sigint)

    batch_texts = []
    batch_ids = []
    batch_metadatas = []
    batch_size = 32
    total_ingested = 0

    while running:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Consumer error:", msg.error())
            continue

        try:
            event = json.loads(msg.value().decode("utf-8"))
        except json.JSONDecodeError as e:
            print("Failed to decode JSON:", e)
            continue

        game_id = event.get("game_id", "unknown_game")
        action_number = event.get("action_number", "unknown_action")
        period = event.get("period", "unknown_period")
        doc_id = f"{game_id}-{period}-{action_number}"

        doc_text, metadata = build_document_from_event(event)

        batch_ids.append(doc_id)
        batch_texts.append(doc_text)
        batch_metadatas.append(metadata)

        if len(batch_ids) >= batch_size:
            embeddings = vectorizer.transform(batch_texts).toarray().tolist()

            collection.add(
                ids=batch_ids,
                documents=batch_texts,
                metadatas=batch_metadatas,
                embeddings=embeddings,
            )
            total_ingested += len(batch_ids)
            print(f"Ingested {total_ingested} events into Chroma (last batch size={len(batch_ids)})")

            batch_ids = []
            batch_texts = []
            batch_metadatas = []

    # Flush remaining batch if any
    if batch_ids:
        embeddings = vectorizer.transform(batch_texts).toarray().tolist()
        collection.add(
            ids=batch_ids,
            documents=batch_texts,
            metadatas=batch_metadatas,
            embeddings=embeddings,
        )
        total_ingested += len(batch_ids)
        print(f"Final batch ingested, total events={total_ingested}")

    consumer.close()
    print("Kafka consumer closed. Ingestion stopped.")


if __name__ == "__main__":
    main()
