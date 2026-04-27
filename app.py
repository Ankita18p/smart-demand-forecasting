"""
app.py — Streamlit entry point
Handles routing: Login → Admin Dashboard or Data Reviewer Dashboard
"""

import streamlit as st

st.set_page_config(
    page_title="SmartDemand | Williams Sonoma",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── session state defaults ─────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "role" not in st.session_state:
    st.session_state.role = None
if "username" not in st.session_state:
    st.session_state.username = None

# ── routing ────────────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    from frontend.pages.login import show_login
    show_login()
elif st.session_state.role == "admin":
    from frontend.pages.admin_dashboard import show_admin_dashboard
    show_admin_dashboard()
elif st.session_state.role == "reviewer":
    from frontend.pages.data_reviewer import show_reviewer_dashboard
    show_reviewer_dashboard()