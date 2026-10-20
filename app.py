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

# Professional Deep Navy Blue Theme CSS
st.markdown("""
    <style>
    .stApp { background-color: #0b192c; color: #e2e8f0; }
    .main-title { font-size: 28px; font-weight: 700; color: #60a5fa; margin-bottom: 0px; }
    .sub-title { font-size: 14px; color: #94a3b8; margin-bottom: 20px; font-weight: 500; }
    .metric-card { background-color: #1e293b; padding: 20px; border-radius: 10px; border-left: 5px solid #3b82f6; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; background-color: #0b192c; }
    .stTabs [data-baseweb="tab"] { background-color: #1e293b; border-radius: 6px; padding: 10px 20px; color: #f8fafc; font-weight: 600; border: 1px solid #334155; }
    .stTabs [aria-selected="true"] { background-color: #3b82f6 !important; color: #ffffff !important; }
    div.stMarkdown p { color: #cbd5e1; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🛡️ SL NAVY - FUNDS SITUATION INTELLIGENCE DASHBOARD</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Office of the Director General Budget & Finance (DG B&F) | Executive Decision Support System</p>', unsafe_allow_html=True)

# Sidebar for PDF Upload & Actions
st.sidebar.header("📁 Weekly Report Upload")
uploaded_file = st.sidebar.file_uploader("Upload SL Navy Fund Situation PDF", type=["pdf"])

st.sidebar.markdown("---")
st.sidebar.header("🖨️ Report Actions")
if st.sidebar.button("🖨️ Print / Export Full Report"):
    st.sidebar.markdown("<script>window.print();</script>", unsafe_allow_html=True)
    st.sidebar.info("Use browser Print dialog (Ctrl+P) to save as PDF.")

def format_currency(val):
    if pd.isna(val): return "Rs. 0"
    return f"Rs. {val:,.2f}"

@st.cache_data
def extract_fund_data(pdf_file):
    parsed_rows = []
    current_section = "Recurrent"
    
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
                            
                        if code in ['Object Code', '', 'None'] or 'Category' in title or 'Total' in title:
                            continue
                            
                        try:
                            def clean_val(val):
                                if not val: return 0.0
                                val_clean = val.replace(',', '').replace('(', '-').replace(')', '').strip()
                                return float(val_clean) if val_clean != '' else 0.0

                            alloc = clean_val(clean_row[2])
                            committed = clean_val(clean_row[3])
                            comm_bal = clean_val(clean_row[4] if len(clean_row) > 4 else 0.0)
                            actual = clean_val(clean_row[5] if len(clean_row) > 5 else clean_row[4])
                            act_bal = clean_val(clean_row[6] if len(clean_row) > 6 else 0.0)
                            
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

                            parsed_rows.append({
                                "Section": current_section,
                                "Object Code": code,
                                "Category / Object Title": title,
                                "Allocation": alloc,
                                "Committed": committed,
                                "Committed Balance": comm_bal,
                                "Actual Amount": actual,
                                "Actual Balance": act_bal,
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
        
        recurrent_df = df[df['Section'] == 'Recurrent']
        capital_df = df[df['Section'] == 'Capital']
        
        # Summary Calculations
        rec_alloc = recurrent_df['Allocation'].sum()
        rec_comm = recurrent_df['Committed'].sum()
        rec_comm_bal = recurrent_df['Committed Balance'].sum()
        rec_actual = recurrent_df['Actual Amount'].sum()
        rec_act_bal = recurrent_df['Actual Balance'].sum()
        rec_pct = round((rec_actual / rec_alloc * 100), 1) if rec_alloc > 0 else 0
        
        cap_alloc = capital_df['Allocation'].sum()
        cap_comm = capital_df['Committed'].sum()
        cap_comm_bal = capital_df['Committed Balance'].sum()
        cap_actual = capital_df['Actual Amount'].sum()
        cap_act_bal = capital_df['Actual Balance'].sum()
        cap_pct = round((cap_actual / cap_alloc * 100), 1) if cap_alloc > 0 else 0
        
        full_alloc = df['Allocation'].sum()
        full_comm = df['Committed'].sum()
        full_comm_bal = df['Committed Balance'].sum()
        full_actual = df['Actual Amount'].sum()
        full_act_bal = df['Actual Balance'].sum()
        full_pct = round((full_actual / full_alloc * 100), 1) if full_alloc > 0 else 0
        
        # Dashboard Top Metrics Split
        st.markdown("### 📊 Executive Summary & Vote-Wise Breakdown")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("#### 🔄 Recurrent Votes")
            st.metric("Allocation", f"Rs. {rec_alloc:,.2f}")
            st.metric("Committed / Balance", f"Rs. {rec_comm:,.2f}", f"Bal: {rec_comm_bal:,.2f}")
            st.metric("Actual Expenditure", f"Rs. {rec_actual:,.2f}", f"Usage: {rec_pct}%")
            st.metric("Actual Balance", f"Rs. {rec_act_bal:,.2f}")
            
        with col2:
            st.markdown("#### 🏗️ Capital Votes")
            st.metric("Allocation", f"Rs. {cap_alloc:,.2f}")
            st.metric("Committed / Balance", f"Rs. {cap_comm:,.2f}", f"Bal: {cap_comm_bal:,.2f}")
            st.metric("Actual Expenditure", f"Rs. {cap_actual:,.2f}", f"Usage: {cap_pct}%")
            st.metric("Actual Balance", f"Rs. {cap_act_bal:,.2f}")
            
        with col3:
            st.markdown("#### 🛡️ Full Total Summary")
            st.metric("Total Allocation", f"Rs. {full_alloc:,.2f}")
            st.metric("Total Committed", f"Rs. {full_comm:,.2f}", f"Bal: {full_comm_bal:,.2f}")
            st.metric("Total Actual Usage", f"Rs. {full_actual:,.2f}", f"Usage: {full_pct}%")
            st.metric("Time Elapsed Pacing", "80.0%", "292 of 365 Days Gone")
        
        st.markdown("---")
        
        # Tabs for Structured Decision Making
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🚨 Low Usage (<50%) - Recurrent", 
            "⚠️ Low Usage (<50%) - Capital", 
            "🔄 Recurrent Votes Master", 
            "🏗️ Capital Votes Master", 
            "📋 Over-Commitments & Risks"
        ])
        
        with tab1:
            st.subheader("🔴 Recurrent Votes Below 50% Actual Usage")
            rec_low = recurrent_df[(recurrent_df["Actual Usage %"] < 50.0) & (recurrent_df["Allocation"] > 0)].copy()
            if not rec_low.empty:
                edited_rec_low = st.data_editor(
                    rec_low[["Object Code", "Category / Object Title", "Allocation", "Committed", "Actual Amount", "Actual Usage %", "DG Remarks / Reasons"]],
                    num_rows="fixed",
                    key="rec_low_editor",
                    use_container_width=True
                )
            else:
                st.success("No Recurrent items below 50% usage.")
                
        with tab2:
            st.subheader("🔴 Capital Votes Below 50% Actual Usage")
            cap_low = capital_df[(capital_df["Actual Usage %"] < 50.0) & (capital_df["Allocation"] > 0)].copy()
            if not cap_low.empty:
                edited_cap_low = st.data_editor(
                    cap_low[["Object Code", "Category / Object Title", "Allocation", "Committed", "Actual Amount", "Actual Usage %", "DG Remarks / Reasons"]],
                    num_rows="fixed",
                    key="cap_low_editor",
                    use_container_width=True
                )
            else:
                st.success("No Capital items below 50% usage.")

        with tab3:
            st.subheader("🔄 Complete Recurrent Votes Table")
            st.dataframe(recurrent_df[["Object Code", "Category / Object Title", "Allocation", "Committed", "Committed Balance", "Actual Amount", "Actual Balance", "Actual Usage %"]], use_container_width=True)

        with tab4:
            st.subheader("🏗️ Complete Capital Votes Table")
            st.dataframe(capital_df[["Object Code", "Category / Object Title", "Allocation", "Committed", "Committed Balance", "Actual Amount", "Actual Balance", "Actual Usage %"]], use_container_width=True)

        with tab5:
            st.subheader("⚠️ Over-Committed Lines (Commitment > Allocation)")
            over_committed = df[df["Committed"] > df["Allocation"]].copy()
            if not over_committed.empty:
                over_committed["Excess Commitment"] = over_committed["Committed"] - over_committed["Allocation"]
                st.dataframe(over_committed[["Section", "Object Code", "Category / Object Title", "Allocation", "Committed", "Excess Commitment"]], use_container_width=True)
            else:
                st.success("No over-committed lines detected.")
            
    else:
        st.warning("⚠️ Could not extract clean table structures. Please verify the PDF format.")
else:
    st.info("👈 Please upload the weekly SL Navy Funds Situation PDF report using the sidebar to generate the DG B&F Executive Dashboard.")
