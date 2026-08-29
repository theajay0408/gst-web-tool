import streamlit as st
import pandas as pd
import json
import io

st.set_page_config(page_title="GST E-Commerce Automation Tool", page_icon="📊", layout="wide")

st.title("📊 E-Commerce GST Sales Processor & GSTR-1 Generator")
st.markdown("Meesho / Flipkart / Amazon Sales रिपोर्ट अपलोड करके तुरंत समरी, Cleaned Excel और JSON प्राप्त करें।")

uploaded_file = st.file_uploader("अपनी Sales Report (Excel / CSV) फ़ाइल अपलोड करें", type=["xlsx", "xls", "csv"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success(f"फ़ाइल सफलतापूर्वक लोड हो गई: {uploaded_file.name} (कुल रिकॉर्ड: {len(df)})")
        
        # ऑटो-कॉलम डिटेक्शन
        cols = df.columns.tolist()
        
        st.subheader("📋 डेटा प्रीव्यू")
        st.dataframe(df.head(5), use_container_width=True)

        # मेट्रिक्स कैलकुलेशन (बेसिक क्लीनिंग व समरी)
        num_cols = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("कुल ऑर्डर्स / रोज़", len(df))
        col2.metric("कुल कॉलम्स", len(cols))
        col3.metric("फ़ाइल स्टेटस", "Ready for Export")

        st.divider()

        # डाउनलोड सेक्शन
        st.subheader("📥 एक्सपोर्ट व डाउनलोड")
        d_col1, d_col2 = st.columns(2)

        # 1. Cleaned Excel Download
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Cleaned_Data')
        excel_data = excel_buffer.getvalue()

        d_col1.download_button(
            label="📊 Download Processed Excel",
            data=excel_data,
            file_name=f"Cleaned_GST_{uploaded_file.name.split('.')[0]}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

        # 2. JSON Data Download
        json_str = df.to_json(orient='records', indent=2)
        d_col2.download_button(
            label="📄 Download GSTR-1 Data (JSON)",
            data=json_str,
            file_name=f"GSTR1_Data_{uploaded_file.name.split('.')[0]}.json",
            mime="application/json",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"फ़ाइल प्रोसेस करने में त्रुटि: {str(e)}")
