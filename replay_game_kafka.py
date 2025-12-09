# replay_game_kafka.py
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from confluent_kafka import Producer


def detect_single_game_csv(data_dir: Path) -> Path:
    """
    Try to automatically find a 'one_game_*.csv' file under the given data directory.
    If multiple files match, the first one (sorted by name) is used.
    """
    candidates = sorted(data_dir.glob("one_game_*.csv"))
    if not candidates:
        raise FileNotFoundError(
            f"No 'one_game_*.csv' file found in {data_dir}. "
            f"Run download_data.py first to generate one."
        )
    return candidates[0]


def build_score_string(row: pd.Series) -> str:
    """
    Build a score string like '102-98' using scoreHome and scoreAway.
    """
    home = None
    away = None
    if "scoreHome" in row.index and pd.notna(row["scoreHome"]):
        home = int(row["scoreHome"])
    if "scoreAway" in row.index and pd.notna(row["scoreAway"]):
        away = int(row["scoreAway"])

    if home is not None and away is not None:
        return f"{home}-{away}"
    return ""


def build_description(row: pd.Series) -> str:
    """
    Use the 'description' column as the main human-readable text.
    Fallback to actionType / subType when necessary.
    """
    if "description" in row.index and pd.notna(row["description"]) and str(row["description"]).strip() != "":
        return str(row["description"])

    pieces = []
    for col in ["actionType", "subType"]:
        if col in row.index and pd.notna(row[col]):
            pieces.append(str(row[col]))
    if pieces:
        return " / ".join(pieces)

    return "(no description)"


def format_event_for_log(row: pd.Series, idx: int) -> str:
    """
    Pretty-print event for console logging.
    """
    period = row["period"] if "period" in row.index else "?"
    clock = row["clock"] if "clock" in row.index else "?"
    action_number = row["actionNumber"] if "actionNumber" in row.index else idx
    score_str = build_score_string(row)
    desc = build_description(row)

    parts = [
        f"# {idx}",
        f"Q{period}",
        f"clock={clock}",
        f"actionNumber={action_number}",
    ]
    if score_str:
        parts.append(f"score={score_str}")
    header = " | ".join(parts)
    return f"{header}\n  -> {desc}"


def build_event_payload(row: pd.Series, idx: int) -> dict:
    """
    Build a JSON-serializable dict representing a single play event.
    This is the message that will be sent to Kafka.
    """
    game_id = row["gameId"] if "gameId" in row.index else None
    period = int(row["period"]) if "period" in row.index and pd.notna(row["period"]) else None
    clock = row["clock"] if "clock" in row.index else None
    action_number = int(row["actionNumber"]) if "actionNumber" in row.index and pd.notna(row["actionNumber"]) else idx

    score_home = int(row["scoreHome"]) if "scoreHome" in row.index and pd.notna(row["scoreHome"]) else None
    score_away = int(row["scoreAway"]) if "scoreAway" in row.index and pd.notna(row["scoreAway"]) else None
    score_str = build_score_string(row)

    description = build_description(row)

    payload = {
        "game_id": game_id,
        "period": period,
        "clock": clock,       
        "action_number": action_number,
        "description": description,
        "score_home": score_home,
        "score_away": score_away,
        "score": score_str,
        "team_id": row["teamId"] if "teamId" in row.index and pd.notna(row["teamId"]) else None,
        "team_tricode": row["teamTricode"] if "teamTricode" in row.index and pd.notna(row["teamTricode"]) else None,
        "player_name": row["playerName"] if "playerName" in row.index and pd.notna(row["playerName"]) else None,
        "action_type": row["actionType"] if "actionType" in row.index and pd.notna(row["actionType"]) else None,
        "sub_type": row["subType"] if "subType" in row.index and pd.notna(row["subType"]) else None,
        "shot_result": row["shotResult"] if "shotResult" in row.index and pd.notna(row["shotResult"]) else None,
        "shot_distance": int(row["shotDistance"]) if "shotDistance" in row.index and pd.notna(row["shotDistance"]) else None,
        "foul_personal_total": int(row["foulPersonalTotal"]) if "foulPersonalTotal" in row.index and pd.notna(row["foulPersonalTotal"]) else None,
        "foul_technical_total": int(row["foulTechnicalTotal"]) if "foulTechnicalTotal" in row.index and pd.notna(row["foulTechnicalTotal"]) else None,
        "turnover_total": int(row["turnoverTotal"]) if "turnoverTotal" in row.index and pd.notna(row["turnoverTotal"]) else None,
        "steal_player_name": row["stealPlayerName"] if "stealPlayerName" in row.index and pd.notna(row["stealPlayerName"]) else None,
        "assist_player_name": row["assistPlayerNameInitial"] if "assistPlayerNameInitial" in row.index and pd.notna(row["assistPlayerNameInitial"]) else None,
        "points_total": int(row["pointsTotal"]) if "pointsTotal" in row.index and pd.notna(row["pointsTotal"]) else None,
        "wallclock_ts": datetime.now(timezone.utc).isoformat()
    }

    return payload


def delivery_report(err, msg):
    """
    Callback for Kafka delivery reports.
    Called once for each message produced to indicate delivery result.
    """
    if err is not None:
        print(f"Delivery failed for record {msg.key()}: {err}")
    # else:
    #     print(f"Record successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")


def create_producer(bootstrap_servers: str = "localhost:9092") -> Producer:
    """
    Create a Kafka producer using confluent-kafka.
    """
    conf = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": "nba-replay-producer"
    }
    return Producer(conf)


def replay_game_to_kafka(
    csv_path: Path,
    topic: str = "nba_pbp_raw",
    sleep_seconds: float = 1.0,
    max_events: int | None = 50,
    bootstrap_servers: str = "localhost:9092",
    also_print: bool = True,
):
    """
    Replay a single game from a CSV file and send each event as a JSON message
    to a Kafka topic. Optionally also print to console.
    """
    print(f"Loading game data from: {csv_path}")

    df = pd.read_csv(csv_path)

    print("CSV loaded.")
    print("DataFrame shape (rows, columns):", df.shape)
    print("Columns:", list(df.columns))

    sort_cols = []
    if "period" in df.columns:
        sort_cols.append("period")
    if "actionNumber" in df.columns:
        sort_cols.append("actionNumber")
    elif "orderNumber" in df.columns:
        sort_cols.append("orderNumber")

    if sort_cols:
        df = df.sort_values(sort_cols)
        print(f"Sorted by columns: {sort_cols}")
    else:
        print("Warning: Could not find typical sorting columns ('period', 'actionNumber', 'orderNumber').")
        print("Using original CSV order.")

    total_events = len(df)
    if max_events is None or max_events > total_events:
        max_events = total_events

    print(f"\nConnecting to Kafka at: {bootstrap_servers}")
    producer = create_producer(bootstrap_servers)

    print(f"Starting replay to Kafka topic '{topic}' "
          f"(sleep={sleep_seconds}s between events, sending {max_events}/{total_events} events)")
    print("-" * 80)

    for i, (_, row) in enumerate(df.iloc[:max_events].iterrows(), start=1):
        event_payload = build_event_payload(row, i)
        event_json = json.dumps(event_payload)

        producer.produce(
            topic=topic,
            value=event_json.encode("utf-8"),
            callback=delivery_report
        )

        if also_print:
            print(format_event_for_log(row, i))

        producer.poll(0)

        time.sleep(sleep_seconds)

    producer.flush()

    print("-" * 80)
    print("Replay finished. All messages flushed to Kafka.")


if __name__ == "__main__":
    data_dir = Path("./data")
    try:
        csv_file = detect_single_game_csv(data_dir)
    except FileNotFoundError as e:
        print(str(e))
        raise SystemExit(1)

    TOPIC = "nba_pbp_raw"
    SLEEP_SECONDS = 1.0   
    MAX_EVENTS = 50      
    BOOTSTRAP_SERVERS = "localhost:9092"

    replay_game_to_kafka(
        csv_path=csv_file,
        topic=TOPIC,
        sleep_seconds=SLEEP_SECONDS,
        max_events=MAX_EVENTS,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        also_print=True,
    )
