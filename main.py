# LIBRARIES
import argparse
from honeypotSSH import *
from honeypotHTTP import *
import time
# PARSE ARGUMENTS
if __name__ == "__main__":
    # ARGUMENTS: address,port,username,password, ssh, html
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--address', type=str, required=True)
    parser.add_argument('-p', '--port', type=int,required=True)
    parser.add_argument('-u', '--username',type=str)
    parser.add_argument('-pw', '--password',type=str)
    parser.add_argument('-s', '--ssh', action="store_true")
    parser.add_argument('-w', '--http', action="store_true")

    #store args
    args = parser.parse_args()
    try:
        if args.ssh:
            print("Running SSH Honeypot...")
            honeypot(args.address, args.port, args.username, args.password)
            if not args.username:
                username = None
            if not args.password:
                password = None
        elif args.http:
            print("Running HTTP Honeypot...")
            honeypot_web()
            if not args.username:
                args.username = "admin"
            if not args.password:
                password = "password"
            print(f"Port: {args.port} Username: {args.username} Password: {args.password}")
            run_honeypot_web(args.port, args.username, args.password)
        else:
            print("ERROR: Choose a honeypot to run!")
            print("SSH (--ssh) or HTTP (--http)")
    except KeyboardInterrupt:
        print()
        print("Exiting program...")
        time.sleep(0.5)
        print("Goodbye!")


