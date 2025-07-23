from selenium import webdriver as wb
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait # 추가
from selenium.webdriver.support import expected_conditions as EC # 추가

def price_searching(ingredient_list):
    missing_ingredients_details = []
    
    oasis_url = "https://www.oasis.co.kr/main"

    options = wb.ChromeOptions()
    options.add_argument('headless') 
    options.add_argument('window-size=1920x1080') 
    options.add_argument("disable-gpu") 

    driver = wb.Chrome(options=options) 
    
    try:
        driver.get(oasis_url)
        # time.sleep(2) # 변경: 명시적 대기로 교체
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body"))) # 페이지 로드 대기

        # 팝업 닫기 (요소가 바로 없을 수 있으므로 try-except로 처리)
        try:
            close_btn = driver.find_element(By.CSS_SELECTOR, ".btn_close_1day")
            close_btn.click()
            # time.sleep(1) # 변경: 명시적 대기로 교체
            WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".btn_close_1day"))) # 팝업이 사라질 때까지 대기
        except Exception as e: # 원래 있던 Exception 처리 그대로 유지
            print(f"팝업이 없거나 닫기 버튼을 찾을 수 없습니다: {e}")

        for ingred in ingredient_list:
            # 검색창 클릭 및 재료 입력
            try:
                search_oasis = driver.find_element(By.CSS_SELECTOR, ".keywordSearch")
                WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".keywordSearch"))) # 검색창 클릭 가능할 때까지 대기
                search_oasis.click()
                # time.sleep(1) # 변경: 위에서 클릭 가능 대기 후 바로 send_keys 가능하도록
                search_oasis.send_keys(ingred)
                search_oasis.send_keys(Keys.ENTER)
                # time.sleep(3) # 변경: 명시적 대기로 교체
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".wrapImg>a"))) # 검색 결과 요소가 나타날 때까지 대기
            except Exception as e:
                print(f"'{ingred}' 검색 중 오류 발생: {e}")
                missing_ingredients_details.append({
                    'name': ingred, 
                    'sellers': [] 
                })
                driver.get(oasis_url) 
                # time.sleep(2) # 변경: 명시적 대기로 교체
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body"))) # 메인 페이지 로드 대기
                continue 

            # --- 이미지 링크(href)와 가격 추출 부분 (기존 코드 유지) ---
            image_link = '정보 없음'
            product_img_url = driver.find_element(By.CSS_SELECTOR, ".swiper-lazy").get_attribute('src')
            best_product_price = '정보 없음'

            try:
                # .wrapimg 클래스 내의 첫 번째 <a> 태그를 찾아서 href 가져오기
                # 이 부분은 이미 위에서 ".wrapImg>a"가 존재할 때까지 기다렸으므로, 바로 find_element 시도
                image_element = driver.find_element(By.CSS_SELECTOR, ".wrapImg>a")
                image_link = image_element.get_attribute('href')
            except Exception as e:
                print(f"'{ingred}'의 이미지 링크를 찾을 수 없습니다: {e}")

            try:
                # 베스트 상품 가격 (할인 가격) 가져오기
                best_product_element = driver.find_element(By.CSS_SELECTOR, ".price_discount")
                best_product_price = best_product_element.text
            except Exception as e:
                print(f"'{ingred}'의 베스트 상품 가격을 찾을 수 없습니다: {e}")

            seller_info = []
            # --- 리턴값만 변경하는 부분 시작 ---
            if image_link != '정보 없음' and best_product_price != '정보 없음':
                seller_info.append({
                    'seller_name': '오아시스', 
                    'image_url': product_img_url,       
                    'link': image_link,             
                    'price': best_product_price,    
                    'type': '베스트 상품'            
                })
            elif image_link != '정보 없음': 
                seller_info.append({
                    'seller_name': '오아시스', 
                    'image_url': product_img_url, 
                    'link': image_link,
                    'price': '가격 정보 없음', 
                    'type': '베스트 상품' 
                })
            elif best_product_price != '정보 없음': 
                seller_info.append({
                    'seller_name': '오아시스', 
                    'image_url': 'https://placehold.co/100x100/cccccc/333333?text=사진없음', 
                    'link': '#', 
                    'price': best_product_price, 
                    'type': '베스트 상품' 
                })
            
            missing_ingredients_details.append({
                'name': ingred,
                'sellers': seller_info
            })
            # --- 리턴값만 변경하는 부분 끝 ---
            
            # 다음 검색을 위해 메인 페이지로 돌아가기
            driver.get(oasis_url)
            # time.sleep(2) # 변경: 명시적 대기로 교체
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "body"))) # 메인 페이지 로드 대기

    except Exception as e:
        print(f"전체 검색 과정에서 오류 발생: {e}")
    finally:
        driver.quit() 
        
    return missing_ingredients_details
