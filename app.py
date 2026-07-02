import streamlit as st
import pandas as pd

st.set_page_config(page_title="Volunteer Analytics Dashboard", layout="wide")
st.title("📊 Volunteer & Program Insights Dashboard")

# Replace this with your actual copied Google Sheet URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/1_3Pd_ZTQTu46sOZ1-FmX7KEg5v4TOQy3xC1DM5840s8/edit?usp=sharing"
# Functions to parse the specific tabs directly
@st.cache_data(ttl=600)  # Caches data for 10 minutes so it loads fast
def load_data(tab_name):
    # This magic string tweaks the URL to export the specific tab as a clean CSV
    csv_url = SHEET_URL.replace("/edit?usp=sharing", f"/gviz/tq?tqx=out:csv&sheet={tab_name.replace(' ', '%20')}")
    return pd.read_csv(csv_url)

try:
    # Load your filtered tabs
    volunteers_df = load_data("Volunteer Database")
    programs_df = load_data("Program Database")

    # --- SIDEBAR NAVIGATION ---
    page = st.sidebar.selectbox("Choose a view", ["Program Performance", "Volunteer Directory"])

    if page == "Program Performance":
        st.subheader("📈 Hour Logging & Value Metrics")
        
        # Quick KPI Cards
        total_hours = programs_df["Total Hours"].sum()
        total_value = programs_df["Dollar Value"].sum()
        
        col1, col2 = st.columns(2)
        col1.metric("Total Hours Contributed", f"{total_hours:,.1f} hrs")
        col2.metric("Estimated Economic Value", f"${total_value:,.2f}")
        
        # Interactive Chart: Hours by Program
        st.write("### Hours Contributed per Program")
        program_chart_data = programs_df.groupby("Program")["Total Hours"].sum().reset_index()
        st.bar_chart(data=program_chart_data, x="Program", y="Total Hours")
        
        # Raw Data View
        st.write("### Recent Logs", programs_df)

    elif page == "Volunteer Directory":
        st.subheader("👥 Active Volunteer Profiles")
        st.write(f"Total Registered Volunteers: {len(volunteers_df)}")
        
        # Search bar to filter volunteers
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
    st.error("Could not connect to the Google Sheet. Please check your URL and sharing settings!")
