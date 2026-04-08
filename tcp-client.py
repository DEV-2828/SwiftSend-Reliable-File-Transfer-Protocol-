from socket import *
import os
import time

SERVER_IP = "127.0.0.1"
SERVER_PORT = 12001
CHUNK_SIZE = 60000

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((SERVER_IP, SERVER_PORT))

filename = input("Enter file name: ")

# Send filename request
clientSocket.send(filename.encode())

# Receive response (SIZE or ERROR)
response = clientSocket.recv(1024)

if response.startswith(b"ERROR"):
    print(response.decode())
    clientSocket.close()
    exit()

# Get file size
if response.startswith(b"SIZE"):
    filesize = int(response.decode().split()[1])
    print(f"File size: {filesize} bytes")

# Send ACK to start transfer
clientSocket.send(b"OK")

os.makedirs("downloads", exist_ok=True)
filepath = os.path.join("downloads", "tcp_" + filename)

bytes_received = 0
start_time = time.time()

with open(filepath, "wb") as f:
    while bytes_received < filesize:
        data = clientSocket.recv(CHUNK_SIZE)
        if not data:
            break
        f.write(data)
        bytes_received += len(data)

        print(f"Received: {bytes_received}/{filesize} bytes")

end_time = time.time()

clientSocket.close()

# Throughput calculation
total_time = end_time - start_time
throughput = (bytes_received / (1024 * 1024)) / total_time

print("\n--- TCP Transfer Complete ---")
print(f"Time taken: {total_time:.2f} seconds")
print(f"Throughput: {throughput:.2f} MB/s")
print(f"Saved to: {filepath}")