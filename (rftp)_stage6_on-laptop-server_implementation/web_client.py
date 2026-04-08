from socket import *
import os
import time
import hashlib

CHUNK_SIZE = 60000
SERVER_IP = "127.0.0.1"
SERVER_PORT = 12000

# This dictionary is how the Web UI talks to the background download thread
state = {
    "status": "idle",       # idle, downloading, paused, finished, error
    "progress": 0,          # 0 to 100
    "speed": 0.0,           # MB/s
    "completed_bytes": 0,
    "total_bytes": 0,
    "is_paused": False,
    "message": ""           # For UI notifications
}

def start_download(filename):
    global state
    
    # Reset state for a new download
    state["status"] = "downloading"
    state["is_paused"] = False
    state["message"] = "Connecting to server..."
    state["completed_bytes"] = 0
    state["total_bytes"] = 0
    state["progress"] = 0

    clientSocket = socket(AF_INET, SOCK_DGRAM)
    os.makedirs("downloads", exist_ok=True)
    filepath = os.path.join("downloads", "downloaded_" + filename)

    start_seq = 0
    bytes_received = 0

    # Auto-Resume logic for the web client
    if os.path.exists(filepath):
        bytes_received = os.path.getsize(filepath)
        start_seq = bytes_received // CHUNK_SIZE
        with open(filepath, "r+b") as f:
            f.truncate(start_seq * CHUNK_SIZE)
        bytes_received = start_seq * CHUNK_SIZE
        state["message"] = f"Resuming from packet {start_seq}..."

    # Initial Request
    request = f"GET {filename} {start_seq}"
    clientSocket.sendto(request.encode(), (SERVER_IP, SERVER_PORT))

    # Handshake
    packet, server_addr = clientSocket.recvfrom(CHUNK_SIZE + 100)
    if packet == b"ACCEPT":
        clientSocket.sendto(b"ACK_ACCEPT", server_addr)
        packet, server_addr = clientSocket.recvfrom(CHUNK_SIZE + 100)

    if packet.startswith(b"ERROR"):
        state["status"] = "error"
        state["message"] = packet.decode()
        clientSocket.close()
        return

    # Get Size
    filesize = 0
    if packet.startswith(b"SIZE"):
        filesize = int(packet.decode().split()[1])
        state["total_bytes"] = filesize
        packet, _ = clientSocket.recvfrom(CHUNK_SIZE + 100)

    file = open(filepath, "ab" if start_seq > 0 else "wb")
    start_time = time.time()
    expected_seq = start_seq

    # Main Loop
    while True:
        if packet == b"END":
            hash_packet, _ = clientSocket.recvfrom(2048)
            if hash_packet.startswith(b"HASH"):
                server_hash = hash_packet.decode().split()[1]
            break

        seq_str, data = packet.split(b"|", 1)
        seq = int(seq_str.decode())
        size = len(data)

        # Go-Back-N Logic
        if seq == expected_seq:
            if not state["is_paused"]:
                state["status"] = "downloading"
                file.write(data)
                bytes_received += size
                ack = f"ACK {expected_seq}"
                clientSocket.sendto(ack.encode(), server_addr)
                expected_seq += 1
            else:
                state["status"] = "paused"
                state["message"] = "Download paused..."
        else:
            if expected_seq > start_seq:
                last_good_ack = expected_seq - 1
                ack = f"ACK {last_good_ack}"
                clientSocket.sendto(ack.encode(), server_addr)

        # Update Web State
        state["completed_bytes"] = bytes_received
        if filesize > 0:
            state["progress"] = int((bytes_received / filesize) * 100)

        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            state["speed"] = (bytes_received / (1024 * 1024)) / elapsed_time

        packet, _ = clientSocket.recvfrom(CHUNK_SIZE + 100)

    file.close()
    clientSocket.close()

    # Integrity Check
    state["message"] = "Verifying file integrity..."
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            sha256.update(chunk)
            
    client_hash = sha256.hexdigest()

    if client_hash == server_hash:
        state["status"] = "finished"
        state["message"] = "Download Complete & Verified! ✔"
    else:
        state["status"] = "error"
        state["message"] = "Hash mismatch — File corrupted ❌"