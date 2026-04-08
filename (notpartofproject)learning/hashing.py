""" 
CODE to demonstrate how hashing works
 """

import hashlib

""" 

 """

name = "DEVOPAM PAL"
print(f"NAME in string: {name}")
binary_name= name.encode()
print(f"NAME in binary: {binary_name}")

hash = hashlib.sha256(b"DEVOPAM")

print("For DEVOPAM : ")
print(hash.digest())
print(hash.hexdigest())

hash = hashlib.sha256(b"PAL")

print("For DEVOPAM : ")
print(hash.digest())
print(hash.hexdigest())


hash = hashlib.sha256(b"DEVOPAM PAL")

print("For DEVOPAM PAL: ")
print(hash.digest())
print(hash.hexdigest())

hash2 = hashlib.sha256()

for i in binary_name :
    hash2.digest(i)
print(hash2.hexdigest)