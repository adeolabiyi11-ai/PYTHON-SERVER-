from flask import Flask,request,jsonify
import time

app=Flask(__name__)

latest_data={}
pending_command="NONE"

zone_history=[]
time_history=[]
speed_prediction="UNKNOWN"

weather_history=[]

last_heartbeat=0

def rain_ai(temp,hum):

    score=(hum*0.7)+(temp*0.3)

    if score>80:
        return "HIGH CHANCE OF RAIN"

    elif score>65:
        return "POSSIBLE RAIN"

    else:
        return "LOW"

def intruder_speed():

    if len(time_history)<2:
        return "UNKNOWN"

    diff=time_history[-1]-time_history[-2]

    if diff<2000:
        return "FAST"

    elif diff<5000:
        return "NORMAL"

    else:
        return "SLOW"

@app.route("/ping")
def ping():
    return "Server Awake"

@app.route("/heartbeat")
def heartbeat():

    global last_heartbeat
    last_heartbeat=time.time()

    return "OK"

@app.route("/device_status")
def device_status():

    if time.time()-last_heartbeat<20:
        return jsonify({"device":"ONLINE"})
    else:
        return jsonify({"device":"OFFLINE"})

@app.route("/arduino/data")
def receive():

    global latest_data

    zone=request.args.get("zone")
    temp=float(request.args.get("temp"))
    hum=float(request.args.get("hum"))
    door=request.args.get("door")
    t=int(request.args.get("time"))

    zone_history.append(zone)
    time_history.append(t)

    if len(zone_history)>10:
        zone_history.pop(0)

    rain=rain_ai(temp,hum)
    speed=intruder_speed()

    latest_data={
    "zone":zone,
    "temperature":temp,
    "humidity":hum,
    "door":door,
    "rain_prediction":rain,
    "intruder_speed":speed,
    "timestamp":t
    }

    return jsonify({"status":"received"})

@app.route("/sensor_data")
def sensor_data():
    return jsonify(latest_data)

@app.route("/send_command",methods=["POST"])
def send_command():

    global pending_command

    data=request.json
    pending_command=data["command"]

    return jsonify({"stored":True})

@app.route("/arduino/get_command")
def get_command():

    global pending_command

    cmd=pending_command
    pending_command="NONE"

    return jsonify({"command":cmd})

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)
