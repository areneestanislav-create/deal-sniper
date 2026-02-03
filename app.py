import streamlit as st
import pdfplumber
import re
import pandas as pd
import streamlit.components.v1 as components

# 1. UI POLISH: Wide Mode + Custom Title
st.set_page_config(page_title="Deal Sniper", layout="wide")

# --- THE LOGIC ENGINE ---
def calculate_amortization(principal, rate, years):
    """Calculates the repayment schedule"""
    monthly_rate = (rate / 100) / 12
    num_payments = int(years * 12)
    
    if monthly_rate > 0:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    else:
        monthly_payment = principal / num_payments

    schedule = []
    balance = principal
    for i in range(1, num_payments + 1):
        interest = balance * monthly_rate
        principal_pay = monthly_payment - interest
        balance -= principal_pay
        schedule.append({
            "Month": i,
            "Balance": max(0, balance),
            "Interest Paid": interest
        })
        
    return pd.DataFrame(schedule)

def smart_search(text, patterns):
    """The Hunter: Loops through specific regex patterns to find the best match"""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Returns the specific capture group (the value)
            return match.group(1) 
    return None

# --- SIDEBAR (INPUT) ---
with st.sidebar:
    st.header("📂 Deal Input")
    uploaded_file = st.file_uploader("Upload Agreement (PDF)", type="pdf")
    st.markdown("---")
    st.write("Or adjust manually:")

# Default Values
default_amount = 1000000.0
default_rate = 6.5
status_msg = "Waiting for file..."

# --- THE BRAIN (EXTRACTION) ---
if uploaded_file:
    with pdfplumber.open(uploaded_file) as pdf:
        text = ""
        for page in pdf.pages[:10]: # Read first 10 pages for better accuracy
            text += page.extract_text()
            
    # THE KEYWORD HUNTER
    # 1. Find Money (Looks for "Principal Amount $X" or just "$X")
    found_amount_str = smart_search(text, [
        r"Principal Amount[:\s]+(\$[\d,]+\.\d{2})",
        r"Loan Amount[:\s]+(\$[\d,]+\.\d{2})",
        r"(\$[\d,]{6,}\.\d{2})" # Fallback: Just look for a big number
    ])
    
    # 2. Find Rate (Looks for "Interest Rate X%" or just "X%")
    found_rate_str = smart_search(text, [
        r"Interest Rate[:\s]+(\d+\.\d+)%",
        r"Fixed Rate[:\s]+(\d+\.\d+)%",
        r"(\d+\.\d+)%\s+per\s+annum"
    ])
    
    # Clean and Apply Data
    if found_amount_str:
        clean_amount = float(found_amount_str.replace("$", "").replace(",", ""))
        default_amount = clean_amount
        status_msg = "✅ Data Extracted Successfully"
    
    if found_rate_str:
        default_rate = float(found_rate_str)

# --- CONTROLS ---
principal = st.sidebar.number_input("Principal ($)", value=default_amount, step=10000.0)
rate = st.sidebar.slider("Interest Rate (%)", 1.0, 15.0, default_rate)
years = st.sidebar.slider("Term (Years)", 1, 30, 10)

# --- MAIN DASHBOARD ---
st.title("🏦 Deal Sniper")
st.caption(f"Status: {status_msg}")

# 1. Top Level Metrics (The "Pitch")
col1, col2, col3, col4 = st.columns(4)
df = calculate_amortization(principal, rate, years)
total_interest = df["Interest Paid"].sum()
monthly_pmt = (principal + total_interest) / (years * 12)

col1.metric("Loan Amount", f"${principal:,.0f}")
col2.metric("Monthly Payment", f"${monthly_pmt:,.2f}")
col3.metric("Total Interest", f"${total_interest:,.0f}", delta="Lender Profit")
col4.metric("DSCR Risk", "Low", "1.25x Coverage") # Placeholder for future logic

# 2. The Visuals
st.markdown("### 📉 Repayment Trajectory")
st.area_chart(df, x="Month", y="Balance", color="#00FF00")

# 3. Export Tools
st.markdown("---")
c1, c2 = st.columns([1, 4])

with c1:
    # CSV Download
    df_rounded = df.round(2)
    csv = df_rounded.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Excel", csv, "deal_data.csv", "text/csv")

with c2:
    # The "Print PDF" Hack (Injects JavaScript to open print dialog)
    if st.button("🖨️ Print Report"):
        components.html("<script>window.print()</script>", height=0, width=0)

