from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

def parse_seite(url):
    partys = []
    try:
        r = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        soup = BeautifulSoup(r.text, 'html.parser')
        text = soup.get_text('\n')
        zeilen = [z.strip() for z in text.split('\n') if z.strip()]

        i = 0
        while i < len(zeilen):
            z = zeilen[i]
            m = re.match(r'^(MO|DI|MI|DO|FR|SA|SO)\s+(\d{2}\.\d{2}\.\d{4})', z)
            if m:
                tag = m.group(1)
                datum = m.group(2)
                name = ''
                ort = ''
                uhr = '12:00'
                atl = False
                for j in range(i+1, min(i+10, len(zeilen))):
                    nz = zeilen[j]
                    if re.match(r'^(MO|DI|MI|DO|FR|SA|SO)\s+\d', nz):
                        break
                    if not name and len(nz) > 3 and not re.match(r'^\d', nz):
                        name = nz
                    pm = re.search(r'(\d{5})\s+(\S.{2,30})', nz)
                    if pm and not ort:
                        ort = pm.group(1) + ' ' + pm.group(2).strip()
                    um = re.search(r'(\d{1,2}:\d{2})', nz)
                    if um:
                        uhr = um.group(1)
                    if 'atlantomed' in nz.lower():
                        atl = True
                partys.append({
                    'tag': tag,
                    'datum': datum,
                    'name': name,
                    'ort': ort,
                    'uhrzeit': uhr,
                    'atlantomed': atl
                })
            i += 1
    except Exception as e:
        print(f'Fehler: {e}')
    return partys

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'Piercingparty Tour-Planer Server'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/partys')
def get_partys():
    seite1 = parse_seite('https://steve-pierce.de/piercingpartys/liste/')
    seite2 = parse_seite('https://steve-pierce.de/piercingpartys/liste/seite/2/')
    alle = seite1 + seite2
    return jsonify({
        'status': 'ok',
        'anzahl': len(alle),
        'partys': alle
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
