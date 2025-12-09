# replay_game.py
import time
from pathlib import Path

import pandas as pd


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
    Try to build a score string like '102-98' using typical column names.
    If no score columns are found, return an empty string.
    """
    # Common guesses for home/away score columns
    home_candidates = ["scoreHome", "homeScore", "home_score", "homeTeamScore"]
    away_candidates = ["scoreAway", "awayScore", "away_score", "awayTeamScore"]
    score_col_candidates = ["score", "SCORE"]

    home_score = None
    away_score = None

    for col in home_candidates:
        if col in row.index and pd.notna(row[col]):
            home_score = row[col]
            break

    for col in away_candidates:
        if col in row.index and pd.notna(row[col]):
            away_score = row[col]
            break

    if home_score is not None and away_score is not None:
        return f"{home_score}-{away_score}"

    # If we don't have separate home/away scores, try a single 'score' column
    for col in score_col_candidates:
        if col in row.index and pd.notna(row[col]):
            return str(row[col])

    return ""  # Unknown / not available


def build_description(row: pd.Series) -> str:
    """
    Try to construct a human-readable description for the play.
    Different datasets may store this in different columns.
    """
    # Possible columns that may contain a text description of the action
    candidate_cols = [
        "description",
        "playDescription",
        "HOMEDESCRIPTION",
        "VISITORDESCRIPTION",
        "NEUTRALDESCRIPTION",
        "actionType",
        "subType"
    ]
    for col in candidate_cols:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip() != "":
            return str(row[col])

    # Fallback: show actionType + subType if available
    pieces = []
    for col in ["actionType", "subType"]:
        if col in row.index and pd.notna(row[col]):
            pieces.append(str(row[col]))
    if pieces:
        return " / ".join(pieces)

    return "(no description)"


def format_event(row: pd.Series, idx: int) -> str:
    """
    Format a single play event as a readable string.
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
        f"actionNumber={action_number}"
    ]
    if score_str:
        parts.append(f"score={score_str}")

    header = " | ".join(parts)
    return f"{header}\n  -> {desc}"


def replay_game(csv_path: Path, sleep_seconds: float = 1.0, max_events: int | None = 50):
    """
    Replay a single game's play-by-play from a CSV file.
    For now it just prints events to the console with a delay between them.
    Later we can replace the print() with Kafka producer logic.
    """
    print(f"Loading game data from: {csv_path}")

    df = pd.read_csv(csv_path)

    print("CSV loaded.")
    print("DataFrame shape (rows, columns):", df.shape)
    print("Columns:", list(df.columns))

    # Try to sort events in game order
    sort_cols = []
    if "period" in df.columns:
        sort_cols.append("period")
    if "actionNumber" in df.columns:
        sort_cols.append("actionNumber")
    elif "EVENTNUM" in df.columns:
        sort_cols.append("EVENTNUM")

    if sort_cols:
        df = df.sort_values(sort_cols)
        print(f"Sorted by columns: {sort_cols}")
    else:
        print("Warning: Could not find typical sorting columns ('period', 'actionNumber', 'EVENTNUM').")
        print("Using original CSV order.")

    total_events = len(df)
    if max_events is None or max_events > total_events:
        max_events = total_events

    print(f"\nStarting replay... (sleep={sleep_seconds}s between events, showing {max_events}/{total_events} events)")
    print("-" * 80)

    for i, (_, row) in enumerate(df.iloc[:max_events].iterrows(), start=1):
        print(format_event(row, i))
        time.sleep(sleep_seconds)

    print("-" * 80)
    print("Replay finished.")


if __name__ == "__main__":
    # Default settings
    data_dir = Path("./data")
    try:
        csv_file = detect_single_game_csv(data_dir)
    except FileNotFoundError as e:
        print(str(e))
        raise SystemExit(1)

    # You can tune these parameters:
    SLEEP_SECONDS = 1.0   # delay between events (in real seconds)
    MAX_EVENTS = 50       # set to None to replay the whole game

    replay_game(csv_file, sleep_seconds=SLEEP_SECONDS, max_events=MAX_EVENTS)
