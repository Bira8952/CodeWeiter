#!/usr/bin/env python3
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import csv
import requests
import subprocess
import json
from io import StringIO

app = Flask(__name__, static_folder='.')
CORS(app)

# Google Sheets Config
GOOGLE_SHEETS_ID = "14e85oqQrUjywXjNasJz7azME0t18RJEEldgRwCRFiH4"
LIVEVOL_SHEET_GID = "0"  # Erster Tab für Live-Vol Daten
POOLS_CONFIG_SHEET_GID = "0"  # Pool-Konfiguration Tab (NAME, START, DEADLINE, FAKTOR, RATE, SCHICHT)

def fetch_google_sheet_csv(sheet_id, gid="0"):
    """Lädt Google Sheet als CSV"""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Fehler beim Laden von Google Sheets: {e}")
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
        
        if len(rows) < 2:
            print("⚠️ Zu wenige Zeilen in CSV, verwende Standard-Pools")
            return get_default_pools()
        
        # Erste Zeile ist Header
        header = [col.strip().upper() for col in rows[0]]
        
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
            return get_default_pools()
        
        # Parse Pool-Daten
        for i, row in enumerate(rows[1:], start=2):
            if len(row) < max(name_idx, start_idx, deadline_idx, factor_idx, rate_idx, rotation_idx) + 1:
                print(f"⚠️ Zeile {i} hat zu wenige Spalten, überspringe")
                continue
            
            try:
                rotation_value = row[rotation_idx].strip().upper()
                use_rotation = rotation_value == 'JA'
                
                pool = {
                    "name": row[name_idx].strip(),
                    "start": row[start_idx].strip(),
                    "deadline": row[deadline_idx].strip(),
                    "factor": float(row[factor_idx].strip()) if row[factor_idx].strip() else 1,
                    "rate": int(row[rate_idx].strip()) if row[rate_idx].strip() else 80,
                    "useRotation": use_rotation
                }
                
                # Validierung
                if not pool["name"]:
                    print(f"⚠️ Zeile {i}: Name ist leer, überspringe")
                    continue
                
                pools.append(pool)
                print(f"✓ Pool geladen: {pool['name']} (START: {pool['start']}, DEADLINE: {pool['deadline']}, ROTATION: {rotation_value})")
                
            except (ValueError, IndexError) as e:
                print(f"⚠️ Fehler beim Parsen von Zeile {i}: {e}, überspringe")
                continue
        
        if pools:
            print(f"✅ {len(pools)} Pools erfolgreich aus Google Sheets geladen")
            return pools
        else:
            print("⚠️ Keine gültigen Pools gefunden, verwende Standard-Pools")
            return get_default_pools()
            
    except Exception as e:
        print(f"❌ Fehler beim Parsen des CSV: {e}, verwende Standard-Pools")
        return get_default_pools()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/pools', methods=['GET'])
def get_pools():
    """Lädt Pool-Konfiguration aus Google Sheets (Tab 2)"""
    try:
        print(f"📥 Lade Pool-Konfiguration aus Google Sheets (GID={POOLS_CONFIG_SHEET_GID})...")
        
        # Lade CSV von Google Sheets (Tab 2 für Pool-Konfiguration)
        csv_text = fetch_google_sheet_csv(GOOGLE_SHEETS_ID, POOLS_CONFIG_SHEET_GID)
        
        # Parse Pools
        pools = parse_pools_from_csv(csv_text)
        
        print(f"✅ {len(pools)} Pools bereitgestellt")
        return jsonify(pools)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Pools: {e}")
        # Fallback zu Standard-Pools
        return jsonify(get_default_pools())

@app.route('/api/pools/save-to-sheets', methods=['POST'])
def save_pools_to_sheets():
    """Speichert Pool-Konfiguration ins Google Sheet (Web → Google Sheet)"""
    try:
        pools = request.get_json()
        
        if not pools or not isinstance(pools, list):
            return jsonify({"error": "Ungültige Pool-Daten"}), 400
        
        print(f"📝 Speichere {len(pools)} Pools ins Google Sheet...")
        
        # Konvertiere Pools zu JSON String
        pools_json = json.dumps(pools)
        
        # Rufe Node.js Script auf
        result = subprocess.run(
            ['node', 'writeToGoogleSheets.js', pools_json],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ Pools erfolgreich ins Google Sheet geschrieben")
            print(result.stdout)
            return jsonify({"success": True, "message": "Pools ins Google Sheet gespeichert"})
        else:
            print(f"❌ Fehler beim Schreiben ins Google Sheet: {result.stderr}")
            return jsonify({"error": result.stderr}), 500
            
    except subprocess.TimeoutExpired:
        print("❌ Timeout beim Schreiben ins Google Sheet")
        return jsonify({"error": "Timeout"}), 500
    except Exception as e:
        print(f"❌ Fehler beim Speichern ins Google Sheet: {e}")
        return jsonify({"error": str(e)}), 500

# Pool-Daten werden aus Google Sheets gelesen
# Änderungen aus dem Web werden ins Google Sheet geschrieben (Web → Google Sheet)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
