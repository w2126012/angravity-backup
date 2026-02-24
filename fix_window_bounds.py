#!/usr/bin/env python3
"""批量注释main.py中所有window_bounds引用"""

import re

# 读取文件
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 计数器
count = 0

# 匹配并注释所有包含window_bounds的行 (不包括已经注释的)
lines = content.split('\n')
new_lines = []

for line in lines:
    # 如果包含window_bounds且不是注释行
    if 'window_bounds' in line and not line.strip().startswith('#'):
        # 在行首添加注释
        indent = len(line) - len(line.lstrip())
        new_line = ' ' * indent + '# ' + line.lstrip()
        new_lines.append(new_line)
        count += 1
        print(f"注释第{len(new_lines)}行: {line.strip()[:60]}...")
    else:
        new_lines.append(line)

# 写回文件
with open('main.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"\n✓ 完成!总共注释了 {count} 行包含window_bounds的代码")
