from socket import *
import os
import time
import hashlib   # used to compute SHA256 of the downloaded file
import msvcrt    # used for detecting key presses without blocking the program

CHUNK_SIZE = 60000

""" 
packet, _ = clientSocket.recvfrom(65535)
This ensures the client can receive the largest possible UDP packet.

or use the 
 """

SERVER_IP = "127.0.0.1"
SERVER_PORT = 12000

clientSocket = socket(AF_INET, SOCK_DGRAM)

filename = input("Enter file name: ")

os.makedirs("downloads", exist_ok=True)

filepath = os.path.join("downloads", "downloaded_" + filename)

# ------------------------------------------------------------
# RESUME SUPPORT (CLIENT SIDE)
# ------------------------------------------------------------
# If a partially downloaded file already exists, we allow
# the user to continue downloading from where it stopped.

start_seq = 0
bytes_received = 0

if os.path.exists(filepath):

    choice = input("Partial file exists. Resume download? (y/n): ")

    if choice.lower() == "y":

        bytes_received = os.path.getsize(filepath)

        # calculate sequence number based on file size
        start_seq = bytes_received // CHUNK_SIZE

        print(f"Resuming from packet {start_seq}")

        # Truncate any partial chunk to ensure a clean resume point
        with open(filepath, "r+b") as f:
            f.truncate(start_seq * CHUNK_SIZE)
            
        bytes_received = start_seq * CHUNK_SIZE

request = f"GET {filename} {start_seq}"
clientSocket.sendto(request.encode(), (SERVER_IP, SERVER_PORT))

packet, server_addr = clientSocket.recvfrom(CHUNK_SIZE + 100)   ###  This ensures the client can receive the largest possible UDP packet.
""" Why +100?

Your packet also contains:

SEQ|DATA

So we leave some extra buffer. """

### NEW: UDP Handshake - Catch ACCEPT and reply to the new server_addr
if packet == b"ACCEPT":
    clientSocket.sendto(b"ACK_ACCEPT", server_addr)
    
    ### NEW: Get the client's own OS-assigned port
    client_local_port = clientSocket.getsockname()[1] 
    
    ### NEW: Print both the client's port and the server's new dedicated port
    print(f"Handshake complete!")
    print(f"Client (Port {client_local_port}) is now talking to Server (Port {server_addr[1]})\n")
    
    ### NEW: Fetch the next actual packet (SIZE or ERROR) from the new port
    packet, server_addr = clientSocket.recvfrom(CHUNK_SIZE + 100)

if packet.startswith(b"ERROR"):
    print(packet.decode())
    clientSocket.close()
    exit()

### receive file size
if packet.startswith(b"SIZE"):
    filesize = int(packet.decode().split()[1])
    print(f"File size: {filesize} bytes\n")

    ### NEW: Fetch the first data chunk or END packet
    packet, _ = clientSocket.recvfrom(CHUNK_SIZE + 100)

# ------------------------------------------------------------
# Open file depending on whether we are resuming or starting fresh
# ------------------------------------------------------------
if start_seq > 0:
    file = open(filepath, "ab")
else:
    file = open(filepath, "wb")


print("\n--- File Transfer Started ---\n")

print("Press P to pause download")
print("Press R to resume\n")

paused = False


start_time = time.time()             ### to implement the speed : xMB/s

last_packet_time = start_time        ### used for instantaneous speed

expected_seq = start_seq             ### duplicate packet protection


while True:

    # ------------------------------------------------------------
    # Keyboard control for pause / resume
    # ------------------------------------------------------------
    if msvcrt.kbhit():

        key = msvcrt.getch().decode().lower()

        if key == "p":
            paused = True
            print("\nDownload Paused")

        if key == "r":
            paused = False
            print("\nDownload Resumed")
    # ------------------------------------------------------------

    if packet == b"END":
        print("\nServer finished sending file")

        # ------------------------------------------------------------
        # Receive the SHA256 hash sent by the server
        # ------------------------------------------------------------
        hash_packet, _ = clientSocket.recvfrom(2048)
        if hash_packet.startswith(b"HASH"):
            server_hash = hash_packet.decode().split()[1]

        break

    seq, data = packet.split(b"|", 1)
    seq = int(seq.decode())

    size = len(data)

    print(f"Received packet {seq} ({size} bytes)")

    ### duplicate / out-of-order packet protection
    if seq == expected_seq:
        if not paused:
            file.write(data)
            bytes_received += size
            
            # 1. Send ACK for the packet we just successfully wrote
            ack = f"ACK {expected_seq}"
            clientSocket.sendto(ack.encode(), server_addr)
            print(f"Sent ACK {expected_seq}")
            
            expected_seq += 1  # Move our expected sequence forward
        else:
            print("Paused: Withholding ACK to stall the server...")
            # We intentionally DO NOT send an ACK here.

    else:
        print(f"Out-of-order packet {seq} ignored. Expected {expected_seq}.")
        # 2. CRITICAL FIX: If we get the wrong packet, we MUST ACK the LAST 
        # successfully received packet (expected_seq - 1) to force the server to Go-Back-N.
        if expected_seq > start_seq:
            last_good_ack = expected_seq - 1
            ack = f"ACK {last_good_ack}"
            clientSocket.sendto(ack.encode(), server_addr)
            print(f"Sent duplicate ACK {last_good_ack} to trigger server resend")

    ### show completed bytes
    print(f"Completed: {bytes_received}/{filesize} bytes")

    current_time = time.time()

    elapsed_time = current_time - start_time
    packet_time = current_time - last_packet_time

    if elapsed_time > 0:
        avg_speed = (bytes_received / (1024 * 1024)) / elapsed_time
    else:
        avg_speed = 0

    if packet_time > 0:
        instant_speed = (size / (1024 * 1024)) / packet_time
    else:
        instant_speed = 0

    print(f"Speed: {avg_speed:.2f} MB/s (avg)")
    print(f"Instant: {instant_speed:.2f} MB/s\n")

    last_packet_time = current_time

    packet, _ = clientSocket.recvfrom(CHUNK_SIZE + 100)

file.close()


# ------------------------------------------------------------
# SHA256 HASHING (CLIENT SIDE)
# ------------------------------------------------------------
# We compute SHA256 of the downloaded file and compare it with
# the hash sent by the server. If they match, the file is correct.

sha256 = hashlib.sha256()

with open(filepath, "rb") as f:
    while True:
        chunk = f.read(8192)
        if not chunk:
            break
        sha256.update(chunk)

client_hash = sha256.hexdigest()

print("\nIntegrity Check")

# show expected vs calculated hash values
print(f"Expected SHA256 (server):   {server_hash}")
print(f"Calculated SHA256 (client): {client_hash}")

if client_hash == server_hash:
    print("Result: ✔ Hash match — File integrity verified")
else:
    print("Result: ❌ Hash mismatch — File corrupted")

# ------------------------------------------------------------

total_time = time.time() - start_time

if total_time > 0:
    avg_speed = (bytes_received / (1024 * 1024)) / total_time
    print(f"\nFinal Average Speed: {avg_speed:.2f} MB/s")

print("\nFile downloaded successfully")
print("Saved to:", filepath)

clientSocket.close()