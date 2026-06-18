import json
html = open('test2.html', encoding='utf-8').read()
import re
match = re.search(r'\"data\":\[({.*})\]\,\"layout\"', html)
if match:
    data_str = match.group(1)
    # Just print the first 200 chars or find 'colorscale'
    idx = data_str.find('"colorscale"')
    print(data_str[idx:idx+200])
