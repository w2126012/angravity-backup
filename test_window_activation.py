#!/usr/bin/env python3
"""测试窗口激活功能"""

import time
from utils.automation import AutomationController

bot = AutomationController()

print("测试企业微信窗口激活...")
print("-" * 60)

# 尝试激活企业微信
print("\n1. 尝试激活'企业微信'...")
result = bot.activate_window("企业微信")
print(f"   结果: {result}")
time.sleep(2)

# 尝试激活WeChat Work
print("\n2. 尝试激活'WeChat Work'...")
result = bot.activate_window("WeChat Work")
print(f"   结果: {result}")
time.sleep(2)

# 尝试激活WeCom
print("\n3. 尝试激活'WeCom'...")
result = bot.activate_window("WeCom")
print(f"   结果: {result}")
time.sleep(2)

# 列出所有运行的应用
print("\n4. 列出所有运行的应用...")
import subprocess
result = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of every application process'], 
                       capture_output=True, text=True)
print(f"   所有应用: {result.stdout}")

print("\n" + "-" * 60)
print("测试完成!")
