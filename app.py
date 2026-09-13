import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="GSTR-1 JSON Generator", layout="wide")
st.title("GSTR-1 Data Processor & JSON Generator")

# 1. Place of Supply (POS) Mapping Dictionary
STATE_MAPPING = {
    # Andaman & Nicobar
    "andaman & nicobar islands": "35",
    "andaman and nicobar islands": "35",
    "andaman & nicobar": "35",
    "andaman": "35",
    "00-andaman & nicobar islands": "35",
    "00-andaman and nicobar islands": "35",
    
    # Puducherry / Pondicherry
    "pondicherry": "34",
    "puducherry": "34",
    "00-pondicherry": "34",
    "00-puducherry": "34",
    "34-puducherry": "34",
    "34-pondicherry": "34",
    
    # Standard States & UTs
    "jammu and kashmir": "01", "jammu & kashmir": "01",
    "himachal pradesh": "02",
    "punjab": "03",
    "chandigarh": "04",
    "uttarakhand": "05",
    "haryana": "06",
    "delhi": "07",
    "rajasthan": "08",
    "uttar pradesh": "09",
    "bihar": "10",
    "sikkim": "11",
    "arunachal pradesh": "12",
    "nagaland": "13",
    "manipur": "14",
    "mizoram": "15",
    "tripura": "16",
    "meghalaya": "17",
    "assam": "18",
    "west bengal": "19",
    "jharkhand": "20",
    "odisha": "21", "orissa": "21",
    "chhattisgarh": "22",
    "madhya pradesh": "23",
    "gujarat": "24",
    "dadra and nagar haveli and daman and diu": "26",
    "maharashtra": "27",
    "andhra pradesh (before division)": "28",
    "karnataka": "29",
    "goa": "30",
    "lakshadweep": "31",
    "kerala": "32",
    "tamil nadu": "33",
    "telangana": "36",
    "andhra pradesh": "37",
    "ladakh": "38",
    "other territory": "97"
}

def clean_pos_code(val):
    """राज्य के नाम या कोड से सही 2-डिजिट जीएसटी कोड निकालता है"""
    if pd.isna(val):
        return "00"
    s = str(val).strip().lower()
    
    # सीधी डिक्शनरी मैचिंग
    if s in STATE_MAPPING:
        return STATE_MAPPING[s]
    
    # अगर '00-Andaman...' या '07-Delhi' जैसे फॉर्मेट में हो
    if "-" in s:
        parts = s.split("-", 1)
        prefix_code = parts[0].strip()
        state_name = parts[1].strip().lower()
        
        # अगर प्रीफ़िक्स 00 है, तो नाम से मैच करें
        if prefix_code == "00" or prefix_code not in [f"{i:02d}" for i in range(1, 39)]:
            if state_name in STATE_MAPPING:
                return STATE_MAPPING[state_name]
        else:
            return prefix_code.zfill(2)
            
    # अगर केवल 2 अंकों का संख्यात्मक कोड हो
    digits = ''.join(filter(str.isdigit, s[:2]))
    if digits and digits != "00":
        return digits.zfill(2)
        
    return "00"

def process_b2cs_data(df, seller_state_code="07"):
    """B2CS डेटा को साफ़ और समूहीकृत (group) करता है"""
    df = df.copy()
    
    # कॉलम नामों को एकसमान करें
    df.columns = df.columns.str.strip()
    
    # POS साफ़ करें
    df['Clean_POS'] = df['Place Of Supply'].apply(clean_pos_code)
    
    # आवश्यक संख्यात्मक फ़ील्ड्स
    df['Rate'] = pd.to_numeric(df.get('Rate', 5.0), errors='coerce').fillna(5.0)
    df['Taxable Value'] = pd.to_numeric(df.get('Taxable Value', 0.0), errors='coerce').fillna(0.0)
    
    # एक ही राज्य और दर को समूहीकृत (merge/sum) करें
    grouped = df.groupby(['Clean_POS', 'Rate'], as_index=False)['Taxable Value'].sum()
    
    # पोर्टल एरर रोकने के लिए नेगेटिव वैल्यू हटाएं (या 0 करें)
    # जीएसटी पोर्टल B2CS में नेगेटिव वैल्यू रिजेक्ट करता है
    grouped = grouped[grouped['Taxable Value'] > 0].copy()
    
    b2cs_list = []
    for _, row in grouped.iterrows():
        pos = row['Clean_POS']
        rate = float(row['Rate'])
        txval = round(float(row['Taxable Value']), 2)
        
        # दिल्ली (होम स्टेट) = INTRA, बाकी सब = INTER
        if pos == seller_state_code:
            sply_ty = "INTRA"
            camt = round(txval * (rate / 2.0) / 100.0, 2)
            samt = camt
            entry = {
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
            entry = {
                "sply_ty": sply_ty,
                "pos": pos,
                "typ": "OE",
                "rt": rate,
                "txval": txval,
                "csamt": 0.0,
                "iamt": iamt
            }
        b2cs_list.append(entry)
        
    return b2cs_list

# UI इनपुट फ़ील्ड्स
col1, col2 = st.columns(2)
with col1:
    gstin = st.text_input("GSTIN", value="07AIRPA0056F1ZL")
with col2:
    fp = st.text_input("Return Period (MMYYYY)", value="082026")

uploaded_file = st.file_uploader("Upload Consolidated B2CS Excel/CSV File", type=["xlsx", "xls", "csv"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
        
    st.subheader("कच्चा डेटा (Raw Data Preview)")
    st.dataframe(df.head())
    
    seller_code = gstin[:2] if len(gstin) >= 2 else "07"
    b2cs_records = process_b2cs_data(df, seller_state_code=seller_code)
    
    final_json = {
        "gstin": gstin,
        "fp": fp,
        "version": "GST3.1.4",
        "hash": "hash",
        "b2cs": b2cs_records
    }
    
    st.subheader(f"सुधारा गया B2CS डेटा ({len(b2cs_records)} रिकॉर्ड्स)")
    st.dataframe(pd.DataFrame(b2cs_records))
    
    json_str = json.dumps(final_json, indent=4)
    
    st.download_button(
        label="Download Clean GSTR-1 JSON",
        data=json_str,
        file_name=f"GSTR1_{gstin}_{fp}.json",
        mime="application/json"
    )
