import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from supabase import create_client
from datetime import date

# ============================================================
# 1. PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Small Business Loan Risk Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# 2. THEME, STYLING AND CHART HELPERS
# ============================================================

# Earthy palette. Greens = safe, ochre = watch, rust = risk.
PARCHMENT = "#F1E9DA"     # page background
CARD = "#FAF5EA"          # cards and chart panels
BORDER = "#D9C9A6"
INK = "#3B2F26"           # main text (deep umber)
FOREST = "#3F5B3A"        # primary
FOREST_DARK = "#2F4A32"
OCHRE = "#C58B2B"
CLAY = "#B5703E"
SAGE = "#8A9A5B"

RISK_LOW = "#5E8C4A"      # healthy / non-default
RISK_MID = "#D19A2E"      # watch
RISK_HIGH = "#A8432B"     # default / high risk

RISK_SCALE = [RISK_LOW, RISK_MID, RISK_HIGH]

# Default-rate thresholds (%) used for the portfolio risk signal.
# Adjust these to match your own risk appetite.
RISK_LOW_PCT = 10
RISK_HIGH_PCT = 20
RISK_RANGE = [0, RISK_HIGH_PCT * 1.5]

OUTCOME_LABELS = {0: "Non-default", 1: "Default"}
OUTCOME_COLOURS = {"Non-default": RISK_LOW, "Default": RISK_HIGH}

# Plotly template so every chart shares the same look.
pio.templates["earth"] = go.layout.Template(
    layout=dict(
        font=dict(
            family="Inter, 'Segoe UI', Helvetica, Arial, sans-serif",
            color=INK,
            size=13
        ),
        title=dict(
            font=dict(
                family="'Source Serif 4', Georgia, serif",
                size=18,
                color=FOREST_DARK
            ),
            x=0.01
        ),
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        colorway=[FOREST, OCHRE, CLAY, SAGE, RISK_HIGH, "#6B5B45", "#8C6A3F"],
        xaxis=dict(
            gridcolor="#EADFC8", linecolor="#BBA982",
            zeroline=False, ticks="outside", tickcolor="#BBA982"
        ),
        yaxis=dict(
            gridcolor="#EADFC8", linecolor="#BBA982",
            zeroline=False
        ),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        hoverlabel=dict(
            bgcolor=FOREST_DARK,
            font=dict(color="#F6EEDC")
        ),
        margin=dict(l=40, r=20, t=60, b=40)
    )
)
pio.templates.default = "earth"


def show_chart(fig):
    """Render a Plotly chart using the dashboard theme."""
    fig.update_layout(coloraxis_showscale=False)
    fig.update_traces(selector=dict(type="bar"), marker_line_width=0)
    # theme=None stops Streamlit overriding the custom colours.
    st.plotly_chart(fig, use_container_width=True, theme=None)


def status_colour(status):
    """Map a repayment status label to a risk colour."""
    text = str(status).lower()

    if "non" in text and "default" in text:
        return RISK_LOW

    high_words = [
        "default", "unpaid", "not paid", "late", "overdue", "arrear",
        "written", "delinq", "charged", "missed", "bad"
    ]
    low_words = [
        "paid", "repaid", "current", "good", "complete",
        "on time", "on-time", "settled"
    ]

    if any(word in text for word in high_words):
        return RISK_HIGH
    if any(word in text for word in low_words):
        return RISK_LOW
    return RISK_MID


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@500;600;700&display=swap');

/* ---------- Page ---------- */
.stApp {
    background-color: #F1E9DA;
    color: #3B2F26;
    font-family: 'Inter', 'Segoe UI', Helvetica, Arial, sans-serif;
}
header[data-testid="stHeader"] { background: transparent; }
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1280px;
}
.stApp p, .stApp li, .stApp label, .stApp span { color: #3B2F26; }
.stApp small, .stApp [data-testid="stCaptionContainer"] { color: #7A6A58; }

/* ---------- Hero banner ---------- */
.hero {
    background: linear-gradient(120deg, #2F4A32 0%, #43623C 60%, #66773A 100%);
    border-radius: 14px;
    padding: 2rem 2.2rem 1.6rem 2.2rem;
    margin-bottom: 1.6rem;
    box-shadow: 0 4px 14px rgba(47, 74, 50, 0.25);
    position: relative;
    overflow: hidden;
}
.hero-eyebrow {
    color: #E3BF73 !important;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.hero-title {
    font-family: 'Source Serif 4', Georgia, serif;
    color: #F6EEDC !important;
    font-size: 2.3rem;
    font-weight: 700;
    line-height: 1.2;
    margin: 0 0 0.6rem 0;
}
.hero-text {
    color: #E4DCC4 !important;
    font-size: 1.02rem;
    max-width: 760px;
    margin: 0 0 1rem 0;
}
.hero-tags {
    color: #BFCBA3 !important;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
}
.risk-strip {
    position: absolute;
    left: 0; right: 0; bottom: 0;
    height: 6px;
    background: linear-gradient(90deg, #5E8C4A 0%, #D19A2E 55%, #A8432B 100%);
}

/* ---------- Headings ---------- */
.stApp h2 {
    font-family: 'Source Serif 4', Georgia, serif;
    color: #2F4A32;
    font-weight: 600;
    font-size: 1.6rem;
    border-bottom: 2px solid #D9C9A6;
    padding-bottom: 0.45rem;
    margin-top: 0.4rem;
}
.stApp h3 {
    font-family: 'Source Serif 4', Georgia, serif;
    color: #5A4632;
    font-weight: 600;
}
hr { border-color: #D3C3A0 !important; }

/* ---------- KPI cards ---------- */
div[data-testid="stMetric"] {
    background-color: #FAF5EA;
    border: 1px solid #D9C9A6;
    border-left: 5px solid #3F5B3A;
    padding: 16px 18px;
    border-radius: 10px;
    box-shadow: 0 1px 3px rgba(59, 47, 38, 0.08);
}
div[data-testid="stHorizontalBlock"] > div:nth-child(2) div[data-testid="stMetric"] { border-left-color: #C58B2B; }
div[data-testid="stHorizontalBlock"] > div:nth-child(3) div[data-testid="stMetric"] { border-left-color: #B5703E; }
div[data-testid="stMetricLabel"] p {
    color: #7A6A58 !important;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
div[data-testid="stMetricValue"] {
    color: #2F4A32;
    font-family: 'Source Serif 4', Georgia, serif;
    font-weight: 700;
}

/* ---------- Chart panels ---------- */
div[data-testid="stPlotlyChart"] {
    background: #FAF5EA;
    border: 1px solid #D9C9A6;
    border-radius: 10px;
    padding: 6px;
    box-shadow: 0 1px 3px rgba(59, 47, 38, 0.08);
    overflow: hidden;
}

/* ---------- Sidebar ---------- */
section[data-testid="stSidebar"] {
    background-color: #E6DCC6;
    border-right: 1px solid #CDBE9E;
}
section[data-testid="stSidebar"] h1 {
    font-family: 'Source Serif 4', Georgia, serif;
    color: #2F4A32;
    font-size: 1.5rem;
}
div[data-baseweb="select"] > div {
    background-color: #FAF5EA;
    border-color: #CDBE9E;
}
span[data-baseweb="tag"] {
    background-color: #3F5B3A !important;
}
span[data-baseweb="tag"] span { color: #F6EEDC !important; }
input[type="text"] {
    background-color: #FAF5EA !important;
    color: #3B2F26 !important;
}

/* ---------- Buttons ---------- */
.stDownloadButton button, .stButton button {
    background-color: #3F5B3A;
    color: #F6EEDC;
    border: 1px solid #2F4A32;
    border-radius: 8px;
    font-weight: 500;
}
.stDownloadButton button:hover, .stButton button:hover {
    background-color: #2F4A32;
    border-color: #C58B2B;
    color: #FFFFFF;
}
.stDownloadButton button p, .stButton button p { color: #F6EEDC !important; }

/* ---------- Alerts and tables ---------- */
div[data-testid="stAlert"] {
    background-color: #EFE3C8;
    border: 1px solid #D9C9A6;
    border-radius: 10px;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #D9C9A6;
    border-radius: 10px;
    overflow: hidden;
}

/* ---------- Risk badge ---------- */
.risk-badge {
    display: inline-block;
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #FFFFFF !important;
    margin: 0.7rem 0 0.2rem 0;
}
</style>
""",
    unsafe_allow_html=True
)

# Page header
st.markdown(
    '<div class="hero">'
    '<div class="hero-eyebrow">Credit Risk Analytics</div>'
    '<div class="hero-title">Small Business Loan Risk Analysis</div>'
    '<p class="hero-text">Explore small business loan applications, repayment '
    'outcomes, loan exposure, and factors associated with defaults.</p>'
    '<div class="hero-tags">Portfolio project &nbsp;|&nbsp; Python &bull; Pandas '
    '&bull; Supabase &bull; SQL &bull; Streamlit &bull; Plotly</div>'
    '<div class="risk-strip"></div>'
    '</div>',
    unsafe_allow_html=True
)

# ============================================================
# 3. DATABASE CONFIGURATION
# ============================================================

TABLE_NAME = "small_business_loans"

@st.cache_data(ttl=300)
def load_data():
    """Fetch the project dataset from Supabase."""

    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]

    supabase = create_client(supabase_url, supabase_key)

    # Supabase returns a maximum number of rows per request
    # depending on the project's API settings. Paginate to
    # retrieve larger datasets as well.
    all_rows = []
    page_size = 1000
    start = 0

    while True:
        response = (
            supabase.table(TABLE_NAME)
            .select("*")
            .range(start, start + page_size - 1)
            .execute()
        )

        batch = response.data or []
        all_rows.extend(batch)

        if len(batch) < page_size:
            break

        start += page_size

    return pd.DataFrame(all_rows)


# ============================================================
# 4. LOAD DATA AND HANDLE ERRORS
# ============================================================

try:
    df = load_data()

except Exception as error:
    st.error("Unable to connect to the Supabase database.")
    st.write("Check your connection details, table name, and database permissions.")
    st.code(str(error))
    st.stop()

if df.empty:
    st.warning(
        f"The table '{TABLE_NAME}' is empty. "
        "Please insert your loan dataset into Supabase."
    )
    st.stop()

# Standardise column names to make analysis easier.
df.columns = [
    str(column).strip().lower().replace(" ", "_")
    for column in df.columns
]

# Support common naming variations without changing the database.
column_aliases = {
    "loan_status": "repayment_status",
    "status": "repayment_status",
    "years_in_operation": "years_in_business",
    "risk_level": "default_flag",
    "default": "default_flag",
    "income": "monthly_income",
    "interest": "interest_rate",
    "amount": "loan_amount",
    "province_name": "province",
    "business_category": "industry"
}

for old_name, new_name in column_aliases.items():
    if old_name in df.columns and new_name not in df.columns:
        df.rename(columns={old_name: new_name}, inplace=True)

# ============================================================
# 5. VALIDATE AND PREPARE THE DATA
# ============================================================

# Convert common numeric columns to numeric values.
numeric_candidates = [
    "loan_amount",
    "monthly_income",
    "interest_rate",
    "years_in_business",
    "credit_score",
    "monthly_expenses",
    "annual_revenue",
    "employees",
    "loan_term_months"
]

for column in numeric_candidates:
    if column in df.columns:
        df[column] = pd.to_numeric(df[column], errors="coerce")

# Convert likely date columns.
date_candidates = [
    "application_date",
    "loan_date",
    "approval_date",
    "repayment_date"
]

for column in date_candidates:
    if column in df.columns:
        df[column] = pd.to_datetime(df[column], errors="coerce")

# Convert the default flag into a consistent 0/1 format.
if "default_flag" in df.columns:

    def convert_default(value):
        if pd.isna(value):
            return None

        if isinstance(value, bool):
            return int(value)

        if isinstance(value, (int, float)):
            if value == 1:
                return 1
            if value == 0:
                return 0

        value = str(value).strip().lower()

        default_values = {
            "1", "yes", "true", "default", "defaulted",
            "high", "high risk"
        }

        non_default_values = {
            "0", "no", "false", "paid", "repaid",
            "non-default", "non default", "low", "low risk"
        }

        if value in default_values:
            return 1

        if value in non_default_values:
            return 0

        return None

    df["default_flag"] = df["default_flag"].apply(convert_default)

# Prepare common categorical columns.
categorical_candidates = [
    "province",
    "industry",
    "repayment_status",
    "gender",
    "industry",
    "loan_purpose"
]

for column in categorical_candidates:
    if column in df.columns:
        df[column] = (
            df[column]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

# Identify the most useful available columns.
available_numeric = [
    column for column in numeric_candidates
    if column in df.columns
    and df[column].notna().any()
]

available_categorical = [
    column for column in categorical_candidates
    if column in df.columns
    and df[column].notna().any()
]

# ============================================================
# 6. SIDEBAR FILTERS
# ============================================================

st.sidebar.title("Dashboard Filters")
st.sidebar.write("Use these filters to explore the loan portfolio.")

filtered_df = df.copy()

# Province filter
if "province" in filtered_df.columns:
    province_values = sorted(
        filtered_df["province"].dropna().astype(str).unique().tolist()
    )

    selected_provinces = st.sidebar.multiselect(
        "Province",
        options=province_values,
        default=province_values
    )

    filtered_df = filtered_df[
        filtered_df["province"].astype("string").isin(selected_provinces)
    ]

# Business type filter
if "industry" in filtered_df.columns:
    business_values = sorted(
        filtered_df["industry"].dropna().astype(str).unique().tolist()
    )

    selected_businesses = st.sidebar.multiselect(
        "Industry",
        options=business_values,
        default=business_values
    )

    filtered_df = filtered_df[
        filtered_df["industry"].astype("string").isin(selected_businesses)
    ]

# Repayment status filter
if "repayment_status" in filtered_df.columns:
    repayment_values = sorted(
        filtered_df["repayment_status"].dropna().astype(str).unique().tolist()
    )

    selected_statuses = st.sidebar.multiselect(
        "Repayment Status",
        options=repayment_values,
        default=repayment_values
    )

    filtered_df = filtered_df[
        filtered_df["repayment_status"].astype("string").isin(selected_statuses)
    ]

# Default filter
if "default_flag" in filtered_df.columns:
    default_options = {
        0: "Non-default",
        1: "Default"
    }

    selected_defaults = st.sidebar.multiselect(
        "Default Outcome",
        options=[0, 1],
        default=[0, 1],
        format_func=lambda value: default_options[value]
    )

    filtered_df = filtered_df[
        filtered_df["default_flag"].isin(selected_defaults)
    ]

# Loan amount filter
if (
    "loan_amount" in filtered_df.columns
    and filtered_df["loan_amount"].notna().any()
):
    min_loan = float(filtered_df["loan_amount"].min())
    max_loan = float(filtered_df["loan_amount"].max())

    if min_loan < max_loan:
        selected_loan_range = st.sidebar.slider(
            "Loan Amount Range",
            min_value=min_loan,
            max_value=max_loan,
            value=(min_loan, max_loan)
        )

        filtered_df = filtered_df[
            filtered_df["loan_amount"].between(
                selected_loan_range[0],
                selected_loan_range[1]
            )
        ]

# Interest rate filter
if (
    "interest_rate" in filtered_df.columns
    and filtered_df["interest_rate"].notna().any()
):
    min_rate = float(filtered_df["interest_rate"].min())
    max_rate = float(filtered_df["interest_rate"].max())

    if min_rate < max_rate:
        selected_rate_range = st.sidebar.slider(
            "Interest Rate Range",
            min_value=min_rate,
            max_value=max_rate,
            value=(min_rate, max_rate)
        )

        filtered_df = filtered_df[
            filtered_df["interest_rate"].between(
                selected_rate_range[0],
                selected_rate_range[1]
            )
        ]

st.sidebar.divider()
st.sidebar.caption(
    "Filters update the dashboard charts and summary metrics."
)

# ============================================================
# 7. PORTFOLIO OVERVIEW
# ============================================================

st.header("1. Loan Portfolio Overview")

total_records = len(filtered_df)

if "loan_amount" in filtered_df.columns:
    total_loan_value = filtered_df["loan_amount"].sum()
    average_loan = filtered_df["loan_amount"].mean()
else:
    total_loan_value = None
    average_loan = None

if (
    "default_flag" in filtered_df.columns
    and filtered_df["default_flag"].notna().any()
):
    known_outcomes = filtered_df["default_flag"].dropna()
    default_count = int((known_outcomes == 1).sum())
    non_default_count = int((known_outcomes == 0).sum())

    known_count = len(known_outcomes)
    default_rate = (
        default_count / known_count * 100
        if known_count else None
    )
else:
    default_count = None
    non_default_count = None
    default_rate = None

metric_columns = st.columns(4)

metric_columns[0].metric(
    "Loan Applications",
    f"{total_records:,}"
)

metric_columns[1].metric(
    "Total Loan Value",
    f"R {total_loan_value:,.2f}"
    if total_loan_value is not None else "N/A"
)

metric_columns[2].metric(
    "Average Loan Amount",
    f"R {average_loan:,.2f}"
    if pd.notna(average_loan) else "N/A"
)

metric_columns[3].metric(
    "Default Rate",
    f"{default_rate:.1f}%"
    if default_rate is not None else "N/A"
)

if default_rate is not None:
    if default_rate < RISK_LOW_PCT:
        risk_label, risk_colour = "Low", RISK_LOW
    elif default_rate < RISK_HIGH_PCT:
        risk_label, risk_colour = "Moderate", RISK_MID
    else:
        risk_label, risk_colour = "Elevated", RISK_HIGH

    # Colour the default-rate card by risk level.
    st.markdown(
        "<style>"
        'div[data-testid="stHorizontalBlock"] > div:nth-child(4) '
        'div[data-testid="stMetric"] {'
        f"border-left-color: {risk_colour} !important;"
        "}"
        'div[data-testid="stHorizontalBlock"] > div:nth-child(4) '
        'div[data-testid="stMetricValue"] {'
        f"color: {risk_colour} !important;"
        "}"
        "</style>"
        f'<span class="risk-badge" style="background:{risk_colour};">'
        f"Portfolio risk signal: {risk_label}</span>"
        f'<span style="color:#7A6A58; font-size:0.82rem; margin-left:10px;">'
        f"Low below {RISK_LOW_PCT}% | Elevated at {RISK_HIGH_PCT}% or more"
        "</span>",
        unsafe_allow_html=True
    )

if default_rate is None:
    st.info(
        "Default rate is unavailable. Check whether default_flag contains "
        "recognised 0/1 or yes/no values."
    )

st.caption(
    "Loan value metrics assume loan_amount is recorded in South African rand. "
    "Default rate excludes records with unknown default outcomes."
)

# ============================================================
# 8. REPAYMENT AND DEFAULT ANALYSIS
# ============================================================

st.divider()
st.header("2. Repayment and Default Analysis")

left, right = st.columns(2)

with left:
    if "repayment_status" in filtered_df.columns:
        status_df = (
            filtered_df["repayment_status"]
            .dropna()
            .value_counts()
            .rename_axis("Repayment Status")
            .reset_index(name="Applications")
        )

        if not status_df.empty:
            fig = px.bar(
                status_df,
                x="Repayment Status",
                y="Applications",
                title="Applications by Repayment Status",
                color="Repayment Status",
                color_discrete_map={
                    status: status_colour(status)
                    for status in status_df["Repayment Status"].astype(str)
                },
                text="Applications"
            )

            fig.update_layout(showlegend=False)
            show_chart(fig)
        else:
            st.info("No repayment status values are available.")
    else:
        st.info("Add repayment_status to display repayment analysis.")

with right:
    if (
        "default_flag" in filtered_df.columns
        and filtered_df["default_flag"].notna().any()
    ):
        default_counts = filtered_df["default_flag"].map({
            0: "Non-default",
            1: "Default"
        }).value_counts().rename_axis("Outcome").reset_index(
            name="Applications"
        )

        fig = px.pie(
            default_counts,
            names="Outcome",
            values="Applications",
            title="Default vs Non-default Applications",
            hole=0.55,
            color_discrete_map=OUTCOME_COLOURS
        )

        fig.update_traces(
            textinfo="percent+label",
            marker=dict(line=dict(color=CARD, width=3))
        )

        show_chart(fig)
    else:
        st.info("Default outcome data is unavailable.")

# ============================================================
# 9. LOAN ANALYSIS BY PROVINCE
# ============================================================

st.divider()
st.header("3. Provincial Loan Analysis")

if "province" in filtered_df.columns:

    if "loan_amount" in filtered_df.columns:
        province_summary = (
            filtered_df.groupby("province", dropna=False)
            .agg(
                applications=("province", "size"),
                total_loan_value=("loan_amount", "sum"),
                average_loan_amount=("loan_amount", "mean")
            )
            .reset_index()
            .sort_values("total_loan_value", ascending=False)
        )

        province_summary["province"] = (
            province_summary["province"].astype(str)
        )

        fig = px.bar(
            province_summary,
            x="province",
            y="total_loan_value",
            title="Total Loan Value by Province",
            labels={
                "province": "Province",
                "total_loan_value": "Total Loan Value (R)"
            },
            text_auto=".2s",
            color_discrete_sequence=[FOREST]
        )

        show_chart(fig)

        st.subheader("Provincial Summary")
        st.dataframe(
            province_summary,
            use_container_width=True,
            hide_index=True
        )

    if (
        "default_flag" in filtered_df.columns
        and filtered_df["default_flag"].notna().any()
    ):
        province_defaults = (
            filtered_df.dropna(subset=["default_flag"])
            .groupby("province")
            .agg(
                applications=("default_flag", "size"),
                default_count=("default_flag", "sum")
            )
            .reset_index()
        )

        province_defaults["default_rate"] = (
            province_defaults["default_count"]
            / province_defaults["applications"] * 100
        )

        fig = px.bar(
            province_defaults,
            x="province",
            y="default_rate",
            title="Default Rate by Province",
            labels={
                "province": "Province",
                "default_rate": "Default Rate (%)"
            },
            text_auto=".1f",
            color="default_rate",
            color_continuous_scale=RISK_SCALE,
            range_color=RISK_RANGE
        )

        show_chart(fig)

else:
    st.info("Add province to your dataset to enable provincial analysis.")

# ============================================================
# 10. BUSINESS TYPE ANALYSIS
# ============================================================

st.divider()
st.header("4. Industry Analysis")

if "industry" in filtered_df.columns:

    business_summary = filtered_df.groupby(
        "industry", dropna=False
    ).size().reset_index(name="Applications")

    business_summary["industry"] = (
        business_summary["industry"].astype(str)
    )

    fig = px.bar(
        business_summary.sort_values(
            "Applications", ascending=False
        ),
        x="industry",
        y="Applications",
        title="Loan Applications by Industry",
        labels={
            "industry": "Business Type",
            "Applications": "Number of Applications"
        },
        text="Applications",
        color_discrete_sequence=[CLAY]
    )

    show_chart(fig)

    if (
        "default_flag" in filtered_df.columns
        and filtered_df["default_flag"].notna().any()
    ):
        business_defaults = (
            filtered_df.dropna(subset=["default_flag"])
            .groupby("industry")
            .agg(
                applications=("default_flag", "size"),
                defaults=("default_flag", "sum")
            )
            .reset_index()
        )

        business_defaults["default_rate"] = (
            business_defaults["defaults"]
            / business_defaults["applications"] * 100
        )

        st.subheader("Default Outcomes by Industry")

        fig = px.bar(
            business_defaults.sort_values(
                "default_rate", ascending=False
            ),
            x="industry",
            y="default_rate",
            title="Default Rate by Industry",
            labels={
                "industry": "Business Type",
                "default_rate": "Default Rate (%)"
            },
            text_auto=".1f",
            color="default_rate",
            color_continuous_scale=RISK_SCALE,
            range_color=RISK_RANGE
        )

        show_chart(fig)

else:
    st.info("Add industry to enable business category analysis.")

# ============================================================
# 11. MONTHLY INCOME AND LOAN AMOUNT
# ============================================================

st.divider()
st.header("5. Income and Loan Exposure")

left, right = st.columns(2)

with left:
    if "monthly_income" in filtered_df.columns:
        income_data = filtered_df.dropna(subset=["monthly_income"])

        if not income_data.empty:
            fig = px.histogram(
                income_data,
                x="monthly_income",
                nbins=20,
                title="Distribution of Monthly Business Income",
                labels={
                    "monthly_income": "Monthly Income (R)"
                },
                color_discrete_sequence=[OCHRE]
            )

            show_chart(fig)
        else:
            st.info("No valid monthly income values.")
    else:
        st.info("Add monthly_income to show income distribution.")

with right:
    if (
        "monthly_income" in filtered_df.columns
        and "loan_amount" in filtered_df.columns
    ):
        scatter_data = filtered_df.dropna(
            subset=["monthly_income", "loan_amount"]
        )

        if not scatter_data.empty:
            hover_columns = [
                column for column in [
                    "province",
                    "industry",
                    "interest_rate",
                    "repayment_status"
                ]
                if column in scatter_data.columns
            ]

            scatter_colour_map = (
                {
                    status: status_colour(status)
                    for status in scatter_data["repayment_status"]
                    .dropna().astype(str).unique()
                }
                if "repayment_status" in scatter_data.columns
                else None
            )

            fig = px.scatter(
                scatter_data,
                x="monthly_income",
                y="loan_amount",
                color=(
                    "repayment_status"
                    if "repayment_status" in scatter_data.columns
                    else None
                ),
                hover_data=hover_columns,
                color_discrete_map=scatter_colour_map,
                title="Monthly Income vs Loan Amount",
                labels={
                    "monthly_income": "Monthly Income (R)",
                    "loan_amount": "Loan Amount (R)"
                }
            )

            fig.update_traces(
                marker=dict(
                    size=8,
                    opacity=0.75,
                    line=dict(width=0.5, color=CARD)
                )
            )

            show_chart(fig)
        else:
            st.info("No valid income and loan amount pairs available.")
    else:
        st.info("Monthly income and loan amount are needed for this chart.")

# ============================================================
# 12. INTEREST RATE ANALYSIS
# ============================================================

st.divider()
st.header("6. Interest Rate Analysis")

if "interest_rate" in filtered_df.columns:

    rate_data = filtered_df.dropna(subset=["interest_rate"])

    if not rate_data.empty:

        left, right = st.columns(2)

        with left:
            fig = px.histogram(
                rate_data,
                x="interest_rate",
                nbins=20,
                title="Distribution of Interest Rates",
                labels={"interest_rate": "Interest Rate"},
                color_discrete_sequence=[CLAY]
            )

            show_chart(fig)

        with right:
            if "default_flag" in rate_data.columns:
                valid_rate_outcomes = rate_data.dropna(
                    subset=["default_flag"]
                )

                if not valid_rate_outcomes.empty:
                    fig = px.box(
                        valid_rate_outcomes.assign(
                            outcome=valid_rate_outcomes["default_flag"].map(
                                OUTCOME_LABELS
                            )
                        ),
                        x="outcome",
                        y="interest_rate",
                        color="outcome",
                        color_discrete_map=OUTCOME_COLOURS,
                        category_orders={
                            "outcome": ["Non-default", "Default"]
                        },
                        title="Interest Rates by Default Outcome",
                        labels={
                            "outcome": "Outcome",
                            "interest_rate": "Interest Rate"
                        }
                    )

                    fig.update_layout(showlegend=False)

                    show_chart(fig)
                else:
                    st.info("No known default outcomes for rate comparison.")
            else:
                st.info("Add default_flag for an outcome comparison.")

    else:
        st.info("No valid interest rate values.")

else:
    st.info("Add interest_rate to enable interest rate analysis.")

# ============================================================
# 13. YEARS IN BUSINESS ANALYSIS
# ============================================================

st.divider()
st.header("7. Business Experience and Default Risk")

if "years_in_business" in filtered_df.columns:

    experience_data = filtered_df.dropna(
        subset=["years_in_business"]
    ).copy()

    if not experience_data.empty:

        if "default_flag" in experience_data.columns:
            valid_experience = experience_data.dropna(
                subset=["default_flag"]
            ).copy()

            if not valid_experience.empty:
                valid_experience["experience_group"] = pd.cut(
                    valid_experience["years_in_business"],
                    bins=[-float("inf"), 1, 3, 5, 10, float("inf")],
                    labels=[
                        "0–1 years",
                        "1–3 years",
                        "3–5 years",
                        "5–10 years",
                        "10+ years"
                    ],
                    right=False
                )

                experience_summary = (
                    valid_experience.dropna(
                        subset=["experience_group"]
                    )
                    .groupby("experience_group", observed=False)
                    .agg(
                        applications=("default_flag", "size"),
                        defaults=("default_flag", "sum")
                    )
                    .reset_index()
                )

                experience_summary = experience_summary[
                    experience_summary["applications"] > 0
                ]

                experience_summary["default_rate"] = (
                    experience_summary["defaults"]
                    / experience_summary["applications"] * 100
                )

                fig = px.bar(
                    experience_summary,
                    x="experience_group",
                    y="default_rate",
                    title="Default Rate by Years in Business",
                    labels={
                        "experience_group": "Years in Business",
                        "default_rate": "Default Rate (%)"
                    },
                    text_auto=".1f",
            color="default_rate",
            color_continuous_scale=RISK_SCALE,
            range_color=RISK_RANGE
                )

                show_chart(fig)

                st.dataframe(
                    experience_summary,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No known default outcomes for business experience.")
        else:
            st.info("Add default_flag to compare experience and defaults.")
    else:
        st.info("No valid years_in_business values.")
else:
    st.info("Add years_in_business to enable this analysis.")

# ============================================================
# 14. CREDIT SCORE ANALYSIS (IF AVAILABLE)
# ============================================================

if "credit_score" in filtered_df.columns:

    st.divider()
    st.header("8. Credit Score Analysis")

    credit_data = filtered_df.dropna(subset=["credit_score"])

    if not credit_data.empty:

        if "default_flag" in credit_data.columns:
            credit_outcomes = credit_data.dropna(subset=["default_flag"])

            fig = px.box(
                credit_outcomes.assign(
                    outcome=credit_outcomes["default_flag"].map(
                        OUTCOME_LABELS
                    )
                ),
                x="outcome",
                y="credit_score",
                color="outcome",
                color_discrete_map=OUTCOME_COLOURS,
                category_orders={"outcome": ["Non-default", "Default"]},
                title="Credit Score Distribution by Default Outcome",
                labels={
                    "outcome": "Outcome",
                    "credit_score": "Credit Score"
                }
            )

            fig.update_layout(showlegend=False)

            show_chart(fig)
        else:
            st.info("Add default_flag to compare credit scores by outcome.")

# ============================================================
# 15. DATA QUALITY CHECKS
# ============================================================

st.divider()
st.header("9. Data Quality Summary")

quality_left, quality_right = st.columns(2)

with quality_left:
    st.subheader("Missing Values")

    missing_summary = (
        filtered_df.isna()
        .sum()
        .rename("Missing Values")
        .reset_index()
        .rename(columns={"index": "Column"})
    )

    missing_summary["Missing Percentage"] = (
        missing_summary["Missing Values"]
        / max(len(filtered_df), 1) * 100
    ).round(2)

    st.dataframe(
        missing_summary,
        use_container_width=True,
        hide_index=True
    )

with quality_right:
    st.subheader("Dataset Information")

    info = pd.DataFrame({
        "Metric": [
            "Total rows",
            "Total columns",
            "Duplicate rows",
            "Columns with missing values"
        ],
        "Value": [
            len(filtered_df),
            len(filtered_df.columns),
            int(filtered_df.duplicated().sum()),
            int((filtered_df.isna().sum() > 0).sum())
        ]
    })

    st.dataframe(
        info,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# 16. DETAILED LOAN RECORDS
# ============================================================

st.divider()
st.header("10. Explore Loan Records")

st.write(
    "Review the records that match your selected filters."
)

search_text = st.text_input(
    "Search records",
    placeholder="Enter a province, business type, repayment status, or other text"
)

display_df = filtered_df.copy()

if search_text.strip():
    searchable_columns = display_df.select_dtypes(
        include=["object", "string"]
    ).columns.tolist()

    searchable_columns += [
        column for column in [
            "application_id",
            "province",
            "industry",
            "repayment_status"
        ]
        if column in display_df.columns
        and column not in searchable_columns
    ]

    if searchable_columns:
        search_mask = pd.Series(
            False, index=display_df.index
        )

        for column in searchable_columns:
            search_mask |= (
                display_df[column]
                .astype("string")
                .str.contains(
                    search_text,
                    case=False,
                    na=False,
                    regex=False
                )
            )

        display_df = display_df[search_mask]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)

st.caption(
    f"Showing {len(display_df):,} records after filtering and search."
)

# ============================================================
# 17. DOWNLOAD FILTERED DATA
# ============================================================

st.subheader("Download Results")

csv_data = display_df.to_csv(index=False).encode("utf-8")

st.download_button(
    label="Download Filtered Loan Data (CSV)",
    data=csv_data,
    file_name="small_business_loan_risk_filtered.csv",
    mime="text/csv"
)

# Download a summary of known default outcomes.
if (
    "default_flag" in filtered_df.columns
    and filtered_df["default_flag"].notna().any()
):
    summary_data = pd.DataFrame({
        "Metric": [
            "Filtered applications",
            "Applications with known outcomes",
            "Default count",
            "Non-default count",
            "Default rate (%)"
        ],
        "Value": [
            len(filtered_df),
            int(filtered_df["default_flag"].notna().sum()),
            default_count,
            non_default_count,
            round(default_rate, 2)
            if default_rate is not None else None
        ]
    })

    st.download_button(
        label="Download Default Summary (CSV)",
        data=summary_data.to_csv(index=False).encode("utf-8"),
        file_name="small_business_loan_risk_summary.csv",
        mime="text/csv"
    )

# ============================================================
# 18. PROJECT NOTES
# ============================================================

st.divider()
st.header("About This Project")

st.markdown(
    """
    This application demonstrates a cloud-connected data analysis workflow:

    1. **Data source:** Loan application records stored in Supabase.
    2. **Data preparation:** Pandas standardises fields and converts data types.
    3. **Data analysis:** Loan exposure, repayment outcomes, and default patterns
       are explored through summaries and charts.
    4. **Visualisation:** Plotly charts respond to interactive filters.
    5. **Reporting:** Users can inspect records and export filtered results.

    **Important:** This is an exploratory portfolio dashboard, not a lending
    decision engine. Observed default rates describe this dataset and do not
    establish that a factor causes default or predict the outcome for a new
    applicant. Validate the data and any predictive model before real-world use.
    """
)

st.caption("Small Business Loan Risk Analysis | Data Engineering Portfolio")
