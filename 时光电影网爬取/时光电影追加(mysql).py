import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from 数据库配置.数据库配置 import get_connection

# 设置浏览器
options = Options()
# chromedriver动态爬取，记得改谷歌浏览器的路径，版本是137
options.binary_location = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
options.add_argument('--disable-blink-features=AutomationControlled')
service = Service(r'chromedriver.exe')

# 创建数据库连接
try:
    connection = get_connection()
    cursor = connection.cursor()

    # 检查表是否存在，不存在则创建
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mtime_movies (
        id INT AUTO_INCREMENT PRIMARY KEY,
        movie_name VARCHAR(255) COMMENT '电影名称',
        director VARCHAR(255) COMMENT '导演',
        actors VARCHAR(500) COMMENT '主演',
        score double COMMENT '评分',
        genres VARCHAR(255) COMMENT '类型',
        release_date VARCHAR(100) COMMENT '上映时间',
        duration VARCHAR(100) COMMENT '片长',
        country VARCHAR(100) COMMENT '制片国家',
        plot TEXT COMMENT '剧情简介',
        writers VARCHAR(255) COMMENT '编剧',
        alternative_titles VARCHAR(255) COMMENT '更多片名',
        distributors VARCHAR(255) COMMENT '发行公司',
        actor_details TEXT COMMENT '主演详情',
        detail_url VARCHAR(500) COMMENT '详情页URL',
        image_url VARCHAR(500) COMMENT '图片URL',
        page_number VARCHAR(20) COMMENT '页码',
        item_number INT COMMENT '本页序号',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_movie (movie_name, detail_url)  # 添加唯一约束防止重复
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """)
    print("数据库表已准备好")

except Exception as e:
    print(f"数据库连接或创建表失败: {str(e)}")
    exit()

# 创建浏览器对象
driver = webdriver.Chrome(options=options, service=service)
driver.maximize_window()

# 打开网页
url = 'http://film.mtime.com/all/filmair'
driver.get(url)

# 等待页面加载完全
time.sleep(random.uniform(2, 4))


def get_movie_details(detail_url):
    """获取电影详情页的额外信息"""
    details = {
        '剧情简介': '',
        '上映时间': '',
        '片长': '',
        '类型': '',
        '制片国家': '',
        '编剧': '',
        '更多片名': '',
        '发行公司': '',
        '主演详情': '',
        '导演': ''
    }

    try:
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(detail_url)
        time.sleep(random.uniform(3, 5))

        try:
            header = driver.find_element(By.CSS_SELECTOR, 'div.m_head')
            try:
                duration = header.find_element(By.CSS_SELECTOR, 'div.otherbox > span:first-child').text
                details['片长'] = duration.strip() if '分钟' in duration else ''
            except:
                pass

            try:
                genres = [a.text for a in header.find_elements(By.CSS_SELECTOR, 'div.otherbox > span > a')]
                details['类型'] = '/'.join(genres)
            except:
                pass

            try:
                details['上映时间'] = header.find_element(By.CSS_SELECTOR, 'div.otherbox > a').text.strip()
            except:
                pass

            try:
                details['制片国家'] = header.find_element(By.CSS_SELECTOR,
                                                          'div.otherbox > span:last-child').text.strip()
            except:
                pass

        except:
            pass

        try:
            details['剧情简介'] = driver.find_element(By.CSS_SELECTOR, 'dt h4.px14.mt12 + p.mt6.moreEllipsis').text
        except:
            pass

        try:
            info_items = driver.find_elements(By.CSS_SELECTOR, 'dl.info_l > dd')
            for item in info_items:
                text = item.text
                if '导演：' in text:
                    details['导演'] = '/'.join([a.text for a in item.find_elements(By.CSS_SELECTOR, 'a')])
                elif '编剧：' in text:
                    details['编剧'] = '/'.join([a.text for a in item.find_elements(By.CSS_SELECTOR, 'a')])
                elif '国家地区：' in text:
                    details['制片国家'] = item.find_element(By.CSS_SELECTOR, 'a.country').text.strip()
                elif '发行公司：' in text:
                    details['发行公司'] = '/'.join([a.text for a in item.find_elements(By.CSS_SELECTOR, 'a')])
                elif '更多片名：' in text:
                    details['更多片名'] = item.find_element(By.CSS_SELECTOR, 'span').text.strip()
        except:
            pass

        try:
            actors = driver.find_elements(By.CSS_SELECTOR, 'ul.main_actor li')
            actors_list = []
            for actor in actors:
                try:
                    name_cn = actor.find_element(By.CSS_SELECTOR, 'dd p.__r_c_:first-child a').text
                    role = actor.find_element(By.CSS_SELECTOR, 'dd p.__r_c_:last-child').text.replace('饰', '').strip()
                    actors_list.append(f"{name_cn} 饰 {role}")
                except:
                    continue
            details['主演详情'] = '; '.join(actors_list)
            details['主演'] = '; '.join([actor.split(' 饰')[0] for actor in actors_list[:3]])
        except:
            pass

        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(random.uniform(1, 2))

    except Exception as e:
        print(f"获取详情页信息失败: {str(e)}")
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    return details


# 等待电影列表加载
WebDriverWait(driver, 15).until(
    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div.film_item'))
)

# 抓取电影榜单数据
movies = driver.find_elements(By.CSS_SELECTOR, 'div.film_item')
success_count = 0

for idx, movie in enumerate(movies, 1):
    try:
        title = movie.find_element(By.CSS_SELECTOR, 'div.film_name a').text.strip()
        try:
            score = movie.find_element(By.CSS_SELECTOR, 'div.film_score').text.strip()
        except:
            score = None
        detail_url = movie.find_element(By.CSS_SELECTOR, 'div.img_content a').get_attribute('href')
        try:
            img_url = movie.find_element(By.CSS_SELECTOR, 'div.img_content img').get_attribute('src')
        except:
            img_url = ''

        print(f"正在获取《{title}》的详情信息...")
        details = get_movie_details(detail_url)

        # 准备插入数据
        movie_info = {
            'movie_name': title,
            'director': details.get('导演', ''),
            'actors': details.get('主演', ''),
            'score': score,
            'genres': details.get('类型', ''),
            'release_date': details.get('上映时间', ''),
            'duration': details.get('片长', ''),
            'country': details.get('制片国家', ''),
            'plot': details.get('剧情简介', ''),
            'writers': details.get('编剧', ''),
            'alternative_titles': details.get('更多片名', ''),
            'distributors': details.get('发行公司', ''),
            'actor_details': details.get('主演详情', ''),
            'detail_url': detail_url,
            'image_url': img_url,
            'page_number': "1",
            'item_number': idx
        }

        # 构建INSERT语句 - 使用ON DUPLICATE KEY UPDATE实现更新已有记录
        columns = ', '.join(movie_info.keys())
        placeholders = ', '.join(['%s'] * len(movie_info))
        update_cols = ', '.join(
            [f"{col}=VALUES({col})" for col in movie_info.keys() if col not in ('movie_name', 'detail_url')])

        sql = f"""
        INSERT INTO mtime_movies ({columns}) 
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_cols}
        """

        try:
            cursor.execute(sql, list(movie_info.values()))
            success_count += 1
            print(f"✓ 成功保存到数据库: 《{title}》 (第{idx}部)")
        except Exception as e:
            print(f"× 数据库插入失败: 《{title}》 - {str(e)}")

    except Exception as e:
        print(f"× 第{idx}部电影爬取失败: {str(e)}")

# 查询数据库中总记录数
cursor.execute("SELECT COUNT(*) FROM mtime_movies")
total_count = cursor.fetchone()[0]

# 关闭连接
cursor.close()
connection.close()

# 关闭浏览器
driver.quit()

print(f"\n✅ 爬取完成，成功保存/更新 {success_count} 条数据，数据库中现有 {total_count} 条电影数据")
