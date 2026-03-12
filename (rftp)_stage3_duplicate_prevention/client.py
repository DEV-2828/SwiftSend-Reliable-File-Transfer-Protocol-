from socket import *
import os
import time

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


os.makedirs("downloads", exist_ok=True)

filepath = os.path.join("downloads", "downloaded_" + filename)
file = open(filepath, "wb")

print("\n--- File Transfer Started ---\n")


start_time = time.time()             ### to implement the speed : xMB/s
bytes_received = 0

last_packet_time = start_time        ### used for instantaneous speed

expected_seq = 0                     ### duplicate packet protection


while True:

    if packet == b"END":
        print("\nServer finished sending file")
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

total_time = time.time() - start_time

if total_time > 0:
    avg_speed = (bytes_received / (1024 * 1024)) / total_time
    print(f"\nFinal Average Speed: {avg_speed:.2f} MB/s")

print("\nFile downloaded successfully")
print("Saved to:", filepath)

clientSocket.close()