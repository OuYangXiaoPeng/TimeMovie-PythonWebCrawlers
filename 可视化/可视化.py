import matplotlib

matplotlib.use('TkAgg')
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
from 数据库配置.数据库配置 import get_connection

# 设置中文字体
font_path = '../字体/SimHei.ttf'  # Windows系统SimHei字体路径
myfont = FontProperties(fname=font_path)

# 连接MySQL数据库获取数据
conn = get_connection()

df = pd.read_sql("SELECT * FROM mtime_movies", conn)
conn.close()

# 配置全局参数
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 150

# 1. 评分分布直方图
plt.figure(figsize=(6, 4))
n, bins, patches = plt.hist(df['score'].dropna(), bins=15, color='#1f77b4', edgecolor='white')

# 添加正态分布曲线
from scipy.stats import norm

# 净化评分列，转换为数值，非数字会变成 NaN
df['score'] = pd.to_numeric(df['score'], errors='coerce')
# 然后再计算均值和标准差
mu, sigma = df['score'].mean(), df['score'].std()
x = np.linspace(bins[0], bins[-1], 100)
plt.plot(x, norm.pdf(x, mu, sigma) * len(df) * 0.8, 'r-', linewidth=1.5)

plt.title('电影评分分布', fontproperties=myfont)
plt.xlabel('评分', fontproperties=myfont)
plt.ylabel('电影数量', fontproperties=myfont)
plt.grid(axis='y', alpha=0.3)

# 添加统计信息
stats_text = f'平均值 = {mu:.2f}\n标准差 = {sigma:.2f}\n样本数 = {len(df)}'
plt.text(0.75, 0.95, stats_text, transform=plt.gca().transAxes,
         verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8),
         fontproperties=myfont)

plt.tight_layout()
plt.show()

# 2. 不同类型电影数量柱状图
plt.figure(figsize=(8, 4))
genre_series = df['genres'].dropna().str.split('/').explode()
genre_series = genre_series[genre_series.str.strip() != '']
genre_counts = genre_series.value_counts()

bars = plt.bar(genre_counts.index, genre_counts.values, color='#2ca02c')
plt.title('电影类型TOP', fontproperties=myfont)
plt.xlabel('电影类型', fontproperties=myfont)
plt.ylabel('数量', fontproperties=myfont)
plt.xticks(rotation=45, ha='right', fontproperties=myfont)

# 添加数值标签
for bar in bars:
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width() / 2., height,
             f'{height}', ha='center', va='bottom',
             fontproperties=myfont)

plt.tight_layout()
plt.show()

# 3. 评分与片长的关系散点图
plt.figure(figsize=(6, 4))
df['duration_min'] = df['duration'].str.extract('(\d+)').astype(float)

plt.scatter(df['duration_min'], df['score'], alpha=0.6,
            c='#9467bd', edgecolors='w', linewidth=0.5)

plt.title('电影时长与评分关系', fontproperties=myfont)
plt.xlabel('时长(分钟)', fontproperties=myfont)
plt.ylabel('评分', fontproperties=myfont)

# 添加回归线
from scipy.stats import linregress

mask = ~df['duration_min'].isna() & ~df['score'].isna()
slope, intercept, r_value, p_value, std_err = linregress(
    df['duration_min'][mask], df['score'][mask])
x = np.array([df['duration_min'].min(), df['duration_min'].max()])
plt.plot(x, intercept + slope * x, 'r--', label=f'R² = {r_value ** 2:.2f}')

plt.legend(prop=myfont)
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()

# 4. 多子图组合
fig, axs = plt.subplots(2, 2, figsize=(8, 6))

# 子图1: 评分直方图（更直观）
axs[0, 0].hist(df['score'].dropna(), bins=15, color='#1f77b4', edgecolor='white')
axs[0, 0].set_title('A. 评分分布（直方图）', fontproperties=myfont)
axs[0, 0].set_xlabel('评分', fontproperties=myfont)
axs[0, 0].set_ylabel('电影数量', fontproperties=myfont)
axs[0, 0].grid(axis='y', alpha=0.3)

# 子图2: 不同类型平均评分柱状图（更亲民）
genre_series = df['genres'].dropna().str.split('/').explode()
genre_series = genre_series[genre_series.str.strip() != '']
top_genres = genre_series.value_counts().index[:8]

avg_scores = [df[df['genres'].str.contains(g, na=False)]['score'].dropna().mean() for g in top_genres]
axs[0, 1].bar(top_genres, avg_scores, color='#ff7f0e')
for i, v in enumerate(avg_scores):
    axs[0, 1].text(i, v + 0.1, f'{v:.2f}', ha='center', fontproperties=myfont)
axs[0, 1].set_title('B. 不同类型平均评分', fontproperties=myfont)
axs[0, 1].set_ylabel('平均评分', fontproperties=myfont)
axs[0, 1].set_ylim(0, 10)  # ✨ 限定评分上限，更美观
for label in axs[0, 1].get_xticklabels():
    label.set_fontproperties(myfont)

# 子图3: 年度平均评分趋势（x轴年份旋转）
# 提取年份
df['year'] = df['release_date'].str.extract('(\d{4})')
# 计算年度平均评分，按年份排序
yearly_avg = df.groupby('year')['score'].mean().sort_index()
# 绘图
axs[1, 0].plot(yearly_avg.index, yearly_avg.values, marker='o')
axs[1, 0].set_title('C. 年度平均评分', fontproperties=myfont)
axs[1, 0].set_xlabel('年份', fontproperties=myfont)
axs[1, 0].set_ylabel('平均评分', fontproperties=myfont)
# ✨ 设置每隔N年显示一个年份刻度（自动根据年份数量确定）
years = yearly_avg.index.tolist()
step = max(len(years) // 10, 1)  # 最多10个标签
axs[1, 0].set_xticks(years[::step])
axs[1, 0].tick_params(axis='x', rotation=45)  # 斜着显示防止重叠

# 子图4: 制片国家分布
top_countries = df['country'].value_counts().index[:8]
country_counts = df['country'].value_counts().head(8)
axs[1, 1].pie(country_counts, labels=top_countries, autopct='%1.1f%%',
              textprops={'fontproperties': myfont})
axs[1, 1].set_title('D. 制片国家分布', fontproperties=myfont)

plt.tight_layout(pad=2.0)
plt.show()
