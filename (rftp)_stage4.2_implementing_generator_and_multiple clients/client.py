from socket import *
import os
import time
import hashlib   # used to compute SHA256 of the downloaded file

CHUNK_SIZE = 60000

""" 

packet, _ = clientSocket.recvfrom(65535)
This ensures the client can receive the largest possible UDP packet.

or use the 
 """

SERVER_IP = "127.0.0.1"
SERVER_PORT = 12000

clientSocket = socket(AF_INET, SOCK_DGRAM)


# ------------------------------------------------------------
# GENERATOR LOGIC
# If launched by the multi-client generator, it passes the
# filename and client id using environment variables.
# Otherwise the program behaves normally and asks for input.
# ------------------------------------------------------------
client_id = os.getenv("CLIENT_ID")

filename = os.getenv("TARGET_FILE")
if not filename:
    filename = input("Enter file name: ")
# ------------------------------------------------------------


request = "GET " + filename
clientSocket.sendto(request.encode(), (SERVER_IP, SERVER_PORT))


packet, _ = clientSocket.recvfrom(CHUNK_SIZE + 100)   ###  This ensures the client can receive the largest possible UDP packet.
""" Why +100?

Your packet also contains:

SEQ|DATA

So we leave some extra buffer. """


if packet.startswith(b"ERROR"):
    print(packet.decode())
    clientSocket.close()
    exit()


### receive file size
if packet.startswith(b"SIZE"):
    filesize = int(packet.decode().split()[1])
    print(f"File size: {filesize} bytes\n")

    packet, _ = clientSocket.recvfrom(CHUNK_SIZE + 100)


# ------------------------------------------------------------
# GENERATOR LOGIC
# Files are saved in multiple_downloads when using the generator
# so that multiple clients do not overwrite each other.
# ------------------------------------------------------------
os.makedirs("multiple_downloads", exist_ok=True)

# create cleaner filename format
name, ext = os.path.splitext(filename)

if client_id:
    new_filename = f"download_{name}_client{client_id}{ext}"
else:
    new_filename = f"download_{filename}"

filepath = os.path.join("multiple_downloads", new_filename)
# ------------------------------------------------------------

file = open(filepath, "wb")

print("\n--- File Transfer Started ---\n")


start_time = time.time()             ### to implement the speed : xMB/s
bytes_received = 0

last_packet_time = start_time        ### used for instantaneous speed

expected_seq = 0                     ### duplicate packet protection


while True:

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

    ### duplicate packet protection
    if seq == expected_seq:
        file.write(data)
        bytes_received += size
        expected_seq += 1
    else:
        print(f"Duplicate packet {seq} ignored")
#--------------------------------------------------------
    ack = f"ACK {seq}"
    clientSocket.sendto(ack.encode(), (SERVER_IP, SERVER_PORT))

    print(f"Sent ACK {seq}")

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