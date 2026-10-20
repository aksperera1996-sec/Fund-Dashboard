import streamlit as st
import pdfplumber
import pandas as pd
import plotly.express as px

# Page Configuration
st.set_page_config(
    page_title="SL Navy - Fund Situation Intelligence Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Professional Navy Blue Executive Theme CSS
st.markdown("""
    <style>
    .main { background-color: #f4f7f9; }
    .main-title { font-size: 26px; font-weight: 700; color: #0B2545; margin-bottom: 0px; }
    .sub-title { font-size: 14px; color: #134074; margin-bottom: 20px; font-weight: 500; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #EEF4F8; border-radius: 5px; padding: 10px 20px; color: #0B2545; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #134074 !important; color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🛡️ SL NAVY - FUNDS SITUATION INTELLIGENCE DASHBOARD</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Office of the Director General Budget & Finance (DG B&F) | Executive Decision Support System</p>', unsafe_allow_html=True)

# Sidebar for PDF Upload & Print
st.sidebar.header("📁 Weekly Report Upload")
uploaded_file = st.sidebar.file_uploader("Upload SL Navy Fund Situation PDF", type=["pdf"])

st.sidebar.markdown("---")
st.sidebar.header("🖨️ Report Actions")
if st.sidebar.button("🖨️ Print / Save Full Report"):
    st.sidebar.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    st.sidebar.info("Use your browser's Print dialog (Ctrl+P) to save as PDF.")

@st.cache_data
def extract_fund_data(pdf_file):
    parsed_rows = []
    current_section = "Recurrent" # Default section tracking
    
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    clean_row = [str(cell).replace('\n', ' ').strip() if cell else '' for cell in row]
                    if len(clean_row) >= 7:
                        code = clean_row[0]
                        title = clean_row[1]
                        
                        if 'CAPITAL EXPENDITURE' in title.upper() or 'CAPITAL' in code.upper():
                            current_section = "Capital"
                            continue
                        if 'RECURRENT EXPENDITURE' in title.upper() or 'RECURRENT' in code.upper():
                            current_section = "Recurrent"
                            continue
                            
                        if code in ['Object Code', '', 'None'] or 'Category' in title:
                            continue
                            
                        try:
                            def clean_val(val):
                                if not val: return 0.0
                                val_clean = val.replace(',', '').replace('(', '-').replace(')', '').strip()
                                return float(val_clean) if val_clean != '' else 0.0

                            alloc = clean_val(clean_row[2])
                            committed = clean_val(clean_row[3])
                            actual = clean_val(clean_row[5] if len(clean_row) > 5 else clean_row[4])
                            
                            pct_val = 0.0
                            for cell in clean_row:
                                if '%' in cell:
                                    pct_clean = cell.replace('%', '').strip()
                                    try:
                                        pct_val = float(pct_clean)
                                        break
                                    except:
                                        pass
                            
                            if pct_val == 0.0 and alloc > 0:
                                pct_val = round((actual / alloc) * 100, 1)

                            # Determine section based on code numbering if header missed
                            if code.startswith('2') or code.startswith('0'):
                                # Check if it's capital
                                pass

                            parsed_rows.append({
                                "Section": current_section,
                                "Object Code": code,
                                "Category / Object Title": title,
                                "Allocation": alloc,
                                "Committed": committed,
                                "Actual Amount": actual,
                                "Actual Usage %": pct_val,
                                "DG Remarks / Reasons": ""
                            })
                        except:
                            continue
                            
    return pd.DataFrame(parsed_rows)

if uploaded_file is not None:
    df = extract_fund_data(uploaded_file)
    
    if not df.empty:
        st.sidebar.success("✅ Report Parsed Successfully!")
        
        # Split Recurrent and Capital Data
        recurrent_df = df[df['Section'] == 'Recurrent']
        capital_df = df[df['Section'] == 'Capital']
        
        # High Level KPI Metrics separated by Recurrent & Capital
        st.markdown("### 📊 Executive Summary & Allocation Split")
        
        rec_alloc = 75643000000 # Rs. 75.64 Bn
        rec_actual = recurrent_df['Actual Amount'].sum()
        cap_alloc = 16224070000  # Rs. 16.22 Bn
        cap_actual = capital_df['Actual Amount'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Recurrent Allocation", "Rs. 75.64 Bn", f"Actual: Rs. {rec_actual/1e9:.2f} Bn")
        col2.metric("Capital Allocation", "Rs. 16.22 Bn", f"Actual: Rs. {cap_actual/1e9:.2f} Bn")
        col3.metric("Full Total Allocation", "Rs. 91.87 Bn", "Total Actual: Rs. 71.98 Bn")
        col4.metric("Time Elapsed Pacing", "80.0%", "292 of 365 Days Gone")
        
        st.markdown("---")
        
        # Tabs for Structured Decision Making
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🚨 Low Usage (<50%) & Remarks", 
            "🔄 Recurrent Votes", 
            "🏗️ Capital Votes", 
            "⚠️ Over-Commitments", 
            "📋 Master Data Table"
        ])
        
        with tab1:
            st.subheader("🔴 Lines Below 50% Actual Usage - Remarks & Justifications")
            st.markdown("DG B&F Review: Add or update reasons/remarks for items below 50% usage directly in the table below:")
            
            low_usage = df[(df["Actual Usage %"] < 50.0) & (df["Allocation"] > 0)].copy()
            
            if not low_usage.empty:
                # Editable DataFrame for Remarks
                edited_low_usage = st.data_editor(
                    low_usage[["Section", "Object Code", "Category / Object Title", "Allocation", "Actual Amount", "Actual Usage %", "DG Remarks / Reasons"]],
                    num_rows="fixed",
                    key="low_usage_editor",
                    use_container_width=True
                )
                
                fig_low = px.bar(
                    low_usage,
                    x="Actual Usage %",
                    y="Category / Object Title",
                    orientation='h',
                    text="Actual Usage %",
                    color="Actual Usage %",
                    color_continuous_scale="Reds",
                    title="Actual Usage Pacing Below 50 Threshold"
                )
                fig_low.update_layout(yaxis={'categoryorder':'total ascending'}, height=450)
                st.plotly_chart(fig_low, use_container_width=True)
            else:
                st.info("No items found below 50% threshold.")
                
        with tab2:
            st.subheader("🔄 Recurrent Expenditure Votes Breakdown")
            rec_display = recurrent_df[["Object Code", "Category / Object Title", "Allocation", "Committed", "Actual Amount", "Actual Usage %"]].copy()
            rec_display["Allocation (Mn)"] = (rec_display["Allocation"] / 1e6).round(2)
            rec_display["Actual (Mn)"] = (rec_display["Actual Amount"] / 1e6).round(2)
            st.dataframe(rec_display[["Object Code", "Category / Object Title", "Allocation (Mn)", "Actual (Mn)", "Actual Usage %"]], use_container_width=True)

        with tab3:
            st.subheader("🏗️ Capital Expenditure Votes Breakdown")
            cap_display = capital_df[["Object Code", "Category / Object Title", "Allocation", "Committed", "Actual Amount", "Actual Usage %"]].copy()
            cap_display["Allocation (Mn)"] = (cap_display["Allocation"] / 1e6).round(2)
            cap_display["Actual (Mn)"] = (cap_display["Actual Amount"] / 1e6).round(2)
            st.dataframe(cap_display[["Object Code", "Category / Object Title", "Allocation (Mn)", "Actual (Mn)", "Actual Usage %"]], use_container_width=True)

        with tab4:
            st.subheader("⚠️ Commitments Exceeding Allocation (Over-Committed Codes)")
            over_committed = df[df["Committed"] > df["Allocation"]].copy()
            if not over_committed.empty:
                over_committed["Excess Commitment (Mn)"] = ((over_committed["Committed"] - over_committed["Allocation"]) / 1e6).round(2)
                fig_oc = px.bar(
                    over_committed,
                    x="Excess Commitment (Mn)",
                    y="Category / Object Title",
                    orientation='h',
                    text="Excess Commitment (Mn)",
                    title="Commitments in Excess of Allocation (Rs. Million)"
                )
                fig_oc.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_oc, use_container_width=True)
                st.dataframe(over_committed[["Section", "Object Code", "Category / Object Title", "Allocation", "Committed", "Excess Commitment (Mn)"]], use_container_width=True)
            else:
                st.success("No over-committed lines detected.")

        with tab5:
            st.subheader("📋 Complete Master Data Table")
            st.dataframe(df, use_container_width=True)
            
    else:
        st.warning("⚠️ Could not extract clean table structures. Please verify the PDF format.")
else:
    st.info("👈 Please upload the weekly SL Navy Funds Situation PDF report using the sidebar to generate the DG B&F Executive Dashboard.")
