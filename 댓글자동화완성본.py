# 네이버 블로그 자동 댓글 작성기 (중복 방지 포함 최적화 버전)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pyperclip
import time
import random
from google import generativeai as genai

# ✅ 네이버 로그인 함수
def naver_login(driver, id, pw):
    driver.get("https://nid.naver.com/nidlogin.login")
    time.sleep(1)
    pyperclip.copy(id)
    driver.find_element(By.CSS_SELECTOR, "#id").send_keys(Keys.CONTROL, "v")
    time.sleep(1)
    pyperclip.copy(pw)
    driver.find_element(By.CSS_SELECTOR, "#pw").send_keys(Keys.CONTROL, "v")
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, "#log\\.login").click()
    time.sleep(2)
    try:
        driver.find_element(By.CSS_SELECTOR, "#new\\.dontsave").click()
    except:
        pass

# ✅ 이웃 블로그 URL 수집 함수
def get_urls(driver):
    driver.get("https://m.blog.naver.com/FeedList.naver")
    time.sleep(3)
    elements = driver.find_elements(By.CSS_SELECTOR, "div[class^='text_area__'] > a[class^='link__']")
    urls = [el.get_attribute("href") for el in elements]
    return urls

# ✅ Gemini 설정 (API 키 필요)
genai.configure(api_key="AIzaSyDaT2AcRn6NUaH-hDODh49sGmZoWY2RYL0")
model = genai.GenerativeModel("gemini-2.0-flash")

# ✅ 실행 흐름 시작
options = Options()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

MY_NICKNAME = "프랑"  # 내 네이버 닉네임

try:
    naver_login(driver, "vscria", "!fldifldigkwk1")
    urls = get_urls(driver)
    count = 0

    for url in urls:
        if count >= 35:
            print("⏹️ 오늘 댓글 한도 도달. 종료합니다.")
            break

        if not driver.session_id:
            print("❌ 드라이버 세션 종료됨. 루프 중단")
            break

        try:
            driver.get(url)
            time.sleep(random.uniform(2.5, 4.5))

            try:
                title = driver.find_element(By.CSS_SELECTOR, ".se-title-text").text
            except:
                print(f"{url} - 제목 없음")
                continue

            try:
                content = driver.find_element(By.CSS_SELECTOR, ".se-main-container").text
            except:
                print(f"{url} - 내용 없음")
                continue

            try:
                reply_btn = driver.find_element(By.CSS_SELECTOR, "a.btn_reply")
                driver.execute_script("arguments[0].scrollIntoView(true);", reply_btn)
                reply_btn.click()
                time.sleep(2)
            except:
                print(f"{url} - 댓글 버튼 실패")
                continue

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".u_cbox_comment_box"))
                )
                comment_boxes = driver.find_elements(By.CSS_SELECTOR, ".u_cbox_comment_box")
                already_commented = any(MY_NICKNAME in c.text for c in comment_boxes)
                if already_commented:
                    print(f"⚠️ 이미 댓글 작성된 페이지: {url}")
                    continue
            except:
                print(f"{url} - 댓글 확인 실패 또는 없음")

            try:
                driver.find_element(By.CSS_SELECTOR, ".u_cbox_guide").click()
                time.sleep(1)
            except:
                pass

            prompt = f"""
            위 블로그 글을 읽은 20~30대가 쓸 법한 자연스러운 댓글을 한두 줄로 작성해줘.
            체험한 척 하지 말고, 정보나 이야기, 감정에 가볍게 공감하는 느낌이면 좋아. 말투는 너무 공손하거나 포멀하지 않게, 살짝 웃음 섞인 구어체로.
            이모지는 자제하되 '~', 'ㅋㅎㅎ', ':)' 정도는 사용 가능. 절대 AI처럼 느껴지지 않도록! 댓글만 출력해줘.
            
            제목: {title}
            내용 요약: {content}
            """
            response = model.generate_content(prompt)
            comment = response.text.strip()

            if not comment:
                print(f"{url} - 댓글 없음")
                continue

            try:
                textarea = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#naverComment__write_textarea"))
                )
                driver.execute_script("arguments[0].scrollIntoView(true);", textarea)
                textarea.click()
                time.sleep(0.5)
                textarea.send_keys(comment)
                time.sleep(1)

                submit_btn = driver.find_element(By.CSS_SELECTOR, ".__uis_naverComment_writeButton")
                driver.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
                submit_btn.click()
                time.sleep(random.uniform(5, 8))

                print(f"✅ 댓글 등록 완료: {url}")
                count += 1

            except Exception as e:
                print(f"{url} - 댓글 입력 실패: {str(e)}")
                continue

        except Exception as e:
            print(f"{url} - 전체 실패: {str(e)}")
            continue

finally:
    driver.quit()
