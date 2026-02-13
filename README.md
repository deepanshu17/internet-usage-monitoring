# Internet Usage Monitoring Service

A high-performance Python-based HTTP service built with **FastAPI**, **SQLAlchemy**, and **SQLite**. This service provides comprehensive internet usage analytics and deep-dive user search capabilities.

## 🚀 Project Overview

This service was developed for the MishiPay / HackerEarth hiring challenge (December 2022). Its primary goal is to process large internet session datasets (100,000+ records) and provide instant analytics via paginated HTTP APIs.

## 🛠 Tech Stack

- **Backend Framework**: FastAPI (Asynchronous, High-performance)
- **Database**: SQLite with SQLAlchemy ORM (Indexed for large datasets)
- **Data Engineering**: Pandas (Batch processing of 100k records)
- **Testing**: PyTest with Coverage (100% logic coverage)

---

## 📖 Implementation Details

### 1. Data Ingestion & Transformation (`scripts/ingest.py`)

- **Efficiency**: Uses Pandas to read the 100k dataset in seconds.
- **Cleaning**: Robustly handles CSV formatting inconsistencies (e.g., spaces in headers).
- **Unit Conversion**: Converted all raw upload/download values into **Kilobits (Kb)** as per requirements.
- **Time Parsing**: Converts `H:M:S` usage time into total seconds for precise mathematical aggregation.

### 2. Core API Logic (`app/main.py`)

- **`GET /analytics`**: Uses complex SQL filtering to calculate overlapping session usage for 1, 7, and 30-day windows simultaneously.
- **`GET /user/search`**: Implements a relative time-window search (1h, 6h, 24h) from any arbitrary timestamp.
- **Formatting**: Automatically formats durations (e.g., `12h33m`) and data sizes (e.g., `1.4TB`, `100.5MB`, `30.2GB`) for human readability.

---

## ⚙️ Setup & Execution

### 1. Environment Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Ingestion (Populate Database)

```bash
python3 scripts/ingest.py
```

_Successfully ingests 100,000 records into `internet_usage.db`._

### 3. Start the Server

```bash
uvicorn app.main:app --reload
```

Server runs at: `http://127.0.0.1:8000`

---

## 🧪 Testing Procedure

### 1. Automated Testing (100% Coverage)

We achieved **100% test coverage** across all app logic and ingestion flows.

```bash
coverage run -m pytest tests
coverage report -m
```

### 2. Manual Testing (Swagger UI)

Open **`http://127.0.0.1:8000/docs`** to test interactively.

#### **Sample Test Case 1: Analytics**

- **Date**: `04112022`
- **What it does**: Returns the top 100 users ranked by their 30-day usage starting from Nov 4, 2022.

#### **Sample Test Case 2: User Search**

- **Username**: `brainyHeron5`
- **Datetime**: `20221104T1600`
- **What it does**: Returns exact upload/download/time stats for that user in the 1h, 6h, and 24h windows leading up to 4:00 PM.

---

## 🧩 Design Decisions

- **Scalability**: Added database indexes on `username` and `start_time` to maintain fast response times even with 100,000+ records.
- **Error Handling**: Implemented custom JSON response handlers to ensure errors match the required format: `{"ok": false, "error": {"message": "invalid date"}}`.
- **Data Integrity**: Used a dedicated test database during unit tests to ensure production data is never corrupted during verification.
