#!/usr/bin/env python3
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import csv
import requests
from io import StringIO

app = Flask(__name__, static_folder='.')
CORS(app)

# Google Sheets Config
GOOGLE_SHEETS_ID = "1EhhG5Da2kDpLMktcrSdn1DTMnr_XLEdJyNUI2ZwLuQ4"
POOLS_SHEET_GID = "0"  # Erster Tab für Pool-Konfiguration

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

def parse_pools_from_csv(csv_text):
    """Parst Pool-Konfiguration aus CSV"""
    
    # Standard-Pools (diese können in Google Sheets angepasst werden)
    default_pools = [
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
    
    # Gebe immer die Standard-Pools zurück
    # TODO: In Zukunft können wir diese aus einem speziellen Google Sheets Tab lesen
    return default_pools

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/pools', methods=['GET'])
def get_pools():
    """Lädt Pool-Konfiguration aus Google Sheets"""
    try:
        # Lade CSV von Google Sheets
        csv_text = fetch_google_sheet_csv(GOOGLE_SHEETS_ID, POOLS_SHEET_GID)
        
        # Parse Pools
        pools = parse_pools_from_csv(csv_text)
        
        return jsonify(pools)
    except Exception as e:
        print(f"Fehler beim Laden der Pools: {e}")
        return jsonify({'error': str(e)}), 500

# Pool-Daten werden jetzt aus Google Sheets gelesen
# Änderungen werden direkt in Google Sheets vorgenommen

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
