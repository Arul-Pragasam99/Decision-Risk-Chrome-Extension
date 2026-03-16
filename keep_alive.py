"""keep_alive.py — Pings Render server every 10 mins to prevent sleep."""

import urllib.request
import threading
import time

RENDER_URL = 'https://decisionrisk-server.onrender.com/ping'

def ping_server():
    while True:
        try:
            urllib.request.urlopen(RENDER_URL, timeout=10)
            print('Pinged server — awake')
        except Exception as e:
            print(f'Ping failed: {e}')
        time.sleep(600)

def start_keep_alive():
    thread = threading.Thread(target=ping_server, daemon=True)
    thread.start()