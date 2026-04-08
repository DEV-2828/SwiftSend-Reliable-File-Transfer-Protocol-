from flask import Flask, render_template, request, jsonify
import threading
import web_client  # Imports your new script

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    filename = data.get("filename")
    server_ip = data.get("ip")  # Grab the IP from the frontend
    
    # Start the download in a background thread so it doesn't block the web server
    # Now passing BOTH filename and server_ip
    thread = threading.Thread(target=web_client.start_download, args=(filename, server_ip))
    thread.start()
    return jsonify({"success": True})

@app.route("/pause", methods=["POST"])
def pause():
    web_client.state["is_paused"] = True
    return jsonify({"success": True})

@app.route("/resume", methods=["POST"])
def resume():
    web_client.state["is_paused"] = False
    return jsonify({"success": True})

@app.route("/status", methods=["GET"])
def status():
    # The frontend will constantly ping this endpoint to get the latest progress
    return jsonify(web_client.state)

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0") # host="0.0.0.0" allows network access to the web UI