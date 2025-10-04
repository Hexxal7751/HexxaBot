from flask import Flask, render_template
from threading import Thread, Lock
import requests
import time
import os
from datetime import datetime, timezone

try:
    import discord
except ImportError:
    discord = None

app = Flask('', template_folder='templates')

start_time = datetime.now(timezone.utc)
telemetry = {
    "last_ping_latency_ms": None,
    "last_ping_at": None,
    "status": "Online",
    "discord_latency_ms": None
}
telemetry_lock = Lock()


def format_duration(delta: datetime):
    total_seconds = int(delta.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts[:4])


def build_metrics(now: datetime):
    uptime_delta = now - start_time
    uptime = format_duration(uptime_delta)

    with telemetry_lock:
        last_latency = telemetry.get("last_ping_latency_ms")
        last_ping_at = telemetry.get("last_ping_at")
        status = telemetry.get("status", "Online")
        discord_latency = telemetry.get("discord_latency_ms")

    metrics = [
        {
            "label": "uptime",
            "value": uptime,
            "meta": f"since {start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        }
    ]

    if last_latency is not None:
        latency_value = f"{last_latency:.0f} ms" if last_latency >= 1 else f"{last_latency:.2f} ms"
        latency_meta = "last successful self-ping"
        if last_ping_at:
            latency_meta += f" @ {last_ping_at.strftime('%H:%M:%S UTC')}"
        metrics.append({
            "label": "self-ping latency",
            "value": latency_value,
            "meta": latency_meta
        })

    if discord_latency is not None:
        discord_value = f"{discord_latency:.0f} ms" if discord_latency >= 1 else f"{discord_latency:.2f} ms"
        metrics.append({
            "label": "discord heartbeat",
            "value": discord_value,
            "meta": "gateway latency reported by Discord.py"
        })

    return status, metrics

@app.route('/')
def home():
    now = datetime.now(timezone.utc)
    status_text, metrics = build_metrics(now)

    description = (
        "HexxaBot V6 is serving live Discord traffic. This portal lists operational "
        "metrics sourced directly from the keep-alive heartbeat so you can monitor "
        "uptime and infrastructure responsiveness without guesswork."
    )

    return render_template(
        'status_index_root.html',
        status_text=status_text,
        description=description,
        metrics=metrics
    )

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
            start = time.perf_counter()
            response = requests.get(f"{app_url}/ping", timeout=30)
            elapsed_ms = (time.perf_counter() - start) * 1000

            with telemetry_lock:
                telemetry["last_ping_latency_ms"] = elapsed_ms
                telemetry["last_ping_at"] = datetime.now(timezone.utc)
                telemetry["status"] = "Online"

            print(f"[{datetime.now()}] Self-ping successful: {response.status_code} ({elapsed_ms:.2f} ms)")
        except Exception as e:
            with telemetry_lock:
                telemetry["status"] = f"Degraded: {type(e).__name__}"
            print(f"[{datetime.now()}] Self-ping failed: {str(e)}")
        finally:
            time.sleep(600)

def supabase_keepalive(supabase):
    """Keep Supabase connection alive with periodic queries"""
    while True:
        try:
            time.sleep(900)  # Wait 15 minutes
            supabase.table('economy').select('user_id').limit(1).execute()
            print(f"[{datetime.now()}] Supabase keepalive successful")
        except Exception as e:
            print(f"[{datetime.now()}] Supabase keepalive failed: {str(e)}")

def keep_alive(*args, supabase=None, bot: "discord.Client" = None):
    # Backward compatibility for positional arguments (supabase, bot)
    if supabase is None and len(args) >= 1:
        supabase = args[0]
    if bot is None and len(args) >= 2:
        bot = args[1]
    # Start Flask server
    Thread(target=run).start()

    # Start self-ping to prevent sleeping
    Thread(target=self_ping, daemon=True).start()

    # Start Supabase keepalive if provided
    if supabase:
        Thread(target=supabase_keepalive, args=(supabase,), daemon=True).start()

    if bot and discord is not None:
        def update_discord_latency():
            while True:
                try:
                    latency_seconds = bot.latency
                    if latency_seconds is not None:
                        with telemetry_lock:
                            telemetry["discord_latency_ms"] = latency_seconds * 1000
                except Exception:
                    pass
                time.sleep(15)

        Thread(target=update_discord_latency, daemon=True).start()

    print("Keep-alive system started: Flask server + self-ping + Supabase keepalive")
