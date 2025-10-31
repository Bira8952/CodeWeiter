#!/usr/bin/env python3
from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
import os
import csv
import requests
import subprocess
import json
from io import StringIO
import time
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

app = Flask(__name__, static_folder='.')
CORS(app)

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("⚠️ WARNING: DATABASE_URL not set - database features will be disabled")

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")
    conn = psycopg2.connect(DATABASE_URL)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# Google Sheets Config - Aus Umgebungsvariablen laden (sicher für GitHub!)
GOOGLE_SHEETS_ID = os.getenv("POOL_CONFIG_SHEET_ID", "14e85oqQrUjywXjNasJz7azME0t18RJEEldgRwCRFiH4")
LIVE_VOL_SHEET_ID = os.getenv("LIVE_VOL_SHEET_ID", "1EhhG5Da2kDpLMktcrSdn1DTMnr_XLEdJyNUI2ZwLuQ4")
LIVEVOL_SHEET_GID = "0"  # Erster Tab für Live-Vol Daten
POOLS_CONFIG_SHEET_GID = "0"  # Pool-Konfiguration Tab
MITARBEITER_SHEET_ID = os.getenv("MITARBEITER_SHEET_ID", "15yfflPhE6Lqykm8aqacnZcrJj0x0Y1Yd")

def fetch_google_sheet_csv(sheet_id, gid="0", max_retries=3):
    """Lädt Google Sheet als CSV mit Retry-Logik"""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                print(f"❌ Google Sheet nicht öffentlich zugänglich (400 Bad Request)")
                print(f"   URL: {url}")
                print(f"   Bitte Sheet öffentlich teilen (Lesezugriff)")
                return None
            elif e.response.status_code == 429:
                # Rate Limit erreicht
                wait_time = (2 ** attempt) * 0.5  # Exponential backoff: 0.5s, 1s, 2s
                print(f"⚠️ Rate Limit erreicht, warte {wait_time}s (Versuch {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ HTTP Error {e.response.status_code}: {e}")
                return None
        except requests.exceptions.Timeout:
            wait_time = (2 ** attempt) * 0.5
            print(f"⚠️ Timeout, wiederhole in {wait_time}s (Versuch {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
            continue
        except Exception as e:
            print(f"❌ Fehler beim Laden von Google Sheets: {e}")
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 0.5
                print(f"   Wiederhole in {wait_time}s...")
                time.sleep(wait_time)
            else:
                return None
    
    print(f"❌ Alle {max_retries} Versuche fehlgeschlagen")
    return None

def get_default_pools():
    """Gibt Standard-Pools zurück (Fallback wenn Google Sheets nicht erreichbar)"""
    return [
        {"name": "FR bis 08:45", "start": "06:00", "deadline": "08:45", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "DE bis 10:00", "start": "06:00", "deadline": "10:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "EMS bis 13:30 und 17:00", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "Luftverkehr bis 16:00", "start": "06:00", "deadline": "16:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "Endpunkt bis 17:00", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "Kleinwaren MUE ab 11:00", "start": "06:00", "deadline": "11:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "NL bis 11:00", "start": "06:00", "deadline": "11:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "DK+NO+SE+CZ+LU+HU+IS bis 11:00", "start": "06:00", "deadline": "11:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "JP+AU+HK+TH+CA+US+IT", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "ROTATION"},
        {"name": "CH Retouren bis 17:00", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "WA Pakete bis 13:00", "start": "06:00", "deadline": "13:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "WA Kleinwaren MUE bis 11:00", "start": "06:00", "deadline": "11:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "BE+GB bis 15:00", "start": "06:00", "deadline": "15:00", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "AT bis 16:30", "start": "06:00", "deadline": "16:30", "factor": 1, "rate": 80, "schicht": "FRÜH"},
        {"name": "EMK PRA BackOffice1", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "ROTATION"},
        {"name": "AVIS PRA BackOffice1", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "ROTATION"},
        {"name": "ZB Pakete Restbestand", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "ROTATION"},
        {"name": "ZB Pakete heute", "start": "06:00", "deadline": "17:00", "factor": 1, "rate": 80, "schicht": "ROTATION"},
    ]

def parse_pools_from_csv(csv_text):
    """
    Parst Pool-Konfiguration aus CSV
    
    Erwartetes Format (mit Header-Zeile):
    NAME,START,DEADLINE,FAKTOR,RATE,ROTATION
    FR bis 08:45,06:00,08:45,1,80,NEIN
    DE bis 10:00,06:00,10:00,1,80,JA
    ...
    """
    pools = []
    
    if not csv_text:
        print("⚠️ Kein CSV-Text vorhanden, verwende Standard-Pools")
        return get_default_pools()
    
    try:
        csv_file = StringIO(csv_text)
        reader = csv.reader(csv_file)
        rows = list(reader)
        
        print(f"📋 CSV hat {len(rows)} Zeilen (inkl. Header)")
        
        if len(rows) < 2:
            print("⚠️ Zu wenige Zeilen in CSV, verwende Standard-Pools")
            return get_default_pools()
        
        # Erste Zeile ist Header
        header = [col.strip().upper() for col in rows[0]]
        print(f"📊 CSV Header: {header}")
        
        # Finde Spalten-Indizes
        try:
            name_idx = header.index('NAME')
            start_idx = header.index('START')
            deadline_idx = header.index('DEADLINE')
            factor_idx = header.index('FAKTOR')
            rate_idx = header.index('RATE')
            rotation_idx = header.index('ROTATION')
        except ValueError as e:
            print(f"⚠️ Fehlende Spalte in CSV: {e}, verwende Standard-Pools")
            print(f"   Gefundene Spalten: {header}")
            return get_default_pools()
        
        # Parse Pool-Daten (START bei rows[1] für erste Datenzeile)
        for i, row in enumerate(rows[1:], start=2):
            # Skip komplett leere Zeilen
            if not any(cell.strip() for cell in row):
                print(f"⚠️ Zeile {i}: Komplett leer, überspringe")
                continue
                
            if len(row) < max(name_idx, start_idx, deadline_idx, factor_idx, rate_idx, rotation_idx) + 1:
                print(f"⚠️ Zeile {i} hat zu wenige Spalten ({len(row)}), überspringe: {row}")
                continue
            
            try:
                name_value = row[name_idx].strip()
                
                # Skip Zeilen mit leerem Namen
                if not name_value:
                    print(f"⚠️ Zeile {i}: Name ist leer, überspringe")
                    continue
                
                rotation_value = row[rotation_idx].strip().upper()
                use_rotation = rotation_value == 'JA'
                
                pool = {
                    "name": name_value,
                    "start": row[start_idx].strip() or "06:00",
                    "deadline": row[deadline_idx].strip() or "17:00",
                    "factor": float(row[factor_idx].strip()) if row[factor_idx].strip() else 1,
                    "rate": int(row[rate_idx].strip()) if row[rate_idx].strip() else 80,
                    "useRotation": use_rotation
                }
                
                pools.append(pool)
                print(f"✓ Pool geladen: {pool['name']} (START: {pool['start']}, DEADLINE: {pool['deadline']}, ROTATION: {rotation_value})")
                
            except (ValueError, IndexError) as e:
                print(f"⚠️ Fehler beim Parsen von Zeile {i}: {e}")
                print(f"   Zeile Inhalt: {row}")
                continue
        
        if pools:
            print(f"✅ {len(pools)} Pools erfolgreich aus Google Sheets geladen")
            return pools
        else:
            print("⚠️ Keine gültigen Pools gefunden, verwende Standard-Pools")
            return get_default_pools()
            
    except Exception as e:
        print(f"❌ Fehler beim Parsen des CSV: {e}, verwende Standard-Pools")
        import traceback
        traceback.print_exc()
        return get_default_pools()

@app.route('/')
def index():
    response = make_response(send_from_directory('.', 'index.html'))
    # Disable caching for index.html to always get latest version
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/pools', methods=['GET'])
def get_pools():
    """Lädt Pool-Konfiguration aus PostgreSQL Datenbank"""
    try:
        print(f"📥 Lade Pool-Konfiguration aus Datenbank...")
        
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT name, start_time as start, deadline, factor, rate, use_rotation as "useRotation"
                    FROM pools
                    ORDER BY id
                """)
                pools = cur.fetchall()
        
        # Konvertiere zu Liste von Dicts (für JSON)
        pools_list = [dict(pool) for pool in pools]
        
        print(f"✅ {len(pools_list)} Pools aus Datenbank geladen")
        return jsonify(pools_list)
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Pools aus Datenbank: {e}")
        import traceback
        traceback.print_exc()
        # Fallback zu Standard-Pools
        return jsonify(get_default_pools())

@app.route('/api/pools/save', methods=['POST'])
@app.route('/api/pools/save-to-sheets', methods=['POST'])  # Backward compatibility
def save_pools():
    """Speichert Pool-Konfiguration in PostgreSQL Datenbank (ersetzt alle Pools)"""
    try:
        pools = request.get_json()
        
        if not pools or not isinstance(pools, list):
            return jsonify({"error": "Ungültige Pool-Daten"}), 400
        
        print(f"📝 Speichere {len(pools)} Pools in Datenbank (ersetzt alle)...")
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Sammle Pool-Namen aus der submitted Liste
                pool_names = [pool.get('name') for pool in pools if pool.get('name')]
                
                # Lösche alle Pools, die NICHT in der submitted Liste sind
                if pool_names:
                    placeholders = ','.join(['%s'] * len(pool_names))
                    cur.execute(f"""
                        DELETE FROM pools 
                        WHERE name NOT IN ({placeholders})
                    """, pool_names)
                    deleted_count = cur.rowcount
                    if deleted_count > 0:
                        print(f"🗑️ {deleted_count} Pools aus Datenbank gelöscht (nicht mehr in Liste)")
                else:
                    # Wenn keine Pools submitted, lösche alle
                    cur.execute("DELETE FROM pools")
                    print("🗑️ Alle Pools aus Datenbank gelöscht")
                
                # Füge/Update alle submitted Pools
                for pool in pools:
                    # UPDATE oder INSERT (UPSERT)
                    cur.execute("""
                        INSERT INTO pools (name, start_time, deadline, factor, rate, use_rotation, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (name) 
                        DO UPDATE SET 
                            start_time = EXCLUDED.start_time,
                            deadline = EXCLUDED.deadline,
                            factor = EXCLUDED.factor,
                            rate = EXCLUDED.rate,
                            use_rotation = EXCLUDED.use_rotation,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        pool.get('name'),
                        pool.get('start'),
                        pool.get('deadline'),
                        pool.get('factor', 1.0),
                        pool.get('rate', 80),
                        pool.get('useRotation', False)
                    ))
        
        print(f"✅ {len(pools)} Pools erfolgreich in Datenbank gespeichert")
        return jsonify({"success": True, "message": "Pools in Datenbank gespeichert"})
            
    except ValueError as ve:
        print(f"❌ Konfigurationsfehler: {ve}")
        return jsonify({"error": "DATABASE_URL nicht konfiguriert"}), 500
    except Exception as e:
        print(f"❌ Fehler beim Speichern in Datenbank: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/mitarbeiter/<date>', methods=['GET'])
def get_mitarbeiter(date):
    """Lädt Mitarbeiter-Daten für ein bestimmtes Datum aus PostgreSQL Datenbank"""
    try:
        # Prüfe zuerst die Datenbank
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT frueh as "maFrueh", spat as "maSpat", taeti as "maTäti"
                    FROM mitarbeiter
                    WHERE date = %s
                """, (date,))
                result = cur.fetchone()
        
        if result:
            data = dict(result)
            print(f"✅ Mitarbeiter für {date} aus Datenbank: FRÜH={data['maFrueh']}, SPÄT={data['maSpat']}, Täti={data['maTäti']}")
            return jsonify(data)
        
        # Fallback: Versuche aus Google Sheets zu laden
        print(f"📥 Lade Mitarbeiter-Daten für {date} aus Google Sheets...")
        
        csv_text = fetch_google_sheet_csv(MITARBEITER_SHEET_ID, gid="0")
        
        if not csv_text:
            print("⚠️ Mitarbeiter-Sheet nicht erreichbar, verwende 0/0/0")
            return jsonify({"maFrueh": 0, "maSpat": 0, "maTäti": 0})
        
        # Parse CSV
        csv_file = StringIO(csv_text)
        reader = csv.reader(csv_file)
        lines = list(reader)
        
        if len(lines) < 6:
            print("⚠️ Mitarbeiter-Sheet hat zu wenige Zeilen")
            return jsonify({"maFrueh": 0, "maSpat": 0, "maTäti": 0})
        
        # Finde die Spalte für das Datum
        date_parts = date.split('-')
        if len(date_parts) == 3:
            day = date_parts[2].lstrip('0')
            month = date_parts[1].lstrip('0')
            search_date = f"{day}.{month}."
        else:
            print(f"⚠️ Ungültiges Datumsformat: {date}")
            return jsonify({"maFrueh": 0, "maSpat": 0, "maTäti": 0})
        
        date_row = lines[3] if len(lines) > 3 else []
        col_index = -1
        
        for i, cell in enumerate(date_row):
            if search_date in str(cell):
                col_index = i
                break
        
        if col_index == -1:
            print(f"⚠️ Datum {search_date} nicht im Sheet gefunden")
            return jsonify({"maFrueh": 0, "maSpat": 0, "maTäti": 0})
        
        # Zähle Schichten
        count_frueh = 0
        count_spat = 0
        count_täti = 0
        
        for row_idx in range(4, len(lines)):
            row = lines[row_idx]
            mitarbeiter = row[0].strip() if len(row) > 0 else ""
            if not mitarbeiter:
                continue
            
            if col_index >= len(row):
                continue
                
            schicht_code = row[col_index].strip().upper()
            
            if not schicht_code or schicht_code == '-' or schicht_code == '':
                continue
            
            schicht_code = ''.join([c for c in schicht_code if not c.isdigit()]).strip()
            
            if schicht_code in ['FT', 'A', 'U', 'K', 'URD', 'KA']:
                continue
            
            if 'FRÜH' in schicht_code or 'FRUEH' in schicht_code:
                count_frueh += 1
            elif 'SPÄT' in schicht_code or 'SPAT' in schicht_code:
                count_spat += 1
            elif 'TÄTI' in schicht_code or schicht_code == 'ROT':
                count_täti += 1
        
        print(f"✅ Mitarbeiter für {date}: FRÜH={count_frueh}, SPÄT={count_spat}, Täti={count_täti}")
        
        return jsonify({
            "maFrueh": count_frueh,
            "maSpat": count_spat,
            "maTäti": count_täti
        })
        
    except Exception as e:
        print(f"❌ Fehler beim Laden der Mitarbeiter-Daten: {e}")
        return jsonify({"maFrueh": 0, "maSpat": 0, "maTäti": 0})

@app.route('/api/mitarbeiter/save', methods=['POST'])
def save_mitarbeiter():
    """Speichert Mitarbeiter-Daten in PostgreSQL Datenbank"""
    try:
        data = request.get_json()
        
        if not data or ('date' not in data and 'datum' not in data):
            return jsonify({"error": "Ungültige Daten"}), 400
        
        date = data.get('date') or data.get('datum')
        ma_frueh = data.get('maFrueh', 0)
        ma_spat = data.get('maSpat', 0)
        ma_täti = data.get('maTäti', 0)
        
        # Speichere in Datenbank (UPSERT)
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO mitarbeiter (date, frueh, spat, taeti, updated_at)
                    VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (date)
                    DO UPDATE SET
                        frueh = EXCLUDED.frueh,
                        spat = EXCLUDED.spat,
                        taeti = EXCLUDED.taeti,
                        updated_at = CURRENT_TIMESTAMP
                """, (date, ma_frueh, ma_spat, ma_täti))
        
        print(f"💾 Mitarbeiter in DB gespeichert für {date}: FRÜH={ma_frueh}, SPÄT={ma_spat}, Täti={ma_täti}")
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"❌ Fehler beim Speichern der Mitarbeiter-Daten: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# API-Endpunkt für Google Sheets Config (sicher für Frontend!)
@app.route('/api/config/sheets', methods=['GET'])
def get_sheets_config():
    """Liefert Google Sheets IDs sicher vom Backend"""
    return jsonify({
        "liveVolSheetId": LIVE_VOL_SHEET_ID,
        "poolConfigSheetId": GOOGLE_SHEETS_ID,
        "mitarbeiterSheetId": MITARBEITER_SHEET_ID
    })

# Pool-Daten werden aus Google Sheets gelesen
# Änderungen aus dem Web werden ins Google Sheet geschrieben (Web → Google Sheet)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
