import streamlit as st
import pandas as pd

st.set_page_config(page_title="Volunteer Analytics Dashboard", layout="wide")
st.title("📊 Volunteer & Program Insights Dashboard")

# Paste your clean share link here
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_3Pd_ZTQTu46sOZ1-FmX7KEg5v4TOQy3xC1DM5840s8/edit?usp=sharing"

def load_data_via_pandas(url, sheet_name):
    csv_url = url.replace("/edit?usp=sharing", f"/export?format=csv&sheet={sheet_name.replace(' ', '+')}")
    df = pd.read_csv(csv_url)
    # This automatically strips accidental spaces from headers
    df.columns = df.columns.str.strip()
    return df

try:
    volunteers_df = load_data_via_pandas(SHEET_URL, "Volunteer Database")
    programs_df = load_data_via_pandas(SHEET_URL, "Program Database")

    # --- SIDEBAR NAVIGATION ---
    page = st.sidebar.selectbox("Choose a view", ["Program Performance", "Volunteer Directory"])

    if page == "Program Performance":
        st.subheader("📈 Hour Logging & Value Metrics")
        
        # Safely find columns even with slight variations
        hours_col = [col for col in programs_df.columns if "hours" in col.lower()]
        value_col = [col for col in programs_df.columns if "value" in col.lower()]
        prog_col = [col for col in programs_df.columns if "program" in col.lower()]
        
        total_hours = pd.to_numeric(programs_df[hours_col[0]], errors='coerce').sum() if hours_col else 0
        total_value = pd.to_numeric(programs_df[value_col[0]], errors='coerce').sum() if value_col else 0
        
        col1, col2 = st.columns(2)
        col1.metric("Total Hours Contributed", f"{total_hours:,.1f} hrs")
        col2.metric("Estimated Economic Value", f"${total_value:,.2f}")
        
        if hours_col and prog_col:
            st.write("### Hours Contributed per Program")
            program_chart_data = programs_df.groupby(prog_col[0])[hours_col[0]].sum().reset_index()
            st.bar_chart(data=program_chart_data, x=prog_col[0], y=hours_col[0])
        
        st.write("### Recent Logs", programs_df)

    elif page == "Volunteer Directory":
        st.subheader("👥 Active Volunteer Profiles")
        st.write(f"Total Registered Volunteers: {len(volunteers_df)}")
        
        name_col = [col for col in volunteers_df.columns if "name" in col.lower()]
        id_col = [col for col in volunteers_df.columns if "id" in col.lower()]
        
        search_query = st.text_input("Search volunteers by name or ID")
        if search_query and (name_col or id_col):
            # Dynamic filtering based on found columns
            mask = pd.Series(False, index=volunteers_df.index)
            if name_col:
                mask |= volunteers_df[name_col[0]].str.contains(search_query, case=False, na=False)
            if id_col:
                mask |= volunteers_df[id_col[0]].str.contains(search_query, case=False, na=False)
            st.dataframe(volunteers_df[mask])
        else:
            st.dataframe(volunteers_df)

except Exception as e:
    st.error(f"Error connecting: {e}")
