import streamlit as st
import pandas as pd

st.set_page_config(page_title="Volunteer Analytics Dashboard", layout="wide")
st.title("📊 Volunteer & Program Insights Dashboard")

# Paste your clean share link here
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_3Pd_ZTQTu46sOZ1-FmX7KEg5v4TOQy3xC1DM5840s8/edit?usp=sharing"

def load_data_via_pandas(url, sheet_name):
    # This automatically forces pandas to find the specific tab structure
    csv_url = url.replace("/edit?usp=sharing", f"/export?format=csv&sheet={sheet_name.replace(' ', '+')}")
    return pd.read_csv(csv_url)

try:
    # Directly pulling the filtered tabs
    volunteers_df = load_data_via_pandas(SHEET_URL, "Volunteer Database")
    programs_df = load_data_via_pandas(SHEET_URL, "Program Database")

    # --- SIDEBAR NAVIGATION ---
    page = st.sidebar.selectbox("Choose a view", ["Program Performance", "Volunteer Directory"])

    if page == "Program Performance":
        st.subheader("📈 Hour Logging & Value Metrics")
        
        total_hours = pd.to_numeric(programs_df["Total Hours"], errors='coerce').sum()
        total_value = pd.to_numeric(programs_df["Dollar Value"], errors='coerce').sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Hours Contributed", f"{total_hours:,.1f} hrs")
        col2.metric("Estimated Economic Value", f"${total_value:,.2f}")
        
        st.write("### Hours Contributed per Program")
        program_chart_data = programs_df.groupby("Program")["Total Hours"].sum().reset_index()
        st.bar_chart(data=program_chart_data, x="Program", y="Total Hours")
        
        st.write("### Recent Logs", programs_df)

    elif page == "Volunteer Directory":
        st.subheader("👥 Active Volunteer Profiles")
        st.write(f"Total Registered Volunteers: {len(volunteers_df)}")
        
        search_query = st.text_input("Search volunteers by name or ID")
        if search_query:
            filtered_vols = volunteers_df[
                volunteers_df["Name"].str.contains(search_query, case=False, na=False) |
                volunteers_df["ID"].str.contains(search_query, case=False, na=False)
            ]
            st.dataframe(filtered_vols)
        else:
            st.dataframe(volunteers_df)

except Exception as e:
    st.error(f"Error connecting: {e}")
