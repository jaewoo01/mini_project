from selenium import webdriver as wb
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests as rq
import time # time 모듈이 없으면 추가해주세요

def finding_place_to_eat(food_name):
    dining="https://www.naver.com/"
    options = wb.ChromeOptions()
    prefs={"profile.default_content_setting_values.geolocation":1} #위치 정보 권한을 허용으로 설정
    options.add_experimental_option("prefs", prefs)
    options.add_argument('headless') # Headless 모드 활성화
    options.add_argument('window-size=1920x1080') # 창 크기 설정 (headless에서도 중요)
    options.add_argument("disable-gpu")
    options.add_argument("no-sandbox") # 샌드박스 비활성화 (Docker 등 환경에서 필요할 수 있음)
    options.add_argument("disable-dev-shm-usage") # /dev/shm 사용 비활성화 (Docker 등 환경에서 필요할 수 있음)
    driver = wb.Chrome(options=options)
    driver.get(dining)
    time.sleep(2)
    driver.maximize_window()
    
    #WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "input_search")))
    search_dining = driver.find_element(By.CSS_SELECTOR, ".search_input")
    search_dining.click()
    search_dining.send_keys(f"{food_name} 맛집")
    search_dining.send_keys(Keys.ENTER)
    cur_url = driver.find_element(By.CSS_SELECTOR, ".bSoi3>a").get_attribute("href")
    return cur_url