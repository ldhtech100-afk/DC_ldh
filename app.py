
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

from data_loader import fetch_all_data
from utils import (
    get_available_dates, get_available_weeks, get_week_str,
    filter_by_date, filter_by_week,
    get_missing_forms_count, get_missing_vles,
    calculate_top_3, calculate_least_3, aggregate_metrics
)
from data_config import SDM_MAPPING

st.set_page_config(page_title="Card Issue Dashboard", layout="wide")

# Load Data
with st.spinner("Loading data from Google Sheets..."):
    df = fetch_all_data()

if df.empty:
    st.error("No data available. Please check the Google Sheet connections.")
    st.stop()

# Helper to get latest date if today is not available
available_dates = get_available_dates(df)
latest_date = available_dates[-1] if available_dates else datetime.now()
try:
    today = datetime.now()
    # If today is not in data, use latest available date for demo purposes?
    # Or strict 'today'? User said "list of the vle name that doesnt fill the form of today".
    # If data is not updated for today, then everyone hasn't filled it? 
    # Or the column doesn't exist.
    # If column doesn't exist, we can't check.
    # Let's use latest_date as 'Today' (Conceptually Current Reporting Date)
    current_date = latest_date
except:
    current_date = datetime.now()

# Sidebar
st.sidebar.title("Navigation")
dashboard_type = st.sidebar.radio("Select Dashboard", ["DC Dashboard", "SDM Dashboard", "SMO Dashboard"])

# --- DC DASHBOARD ---
if dashboard_type == "DC Dashboard":
    st.title("DC Dashboard")
    
    # Top Metrics
    total_issued = df['Cards Issued'].sum()
    
    # Calculate period metrics
    # Today (Current Reporting Date)
    df_today = filter_by_date(df, current_date)
    today_issued = df_today['Cards Issued'].sum()
    
    # This Week
    current_week_str = get_week_str(current_date)
    df_week = filter_by_week(df, current_week_str)
    week_issued = df_week['Cards Issued'].sum()
    
    # This Month
    # Naive month filter
    df_month = df[df['Date'].dt.month == current_date.month]
    month_issued = df_month['Cards Issued'].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cards Issued (All Time)", f"{total_issued:,.0f}")
    col2.metric(f"Issued Today ({current_date.strftime('%d %b')})", f"{today_issued:,.0f}")
    col3.metric("Issued This Week", f"{week_issued:,.0f}")
    col4.metric("Issued This Month", f"{month_issued:,.0f}")
    
    st.divider()
    
    # SDM Performance
    st.subheader("SDM Performance Ranking")
    sdm_ranking = df.groupby('SDM')['Cards Issued'].sum().reset_index().sort_values('Cards Issued', ascending=False)
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("Most Issues by SDM")
        if not sdm_ranking.empty:
            best_sdm = sdm_ranking.iloc[0]
            st.success(f"🏆 {best_sdm['SDM']}: {best_sdm['Cards Issued']:,.0f}")
    with c2:
        st.write("Least Issues by SDM")
        if not sdm_ranking.empty:
            worst_sdm = sdm_ranking.iloc[-1]
            st.error(f"⚠️ {worst_sdm['SDM']}: {worst_sdm['Cards Issued']:,.0f}")

    # Graph
    st.subheader("Timeline of Card Issues by SDM")
    # Group by Date and SDM
    timeline_df = df.groupby(['Date', 'SDM'])['Cards Issued'].sum().reset_index()
    if not timeline_df.empty:
        fig = px.line(timeline_df, x='Date', y='Cards Issued', color='SDM', markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
    st.divider()
    
    # Drill Down: Missing Forms
    st.subheader("Missing Forms Drill-Down")
    st.info("Click on SDM > SMO to see VLEs who haven't filled the form for the selected date.")
    
    date_filter = st.date_input("Select Date for Missing Forms", current_date)
    date_filter = pd.to_datetime(date_filter)
    
    df_date_filtered = filter_by_date(df, date_filter)
    
    # Iterate SDMs
    for sdm in SDM_MAPPING.keys():
        sdm_df = df_date_filtered[df_date_filtered['SDM'] == sdm]
        missing_count = get_missing_forms_count(sdm_df)
        
        with st.expander(f"{sdm} (Missing Forms: {missing_count})"):
            # Iterate SMOs in this SDM
            smos_in_sdm = [s['smo_name'] for s in SDM_MAPPING[sdm]]
            for smo in smos_in_sdm:
                smo_df = sdm_df[sdm_df['SMO Name'] == smo]
                smo_missing_count = get_missing_forms_count(smo_df)
                
                with st.expander(f"{smo} (Missing: {smo_missing_count})"):
                    missing_vles = get_missing_vles(smo_df)
                    if not missing_vles.empty:
                        st.table(missing_vles[['VLE Name', 'VLE Contact Number']])
                    else:
                        st.write("All VLEs filled the form!")

    st.divider()
    
    # Top/Least 3 Tables
    st.subheader("Top & Least 3 Performers (VLEs)")
    
    tab1, tab2, tab3 = st.tabs(["Specific Date", "Specific Week", "All Time"])
    
    with tab1:
        d_sel = st.date_input("Select Date", current_date, key="dc_top_date")
        d_sel = pd.to_datetime(d_sel)
        df_d = filter_by_date(df, d_sel)
        
        c1, c2 = st.columns(2)
        with c1:
            st.write("Top 3 Cards Issued")
            st.table(calculate_top_3(df_d, 'VLE Name'))
        with c2:
            st.write("Least 3 Cards Issued") # Should we exclude NaNs?
            st.table(calculate_least_3(df_d, 'VLE Name'))
            
    with tab2:
        w_avail = get_available_weeks(df)
        if w_avail:
            w_sel = st.selectbox("Select Week", w_avail, index=len(w_avail)-1, key="dc_top_week")
            df_w = filter_by_week(df, w_sel)
            c1, c2 = st.columns(2)
            with c1:
                st.write("Top 3 Cards Issued")
                st.table(calculate_top_3(df_w, 'VLE Name'))
            with c2:
                st.write("Least 3 Cards Issued")
                st.table(calculate_least_3(df_w, 'VLE Name'))
        else:
            st.write("No week data available.")

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.write("Top 3 Highest Number of Card Issue")
            st.table(calculate_top_3(df, 'VLE Name'))
        with c2:
            st.write("Least 3 Number of Card Issue")
            st.table(calculate_least_3(df, 'VLE Name'))


# --- SDM DASHBOARD ---
elif dashboard_type == "SDM Dashboard":
    st.title("SDM Dashboard")
    
    selected_sdm = st.selectbox("Select SDM", list(SDM_MAPPING.keys()))
    
    # Filter data for SDM
    df_sdm = df[df['SDM'] == selected_sdm]
    
    if df_sdm.empty:
        st.warning("No data for this SDM.")
    else:
        # Metrics
        # Missing forms today
        df_today = filter_by_date(df_sdm, current_date)
        missing_today = get_missing_forms_count(df_today)
        
        st.metric("VLEs Not Filling Form (Today)", missing_today)
        
        # List of VLEs not filling form today
        st.subheader(f"VLEs Missing Form on {current_date.strftime('%d %b')}")
        missing_vles = get_missing_vles(df_today)
        if not missing_vles.empty:
            st.dataframe(missing_vles[['VLE Name', 'SMO Name', 'VLE Contact Number']])
        else:
            st.success("All VLEs filled the form today!")
            
        st.divider()
        
        # Drill Down (SMO -> VLE)
        st.subheader("Drill Down: SMO Status")
        for smo in df_sdm['SMO Name'].unique():
            smo_df = df_today[df_today['SMO Name'] == smo]
            miss_count = get_missing_forms_count(smo_df)
            with st.expander(f"{smo} (Missing: {miss_count})"):
                miss_vle_smo = get_missing_vles(smo_df)
                if not miss_vle_smo.empty:
                    st.table(miss_vle_smo[['VLE Name', 'VLE Contact Number']])
                else:
                    st.write("No missing forms.")

        st.divider()
        
        # Top/Least Tables (Within SDM)
        st.subheader("Performance Tables")
        
        tab1, tab2, tab3 = st.tabs(["Specific Date", "Specific Week", "All Time"])
        
        with tab1:
            d_sel = st.date_input("Select Date", current_date, key="sdm_date")
            d_sel = pd.to_datetime(d_sel)
            df_d = filter_by_date(df_sdm, d_sel)
            c1, c2 = st.columns(2)
            c1.table(calculate_top_3(df_d, 'VLE Name'))
            c2.table(calculate_least_3(df_d, 'VLE Name'))
            
        with tab2:
            w_avail = get_available_weeks(df_sdm)
            if w_avail:
                w_sel = st.selectbox("Select Week", w_avail, index=len(w_avail)-1, key="sdm_week")
                df_w = filter_by_week(df_sdm, w_sel)
                c1, c2 = st.columns(2)
                c1.table(calculate_top_3(df_w, 'VLE Name'))
                c2.table(calculate_least_3(df_w, 'VLE Name'))
                
        with tab3:
            c1, c2 = st.columns(2)
            c1.table(calculate_top_3(df_sdm, 'VLE Name'))
            c2.table(calculate_least_3(df_sdm, 'VLE Name'))

# --- SMO DASHBOARD ---
elif dashboard_type == "SMO Dashboard":
    st.title("SMO Dashboard")
    
    # Get all SMOs
    all_smos = sorted(df['SMO Name'].dropna().unique())
    selected_smo = st.selectbox("Select SMO", all_smos)
    
    df_smo = df[df['SMO Name'] == selected_smo]
    
    if df_smo.empty:
        st.warning("No data for this SMO.")
    else:
        # Metrics
        df_today = filter_by_date(df_smo, current_date)
        missing_today = get_missing_forms_count(df_today)
        
        st.metric("VLEs Not Filling Form (Today)", missing_today)
        
        st.subheader("Each VLE Card Issue Status")
        st.dataframe(df_today[['VLE Name', 'Cards Issued']].fillna("Not Filled"))
        
        st.divider()
        
        # Top/Least
        st.subheader("Performance Tables")
        
        tab1, tab2, tab3 = st.tabs(["Specific Date", "Specific Week", "All Time"])
        
        with tab1:
            d_sel = st.date_input("Select Date", current_date, key="smo_date")
            d_sel = pd.to_datetime(d_sel)
            df_d = filter_by_date(df_smo, d_sel)
            c1, c2 = st.columns(2)
            c1.write("Top 3")
            c1.table(calculate_top_3(df_d, 'VLE Name'))
            c2.write("Least 3")
            c2.table(calculate_least_3(df_d, 'VLE Name'))
            
        with tab2:
            w_avail = get_available_weeks(df_smo)
            if w_avail:
                w_sel = st.selectbox("Select Week", w_avail, index=len(w_avail)-1, key="smo_week")
                df_w = filter_by_week(df_smo, w_sel)
                c1, c2 = st.columns(2)
                c1.write("Top 3")
                c1.table(calculate_top_3(df_w, 'VLE Name'))
                c2.write("Least 3")
                c2.table(calculate_least_3(df_w, 'VLE Name'))
        
        with tab3:
            c1, c2 = st.columns(2)
            c1.write("Top 3 (Highest Number)")
            c1.table(calculate_top_3(df_smo, 'VLE Name'))
            c2.write("Least 3 (Least Number)")
            c2.table(calculate_least_3(df_smo, 'VLE Name'))

