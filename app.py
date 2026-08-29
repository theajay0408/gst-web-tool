import streamlit as st
import pandas as pd
import json
import io

st.set_page_config(page_title="E-Commerce GST Master Automation", page_icon="⚖️", layout="wide")

# Complete GST State Master Dictionary with Variations
STATE_MASTER = {
    "JAMMU AND KASHMIR": ("01", "Jammu and Kashmir"),
    "JAMMU & KASHMIR": ("01", "Jammu and Kashmir"),
    "HIMACHAL PRADESH": ("02", "Himachal Pradesh"),
    "PUNJAB": ("03", "Punjab"),
    "CHANDIGARH": ("04", "Chandigarh"),
    "UTTARAKHAND": ("05", "Uttarakhand"),
    "UTTRANCHAL": ("05", "Uttarakhand"),
    "HARYANA": ("06", "Haryana"),
    "DELHI": ("07", "Delhi"),
    "RAJASTHAN": ("08", "Rajasthan"),
    "UTTAR PRADESH": ("09", "Uttar Pradesh"),
    "BIHAR": ("10", "Bihar"),
    "SIKKIM": ("11", "Sikkim"),
    "ARUNACHAL PRADESH": ("12", "Arunachal Pradesh"),
    "NAGALAND": ("13", "Nagaland"),
    "MANIPUR": ("14", "Manipur"),
    "MIZORAM": ("15", "Mizoram"),
    "TRIPURA": ("16", "Tripura"),
    "MEGHALAYA": ("17", "Meghalaya"),
    "ASSAM": ("18", "Assam"),
    "WEST BENGAL": ("19", "West Bengal"),
    "JHARKHAND": ("20", "Jharkhand"),
    "ODISHA": ("21", "Odisha"),
    "ORISSA": ("21", "Odisha"),
    "CHHATTISGARH": ("22", "Chhattisgarh"),
    "CHATTISGARH": ("22", "Chhattisgarh"),
    "MADHYA PRADESH": ("23", "Madhya Pradesh"),
    "GUJARAT": ("24", "Gujarat"),
    "DAMAN AND DIU": ("25", "Daman and Diu"),
    "DADRA AND NAGAR HAVELI": ("26", "Dadra and Nagar Haveli"),
    "DADRA & NAGAR HAVELI AND DAMAN & DIU": ("26", "Dadra and Nagar Haveli and Daman and Diu"),
    "MAHARASHTRA": ("27", "Maharashtra"),
    "ANDHRA PRADESH": ("37", "Andhra Pradesh"),
    "ANDHRA PRADESH(NEW)": ("37", "Andhra Pradesh"),
    "KARNATAKA": ("29", "Karnataka"),
    "GOA": ("30", "Goa"),
    "LAKSHADWEEP": ("31", "Lakshadweep"),
    "KERALA": ("32", "Kerala"),
    "TAMIL NADU": ("33", "Tamil Nadu"),
    "PUDUCHERRY": ("34", "Puducherry"),
    "PONDICHERRY": ("34", "Puducherry"),
    "ANDAMAN AND NICOBAR ISLANDS": ("35", "Andaman and Nicobar Islands"),
    "ANDAMAN & NICOBAR": ("35", "Andaman and Nicobar Islands"),
    "TELANGANA": ("36", "Telangana"),
    "LADAKH": ("38", "Ladakh"),
    "OTHER TERRITORY": ("97", "Other Territory")
}

PLATFORM_GSTIN_MAP = {
    "Meesho": "07AARCM9332R1CQ",
    "Flipkart": "07AAGCF0285P1ZL",
    "Amazon": "07AAACA6687K1ZT"
}

def clean_state_info(raw_state):
    st_clean = str(raw_state).upper().strip()
    if "ANDHRA" in st_clean:
        return "37", "Andhra Pradesh"
    if "JAMMU" in st_clean:
        return "01", "Jammu and Kashmir"
    if "CHATTISGARH" in st_clean or "CHHATTISGARH" in st_clean:
        return "22", "Chhattisgarh"
    if "ORISSA" in st_clean or "ODISHA" in st_clean:
        return "21", "Odisha"

    if st_clean in STATE_MASTER:
        return STATE_MASTER[st_clean]
    
    # Fallback
    return "00", st_clean.title()

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

with p_col1:
    st.markdown("### 🟠 Meesho")
    m_sales = st.file_uploader("Meesho TCS Sales (Excel/CSV)", type=["xlsx", "xls", "csv"], key="ms")
    m_return = st.file_uploader("Meesho TCS Return (Excel/CSV)", type=["xlsx", "xls", "csv"], key="mr")

with p_col2:
    st.markdown("### 🔵 Flipkart")
    fk_file = st.file_uploader("Flipkart GST Report (7A/7B Multi-sheet)", type=["xlsx", "xls"], key="fk")

with p_col3:
    st.markdown("### 🟡 Amazon")
    az_file = st.file_uploader("Amazon B2C Report (Excel/CSV)", type=["xlsx", "xls", "csv"], key="az")

processed_rows = []

# 1. Process Meesho
if m_sales is not None:
    try:
        ms_df = pd.read_excel(m_sales) if m_sales.name.endswith(('xlsx', 'xls')) else pd.read_csv(m_sales)
        ms_df.columns = ms_df.columns.str.strip().str.lower()
        
        for _, r in ms_df.iterrows():
            gross = float(pd.to_numeric(r.get('total_taxable_sale_value', r.get('gross amount', 0)), errors='coerce') or 0)
            rate = float(pd.to_numeric(r.get('gst_rate', r.get('rate', 0)), errors='coerce') or 0)
            state = str(r.get('end_customer_state_new', r.get('customer state', ''))).strip()
            if state and abs(gross) > 0.001:
                processed_rows.append({"Platform": "Meesho", "Gross": gross, "Return": 0.0, "Rate": rate, "State": state})

        if m_return is not None:
            mr_df = pd.read_excel(m_return) if m_return.name.endswith(('xlsx', 'xls')) else pd.read_csv(m_return)
            mr_df.columns = mr_df.columns.str.strip().str.lower()
            for _, r in mr_df.iterrows():
                ret_val = abs(float(pd.to_numeric(r.get('total_taxable_sale_value', r.get('gross amount', 0)), errors='coerce') or 0))
                rate = float(pd.to_numeric(r.get('gst_rate', r.get('rate', 0)), errors='coerce') or 0)
                state = str(r.get('end_customer_state_new', r.get('customer state', ''))).strip()
                if state and abs(ret_val) > 0.001:
                    processed_rows.append({"Platform": "Meesho", "Gross": 0.0, "Return": ret_val, "Rate": rate, "State": state})
    except Exception as e:
        st.error(f"Meesho File Error: {e}")

# 2. Process Flipkart
if fk_file is not None:
    try:
        xl = pd.ExcelFile(fk_file)
        sheet_7b = [s for s in xl.sheet_names if "7(B)" in s or "7(B)(2)" in s]
        if sheet_7b:
            df_7b = pd.read_excel(fk_file, sheet_name=sheet_7b[0])
            for _, r in df_7b.iloc[1:].iterrows():
                gross = float(pd.to_numeric(r.iloc[1], errors='coerce') or 0)
                returns = float(pd.to_numeric(r.iloc[2], errors='coerce') or 0)
                rate = float(pd.to_numeric(r.iloc[4], errors='coerce') or 0)
                state = str(r.iloc[8]).strip() if len(r) > 8 else "Delhi"
                if state and (abs(gross) > 0.001 or abs(returns) > 0.001):
                    processed_rows.append({"Platform": "Flipkart", "Gross": gross, "Return": returns, "Rate": rate, "State": state})

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
                if abs(gross) > 0.001 or abs(returns) > 0.001:
                    processed_rows.append({"Platform": "Flipkart", "Gross": gross, "Return": returns, "Rate": rate, "State": state})
    except Exception as e:
        st.error(f"Flipkart File Error: {e}")

# 3. Process Amazon
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

# Calculations & Master Display
if len(processed_rows) > 0:
    master_df = pd.DataFrame(processed_rows)
    master_df['Net Taxable'] = master_df['Gross'] - master_df['Return']
    master_df = master_df[master_df['Net Taxable'].abs() > 0.001].copy()

    def enrich_row(row):
        code, st_proper = clean_state_info(row['State'])
        supply = "INTRA" if code == "07" or "DELHI" in st_proper.upper() else "INTER"
        ecomm_gstin = PLATFORM_GSTIN_MAP.get(row['Platform'], "")
        return pd.Series([code, st_proper, supply, ecomm_gstin], index=['StateCode', 'CleanState', 'SupplyType', 'EcommGSTIN'])

    master_df[['StateCode', 'CleanState', 'SupplyType', 'EcommGSTIN']] = master_df.apply(enrich_row, axis=1)

    master_df['TaxAmount'] = (master_df['Net Taxable'] * master_df['Rate'] / 100).round(2)
    master_df['IGST'] = master_df.apply(lambda r: r['TaxAmount'] if r['SupplyType'] == "INTER" else 0.0, axis=1)
    master_df['CGST'] = master_df.apply(lambda r: round(r['TaxAmount']/2, 2) if r['SupplyType'] == "INTRA" else 0.0, axis=1)
    master_df['SGST'] = master_df.apply(lambda r: round(r['TaxAmount']/2, 2) if r['SupplyType'] == "INTRA" else 0.0, axis=1)

    # TABLE 1: State-Wise Summary (Left Side)
    t1 = master_df.groupby(['SupplyType', 'StateCode', 'CleanState', 'Rate']).agg({
        'Net Taxable': 'sum',
        'IGST': 'sum',
        'CGST': 'sum',
        'SGST': 'sum'
    }).reset_index()
    t1['Place Of Supply (POS)'] = t1['StateCode'] + "-" + t1['CleanState']
    t1 = t1[['SupplyType', 'Place Of Supply (POS)', 'Rate', 'Net Taxable', 'IGST', 'CGST', 'SGST']].round(2)

    # Table 1 Grand Total
    t1_total = pd.DataFrame([{
        'SupplyType': 'Grand Total',
        'Place Of Supply (POS)': '',
        'Rate': '',
        'Net Taxable': round(t1['Net Taxable'].sum(), 2),
        'IGST': round(t1['IGST'].sum(), 2),
        'CGST': round(t1['CGST'].sum(), 2),
        'SGST': round(t1['SGST'].sum(), 2)
    }])
    t1_display = pd.concat([t1, t1_total], ignore_index=True)

    # TABLE 2: Platform Breakdown (Right Side)
    t2 = master_df.groupby(['Platform', 'SupplyType']).agg({
        'Net Taxable': 'sum',
        'IGST': 'sum',
        'CGST': 'sum',
        'SGST': 'sum'
    }).reset_index().round(2)

    # Table 2 Grand Total
    t2_total = pd.DataFrame([{
        'Platform': 'Grand Total',
        'SupplyType': '',
        'Net Taxable': round(t2['Net Taxable'].sum(), 2),
        'IGST': round(t2['IGST'].sum(), 2),
        'CGST': round(t2['CGST'].sum(), 2),
        'SGST': round(t2['SGST'].sum(), 2)
    }])
    t2_display = pd.concat([t2, t2_total], ignore_index=True)

    # TABLE 3: GSTR-1 B2CS Final Format
    b2cs_export = t1.copy()
    b2cs_export['Type'] = "OE"
    b2cs_export['Applicable % of Tax Rate'] = ""
    b2cs_export['Cess Amount'] = 0.0
    b2cs_export['E-Commerce GSTIN'] = PLATFORM_GSTIN_MAP.get("Meesho", "")
    b2cs_export = b2cs_export[['Type', 'Place Of Supply (POS)', 'Rate', 'Applicable % of Tax Rate', 'Net Taxable', 'Cess Amount', 'E-Commerce GSTIN']]
    b2cs_export.rename(columns={'Place Of Supply (POS)': 'Place Of Supply', 'Net Taxable': 'Taxable Value'}, inplace=True)

    st.divider()
    st.header("📊 GSTR-3B ADVANCE CONTROL REPORT (SIDE-BY-SIDE SUMMARY)")

    tab_col1, tab_col2 = st.columns([3, 2])
    with tab_col1:
        st.subheader("🔵 Table 1: State-wise POS Breakdown")
        st.dataframe(t1_display.style.format({
            'Net Taxable': '{:,.2f}',
            'IGST': '{:,.2f}',
            'CGST': '{:,.2f}',
            'SGST': '{:,.2f}'
        }), use_container_width=True)

    with tab_col2:
        st.subheader("🔴 Table 2: Platform Summary (INTER / INTRA)")
        st.dataframe(t2_display.style.format({
            'Net Taxable': '{:,.2f}',
            'IGST': '{:,.2f}',
            'CGST': '{:,.2f}',
            'SGST': '{:,.2f}'
        }), use_container_width=True)

    st.divider()
    st.header("📑 Table 7: GSTR-1 B2CS Final Table")
    st.dataframe(b2cs_export, use_container_width=True)

    # Downloads
    st.divider()
    st.subheader("📥 Export & Download Master Files")
    d1, d2, d3 = st.columns(3)

    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
        t1_display.to_excel(writer, index=False, sheet_name='State_Wise_Summary')
        t2_display.to_excel(writer, index=False, sheet_name='Platform_Summary')
        b2cs_export.to_excel(writer, index=False, sheet_name='GSTR1_B2CS_Final')
        master_df.to_excel(writer, index=False, sheet_name='Raw_Consolidated_Data')
    
    d1.download_button(
        "📊 Download Master Excel Report",
        data=excel_buf.getvalue(),
        file_name=f"GSTR_Master_Report_{return_period}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    csv_buf = io.StringIO()
    b2cs_export.to_csv(csv_buf, index=False)
    d2.download_button(
        "📄 Download GSTR-1 B2CS CSV",
        data=csv_buf.getvalue(),
        file_name="GSTR1_B2CS_Final_Clean.csv",
        mime="text/csv",
        use_container_width=True
    )

    json_b2cs_list = []
    for _, r in t1.iterrows():
        pos_c = r['Place Of Supply (POS)'].split('-')[0]
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
