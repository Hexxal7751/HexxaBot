from flask import Flask, render_template
from threading import Thread
import requests
import time
import os
from datetime import datetime

app = Flask('', template_folder='templates')

@app.route('/')
def home():
    return render_template('status_index_root.html')

@app.route('/health')
def health():
    return {'status': 'alive', 'timestamp': datetime.now().isoformat()}

@app.route('/ping')
def ping():
    return 'pong'

def run():
    app.run(host='0.0.0.0', port=8080, debug=False)

def self_ping():
    """Ping the app every 10 minutes to prevent Render from sleeping"""
    app_url = os.getenv('RENDER_EXTERNAL_URL', 'http://localhost:8080')
    
    while True:
        try:
            time.sleep(600)  # Wait 10 minutes
            response = requests.get(f"{app_url}/ping", timeout=30)
            print(f"[{datetime.now()}] Self-ping successful: {response.status_code}")
        except Exception as e:
            print(f"[{datetime.now()}] Self-ping failed: {str(e)}")

def supabase_keepalive(supabase):
    """Keep Supabase connection alive with periodic queries"""
    while True:
        try:
            time.sleep(900)  # Wait 15 minutes
            # Simple query to keep connection alive
            supabase.table('economy').select('user_id').limit(1).execute()
            print(f"[{datetime.now()}] Supabase keepalive successful")
        except Exception as e:
            print(f"[{datetime.now()}] Supabase keepalive failed: {str(e)}")

def keep_alive(supabase=None):
    # Start Flask server
    Thread(target=run).start()
    
    # Start self-ping to prevent sleeping
    Thread(target=self_ping, daemon=True).start()
    
    # Start Supabase keepalive if provided
    if supabase:
        Thread(target=supabase_keepalive, args=(supabase,), daemon=True).start()
    
    print("Keep-alive system started: Flask server + self-ping + Supabase keepalive")
