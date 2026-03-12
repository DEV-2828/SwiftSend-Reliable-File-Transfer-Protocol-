from socket import *
import threading
import os

SERVER_PORT = 12000
CHUNK_SIZE = 60000          ### default is 1KB = 1024

""" 
Maximum UDP payload : 65507 bytes
This comes from:

65535 (max IP packet)
- 8    (UDP header)
- 20   (IP header)

So anything larger than ~65 KB will cause:

WinError 10040
message larger than internal buffer
"""

serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', SERVER_PORT))

print("Server running on port", SERVER_PORT)


def handle_client(filename, clientAddress):

    try:
        filepath = os.path.join("files", filename)
        file = open(filepath, "rb")
    except FileNotFoundError:
        serverSocket.sendto(b"ERROR: File not found", clientAddress)
        return

    ### send file size first so the client can track completed bytes
    filesize = os.path.getsize(filepath)
    serverSocket.sendto(f"SIZE {filesize}".encode(), clientAddress)

    seq = 0

    while True:
        data = file.read(CHUNK_SIZE)

        if not data:
            break

        packet = str(seq).encode() + b"|" + data

                                                ### now set the timeout to 50ms
        serverSocket.settimeout(0.05)           ### change this value to increase or decrease the speed
                                             ###  and keep it outside the inner while loop so that it's not runned continuouly
        """ 
        Stop-and-Wait throughput depends on:

        Throughput ≈ Packet Size / RTT

        If the timeout is 1 second, the server may stall unnecessarily.
        Reducing it keeps the pipeline moving.
        """

        while True:                                                ### now we add the reliability part of the file transfer
            serverSocket.sendto(packet, clientAddress)             ### implement the Stop-and-Wait ACK system 
                                                                   ### If the server doesn't receive ACK within a timeout, it resends the packet.

            print(f"Sent packet {seq} ({len(data)} bytes)")

            try:
                ack, addr = serverSocket.recvfrom(1024)

                if addr == clientAddress and ack.decode() == f"ACK {seq}":
                    print(f"ACK {seq} received\n")
                    serverSocket.settimeout(None)
                    break

            except timeout:
                print(f"Resending packet {seq}\n")

        seq += 1

    serverSocket.sendto(b"END", clientAddress)

    file.close()

    serverSocket.settimeout(None)

    print("Finished sending to", clientAddress)


while True:

    try:
        message, clientAddress = serverSocket.recvfrom(2048)    ### the buffer size is small since we are only getting the ACK from the client side
    except timeout:
        continue

    request = message.decode()

    if request.startswith("GET"):
        filename = request.split()[1]

        print("Client requested:", filename)

        thread = threading.Thread(
            target=handle_client,
            args=(filename, clientAddress)
        )

        thread.start()