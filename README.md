# Quantitative Portfolio Management System

An automated, full-stack financial analytics engine built in Python to track, simulate, and analyze a Systematic Investment Plan (SIP) across a diversified mutual fund portfolio. 

This project bridges software engineering with institutional quantitative finance, autonomously ingesting daily market data and calculating risk-adjusted performance metrics.

## ⚙️ Technical Architecture
* **Data Ingestion Layer:** Utilizes the `mftool` API to dynamically resolve scheme codes and scrape historical Net Asset Value (NAV) time-series data from the Association of Mutual Funds in India (AMFI).
* **Financial Mathematics Engine:** Implements the Newton-Raphson numerical method via `scipy.optimize` to calculate precise Extended Internal Rate of Return (XIRR) for irregular cash flows.
* **Risk Analytics:** Computes institutional-grade Modern Portfolio Theory (MPT) metrics utilizing `pandas` and `numpy` vectorized operations, including Annualized Volatility, Maximum Drawdown, and Sharpe Ratios.
* **Presentation Layer:** A responsive, interactive web dashboard built with `Streamlit` and `Plotly` to visualize portfolio weight drift, capital deployment versus asset appreciation, and real-time risk evaluation.

## 📊 Core Financial Models Implemented
1. **XIRR (Extended Internal Rate of Return):** Solves the root-finding problem for $\sum_{t=0}^{N} \frac{C_t}{(1 + r)^{\frac{d_t - d_0}{365}}} = 0$
2. **Sharpe Ratio:** Evaluates risk-adjusted excess returns over a baseline 7% risk-free rate.
3. **Rupee Cost Averaging Simulation:** Algorithmically models monthly fractional unit accumulation based on historical daily closing NAVs.

## 🚀 How to Run Locally
1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Fetch the latest market data: `python mf_data_ingestion.py`
4. Launch the dashboard: `streamlit run app.py`