import csv
import sqlite3
import requests
from io import StringIO
from config import DATABASE_PATH, OURAIRPORTS_URLS, HTTP_HEADERS

update_status = {'in_progress': False, 'message': '', 'progress': 0}


def download_database():
    global update_status
    update_status = {'in_progress': True, 'progress': 5, 'message': 'Downloading airports...'}
    try:
        r = requests.get(OURAIRPORTS_URLS['airports'], timeout=300, headers=HTTP_HEADERS)
        conn = sqlite3.connect(DATABASE_PATH)
        c = conn.cursor()
        c.execute('DELETE FROM airports')
        c.execute('DELETE FROM runways')
        c.execute('DELETE FROM navaids')

        update_status['progress'] = 20
        cnt = 0
        for row in csv.DictReader(StringIO(r.content.decode('utf-8'))):
            icao = row.get('ident', '').upper()
            if row.get('iso_country') in ['US'] and len(icao) >= 3:
                try:
                    c.execute('INSERT OR REPLACE INTO airports VALUES (?,?,?,?,?,?,?)',
                              (icao, row.get('name', ''), row.get('municipality', ''),
                               row.get('iso_region', '')[-2:] if row.get('iso_region') else '',
                               float(row.get('latitude_deg', 0) or 0),
                               float(row.get('longitude_deg', 0) or 0),
                               int(float(row.get('elevation_ft', 0) or 0))))
                    cnt += 1
                except Exception:
                    pass
        conn.commit()

        update_status['message'] = 'Downloading runways...'
        update_status['progress'] = 40
        r = requests.get(OURAIRPORTS_URLS['runways'], timeout=300, headers=HTTP_HEADERS)

        c.execute('SELECT icao FROM airports')
        apts = set(x[0] for x in c.fetchall())
        rcnt = 0
        for row in csv.DictReader(StringIO(r.content.decode('utf-8'))):
            apt = row.get('airport_ident', '').upper()
            if apt in apts and row.get('le_ident'):
                try:
                    c.execute('INSERT INTO runways (airport_icao, runway_id, length, surface) VALUES (?,?,?,?)',
                              (apt, row.get('le_ident', ''),
                               int(float(row.get('length_ft', 0) or 0)),
                               row.get('surface', '')))
                    rcnt += 1
                except Exception:
                    pass
        conn.commit()

        update_status['message'] = 'Downloading navaids...'
        update_status['progress'] = 70
        r = requests.get(OURAIRPORTS_URLS['navaids'], timeout=300, headers=HTTP_HEADERS)

        ncnt = 0
        for row in csv.DictReader(StringIO(r.content.decode('utf-8'))):
            nid = row.get('ident', '').upper()
            if row.get('iso_country') in ['US'] and nid:
                try:
                    c.execute('INSERT OR REPLACE INTO navaids VALUES (?,?,?,?,?)',
                              (nid, row.get('name', ''), row.get('type', ''),
                               float(row.get('latitude_deg', 0) or 0),
                               float(row.get('longitude_deg', 0) or 0)))
                    ncnt += 1
                except Exception:
                    pass
        conn.commit()
        conn.close()

        update_status['message'] = f'Done! {cnt} airports, {rcnt} runways, {ncnt} navaids'
        update_status['progress'] = 100
    except Exception as e:
        update_status['message'] = f'Error: {e}'
    finally:
        update_status['in_progress'] = False
