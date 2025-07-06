# LIBRARIES
import logging
from logging.handlers import RotatingFileHandler
import time
import paramiko
import socket
import threading
from paramiko.auth_strategy import PrivateKey
from paramiko.client import SSHClient

# CONSTANTS
LOGGING_FORMAT =  logging.Formatter('%(message)s')
STANDARD_BANNER = b"""
Welcome to Ubuntu 20.04.6 LTS (GNU/Linux 5.15.0-97-generic x86_64)
\r\n\r\n
"""

#Change this to private server key!
HOST_KEY_PATH = 'server.key'
HOST_KEY = paramiko.RSAKey.from_private_key_file(HOST_KEY_PATH)


# LOGGING PREP
funnelLogger = logging.getLogger('FunnelLogger')
funnelLogger.setLevel(logging.INFO)
#custom handler to log attacks
funnelHandler = RotatingFileHandler('audits.log', maxBytes=2000, backupCount=5)
funnelHandler.setFormatter(LOGGING_FORMAT)
#add Handler to Logger
funnelLogger.addHandler(funnelHandler)
#credentials logger
credsLogger = logging.getLogger('CredsLogger')
credsLogger.setLevel(logging.INFO)
credsHandler = RotatingFileHandler('cmdAudits.log', maxBytes=2000, backupCount=5)
credsHandler.setFormatter(LOGGING_FORMAT)
credsLogger.addHandler(credsHandler)

# EMULATED SHELL
def emulatedShell(channel, client_ip):
    #fake shell prompt
    channel.send(b'[admin@prod-db01 ~]$ ')
    command = b""
    while True:
        #listen for user input
        char = channel.recv(1)
        channel.send(char)
        if not char:
            channel.close()
        command += char
        # fake shell commands
        # feel free to change this to your liking :)
        if char == b'\r':
            if command.strip() == b'exit':
                response = b'\nGoodbye!\n'
                channel.close()
                credsLogger.info(f'Client {client_ip} disconnected from the server')
            elif command.strip() == b'pwd':
                response = b'\n \user\local' + b'\r\n'
                credsLogger.info(f'Command {command.strip()} executed by {client_ip}')
            elif command.strip() == b'whoami':
                credsLogger.info(f'Command {command.strip()} executed by {client_ip}')
                response = b'\n admin\r\n'
            elif command.strip() == b'ls':
                credsLogger.info(f'Command {command.strip()} executed by {client_ip}')
                response = b'\n Documents  Downloads  backup.sh  mysql.sock\r\n'
            elif command.strip() == b'ps aux':
                credsLogger.info(f'Command {command.strip()} executed by {client_ip}')
                time.sleep(0.5)
                response = (
                    b'\n'
                    b'USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\r\n'
                    b'root         1  0.0  0.1  22568  1584 ?        Ss   08:30   0:01 /sbin/init\r\n'
                    b'mysql      203  0.1  1.2 274848 10232 ?       Ssl  08:31   0:03 /usr/sbin/mysqld\r\n'
                    b'admin      512  0.0  0.3  44688  3408 pts/0    Ss   08:35   0:00 bash\r\n'
                )
            elif command.strip() == b'netstat -tulnp':
                credsLogger.info(f'Command {command.strip()} executed by {client_ip}')
                time.sleep(0.5)
                response = (
                    b'\n'
                    b'Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name\r\n'
                    b'tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      203/sshd\r\n'
                    b'tcp6       0      0 :::3306                :::*                    LISTEN      312/mysqld\r\n'
                )
            elif command.strip() == b'ifconfig' or command.strip() == b'ip a':
                credsLogger.info(f'Command {command.strip()} executed by {client_ip}')
                time.sleep(0.5)
                response = (
                    b'\n'
                    b'eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\r\n'
                    b'        inet 192.168.1.24  netmask 255.255.255.0  broadcast 192.168.1.255\r\n'
                    b'        inet6 fe80::a00:27ff:fe4e:66a1  prefixlen 64  scopeid 0x20<link>\r\n'
                )
            elif command.strip().startswith(b'cat '):
                credsLogger.info(f'Command {command.strip()} executed by {client_ip}')
                response = b'\n Permission denied\r\n'
            else:
                credsLogger.info(f'Command {command.strip()} executed by {client_ip}')
                response = b'\n bash: ' + command.strip() + b': command not found\r\n'
            #listen for next command
            channel.send(response)
            channel.send(b'[admin@prod-db01 ~]$ ')
            command = b""

# SSH SERVER
class Server(paramiko.ServerInterface):
    def __init__(self,client_ip, input_username=None, input_password=None):
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
        #log actions
        funnelLogger.info(f'Client {self.client_ip} attempted connection with username: {username}, password: {password}')
        credsLogger.info(f'{self.client_ip}, {username}, {password}')
        if self.input_username is not None and self.input_password is not None:
            if username == self.input_username and password == self.input_password:
                return paramiko.common.AUTH_SUCCESSFUL
            else:
                return paramiko.common.AUTH_FAILED
        else:
            return paramiko.common.AUTH_SUCCESSFUL
    def check_channel_shell_request(self,channel):
        self.event.set()
        return True
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True
    def check_channel_exec_request(self, channel, command):
        command = str(command)
        return True

# CLIENT HANDLER (create local instance of server)
def client_handle(client,addr,username,password):
    #client ip in index 0
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
        channel.send(STANDARD_BANNER)
        emulatedShell(channel, client_ip= clientIP)
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
    #create new socket
    socks = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socks.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socks.bind((address,port))
    #limit to 100 connections
    socks.listen(100)
    print(f"SSH server is listening on port {port}.")
    #create thread
    while True:
        try:
            client,addr = socks.accept()
            sshHoneypotThread = threading.Thread(target=client_handle, args=(client,addr,username,password))
            sshHoneypotThread.start()
        except Exception as error:
            print("ERROR")
            print(error)
#testing
honeypot('127.0.0.1', 2223, 'username', 'password')