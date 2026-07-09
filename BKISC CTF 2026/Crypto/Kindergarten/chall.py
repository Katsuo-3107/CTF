from Crypto.Util.number import getPrime
import os
import secrets

FLAG = os.getenv("GZCTF_FLAG", "BKISC{local_test_flag}")

def menu():
    print("1. Query")
    print("2. Verify")
    print("3. Exit")
    return input("Option: ")
def main():
    secret_size = 256
    p_size = 32
    secret = os.urandom(secret_size)
    secret_num = int(secret.hex(), 16)
    for _ in range(75):
        option = menu()
        if option == "1":
            p = getPrime(p_size)
            r = secret_num % p
            if secrets.randbits(1):
                r = -r % p
            print(f'(p, r) = ({p}, {r})')
        elif option == "2":
            secret_input = input("What is the secret? ")
            secret_input = bytes.fromhex(secret_input)
            if secret_input == secret:
                print("Correct!")
                print("Here is your reward: ", FLAG)
            else:
                print("SUSSSSSS")
            exit()
        elif option == "3":
            print("Exiting...")
            break
        else:
            print("Invalid option, please try again.")

main()
