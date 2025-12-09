下面是 **完整、可直接复制、不会被 Markdown 破坏格式的 `README.md`**。
你可以把它直接放入项目根目录，GitHub 上显示效果非常专业。

---

# 🎯 **完整可复制版 README.md（最终版）**

```markdown
# NBA Play-by-Play Streaming Pipeline  
### Kafka + ChromaDB + Real-Time Retrieval + Analyst CLI

This project implements a **real-time streaming and retrieval pipeline** for NBA play-by-play data using:

- **Apache Kafka** (streaming)
- **Python producers/consumers**
- **ChromaDB** (vector search)
- **Hashing embeddings** (fast, lightweight)
- **Analyst CLI** (rule-based natural language answers)

It corresponds to **Project 2 — Theme 5**.

---

# 🏀 Project Overview

The system streams NBA play-by-play data through Kafka, ingests it into a vector database, and supports **natural-language queries** over the game using semantic search.

You can ask questions like:

- *“Who scored the last points?”*  
- *“Why was there a foul?”*  
- *“What happened during the last possession?”*

---

# 🧱 System Architecture

```

```
 ┌──────────────────┐      ┌─────────────────────────┐
 │  NBA CSV Data    │      │ replay_game_kafka.py     │
 │ (downloaded once)│ ---> │  sends events to Kafka   │
 └──────────────────┘      └─────────────┬───────────┘
                                          │
                                  Kafka topic: nba_pbp_raw
                                          │
               ┌──────────────────────────┴───────────────────────────┐
               │ ingest_to_chroma.py                                   │
               │ - consumes Kafka stream                               │
               │ - builds text + hashing embeddings                    │
               │ - inserts documents into ChromaDB                     │
               └───────────────┬───────────────────────────────────────┘
                               │
                        ChromaDB vector storage
                               │
             ┌─────────────────┴─────────────────────┐
             │ query_chroma.py      analyst_cli.py    │
             │ - semantic search    - rule-based Q&A  │
             └────────────────────────────────────────┘
```

```

---

# 📁 Folder Structure

```

project/
│
├── download_data.py
├── replay_game_kafka.py
├── ingest_to_chroma.py
├── query_chroma.py
├── analyst_cli.py
│
├── data/                   # downloaded CSV files
├── chroma_db/              # persistent vector storage
└── README.md

````

---

# ⚙️ Installation

### Install Python dependencies:

```bash
pip install pandas chromadb confluent-kafka scikit-learn
````

### Install Kafka (Windows)

Unzip Kafka to:

```
C:\kafka_2.13-3.6.0
```

---

# 🚀 Run the Full Demo (Step-by-Step)

Open **six terminal windows** and run the following commands.

---

## 🪟 Window 1 — Start Zookeeper

```powershell
cd C:\kafka_2.13-3.6.0
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties
```

---

## 🪟 Window 2 — Start Kafka Broker

```powershell
cd C:\kafka_2.13-3.6.0
.\bin\windows\kafka-server-start.bat .\config\server.properties
```

---

## 🪟 Window 3 — Start ingestion (Kafka → Chroma)

```powershell
cd C:\Users\OS\Desktop\data_stream_processing\project
python ingest_to_chroma.py
```

You should see:

```
Ready. Starting ingestion loop...
```

---

## 🪟 Window 4 — Replay the NBA game (Producer → Kafka)

```powershell
cd C:\Users\OS\Desktop\data_stream_processing\project
python replay_game_kafka.py
```

Example output:

```
#1 | Q1 | clock=PT12M00S | score 0-0
-> Jump Ball...
```

Meanwhile, ingestion window shows:

```
Ingested 32 events into Chroma
Ingested 64 events...
```

---

## 🪟 Window 5 — Query the vector database

```powershell
cd C:\Users\OS\Desktop\data_stream_processing\project
python query_chroma.py
```

Example queries:

```
who scored the last points?
who made the last three-point shot?
what happened at the beginning of the game?
```

---

## 🪟 Window 6 — Run the Analyst CLI (rule-based explanation)

```powershell
cd C:\Users\OS\Desktop\data_stream_processing\project
python analyst_cli.py
```

Example interaction:

```
Question: who scored the last points?

--- Retrieved context ---
1. C. Capela alley-oop DUNK...

--- Analyst answer ---
Based on the most relevant recent play, Capela scored the last points.
```

---

# 🔍 Example Questions to Try

```
who scored the last points?
who committed the most recent foul?
what happened in the last possession?
who made the last 3pt shot?
summarize the last three plays.
why did the possession change?
```

---

# 🌟 Features

### ✔ Real-time Kafka streaming

Simulates live game feed event-by-event.

### ✔ Local vector embeddings

Efficient HashingVectorizer (no GPU needed).

### ✔ Searchable play-by-play database

Natural-language queries supported via ChromaDB.

### ✔ Analyst mode

Provides readable English explanations of retrieved events.

### ✔ Fully local, no API required

Runs on any machine.

---

# 🔮 Future Extensions

* Real LLM integration (OpenAI, Groq, DeepSeek)
* Web app interface (Streamlit / FastAPI)
* Real-time scoring dashboards
* Player analytics & heatmaps
* Multi-game ingestion and retrieval

---

# 📌 Notes

* Designed for educational purposes (Project 2 Theme 5).
* Fully reproducible on Windows.
* All computation runs locally (no cloud services required).

---

# 🎉 End of README

For questions or issues, feel free to open an issue or contact the project author.

```
