import streamlit as st
import pandas as pd

st.set_page_config(page_title="Community Reach — Volunteer Dashboard", layout="wide")
st.title("Community Reach — Volunteer Dashboard")
st.caption("Data from volunteer registration and service entry forms")

# Google Sheets URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/17r5Z3jJo5vR3Ye0cJfPUt8mi_Mi5cpFVYteZCnaIrKI/edit?usp=sharing"

def load_data_via_pandas(url, sheet_name):
    csv_url = url.replace("/edit?usp=sharing", f"/export?format=csv&sheet={sheet_name.replace(' ', '+')}")
    try:
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading sheet '{sheet_name}': {e}")
        return pd.DataFrame()

# Helper function to auto-assign Volunteer IDs cleanly
def assign_volunteer_ids(df, directory_df):
    if df.empty or directory_df.empty:
        return df
    
    # Locate First and Last Name columns
    first_col = next((c for c in df.columns if "first" in c.lower()), None)
    last_col = next((c for c in df.columns if "last" in c.lower()), None)
    
    # Strictly find the actual Volunteer ID column (exclude long survey questions)
    dir_id_col = next((c for c in directory_df.columns if "volunteer id" in c.lower() or c.strip().lower() == "id"), None)
    
    dir_first_col = next((c for c in directory_df.columns if "first" in c.lower()), None)
    dir_last_col = next((c for c in directory_df.columns if "last" in c.lower()), None)
    dir_name_col = next((c for c in directory_df.columns if "name" in c.lower() and "first" not in c.lower() and "last" not in c.lower()), None)

    if first_col and last_col:
        df_copy = df.copy()
        
        # Clean Full Name for main dataset
        f_names = df_copy[first_col].fillna('').astype(str).str.strip()
        l_names = df_copy[last_col].fillna('').astype(str).str.strip()
        df_copy['Full Name'] = (f_names + " " + l_names).str.strip()
        
        dir_clean = directory_df.copy()
        
        # Clean Full Name for directory dataset
        if dir_first_col and dir_last_col:
            d_f = dir_clean[dir_first_col].fillna('').astype(str).str.strip()
            d_l = dir_clean[dir_last_col].fillna('').astype(str).str.strip()
            dir_clean['Full Name'] = (d_f + " " + d_l).str.strip()
        elif dir_name_col:
            dir_clean['Full Name'] = dir_clean[dir_name_col].fillna('').astype(str).str.strip()
        else:
            dir_clean['Full Name'] = ''

        # Filter out empty names from directory
        dir_clean = dir_clean[dir_clean['Full Name'].str.len() > 1].copy()

        # Generate sequential IDs (V-100, V-101...) if no valid ID column exists
        if dir_id_col and dir_id_col in dir_clean.columns:
            dir_clean['Volunteer ID'] = dir_clean[dir_id_col].astype(str).str.strip()
            # Replace missing or generic text with sequential ID
            invalid_ids = dir_clean['Volunteer ID'].isna() | dir_clean['Volunteer ID'].str.contains('nan|Social|Unassigned', case=False)
            dir_clean.loc[invalid_ids, 'Volunteer ID'] = [f"V-{100+i}" for i in range(invalid_ids.sum())]
        else:
            dir_clean['Volunteer ID'] = [f"V-{100+i}" for i in range(len(dir_clean))]

        # Drop duplicates on Full Name
        dir_subset = dir_clean[['Full Name', 'Volunteer ID']].drop_duplicates(subset=['Full Name'])
        
        # Merge onto the main dataset
        merged = df_copy.merge(dir_subset, on='Full Name', how='left')
        merged['Volunteer ID'] = merged['Volunteer ID'].fillna('Unassigned')
        merged = merged.drop(columns=['Full Name'])
        
        # Reorder to put Volunteer ID first
        cols = ['Volunteer ID'] + [c for c in merged.columns if c != 'Volunteer ID']
        return merged[cols]
    
    return df

# --- 1. LOAD DATA ---
volunteers_df = load_data_via_pandas(SHEET_URL, "Volunteer Database")
programs_df = load_data_via_pandas(SHEET_URL, "Program Database")

# Apply ID assignment to both DataFrames
volunteers_df = assign_volunteer_ids(volunteers_df, volunteers_df)
programs_df = assign_volunteer_ids(programs_df, volunteers_df)

# --- 2. DYNAMIC COLUMN MAPPING ---
hours_col = value_col = prog_col = date_col = fy_col = type_col = None

if not programs_df.empty:
    hours_col = next((col for col in programs_df.columns if "hours" in col.lower() or "hrs" in col.lower()), None)
    value_col = next((col for col in programs_df.columns if "value" in col.lower() or "economic" in col.lower()), None)
    prog_col = next((col for col in programs_df.columns if "program" in col.lower() or "proj" in col.lower()), None)
    date_col = next((col for col in programs_df.columns if "date" in col.lower() or "time" in col.lower()), None)
    fy_col = next((col for col in programs_df.columns if "fiscal" in col.lower() or "fy" in col.lower()), None)
    type_col = next((col for col in programs_df.columns if "type" in col.lower() or "status" in col.lower()), None)

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

# --- 3. SIDEBAR FILTERS ---
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

# --- 4. FILTER DATA DYNAMICALLY ---
filtered_df = programs_df.copy() if not programs_df.empty else pd.DataFrame()
if not filtered_df.empty:
    if selected_progs and prog_col:
        filtered_df = filtered_df[filtered_df[prog_col].isin(selected_progs)]
    if selected_types and type_col:
        filtered_df = filtered_df[filtered_df[type_col].isin(selected_types)]
    if selected_fys and fy_col:
        filtered_df = filtered_df[filtered_df[fy_col].isin(selected_fys)]

# --- 5. DASHBOARD TABS ---
tabs = st.tabs(["Overview", "Volunteer Lookup"])

# ================= TAB 1: OVERVIEW =================
with tabs[0]:
    st.subheader("Overview")
    
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
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Hours by Program")
        if prog_col and hours_col and not filtered_df.empty:
            chart_data = filtered_df.groupby(prog_col)[hours_col].sum().reset_index()
            chart_data.columns = ['Program', 'Hours']
            st.bar_chart(chart_data, x='Program', y='Hours')
        else:
            st.info("Missing program tracking data.")
            
    with c2:
        st.write("### By Volunteer Type")
        if type_col and hours_col and not filtered_df.empty:
            chart_data = filtered_df.groupby(type_col)[hours_col].sum().reset_index()
            chart_data.columns = ['Type', 'Hours']
            st.bar_chart(chart_data, x='Type', y='Hours')
        else:
            st.info("Volunteer type data unavailable in program history.")

    c3, c4 = st.columns(2)
    with c3:
        st.write("### Trend by Fiscal Year")
        if fy_col and hours_col and not filtered_df.empty:
            chart_data = filtered_df.groupby(fy_col)[hours_col].sum().reset_index()
            chart_data.columns = ['Fiscal Year', 'Hours']
            chart_data['Fiscal Year'] = chart_data['Fiscal Year'].astype(str)
            st.line_chart(chart_data, x='Fiscal Year', y='Hours')
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
    
    c5, c6 = st.columns(2)
    with c5:
        st.write("### How Volunteers Found Community Reach")
        found_col = next((col for col in volunteers_df.columns if "find" in col.lower() or "how" in col.lower() or "source" in col.lower()), None) if not volunteers_df.empty else None
        if found_col and not volunteers_df.empty:
            source_data = volunteers_df[found_col].value_counts().reset_index()
            source_data.columns = ['Source', 'Count']
            st.bar_chart(source_data, x='Source', y='Count')
        else:
            st.info("Add a 'How Found' column to your Volunteer Database to populate this chart.")

    with c6:
        st.write("### Top Volunteers by Total Hours")
        vol_name_col = next((col for col in filtered_df.columns if "name" in col.lower() or "volunteer" in col.lower()), None) if not filtered_df.empty else None
        if vol_name_col and hours_col and not filtered_df.empty:
            top_vols = filtered_df.groupby(vol_name_col)[hours_col].sum().reset_index()
            top_vols.columns = ['Volunteer Name', 'Total Hours']
            top_vols = top_vols.sort_values(by='Total Hours', ascending=False).head(10)
            st.dataframe(top_vols, use_container_width=True, hide_index=True)
        else:
            st.info("Volunteer names not found in the activity sheet logs.")

    st.write("---")
    st.write("### 📝 Recent Logs")
    if not filtered_df.empty:
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    else:
        st.info("No service logs found matching the active filter selections.")

# ================= TAB 2: VOLUNTEER LOOKUP =================
with tabs[1]:
    st.subheader("Volunteer Lookup")
    
    if volunteers_df.empty:
        st.error("The 'Volunteer Database' sheet is empty or couldn't be loaded.")
    else:
        search_query = st.text_input("Search by name or Volunteer ID (type at least 2 characters):").strip()
        
        if len(search_query) >= 2:
            # Filter out entries where both first and last names are missing or empty
            first_c = next((c for c in volunteers_df.columns if "first" in c.lower()), None)
            last_c = next((c for c in volunteers_df.columns if "last" in c.lower()), None)
            
            valid_vols = volunteers_df.copy()
            if first_c and last_c:
                has_first = valid_vols[first_c].fillna('').astype(str).str.strip() != ''
                has_last = valid_vols[last_c].fillna('').astype(str).str.strip() != ''
                valid_vols = valid_vols[has_first | has_last]
            
            # Explicit search columns: First Name, Last Name, Volunteer ID
            search_cols = [c for c in valid_vols.columns if c in [first_c, last_c, 'Volunteer ID']]
            if not search_cols:
                search_cols = list(valid_vols.columns)
            
            mask = pd.Series(False, index=valid_vols.index)
            for col in search_cols:
                mask |= valid_vols[col].astype(str).str.contains(search_query, case=False, na=False)
            
            results = valid_vols[mask]
            
            if not results.empty:
                st.success(f"Found {len(results)} matching profile(s):")
                for idx, row in results.iterrows():
                    first = str(row.get(first_c, '')).replace('nan', '').strip() if first_c else ''
                    last = str(row.get(last_c, '')).replace('nan', '').strip() if last_c else ''
                    display_name = f"{first} {last}".strip()
                    
                    if not display_name:
                        continue
                    
                    vol_id = str(row.get('Volunteer ID', 'Unassigned')).strip()
                    
                    with st.expander(f"👤 {display_name} — ID: {vol_id}"):
                        st.metric("Volunteer ID", vol_id)
                        st.write("**Profile Details:**")
                        st.dataframe(pd.DataFrame(row).T, hide_index=True)
                        
                        if not programs_df.empty:
                            # Match service history using First + Last Name or ID
                            prog_first = next((c for c in programs_df.columns if "first" in c.lower()), None)
                            prog_last = next((c for c in programs_df.columns if "last" in c.lower()), None)
                            
                            if prog_first and prog_last:
                                history_mask = (
                                    (programs_df[prog_first].fillna('').astype(str).str.lower() == first.lower()) &
                                    (programs_df[prog_last].fillna('').astype(str).str.lower() == last.lower())
                                )
                            else:
                                history_mask = pd.Series(False, index=programs_df.index)
                            
                            if 'Volunteer ID' in programs_df.columns and vol_id != 'Unassigned':
                                history_mask |= (programs_df['Volunteer ID'].astype(str) == vol_id)
                            
                            history = programs_df[history_mask]
                            
                            st.write("**Service History:**")
                            if not history.empty:
                                st.dataframe(history, hide_index=True)
                            else:
                                st.info("No service logs found matching this individual.")
            else:
                st.warning(f"No volunteer records found matching '{search_query}'.")
        else:
            st.info("Type a volunteer's name or ID above to pull up their record.")
