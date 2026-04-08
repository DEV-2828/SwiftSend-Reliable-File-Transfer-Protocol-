from flask import Flask, render_template, request, jsonify
import threading
import web_client  # Imports your new script
import os 


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    data = request.json
    filename = data.get("filename")
    
    # Start the download in a background thread so it doesn't block the web server
    thread = threading.Thread(target=web_client.start_download, args=(filename,))
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


@app.route("/files", methods=["GET"])
def list_files():
    # The folder where the server keeps the files
    files_dir = "files" 
    
    # Create the folder if it doesn't exist to prevent crashes
    if not os.path.exists(files_dir):
        os.makedirs(files_dir)
        
    # Get a list of all files in that directory
    available_files = [f for f in os.listdir(files_dir) if os.path.isfile(os.path.join(files_dir, f))]
    
    return jsonify({"files": available_files})

if __name__ == "__main__":
    app.run(debug=True, port=5000)