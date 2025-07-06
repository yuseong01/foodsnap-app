import pandas as pd
import os
import time
import urllib.parse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 입력/출력 CSV 경로
input_csv_path = "C:\\Cprogram\\SAI_FALCON\\foodsnap\\munu_missing_통합.csv"
output_csv_path = "C:\\Cprogram\\SAI_FALCON\\foodsnap\\menu_missing_네이버결과.csv"
CHROME_DRIVER_PATH = "C:\\Cprogram\\SAI_FALCON\\foodsnap\\chromedriver-win64\\chromedriver.exe"

# 크롬 드라이버 설정
options = webdriver.ChromeOptions()
options.add_argument("user-agent=Mozilla/5.0")
driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
wait = WebDriverWait(driver, 10)

# CSV 읽기
df_input = pd.read_csv(input_csv_path, encoding="utf-8-sig")
results = []

def search_and_extract_menu(keyword):
    query = urllib.parse.quote(keyword)
    search_url = f"https://map.naver.com/p/search/{query}"
    driver.get(search_url)
    time.sleep(4)

    try:
        driver.switch_to.frame("searchIframe")
        results_list = driver.find_elements(By.CSS_SELECTOR, 'ul#_pcmap_list_scroll_container li.item_place')
        if not results_list:
            return "검색 결과 없음", "검색 결과 없음"
        results_list[0].click()
        time.sleep(3)
        driver.switch_to.default_content()
        driver.switch_to.frame("entryIframe")

        # 메뉴탭 클릭 시도
        tabs = driver.find_elements(By.CSS_SELECTOR, "a.tab_item")
        menu_url = driver.current_url
        found_menu = False
        for tab in tabs:
            if "메뉴" in tab.text:
                tab.click()
                time.sleep(2)
                found_menu = True
                break

        if not found_menu:
            return menu_url, "메뉴탭 없음"

        # 메뉴 추출
        menu_items = driver.find_elements(By.CSS_SELECTOR, "li.E2jtL")
        menus = []
        for item in menu_items:
            try:
                name = item.find_element(By.CSS_SELECTOR, "span.lPzHi").text.strip()
                price = item.find_element(By.CSS_SELECTOR, "div.GXS1X em").text.strip()
                menus.append(f"{name} ({price}원)")
            except:
                continue

        return menu_url, "; ".join(menus) if menus else "메뉴 정보 없음"

    except Exception as e:
        return "오류", f"크롤링 실패: {e}"
    finally:
        driver.switch_to.default_content()

# 전체 행에 대해 크롤링
for idx, row in df_input.iterrows():
    full_keyword = f"{row['역']} {row['이름']}"
    name_only = row['이름']

    print(f"\n🔍 1차 검색: {full_keyword}")
    url, menu = search_and_extract_menu(full_keyword)

    if menu == "검색 결과 없음":
        print(f"🔁 2차 재검색: {name_only}")
        url, menu = search_and_extract_menu(name_only)

    results.append({
        "역": row["역"],
        "이름": row["이름"],
        "네이버메뉴링크": url,
        "네이버메뉴목록": menu
    })

# 종료 및 결과 저장
driver.quit()
df_result = pd.DataFrame(results)
df_result.to_csv(output_csv_path, index=False, encoding="utf-8-sig")
print(f"\n✅ 메뉴 정보 저장 완료: {output_csv_path}")
