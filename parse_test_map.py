import json
from bs4 import BeautifulSoup
html = open('test_map.html', encoding='utf-8').read()
soup = BeautifulSoup(html, 'html.parser')
for script in soup.find_all('script'):
    if script.string and 'Plotly.newPlot' in script.string:
        s = script.string
        start = s.find('{"data":')
        if start != -1:
            end = s.rfind(',"layout"')
            if end != -1:
                data = json.loads(s[start:end] + '}')
                choro = data['data'][0]
                print('Locations:', choro.get('locations')[:3])
                print('Z:', choro.get('z')[:3])
                print('FeatureIdKey:', choro.get('featureidkey'))
                print('Colorscale:', choro.get('colorscale'))
