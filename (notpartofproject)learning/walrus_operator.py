""" 
WALRUS OPERATOR ---> :=
called assignment expression operator
"""

import os

# data = input()
# while data != "exit":
#     print(data)
#     data = input()

# --- Example 1: User Input with Walrus Operator ---
# This example demonstrates how the walrus operator can make input loops more concise.
# Uncomment the following lines to try it out. Type 'exit' to stop.
# print("\n--- Walrus Operator Input Loop (type 'exit' to exit) ---")
# while (user_input := input("Enter something: ")) != 'exit':
#     print(f"You entered: {user_input}")
# print("Exited walrus input loop.")

# --- Example 2: File Reading with Walrus Operator ---
# This example demonstrates efficient chunk reading from a file.
# If 'sample.txt' doesn't exist, it will be created for demonstration.


sample_file_path = "sample.txt"
if not os.path.exists(sample_file_path):
    print(f"'{sample_file_path}' not found. Creating a dummy file for demonstration.")
    with open(sample_file_path, "w") as f:
        f.write("Hello World! This is a test file for the walrus operator example.")

print(f"\n--- Reading '{sample_file_path}' in chunks using Walrus Operator ---")
with open(sample_file_path,"r") as data:
    while(chunk:= data.read(4)):
        print(f"Read chunk: '{chunk}'")
print("Finished reading file.")