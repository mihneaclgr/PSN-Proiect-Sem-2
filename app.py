from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import serial
import threading
import time
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
CORS(app)

state = {
    "temperature": None,
    "humidity": None,
    "led": "OFF",
    "messages": [""] * 10,
    "floods": [0] * 10
}
ser = None

def send_email():
    try:
        msg = EmailMessage()
        msg.set_content("Sistemul a detectat o inundație!")
        msg['Subject'] = 'Alertă Inundație IoT'
        msg['From'] = "proiectpsnmihneasidarius@gmail.com"
        msg['To'] = "dariuscdragan66@gmail.com"

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        # ATENȚIE: Înlocuiește cu Parola de Aplicație Google, parola standard va da eroare.
        server.login("proiectpsnmihneasidarius@gmail.com", "voqu xplq emxm fdxx")
        server.send_message(msg)
        server.quit()
        print("Email trimis cu succes")
    except Exception as e:
        print(f"Eroare email: {e}")

def connect_serial():
    global ser
    while True:
        try:
            ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
            time.sleep(2)
            ser.write(b'R')
            break
        except Exception:
            time.sleep(3)

def read_serial():
    global state
    while True:
        try:
            if ser and ser.is_open and ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("TEMP:"): state["temperature"] = line.split(":")[1]
                elif line.startswith("HUM:"): state["humidity"] = line.split(":")[1]
                elif line.startswith("LED_STATE:"): state["led"] = line.split(":")[1]
                elif line == "FLOOD_EVENT":
                    send_email()
                elif line.startswith("MSG:"):
                    parts = line.split(":", 2)
                    if len(parts) >= 3: state["messages"][int(parts[1])] = parts[2]
                elif line.startswith("FLD:"):
                    parts = line.split(":", 2)
                    if len(parts) >= 3: state["floods"][int(parts[1])] = int(parts[2])
            else:
                time.sleep(0.01)
        except Exception:
            time.sleep(0.1)

@app.route('/')
def index(): return render_template('index.html')

@app.route('/api/status')
def status(): return jsonify(state)

@app.route('/api/led', methods=['POST'])
def control_led():
    cmd = 'A' if request.get_json().get('state') == 'on' else 'S'
    ser.write(cmd.encode())
    return jsonify({"ok": True})

@app.route('/api/message', methods=['POST'])
def send_message():
    msg = request.get_json().get('text', '')[:19]
    ser.write(f"M{msg}\n".encode())
    return jsonify({"ok": True})

@app.route('/api/flood/<int:id>', methods=['DELETE'])
def delete_flood(id):
    ser.write(f"D{id}\n".encode())
    return jsonify({"ok": True})

if __name__ == '__main__':
    connect_serial()
    threading.Thread(target=read_serial, daemon=True).start()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)