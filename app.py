import streamlit as st
import pandas as pd

st.set_page_config(page_title="Community Reach — Volunteer Dashboard", layout="wide")
st.title("Community Reach — Volunteer Dashboard")
st.caption("Data from volunteer registration and service entry forms")

# Google Sheets URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_3Pd_ZTQTu46sOZ1-FmX7KEg5v4TOQy3xC1DM5840s8/edit?usp=sharing"

def load_data_via_pandas(url, sheet_name):
    csv_url = url.replace("/edit?usp=sharing", f"/export?format=csv&sheet={sheet_name.replace(' ', '+')}")
    try:
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading sheet '{sheet_name}': {e}")
        return pd.DataFrame()

# Load Data
volunteers_df = load_data_via_pandas(SHEET_URL, "Volunteer Database")
programs_df = load_data_via_pandas(SHEET_URL, "Program Database")

# Ensure columns are standardized and datetime-parsed
if not programs_df.empty:
    hours_col = next((col for col in programs_df.columns if "hours" in col.lower()), None)
    value_col = next((col for col in programs_df.columns if "value" in col.lower()), None)
    prog_col = next((col for col in programs_df.columns if "program" in col.lower()), None)
    date_col = next((col for col in programs_df.columns if "date" in col.lower()), None)
    fy_col = next((col for col in programs_df.columns if "fiscal" in col.lower() or "fy" in col.lower()), None)
    type_col = next((col for col in programs_df.columns if "type" in col.lower()), None)

    # Convert numeric columns safely
    if hours_col: programs_df[hours_col] = pd.to_numeric(programs_df[hours_col], errors='coerce').fillna(0)
    if value_col: programs_df[value_col] = pd.to_numeric(programs_df[value_col], errors='coerce').fillna(0)
    
    # Try to parse date and extract Month/Fiscal Year if missing
    if date_col:
        programs_df[date_col] = pd.to_datetime(programs_df[date_col], errors='coerce')
        programs_df['Month'] = programs_df[date_col].dt.strftime('%B')
        if not fy_col:
            # Fallback calculation if FY column doesn't exist
            programs_df['Fiscal Year'] = programs_df[date_col].dt.year
            fy_col = 'Fiscal Year'

# --- SIDEBAR FILTERS ---
st.sidebar.header("Global Filters")

# 1. Program Filter
if prog_col and not programs_df.empty:
    unique_progs = sorted(programs_df[prog_col].dropna().unique())
    selected_progs = st.sidebar.multiselect("Programs", unique_progs, default=unique_progs)
else:
    selected_progs = []

# 2. Volunteer Type Filter
if type_col and not programs_df.empty:
    unique_types = sorted(programs_df[type_col].dropna().unique())
    selected_types = st.sidebar.multiselect("Volunteer Type", unique_types, default=unique_types)
else:
    selected_types = []

# 3. Fiscal Year Filter
if fy_col and not programs_df.empty:
    unique_fys = sorted(programs_df[fy_col].dropna().unique(), reverse=True)
    selected_fys = st.sidebar.multiselect("Fiscal Year", unique_fys, default=unique_fys)
else:
    selected_fys = []

# --- FILTER DATA DYNAMICALLY ---
filtered_df = programs_df.copy()
if selected_progs:
    filtered_df = filtered_df[filtered_df[prog_col].isin(selected_progs)]
if selected_types:
    filtered_df = filtered_df[filtered_df[type_col].isin(selected_types)]
if selected_fys:
    filtered_df = filtered_df[filtered_df[fy_col].isin(selected_fys)]

# --- MAIN DASHBOARD NAVIGATION ---
tabs = st.tabs(["Overview", "Volunteer Lookup"])

# ================= TAB 1: OVERVIEW =================
with tabs[0]:
    st.subheader("Overview")
    
    # Calculate Metrics
    tot_vols = len(volunteers_df) if not volunteers_df.empty else 0
    tot_hours = filtered_df[hours_col].sum() if hours_col else 0
    tot_value = filtered_df[value_col].sum() if value_col else 0
    act_progs = filtered_df[prog_col].nunique() if prog_col else 0
    
    # Top KPI Metrics Cards
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Volunteers", f"{tot_vols:,}")
    m2.metric("Total Hours", f"{tot_hours:,.0f}")
    m3.metric("Total Value", f"${tot_value:,.2f}")
    m4.metric("Programs Active", f"{act_progs}")
    
    st.write("---")
    
    # Row 1 Charts
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Hours by Program")
        if prog_col and hours_col:
            chart_data = filtered_df.groupby(prog_col)[hours_col].sum().reset_index()
            st.bar_chart(chart_data, x=prog_col, y=hours_col)
            
    with c2:
        st.write("### By Volunteer Type")
        if type_col and hours_col:
            chart_data = filtered_df.groupby(type_col)[hours_col].sum().reset_index()
            st.bar_chart(chart_data, x=type_col, y=hours_col)

    # Row 2 Charts
    c3, c4 = st.columns(2)
    with c3:
        st.write("### Trend by Fiscal Year")
        if fy_col and hours_col:
            chart_data = filtered_df.groupby(fy_col)[hours_col].sum().reset_index()
            # Convert year to string to stop Streamlit from adding comma formatting to numbers
            chart_data[fy_col] = chart_data[fy_col].astype(str) 
            st.line_chart(chart_data, x=fy_col, y=hours_col)
            
    with c4:
        st.write("### Busiest Months by Program")
        if prog_col and 'Month' in filtered_df.columns:
            # Multi-index pivot setup for complex grouping
            chart_data = filtered_df.groupby(['Month', prog_col])[hours_col].sum().unstack().fillna(0)
            st.bar_chart(chart_data)

    st.write("---")
    
    # Row 3 Charts & Aggregations
    c5, c6 = st.columns(2)
    with c5:
        st.write("### How Volunteers Found Community Reach")
        found_col = next((col for col in volunteers_df.columns if "find" in col.lower() or "how" in col.lower() or "source" in col.lower()), None)
        if found_col and not volunteers_df.empty:
            source_data = volunteers_df[found_col].value_counts().reset_index()
            st.bar_chart(source_data, x=found_col, y="count")
        else:
            st.info("Ensure you have a column matching 'how found' or 'source' in your Volunteer sheet.")

    with c6:
        st.write("### Top Volunteers by Total Hours")
        vol_name_col = next((col for col in filtered_df.columns if "name" in col.lower() or "volunteer" in col.lower()), None)
        if vol_name_col and hours_col:
            top_vols = filtered_df.groupby(vol_name_col)[hours_col].sum().reset_index()
            top_vols = top_vols.sort_values(by=hours_col, ascending=False).head(10)
            st.dataframe(top_vols, use_container_width=True, hide_index=True)

# ================= TAB 2: VOLUNTEER LOOKUP =================
with tabs[1]:
    st.subheader("Volunteer Lookup")
    
    name_col = next((col for col in volunteers_df.columns if "name" in col.lower()), None)
    
    search_query = st.text_input("Search by name (type at least 2 characters):")
    
    if len(search_query) >= 2 and name_col:
        mask = volunteers_df[name_col].str.contains(search_query, case=False, na=False)
        results = volunteers_df[mask]
        
        if not results.empty:
            st.success(f"Found {len(results)} profile(s):")
            for idx, row in results.iterrows():
                with st.expander(f"👤 {row[name_col]}"):
                    st.write("**Full Profile Information:**")
                    st.dataframe(pd.DataFrame(row).T, hide_index=True)
                    
                    # Match history from program logs
                    prog_vol_name = next((col for col in programs_df.columns if "name" in col.lower() or "volunteer" in col.lower()), None)
                    if prog_vol_name:
                        history = programs_df[programs_df[prog_vol_name].str.lower() == row[name_col].lower()]
                        st.write("**Service History:**")
                        if not history.empty:
                            st.dataframe(history, hide_index=True)
                        else:
                            st.info("No logs found for this volunteer.")
        else:
            st.warning("No volunteers found matching that name.")
    else:
        st.info("Type a volunteer's name above to see their full profile and service history.")
