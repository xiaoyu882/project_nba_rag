# download_data.py
from pathlib import Path
from nba_data_loader import load_nba_data  # Make sure nba_data_loader.py is in the same directory

def find_game_id_column(df):
    """
    Try to find which column represents the game identifier.
    Different datasets may use different names.
    """
    candidate_cols = ["GAME_ID", "gameId", "game_id", "game"]
    for col in candidate_cols:
        if col in df.columns:
            return col
    return None

def main():
    # 1. Directory to store data (will be created automatically)
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)

    print("download_data.py started")
    print("Starting download: cdnnba regular season 2024 data...")

    # 2. Call load_nba_data to download and load the dataset into memory
    df = load_nba_data(
        path=data_dir,     # Used only if in_memory=False (we keep in_memory=True)
        seasons=2024,      # Download only the 2024 season
        data="cdnnba",     # Use the 'cdnnba' dataset type
        seasontype="rg",   # 'rg' = Regular Season
        league="nba",
        in_memory=True,    # Load directly into memory as a DataFrame
        use_pandas=True    # Return a pandas DataFrame
    )

    # 3. Basic information output
    print("Download complete!")
    print("DataFrame shape (rows, columns):", df.shape)
    print("\nPreview of the first 5 rows:")
    print(df.head())

    # 4. Save the full dataset to CSV
    full_csv_path = data_dir / "cdnnba_2024_full.csv"
    df.to_csv(full_csv_path, index=False)
    print(f"\nFull dataset saved to: {full_csv_path}")

    # 5. Try to detect which column is the game id
    game_id_col = find_game_id_column(df)
    if game_id_col is None:
        print("\nWarning: Could not find a game id column (e.g. GAME_ID, gameId, game_id, game).")
        print("Columns available in the DataFrame are:")
        print(list(df.columns))
        return

    print(f"\nDetected game id column: '{game_id_col}'")

    # 6. Extract a single game for Kafka replay demo
    game_ids = df[game_id_col].unique()
    print("Number of games in this dataset:", len(game_ids))
    print("First few game ids:", game_ids[:5])

    one_game_id = game_ids[0]  # Select the first game
    df_one_game = df[df[game_id_col] == one_game_id].copy()

    one_game_csv_path = data_dir / f"one_game_{one_game_id}.csv"
    df_one_game.to_csv(one_game_csv_path, index=False)
    print(f"\nSingle game extracted and saved to: {one_game_csv_path}")

if __name__ == "__main__":
    main()
