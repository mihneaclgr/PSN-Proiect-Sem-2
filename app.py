from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

state = {
    "temperature": "--",
    "humidity": "--",
    "led": "OFF",
    "messages": [""] * 10,
    "floods": [0] * 10,
    "pending_commands": []
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/status')
def status():
    return jsonify(state)


@app.route('/api/update', methods=['POST'])
def update_from_local():
    global state
    data = request.get_json()
    if data and "state" in data:
        for key in data["state"]:
            state[key] = data["state"][key]

    cmds = state["pending_commands"].copy()
    state["pending_commands"].clear()
    return jsonify({"commands": cmds})


@app.route('/api/led', methods=['POST'])
def control_led():
    cmd = 'A' if request.get_json().get('state') == 'on' else 'S'
    state["pending_commands"].append(cmd)
    return jsonify({"ok": True})


@app.route('/api/message', methods=['POST'])
def send_message():
    msg = request.get_json().get('text', '')[:19]
    state["pending_commands"].append(f"M{msg}\n")
    return jsonify({"ok": True})


@app.route('/api/flood/<int:id>', methods=['POST'])
def delete_flood(id):
    state["pending_commands"].append(f"D{id}\n")
    return jsonify({"ok": True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)