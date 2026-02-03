
import pandas as pd
import requests
from io import StringIO
from datetime import datetime
import streamlit as st
from data_config import BASE_URL, SDM_MAPPING

@st.cache_data(ttl=300)  # Cache data for 5 minutes
def fetch_sheet_data(gid):
    url = f"{BASE_URL}{gid}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        return df
    except Exception as e:
        print(f"Error fetching GID {gid}: {e}")
        return pd.DataFrame()

def parse_date(date_str):
    try:
        # Assuming format "26 Jan" and current year 2025
        # We need to handle the year dynamically if possible, or just assume 2025
        # Since the prompt implies recent data, 2025 is a safe bet for Jan/Feb dates.
        current_year = datetime.now().year
        # If we are in early 2025 and data is "Dec", it might be 2024. 
        # But for now, let's keep it simple.
        dt = datetime.strptime(f"{date_str} {current_year}", "%d %b %Y")
        return dt
    except ValueError:
        return None

def fetch_all_data():
    all_dfs = []
    
    for sdm_name, smos in SDM_MAPPING.items():
        for smo_info in smos:
            smo_name = smo_info["smo_name"]
            gid = smo_info["gid"]
            
            df = fetch_sheet_data(gid)
            if not df.empty:
                # Ensure we have the SDM column
                df['SDM'] = sdm_name
                # Ensure we have the SMO column from config if missing or normalize it
                if 'SMO Name' not in df.columns:
                     df['SMO Name'] = smo_name
                
                all_dfs.append(df)
    
    if not all_dfs:
        return pd.DataFrame()
    
    combined_df = pd.concat(all_dfs, ignore_index=True)
    return process_data(combined_df)

def process_data(df):
    # Identify static columns
    static_cols = ['Sr No', 'CSC ID', 'VLE Name', 'VLE Contact Number', 'SMO', 'SMO Name', 'SDM']
    
    # Identify date columns (columns that are not static)
    date_cols = [c for c in df.columns if c not in static_cols]
    
    # Filter out columns that might be junk (unnamed, empty)
    valid_date_cols = []
    for col in date_cols:
        # check if it looks like a date "DD Mon"
        if parse_date(col):
            valid_date_cols.append(col)
            
    # Melt the dataframe
    # We want: SDM, SMO Name, VLE Name, VLE Contact Number, Date, Count
    
    # Select only relevant columns
    cols_to_keep = [c for c in static_cols if c in df.columns] + valid_date_cols
    df = df[cols_to_keep]
    
    melted_df = df.melt(
        id_vars=[c for c in cols_to_keep if c in static_cols],
        value_vars=valid_date_cols,
        var_name='Date_Str',
        value_name='Cards Issued'
    )
    
    # Convert Date_Str to datetime
    melted_df['Date'] = melted_df['Date_Str'].apply(parse_date)
    
    # Convert Cards Issued to numeric (coerce errors to NaN)
    melted_df['Cards Issued'] = pd.to_numeric(melted_df['Cards Issued'], errors='coerce')
    
    # "Filled Form" Logic:
    # If 'Cards Issued' is NaN, it means they didn't fill the form (according to prompt interpretation).
    # If it is 0, they filled it but issued 0. 
    # However, CSV often treats empty cells as NaN. 
    # If the user says "how many vle doesnt fill the form", and the sheet has NaNs for empty cells, 
    # then NaN = Not Filled.
    
    return melted_df

