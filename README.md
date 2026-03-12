# 📦 RFTP – Reliable File Transfer Protocol (UDP)
![Python](https://img.shields.io/badge/python-3.x-blue)
![Protocol](https://img.shields.io/badge/networking-UDP-green)
![Integrity](https://img.shields.io/badge/hash-SHA256-orange)
![GUI](https://img.shields.io/badge/gui-PyQt-purple)

A custom **reliable file transfer protocol built over UDP** implementing chunked transmission, SHA-256 integrity verification, resumable downloads, and a PyQt-based GUI for monitoring transfers.

## 🚀 Features

- 📡 Reliable file transfer over UDP
- 📦 Chunk-based transmission for efficient data transfer
- 🔐 SHA-256 integrity verification
- ⏯ Download resume capability
- 📉 Packet loss simulation
- 📊 Transfer speed monitoring
- 🖥 PyQt GUI interface
- ⚡ Optimized UDP packet size (~60KB)

## 🧠 How It Works
Since UDP does not guarantee reliability, this project implements its own reliability layer.
UDP was chosen instead of TCP to demonstrate how reliability mechanisms such as retransmission, integrity verification, and chunk management can be implemented at the application layer.

### Transfer Workflow

1. Server loads the requested file.
2. Server computes the **SHA-256 hash** of the file.
3. The file is divided into **fixed-size chunks**.
4. Client requests the file from the server.
5. Server sends chunks via **UDP packets**.
6. Client receives packets and reconstructs the file.
7. Missing packets are detected and **retransmission is requested**.
8. Client computes **SHA-256 hash** of the downloaded file.
9. Hash comparison verifies **file integrity**.
```text
Client                         Server
  |                              |
  | ---- Request File ---------> |
  |                              |
  | <---- File Metadata -------- |
  |                              |
  | <----- UDP Data Chunks ----- |
  |                              |
  | ---- Missing Packets ------> |
  |                              |
  | <---- Retransmissions ------ |
  |                              |
  | ---- Hash Verification ----> |
```

## 🛠 Technologies Used

- Python
- Socket Programming
- UDP Protocol
- SHA-256 Hashing
- PyQt GUI Framework
- Multithreading

## 📂 Project Structure
```
SwiftSend-Reliable-File-Transfer-Protocol/
│
├── server.py
├── client.py
├── gui_client.py
├── gui_server.py
│
├── test_files/
├── screenshots/
│
└── README.md
```
## ⚙ Installation

Clone the repository:
```bash
git clone https://github.com/DEV-2828/SwiftSend-Reliable-File-Transfer-Protocol.git
cd SwiftSend-Reliable-File-Transfer-Protocol
```

Install dependencies:
```bash
pip install pyqt5
```
## ▶ Running the Project

Start the Server
```bash
python server.py
```
Start the Client
```bash
python client.py
```
Run GUI Version
```bash
python gui_client.py
```
## 🔐 Integrity Verification

The server computes the SHA-256 hash of the original file.

After the download:

- Client calculates SHA-256 of the received file
- Client compares it with the server hash

Example output:
```bash
Expected Hash  : a7c5d92f4b4e...
Received Hash  : a7c5d92f4b4e...

Integrity Check Passed ✔
```

If the hashes differ, the transfer is considered corrupted.

## ⚡ Performance Optimization

The project increases UDP packet size for faster transfers.

```text
Maximum UDP Payload = 65507 bytes

65535 (IP packet)
- 8    UDP header
- 20   IP header
-------------------
= 65507 bytes
```

The implementation uses ~60000 byte chunks to maximize throughput.

## 📊 Example Transfer Output

```bash
Starting Transfer...
Packets Received: 1024
Transfer Speed: 8.4 MB/s

Expected Hash : a7c5d92f4b...
Received Hash : a7c5d92f4b...

Integrity Check Passed ✔
```

## 🔮 Future Improvements

- 🔐 TLS / SSL encryption
- 📡 Congestion control
- 📦 Parallel chunk downloading
- 🌐 Web-based client interface
- 📉 Advanced packet recovery algorithms

---

# 👨‍💻 Author

Dev
BTech Computer Science Student

## ⭐ If you like this project

Give the repository a **star ⭐ on GitHub!**
