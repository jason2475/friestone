#!/usr/bin/env python3
"""
Adapter skeleton: take a JSON list of scraped markets and insert into polymarket signals DB idempotently.
Usage: adapter_polymarket.py /path/to/scraped.json
Expected input: list of objects with keys: id (optional), question, market_price, claude_prob, direction, score
This script will insert rows into ~/.openclaw/agents/polymarket/data/signals.db table `signals`.
"""
import sqlite3, json, sys, os
from datetime import datetime

POLY_DB = os.path.expanduser('~/.openclaw/agents/polymarket/data/signals.db')

SCHEMA_SQL = '''
CREATE TABLE IF NOT EXISTS signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    market_price REAL,
    claude_prob REAL,
    direction TEXT,
    score REAL,
    sent INTEGER DEFAULT 0,
    raw_json TEXT
)
'''


def ensure_db():
    os.makedirs(os.path.dirname(POLY_DB), exist_ok=True)
    conn = sqlite3.connect(POLY_DB)
    conn.execute(SCHEMA_SQL)
    conn.commit()
    conn.close()


def insert_items(items):
    conn = sqlite3.connect(POLY_DB)
    cur = conn.cursor()
    # get existing columns
    cur.execute("PRAGMA table_info(signals)")
    cols=[r[1] for r in cur.fetchall()]

    for it in items:
        question = it.get('question')
        if not question:
            continue
        # idempotence by question + direction + market_price (only use columns that exist)
        checks = ['question']
        params = [question]
        conds = ['question = ?']
        if 'direction' in cols:
            conds.append('direction = ?'); params.append(it.get('direction'))
        if 'market_price' in cols:
            conds.append('market_price = ?'); params.append(it.get('market_price'))
        sql_check = 'SELECT id FROM signals WHERE ' + ' AND '.join(conds)
        cur.execute(sql_check, tuple(params))
        if cur.fetchone():
            # already present
            continue
        # build insert with available columns
        insert_cols=[]
        insert_vals=[]
        if 'ts' in cols:
            insert_cols.append('ts'); insert_vals.append(datetime.now().isoformat())
        if 'market_id' in cols and it.get('market_id') is not None:
            insert_cols.append('market_id'); insert_vals.append(it.get('market_id'))
        if 'question' in cols:
            insert_cols.append('question'); insert_vals.append(question)
        if 'market_price' in cols:
            insert_cols.append('market_price'); insert_vals.append(it.get('market_price'))
        if 'claude_prob' in cols:
            insert_cols.append('claude_prob'); insert_vals.append(it.get('claude_prob'))
        if 'deviation' in cols and it.get('deviation') is not None:
            insert_cols.append('deviation'); insert_vals.append(it.get('deviation'))
        if 'score' in cols:
            insert_cols.append('score'); insert_vals.append(it.get('score'))
        if 'direction' in cols:
            insert_cols.append('direction'); insert_vals.append(it.get('direction'))
        # put whole raw as reasoning if available
        if 'reasoning' in cols:
            insert_cols.append('reasoning'); insert_vals.append(json.dumps(it))
        # sent default 0 handled by DB default, but include if present
        if 'sent' in cols and 'sent' not in insert_cols:
            # do not add sent explicitly; rely on default
            pass
        # build SQL
        cols_sql = ','.join(insert_cols)
        qmarks = ','.join(['?']*len(insert_vals))
        sql = f'INSERT INTO signals ({cols_sql}) VALUES ({qmarks})'
        cur.execute(sql, tuple(insert_vals))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: adapter_polymarket.py /path/to/scraped.json')
        sys.exit(1)
    path = sys.argv[1]
    with open(path,'r',encoding='utf-8') as f:
        data=json.load(f)
    ensure_db()
    insert_items(data)
    print('Inserted items from', path)
