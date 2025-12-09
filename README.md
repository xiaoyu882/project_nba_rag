# NBA Play-by-Play Streaming Pipeline  
### Kafka + ChromaDB + Real-Time Retrieval + Analyst CLI

This project implements a real-time streaming and retrieval pipeline for NBA play-by-play data using Apache Kafka, Python producers/consumers, ChromaDB vector search, lightweight hashing embeddings, and a rule-based analyst interface.

It corresponds to Project 2 — Theme 5.

---

## Project Overview

The system streams NBA play-by-play data through Kafka, ingests it into a local vector database, and supports natural-language queries using semantic retrieval.

Users can ask questions such as:

- Who scored the last points?  
- Why was there a foul?  
- What happened during the last possession?

---

## Supplement: Optional GPT-Based Version (Limited by API Quotas)

The project also includes an optional version of the analyst module that uses commercial large language models (e.g., OpenAI GPT-4/4o).  
These models can generate more fluent explanations but require paid API credits.

Due to quota limits, the default configuration uses a fully local, rule-based analyst that does not depend on any external API and can run on any machine without cost.

---

## System Architecture

┌──────────────────┐ ┌─────────────────────────┐
│ NBA CSV Data │ │ replay_game_kafka.py │
│ (downloaded once)│ ---> │ sends events to Kafka │
└──────────────────┘ └─────────────┬────────────┘
│
Kafka topic: nba_pbp_raw
│
┌─────────────────────────┴──────────────────────────┐
│ ingest_to_chroma.py │
│ - consumes Kafka stream │
│ - builds text + hashing embeddings │
│ - inserts documents into ChromaDB │
└───────────────┬────────────────────────────────────┘
│
ChromaDB vector storage
│
┌─────────────────┴─────────────────────┐
│ query_chroma.py analyst_cli.py │
│ - semantic search - rule-based Q&A │
└────────────────────────────────────────┘


---

## Folder Structure



project/
│
├── download_data.py
├── replay_game_kafka.py
├── ingest_to_chroma.py
├── query_chroma.py
├── analyst_cli.py # default local analyst (no LLM)
├── analyst_gpt.py # optional GPT-based analyst (requires API credits)
│
├── data/ # downloaded CSV files
├── chroma_db/ # persistent vector storage
└── README.md

