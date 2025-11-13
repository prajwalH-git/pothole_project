# app.py
import os
import sqlite3
import datetime
from flask import Flask, jsonify, request, send_from_directory, url_for, abort, redirect
from werkzeug.utils import secure_filename
import requests

# Config
DB = os.getenv("DB_FILE", "potholes_demo.db")
UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
ALLOWED_EXT = set(["png", "jpg", "jpeg", "gif"])
OWM_KEY = os.getenv("OWM_KEY")  # set in Render or .env for weather API

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

def get_conn():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    conn = get_conn()
    conn.execute('''
    CREATE TABLE IF NOT EXISTS potholes (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      title TEXT,
      description TEXT,
      lat REAL,
      lon REAL,
      photo_filename TEXT,
      reported_by TEXT,
      reported_at TEXT,
      city TEXT,
      severity INTEGER,
      status TEXT DEFAULT 'pending',
      assigned_official TEXT
    );
    ''')
    conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      username TEXT UNIQUE,
      password_hash TEXT,
      role TEXT
    );
    ''')
    conn.commit()
    conn.close()

init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXT

@app.route('/')
def root():
    return redirect('/user')

# Serve static pages
@app.route('/user')
def user_page():
    return send_from_directory('static', 'user.html')

@app.route('/admin')
def admin_page():
    return send_from_directory('static', 'admin.html')

@app.route('/superadmin')
def superadmin_page():
    return send_from_directory('static', 'superadmin.html')

# Serve uploaded images
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API: return all potholes as GeoJSON
@app.route('/api/potholes', methods=['GET'])
def api_potholes():
    conn = get_conn()
    rows = conn.execute('SELECT * FROM potholes').fetchall()
    conn.close()
    features = []
    for r in rows:
        features.append({
            "type": "Feature",
            "properties": {
                "id": r["id"],
                "title": r["title"],
                "description": r["description"],
                "reported_by": r["reported_by"],
                "reported_at": r["reported_at"],
                "status": r["status"],
                "assigned_official": r["assigned_official"],
                "photo": url_for('uploaded_file', filename=r["photo_filename"]) if r["photo_filename"] else None,
                "severity": r["severity"]
            },
            "geometry": {
                "type": "Point",
                "coordinates": [r["lon"], r["lat"]]
            }
        })
    return jsonify({"type":"FeatureCollection","features":features})

# API: Create a new pothole report (multipart form-data)
@app.route('/api/report', methods=['POST'])
def api_report():
    try:
        title = request.form.get('title') or 'Pothole report'
        description = request.form.get('description') or ''
        lat = float(request.form.get('lat'))
        lon = float(request.form.get('lon'))
        reported_by = request.form.get('reported_by') or 'anonymous'
        severity = int(request.form.get('severity') or 1)
        reported_at = datetime.datetime.utcnow().isoformat()

        photo_filename = None
        if 'photo' in request.files:
            f = request.files['photo']
            if f and f.filename and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                # make filename unique
                timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
                filename = f"{timestamp}_{filename}"
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                f.save(save_path)
                photo_filename = filename

        conn = get_conn()
        conn.execute('''
          INSERT INTO potholes (title,description,lat,lon,photo_filename,reported_by,reported_at,city,severity)
          VALUES (?,?,?,?,?,?,?,?,?)
        ''', (title, description, lat, lon, photo_filename, reported_by, reported_at, "Bengaluru", severity))
        conn.commit()
        conn.close()
        return jsonify({"status":"ok"})
    except Exception as e:
        return jsonify({"status":"error", "message": str(e)}), 400

# API: admin assigns official to a pothole
@app.route('/api/assign', methods=['POST'])
def api_assign():
    data = request.get_json()
    if not data or 'id' not in data or 'official' not in data:
        return jsonify({"status":"error", "message":"id and official required"}), 400
    pothole_id = int(data['id'])
    official = data['official']
    conn = get_conn()
    conn.execute('UPDATE potholes SET assigned_official=?, status="assigned" WHERE id=?', (official, pothole_id))
    conn.commit()
    conn.close()
    # Optionally: send notification to official or webhook
    return jsonify({"status":"assigned"})

# API: basic weather fetch (current)
@app.route('/api/weather', methods=['GET'])
def api_weather():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({"status":"error", "message":"lat and lon required"}), 400
    if not OWM_KEY:
        return jsonify({"status":"error", "message":"OWM_KEY not configured"}), 500
    url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely,hourly&units=metric&appid={OWM_KEY}"
    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        return jsonify({"status":"error", "message":"weather api error", "details": resp.text}), 500
    data = resp.json()
    # Basic risk inference
    risks = {"flood": False, "storm": False}
    for d in data.get("daily", []):
        precip = d.get("rain", 0) or 0
        wind = d.get("wind_speed", 0)
        if precip >= 50:
            risks["flood"] = True
        if wind >= 17:
            risks["storm"] = True
    return jsonify({"status":"ok", "data": data, "risks": risks})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
