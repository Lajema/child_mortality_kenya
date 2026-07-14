import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. PAGE SETUP (Old-School Technical Styling)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Kenya Child Health & Nutrition Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom CSS to force our Segoe UI/Arial fonts and subtle grey canvas background
st.markdown("""
    <style>
        /* Force Times New Roman globally across the app's structural components */
        html, body, .stApp, [class*="css"], h1, h2, h3, h4, h5, h6, p, span, label {
            font-family: 'Times New Roman', Times, serif !important;
        }

        /* Set main container background to a professional slate-grey tint */
        .stApp {
            background-color: #F8FAFC;
        }

        /* Custom styled borders for our container blocks */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FFFFFF;
            border: 1px solid #CBD5E1 !important;
            border-radius: 4px !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. DATA CACHING AND LOADING
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_clean_data():
    # Load the raw CSV (skipping World Bank header metadata)
    df_raw = pd.read_csv("API_KEN_DS2_en_csv_v2_5938.csv", skiprows=4)
    
    # Target health & nutrition metrics
    target_indicators = {
        "Mortality rate, under-5 (per 1,000 live births)": "Child Mortality Rate",
        "Prevalence of stunting, height for age (% of children under 5)": "Child Stunting Rate",
        "Prevalence of underweight, weight for age (% of children under 5)": "Child Underweight Rate"
    }
    
    df_health = df_raw[df_raw["Indicator Name"].isin(target_indicators.keys())].copy()
    df_health["Friendly Name"] = df_health["Indicator Name"].map(target_indicators)
    
    # Unpivot Year columns to long-form format
    year_cols = [col for col in df_health.columns if col.isdigit()]
    df_long = df_health.melt(
        id_vars=["Friendly Name"], 
        value_vars=year_cols, 
        var_name="Year", 
        value_name="Value"
    )
    
    # Clean and cast column formats strictly
    df_long["Year"] = df_long["Year"].astype(int)
    df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce")
    
    # Drop empty records
    return df_long.dropna(subset=["Value"])

# Load dataset
try:
    df_clean = load_and_clean_data()
except FileNotFoundError:
    st.error("🚨 **Data File Not Found!** Please ensure 'API_KEN_DS2_en_csv_v2_5938.csv' is saved in the exact same directory as this script.")
    st.stop()

# Pivot for dual-axis plotting
df_pivot = df_clean.pivot(index="Year", columns="Friendly Name", values="Value").reset_index()

# -----------------------------------------------------------------------------
# 3. INTERACTIVE TIMELINE SIDEBAR
# -----------------------------------------------------------------------------
st.sidebar.title("🛠️ Dashboard Controls")
st.sidebar.markdown("Filter the analysis timelines below:")

min_year = int(df_pivot["Year"].min())
max_year = int(df_pivot["Year"].max())

# Timeline Range Slider
selected_years = st.sidebar.slider(
    "Select Analysis Window",
    min_value=min_year,
    max_value=max_year,
    value=(1990, max_year),
    step=1
)

# Apply filtered range to our pivoted dataframe
df_filtered = df_pivot[
    (df_pivot["Year"] >= selected_years[0]) & 
    (df_pivot["Year"] <= selected_years[1])
]

# -----------------------------------------------------------------------------
# 4. APP LAYOUT & DISPLAY ENGINE
# -----------------------------------------------------------------------------
st.title("Child Health & Nutrition Survival Loop")
st.caption("A structural analysis linking chronic childhood malnutrition (stunting) directly with under-5 mortality rates in Kenya.")

# Space helper
st.markdown("---")

# --- ZONE A: THE VITAL SIGN METRIC CARDS ---
col1, col2, col3 = st.columns(3)

# Calculate latest indicators within our selected timeline
latest_data = df_filtered.dropna().tail(1)

with col1:
    with st.container(border=True):
        if not latest_data.empty and not pd.isna(latest_data["Child Mortality Rate"].values[0]):
            val = round(latest_data["Child Mortality Rate"].values[0], 1)
            st.metric(label="Latest Child Mortality (per 1,000 live births)", value=f"{val}")
        else:
            st.metric(label="Latest Child Mortality", value="No Data")

with col2:
    with st.container(border=True):
        if not latest_data.empty and not pd.isna(latest_data["Child Stunting Rate"].values[0]):
            val = round(latest_data["Child Stunting Rate"].values[0], 1)
            st.metric(label="Latest Child Stunting Rate (% of under 5s)", value=f"{val}%")
        else:
            st.metric(label="Latest Child Stunting", value="No Data")

with col3:
    with st.container(border=True):
        if not latest_data.empty and not pd.isna(latest_data["Child Underweight Rate"].values[0]):
            val = round(latest_data["Child Underweight Rate"].values[0], 1)
            st.metric(label="Child Underweight Rate (% of under 5s)", value=f"{val}%")
        else:
            st.metric(label="Child Underweight Rate", value="No Data")

# Space helper
st.markdown(" ")

# --- ZONE B: COHESIVE INTERACTIVE PLOT & STORY NARRATIVE ---
with st.container(border=True):
    st.subheader("The Nutrition-Survival Trend Engine")
    
    # Create the dual-axis canvas
    fig = go.Figure()
    
    # 1. Mortality Line (Continuous Timeline)
    fig.add_trace(
        go.Scatter(
            x=df_filtered["Year"],
            y=df_filtered["Child Mortality Rate"],
            name="Child Mortality (per 1K births)",
            line=dict(color="#DC2626", width=4), # Crimson
            yaxis="y1"
        )
    )
    
    # 2. Stunting Columns (Sporadic Health Survey Years)
    # Removing NaN values from stunting specifically so we don't render empty columns
    stunt_df = df_filtered[["Year", "Child Stunting Rate"]].dropna()
    fig.add_trace(
        go.Bar(
            x=stunt_df["Year"],
            y=stunt_df["Child Stunting Rate"],
            name="Child Stunting Rate (%)",
            marker_color="#16A34A", # Green
            opacity=0.75,
            yaxis="y2"
        )
    )
    
    # 3. Setup scales and layouts to look sharp and clean
    # 3. Setup scales and layouts with corrected font properties
    fig.update_layout(
        xaxis=dict(
            title=dict(text="Year"), 
            gridcolor="#E2E8F0",
            dtick=5 # Grid tick markers every 5 years
        ),
        yaxis=dict(
            title=dict(
                text="Under-5 Mortality Rate (per 1,000 live births)",
                font=dict(color="#DC2626")
            ),
            tickfont=dict(color="#DC2626"),
            gridcolor="#E2E8F0"
        ),
        yaxis2=dict(
            title=dict(
                text="Stunting Prevalence (% of children under 5)",
                font=dict(color="#16A34A")
            ),
            tickfont=dict(color="#16A34A"),
            overlaying="y",
            side="right"
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Translator explanation note
    st.markdown("""
        > This chart visually represents one of the most critical equations in national development: *food security directly determines child survival*. 
        > Notice that as childhood stunting metrics (green columns, representing chronic physical and cognitive developmental delays caused by prolonged malnutrition) decline, 
        > the under-5 mortality curve (red line) experiences a corresponding, steady descent. Reducing nutritional starvation acts as the primary pillar of saving child lives.
    """)