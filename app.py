from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import serial
import threading
import time

app = Flask(__name__)
CORS(app)

state = {
    "temperature": None,
    "humidity": None,
    "led": "OFF",
    "messages": [""] * 10
}

ser = None

def connect_serial():
    global ser
    while True:
        try:
            ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
            print("Serial conectat!")
            time.sleep(2)
            ser.write(b'R')
            break
        except Exception as e:
            print(f"Eroare serial: {e}, reîncerc în 3s...")
            time.sleep(3)

def read_serial():
    global state
    while True:
        try:
            if ser and ser.is_open:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line.startswith("TEMP:"):
                        state["temperature"] = line.split(":")[1]
                    elif line.startswith("HUM:"):
                        state["humidity"] = line.split(":")[1]
                    elif line.startswith("LED_STATE:"):
                        state["led"] = line.split(":")[1]
                    elif line.startswith("MSG:"):
                        parts = line.split(":", 2)
                        if len(parts) >= 3:
                            idx = int(parts[1])
                            msg_text = parts[2]
                            state["messages"][idx] = msg_text
                else:
                    time.sleep(0.01)
        except Exception:
            time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def status():
    return jsonify(state)

@app.route('/api/led', methods=['POST'])
def control_led():
    data = request.get_json()
    cmd = 'A' if data.get('state') == 'on' else 'S'
    try:
        ser.write(cmd.encode())
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route('/api/message', methods=['POST'])
def send_message():
    data = request.get_json()
    msg = data.get('text', '')[:19]
    try:
        ser.write(f"M{msg}\n".encode())
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == '__main__':
    connect_serial()
    thread_read = threading.Thread(target=read_serial, daemon=True)
    thread_read.start()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)