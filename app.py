from flask import Flask, jsonify
from flask_cors import CORS
import requests
from datetime import datetime

app = Flask(__name__)
CORS(app)

WP_API = "https://steve-pierce.de/wp-json/tribe/events/v1/events"

def lade_partys():
    partys = []
    try:
        # WordPress The Events Calendar REST API
        params = {
            'per_page': 50,
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'publish'
        }
        r = requests.get(WP_API, params=params, timeout=15, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        r.raise_for_status()
        data = r.json()
        events = data.get('events', [])

        for e in events:
            # Datum parsen
            start = e.get('start_date', '')  # z.B. "2026-06-26 12:00:00"
            if not start:
                continue
            dt = datetime.strptime(start[:10], '%Y-%m-%d')
            tag = ['MO','DI','MI','DO','FR','SA','SO'][dt.weekday()]
            datum = dt.strftime('%d.%m.%Y')
            uhr = start[11:16] if len(start) > 10 else '12:00'

            # Titel = Ort (z.B. "Piercingparty 49808 Lingen")
            titel = e.get('title', '')
            # PLZ aus Titel oder Venue
            venue = e.get('venue', {})
            ort = ''
            plz = ''
            if venue:
                plz = venue.get('zip', '')
                city = venue.get('city', '')
                ort = (plz + ' ' + city).strip()
            if not ort:
                ort = titel

            # Atlantomed aus Beschreibung
            desc = e.get('description', '') + e.get('excerpt', '')
            atl = 'atlantomed' in desc.lower()

            # E-Mail aus Beschreibung (z.B. lingen@steve-pierce.de)
            import re
            email_m = re.search(r'[\w.-]+@steve-pierce\.de', desc)
            email = email_m.group(0) if email_m else ''

            partys.append({
                'tag': tag,
                'datum': datum,
                'datum_iso': dt.strftime('%Y-%m-%d'),
                'uhrzeit': uhr,
                'name': titel,
                'ort': ort,
                'plz': plz,
                'atlantomed': atl,
                'email': email,
                'url': e.get('url', '')
            })

    except Exception as ex:
        print(f'API Fehler: {ex}')
        return [], str(ex)

    return partys, None

@app.route('/')
def index():
    return jsonify({'status': 'ok', 'service': 'Piercingparty Tour-Planer Server v2'})

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/partys')
def get_partys():
    partys, fehler = lade_partys()
    if fehler:
        return jsonify({'status': 'error', 'fehler': fehler, 'partys': [], 'anzahl': 0})
    return jsonify({
        'status': 'ok',
        'anzahl': len(partys),
        'partys': partys
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
