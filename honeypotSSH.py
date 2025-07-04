
# LIBRARIES
import logging
from logging.handlers import RotatingFileHandler
import time
import paramiko

# CONSTANTS
LOGGING_FORMAT =  logging.Formatter('%(message)s')

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
        #fake shell commands
        if char == b'\r':
            if command.strip() == b'exit':
                response = b'\n Goodbye!\n'
                channel.close()
            elif command.strip() == b'pwd':
                response = b'\\user\\local' + b'\r\n'
            elif command.strip() == b'whoami':
                response = b'admin\r\n'
            elif command.strip() == b'ls':
                response = b'\n Documents  Downloads  backup.sh  mysql.sock\r\n'
            elif command.strip() == b'ps aux':
                time.sleep(0.5)
                response = (
                    b'USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\r\n'
                    b'root         1  0.0  0.1  22568  1584 ?        Ss   08:30   0:01 /sbin/init\r\n'
                    b'mysql      203  0.1  1.2 274848 10232 ?       Ssl  08:31   0:03 /usr/sbin/mysqld\r\n'
                    b'admin      512  0.0  0.3  44688  3408 pts/0    Ss   08:35   0:00 bash\r\n'
                )
            elif command.strip() == b'netstat -tulnp':
                time.sleep(0.5)
                response = (
                    b'Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name\r\n'
                    b'tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      203/sshd\r\n'
                    b'tcp6       0      0 :::3306                :::*                    LISTEN      312/mysqld\r\n'
                )
            elif command.strip() == b'ifconfig' or command.strip() == b'ip a':
                time.sleep(0.5)
                response = (
                    b'eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500\r\n'
                    b'        inet 192.168.1.24  netmask 255.255.255.0  broadcast 192.168.1.255\r\n'
                    b'        inet6 fe80::a00:27ff:fe4e:66a1  prefixlen 64  scopeid 0x20<link>\r\n'
                )
            elif command.strip().startswith(b'cat '):
                response = b'Permission denied\r\n'
            else:
                response = b'bash: ' + command.strip() + b': command not found\r\n'
        #listen for next command
        channel.send(response)
        channel.send(b'[admin@prod-db01 ~]$ ')
        command = b""

# SSH SERVER
class Server(paramiko.ServerInterface):
    def __init__(self,client_ip, input_username=None, input_password=None):
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
        if self.input_username is not None and self.input_password is not None:
            if username == 'username' and password == 'password':
                return paramiko.common.AUTH_SUCCESSFUL
            else:
                return paramiko.common.AUTH_FAILED
        else:
            return paramiko.common.AUTH_FAILED
    def check_channel_shell_request(self,channel):
        self.event.set()
        return True
    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
        return True
    def check_channel_exec_request(self, channel, command):
        command = str(command)
        return True

