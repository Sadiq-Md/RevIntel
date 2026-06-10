import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.graph_objects as go

from forecasting import forecast
import report_generator
from modules.virtual_consultant import generate_consultant_suggestion
from modules.bid_optimizer import suggest_bid_pricing
from modules.leakage_detector import calculate_revenue_leakage
from modules.competitor_tracker import competitor_loss_comparison
import plotly.express as px  # if not imported yet


# ----------------------------
# Load & preprocess data
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/company_data.csv")
    df["Profit_Margin"] = (df["Profit"] / df["Revenue"]) * 100
    return df

df = load_data()

# ----------------------------
# Sidebar filters
# ----------------------------
st.title("📊 IntelliRev - Company Performance Dashboard")
company = st.sidebar.multiselect("Select Company", df["Company"].unique(), default=df["Company"].unique())
year = st.sidebar.multiselect("Select Year", df["Year"].unique(), default=df["Year"].unique())

filtered = df[df["Company"].isin(company) & df["Year"].isin(year)]

# ----------------------------
# KPI Metrics
# ----------------------------
st.subheader("🔹 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Revenue", f"${filtered['Revenue'].sum():,.0f}")
col2.metric("Total Profit", f"${filtered['Profit'].sum():,.0f}")
col3.metric("Lost Contracts", int(filtered["Lost_Contracts"].sum()))

# ----------------------------
# Charts
# ----------------------------
st.subheader("📈 Revenue by Company")
fig1 = plt.figure()
sns.barplot(data=filtered, x="Company", y="Revenue", estimator=sum)
st.pyplot(fig1)

st.subheader("📊 Revenue Trend Over Time")
fig2 = plt.figure(figsize=(8, 5))
sns.lineplot(data=filtered, x="Year", y="Revenue", hue="Company", marker="o")
plt.title("Revenue Trend")
plt.xticks(sorted(filtered["Year"].unique()))
st.pyplot(fig2)

st.subheader("💰 Profit Margin by Year")
fig3 = plt.figure()
sns.lineplot(data=filtered, x="Year", y="Profit_Margin", hue="Company", marker="o")
st.pyplot(fig3)

st.subheader("💸 Profit Margin Distribution")
fig4 = plt.figure(figsize=(8, 5))
sns.boxplot(data=filtered, x="Company", y="Profit_Margin")
plt.title("Profit Margin Distribution")
st.pyplot(fig4)

st.subheader("❌ Contract Losses by Reason")
fig5 = plt.figure()
sns.countplot(data=filtered, x="Loss_Reason", hue="Company")
plt.xticks(rotation=30)
st.pyplot(fig5)

st.subheader("❗ Loss Reason Share (Overall)")
loss_counts = filtered["Loss_Reason"].value_counts()
fig6 = plt.figure(figsize=(6, 6))
plt.pie(loss_counts, labels=loss_counts.index, autopct="%1.1f%%", startangle=140)
plt.axis("equal")
plt.title("Loss Reasons - Proportion by Count")
st.pyplot(fig6)

# ----------------------------
# Forecasting
# ----------------------------
st.subheader("📈 Forecasting")
companies = df["Company"].unique().tolist()
selected_metric = st.selectbox("Select Metric to Forecast", ["Revenue", "Profit"])
selected_company = st.selectbox("Select Company", companies)

if st.button("Run Forecast"):
    historical, predicted = forecast(df, selected_company, selected_metric)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=historical["ds"], y=historical["y"],
                             mode='lines+markers', name='Historical'))
    fig.add_trace(go.Scatter(x=predicted["ds"], y=predicted["yhat"],
                             mode='lines+markers', name='Forecast'))
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# PDF Report Generator
# ----------------------------
st.subheader("📥 Export Report")
if st.button("Generate PDF Report"):
    with st.spinner("Generating PDF report..."):
        report_generator.generate_pdf(filtered)
    st.success("✅ PDF report generated! Check IntelliRev_Report.pdf in your folder.")

# ----------------------------
# Contract Loss Autopsy
# ----------------------------
st.subheader("🔍 Contract Loss Autopsy")
loss_df = df.groupby(["Loss_Reason", "Industry"]).agg(
    Total_Lost=("Lost_Contracts", "sum")
).reset_index()
st.dataframe(loss_df.sort_values("Total_Lost", ascending=False))

# ----------------------------
# Virtual Revenue Consultant
# ----------------------------
st.subheader("🧠 Virtual Revenue Consultant")
vc_suggestion = generate_consultant_suggestion(filtered)
st.info(vc_suggestion)

# ----------------------------
# AI-powered Bid Optimizer
# ----------------------------
st.subheader("📈 AI-powered Bid Optimizer")

deal_size = st.selectbox("Select Deal Size", ["Small", "Medium", "Large"])
region = st.selectbox("Select Region", ["North America", "Europe", "Asia", "Other"])
industry = st.selectbox("Select Industry", ["Banking", "Healthcare", "Technology", "Other"])

pricing_suggestion = suggest_bid_pricing(deal_size, region, industry)
st.success(f"💡 Pricing Suggestion: {pricing_suggestion}")

# ----------------------------
# Revenue Leakage Detector
# ----------------------------
st.subheader("💸 Revenue Leakage Detector")

# You can later replace this with real actual vs forecasted data
actual_data = {
    "Month": ["Jan", "Feb", "Mar", "Apr"],
    "Revenue": [100000, 95000, 97000, 92000]
}
forecast_data = {
    "Month": ["Jan", "Feb", "Mar", "Apr"],
    "Revenue": [102000, 98000, 99000, 95000]
}

actual_df = pd.DataFrame(actual_data)
forecast_df = pd.DataFrame(forecast_data)

leakage = calculate_revenue_leakage(actual_df, forecast_df)

if leakage > 0:
    st.warning(f"⚠️ Estimated Revenue Leakage: ${leakage:,.0f}")
else:
    st.success("✅ No revenue leakage detected")


st.subheader("📊 Competitive Intelligence Tracker")

# Optional filter for companies
comp_companies = st.multiselect(
    "Select Companies to Compare",
    options=df["Company"].unique(),
    default=df["Company"].unique()
)

comp_filtered = df[df["Company"].isin(comp_companies)]

fig_comp = competitor_loss_comparison(comp_filtered)
st.plotly_chart(fig_comp, use_container_width=True)
