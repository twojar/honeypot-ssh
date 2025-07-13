# LIBRARIES
import logging
from logging.handlers import RotatingFileHandler
import time
import datetime
import paramiko
import socket
import threading
from paramiko.auth_strategy import PrivateKey
from paramiko.client import SSHClient

# CONSTANTS
LOGGING_FORMAT = logging.Formatter('%(message)s')


# generate a dynamic banner with current time and date
def generate_banner():
    now = datetime.datetime.now()
    current_time = now.strftime("%a %b %d %H:%M:%S UTC %Y")
    last_login_time = (now - datetime.timedelta(hours=2, minutes=7)).strftime("%a %b %d %H:%M:%S %Y")

    banner = (
            b"Welcome to Ubuntu 20.04.6 LTS (GNU/Linux 5.15.0-97-generic x86_64)\r\n"
            b"\r\n"
            b" * Documentation:  https://help.ubuntu.com\r\n"
            b" * Management:     https://landscape.canonical.com\r\n"
            b" * Support:        https://ubuntu.com/advantage\r\n"
            b"\r\n"
            b"  System information as of " + current_time.encode('utf-8') + b"\r\n"
                                                                            b"\r\n"
                                                                            b"  System load:  0.08               Processes:             112\r\n"
                                                                            b"  Usage of /:   41.2% of 19.56GB   Users logged in:       1\r\n"
                                                                            b"  Memory usage: 32%                IPv4 address for eth0: 192.168.1.24\r\n"
                                                                            b"  Swap usage:   0%\r\n"
                                                                            b"\r\n"
                                                                            b" * Canonical Livepatch is available for installation.\r\n"
                                                                            b"   - Reduce system reboots and improve kernel security. Activate at:\r\n"
                                                                            b"     https://ubuntu.com/livepatch\r\n"
                                                                            b"\r\n"
                                                                            b"Last login: " + last_login_time.encode(
        'utf-8') + b" from 192.168.1.10\r\n"
                   b"\r\n"
    )
    return banner

# Change this to private server key!
HOST_KEY_PATH = 'server.key'
HOST_KEY = paramiko.RSAKey.from_private_key_file(HOST_KEY_PATH)

# LOGGING PREP
funnelLogger = logging.getLogger('FunnelLogger')
funnelLogger.setLevel(logging.INFO)
# custom handler to log attacks
funnelHandler = RotatingFileHandler('audits.log', maxBytes=2000, backupCount=5)
funnelHandler.setFormatter(LOGGING_FORMAT)
# add Handler to Logger
funnelLogger.addHandler(funnelHandler)
# credentials logger
credsLogger = logging.getLogger('CredsLogger')
credsLogger.setLevel(logging.INFO)
credsHandler = RotatingFileHandler('cmdAudits.log', maxBytes=2000, backupCount=5)
credsHandler.setFormatter(LOGGING_FORMAT)
credsLogger.addHandler(credsHandler)


# IMPROVED EMULATED SHELL
def emulatedShell(channel, client_ip):
    # fake shell prompt
    prompt = b'[admin@prod-db01 ~]$ '
    channel.send(prompt)
    command_buffer = bytearray()
    cursor_pos = 0

    while True:
        try:
            # listen for user input
            char = channel.recv(1)
            if not char:
                channel.close()
                break

            # Handle different control characters
            if char == b'\x7f' or char == b'\x08':  # Backspace (DEL or BS)
                if cursor_pos > 0:
                    # Remove character from buffer
                    command_buffer.pop(cursor_pos - 1)
                    cursor_pos -= 1
                    # Send backspace sequence: move cursor back, clear to end, rewrite line
                    channel.send(b'\x08 \x08')  # backspace, space, backspace
                    # Rewrite the rest of the line if there are characters after cursor
                    if cursor_pos < len(command_buffer):
                        remaining = command_buffer[cursor_pos:]
                        channel.send(remaining)
                        channel.send(b' ')  # Clear any leftover character
                        # Move cursor back to correct position
                        for _ in range(len(remaining) + 1):
                            channel.send(b'\x08')

            elif char == b'\x1b':  # ESC sequence (arrow keys, etc.)
                # Read the next two characters for arrow key sequences
                seq1 = channel.recv(1)
                seq2 = channel.recv(1)
                if seq1 == b'[':
                    if seq2 == b'D':  # Left arrow
                        if cursor_pos > 0:
                            cursor_pos -= 1
                            channel.send(b'\x1b[D')  # Move cursor left
                    elif seq2 == b'C':  # Right arrow
                        if cursor_pos < len(command_buffer):
                            cursor_pos += 1
                            channel.send(b'\x1b[C')  # Move cursor right
                    elif seq2 == b'A' or seq2 == b'B':  # Up/Down arrows
                        # You could implement command history here
                        pass

            elif char == b'\x01':  # Ctrl+A (beginning of line)
                # Move cursor to beginning
                for _ in range(cursor_pos):
                    channel.send(b'\x08')
                cursor_pos = 0

            elif char == b'\x05':  # Ctrl+E (end of line)
                # Move cursor to end
                for _ in range(len(command_buffer) - cursor_pos):
                    channel.send(b'\x1b[C')
                cursor_pos = len(command_buffer)

            elif char == b'\x0c':  # Ctrl+L (clear screen)
                channel.send(b'\x1b[2J\x1b[H')  # Clear screen and move to top
                channel.send(prompt)
                channel.send(command_buffer)

            elif char == b'\r' or char == b'\n':  # Enter
                channel.send(b'\r\n')
                command = bytes(command_buffer).strip()

                # Process the command
                response = process_command(command, client_ip)

                if command == b'exit':
                    channel.send(response)
                    channel.close()
                    credsLogger.info(f'Client {client_ip} disconnected from the server')
                    break
                else:
                    channel.send(response)
                    channel.send(prompt)

                # Reset command buffer
                command_buffer = bytearray()
                cursor_pos = 0

            elif char == b'\x03':  # Ctrl+C
                channel.send(b'^C\r\n')
                channel.send(prompt)
                command_buffer = bytearray()
                cursor_pos = 0

            elif char == b'\x04':  # Ctrl+D (EOF)
                if len(command_buffer) == 0:
                    channel.send(b'logout\r\n')
                    channel.close()
                    break

            elif char == b'\t':  # Tab completion
                # Basic tab completion - you can expand this
                command_so_far = bytes(command_buffer[:cursor_pos])
                completion = handle_tab_completion(command_so_far)
                if completion:
                    # Add completion to buffer
                    for c in completion:
                        command_buffer.insert(cursor_pos, c)
                        cursor_pos += 1
                    channel.send(completion)

            else:
                # Regular character - insert at cursor position
                if 32 <= ord(char) <= 126:  # Printable ASCII
                    command_buffer.insert(cursor_pos, ord(char))
                    cursor_pos += 1

                    # Send the character and any characters after it
                    channel.send(char)
                    if cursor_pos < len(command_buffer):
                        # There are characters after the cursor, need to redraw
                        remaining = command_buffer[cursor_pos:]
                        channel.send(remaining)
                        # Move cursor back to correct position
                        for _ in range(len(remaining)):
                            channel.send(b'\x08')

        except Exception as e:
            print(f"Error in shell: {e}")
            break


def process_command(command, client_ip):
    """Process shell commands and return response"""
    credsLogger.info(f'Command {command} executed by {client_ip}')

    if command == b'exit':
        return b'Goodbye!\r\n'
    elif command == b'pwd':
        return b'/user/local\r\n'
    elif command == b'whoami':
        return b'admin\r\n'
    elif command == b'ls':
        return b'Documents  Downloads  backup.sh  mysql.sock\r\n'
    elif command == b'ls -la':
        return (
            b'total 28\r\n'
            b'drwxr-xr-x  4 admin admin 4096 Jan 15 10:30 .\r\n'
            b'drwxr-xr-x  3 root  root  4096 Jan 10 09:15 ..\r\n'
            b'-rw-r--r--  1 admin admin  220 Jan 10 09:15 .bash_logout\r\n'
            b'-rw-r--r--  1 admin admin 3771 Jan 10 09:15 .bashrc\r\n'
            b'-rw-r--r--  1 admin admin  807 Jan 10 09:15 .profile\r\n'
            b'drwxr-xr-x  2 admin admin 4096 Jan 12 14:20 Documents\r\n'
            b'drwxr-xr-x  2 admin admin 4096 Jan 12 14:20 Downloads\r\n'
            b'-rwxr-xr-x  1 admin admin  156 Jan 15 10:30 backup.sh\r\n'
            b'srw-rw-rw-  1 mysql mysql    0 Jan 15 08:31 mysql.sock\r\n'
        )
    elif command == b'ps aux':
        time.sleep(0.5)
        return (
            b'USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\r\n'
            b'root         1  0.0  0.1  22568  1584 ?        Ss   08:30   0:01 /sbin/init\r\n'
            b'mysql      203  0.1  1.2 274848 10232 ?       Ssl  08:31   0:03 /usr/sbin/mysqld\r\n'
            b'admin      512  0.0  0.3  44688  3408 pts/0    Ss   08:35   0:00 bash\r\n'
            b'admin      789  0.0  0.2  36084  2588 pts/0    R+   10:42   0:00 ps aux\r\n'
        )
    elif command == b'netstat -tulnp':
        time.sleep(0.5)
        return (
            b'Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name\r\n'
            b'tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      203/sshd\r\n'
            b'tcp6       0      0 :::3306                :::*                    LISTEN      312/mysqld\r\n'
            b'tcp        0      0 127.0.0.1:80           0.0.0.0:*               LISTEN      445/nginx\r\n'
        )
    elif command == b'ifconfig' or command == b'ip a':
        time.sleep(0.5)
        return (
            b'eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\r\n'
            b'        inet 192.168.1.24  netmask 255.255.255.0  broadcast 192.168.1.255\r\n'
            b'        inet6 fe80::a00:27ff:fe4e:66a1  prefixlen 64  scopeid 0x20<link>\r\n'
            b'        ether 08:00:27:4e:66:a1  txqueuelen 1000  (Ethernet)\r\n'
        )
    elif command.startswith(b'cat '):
        filename = command[4:]
        if filename == b'backup.sh':
            return (
                b'#!/bin/bash\r\n'
                b'# Database backup script\r\n'
                b'mysqldump -u backup_user -p$DB_PASS --all-databases > /backups/db_$(date +%Y%m%d).sql\r\n'
                b'echo "Backup completed"\r\n'
            )
        else:
            return b'cat: ' + filename + b': No such file or directory\r\n'
    elif command == b'history':
        return (
            b'  1  ls\r\n'
            b'  2  pwd\r\n'
            b'  3  ps aux\r\n'
            b'  4  netstat -tulnp\r\n'
            b'  5  cat backup.sh\r\n'
        )
    elif command == b'uname -a':
        return b'Linux prod-db01 5.15.0-97-generic #107-Ubuntu SMP x86_64 x86_64 x86_64 GNU/Linux\r\n'
    elif command == b'df -h':
        return (
            b'Filesystem      Size  Used Avail Use% Mounted on\r\n'
            b'/dev/sda1        20G  8.1G   11G  44% /\r\n'
            b'/dev/sda2       100G   45G   50G  48% /var\r\n'
            b'tmpfs           2.0G     0  2.0G   0% /dev/shm\r\n'
        )
    elif command == b'free -h':
        return (
            b'              total        used        free      shared  buff/cache   available\r\n'
            b'Mem:          3.8Gi       1.2Gi       1.8Gi        12Mi       847Mi       2.4Gi\r\n'
            b'Swap:         2.0Gi          0B       2.0Gi\r\n'
        )
    elif command == b'':
        return b''
    else:
        return b'bash: ' + command + b': command not found\r\n'


def handle_tab_completion(command_so_far):
    """Basic tab completion for common commands"""
    commands = [b'ls', b'pwd', b'whoami', b'ps', b'netstat', b'ifconfig', b'cat',
                b'history', b'uname', b'df', b'free', b'exit']

    matches = [cmd for cmd in commands if cmd.startswith(command_so_far)]

    if len(matches) == 1:
        # Complete the command
        return matches[0][len(command_so_far):]
    elif len(matches) > 1:
        # Could show available options, but for simplicity just return nothing
        return b''

    return b''


# SSH SERVER
class Server(paramiko.ServerInterface):
    def __init__(self, client_ip, input_username=None, input_password=None):
        self.event = threading.Event()
        self.client_ip = client_ip
        self.input_username = input_username
        self.input_password = input_password

    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == 'session':
            return paramiko.common.OPEN_SUCCEEDED
        return paramiko.common.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_allowed_auth(self):
        return "password"

    def check_auth_password(self, username, password) -> int:
        # log actions
        funnelLogger.info(
            f'Client {self.client_ip} attempted connection with username: {username}, password: {password}')
        credsLogger.info(f'{self.client_ip}, {username}, {password}')
        if self.input_username is not None and self.input_password is not None:
            if username == self.input_username and password == self.input_password:
                return paramiko.common.AUTH_SUCCESSFUL
            else:
                return paramiko.common.AUTH_FAILED
        else:
            return paramiko.common.AUTH_SUCCESSFUL

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True

    def check_channel_exec_request(self, channel, command):
        command = str(command)
        return True


# CLIENT HANDLER (create local instance of server)
def client_handle(client, addr, username, password):
    # client ip in index 0
    clientIP = addr[0];
    print(f"{clientIP} has connected to the server")
    # initialize new transport object
    try:
        transport = paramiko.Transport(client)
        transport.local_version = "SSH-2.0-OpenSSH_8.9"
        server = Server(client_ip=clientIP, input_username=username, input_password=password)
        transport.add_server_key(HOST_KEY)
        transport.start_server(server=server)
        channel = transport.accept(100)
        if channel is None:
            print("No channel was opened!")
        channel.send(generate_banner())
        emulatedShell(channel, client_ip=clientIP)
    except Exception as error:
        print("ERROR")
        print(error)
    finally:
        try:
            transport.close()
        except Exception as error:
            print("ERROR")
            print(error)
        client.close()


# PROVISION SSH-BASED HONEYPOT
def honeypot(address, port, username, password):
    # create new socket
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socks.bind((address, port))
    # limit to 100 connections
    socks.listen(100)
    print(f"SSH server is listening on port {port}.")
    # create thread
    while True:
        try:
            client, addr = socks.accept()
            sshHoneypotThread = threading.Thread(target=client_handle, args=(client, addr, username, password))
            sshHoneypotThread.start()
        except Exception as error:
            print("ERROR")
            print(error)