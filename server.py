#!/usr/bin/env python3
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime, date
import json

app = Flask(__name__, static_folder='.')
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/api/pools', methods=['GET'])
def get_pools():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, start_time, deadline_time, hours, faktor, rate, schicht
            FROM pools
            ORDER BY id
        """)
        
        pools = []
        for row in cur.fetchall():
            start_time_str = None
            if row[2]:
                start_time_str = str(row[2])[:5]
            
            deadline_time_str = None
            if row[3]:
                deadline_time_str = str(row[3])[:5]
            
            pools.append({
                'id': row[0],
                'name': row[1],
                'start': start_time_str,
                'deadline': deadline_time_str,
                'hours': float(row[4]) if row[4] else 0,
                'factor': row[5],
                'rate': row[6],
                'schicht': row[7]
            })
        
        cur.close()
        conn.close()
        return jsonify(pools)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pools', methods=['POST'])
def create_or_update_pool():
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO pools (name, start_time, deadline_time, hours, faktor, rate, schicht)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (name) DO UPDATE SET
                start_time = EXCLUDED.start_time,
                deadline_time = EXCLUDED.deadline_time,
                hours = EXCLUDED.hours,
                faktor = EXCLUDED.faktor,
                rate = EXCLUDED.rate,
                schicht = EXCLUDED.schicht,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
        """, (
            data['name'],
            data.get('start_time'),
            data.get('deadline_time'),
            data.get('hours', 0),
            data.get('faktor', 1),
            data.get('rate', 80),
            data.get('schicht', 'FRÜH')
        ))
        
        pool_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'id': pool_id, 'message': 'Pool gespeichert'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pools/<int:pool_id>', methods=['PUT'])
def update_pool(pool_id):
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            UPDATE pools SET
                start_time = %s,
                deadline_time = %s,
                hours = %s,
                faktor = %s,
                rate = %s,
                schicht = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
        """, (
            data.get('start_time'),
            data.get('deadline_time'),
            data.get('hours'),
            data.get('faktor'),
            data.get('rate'),
            data.get('schicht'),
            pool_id
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Pool aktualisiert'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pools/import', methods=['POST'])
def import_pools():
    try:
        data = request.json
        pools = data.get('pools', [])
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        for pool in pools:
            cur.execute("""
                INSERT INTO pools (name, start_time, deadline_time, hours, faktor, rate, schicht)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (name) DO UPDATE SET
                    start_time = EXCLUDED.start_time,
                    deadline_time = EXCLUDED.deadline_time,
                    hours = EXCLUDED.hours,
                    faktor = EXCLUDED.faktor,
                    rate = EXCLUDED.rate,
                    schicht = EXCLUDED.schicht,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                pool['name'],
                pool.get('start_time'),
                pool.get('deadline_time'),
                pool.get('hours', 0),
                pool.get('faktor', 1),
                pool.get('rate', 80),
                pool.get('schicht', 'FRÜH')
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': f'{len(pools)} Pools importiert'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
