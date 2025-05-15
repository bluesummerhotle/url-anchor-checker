import pandas as pd
import streamlit as st
from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="URL & Anchor Validator", layout="wide")
st.title("🔍 Google Sheet Style - URL & Anchor Checker (No Selenium)")

st.markdown("""
Upload file Excel/CSV với định dạng:

- Cột A: Source URL (trang cần kiểm tra)
- Cột B: AnchorText1
- Cột C: Link đích 1
- Cột D: AnchorText2
- Cột E: Link đích 2
- ...

Tool sẽ:
- Tải HTML bằng requests
- Parse DOM bằng BeautifulSoup
- Kiểm tra từng anchor text có tồn tại không
- Anchor đó có trỏ đúng hoặc chứa link đích không
""")

uploaded_file = st.file_uploader("📎 Tải lên file CSV hoặc Excel", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    if df.shape[1] < 3:
        st.error("❌ File phải có ít nhất 1 URL và 1 cặp anchor/link")
    else:
        st.success(f"✅ Đã tải {len(df)} dòng. Bấm nút để bắt đầu kiểm tra.")

        if st.button("🚀 Bắt đầu kiểm tra"):
            results = []
            progress = st.progress(0)
            status_placeholder = st.empty()

            for i, row in df.iterrows():
                source_url = row[0]
                anchors_links = list(row[1:].dropna().values)
                pairs = [(anchors_links[i], anchors_links[i+1]) for i in range(0, len(anchors_links)-1, 2)]

                try:
                    response = requests.get(source_url, timeout=10)
                    status_code = response.status_code
                    reason = response.reason
                    html = response.text
                    soup = BeautifulSoup(html, 'html.parser')
                    a_tags = soup.find_all('a')

                    for anchor, target_url in pairs:
                        found_anchor = False
                        correct_link = False

                        clean_anchor = ' '.join(str(anchor).lower().split())
                        clean_target = str(target_url).strip().rstrip('/').lower()

                        for a in a_tags:
                            a_text = a.get_text()
                            a_href = a.get("href")

                            clean_text = ' '.join(str(a_text).lower().split())
                            href = str(a_href).strip().rstrip('/') if a_href else ''

                            if clean_text == clean_anchor:
                                found_anchor = True
                                if clean_target in href.lower():
                                    correct_link = True
                                break

                        results.append({
                            "Anchor": anchor,
                            "Target URL": target_url,
                            "Source URL": source_url,
                            "Status Code": status_code,
                            "Reason": reason,
                            "OK?": "Yes" if status_code == 200 else "No",
                            "Anchor Exists?": 'Yes' if found_anchor else 'No',
                            "Anchor Links Correctly?": 'Yes' if correct_link else 'No'
                        })
                except Exception as e:
                    for anchor, target_url in pairs:
                        results.append({
                            "Anchor": anchor,
                            "Target URL": target_url,
                            "Source URL": source_url,
                            "Status Code": 'Error',
                            "Reason": str(e),
                            "OK?": 'No',
                            "Anchor Exists?": 'Error',
                            "Anchor Links Correctly?": 'Error'
                        })

                progress.progress((i + 1) / len(df))
                status_placeholder.text(f"Đang kiểm tra: {source_url}")
                time.sleep(0.25)

            progress.empty()
            status_placeholder.empty()
            output_df = pd.DataFrame(results)
            st.dataframe(output_df, use_container_width=True)

            csv = output_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="⬇️ Tải kết quả CSV",
                data=csv,
                file_name=f'result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mime='text/csv',
            )
else:
    st.info("📥 Tải lên file chứa Source URL + Anchor + Link đích")
