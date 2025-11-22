
# Trading Lab
A modular analytics platform designed to explore order books, liquidity, forecasting, volatility, alternative data, and sentiment-driven trading strategies.

<img width="1024" height="784" alt="tradinglab" src="https://github.com/user-attachments/assets/17eb36c2-8721-44c2-8ec8-8a9b7b0378f1" />


This project simulates the type of internal analytics tooling used by modern electronic marketplaces. It combines real-time data pipelines, machine learning models, and interactive dashboards to demonstrate practical insights into price discovery, liquidity dynamics, and market behavior.

## 🎯 Project Purpose

Trading Lab is in a domain where price discovery, liquidity distribution, and order book transparency matter deeply. 

The purpose of this project is to:

- Demonstrate strong capabilities in **data engineering**, **machine learning**, and **market microstructure analysis**.
- Build practical tools that explore **order flow**, **liquidity imbalance**, **forecasting**, **volatility modeling**, and **sentiment analysis**.
- Show how alternative signals (Google Trends, sentiment, SEC filings) can enhance understanding of market behavior.
- Deliver the entire project in one unified app with multiple “labs,” mimicking an internal analytics platform for a trading marketplace.

## 🏗️ Architecture Overview

                      ┌────────────────────────────┐
                      │   Binance / Yahoo APIs     │
                      └──────────────┬─────────────┘
                                     │
                          Real-Time & Historical Data
                                     │
             ┌───────────────────────┴───────────────────────┐
             │                                               │
     ┌───────────────┐                               ┌─────────────────┐
     │ Data Pipeline  │                               │  Alt Data APIs  │
     │ (Python ETL)   │                               │ (Google Trends) │
     └──────┬─────────┘                               └──────┬──────────┘
            │                                                │
            ▼                                                ▼
     ┌────────────────┐                             ┌──────────────────┐
     │  PostgreSQL    │                             │   Sentiment Data  │
     │  (market data) │                             │  Reddit + SEC     │
     └────────┬───────┘                             └─────────┬────────┘
              │                                               │
              ├───────────────────────────────┬───────────────┤
              ▼                               ▼               ▼
     ┌────────────────┐              ┌────────────────┐  ┌─────────────────┐
     │  Analytics     │              │ ML Forecasting  │  │ Volatility Lab  │
     │ (Order Book,   │              │ (Prophet/LSTM)  │  │ (Risk models)   │
     │ Liquidity)     │              └────────────────┘  └─────────────────┘
     └────────┬───────┘                      │                   │
              │                               └──────────┬────────┘
              ▼                                          ▼
     ┌─────────────────────────────────────────────────────────────┐
     │   Streamlit Dashboard / Power BI (Real-Time Visualizations) │
     └─────────────────────────────────────────────────────────────┘


## 🧩 Project Modules (Sections Overview)

This project is organized into several specialized “labs,” each focusing on a different area of trading analytics:

### 1. 📊 Order Book Heatmap & Liquidity Radar
- Fetches real-time order book snapshots from Binance
- Builds depth heatmaps over time
- Computes liquidity imbalance and spread metrics
- Visualizes volume clusters and market microstructure

### 2. 📈 Stock Price Forecasting (Prophet & LSTM)
- Daily OHLCV data via Yahoo Finance
- Time-series forecasting using Prophet
- LSTM deep learning model for comparison
- Interactive forecast plots in dashboard

### 3. ⚡ Volatility Prediction Model
- Computes realized volatility from high-frequency data
- ML models to predict next-day volatility
- Vol spikes detection + feature importance

### 4. 🔄 Real-Time ETL → PostgreSQL → Power BI
- Custom ETL job ingesting streaming Binance data
- Cleans, transforms, loads into PostgreSQL
- Live Power BI dashboard connected to the DB

### 5. 🌍 Alternative Data Alpha (Google Trends)
- Google Trends interest mapped to asset price behavior
- Correlation / lag analysis
- Toy strategy using spikes in search interest
- Equity curve visualization

### 6. 🧠 Sentiment-Driven Trading Strategy (Reddit + SEC)
- NLP sentiment scoring of Reddit posts
- Tone analysis of SEC filings (MD&A sections)
- Long/short strategy based on sentiment changes
- Backtesting with price data

---

Each lab is modular and independent, but all share:
- a unified data pipeline
- consistent data models
- centralized analytics utilities
- a unified dashboard UI

## 🚀 Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/) (optional, but recommended)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/doublehm/trading-lab.git
   cd trading-lab
   ```

2. **Configure Environment**
   Copy the example environment file and configure your credentials:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` to set your database credentials. If using Docker Compose, ensure `POSTGRES_*` variables are set.

### Running with Docker Compose (Recommended)

This will start the database, the web app, and the ETL worker all together.

```bash
docker-compose up --build
```

- **Web App**: Access at [http://localhost:8501](http://localhost:8501)
- **Database**: Accessible internally at `db:5432`

### Running Manually with Docker

If you prefer to run containers individually or use a local database:

1. **Build the image**
   ```bash
   docker build -t trading-lab .
   ```

2. **Run the Web App**
   ```bash
   # Using host network (Linux) to access local DB
   docker run --network="host" --env-file .env -p 8501:8501 trading-lab
   ```

3. **Run the ETL Worker**
   ```bash
   docker run --network="host" --env-file .env trading-lab python -m src.data_pipeline.etl_jobs
   ```

