# Distributed Real-Time Fixed Income & Derivatives Risk Engine

A high-performance, event-driven risk management system for monitoring portfolios of Fixed-Rate Bonds and Interest Rate Swaps in real-time.

![Architecture](docs/architecture.png)

## 🎯 Project Overview

This system demonstrates production-grade patterns for building financial risk infrastructure:

- **Real-Time Processing**: Sub-100ms latency from market update to risk calculation
- **Dual-Curve Framework**: Post-2008 standard for accurate swap valuation using QuantLib
- **Event-Driven Architecture**: Apache Kafka for scalable data distribution
- **Microservices Design**: Independent, horizontally scalable services
- **Portfolio Aggregation**: Redis-based Map-Reduce for desk-level risk views

### Key Features

✅ **Market Data Simulation**: Python generator replays historical yield curves into Kafka  
✅ **Instrument Repository**: FastAPI-based "Golden Source" for bonds and swaps  
✅ **Risk Calculations**: DV01 (parallel sensitivity) and KRD (key rate duration)  
✅ **Real-Time Dashboard**: Streamlit UI with 2-second refresh  
✅ **Horizontal Scalability**: Stateless workers enable linear throughput scaling  

---

## 🏗️ Architecture

### System Components

```
┌─────────────────┐     ┌──────────────────────────────────┐
│  Market Data    │────>│  Kafka: yield_curve_ticks        │
│  Feed Generator │     └──────────────────────────────────┘
└─────────────────┘                    │
                                       │ (Consumer Group)
                                       ├──────┬──────┬──────┐
                                       ▼      ▼      ▼      ▼
                               ┌─────────────────────────────┐
                               │  Risk Workers (QuantLib)    │
                               │  • Dual-curve bootstrap     │
                               │  • NPV calculation          │
                               │  • DV01 & KRD computation   │
                               └─────────────────────────────┘
                                       │
                                       ▼
                               ┌─────────────────────────────┐
                               │  Redis (Aggregation Layer)  │
                               │  • Per-trade risk storage   │
                               │  • Portfolio-level sums     │
                               │  • Pub/Sub notifications    │
                               └─────────────────────────────┘
                                       │
                                       ▼
                               ┌─────────────────────────────┐
                               │  Streamlit Dashboard        │
                               │  • Real-time metrics        │
                               │  • KRD visualization        │
                               │  • Type/currency breakdown  │
                               └─────────────────────────────┘

┌─────────────────┐
│ Security Master │ <──── (Startup: Load portfolio)
│ (PostgreSQL)    │
└─────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Streaming** | Apache Kafka 3.x | Event distribution, backpressure control |
| **API** | FastAPI 0.104+ | Instrument reference data service |
| **Database** | PostgreSQL 15+ | Persistent instrument storage |
| **Cache** | Redis 7+ | Low-latency risk aggregation |
| **Pricing** | QuantLib 1.32+ | Industry-standard fixed income library |
| **Language** | Python 3.11+ | Primary development language |
| **Orchestration** | Docker Compose | Local development environment |
| **Dashboard** | Streamlit 1.28+ | Real-time visualization |

