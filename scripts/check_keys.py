import json

with open('C:/Users/e.cetin/Desktop/e_cuzdan_v15/database/decrypted_backup.json', 'r', encoding='utf-8') as f:
    d = json.load(f)
print(list(d.keys()))
