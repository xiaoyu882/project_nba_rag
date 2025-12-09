# NBA Play-by-Play Streaming Pipeline  
Data Stream Processing – Final Project

This project implements a real-time data streaming pipeline for NBA play-by-play (PBP) events using Apache Kafka, Python producers/consumers, ChromaDB vector storage, and a lightweight analyst interface. The system supports natural-language queries over the game and retrieves semantically relevant events from a vector database.

All components run locally. An optional LLM-based analyst is included but requires an external API key and may incur usage fees.

---

## Features

- Real-time event streaming through Kafka  
- Play-by-play ingestion, embedding, and storage in ChromaDB  
- Natural-language retrieval over historical or live-streamed events  
- Rule-based analyst for English explanations (local, no API required)  
- Optional GPT-based analyst for enhanced explanations (requires API)  

---

## File Overview

data/ # Downloaded NBA play-by-play CSV files
chroma_db/ # Persistent ChromaDB vector storage

download_data.py # Downloads NBA PBP data
nba_data_loader.py # Loads and parses CSV files

replay_game.py # Sequential offline replay of events
replay_game_kafka.py # Kafka producer streaming events to topic 'nba_pbp_raw'

ingest_to_chroma.py # Kafka consumer:
- receives events
- converts them to text
- builds hashing embeddings
- stores in ChromaDB

query_chroma.py # Natural-language vector search interface

analyst_cli.py # Local analyst with simple rule-based explanations
analyst_gpt.py # LLM-based analyst (optional; requires API key, may incur costs)

README.md # Project documentation

---

## System Workflow

1. download_data.py

2. replay_game_kafka.py → streams play-by-play events to Kafka

3. ingest_to_chroma.py → consumes events, embeds them, stores in ChromaDB

4. query_chroma.py → retrieves relevant events based on a question

5. analyst_cli.py → produces explanations (local)
   or
   analyst_gpt.py → produces LLM explanations (API required)


---

## Running Instructions

Open multiple terminals and execute:

### 1. Start Zookeeper
cd C:\kafka_2.13-3.6.0
bin\windows\zookeeper-server-start.bat config\zookeeper.properties

### 2. Start Kafka Broker
cd C:\kafka_2.13-3.6.0
bin\windows\kafka-server-start.bat config\server.properties

### 3. Start Chroma ingestion
python ingest_to_chroma.py

### 4. Stream game events into Kafka
python replay_game_kafka.py

### 5. Query the vector store
python query_chroma.py


### 6. Run the analyst (local, recommended)
python analyst_cli.py


---

## Example Queries

who scored the last points?
who made the last 3-point shot?
what happened during the last possession?
which team committed the most recent foul?

---

## Notes

- The project is fully reproducible on Windows and requires no external paid services.  
- The GPT-based analyst (`analyst_gpt.py`) provides enhanced explanations but relies on external API usage and may incur charges.  
- The default pipeline (`analyst_cli.py`) operates entirely offline and is used for grading unless otherwise specified.

