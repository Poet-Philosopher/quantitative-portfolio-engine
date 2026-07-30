import os
import sys
import time
import difflib
from datetime import datetime, timedelta
import pandas as pd
from mftool import Mftool

FUND_NAMES = [
    "Axis Gold",
    "Axis Short Duration",
    "WhiteOak Capital Arbitrage",
    "Nippon India Large Cap",
    "Bandhan Small Cap",
]
EXCLUDE_KEYWORDS = ["idcw", "dividend"]
REGULAR_PLAN_KEYWORDS = ["regular"]
CSV_PATH = "mutual_fund_nav_history.csv"

def _normalize_search_results(raw) -> dict:
    if not raw: return {}
    if isinstance(raw, dict): return {str(k): str(v) for k, v in raw.items()}
    if isinstance(raw, list):
        return {str(i.get("schemeCode") or i.get("code")): str(i.get("schemeName") or i.get("name")) 
                for i in raw if isinstance(i, dict) and (i.get("schemeCode") or i.get("code"))}
    return {}

def _score_candidate(fund_name: str, candidate_name: str) -> float:
    lower_candidate = candidate_name.lower()
    if any(bad in lower_candidate for bad in EXCLUDE_KEYWORDS + REGULAR_PLAN_KEYWORDS): return -1.0
    if "growth" not in lower_candidate or "direct" not in lower_candidate: return -1.0
    return difflib.SequenceMatcher(None, fund_name.lower(), lower_candidate).ratio()

def find_best_scheme_code(mf: Mftool, fund_name: str):
    candidates = _normalize_search_results(mf.search_schemes(fund_name))
    if not candidates:
        shortened = " ".join(fund_name.split()[:-1])
        if shortened: candidates = _normalize_search_results(mf.search_schemes(shortened))
    if not candidates: return None

    scored = [(code, name, _score_candidate(fund_name, name)) for code, name in candidates.items()]
    scored = [c for c in scored if c[2] > 0]
    if not scored: return None
    
    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[0][0], scored[0][1]

def setup_scheme_codes(mf: Mftool, fund_names: list[str]) -> dict:
    resolved = {}
    for fund_name in fund_names:
        result = find_best_scheme_code(mf, fund_name)
        if result:
            resolved[fund_name] = {"code": result[0], "matched_name": result[1]}
    return resolved

def fetch_historical_nav(mf: Mftool, scheme_code: str, start_date: datetime, end_date: datetime) -> pd.Series:
    start_str = start_date.strftime("%d-%m-%Y")
    end_str = end_date.strftime("%d-%m-%Y")
    raw_data = mf.get_scheme_historical_nav_for_dates(scheme_code, start_str, end_str)
    
    # 1. Safely handle whatever unpredictable format the API returns
    if isinstance(raw_data, dict): 
        df = pd.DataFrame(raw_data.get("data", []))
    elif isinstance(raw_data, list):
        df = pd.DataFrame(raw_data)
    else:
        df = pd.DataFrame()

    if df.empty: 
        return pd.Series(dtype=float)

    # 2. FIXED: Force all column names to be strings before applying .lower()
    df.columns = [str(c).lower() for c in df.columns]

    # 3. FIXED: If the API returned a text error instead of a table, it won't have a 'date' column
    if "date" not in df.columns or "nav" not in df.columns:
        print(f"    -> No NAV published yet for {start_str}")
        return pd.Series(dtype=float)

    # Clean and format the valid data
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    
    return df.dropna(subset=["date", "nav"]).sort_values("date").set_index("date")["nav"]

def build_nav_dataframe(fund_names=FUND_NAMES):
    mf = Mftool()
    resolved = setup_scheme_codes(mf, fund_names)
    
    end_date = datetime.today()
    existing_df = pd.DataFrame()
    start_date = end_date - timedelta(days=365 * 3)

    if os.path.exists(CSV_PATH):
        existing_df = pd.read_csv(CSV_PATH, parse_dates=["date"], index_col="date")
        if not existing_df.empty:
            start_date = existing_df.index.max() + timedelta(days=1)
            print(f"Found cached data up to {existing_df.index.max().date()}. Fetching delta...")

    if start_date > end_date:
        print("Data is already up to date for today. Skipping fetch.")
        return existing_df

    series_by_fund = {}
    for fund_name, info in resolved.items():
        print(f"Fetching delta for '{fund_name}'...")
        series_by_fund[fund_name] = fetch_historical_nav(mf, info["code"], start_date, end_date)
        time.sleep(0.5) 

    # FIXED: Drop empty columns to avoid deprecation warnings
    new_data = pd.DataFrame(series_by_fund).dropna(axis=1, how='all')
    
    # FIXED: Only concatenate if there is actually new data downloaded
    if not new_data.empty:
        if not existing_df.empty:
            merged = pd.concat([existing_df, new_data])
            merged = merged[~merged.index.duplicated(keep='last')]
        else:
            merged = new_data
    else:
        merged = existing_df
        print("No new NAV data available yet. Keeping existing history.")

    if not merged.empty:
        # FIXED: Explicitly name the index 'date' so it is never lost in the CSV
        merged.index.name = "date"
        merged = merged.sort_index().ffill().dropna(how="all")
        merged.to_csv(CSV_PATH, index_label="date")
        print(f"Saved optimized NAV history to {CSV_PATH}")
        
    return merged

if __name__ == "__main__":
    build_nav_dataframe()