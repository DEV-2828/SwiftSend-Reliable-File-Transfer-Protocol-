# import subprocess
# import os

# # create download directory if it doesn't exist
# os.makedirs("multiple_downloads", exist_ok=True)

# num_clients = int(input("Number of clients to spawn: "))
# filename = input("Enter file to download: ")

# for i in range(1, num_clients + 1):

#     print(f"Launching client {i}...")

#     command = f"""
# $env:CLIENT_ID={i};
# $env:TARGET_FILE="{filename}";
# python client.py
# """

#     subprocess.Popen(
#         ["powershell", "-NoExit", "-Command", command]
#     )

# print("\nAll clients launched.")


import os
import subprocess

num_clients = int(input("Number of clients to spawn: "))
filename = input("Enter file to download: ")

for i in range(1, num_clients + 1):

    print(f"Launching client {i}")

    cmd = f'start powershell -NoExit -Command "$env:CLIENT_ID={i}; $env:TARGET_FILE=\\"{filename}\\"; python client.py"'

    subprocess.Popen(cmd, shell=True)

print("\nAll clients launched.")