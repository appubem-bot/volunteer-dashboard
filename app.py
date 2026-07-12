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

# Initialize columns to None
hours_col = value_col = prog_col = date_col = fy_col = type_col = None

# Safely extract columns if dataframe is populated
if not programs_df.empty:
    hours_col = next((col for col in programs_df.columns if "hours" in col.lower() or "hrs" in col.lower()), None)
    value_col = next((col for col in programs_df.columns if "value" in col.lower() or "economic" in col.lower()), None)
    prog_col = next((col for col in programs_df.columns if "program" in col.lower() or "proj" in col.lower()), None)
    date_col = next((col for col in programs_df.columns if "date" in col.lower() or "time" in col.lower()), None)
    fy_col = next((col for col in programs_df.columns if "fiscal" in col.lower() or "fy" in col.lower()), None)
    type_col = next((col for col in programs_df.columns if "type" in col.lower() or "status" in col.lower()), None)

    # Force format conversions safely
    if hours_col: 
        programs_df[hours_col] = pd.to_numeric(programs_df[hours_col], errors='coerce').fillna(0)
    if value_col: 
        programs_df[value_col] = pd.to_numeric(programs_df[value_col], errors='coerce').fillna(0)
    if date_col:
        programs_df[date_col] = pd.to_datetime(programs_df[date_col], errors='coerce')
        programs_df['Month'] = programs_df[date_col].dt.strftime('%B')
        if not fy_col:
            programs_df['Fiscal Year'] = programs_df[date_col].dt.year.fillna(2026).astype(int).astype(str)
            fy_col = 'Fiscal Year'
    elif fy_col:
        programs_df[fy_col] = programs_df[fy_col].astype(str)

# --- SIDEBAR FILTERS WITH VALUE CHECKS ---
st.sidebar.header("Global Filters")

# --- SIDEBAR FILTERS WITH VALUE CHECKS ---
st.sidebar.header("Global Filters")

selected_progs = []
if prog_col and not programs_df.empty:
    unique_progs = sorted(list(programs_df[prog_col].dropna().unique()))
    selected_progs = st.sidebar.multiselect("Programs", unique_progs, default=unique_progs)

selected_types = []
if type_col and not programs_df.empty:
    unique_types = sorted(list(programs_df[type_col].dropna().unique()))
    selected_types = st.sidebar.multiselect("Volunteer Type", unique_types, default=unique_types)

selected_fys = []
if fy_col and not programs_df.empty:
    unique_fys = sorted(list(programs_df[fy_col].dropna().unique()), reverse=True)
    selected_fys = st.sidebar.multiselect("Fiscal Year", unique_fys, default=unique_fys)
filtered_df = programs_df.copy() if not programs_df.empty else pd.DataFrame()
if not filtered_df.empty:
    if selected_progs and prog_col:
        filtered_df = filtered_df[filtered_df[prog_col].isin(selected_progs)]
    if selected_types and type_col:
        filtered_df = filtered_df[filtered_df[type_col].isin(selected_types)]
    if selected_fys and fy_col:
        filtered_df = filtered_df[filtered_df[fy_col].isin(selected_fys)]

# --- MAIN DASHBOARD NAVIGATION ---
tabs = st.tabs(["Overview", "Volunteer Lookup"])

# ================= TAB 1: OVERVIEW =================
with tabs[0]:
    st.subheader("Overview")
    
    # Safely Calculate KPI Numbers
    tot_vols = len(volunteers_df) if not volunteers_df.empty else 0
    tot_hours = filtered_df[hours_col].sum() if (hours_col and not filtered_df.empty) else 0
    tot_value = filtered_df[value_col].sum() if (value_col and not filtered_df.empty) else 0
    act_progs = filtered_df[prog_col].nunique() if (prog_col and not filtered_df.empty) else 0
    
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
        if prog_col and hours_col and not filtered_df.empty:
            chart_data = filtered_df.groupby(prog_col)[hours_col].sum().to_frame()
            st.bar_chart(chart_data)
        else:
            st.info("Missing program tracking data.")
            
    with c2:
        st.write("### By Volunteer Type")
        if type_col and hours_col and not filtered_df.empty:
            chart_data = filtered_df.groupby(type_col)[hours_col].sum().to_frame()
            st.bar_chart(chart_data)
        else:
            st.info("Volunteer type data unavailable in program history.")

    # Row 2 Charts
    c3, c4 = st.columns(2)
    with c3:
        st.write("### Trend by Fiscal Year")
        if fy_col and hours_col and not filtered_df.empty:
            chart_data = filtered_df.groupby(fy_col)[hours_col].sum().to_frame()
            st.line_chart(chart_data)
        else:
            st.info("Fiscal Year tracking data unavailable.")
            
    with c4:
        st.write("### Busiest Months by Program")
        if prog_col and 'Month' in filtered_df.columns and hours_col and not filtered_df.empty:
            chart_data = filtered_df.groupby(['Month', prog_col])[hours_col].sum().unstack().fillna(0)
            st.bar_chart(chart_data)
        else:
            st.info("Date/Month entries unavailable.")

    st.write("---")
    
    # Row 3 Charts & Aggregations
    c5, c6 = st.columns(2)
    with c5:
        st.write("### How Volunteers Found Community Reach")
        found_col = next((col for col in volunteers_df.columns if "find" in col.lower() or "how" in col.lower() or "source" in col.lower()), None) if not volunteers_df.empty else None
        if found_col and not volunteers_df.empty:
            source_data = volunteers_df[found_col].value_counts().to_frame()
            st.bar_chart(source_data)
        else:
            st.info("Add a 'How Found' column to your Volunteer Database to populate this chart.")

    with c6:
        st.write("### Top Volunteers by Total Hours")
        vol_name_col = next((col for col in filtered_df.columns if "name" in col.lower() or "volunteer" in col.lower()), None) if not filtered_df.empty else None
        if vol_name_col and hours_col and not filtered_df.empty:
            top_vols = filtered_df.groupby(vol_name_col)[hours_col].sum().reset_index()
            top_vols = top_vols.sort_values(by=hours_col, ascending=False).head(10)
            st.dataframe(top_vols, use_container_width=True, hide_index=True)
        else:
            st.info("Volunteer names not found in the activity sheet logs.")

# ================= TAB 2: VOLUNTEER LOOKUP =================
with tabs[1]:
    st.subheader("Volunteer Lookup")
    
    name_col = next((col for col in volunteers_df.columns if "name" in col.lower()), None) if not volunteers_df.empty else None
    search_query = st.text_input("Search by name (type at least 2 characters):")
    
    if len(search_query) >= 2 and name_col:
        mask = volunteers_df[name_col].str.contains(search_query, case=False, na=False)
        results = volunteers_df[mask]
        
        if not results.empty:
            st.success(f"Found {len(results)} profile(s):")
            for idx, row in results.iterrows():
                with st.expander(f"👤 {row[name_col]}"):
                    st.dataframe(pd.DataFrame(row).T, hide_index=True)
                    
                    prog_vol_name = next((col for col in programs_df.columns if "name" in col.lower() or "volunteer" in col.lower()), None) if not programs_df.empty else None
                    if prog_vol_name:
                        history = programs_df[programs_df[prog_vol_name].str.lower() == row[name_col].lower()]
                        st.write("**Service History:**")
                        if not history.empty:
                            st.dataframe(history, hide_index=True)
                        else:
                            st.info("No service logs found for this individual.")
        else:
            st.warning("No volunteers found matching that name.")
    else:
        st.info("Type a volunteer's name above to see their full profile and service history.")
