
# Hiive Trading Lab
A modular analytics platform designed to explore order books, liquidity, forecasting, volatility, alternative data, and sentiment-driven trading strategies. 

This project simulates the type of internal analytics tooling used by modern electronic marketplaces such as Hiive. It combines real-time data pipelines, machine learning models, and interactive dashboards to demonstrate practical insights into price discovery, liquidity dynamics, and market behavior.

## 🎯 Project Purpose

Hiive operates in a domain where price discovery, liquidity distribution, and order book transparency matter deeply. 

The purpose of this project is to:

- Demonstrate strong capabilities in **data engineering**, **machine learning**, and **market microstructure analysis**.
- Build practical tools that explore **order flow**, **liquidity imbalance**, **forecasting**, **volatility modeling**, and **sentiment analysis**.
- Show how alternative signals (Google Trends, sentiment, SEC filings) can enhance understanding of market behavior.
- Deliver the entire project in one unified app with multiple “labs,” mimicking an internal analytics platform for a trading marketplace.

This repository showcases how I would contribute value as a data engineer, quantitative analyst, or ML engineer at Hiive.

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

