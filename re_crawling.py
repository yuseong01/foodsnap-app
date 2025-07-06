import os
import csv
import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# ---------- 설정 영역 ----------
CRAWL_DIR = r"C:\Users\rkdgu\Documents\GitHub\foodsnap-app"
NO_MENU_CSV = os.path.join(CRAWL_DIR, "crawling_result", "no_menu_link.csv")
OUTPUT_CSV = os.path.join(CRAWL_DIR, "재크롤링_결과.csv")
WAIT_TIMEOUT = 30  # 대기 최대 시간 (초)
RETRY_COUNT = 3  # 메뉴 로딩 재시도 횟수


# ---------- 유틸 함수 ----------
def load_no_menu_links(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["파일명"] = df["파일"].apply(lambda p: os.path.basename(p))
    return df


def write_header(path: str):
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(
                [
                    "역",
                    "이름",
                    "주소",
                    "상세보기",
                    "원본_메뉴",
                    "새_메뉴",
                    "이유",
                    "크롤링_시간",
                ]
            )


def append_result(path: str, rec: dict):
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerow(
            [
                rec["역"],
                rec["이름"],
                rec["주소"],
                rec["상세보기"],
                rec["원본_메뉴"],
                rec["새_메뉴"],
                rec["이유"],
                rec["크롤링_시간"],
            ]
        )


# ---------- 크롤러 초기화 ----------
def init_driver() -> webdriver.Chrome:
    opts = webdriver.ChromeOptions()
    # opts.add_argument("--headless")  # 필요 시 활성화
    opts.add_argument("user-agent=Mozilla/5.0")
    opts.add_argument("--disable-logging")
    opts.add_argument("--log-level=3")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


# ---------- 메뉴 크롤링 함수 ----------
def fetch_menu(driver: webdriver.Chrome, wait: WebDriverWait, url: str) -> list[str]:
    """
    1) URL 접속
    2) “데이터를 불러올 수 없습니다” 오류 감지 시 뒤로가기
    3) 메뉴 탭 클릭 → 메뉴 리스트 추출
    4) TimeoutException 시 최대 RETRY_COUNT 회 재시도
    """
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            driver.get(url)
            wait.until(EC.presence_of_element_located((By.ID, "mainContent")))

            # 오류 화면 감지 후 뒤로가기
            try:
                empty = driver.find_element(By.CSS_SELECTOR, ".wrap_empty .info_empty")
                if empty.text.strip() == "데이터를 불러올 수 없습니다":
                    driver.back()
                    wait.until(EC.presence_of_element_located((By.ID, "mainContent")))
            except NoSuchElementException:
                pass

            # 메뉴 탭 클릭
            tab = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a.link_tab[href='#menuInfo']")
                )
            )
            driver.execute_script("arguments[0].scrollIntoView();", tab)
            tab.click()

            # 메뉴 항목 로딩 대기
            wait.until(
                EC.visibility_of_all_elements_located(
                    (By.CSS_SELECTOR, ".wrap_goods ul.list_goods > li")
                )
            )
            items = driver.find_elements(
                By.CSS_SELECTOR, ".wrap_goods ul.list_goods > li"
            )

            # 메뉴명 및 가격 추출
            result = []
            for it in items:
                name = it.find_element(By.CSS_SELECTOR, ".tit_item").text.strip()
                price_elems = it.find_elements(By.CSS_SELECTOR, ".desc_item")
                price = price_elems[0].text.strip() if price_elems else ""
                result.append(f"{name} ({price})" if price else name)
            return result or ["메뉴 정보 없음"]

        except TimeoutException:
            if attempt == RETRY_COUNT:
                return ["메뉴 로딩 실패"]
            time.sleep(1)  # 재시도 전 대기


# ---------- 메인 실행부 ----------
def main():
    df_no = load_no_menu_links(NO_MENU_CSV)
    if df_no.empty:
        print("❌ no_menu_link.csv에 대상이 없습니다.")
        return

    write_header(OUTPUT_CSV)
    driver = init_driver()
    wait = WebDriverWait(driver, WAIT_TIMEOUT)

    try:
        for idx, row in df_no.iterrows():
            src_file = os.path.join(CRAWL_DIR, row["파일명"])
            orig_df = pd.read_csv(src_file, encoding="utf-8-sig")
            url = orig_df.iloc[int(row["행번호"]) - 1]["상세보기"]

            menus = fetch_menu(driver, wait, url)
            record = {
                "역": row["역"],
                "이름": row["이름"],
                "주소": row["주소"],
                "상세보기": url,
                "원본_메뉴": row["메뉴"],
                "새_메뉴": "; ".join(menus),
                "이유": row["이유"],
                "크롤링_시간": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            append_result(OUTPUT_CSV, record)
            print(f"[저장] {idx+1}/{len(df_no)}: {row['이름']}")
            time.sleep(random.uniform(1.0, 2.0))

    finally:
        driver.quit()
        print(f"✅ 재크롤링 완료. 결과는 '{OUTPUT_CSV}'에 저장되었습니다.")


if __name__ == "__main__":
    main()
