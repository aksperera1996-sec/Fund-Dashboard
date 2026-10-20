import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

# Page Configuration
st.set_page_config(
    page_title="Fund Situation Dashboard",
    page_icon="📊",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ Executive Fund Situation Dashboard")
st.markdown("Upload your weekly PDF summary report to generate instant analytics, charts, and actionable insights.")

# Sidebar File Uploader
st.sidebar.header("📁 Document Upload")
uploaded_file = st.sidebar.file_uploader("Upload Summary PDF", type=["pdf"])

def extract_data_from_pdf(pdf_file):
    rows = []
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Clean up empty cells / newlines
                    clean_row = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                    if len(clean_row) >= 7 and clean_row[0] != 'Object Code':
                        rows.append(clean_row)
    
    # Process extracted data into DataFrame
    parsed_data = []
    for r in rows:
        code = r[0]
        title = r[1]
        try:
            alloc = float(r[2].replace(',', '').replace('(', '-').replace(')', '')) if r[2] else 0.0
            comm = float(r[3].replace(',', '').replace('(', '-').replace(')', '')) if r[3] else 0.0
            actual = float(r[5].replace(',', '').replace('(', '-').replace(')', '')) if r[5] else 0.0
            usage_str = r[7] if len(r) > 7 and '%' in r[7] else (r[6] if '%' in r[6] else '0%')
            usage_pct = float(usage_str.replace('%', '').strip()) if '%' in usage_str else 0.0
            
            parsed_data.append({
                "Object Code": code,
                "Title": title,
                "Allocation": alloc,
                "Committed": comm,
                "Actual Amount": actual,
                "Actual Usage %": usage_pct
            })
        except:
            continue
            
    return pd.DataFrame(parsed_data)

if uploaded_file is not None:
    try:
        df = extract_data_from_pdf(uploaded_file)
        
        if not df.empty:
            st.success("✅ PDF processed successfully!")
            
            # Key Summary KPIs
            total_alloc = df["Allocation"].sum()
            total_comm = df["Committed"].sum()
            total_actual = df["Actual Amount"].sum()
            overall_usage = (total_actual / total_alloc * 100) if total_alloc > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Allocation", f"Rs. {total_alloc/1e9:.2f} Bn")
            col2.metric("Committed Amount", f"Rs. {total_comm/1e9:.2f} Bn")
            col3.metric("Actual Expenditure", f"Rs. {total_actual/1e9:.2f} Bn")
            col4.metric("Overall Actual Usage", f"{overall_usage:.1f}%")
            
            st.markdown("---")
            
            # Interactive Visual Tabs
            tab1, tab2, tab3 = st.tabs(["📉 Critical Alerts (<50% Usage)", "📊 Allocation & Usage Analytics", "📋 Detailed Data Table"])
            
            with tab1:
                st.subheader("⚠️ Critical Review: Lines Below 50% Usage")
                low_usage_df = df[(df["Actual Usage %"] < 50.0) & (df["Allocation"] > 0)].sort_values(by="Actual Usage %")
                
                if not low_usage_df.empty:
                    fig_low = px.bar(
                        low_usage_df,
                        x="Actual Usage %",
                        y="Title",
                        orientation='h',
                        color="Actual Usage %",
                        color_continuous_scale="Reds_r",
                        title="Projects/Items Needing Immediate Follow-up"
                    )
                    st.plotly_chart(fig_low, use_container_width=True)
                    st.dataframe(low_usage_df[["Object Code", "Title", "Allocation", "Actual Amount", "Actual Usage %"]], use_container_width=True)
                else:
                    st.info("No items below 50% usage found.")
            
            with tab2:
                st.subheader("Top Expenditures & Budget Allocation")
                top_items = df.sort_values(by="Allocation", ascending=False).head(10)
                fig_top = px.bar(
                    top_items,
                    x="Title",
                    y=["Allocation", "Committed", "Actual Amount"],
                    barmode="group",
                    title="Top 10 Budget Allocations vs Spending (Rs.)"
                )
                st.plotly_chart(fig_top, use_container_width=True)
                
            with tab3:
                st.subheader("Complete Funds Summary Data")
                st.dataframe(df, use_container_width=True)

        else:
            st.warning("Could not automatically parse tables from this layout. Showing fallback summary view.")
    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("👈 Please upload your weekly PDF summary report using the sidebar on the left.")
