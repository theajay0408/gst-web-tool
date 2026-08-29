import streamlit as st
import pandas as pd
import json
import io

st.set_page_config(page_title="E-Commerce GST Master Automation", page_icon="⚖️", layout="wide")

# State to Code Master Mapping (Including AP 37 & Proper Formatting)
STATE_CONFIG = {
    "JAMMU AND KASHMIR": "01", "HIMACHAL PRADESH": "02", "PUNJAB": "03", "CHANDIGARH": "04",
    "UTTARAKHAND": "05", "HARYANA": "06", "DELHI": "07", "RAJASTHAN": "08",
    "UTTAR PRADESH": "09", "BIHAR": "10", "SIKKIM": "11", "ARUNACHAL PRADESH": "12",
    "NAGALAND": "13", "MANIPUR": "14", "MIZORAM": "15", "TRIPURA": "16",
    "MEGHALAYA": "17", "ASSAM": "18", "WEST BENGAL": "19", "JHARKHAND": "20",
    "ODISHA": "21", "CHHATTISGARH": "22", "MADHYA PRADESH": "23", "GUJARAT": "24",
    "DAMAN AND DIU": "25", "DADRA AND NAGAR HAVELI": "26", "MAHARASHTRA": "27",
    "ANDHRA PRADESH": "37", "KARNATAKA": "29", "GOA": "30", "LAKSHADWEEP": "31",
    "KERALA": "32", "TAMIL NADU": "33", "PUDUCHERRY": "34", "ANDAMAN AND NICOBAR ISLANDS": "35",
    "TELANGANA": "36", "LADAKH": "38", "OTHER TERRITORY": "97"
}

PLATFORM_GSTIN_MAP = {
    "Meesho": "07AARCM9332R1CQ",
    "Flipkart": "07AAGCF0285P1ZL",
    "Amazon": "07AAACA6687K1ZT"
}

def clean_state_name(raw_state):
    st_clean = str(raw_state).upper().strip()
    if "ANDHRA" in st_clean:
        return "37", "Andhra Pradesh"
    if "JAMMU" in st_clean:
        return "01", "Jammu and Kashmir"
    
    code = STATE_CONFIG.get(st_clean, "00")
    formatted_name = st_clean.title()
    return code, formatted_name

st.title("⚖️ Master E-Commerce GST & Return Processing Utility")
st.markdown("Meesho, Flipkart और Amazon के डेटा को प्रोसेस करके **Side-by-Side Pivot Report**, **GSTR-1 CSV/Excel** और **JSON** तैयार करें।")

# UI: Client Details
st.subheader("📌 Client & Return Details")
uic1, uic2 = st.columns(2)
client_gstin = uic1.text_input("Client GSTIN", value="07AABCU9603R1ZM")
return_period = uic2.selectbox("Return Period (MMYYYY)", [
    "042025","052025","062025","072025","082025","092025",
    "102025","112025","122025","012026","022026","032026",
    "042026","052026","062026","072026","082026","092026"
])

st.divider()

# Upload Section for 3 Platforms
st.subheader("📂 Step 1: Upload Platform Reports")
p_col1, p_col2, p_col3 = st.columns(3)

# 1. Meesho Upload
with p_col1:
    st.markdown("### 🟠 Meesho")
    m_sales = st.file_uploader("Meesho TCS Sales (Excel/CSV)", type=["xlsx", "xls", "csv"], key="ms")
    m_return = st.file_uploader("Meesho TCS Return (Excel/CSV)", type=["xlsx", "xls", "csv"], key="mr")

# 2. Flipkart Upload
with p_col2:
    st.markdown("### 🔵 Flipkart")
    fk_file = st.file_uploader("Flipkart GST Report (7A/7B Multi-sheet)", type=["xlsx", "xls"], key="fk")

# 3. Amazon Upload
with p_col3:
    st.markdown("### 🟡 Amazon")
    az_file = st.file_uploader("Amazon B2C Report (Excel/CSV)", type=["xlsx", "xls", "csv"], key="az")

# Master Records Collector
processed_rows = []

# --- 1. Process Meesho ---
if m_sales is not None:
    try:
        ms_df = pd.read_excel(m_sales) if m_sales.name.endswith(('xlsx', 'xls')) else pd.read_csv(m_sales)
        ms_df.columns = ms_df.columns.str.strip().str.lower()
        
        # Sales Rows
        for _, r in ms_df.iterrows():
            gross = float(r.get('total_taxable_sale_value', r.get('gross amount', 0)) or 0)
            rate = float(r.get('gst_rate', r.get('rate', 0)) or 0)
            state = str(r.get('end_customer_state_new', r.get('customer state', ''))).strip()
            if state and abs(gross) > 0.01:
                processed_rows.append({"Platform": "Meesho", "Gross": gross, "Return": 0.0, "Rate": rate, "State": state})

        # Return Rows
        if m_return is not None:
            mr_df = pd.read_excel(m_return) if m_return.name.endswith(('xlsx', 'xls')) else pd.read_csv(m_return)
            mr_df.columns = mr_df.columns.str.strip().str.lower()
            for _, r in mr_df.iterrows():
                ret_val = abs(float(r.get('total_taxable_sale_value', r.get('gross amount', 0)) or 0))
                rate = float(r.get('gst_rate', r.get('rate', 0)) or 0)
                state = str(r.get('end_customer_state_new', r.get('customer state', ''))).strip()
                if state and abs(ret_val) > 0.01:
                    processed_rows.append({"Platform": "Meesho", "Gross": 0.0, "Return": ret_val, "Rate": rate, "State": state})
    except Exception as e:
        st.error(f"Meesho File Error: {e}")

# --- 2. Process Flipkart ---
if fk_file is not None:
    try:
        xl = pd.ExcelFile(fk_file)
        # Inter-State (7B2)
        sheet_7b = [s for s in xl.sheet_names if "7(B)" in s or "7(B)(2)" in s]
        if sheet_7b:
            df_7b = pd.read_excel(fk_file, sheet_name=sheet_7b[0])
            for _, r in df_7b.iloc[1:].iterrows():
                gross = float(pd.to_numeric(r.iloc[1], errors='coerce') or 0)
                returns = float(pd.to_numeric(r.iloc[2], errors='coerce') or 0)
                rate = float(pd.to_numeric(r.iloc[4], errors='coerce') or 0)
                state = str(r.iloc[8]).strip() if len(r) > 8 else "Delhi"
                if state and (abs(gross) > 0.01 or abs(returns) > 0.01):
                    processed_rows.append({"Platform": "Flipkart", "Gross": gross, "Return": returns, "Rate": rate, "State": state})

        # Intra-State (7A2)
        sheet_7a = [s for s in xl.sheet_names if "7(A)" in s or "7(A)(2)" in s]
        if sheet_7a:
            df_7a = pd.read_excel(fk_file, sheet_name=sheet_7a[0])
            for _, r in df_7a.iloc[1:].iterrows():
                gross = float(pd.to_numeric(r.iloc[1], errors='coerce') or 0)
                returns = float(pd.to_numeric(r.iloc[2], errors='coerce') or 0)
                cgst_r = float(pd.to_numeric(r.iloc[4], errors='coerce') or 0)
                sgst_r = float(pd.to_numeric(r.iloc[6], errors='coerce') or 0)
                rate = cgst_r + sgst_r
                state = "Delhi"
                if abs(gross) > 0.01 or abs(returns) > 0.01:
                    processed_rows.append({"Platform": "Flipkart", "Gross": gross, "Return": returns, "Rate": rate, "State": state})
    except Exception as e:
        st.error(f"Flipkart File Error: {e}")

# --- 3. Process Amazon ---
if az_file is not None:
    try:
        az_df = pd.read_excel(az_file) if az_file.name.endswith(('xlsx', 'xls')) else pd.read_csv(az_file)
        for _, r in az_df.iterrows():
            trans_type = str(r.iloc[3]).strip() if len(r) > 3 else ""
            val = float(pd.to_numeric(r.iloc[28], errors='coerce') or 0) if len(r) > 28 else 0.0
            rate = float(pd.to_numeric(r.iloc[33], errors='coerce') or 0) * 100 if len(r) > 33 else 0.0
            state = str(r.iloc[24]).strip() if len(r) > 24 else ""
            
            if state and trans_type in ["Shipment", "Refund", "Cancel"]:
                if trans_type == "Shipment":
                    processed_rows.append({"Platform": "Amazon", "Gross": val, "Return": 0.0, "Rate": rate, "State": state})
                elif trans_type == "Refund":
                    processed_rows.append({"Platform": "Amazon", "Gross": 0.0, "Return": abs(val), "Rate": rate, "State": state})
                elif trans_type == "Cancel":
                    processed_rows.append({"Platform": "Amazon", "Gross": val, "Return": 0.0, "Rate": rate, "State": state})
    except Exception as e:
        st.error(f"Amazon File Error: {e}")

# --- MASTER SUMMARY & PIVOT ENGINE ---
if len(processed_rows) > 0:
    master_df = pd.DataFrame(processed_rows)
    master_df['Net Taxable'] = master_df['Gross'] - master_df['Return']
    master_df = master_df[master_df['Net Taxable'].abs() > 0.01].copy()

    # Apply Mapping Logic
    def enrich_row(row):
        code, st_proper = clean_state_name(row['State'])
        supply = "INTRA" if code == "07" or "DELHI" in st_proper.upper() else "INTER"
        ecomm_gstin = PLATFORM_GSTIN_MAP.get(row['Platform'], "")
        return pd.Series([code, st_proper, supply, ecomm_gstin], index=['StateCode', 'CleanState', 'SupplyType', 'EcommGSTIN'])

    master_df[['StateCode', 'CleanState', 'SupplyType', 'EcommGSTIN']] = master_df.apply(enrich_row, axis=1)

    # Calculate Taxes
    master_df['TaxAmount'] = (master_df['Net Taxable'] * master_df['Rate'] / 100).round(2)
    master_df['IGST'] = master_df.apply(lambda r: r['TaxAmount'] if r['SupplyType'] == "INTER" else 0.0, axis=1)
    master_df['CGST'] = master_df.apply(lambda r: round(r['TaxAmount']/2, 2) if r['SupplyType'] == "INTRA" else 0.0, axis=1)
    master_df['SGST'] = master_df.apply(lambda r: round(r['TaxAmount']/2, 2) if r['SupplyType'] == "INTRA" else 0.0, axis=1)

    # --- TABLE 1: State-Wise Summary (Left Side) ---
    t1 = master_df.groupby(['SupplyType', 'StateCode', 'CleanState', 'Rate']).agg({
        'Net Taxable': 'sum',
        'IGST': 'sum',
        'CGST': 'sum',
        'SGST': 'sum'
    }).reset_index()
    t1['POS'] = t1['StateCode'] + "-" + t1['CleanState']
    t1 = t1[['SupplyType', 'POS', 'Rate', 'Net Taxable', 'IGST', 'CGST', 'SGST']].round(2)

    # --- TABLE 2: Platform Breakdown (Right Side) ---
    t2 = master_df.groupby(['Platform', 'SupplyType']).agg({
        'Net Taxable': 'sum',
        'IGST': 'sum',
        'CGST': 'sum',
        'SGST': 'sum'
    }).reset_index().round(2)

    # --- TABLE 3: GSTR-1 B2CS Final Format ---
    b2cs_export = t1.copy()
    b2cs_export['Type'] = "OE"
    b2cs_export['Applicable % of Tax Rate'] = ""
    b2cs_export['Cess Amount'] = 0.0
    b2cs_export['E-Commerce GSTIN'] = PLATFORM_GSTIN_MAP.get("Meesho", "")
    b2cs_export = b2cs_export[['Type', 'POS', 'Rate', 'Applicable % of Tax Rate', 'Net Taxable', 'Cess Amount', 'E-Commerce GSTIN']]
    b2cs_export.rename(columns={'POS': 'Place Of Supply', 'Net Taxable': 'Taxable Value'}, inplace=True)

    st.divider()
    st.header("📊 GSTR-3B Advance Control Report (Side-by-Side Summary)")

    tab_col1, tab_col2 = st.columns([3, 2])
    with tab_col1:
        st.subheader("🔵 Table 1: State-wise POS Breakdown")
        st.dataframe(t1, use_container_width=True)
    with tab_col2:
        st.subheader("🔴 Table 2: Platform Summary (INTER / INTRA)")
        st.dataframe(t2, use_container_width=True)

    st.divider()
    st.header("📑 Table 7: GSTR-1 B2CS Final Table")
    st.dataframe(b2cs_export, use_container_width=True)

    # Downloads
    st.divider()
    st.subheader("📥 Export & Download Master Files")
    d1, d2, d3 = st.columns(3)

    # 1. Multi-Sheet Excel Export
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
        t1.to_excel(writer, index=False, sheet_name='State_Wise_Summary')
        t2.to_excel(writer, index=False, sheet_name='Platform_Summary')
        b2cs_export.to_excel(writer, index=False, sheet_name='GSTR1_B2CS_Final')
        master_df.to_excel(writer, index=False, sheet_name='Raw_Consolidated_Data')
    
    d1.download_button(
        "📊 Download Master Excel Report",
        data=excel_buf.getvalue(),
        file_name=f"GSTR_Master_Report_{return_period}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    # 2. Offline Utility CSV Export
    csv_buf = io.StringIO()
    b2cs_export.to_csv(csv_buf, index=False)
    d2.download_button(
        "📄 Download GSTR-1 B2CS CSV",
        data=csv_buf.getvalue(),
        file_name="GSTR1_B2CS_Final_Clean.csv",
        mime="text/csv",
        use_container_width=True
    )

    # 3. GSTR-1 Portal Compliant JSON Export
    json_b2cs_list = []
    for _, r in t1.iterrows():
        pos_c = r['POS'].split('-')[0]
        json_b2cs_list.append({
            "sply_ty": r['SupplyType'],
            "rt": float(r['Rate']),
            "typ": "OE",
            "pos": str(pos_c).zfill(2),
            "txval": round(float(r['Net Taxable']), 2),
            "iamt": round(float(r['IGST']), 2)
        })

    json_payload = {
        "gstin": client_gstin,
        "fp": return_period,
        "gt": 0,
        "cur_gt": 0,
        "b2cs": json_b2cs_list
    }

    d3.download_button(
        "📦 Download GSTR-1 JSON File",
        data=json.dumps(json_payload, indent=2),
        file_name=f"GSTR1_{client_gstin}_{return_period}.json",
        mime="application/json",
        use_container_width=True
    )
