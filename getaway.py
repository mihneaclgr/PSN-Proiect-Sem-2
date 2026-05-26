import serial
import time
import requests
import smtplib
from email.message import EmailMessage

# ÎNLOCUIEȘTE CU LINK-UL TĂU DIN AZURE (ex: https://nume-proiect.azurewebsites.net)
CLOUD_URL = "psn-dragan-calugar-fycvhrhqapewf8cc.uaenorth-01.azurewebsites.net"

state = {
    "temperature": "--",
    "humidity": "--",
    "led": "OFF",
    "messages": [""] * 10,
    "floods": [0] * 10
}


def send_email():
    try:
        msg = EmailMessage()
        msg.set_content("Sistemul a detectat o inundație!")
        msg['Subject'] = 'Alertă Inundație IoT'
        msg['From'] = "proiectpsnmihneasidarius@gmail.com"
        msg['To'] = "dariuscdragan66@gmail.com"
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login("proiectpsnmihneasidarius@gmail.com", "kneh drqf uegg tgqg")
        server.send_message(msg)
        server.quit()
        print("Email inundație trimis.")
    except Exception as e:
        print(f"Eroare email: {e}")


try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=0.1)
    time.sleep(2)
    ser.write(b'R')
except Exception as e:
    print(f"Eroare conectare serial: {e}")
    ser = None

while True:
    try:
        if ser and ser.is_open and ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("TEMP:"):
                state["temperature"] = line.split(":")[1]
            elif line.startswith("HUM:"):
                state["humidity"] = line.split(":")[1]
            elif line.startswith("LED_STATE:"):
                state["led"] = line.split(":")[1]
            elif line == "FLOOD_EVENT":
                send_email()
            elif line.startswith("MSG:"):
                parts = line.split(":", 2)
                if len(parts) >= 3: state["messages"][int(parts[1])] = parts[2]
            elif line.startswith("FLD:"):
                parts = line.split(":", 2)
                if len(parts) >= 3: state["floods"][int(parts[1])] = int(parts[2])

        #print(state)
        res = requests.post(CLOUD_URL, json={"state": state}, timeout=5)
        commands = res.json().get("commands", [])

        for cmd in commands:
            if ser and ser.is_open:
                if not cmd.endswith('\n'):
                    cmd += '\n'
                ser.write(cmd.encode('utf-8'))
                ser.flush()

        time.sleep(0.1)
    except Exception as e:
        time.sleep(1)