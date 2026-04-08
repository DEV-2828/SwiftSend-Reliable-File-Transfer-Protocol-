from socket import *
import threading
import os
import hashlib   # used for SHA-256 hashing of the original file

SERVER_PORT = 12000
CHUNK_SIZE = 60000          ### default is 1KB = 1024
WINDOW_SIZE = 20          # How many packets to blast out before waiting

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


def handle_client(filename, clientAddress, start_seq):

    # ------------------------------------------------------------
    # Each client thread uses its own socket.
    # This prevents ACK collisions between multiple clients.
    # ------------------------------------------------------------
    clientSocket = socket(AF_INET, SOCK_DGRAM)
    clientSocket.bind(('', 0))   # OS assigns a free port

    ### NEW: UDP Handshake - send ACCEPT from the new port
    clientSocket.sendto(b"ACCEPT", clientAddress)
    
    ### NEW: Wait up to 5s for client to acknowledge the port switch
    clientSocket.settimeout(5.0) 
    try:
        ack_msg, addr = clientSocket.recvfrom(1024)
        if ack_msg != b"ACK_ACCEPT" or addr != clientAddress:
            print("Invalid handshake.")
            clientSocket.close()
            return
        print(f"Handshake complete. Client {addr} on new port.")
    except timeout:
        print(f"Handshake timeout for {clientAddress}")
        clientSocket.close()
        return
        
    clientSocket.settimeout(None) ### NEW: Reset timeout for normal operations

    try:
        filepath = os.path.join("files", filename)
        file = open(filepath, "rb")
    except FileNotFoundError:
        clientSocket.sendto(b"ERROR: File not found", clientAddress)
        return

    ### send file size first so the client can track completed bytes
    filesize = os.path.getsize(filepath)
    clientSocket.sendto(f"SIZE {filesize}".encode(), clientAddress)

    # SHA256 HASHING (SERVER SIDE)
    # ------------------------------------------------------------
    # Here we compute the SHA256 hash of the original file.
    # This hash acts as a fingerprint of the file contents.
    # The client will compute the same hash after download
    # and compare them to verify the file was not corrupted.
    sha256 = hashlib.sha256()

    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha256.update(chunk)

    file_hash = sha256.hexdigest()
    # ------------------------------------------------------------

    # ------------------------------------------------------------
    # RESUME SUPPORT
    # ------------------------------------------------------------
    # Move the file pointer to the correct byte position
    # based on the sequence number sent by the client.
    # This allows the server to continue sending from
    # where the client previously stopped downloading.
    file.seek(start_seq * CHUNK_SIZE)

    # ------------------------------------------------------------
    # NEW: SLIDING WINDOW (GO-BACK-N) LOGIC
    # ------------------------------------------------------------
    # WINDOW_SIZE = 20          # How many packets to blast out before waiting
    base = start_seq          # Oldest unacknowledged packet
    next_seq = start_seq      # Next packet to be sent
    window = {}               # Buffer to hold unacknowledged packets {seq: packet}
    eof_reached = False

    # Short timeout so the server constantly alternates between sending and checking for ACKs
    clientSocket.settimeout(0.02) 

    while True:
        # 1. Fill the window: Send packets until we hit the WINDOW_SIZE limit
        while next_seq < base + WINDOW_SIZE and not eof_reached:
            data = file.read(CHUNK_SIZE)
            
            if not data:
                eof_reached = True
                break

            packet = str(next_seq).encode() + b"|" + data
            window[next_seq] = packet  # Save packet in buffer in case we need to resend
            
            clientSocket.sendto(packet, clientAddress)
            print(f"Sent packet {next_seq} ({len(data)} bytes)")
            next_seq += 1

        # 2. Listen for ACKs to slide the window forward
        try:
            ack_msg, addr = clientSocket.recvfrom(1024)

            if addr == clientAddress and ack_msg.startswith(b"ACK"):
                ack_seq = int(ack_msg.decode().split()[1])
                
                # If we get an ACK for a packet inside our window, slide it forward
                if ack_seq >= base:
                    print(f"ACK {ack_seq} received -> Sliding window")
                    
                    # Remove all acknowledged packets from our memory buffer
                    for s in range(base, ack_seq + 1):
                        window.pop(s, None)
                    
                    base = ack_seq + 1 # Move the base up

        except timeout:
            # 3. Timeout: We haven't received ACKs lately. Resend the current window!
            if base < next_seq:
                print(f"\n--- Timeout! Resending window from {base} to {next_seq - 1} ---\n")
                for s in range(base, next_seq):
                    clientSocket.sendto(window[s], clientAddress)

        # 4. Exit Condition: We hit the end of the file AND all packets have been ACKed
        if eof_reached and base == next_seq:
            break
    # ------------------------------------------------------------

    clientSocket.sendto(b"END", clientAddress)

    # ------------------------------------------------------------
    # Send the SHA256 hash to the client for integrity verification
    # ------------------------------------------------------------
    clientSocket.sendto(f"HASH {file_hash}".encode(), clientAddress)

    file.close()

    clientSocket.settimeout(None)

    print("Finished sending to", clientAddress)

    clientSocket.close()


while True:

    message, clientAddress = serverSocket.recvfrom(2048)    ### the buffer size is small since we are only getting the ACK from the client side

    request = message.decode()

    if request.startswith("GET"):

        parts = request.split()

        filename = parts[1]

        # ------------------------------------------------------------
        # RESUME REQUEST SUPPORT
        # ------------------------------------------------------------
        # Client may send: GET filename start_seq
        # If start_seq is present, resume the transfer.
        if len(parts) > 2:
            start_seq = int(parts[2])
        else:
            start_seq = 0
        # ------------------------------------------------------------

        print("Client requested:", filename, "from seq", start_seq)

        thread = threading.Thread(
            target=handle_client,
            args=(filename, clientAddress, start_seq)
        )

        thread.start()