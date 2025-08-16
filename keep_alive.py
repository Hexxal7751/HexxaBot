from flask import Flask, render_template
from threading import Thread

app = Flask('', template_folder='templates')

@app.route('/')
def home():
    return render_template('status_index_root.html')

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()
