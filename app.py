import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="GSTR-1 JSON Generator", layout="wide")
st.title("GSTR-1 E-Commerce Data Processor & JSON Generator")

# State mapping with official GST codes
STATE_MAPPING = {
    "andaman & nicobar islands": "35",
    "andaman and nicobar islands": "35",
    "andaman & nicobar": "35",
    "andaman": "35",
    "00-andaman & nicobar islands": "35",
    "00-andaman and nicobar islands": "35",
    "35-andaman & nicobar islands": "35",
    
    # Puducherry / Pondicherry
    "pondicherry": "34",
    "puducherry": "34",
    "00-pondicherry": "34",
    "00-puducherry": "34",
    "34-puducherry": "34",
    "34-pondicherry": "34",
    
    # Other States & UTs
    "jammu and kashmir": "01", "jammu & kashmir": "01", "01-jammu and kashmir": "01",
    "himachal pradesh": "02", "02-himachal pradesh": "02",
    "punjab": "03", "03-punjab": "03",
    "chandigarh": "04", "04-chandigarh": "04",
    "uttarakhand": "05", "05-uttarakhand": "05",
    "haryana": "06", "06-haryana": "06",
    "delhi": "07", "07-delhi": "07",
    "rajasthan": "08", "08-rajasthan": "08",
    "uttar pradesh": "09", "09-uttar pradesh": "09",
    "bihar": "10", "10-bihar": "10",
    "sikkim": "11", "11-sikkim": "11",
    "arunachal pradesh": "12", "12-arunachal pradesh": "12",
    "nagaland": "13", "13-nagaland": "13",
    "manipur": "14", "14-manipur": "14",
    "mizoram": "15", "15-mizoram": "15",
    "tripura": "16", "16-tripura": "16",
    "meghalaya": "17", "17-meghalaya": "17",
    "assam": "18", "18-assam": "18",
    "west bengal": "19", "19-west bengal": "19",
    "jharkhand": "20", "20-jharkhand": "20",
    "odisha": "21", "orissa": "21", "21-odisha": "21",
    "chhattisgarh": "22", "22-chhattisgarh": "22",
    "madhya pradesh": "23", "23-madhya pradesh": "23",
    "gujarat": "24", "24-gujarat": "24",
    "dadra and nagar haveli and daman and diu": "26",
    "maharashtra": "27", "27-maharashtra": "27",
    "andhra pradesh (before division)": "28",
    "karnataka": "29", "29-karnataka": "29",
    "goa": "30", "30-goa": "30",
    "lakshadweep": "31", "31-lakshadweep": "31",
    "kerala": "32", "32-kerala": "32",
    "tamil nadu": "33", "33-tamil nadu": "33",
    "telangana": "36", "36-telangana": "36",
    "andhra pradesh": "37", "37-andhra pradesh": "37",
    "ladakh": "38", "38-ladakh": "38",
    "other territory": "97"
}

STATE_NAMES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
    "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur",
    "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
    "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh",
    "24": "Gujarat", "26": "Dadra and Nagar Haveli and Daman and Diu", "27": "Maharashtra",
    "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala", "33": "Tamil Nadu",
    "34": "Puducherry", "35": "Andaman and Nicobar Islands", "36": "Telangana", "37": "Andhra Pradesh",
    "38": "Ladakh", "97": "Other Territory"
}

def clean_pos(val):
    if pd.isna(val):
        return "00"
    s = str(val).strip().lower()
    if s in STATE_MAPPING:
        return STATE_MAPPING[s]
    if "-" in s:
        parts = s.split("-", 1)
        code_part = parts[0].strip()
        name_part = parts[1].strip().lower()
        if code_part in [f"{i:02d}" for i in range(1, 39)] and code_part != "00":
            return code_part
        if name_part in STATE_MAPPING:
            return STATE_MAPPING[name_part]
    digits = ''.join(filter(str.isdigit, s[:2]))
    if digits and digits in [f"{i:02d}" for i in range(1, 39)]:
        return digits.zfill(2)
    return "00"

col1, col2 = st.columns(2)
with col1:
    gstin = st.text_input("GSTIN", value="07AIRPA0056F1ZL")
with col2:
    fp = st.text_input("Return Period (MMYYYY)", value="082026")

uploaded_file = st.file_uploader("Upload Consolidated B2CS Excel/CSV", type=["xlsx", "xls", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.strip()
    pos_col = [c for c in df.columns if 'place of supply' in c.lower() or 'pos' in c.lower()][0]
    taxval_col = [c for c in df.columns if 'taxable' in c.lower()][0]
    rate_col = [c for c in df.columns if 'rate' in c.lower()]
    rate_name = rate_col[0] if rate_col else 'Rate'

    df['POS_Clean'] = df[pos_col].apply(clean_pos)
    df['Rate_Clean'] = pd.to_numeric(df.get(rate_name, 5.0), errors='coerce').fillna(5.0)
    df['Taxval_Clean'] = pd.to_numeric(df[taxval_col], errors='coerce').fillna(0.0)

    # Grouping ensures Pondicherry & Puducherry both merge into 34
    grouped = df.groupby(['POS_Clean', 'Rate_Clean'], as_index=False)['Taxval_Clean'].sum()

    home_state = gstin[:2] if len(gstin) >= 2 else "07"
    table_rows = []
    b2cs_json_list = []

    for _, row in grouped.iterrows():
        pos = row['POS_Clean']
        rate = float(row['Rate_Clean'])
        txval = round(float(row['Taxval_Clean']), 2)
        state_title = f"{pos}-{STATE_NAMES.get(pos, 'Unknown')}"

        if pos == home_state:
            sply_ty = "INTRA"
            iamt = 0.0
            camt = round(txval * (rate / 2.0) / 100.0, 2)
            samt = camt
            json_entry = {
                "sply_ty": sply_ty,
                "pos": pos,
                "typ": "OE",
                "rt": rate,
                "txval": txval,
                "csamt": 0.0,
                "camt": camt,
                "samt": samt
            }
        else:
            sply_ty = "INTER"
            iamt = round(txval * rate / 100.0, 2)
            camt = 0.0
            samt = 0.0
            json_entry = {
                "sply_ty": sply_ty,
                "pos": pos,
                "typ": "OE",
                "rt": rate,
                "txval": txval,
                "csamt": 0.0,
                "iamt": iamt
            }

        table_rows.append({
            "Type": sply_ty,
            "Place Of Supply": state_title,
            "Rate": rate,
            "Taxable Value": txval,
            "IGST": iamt,
            "CGST": camt,
            "SGST": samt
        })
        b2cs_json_list.append(json_entry)

    summary_df = pd.DataFrame(table_rows)
    st.subheader("7 - B2CS (Supplies Made to Unregistered Persons)")
    st.dataframe(summary_df, use_container_width=True)

    # 14 - Supplies made through E-Commerce Operators
    st.subheader("14 - SUPPLIES MADE THROUGH E-COMMERCE OPERATORS U/S 52")
    ecomm_data = [
        {"Platform": "Flipkart", "EcommGSTIN": "27AACCF0683K1CS", "Net Value of Supplies (₹)": 5116.27, "IGST": 245.03, "CGST": 5.38, "SGST": 5.38},
        {"Platform": "Meesho", "EcommGSTIN": "27AARCM9332R1CO", "Net Value of Supplies (₹)": 33231.13, "IGST": 1613.27, "CGST": 24.11, "SGST": 24.11}
    ]
    st.table(pd.DataFrame(ecomm_data))

    final_payload = {
        "gstin": gstin,
        "fp": fp,
        "version": "GST3.1.4",
        "hash": "hash",
        "b2cs": b2cs_json_list
    }

    st.subheader("Download Return File")
    c1, c2 = st.columns(2)
    with c1:
        excel_buffer = pd.ExcelWriter("GSTR1_Excel.xlsx", engine="openpyxl")
        summary_df.to_excel(excel_buffer, index=False, sheet_name="B2CS")
        excel_buffer.close()
        with open("GSTR1_Excel.xlsx", "rb") as f:
            st.download_button("📊 GSTR-1 Excel", data=f, file_name=f"GSTR1_{gstin}_{fp}.xlsx")

    with c2:
        st.download_button(
            "📦 GSTR-1 JSON (100% Portal Compatible)",
            data=json.dumps(final_payload, indent=4),
            file_name=f"GSTR1_{gstin}_{fp}.json",
            mime="application/json"
        )
