import pandas as pd
import streamlit as st
from datetime import datetime
import time
import os
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Cài Google Chrome nếu chưa có
if not os.path.exists("/usr/bin/google-chrome"):
    subprocess.run([
        "bash", "-c",
        """
        wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
        apt update && apt install -y /tmp/chrome.deb
        """
    ])

st.set_page_config(page_title="URL & Anchor Validator", layout="wide")
st.title("🔍 Google Sheet Style - URL & Anchor Checker (Selenium Mode)")

st.markdown("""
Upload file Excel/CSV với định dạng:

- Cột A: Source URL (trang cần kiểm tra)
- Cột B: AnchorText1
- Cột C: Link đích 1
- Cột D: AnchorText2
- Cột E: Link đích 2
- ...

Tool sẽ:
- Mở trang bằng Selenium (giống trình duyệt thật)
- Duyệt DOM thật bằng Selenium
- Kiểm tra từng anchor text có tồn tại không
- Anchor đó có trỏ đúng hoặc chứa link đích không (linh hoạt cho redirect, tracking, rút gọn...)
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

            chrome_options = Options()
            chrome_options.binary_location = "/usr/bin/google-chrome"
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0")

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

            for i, row in df.iterrows():
                source_url = row[0]
                anchors_links = list(row[1:].dropna().values)
                pairs = [(anchors_links[i], anchors_links[i+1]) for i in range(0, len(anchors_links)-1, 2)]

                try:
                    driver.get(source_url)
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "a"))
                    )

                    a_tags = driver.find_elements(By.TAG_NAME, "a")
                    for anchor, target_url in pairs:
                        found_anchor = False
                        correct_link = False

                        clean_anchor = ' '.join(str(anchor).lower().split())
                        clean_target = str(target_url).strip().rstrip('/').lower()

                        for a in a_tags:
                            a_text = a.text
                            a_href = a.get_attribute("href")

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
                            "Status Code": 200,
                            "Reason": "OK",
                            "OK?": "Yes",
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
                time.sleep(0.5)

            driver.quit()
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
