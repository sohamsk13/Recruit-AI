import os

file_path = r'C:\Users\soham\AppData\Roaming\Python\Python313\site-packages\pymongo\common.py'

with open(file_path, 'r') as f:
    content = f.read()

content = content.replace('from bson import SON', 'from bson.son import SON')

with open(file_path, 'w') as f:
    f.write(content)

print("Fixed")