# main.py
import subprocess

# 运行第一个程序
subprocess.run(["python", "时光电影热映(mysql).py"])

# 运行第二个程序
print("第一个程序运行完毕，正在运行第二个程序...")
subprocess.run(["python", "时光电影追加(mysql).py"])