"""
frontend/components/sidebar.py
FIX: City dropdown reads from stores.csv (raw data) which always has city names.
Falls back through multiple CSVs if stores.csv doesn't have what we need.
Button text forced white.
"""

import streamlit as st
import pandas as pd
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output")
RAW_DIR    = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")

TEAL  = "#0d9488"
SLATE = "#0f172a"


@st.cache_data(ttl=300, show_spinner=False)
def _load_sidebar_data() -> dict:
    """
    Loads data for filter dropdowns.
    City source priority:
      1. data/raw/stores.csv           ← has city + store_id + store_name
      2. output/full_pipeline_output.csv  ← has city in most rows
      3. output/demand_forecast_output.csv
      4. output/dashboard_output.csv  (may lack city)
    """
    result = {"stores": pd.DataFrame(), "cities": [], "products": []}

    # ── 1. stores.csv — best source ──────────────────────────────────────────
    stores_path = os.path.join(RAW_DIR, "stores.csv")
    if os.path.exists(stores_path):
        try:
            result["stores"] = pd.read_csv(stores_path)
        except Exception:
            pass

    if not result["stores"].empty and "city" in result["stores"].columns:
        result["cities"] = sorted(result["stores"]["city"].dropna().unique().tolist())

    # ── 2. Fallback through output CSVs for cities ────────────────────────────
    if not result["cities"]:
        for fname in ["full_pipeline_output.csv","demand_forecast_output.csv","dashboard_output.csv"]:
            path = os.path.join(OUTPUT_DIR, fname)
            if not os.path.exists(path):
                continue
            try:
                # Only read city column for speed
                df = pd.read_csv(path, usecols=["city"])
                if "city" in df.columns:
                    cities = sorted(df["city"].dropna().unique().tolist())
                    if cities:
                        result["cities"] = cities
                        break
            except Exception:
                continue

    # ── 3. Products from dashboard or forecast ────────────────────────────────
    for fname in ["dashboard_output.csv","demand_forecast_output.csv"]:
        path = os.path.join(OUTPUT_DIR, fname)
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path, usecols=["product_id"])
            result["products"] = sorted(df["product_id"].dropna().unique().astype(str).tolist())
            break
        except Exception:
            continue

    return result


def render_sidebar(nav_items: list, default: str = None) -> tuple:
    data    = _load_sidebar_data()
    stores  = data["stores"]
    cities  = data["cities"]
    products = data["products"]

    st.markdown(f"""
<style>

[data-testid="stSidebar"] {{
    background: {SLATE} !important;
}}

/* 🔥 FORCE ALL TEXT VISIBLE */
[data-testid="stSidebar"] * {{
    color: #f1f5f9 !important;
}}

/* Labels */
[data-testid="stSidebar"] label {{
    font-weight: 500 !important;
    color: #e2e8f0 !important;
}}

/* Selectbox FIX */
[data-testid="stSidebar"] .stSelectbox > div {{
    background: #020617 !important;
    border: 1px solid {TEAL} !important;
    border-radius: 6px !important;
}}

[data-testid="stSidebar"] .stSelectbox div {{
    color: #f8fafc !important;
}}

/* Dropdown menu */
div[role="listbox"] {{
    background: #020617 !important;
    color: white !important;
}}

/* Radio buttons */
[data-testid="stSidebar"] .stRadio label {{
    color: #cbd5e1 !important;
}}

[data-testid="stSidebar"] .stRadio label:hover {{
    color: #5eead4 !important;
    background: rgba(13,148,136,0.15) !important;
}}

/* Buttons */
[data-testid="stSidebar"] button {{
    background: #020617 !important;
    color: white !important;
    border: 1px solid {TEAL} !important;
}}

[data-testid="stSidebar"] button:hover {{
    background: {TEAL} !important;
    color: white !important;
}}

</style>
""", unsafe_allow_html=True)

    with st.sidebar:
        # Brand
        st.markdown("""
        <div class="sb-brand">
            <div class="sb-icon">🏺</div>
            <div>
                <div class="sb-name">SmartDemand</div>
                <div class="sb-sub">Williams Sonoma</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            f'<div class="sb-pill">👤 {st.session_state.get("username","User")} '
            f'· {st.session_state.get("role","").title()}</div>',
            unsafe_allow_html=True
        )

        # Nav
        st.markdown('<span class="sb-sec">Navigation</span>', unsafe_allow_html=True)
        selected = st.radio(
            "nav", nav_items,
            index=nav_items.index(default) if default in nav_items else 0,
            label_visibility="collapsed",
            key="sidebar_nav"
        )

        # Filters
        filters = {"store": None, "city": None, "product": None, "date_range": None}

        if cities:
            st.markdown('<span class="sb-sec">🔍 Filters</span>', unsafe_allow_html=True)

            # ── City ─────────────────────────────────────────────────────────
            sel_city = st.selectbox("City", ["All Cities"] + cities, key="filter_city")
            filters["city"] = None if sel_city == "All Cities" else sel_city

            # ── Store ─────────────────────────────────────────────────────────
            if not stores.empty and "store_id" in stores.columns:
                sdf = stores.copy()
                if filters["city"] and "city" in sdf.columns:
                    sdf = sdf[sdf["city"] == filters["city"]]
                sdf = sdf.drop_duplicates(subset=["store_id"])
                has_name = "store_name" in sdf.columns
                if has_name:
                    labels = [f"{row.store_id} — {row.store_name}" for row in sdf.itertuples()]
                    id_map = {f"{row.store_id} — {row.store_name}": str(row.store_id) for row in sdf.itertuples()}
                else:
                    labels = sorted(sdf["store_id"].dropna().unique().astype(str).tolist())
                    id_map = {s: s for s in labels}
                sel_s = st.selectbox("Store", ["All Stores"] + labels, key="filter_store")
                filters["store"] = None if sel_s == "All Stores" else id_map.get(sel_s, sel_s)

            # ── Product ───────────────────────────────────────────────────────
            if products:
                sel_p = st.selectbox("Product ID", ["All Products"] + products, key="filter_product")
                filters["product"] = None if sel_p == "All Products" else sel_p

            # ── Date range ────────────────────────────────────────────────────
            # Read min/max date from whichever CSV has dates
            date_range_loaded = False
            for fname in ["demand_forecast_output.csv","full_pipeline_output.csv","dashboard_output.csv"]:
                path = os.path.join(OUTPUT_DIR, fname)
                if not os.path.exists(path): continue
                try:
                    df_dates = pd.read_csv(path, usecols=["date"])
                    d_col = pd.to_datetime(df_dates["date"], errors="coerce")
                    min_d, max_d = d_col.min().date(), d_col.max().date()
                    dr = st.date_input("Date Range", value=(min_d, max_d),
                                       min_value=min_d, max_value=max_d, key="filter_date")
                    filters["date_range"] = dr if len(dr) == 2 else None
                    date_range_loaded = True
                    break
                except Exception:
                    continue

        else:
            st.caption("⚠️ Run main.py to populate city filters")

        st.markdown("---")
        if st.button("🚪 Logout", key="sidebar_logout"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    return selected, filters
