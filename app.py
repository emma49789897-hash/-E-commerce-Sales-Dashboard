import os
import pandas as pd
import streamlit as st
import plotly.express as px
from groq import Groq


# ============================================================
# E-COMMERCE SALES DASHBOARD
# ============================================================

st.set_page_config(
    page_title="E-Commerce Sales Dashboard",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("📊 E-Commerce Sales Dashboard")

st.write(
    "Upload your CSV or Excel sales data to analyze "
    "revenue, orders, products, categories and profit."
)


# ============================================================
# FUNCTIONS
# ============================================================

def read_data(file):

    if file.name.lower().endswith(".csv"):
        return pd.read_csv(file)

    return pd.read_excel(file)


def find_column(df, possible_names):

    columns = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for name in possible_names:

        if name.lower() in columns:
            return columns[name.lower()]

    return None


def get_groq_client():

    api_key = None

    # Streamlit Cloud Secrets
    try:
        api_key = st.secrets.get("GROQ_API_KEY")
    except Exception:
        pass

    # Environment variable
    if not api_key:
        api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        return None

    return Groq(api_key=api_key)


def generate_ai_insights(summary):

    client = get_groq_client()

    if client is None:

        return """
⚠️ Groq API key is not configured.

Please add GROQ_API_KEY in Streamlit Cloud Secrets.
"""

    prompt = f"""
You are an expert e-commerce business analyst.

Analyze the following calculated sales summary:

{summary}

Provide:

1. Three important business insights
2. Two possible business problems or risks
3. Three practical recommendations

Use only the numbers provided.
Do not invent numbers.

Keep the response clear and easy to understand.
"""

    try:

        response = client.chat.completions.create(

            model="openai/gpt-oss-120b",
            messages=[

                {
                    "role": "system",
                    "content":
                    "You are a careful e-commerce analytics assistant."
                },

                {
                    "role": "user",
                    "content": prompt
                }

            ],

            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:

        return f"Groq error: {e}"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header("📁 Upload Sales Data")

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx"]
    )

    st.divider()

    st.header("🔎 Filters")


# ============================================================
# CHECK FILE
# ============================================================

if uploaded_file is None:

    st.info(
        "👈 Please upload a CSV or Excel sales file "
        "from the sidebar."
    )

    st.subheader("📋 Recommended Columns")

    st.code(
        """
Date
Product
Category
Quantity
Revenue
Cost
Profit
City
        """
    )

    st.stop()


# ============================================================
# READ FILE
# ============================================================

try:

    df = read_data(uploaded_file)

except Exception as e:

    st.error(
        f"Unable to read the file: {e}"
    )

    st.stop()


if df.empty:

    st.warning(
        "The uploaded file is empty."
    )

    st.stop()


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

df.columns = [
    str(column).strip()
    for column in df.columns
]


# ============================================================
# FIND IMPORTANT COLUMNS
# ============================================================

date_column = find_column(
    df,
    [
        "date",
        "order date",
        "order_date",
        "sales date"
    ]
)


product_column = find_column(
    df,
    [
        "product",
        "product name",
        "product_name",
        "item"
    ]
)


category_column = find_column(
    df,
    [
        "category",
        "product category"
    ]
)


quantity_column = find_column(
    df,
    [
        "quantity",
        "qty",
        "units",
        "units sold"
    ]
)


revenue_column = find_column(
    df,
    [
        "revenue",
        "sales",
        "sales amount",
        "total sales",
        "amount"
    ]
)


cost_column = find_column(
    df,
    [
        "cost",
        "total cost",
        "cost amount"
    ]
)


profit_column = find_column(
    df,
    [
        "profit",
        "net profit",
        "gross profit"
    ]
)


city_column = find_column(
    df,
    [
        "city",
        "customer city",
        "location"
    ]
)


# ============================================================
# FILTERED DATA
# ============================================================

filtered_df = df.copy()


# ============================================================
# DATE FILTER
# ============================================================

if date_column:

    filtered_df[date_column] = pd.to_datetime(
        filtered_df[date_column],
        errors="coerce"
    )

    valid_dates = filtered_df[
        date_column
    ].dropna()

    if not valid_dates.empty:

        with st.sidebar:

            date_range = st.date_input(
                "Date Range",
                value=(
                    valid_dates.min().date(),
                    valid_dates.max().date()
                )
            )

        if (
            isinstance(date_range, tuple)
            and len(date_range) == 2
        ):

            start_date = date_range[0]
            end_date = date_range[1]

            filtered_df = filtered_df[
                (
                    filtered_df[date_column].dt.date
                    >= start_date
                )
                &
                (
                    filtered_df[date_column].dt.date
                    <= end_date
                )
            ]


# ============================================================
# CATEGORY FILTER
# ============================================================

if category_column:

    categories = sorted(
        filtered_df[
            category_column
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    with st.sidebar:

        selected_categories = st.multiselect(
            "Category",
            categories
        )

    if selected_categories:

        filtered_df = filtered_df[
            filtered_df[
                category_column
            ]
            .astype(str)
            .isin(selected_categories)
        ]


# ============================================================
# PRODUCT FILTER
# ============================================================

if product_column:

    products = sorted(
        filtered_df[
            product_column
        ]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    with st.sidebar:

        selected_products = st.multiselect(
            "Product",
            products
        )

    if selected_products:

        filtered_df = filtered_df[
            filtered_df[
                product_column
            ]
            .astype(str)
            .isin(selected_products)
        ]


# ============================================================
# CALCULATE KPIs
# ============================================================

revenue = 0

cost = 0

profit = 0

units = 0

orders = len(filtered_df)


if revenue_column:

    revenue = pd.to_numeric(
        filtered_df[
            revenue_column
        ],
        errors="coerce"
    ).fillna(0).sum()


if cost_column:

    cost = pd.to_numeric(
        filtered_df[
            cost_column
        ],
        errors="coerce"
    ).fillna(0).sum()


if profit_column:

    profit = pd.to_numeric(
        filtered_df[
            profit_column
        ],
        errors="coerce"
    ).fillna(0).sum()

elif revenue_column and cost_column:

    profit = revenue - cost


if quantity_column:

    units = pd.to_numeric(
        filtered_df[
            quantity_column
        ],
        errors="coerce"
    ).fillna(0).sum()


if revenue > 0:

    profit_margin = (
        profit / revenue
    ) * 100

else:

    profit_margin = 0


# ============================================================
# KPI SECTION
# ============================================================

st.subheader("📌 Key Performance Indicators")


col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "💰 Revenue",
        f"{revenue:,.2f}"
    )


with col2:

    st.metric(
        "📦 Orders",
        f"{orders:,}"
    )


with col3:

    st.metric(
        "🛒 Units Sold",
        f"{units:,.0f}"
    )


with col4:

    st.metric(
        "📈 Profit",
        f"{profit:,.2f}"
    )


with col5:

    st.metric(
        "📊 Profit Margin",
        f"{profit_margin:.2f}%"
    )


# ============================================================
# DATA QUALITY
# ============================================================

with st.expander("🧹 Data Quality Check"):

    q1, q2, q3 = st.columns(3)

    with q1:

        st.metric(
            "Total Rows",
            f"{len(df):,}"
        )

    with q2:

        st.metric(
            "Missing Values",
            f"{int(df.isna().sum().sum()):,}"
        )

    with q3:

        st.metric(
            "Duplicate Rows",
            f"{int(df.duplicated().sum()):,}"
        )

    st.write(
        "Missing values by column:"
    )

    st.dataframe(
        df.isna().sum().rename(
            "Missing Values"
        ),
        use_container_width=True
    )


# ============================================================
# SALES TREND
# ============================================================

st.subheader("📈 Sales Performance")


left_column, right_column = st.columns(2)


with left_column:

    if date_column and revenue_column:

        trend_df = filtered_df.copy()

        trend_df[revenue_column] = pd.to_numeric(
            trend_df[revenue_column],
            errors="coerce"
        ).fillna(0)

        trend_df = trend_df.dropna(
            subset=[date_column]
        )

        if not trend_df.empty:

            monthly_sales = (
                trend_df
                .set_index(date_column)
                .resample("ME")[
                    revenue_column
                ]
                .sum()
                .reset_index()
            )

            fig = px.line(
                monthly_sales,
                x=date_column,
                y=revenue_column,
                markers=True,
                title="Monthly Revenue Trend"
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    else:

        st.info(
            "Revenue trend requires Date and Revenue/Sales columns."
        )


# ============================================================
# TOP PRODUCTS
# ============================================================

with right_column:

    if product_column and revenue_column:

        product_df = filtered_df.copy()

        product_df[revenue_column] = pd.to_numeric(
            product_df[revenue_column],
            errors="coerce"
        ).fillna(0)

        top_products = (
            product_df
            .groupby(product_column)[
                revenue_column
            ]
            .sum()
            .sort_values(
                ascending=False
            )
            .head(10)
            .reset_index()
        )

        fig = px.bar(
            top_products,
            x=revenue_column,
            y=product_column,
            orientation="h",
            title="Top 10 Products by Revenue"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "Top products requires Product and Revenue/Sales columns."
        )


# ============================================================
# CATEGORY ANALYSIS
# ============================================================

left_column, right_column = st.columns(2)


with left_column:

    if category_column and revenue_column:

        category_df = filtered_df.copy()

        category_df[revenue_column] = pd.to_numeric(
            category_df[revenue_column],
            errors="coerce"
        ).fillna(0)

        category_sales = (
            category_df
            .groupby(category_column)[
                revenue_column
            ]
            .sum()
            .reset_index()
            .sort_values(
                revenue_column,
                ascending=False
            )
        )

        fig = px.bar(
            category_sales,
            x=category_column,
            y=revenue_column,
            title="Revenue by Category"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "Category analysis requires Category and Revenue columns."
        )


# ============================================================
# UNITS SOLD
# ============================================================

with right_column:

    if product_column and quantity_column:

        units_df = filtered_df.copy()

        units_df[quantity_column] = pd.to_numeric(
            units_df[quantity_column],
            errors="coerce"
        ).fillna(0)

        top_units = (
            units_df
            .groupby(product_column)[
                quantity_column
            ]
            .sum()
            .sort_values(
                ascending=False
            )
            .head(10)
            .reset_index()
        )

        fig = px.bar(
            top_units,
            x=product_column,
            y=quantity_column,
            title="Top Products by Units Sold"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    else:

        st.info(
            "Units chart requires Product and Quantity columns."
        )


# ============================================================
# BUSINESS SUMMARY
# ============================================================

st.subheader("💡 Business Summary")


summary = f"""
Revenue: {revenue:.2f}

Orders: {orders}

Units Sold: {units:.2f}

Cost: {cost:.2f}

Profit: {profit:.2f}

Profit Margin: {profit_margin:.2f}%
"""


st.code(summary)


# ============================================================
# AI INSIGHTS
# ============================================================

if st.button(
    "🤖 Generate AI Business Insights",
    type="primary"
):

    with st.spinner(
        "AI is analyzing your sales data..."
    ):

        insights = generate_ai_insights(
            summary
        )

    st.markdown(
        "### 🤖 AI Business Insights"
    )

    st.markdown(
        insights
    )


# ============================================================
# DOWNLOAD
# ============================================================

st.subheader("📥 Download Filtered Data")


csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download CSV",
    data=csv_data,
    file_name="filtered_sales_data.csv",
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "E-Commerce Sales Dashboard | "
    "Python + Streamlit + Pandas + Plotly + Groq"
)
