from price_searching import price_searching
import sqlite3
import re
from flask import Flask, render_template, request, redirect, url_for, session
from map import finding_place_to_eat

from selenium import webdriver as wb
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Flask 애플리케이션 초기화
app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # 실제 배포 시에는 강력한 시크릿 키로 변경하세요!

# --- 재료 이름 정규화 헬퍼 함수
def normalize_ingredient_name(ingredient_string):
    """
    쉼표로 분리된 재료 문자열에서 괄호·단위 등을 제거하고
    순수 한글 재료명만 리스트로 반환
    """
    if not ingredient_string:
        return []

    names = []
    # 쉼표 기준으로 분리
    parts = [p.strip() for p in ingredient_string.split(',') if p.strip()]
    for part in parts:
        # 1) 괄호 이전까지만
        raw = part.split('(')[0].strip()
        # 2) 공백 기준 토큰 분리
        tokens = raw.split()
        if not tokens:
            # e.g. part 가 "(선택)" 같이 빈 토큰만 있을 때 건너뜀
            continue

        first = tokens[0]  # e.g. "김치", "밥"
        # 3) 한글 연속 패턴 매칭
        m = re.match(r'^([가-힣]+)', first)
        if m:
            names.append(m.group(1))
    return names

# --- DB에서 cook_ingredient 테이블 로드 ---
def load_ingredients_from_db(db_path: str = 'cook.db') -> list:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute('SELECT * FROM cook_ingredient')
    rows = cur.fetchall()
    conn.close()

    data = []
    for row in rows:
        entry = {
            'food_number':           row['food_number'],
            'food_name':             row['food_name'],
            'types_cooking':         row['types_cooking'],
            'ingredient_main':       row['ingredient_main'],
            'ingredient_sub':        row['ingredient_sub'],
            'seasoning':             row['seasoning'],
            'national_classification': row['national_classification'],
            'image_url':             row['image_url']
        }
        # kcal 정수 변환
        try:
            kcal_raw = str(row['kcal'])
            entry['kcal'] = int(re.sub(r'[^0-9]', '', kcal_raw))
        except:
            entry['kcal'] = 0

        # 재료 리스트 생성 (정규화된 이름)
        ings = []
        ings += normalize_ingredient_name(entry['ingredient_main'])
        ings += normalize_ingredient_name(entry['ingredient_sub'])
        ings += normalize_ingredient_name(entry['seasoning'])
        entry['ingredients_list'] = ings

        # 원본 재료 리스트 생성 (분량이 포함된 원본 재료)
        original_ings = []
        if entry['ingredient_main']:
            original_ings.extend([p.strip() for p in entry['ingredient_main'].split(',') if p.strip()])
        if entry['ingredient_sub']:
            original_ings.extend([p.strip() for p in entry['ingredient_sub'].split(',') if p.strip()])
        if entry['seasoning']:
            original_ings.extend([p.strip() for p in entry['seasoning'].split(',') if p.strip()])
        entry['original_ingredients_list'] = original_ings

        data.append(entry)
    return data

# --- DB에서 cook_recipe 테이블 로드 ---
def load_recipes_from_db(db_path: str = 'cook.db') -> list:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute('SELECT * FROM cook_recipe')
    rows = cur.fetchall()
    conn.close()

    data = []
    for row in rows:
        entry = {
            'food_number': row['food_number'],
            'food_name': row['food_name'],
            'recipe': row['recipe'],
            'serving_number': row['serving_number'],
            'level': row['level']
        }
        data.append(entry)
    return data

# --- 초기 데이터 로드 ---
COOK_INGREDIENT_DATA = load_ingredients_from_db('cook.db')
COOK_RECIPE_DATA = load_recipes_from_db('cook.db')

# --- 외부 API 시뮬레이션 함수 ---
def youtube_link(food_name: str) -> dict:
    """
    쇼츠 2개, 일반 2개를 분리해서
    {'shorts': [ {'title':..., 'link':...}, ... ],
     'normal': [ {'title':..., 'link':...}, ... ] }
    형태로 리턴합니다.
    """    
    options = wb.ChromeOptions()
    options.add_argument('headless') 
    options.add_argument('window-size=1920x1080') 
    options.add_argument("disable-gpu")
                         

    driver = wb.Chrome(options=options)

    driver.get("https://www.youtube.com/")
    driver.maximize_window()
    # 검색
    search = driver.find_element(By.CSS_SELECTOR, ".ytSearchboxComponentSearchForm>input")
    search.click()
    search.send_keys(f"{food_name} 레시피")
    search.send_keys(Keys.ENTER)

    # 결과 로딩 대기
    elements = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a#video-title"))
    )

    shorts_vids = []
    normal_vids = []
    for el in elements[:10]:
        href  = el.get_attribute("href")
        title = el.get_attribute("title") or el.text

        # **여기** 꼭 `'title'` 과 `'link'` 로 저장!
        vid_info = {
            "title": title,
            "link":  href
        }

        if "/shorts/" in href and len(shorts_vids) < 2:
            shorts_vids.append(vid_info)
        elif "/watch?" in href and len(normal_vids) < 2:
            normal_vids.append(vid_info)

    driver.quit()
    return {"shorts": shorts_vids, "normal": normal_vids}

def to_embed_url(raw_url: str) -> str:
    # watch?v=abc123 → abc123
    m = re.search(r"(?:v=|\/shorts\/)([\w\-]+)", raw_url)
    if not m:
        return raw_url
    vid = m.group(1)
    return f"https://www.youtube.com/embed/{vid}"

def get_youtube_links_from_api(dish_name: str) -> list:
    vids = youtube_link(dish_name)
    out = []
    for section in ("shorts","normal"):
        for info in vids[section]:
            out.append({
                "title": info["title"],
                # raw link → embed link
                "link":  to_embed_url(info["link"])
            })
    return out

def get_buy_link_from_api(dish_name):
    return f'https://www.coupang.com/search?q={dish_name}+재료'

def get_restaurants_from_api(dish_name):
    search_result_url = finding_place_to_eat(dish_name)
    return search_result_url

# --- 요리 찾기 로직 (이 함수는 다른 라우트들보다 위에 정의되어야 합니다!) ---

def find_recipes_by_ingredients(user_ingredients_list):
    """
    사용자가 제공한 재료(예: ['콩', '밥'])를
    COOK_INGREDIENT_DATA의 ingredients_list(예: ['강낭콩', '쌀'])와
    부분 매칭하여 필터링합니다.
    """
    # 1) 사용자 입력 재료 정규화 및 소문자화
    normalized_users = []
    for ing in user_ingredients_list:
        parts = normalize_ingredient_name(ing)
        if parts:
            normalized_users.append(parts[0].lower())
    # 예: ['콩', '밥']
    results = []
    for info in COOK_INGREDIENT_DATA:
        # 레시피에 저장된 재료들 소문자화
        recipe_ings = [ri.lower() for ri in info['ingredients_list']]
        # 모든 사용자 재료가 어느 하나의 recipe_ing에 포함되는지 검사
        if all(any(user in recipe_ing for recipe_ing in recipe_ings)
               for user in normalized_users):
            # image_url이 비어 있으면 플레이스홀더 채워두기
            if not info.get('image_url'):
                info['image_url'] = (
                  'https://placehold.co/250x150/cccccc/333333?text=이미지+없음'
                )
            results.append(info)
    return results


# --- Flask 라우트 정의 ---
@app.route('/')
def main_page():
    return render_template('main_food_choice.html')

@app.route('/choose', methods=['POST'])
def handle_food_choice():
    place = request.form.get('where')
    if place == 'home':
        return render_template('home_ingredient_count_input.html')
    else:
        return render_template('out_restaurant_recommendation.html', recommended_restaurants_list=None)

@app.route('/home_dish_ingredient_count_input', methods=['GET', 'POST'])
def home_dish_ingredient_count_input():
    if request.method == 'POST':
        count = int(request.form.get('ingredient_count', 0))
        if 2 <= count <= 10:
            return render_template('home_ingredient_details_input.html', ingredient_count=count)
        else:
            return render_template('home_ingredient_count_input.html', error_message="재료 개수는 2개에서 10개 사이로 입력해주세요.")
    return render_template('home_ingredient_count_input.html')

@app.route('/dish_selection_page', methods=['POST'])
def dish_selection_page():
    user_ings = [v for k, v in request.form.items() if k.startswith('ingredient_') and v]
    normalized_user_ings_for_display = []
    for ing in user_ings:
        normalized_name = normalize_ingredient_name(ing)
        if normalized_name:
            normalized_user_ings_for_display.append(normalized_name[0])
    
    # 여기서 find_recipes_by_ingredients가 정상적으로 호출됩니다.
    dishes = find_recipes_by_ingredients(user_ings)
    return render_template('home_dish_selection.html',
                           input_ingredients_list=normalized_user_ings_for_display,
                           recommended_dish_list=dishes)

@app.route('/view_recipe', methods=['POST'])
def view_recipe():
    sel_no = int(request.form.get('selected_dish_number'))
    general = next((d for d in COOK_INGREDIENT_DATA if d['food_number'] == sel_no), None)
    detail = next((r for r in COOK_RECIPE_DATA if r['food_number'] == sel_no), None)
    if not general or not detail:
        return redirect(url_for('home_dish_ingredient_count_input'))
    
    recipe = {**general, **detail}
    recipe['recipe_text'] = detail['recipe']
    raw = youtube_link(general['food_name'])
    recipe['video_links'] = get_youtube_links_from_api(general['food_name'])
    
    recipe['video_links'] = get_youtube_links_from_api(general['food_name'])
    recipe['buy_link'] = get_buy_link_from_api(general['food_name'])

    user_ingredients_str = request.form.get('user_ingredients_str', '')
    user_ingredients_list_raw = [s.strip() for s in user_ingredients_str.split(',') if s.strip()]

    # 세션에 필요한 데이터를 저장합니다. (크롤링은 여기서 하지 않습니다)
    session['selected_recipe_ingredients'] = general['ingredients_list']
    session['user_provided_ingredients'] = user_ingredients_list_raw
    session['recipe_food_name'] = general['food_name']

    return render_template('home_dish_recipe_display.html', recipe=recipe)

@app.route('/missing_ingredients') # POST를 제거하고 GET만 허용하거나, GET, POST 모두 허용하되 POST 데이터를 사용하지 않도록 수정합니다.
def missing_ingredients():
    # 이 라우트에서는 'selected_dish_number'와 같은 폼 데이터를 받지 않습니다.
    # 모든 정보는 세션에서 가져옵니다.

    selected_recipe_ingredients = session.pop('selected_recipe_ingredients', None)
    user_provided_ingredients = session.pop('user_provided_ingredients', None)
    recipe_food_name = session.pop('recipe_food_name', '선택된 요리')

    missing_ingredients_data = []
    info_message = None

    if selected_recipe_ingredients and user_provided_ingredients:
        # 사용자가 가진 재료를 정규화하여 소문자 집합으로 만듭니다.
        user_have_lower = {normalize_ingredient_name(ing)[0].lower() if normalize_ingredient_name(ing) else '' for ing in user_provided_ingredients if ing}
        
        actual_missing_names = []
        for ingredient_in_recipe in selected_recipe_ingredients:
            if ingredient_in_recipe.lower() not in user_have_lower:
                actual_missing_names.append(ingredient_in_recipe)

        if actual_missing_names:
            # 부족한 재료가 있을 때만 price_searching (크롤링)을 수행합니다.
            missing_ingredients_data = price_searching(actual_missing_names)
        else:
            info_message = "모든 재료가 충분합니다! 별도로 구매할 재료가 없어요."
    else:
        # 세션 데이터가 없는 경우 (예: 새로고침 또는 직접 URL 접근)
        info_message = "재료 정보를 다시 불러올 수 없습니다. 레시피 페이지에서 다시 시도해주세요."
        return redirect(url_for('main_page')) # 메인 페이지로 리다이렉트

    return render_template('missing_ingredients.html',
                           missing_ingredients=missing_ingredients_data,
                           recipe_food_name=recipe_food_name,
                           info_message=info_message)

@app.route('/out_restaurant_recommendation', methods=['POST'])
def out_restaurant_recommendation():
    menu = request.form.get('menu', '')
    search_url = get_restaurants_from_api(menu) if menu else ""
    recommended_restaurants_list = []
    if search_url:
        recommended_restaurants_list.append({
            'name': f"'{menu}' 맛집 검색 결과",
            'address': "자세한 정보는 아래 링크를 클릭하세요.",
            'image_url': "https://placehold.co/250x150/ff6f61/ffffff?text=Click+Link", # 링크를 위한 대체 이미지
            'link': search_url # 실제 검색 결과 URL
            })
    return render_template('out_restaurant_recommendation.html', recommended_restaurants_list=recommended_restaurants_list)

if __name__ == '__main__':
    app.run(debug=True)