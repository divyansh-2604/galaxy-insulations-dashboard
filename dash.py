import streamlit as st
import pandas as pd
import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    RunRealtimeReportRequest,
)

# ✅ Set credentials and GA4 property
KEY_PATH = r"C:\Users\Rajan Narula\Downloads\galaxy-insulations-dashboard-9f30440ad087.json"
PROPERTY_ID = "498240746"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = KEY_PATH

client = BetaAnalyticsDataClient()

# ✅ Safe conversion for null values
def safe_int(value):
    try:
        return int(value) if value else 0
    except:
        return 0

def safe_float(value):
    try:
        return float(value) if value else 0.0
    except:
        return 0.0

# 📊 Historical data (Last 30 Days)
def get_historical_data():
    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="date")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="sessions"),
            Metric(name="screenPageViews"),
            Metric(name="averageSessionDuration"),
            Metric(name="bounceRate"),
            Metric(name="engagementRate"),
            Metric(name="userEngagementDuration")
            # REMOVED "views" – not a valid GA4 metric
        ],
        date_ranges=[DateRange(start_date="30daysAgo", end_date="today")]
    )
    response = client.run_report(request)

    data = []
    for row in response.rows:
        date_str = row.dimension_values[0].value
        formatted_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        data.append({
            "Date": formatted_date,
            "Active Users": safe_int(row.metric_values[0].value),
            "New Users": safe_int(row.metric_values[1].value),
            "Sessions": safe_int(row.metric_values[2].value),
            "Page Views": safe_int(row.metric_values[3].value),
            "Avg. Session Duration (s)": safe_float(row.metric_values[4].value),
            "Bounce Rate (%)": safe_float(row.metric_values[5].value),
            "Engagement Rate (%)": safe_float(row.metric_values[6].value),
            "User Engagement (s)": safe_float(row.metric_values[7].value)
        })
    return pd.DataFrame(data)

# 🟢 Realtime data by device, country, platform
def get_realtime_data():
    request = RunRealtimeReportRequest(
        property=f"properties/{PROPERTY_ID}",
        dimensions=[Dimension(name="deviceCategory"), Dimension(name="country"), Dimension(name="platform")],
        metrics=[Metric(name="activeUsers")]
    )
    response = client.run_realtime_report(request)

    total = 0
    device_data, country_data, platform_data = {}, {}, {}

    for row in response.rows:
        device = row.dimension_values[0].value
        country = row.dimension_values[1].value
        platform = row.dimension_values[2].value
        users = safe_int(row.metric_values[0].value)
        total += users

        device_data[device] = device_data.get(device, 0) + users
        country_data[country] = country_data.get(country, 0) + users
        platform_data[platform] = platform_data.get(platform, 0) + users

    device_df = pd.DataFrame(list(device_data.items()), columns=["Device", "Active Users"])
    country_df = pd.DataFrame(list(country_data.items()), columns=["Country", "Active Users"])
    platform_df = pd.DataFrame(list(platform_data.items()), columns=["Platform", "Active Users"])

    return total, device_df, country_df, platform_df

# 🌐 Streamlit UI
st.set_page_config(page_title="Galaxy Insulations Dashboard", layout="centered")

st.title("📊 Galaxy Insulations Dashboard")
st.markdown("Google Analytics 4 Real-Time and Historical Metrics")

# 🔥 Realtime section
st.subheader("🟢 Real-Time Active Users")
total_users, device_df, country_df, platform_df = get_realtime_data()
st.metric("Currently Active Users", total_users)

# Realtime charts
col1, col2 = st.columns(2)
with col1:
    if not device_df.empty:
        st.bar_chart(device_df.set_index("Device"))
    else:
        st.info("No device data to show.")

with col2:
    if not platform_df.empty:
        st.bar_chart(platform_df.set_index("Platform"))
    else:
        st.info("No platform data to show.")

if not country_df.empty:
    st.subheader("🌍 Active Users by Country")
    st.dataframe(country_df.sort_values("Active Users", ascending=False).reset_index(drop=True))

# 📅 Historical section
st.subheader("📅 Metrics Over the Last 30 Days")

history_df = get_historical_data()
st.dataframe(history_df)

# Line chart for users & sessions
st.line_chart(history_df.set_index("Date")[["Active Users", "New Users", "Sessions"]])

# Additional charts
st.subheader("📈 Engagement Metrics")
col3, col4 = st.columns(2)
with col3:
    st.line_chart(history_df.set_index("Date")[["Engagement Rate (%)", "Bounce Rate (%)"]])
with col4:
    st.line_chart(history_df.set_index("Date")[["User Engagement (s)", "Avg. Session Duration (s)"]])

st.subheader("🔁 Page Interactions")
st.line_chart(history_df.set_index("Date")[["Page Views"]])  # Removed "Views"

st.markdown("---")
st.caption("Powered by Streamlit & Google Analytics 4")
