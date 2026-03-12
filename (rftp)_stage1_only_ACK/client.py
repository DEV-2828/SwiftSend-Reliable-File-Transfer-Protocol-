from socket import *
import os

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

os.makedirs("downloads", exist_ok=True)

filepath = os.path.join("downloads", "downloaded_" + filename)
file = open(filepath, "wb")

print("\n--- File Transfer Started ---\n")

while True:

    if packet == b"END":
        print("\nServer finished sending file")
        break

    seq, data = packet.split(b"|", 1)
    seq = int(seq.decode())

    size = len(data)

    print(f"Received packet {seq} ({size} bytes)")

    file.write(data)

    ack = f"ACK {seq}"
    clientSocket.sendto(ack.encode(), (SERVER_IP, SERVER_PORT))

    print(f"Sent ACK {seq}\n")

    packet, _ = clientSocket.recvfrom(CHUNK_SIZE + 100)

file.close()

print("\nFile downloaded successfully")
print("Saved to:", filepath)

clientSocket.close()