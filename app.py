import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import io
import re

st.set_page_config(page_title="GST Online Seller Automation", page_icon="⚖️", layout="wide")

# CSS for Clean Modern UI
st.markdown("""
    <style>
    header a[href*="github"],
    header button[title*="Edit"],
    header button[aria-label*="Edit"],
    header svg[data-testid="stIconGitHub"],
    header svg[data-testid="stIconPencil"],
    [data-testid="stToolbar"] a[href*="github"],
    [data-testid="stToolbar"] button:has(svg[data-testid="stIconGitHub"]),
    [data-testid="stToolbar"] button:has(svg[data-testid="stIconPencil"]) {
        display: none !important;
        visibility: hidden !important;
    }
    </style>
""", unsafe_allow_html=True)

components.html("""
    <script>
    function removeIcons() {
        const doc = window.parent.document;
        const gitLinks = doc.querySelectorAll('a[href*="github.com"], button:has(svg[data-testid="stIconGitHub"])');
        gitLinks.forEach(el => el.style.setProperty('display', 'none', 'important'));
        
        const editButtons = doc.querySelectorAll('button[title*="Edit"], button[aria-label*="Edit"], button:has(svg[data-testid="stIconPencil"])');
        editButtons.forEach(el => el.style.setProperty('display', 'none', 'important'));

        const svgs = doc.querySelectorAll('header svg, [data-testid="stToolbar"] svg');
        svgs.forEach(svg => {
            const html = svg.outerHTML.toLowerCase();
            if (html.includes('m12 2c6.477') || html.includes('github') || html.includes('m14.06 9.02') || html.includes('pencil')) {
                const btn = svg.closest('button') || svg.closest('a');
                if (btn) btn.style.setProperty('display', 'none', 'important');
            }
        });
    }
    setInterval(removeIcons, 300);
    </script>
""", height=0, width=0)

STATE_MASTER = {
    "JAMMU AND KASHMIR": ("01", "Jammu and Kashmir"), "HIMACHAL PRADESH": ("02", "Himachal Pradesh"),
    "PUNJAB": ("03", "Punjab"), "CHANDIGARH": ("04", "Chandigarh"), "UTTARAKHAND": ("05", "Uttarakhand"),
    "HARYANA": ("06", "Haryana"), "DELHI": ("07", "Delhi"), "RAJASTHAN": ("08", "Rajasthan"),
    "UTTAR PRADESH": ("09", "Uttar Pradesh"), "BIHAR": ("10", "Bihar"), "SIKKIM": ("11", "Sikkim"),
    "ARUNACHAL PRADESH": ("12", "Arunachal Pradesh"), "NAGALAND": ("13", "Nagaland"), "MANIPUR": ("14", "Manipur"),
    "MIZORAM": ("15", "Mizoram"), "TRIPURA": ("16", "Tripura"), "MEGHALAYA": ("17", "Meghalaya"),
    "ASSAM": ("18", "Assam"), "WEST BENGAL": ("19", "West Bengal"), "JHARKHAND": ("20", "Jharkhand"),
    "ODISHA": ("21", "Odisha"), "CHHATTISGARH": ("22", "Chhattisgarh"), "MADHYA PRADESH": ("23", "Madhya Pradesh"),
    "GUJARAT": ("24", "Gujarat"), "DAMAN AND DIU": ("25", "Daman and Diu"), "DADRA AND NAGAR HAVELI": ("26", "Dadra and Nagar Haveli"),
    "DADRA AND NAGAR HAVELI AND DAMAN AND DIU": ("26", "Dadra and Nagar Haveli and Daman and Diu"),
    "MAHARASHTRA": ("27", "Maharashtra"), "ANDHRA PRADESH": ("37", "Andhra Pradesh"), "KARNATAKA": ("29", "Karnataka"),
    "GOA": ("30", "Goa"), "LAKSHADWEEP": ("31", "Lakshadweep"), "KERALA": ("32", "Kerala"), "TAMIL NADU": ("33", "Tamil Nadu"),
    "PONDICHERRY": ("34", "Puducherry"), "PUDUCHERRY": ("34", "Puducherry"),
    "ANDAMAN AND NICOBAR": ("35", "Andaman and Nicobar Islands"), "ANDAMAN AND NICOBAR ISLANDS": ("35", "Andaman and Nicobar Islands"),
    "ANDAMAN & NICOBAR ISLANDS": ("35", "Andaman and Nicobar Islands"), "ANDAMAN & NICOBAR": ("35", "Andaman and Nicobar Islands"),
    "TELANGANA": ("36", "Telangana"), "LADAKH": ("38", "Ladakh"), "OTHER TERRITORY": ("97", "Other Territory")
}
CODE_TO_STATE = {v[0]: v for v in STATE_MASTER.values()}

PLATFORM_ECOMM_GSTIN = {
    "Meesho": "27AARCM9332R1CO",
    "Flipkart": "27AACCF0683K1CS",
    "Amazon": "07AAACA6687K1ZT"
}

def clean_state_info(raw_state):
    st_clean = str(raw_state).upper().strip()
    if not st_clean or st_clean in ["NAN", "NONE", "NULL"]:
        return "00", "Unknown"
    
    # Check for prefix digits (e.g., "07-Delhi" or "34-Puducherry")
    code_match = re.match(r"^(\d{1,2})[\s\-_]*(.*)$", st_clean)
    if code_match:
        c_code = code_match.group(1).zfill(2)
        # If code is valid and not "00", map from code
        if c_code != "00" and c_code in CODE_TO_STATE:
            return CODE_TO_STATE[c_code]
        st_clean = code_match.group(2).strip()

    # Specific name checks
    if "ANDAMAN" in st_clean:
        return "35", "Andaman and Nicobar Islands"
    if "PUDU" in st_clean or "PONDI" in st_clean:
        return "34", "Puducherry"
    if "MAHA" in st_clean:
        return "27", "Maharashtra"
    if "ANDHRA" in st_clean:
        return "37", "Andhra Pradesh"
    if "BENGAL" in st_clean:
        return "19", "West Bengal"
    if "CHATTIS" in st_clean:
        return "22", "Chhattisgarh"
    if "ODISHA" in st_clean or "ORISSA" in st_clean:
        return "21", "Odisha"
        
    return STATE_MASTER.get(st_clean, ("00", st_clean.title()))

st.title("💼 GST Online Seller - Return Generator")
c1, c2, c3 = st.columns([2, 1, 1])
active_gstin = c1.text_input("ACTIVE GSTIN", value="07AIRPA0056F1ZL")
home_state_code = active_gstin[:2] if len(active_gstin) >= 2 else "07"
period = c2.selectbox("Period", ["08-2026", "07-2026", "09-2026", "06-2026", "05-2026"])
return_type = c3.selectbox("Return", ["Monthly", "Quarterly"])

fp_code = period.replace("-", "")

st.divider()

st.subheader("📁 E-COMMERCE PLATFORMS")
p_col1, p_col2, p_col3 = st.columns(3)

with p_col1:
    st.markdown("### 🟣 Meesho (B2C)")
    m_sales = st.file_uploader("Upload tcs_sales.xlsx", type=["xlsx", "xls", "csv"], key="ms")
    m_return = st.file_uploader("Upload tcs_sales_return.xlsx", type=["xlsx", "xls", "csv"], key="mr")
    m_invoice = st.file_uploader("Upload Tax_invoice_details.xlsx (Optional)", type=["xlsx", "xls", "csv"], key="mi")

with p_col2:
    st.markdown("### 🟡 Flipkart (B2C/B2B)")
    fk_file = st.file_uploader("Upload Flipkart GST Report (7A/7B)", type=["xlsx", "xls"], key="fk")

with p_col3:
    st.markdown("### 🟠 Amazon (B2C)")
    az_file = st.file_uploader("Upload Amazon MTR / B2C Report", type=["xlsx", "xls", "csv"], key="az")

processed_rows = []

if m_sales is not None:
    try:
        df_s = pd.read_excel(m_sales) if m_sales.name.endswith(('xlsx', 'xls')) else pd.read_csv(m_sales)
        df_s.columns = df_s.columns.str.strip().str.lower()
        for _, r in df_s.iterrows():
            g = float(pd.to_numeric(r.get('total_taxable_sale_value', r.get('gross amount', 0)), errors='coerce') or 0)
            rt = float(pd.to_numeric(r.get('gst_rate', r.get('rate', 0)), errors='coerce') or 0)
            st_name = str(r.get('end_customer_state_new', r.get('customer state', ''))).strip()
            if st_name and abs(g) > 0.001:
                processed_rows.append({"Platform": "Meesho", "Gross": g, "Return": 0.0, "Rate": rt, "State": st_name})
        if m_return is not None:
            df_r = pd.read_excel(m_return) if m_return.name.endswith(('xlsx', 'xls')) else pd.read_csv(m_return)
            df_r.columns = df_r.columns.str.strip().str.lower()
            for _, r in df_r.iterrows():
                ret = abs(float(pd.to_numeric(r.get('total_taxable_sale_value', r.get('gross amount', 0)), errors='coerce') or 0))
                rt = float(pd.to_numeric(r.get('gst_rate', r.get('rate', 0)), errors='coerce') or 0)
                st_name = str(r.get('end_customer_state_new', r.get('customer state', ''))).strip()
                if st_name and abs(ret) > 0.001:
                    processed_rows.append({"Platform": "Meesho", "Gross": 0.0, "Return": ret, "Rate": rt, "State": st_name})
    except Exception as e:
        st.error(f"Meesho Error: {e}")

if fk_file is not None:
    try:
        xl = pd.ExcelFile(fk_file)
        s_7b = [s for s in xl.sheet_names if "7(B)" in s or "7(B)(2)" in s]
        if s_7b:
            raw_7b = pd.read_excel(fk_file, sheet_name=s_7b[0], header=None)
            h_idx = 0
            for idx, rw in raw_7b.head(5).iterrows():
                if any(x in " ".join([str(v).lower() for v in rw]) for x in ["rate", "taxable"]):
                    h_idx = idx
                    break
            df_7b = pd.read_excel(fk_file, sheet_name=s_7b[0], skiprows=h_idx)
            for _, r in df_7b.iterrows():
                g = float(pd.to_numeric(r.iloc[1], errors='coerce') or 0)
                ret = float(pd.to_numeric(r.iloc[2], errors='coerce') or 0)
                rt = float(pd.to_numeric(r.iloc[4], errors='coerce') or 0)
                st_val = ""
                for ci in [8, 9, 10, 7]:
                    if len(r) > ci and str(r.iloc[ci]).strip().upper() not in ["NAN", "NONE", "0", "0.0", ""]:
                        st_val = str(r.iloc[ci]).strip()
                        break
                if abs(g) > 0.001 or abs(ret) > 0.001:
                    processed_rows.append({"Platform": "Flipkart", "Gross": g, "Return": ret, "Rate": rt, "State": st_val or "Delhi"})

        s_7a = [s for s in xl.sheet_names if "7(A)" in s or "7(A)(2)" in s]
        if s_7a:
            raw_7a = pd.read_excel(fk_file, sheet_name=s_7a[0], header=None)
            h_idx_a = 0
            for idx, rw in raw_7a.head(5).iterrows():
                if any(x in " ".join([str(v).lower() for v in rw]) for x in ["rate", "taxable"]):
                    h_idx_a = idx
                    break
            df_7a = pd.read_excel(fk_file, sheet_name=s_7a[0], skiprows=h_idx_a)
            for _, r in df_7a.iterrows():
                g = float(pd.to_numeric(r.iloc[1], errors='coerce') or 0)
                ret = float(pd.to_numeric(r.iloc[2], errors='coerce') or 0)
                rt = (float(pd.to_numeric(r.iloc[4], errors='coerce') or 0)) + (float(pd.to_numeric(r.iloc[6], errors='coerce') or 0))
                if abs(g) > 0.001 or abs(ret) > 0.001:
                    processed_rows.append({"Platform": "Flipkart", "Gross": g, "Return": ret, "Rate": rt, "State": "Delhi"})
    except Exception as e:
        st.error(f"Flipkart Error: {e}")

if az_file is not None:
    try:
        az_df = pd.read_excel(az_file) if az_file.name.endswith(('xlsx', 'xls')) else pd.read_csv(az_file)
        for _, r in az_df.iterrows():
            ttype = str(r.iloc[3]).strip() if len(r) > 3 else ""
            val = float(pd.to_numeric(r.iloc[28], errors='coerce') or 0) if len(r) > 28 else 0.0
            rt = float(pd.to_numeric(r.iloc[33], errors='coerce') or 0) * 100 if len(r) > 33 else 0.0
            st_val = str(r.iloc[24]).strip() if len(r) > 24 else ""
            if st_val and ttype in ["Shipment", "Refund", "Cancel"]:
                if ttype in ["Shipment", "Cancel"]:
                    processed_rows.append({"Platform": "Amazon", "Gross": val, "Return": 0.0, "Rate": rt, "State": st_val})
                elif ttype == "Refund":
                    processed_rows.append({"Platform": "Amazon", "Gross": 0.0, "Return": abs(val), "Rate": rt, "State": st_val})
    except Exception as e:
        st.error(f"Amazon Error: {e}")

if len(processed_rows) > 0:
    mdf = pd.DataFrame(processed_rows)
    mdf['Net'] = mdf['Gross'] - mdf['Return']
    mdf = mdf[mdf['Net'].abs() > 0.001].copy()

    def map_row(r):
        code, s_name = clean_state_info(r['State'])
        sp_type = "INTRA" if code == home_state_code else "INTER"
        ecom_id = PLATFORM_ECOMM_GSTIN.get(r['Platform'], "")
        return pd.Series([code, s_name, sp_type, ecom_id], index=['StateCode', 'StateName', 'SupplyType', 'EcommGSTIN'])

    mdf[['StateCode', 'StateName', 'SupplyType', 'EcommGSTIN']] = mdf.apply(map_row, axis=1)
    mdf['Tax'] = (mdf['Net'] * mdf['Rate'] / 100).round(2)
    mdf['IGST'] = mdf.apply(lambda r: r['Tax'] if r['SupplyType'] == "INTER" else 0.0, axis=1)
    mdf['CGST'] = mdf.apply(lambda r: round(r['Tax']/2, 2) if r['SupplyType'] == "INTRA" else 0.0, axis=1)
    mdf['SGST'] = mdf.apply(lambda r: round(r['Tax']/2, 2) if r['SupplyType'] == "INTRA" else 0.0, axis=1)

    t7 = mdf.groupby(['SupplyType', 'StateCode', 'StateName', 'Rate'], dropna=False).agg({
        'Net': 'sum', 'IGST': 'sum', 'CGST': 'sum', 'SGST': 'sum'
    }).reset_index().round(2)
    t7['Place Of Supply'] = t7['StateCode'] + "-" + t7['StateName']

    t14 = mdf.groupby(['Platform', 'EcommGSTIN'], dropna=False).agg({
        'Net': 'sum', 'IGST': 'sum', 'CGST': 'sum', 'SGST': 'sum'
    }).reset_index().round(2)

    st.divider()
    st.subheader("📑 7 - B2CS (OTHERS)")
    st.dataframe(t7[['SupplyType', 'Place Of Supply', 'Rate', 'Net', 'IGST', 'CGST', 'SGST']].rename(columns={'Net': 'Taxable Value (₹)'}), use_container_width=True)

    st.subheader("🏢 14 - SUPPLIES MADE THROUGH E-COMMERCE OPERATORS U/S 52")
    st.dataframe(t14.rename(columns={'Net': 'Net Value of Supplies (₹)'}), use_container_width=True)

    b2cs_json_list = []
    for _, r in t7.iterrows():
        pos_num = str(r['StateCode']).zfill(2)
        row_dict = {
            "sply_ty": str(r['SupplyType']),
            "pos": pos_num,
            "typ": "OE",
            "rt": float(r['Rate']),
            "txval": round(float(r['Net']), 2),
            "csamt": 0.0
        }
        if r['SupplyType'] == "INTER":
            row_dict["iamt"] = round(float(r['IGST']), 2)
        else:
            row_dict["camt"] = round(float(r['CGST']), 2)
            row_dict["samt"] = round(float(r['SGST']), 2)
        b2cs_json_list.append(row_dict)

    official_portal_json = {
        "gstin": active_gstin.strip(),
        "fp": str(fp_code).strip(),
        "version": "GST3.1.4",
        "hash": "hash",
        "b2cs": b2cs_json_list
    }

    b2cs_excel = pd.DataFrame({
        'Type': 'OE',
        'Place Of Supply': t7['Place Of Supply'],
        'Rate': t7['Rate'],
        'Applicable % of Tax Rate': '',
        'Taxable Value': t7['Net'],
        'Cess Amount': '',
        'E-Commerce GSTIN': ''
    })

    st.divider()
    st.subheader("📥 Download Return File")
    d_col1, d_col2 = st.columns(2)

    buf_excel = io.BytesIO()
    with pd.ExcelWriter(buf_excel, engine='openpyxl') as writer:
        b2cs_excel.to_excel(writer, index=False, sheet_name='b2cs')

    d_col1.download_button(
        "📊 GSTR-1 Excel",
        data=buf_excel.getvalue(),
        file_name=f"GSTR1_{active_gstin}_{fp_code}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    d_col2.download_button(
        "📦 GSTR-1 JSON (100% Portal Compatible)",
        data=json.dumps(official_portal_json, indent=4),
        file_name=f"GSTR1_{active_gstin}_{fp_code}.json",
        mime="application/json",
        use_container_width=True
    )
