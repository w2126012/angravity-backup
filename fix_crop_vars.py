#!/usr/bin/env python3
"""批量注释main.py中所有crop_x和chat_focus相关引用"""

# 读取文件
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 计数器
count = 0

# 匹配并注释所有包含crop_x或chat_focus的行 (不包括已经注释的)
lines = content.split('\n')
new_lines = []

for line in lines:
    # 如果包含crop_x或chat_focus且不是注释行
    if ('crop_x' in line or 'crop_y' in line or 'crop_w' in line or 'crop_h' in line or 'chat_focus' in line) and not line.strip().startswith('#'):
        # 在行首添加注释
        indent = len(line) - len(line.lstrip())
        new_line = ' ' * indent + '# ' + line.lstrip()
        new_lines.append(new_line)
        count += 1
        print(f"注释第{len(new_lines)}行: {line.strip()[:70]}...")
    else:
        new_lines.append(line)

# 写回文件
with open('main.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))

print(f"\n✓ 完成!总共注释了 {count} 行包含crop_x/chat_focus的代码")
