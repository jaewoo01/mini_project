from selenium import webdriver as wb # 브라우저 제어
from selenium.webdriver.common.by import By # 선택자 구분
from selenium.webdriver.common.keys import Keys # 키보드 제어
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException # selenium 요소 에러 예외 처리 코드
import requests # 요청 관련 라이브러리
from selenium.webdriver.support.ui import WebDriverWait #
from selenium.webdriver.support import expected_conditions as EC #
import time


#빈리스트 생성
food_number_list             = []
food_name_list               = []
types_cooking_list           = []
national_classification_list = []
food_diff_list               = []
food_cal_list                = []
food_portion_list            = []
food_main_ingredients_list   = []
food_sub_ingredients_list    = []
food_spices_ingredients_list = []
food_recipe_list             = []
food_image_list  = []


url_food = "https://www.menupan.com/Cook/RecipeRe.asp?difficulty=10" # 난이도 분류 음식 사이트
driver = wb.Chrome()
wait = WebDriverWait(driver, 10) # 최대 10초까지 대기
driver.get(url_food)
i=0


try:
    diff_page = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/Cook/RecipeRe.asp?difficulty="]') # diff 페이지 이동
    for next_page in range(1, len(diff_page)):
        while True:
            try:
                try:
                    page_list = driver.find_elements(By.CLASS_NAME, "list_navi_pg_cur")
                    for page_num in range(len(page_list)+1):
                        food_lists = driver.find_elements(By.CSS_SELECTOR, 'span.link > a[href*="goRecipeView"]') # 현재 페이지에 있는 음식 데이터
                        food_lists = [elem for elem in food_lists if elem.text.strip() != ""]
                        for food_index in range(len(food_lists)):
                            i += 1
                            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span.link > a[href*="goRecipeView"]')))  # 목록 복귀 대기
                            food_lists = driver.find_elements(By.CSS_SELECTOR, 'span.link > a[href*="goRecipeView"]')
                            food_lists[food_index].click()
                            wait.until(EC.presence_of_element_located((By.TAG_NAME, "h2")))  # 목록 복귀 대기
                            food_name = driver.find_element(By.TAG_NAME, "h2").text # 음식 이름
                            food_type = driver.find_element(By.CLASS_NAME, "name").text # 방법 분류
                            food_country = driver.find_elements(By.CSS_SELECTOR, "dd.type a")[-1].text # 국가 분류
                            food_info_list = driver.find_elements(By.CLASS_NAME, "restTxt") # 난이도, 칼로리 데이터
                            food_diff = food_info_list[1].text.split()[1] # 난이도
                            food_cal = food_info_list[2].text.split()[1] # 칼로리
                            food_table_info = driver.find_element(By.CLASS_NAME, "tableLR").text.split("\n") # 재료 정보
                            food_portion = food_table_info[1] # 분량
                            food_main_ingredients = food_table_info[3] # 주재료
                            try:
                                food_sub_ingredients = food_table_info[5] # 부재료
                            except:
                                food_sub_ingredients = None
                            try:
                                food_spices_ingredients = food_table_info[7] #양념
                            except:
                                food_spices_ingredients = None
                            food_recipe_info = driver.find_elements(By.CLASS_NAME, "recipePlus dt") # 레시피
                            recipe_text = [elem.text for elem in food_recipe_info] # webelement 요소를 text로 추출
                            food_recipe = '\n'.join(recipe_text) # list형식을 \n구문으로 한 요소로 합치기

                            try:
                                # 사이트 구조에 맞는 셀렉터로 메인 이미지를 찾아주세요.
                                img_elem = driver.find_element(By.CSS_SELECTOR, "div.areaThumbnail dt img.img")
                                img_url = img_elem.get_attribute("src")
                            except NoSuchElementException:
                                img_url = None

                                
                            # append
                            food_number_list.append(i)
                            food_name_list.append(food_name)
                            types_cooking_list.append(food_type)
                            national_classification_list.append(food_country)
                            food_diff_list.append(food_diff)
                            food_cal_list.append(food_cal)
                            food_portion_list.append(food_portion)
                            food_main_ingredients_list.append(food_main_ingredients)
                            food_sub_ingredients_list.append(food_sub_ingredients)
                            food_spices_ingredients_list.append(food_spices_ingredients)
                            food_recipe_list.append(food_recipe)
                            food_image_list.append(img_url)

                            
                            time.sleep(0.2)
                            driver.back()
                        page_list = driver.find_elements(By.CLASS_NAME, "list_navi_pg_cur")
                        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "list_navi_pg_cur")))
                        page_list[page_num].click() # 페이지 이동
                        page_list = driver.find_elements(By.CLASS_NAME, "list_navi_pg_cur") # 페이지 수 리스트
                except IndexError:
                    None
                right_page = driver.find_element(By.CSS_SELECTOR, 'img[src="/Common/nvIMG/Button/listNext.gif"]')
                right_page.click()
                time.sleep(5)
            except NoSuchElementException:
                break
        diff_page = driver.find_elements(By.CSS_SELECTOR, 'a[href^="/Cook/RecipeRe.asp?difficulty="]')
        diff_page[next_page].click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href^="/Cook/RecipeRe.asp?difficulty="]')))
except IndexError:
    None


# In[ ]:


# Made CSV
import csv
# 음식정보 ( 요리이름,요리종류,재료,양념,국가,칼로리)
# example.csv 파일을 쓰기 모드로 열기
with open("./cook_ingredient.csv", 'w', newline='', encoding="utf-8-sig") as f:
    wtr = csv.writer(f)
    # 1) header (컬럼명) 쓰기
    wtr.writerow(["food_number", "food_name", "types_cooking" , "ingredient_main" , "ingredient_sub", "seasoning", "national_classification" , "kcal" , "image_url"])
    # 2) for문을 이용한 여러 행 쓰기
    food_name_list = food_name_list
    food_number_list = food_number_list
    types_cooking_list = types_cooking_list
    ingredient_main_list = food_main_ingredients_list
    ingredient_sub_list = food_sub_ingredients_list
    seasoning_list = food_spices_ingredients_list
    national_classification_list = national_classification_list
    kcal_list = food_cal_list
    image_url_list = food_image_list
    
    for i in range(len(food_name_list)):
        wtr.writerow([food_number_list[i], food_name_list[i], types_cooking_list[i], ingredient_main_list[i],ingredient_sub_list[i] ,seasoning_list[i] ,  national_classification_list[i] , kcal_list[i] , image_url_list[i] ])
# 레시피 (음식이름,레시피,인분,난이도,요리종류)
with open("./cook_recipe.csv", 'w', newline='', encoding="utf-8-sig") as f:
    wtr = csv.writer(f)
    # 1) header (컬럼명) 쓰기
    wtr.writerow(["food_number", "food_name", "recipe", "serving_number" , "level"])
    # 2) for문을 이용한 여러 행 쓰기
    food_number_list  = food_number_list
    food_name_list = food_name_list
    recipe_list = food_recipe_list
    serving_number_list = food_portion_list
    level_list = food_diff_list
    for i in range(len(food_name_list)):
        wtr.writerow([food_number_list[i], food_name_list[i], recipe_list[i], serving_number_list[i],level_list[i] ])


# In[ ]:


# Made DB
# CSV->DB
import pandas as pd
import sqlite3
#음식정보 ( 요리이름,요리종류,재료,양념,국가,칼로리)
# CSV 읽기
df = pd.read_csv('cook_ingredient.csv')
# DB 연결
conn = sqlite3.connect('cook.db')
# to_sql 사용 (이미 있으면 덮어쓰기)
df.to_sql('cook_ingredient', conn, if_exists='replace', index=False)
conn.close()
# 레시피 (음식이름,레시피,인분,난이도,요리종류)
df = pd.read_csv('cook_recipe.csv')
conn = sqlite3.connect('cook.db')
df.to_sql('cook_recipe', conn, if_exists='replace', index=False)
conn.close()










