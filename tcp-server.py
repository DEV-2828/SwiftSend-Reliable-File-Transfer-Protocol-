from socket import *
import os

SERVER_PORT = 12001
CHUNK_SIZE = 60000

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', SERVER_PORT))
serverSocket.listen(5)

print(f"TCP Server running on port {SERVER_PORT}")

def handle_client(conn, addr):
    print(f"Connected to {addr}")

    try:
        # Receive filename
        filename = conn.recv(1024).decode().strip()
        filepath = os.path.join("files", filename)

        if not os.path.exists(filepath):
            conn.sendall(b"ERROR: File not found")
            conn.close()
            return

        filesize = os.path.getsize(filepath)

        # Send file size first
        conn.sendall(f"SIZE {filesize}".encode())

        # Wait for ACK from client
        ack = conn.recv(1024)

        # Send file data
        with open(filepath, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                conn.sendall(chunk)

        print(f"Finished sending {filename} to {addr}")

    except Exception as e:
        print("Error:", e)

    finally:
        conn.close()


while True:
    conn, addr = serverSocket.accept()
    handle_client(conn, addr)