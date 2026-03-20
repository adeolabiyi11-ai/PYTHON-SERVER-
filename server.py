from flask import Flask, request, jsonify
import time

app = Flask(__name__)

# ========================
# CONFIG
# ========================
API_KEY = "mysecret123"

# ========================
# DATA STORAGE
# ========================
latest_data = {}
pending_command = "NONE"

zone_history = []
time_history = []

last_heartbeat = 0

# ✅ NEW TRACKING
last_command_sent = "NONE"
last_command_time = 0
command_fetched = True

last_data_received_time = 0

# ========================
# SECURITY
# ========================
def authenticate(req):
    key = req.headers.get("x-api-key")
    return key == API_KEY

# ========================
# AI FUNCTIONS
# ========================
def rain_ai(temp, hum):
    score = (hum * 0.7) + (temp * 0.3)

    if score > 80:
        return "HIGH CHANCE OF RAIN"
    elif score > 65:
        return "POSSIBLE RAIN"
    return "LOW"

def intruder_speed():
    if len(time_history) < 2:
        return "UNKNOWN"

    diff = time_history[-1] - time_history[-2]

    if diff < 2000:
        return "FAST"
    elif diff < 5000:
        return "NORMAL"
    return "SLOW"

# ========================
# BASIC ROUTES
# ========================
@app.route("/")
def home():
    return jsonify({"message": "API Running"})

@app.route("/ping")
def ping():
    return jsonify({"status": "alive"})

# ========================
# HEARTBEAT
# ========================
@app.route("/heartbeat", methods=["GET", "POST"])
def heartbeat():
    global last_heartbeat

    if request.method == "POST":
        if not authenticate(request):
            return jsonify({"error": "Unauthorized"}), 401

    last_heartbeat = time.time()
    return jsonify({"status": "OK"})

@app.route("/device_status")
def device_status():
    if time.time() - last_heartbeat < 20:
        return jsonify({"device": "ONLINE"})
    return jsonify({"device": "OFFLINE"})

# ========================
# SENSOR DATA
# ========================
@app.route("/arduino/data", methods=["GET", "POST"])
def receive():
    global latest_data, last_data_received_time

    try:
        if request.method == "POST":
            if not authenticate(request):
                return jsonify({"error": "Unauthorized"}), 401

            data = request.json
            zone = data["zone"]
            temp = float(data["temp"])
            hum = float(data["hum"])
            door = data["door"]
            t = int(data["time"])

        else:
            zone = request.args.get("zone")
            temp = float(request.args.get("temp"))
            hum = float(request.args.get("hum"))
            door = request.args.get("door")
            t = int(request.args.get("time"))

    except (TypeError, ValueError, KeyError):
        return jsonify({"error": "Invalid input"}), 400

    zone_history.append(zone)
    time_history.append(t)

    if len(zone_history) > 10:
        zone_history.pop(0)
        time_history.pop(0)

    rain = rain_ai(temp, hum)
    speed = intruder_speed()

    latest_data = {
        "zone": zone,
        "temperature": temp,
        "humidity": hum,
        "door": door,
        "rain_prediction": rain,
        "intruder_speed": speed,
        "timestamp": t
    }

    # ✅ Track last data received
    last_data_received_time = time.time()

    return jsonify({"status": "received"})

# ========================
# GET SENSOR DATA
# ========================
@app.route("/sensor_data")
def sensor_data():
    return jsonify(latest_data)

# ========================
# COMMAND SYSTEM
# ========================
@app.route("/send_command", methods=["POST"])
def send_command():
    global pending_command, last_command_sent, last_command_time, command_fetched

    if not authenticate(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    if not data or "command" not in data:
        return jsonify({"error": "Missing command"}), 400

    pending_command = data["command"]

    # ✅ Track command
    last_command_sent = pending_command
    last_command_time = time.time()
    command_fetched = False

    return jsonify({
        "stored": True,
        "command": pending_command
    })

@app.route("/arduino/get_command", methods=["GET"])
def get_command():
    global pending_command, command_fetched

    cmd = pending_command
    pending_command = "NONE"

    # ✅ Mark as fetched
    if cmd != "NONE":
        command_fetched = True

    return jsonify({"command": cmd})

# ========================
# 🔥 NEW STATUS ENDPOINT (IMPORTANT)
# ========================
@app.route("/system_status")
def system_status():
    return jsonify({
        "device_status": "ONLINE" if time.time() - last_heartbeat < 20 else "OFFLINE",

        "last_command": {
            "command": last_command_sent,
            "sent_at": last_command_time,
            "fetched_by_arduino": command_fetched
        },

        "last_data_received": {
            "time": last_data_received_time,
            "data": latest_data
        }
    })

# ========================
# RUN
# ========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
