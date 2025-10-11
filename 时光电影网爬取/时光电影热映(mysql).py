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

# 获取用户输入的爬取页数
pages_to_scrape = int(input("请输入要爬取的页数(1-10): "))
if pages_to_scrape < 1 or pages_to_scrape > 10:
    print("页数必须在1-10之间")
    exit()

# 创建数据库连接
try:
    connection = get_connection()
    cursor = connection.cursor()

    # 删除表（如果已存在）
    cursor.execute("DROP TABLE IF EXISTS mtime_movies")

    # 创建表
    create_table_query = """
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
        page_number INT COMMENT '页码',
        item_number INT COMMENT '本页序号',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    cursor.execute(create_table_query)
    connection.commit()
    print("数据库表已准备好")

except Exception as e:
    print(f"数据库连接或创建表失败: {str(e)}")
    exit()

# 创建浏览器对象
driver = webdriver.Chrome(options=options, service=service)
driver.maximize_window()

# 打开网页
url = 'http://list.mtime.com/listIndex'
driver.get(url)

# 等待页面加载完全
time.sleep(random.uniform(2, 4))

# 保存的数据
success_count = 0


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
        '主演详情': ''
    }

    try:
        # 在新标签页中打开详情页
        driver.execute_script("window.open('');")
        driver.switch_to.window(driver.window_handles[1])
        driver.get(detail_url)

        # 等待详情页加载
        time.sleep(random.uniform(3, 5))

        try:
            # 获取头部信息 - 包含片长、类型和上映时间
            header = driver.find_element(By.CSS_SELECTOR, 'div.m_head')

            # 片长 (格式如"142分钟")
            try:
                duration = header.find_element(By.CSS_SELECTOR, 'div.otherbox > span:first-child').text
                if '分钟' in duration:
                    details['片长'] = duration.strip()
                else:
                    details['片长'] = ''

            except:
                pass

            # 类型 (可能有多个类型，用斜杠分隔)
            try:
                genres = [a.text for a in header.find_elements(By.CSS_SELECTOR, 'div.otherbox > span > a')]
                details['类型'] = '/'.join(genres)
            except:
                pass

            # 上映时间 (格式如"1994年9月23日")
            try:
                release_date = header.find_element(By.CSS_SELECTOR, 'div.otherbox > a').text
                details['上映时间'] = release_date.strip()
            except:
                pass

            # 制片国家/地区
            try:
                country = header.find_element(By.CSS_SELECTOR, 'div.otherbox > span:last-child').text
                details['制片国家'] = country.strip()
            except:
                pass

        except Exception as e:
            print(f"获取头部信息失败: {str(e)}")

        try:
            # 获取剧情简介 - 根据之前的HTML结构
            plot_element = driver.find_element(By.CSS_SELECTOR, 'dt h4.px14.mt12 + p.mt6.moreEllipsis')
            details['剧情简介'] = plot_element.text
        except Exception as e:
            print(f"获取剧情简介失败")

        try:
            # 获取左侧信息栏的所有dd元素
            info_items = driver.find_elements(By.CSS_SELECTOR, 'dl.info_l > dd')
            for item in info_items:
                text = item.text
                if '导演：' in text:
                    continue  # 导演信息已经在主页面获取
                elif '编剧：' in text:
                    details['编剧'] = text.replace('编剧：', '').strip()
                elif '发行公司：' in text:
                    details['发行公司'] = text.replace('发行公司：', '').strip()
                elif '更多片名：' in text:
                    details['更多片名'] = text.replace('更多片名：', '').strip()
        except Exception as e:
            print(f"获取左侧信息栏失败")

        try:
            # 获取右侧主演信息
            actors = driver.find_elements(By.CSS_SELECTOR, 'ul.main_actor li')
            actors_list = []
            for actor in actors:
                try:
                    name = actor.find_element(By.CSS_SELECTOR, 'dd p.__r_c_ > a').text
                    role = actor.find_element(By.CSS_SELECTOR, 'dd p.__r_c_:last-child').text.replace('饰', '').strip()
                    actors_list.append(f"{name} 饰 {role}")
                except:
                    continue
            details['主演详情'] = '; '.join(actors_list)
        except Exception as e:
            print(f"获取主演信息失败: {str(e)}")

        # 关闭详情页标签，返回列表页
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(random.uniform(1, 2))

    except Exception as e:
        print(f"获取详情页信息失败")
        # 确保返回主窗口
        if len(driver.window_handles) > 1:
            driver.close()
            driver.switch_to.window(driver.window_handles[0])

    return details


for current_page in range(1, pages_to_scrape + 1):
    print(f"\n=== 正在爬取第 {current_page} 页 ===")

    # 等待电影列表加载
    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'movie-item-list-item'))
    )

    # 抓取电影榜单数据
    movies = driver.find_elements(By.CLASS_NAME, 'movie-item-list-item')

    for idx, movie in enumerate(movies, 1):
        try:
            # 获取基础信息
            title = movie.find_element(By.CLASS_NAME, 'movie-name').text
            director = movie.find_element(By.CLASS_NAME, 'movie-director').text.replace('导演: ', '')
            stars = movie.find_element(By.CLASS_NAME, 'movie-star').text.replace('主演: ', '')
            score = movie.find_element(By.CLASS_NAME, 'movie-score').text
            detail_url = movie.find_element(By.CSS_SELECTOR, '.top-pic a').get_attribute('href')
            img_url = movie.find_element(By.CSS_SELECTOR, '.top-pic img').get_attribute('src')

            # 获取详情页信息
            print(f"正在获取《{title}》的详情信息...")
            details = get_movie_details(detail_url)

            # 合并数据
            movie_info = {
                'movie_name': title,
                'director': director,
                'actors': stars,
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
                'page_number': current_page,
                'item_number': idx
            }

            # 插入数据到MySQL
            try:
                columns = ', '.join(movie_info.keys())
                placeholders = ', '.join(['%s'] * len(movie_info))
                sql = f"INSERT INTO mtime_movies ({columns}) VALUES ({placeholders})"

                cursor.execute(sql, list(movie_info.values()))
                connection.commit()
                success_count += 1
                print(f"✓ 成功保存到数据库: 《{title}》 (第{current_page}页第{idx}部)")
            except Exception as e:
                print(f"× 数据库插入失败: 《{title}》 - {str(e)}")
                connection.rollback()

        except Exception as e:
            print(f"× 第{current_page}页第{idx}部电影爬取失败")

    # 翻页处理
    if current_page < pages_to_scrape:
        try:
            next_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-next:not([disabled])')))
            driver.execute_script("arguments[0].click();", next_btn)
            time.sleep(random.uniform(3, 5))  # 翻页后等待
        except Exception as e:
            print(f"翻页到第{current_page + 1}页失败")
            break

# 关闭数据库连接
cursor.close()
connection.close()

# 关闭浏览器
driver.quit()

print(f"\n✅ 爬取完成，共保存 {success_count} 条数据到MySQL数据库")