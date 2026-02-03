
import pandas as pd

def get_available_dates(df):
    if df.empty or 'Date' not in df.columns:
        return []
    return sorted(df['Date'].dropna().unique())

def get_week_str(date):
    # Returns "Year-Week" string, e.g., "2025-W04"
    return date.strftime("%Y-W%U")

def get_available_weeks(df):
    if df.empty or 'Date' not in df.columns:
        return []
    df['Week'] = df['Date'].apply(get_week_str)
    return sorted(df['Week'].unique())

def filter_by_date(df, date):
    # date can be a datetime object or string
    if df.empty:
        return df
    # Ensure comparison works (timestamps)
    return df[df['Date'] == pd.to_datetime(date)]

def filter_by_week(df, week_str):
    if df.empty:
        return df
    # Ensure Week column exists
    if 'Week' not in df.columns:
        df['Week'] = df['Date'].apply(get_week_str)
    return df[df['Week'] == week_str]

def get_missing_forms_count(df):
    # Count rows where 'Cards Issued' is NaN
    # Assuming df is already filtered by date/context
    return df['Cards Issued'].isna().sum()

def get_missing_vles(df):
    # Return df of VLEs who didn't fill form
    return df[df['Cards Issued'].isna()]

def calculate_top_3(df, group_by_col, metric_col='Cards Issued'):
    # Sum metric by group
    grouped = df.groupby(group_by_col)[metric_col].sum().reset_index()
    # Sort desc
    sorted_df = grouped.sort_values(by=metric_col, ascending=False)
    return sorted_df.head(3)

def calculate_least_3(df, group_by_col, metric_col='Cards Issued'):
    # Sum metric by group
    grouped = df.groupby(group_by_col)[metric_col].sum().reset_index()
    
    # Filter out 0s to make the list useful (show low performers, not non-performers)
    # Non-performers (0/NaN) are captured in "Missing Forms" or just have 0.
    # Given the high number of NaNs/0s, showing random 0s is useless.
    # We will show the least among those who have > 0.
    filtered_grouped = grouped[grouped[metric_col] > 0]
    
    sorted_df = filtered_grouped.sort_values(by=metric_col, ascending=True)
    return sorted_df.head(3)

def aggregate_metrics(df):
    total = df['Cards Issued'].sum()
    return total
