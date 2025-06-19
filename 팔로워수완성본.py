import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# ▶ 엑셀 파일 경로 (규리님이 만든 엑셀 파일 위치)
file_path = r"C:\Users\Gyuri\Desktop\1기링크.xlsx"

# ▶ 엑셀 파일 읽기
df = pd.read_excel(file_path)
urls = df.iloc[:, 0]  # A열: 스토어 URL 목록

# ▶ 크롬 드라이버 설정
options = Options()
options.add_argument("--headless")  # 창 없이 실행
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

# ▶ 결과 저장용 리스트
product_counts = []
follower_counts = []

# ▶ URL 하나씩 접속하여 상품수, 팔로워수 수집
for idx, url in enumerate(urls):
    try:
        # ✅ URL 보정 (http 누락 방지)
        url = str(url).strip()
        if not url.startswith("http"):
            url = "https://" + url

        driver.get(url)
        time.sleep(2.5)  # 로딩 대기

        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # 상품 수 추출
        product_span = soup.find('span', class_='num')
        product_count = product_span.text.strip() if product_span else "N/A"

        # 팔로워 수 추출
        follower_span = soup.find('span', class_='flw_num')
        follower_count = follower_span.find('em').text.strip() if follower_span else "N/A"

        print(f"[{idx+1}] ✅ {url} → 상품수: {product_count} / 팔로워: {follower_count}")

    except Exception as e:
        print(f"[{idx+1}] ❌ 오류 발생: {url} / {e}")
        product_count = "ERR"
        follower_count = "ERR"

    product_counts.append(product_count)
    follower_counts.append(follower_count)

driver.quit()

# ▶ 엑셀에 결과 저장
df['상품등록수'] = product_counts
df['팔로워수'] = follower_counts

# ▶ 결과 파일 저장 경로
output_path = r"C:\Users\Gyuri\Desktop\1기링크_결과.xlsx"
df.to_excel(output_path, index=False)

print(f"\n📁 수집 완료! 결과 저장됨 → {output_path}")
