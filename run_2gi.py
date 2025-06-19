# 필요한 라이브러리들을 불러옵니다.
import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import datetime

# --- ⚙️ 구글 시트 연동 설정 (최종 확정) ---
SERVICE_ACCOUNT_FILE = r"C:\Users\Gyuri\Desktop\my_key.json"
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/15so_KG3-0aR8QAv02-P6AyNFSzy-NLl20zfUfujGQa4/edit?usp=sharing"
URL_COLUMN = 7

# ---  자동화 실행 코드 (최종 확정) ---

# ▶ 구글 시트 인증 및 클라이언트 선언
try:
    print("▶ 1단계: 인증 파일 읽기 시도...")
    scopes = [ "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive" ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    print("✅ 1단계: 구글 인증 및 클라이언트 선언 성공!")
    print(f"▶ 2단계: URL로 시트 열기 시도...")
    spreadsheet = client.open_by_url(GOOGLE_SHEET_URL)
    print("✅ 2단계: URL로 시트 파일 열기 성공!")
    print("▶ 3단계: 첫 번째 워크시트 접근 시도...")
    sheet = spreadsheet.sheet1
    print(f"✅ 3단계: 첫 번째 시트('{sheet.title}') 접근 성공!")
    print(f"\n✅ 시트 연결 최종 성공!")
except Exception as e:
    print(f"\n❌ 구글 시트 연결 실패: {e}")
    exit()

# ▶ 시트에서 URL 목록 가져오기 (4행부터)
urls = sheet.col_values(URL_COLUMN)[3:]
print(f"✅ 총 {len(urls)}개의 URL을 가져와서 스크래핑을 시작합니다.")

# ▶ 크롬 드라이버 설정
options = Options()
options.add_argument("--headless")
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

# ▶ 결과 저장용 리스트
product_counts = []
follower_counts = []

# ▶ URL 하나씩 접속하여 상품수, 팔로워수 수집
for idx, url in enumerate(urls):
    if not url or url.strip() == "":
        print(f"[{idx+1}/{len(urls)}] ⏩ 빈 셀이므로 건너뜁니다.")
        product_counts.append("")
        follower_counts.append("")
        continue
    try:
        url = str(url).strip()
        if not url.startswith("http"): url = "https://" + url
        driver.get(url)
        time.sleep(2.5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_span = soup.find('span', class_='num')
        product_count = product_span.text.strip().replace(',', '') if product_span else "N/A"
        follower_span = soup.find('span', class_='flw_num')
        follower_count = follower_span.find('em').text.strip().replace(',', '') if follower_span else "N/A"
        print(f"[{idx+1}/{len(urls)}] ✅ {url} → 상품수: {product_count} / 팔로워: {follower_count}")
        product_counts.append(product_count)
        follower_counts.append(follower_count)
    except Exception as e:
        print(f"[{idx+1}/{len(urls)}] ❌ 오류 발생: {url} / {e}")
        product_counts.append("ERR")
        follower_counts.append("ERR")
driver.quit()

# ▶ 구글 시트에 결과 업데이트
try:
    print("\n🔄 구글 시트에 데이터를 업데이트하는 중입니다...")
    header_row = sheet.row_values(3) 
    last_col = len(header_row)

    if sheet.col_count <= last_col + 1:
        print(f"▶ 현재 {sheet.col_count}개 열이 있습니다. 오른쪽에 2개 열을 추가합니다.")
        sheet.add_cols(2)

    today_str = datetime.datetime.now().strftime('%y-%m-%d')
    sheet.update_cell(3, last_col + 1, f"{today_str} 상품수")
    sheet.update_cell(3, last_col + 2, f"{today_str} 팔로워수")

    data_start_row = 4
    data_end_row = data_start_row + len(product_counts) - 1

    # 상품수 업데이트
    product_range_to_update = sheet.range(data_start_row, last_col + 1, data_end_row, last_col + 1)
    for i, cell in enumerate(product_range_to_update):
        cell.value = product_counts[i]
    sheet.update_cells(product_range_to_update)

    # 팔로워수 업데이트 (버그 수정된 부분)
    follower_range_to_update = sheet.range(data_start_row, last_col + 2, data_end_row, last_col + 2)
    # ▼▼▼ 이 부분을 follower_range_to_update 로 올바르게 수정했습니다 ▼▼▼
    for i, cell in enumerate(follower_range_to_update):
        cell.value = follower_counts[i]
    sheet.update_cells(follower_range_to_update)
    
    print(f"\n🎉 수집 및 업데이트 완료! 구글 시트를 확인해보세요.")
except Exception as e:
    print(f"\n❌ 구글 시트 업데이트 중 오류 발생: {e}")