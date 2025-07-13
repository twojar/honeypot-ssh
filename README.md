                                              
# SSH (Super Simple Honeypot)

*Not to be confused with SSH (Secure Shell)*  
**Contributors:** [@2jar](https://github.com/2jar) and [@Raforawesome](https://github.com/Raforawesome)
```
  ______   __    __  _______   ________  _______                                 
 /      \ |  \  |  \|       \ |        \|       \                                
|  $$$$$$\| $$  | $$| $$$$$$$\| $$$$$$$$| $$$$$$$\                               
| $$___\$$| $$  | $$| $$__/ $$| $$__    | $$__| $$                               
 \$$    \ | $$  | $$| $$    $$| $$  \   | $$    $$                               
 _\$$$$$$\| $$  | $$| $$$$$$$ | $$$$$   | $$$$$$$\                               
|  \__| $$| $$__/ $$| $$      | $$_____ | $$  | $$                               
 \$$    $$ \$$    $$| $$      | $$     \| $$  | $$                               
  \$$$$$$   \$$$$$$  \$$       \$$$$$$$$ \$$   \$$                               
                                                                                 
                                                                                 
                                                                                 
  ______   ______  __       __  _______   __        ________                     
 /      \ |      \|  \     /  \|       \ |  \      |        \                    
|  $$$$$$\ \$$$$$$| $$\   /  $$| $$$$$$$\| $$      | $$$$$$$$                    
| $$___\$$  | $$  | $$$\ /  $$$| $$__/ $$| $$      | $$__                        
 \$$    \   | $$  | $$$$\  $$$$| $$    $$| $$      | $$  \                       
 _\$$$$$$\  | $$  | $$\$$ $$ $$| $$$$$$$ | $$      | $$$$$                       
|  \__| $$ _| $$_ | $$ \$$$| $$| $$      | $$_____ | $$_____                     
 \$$    $$|   $$ \| $$  \$ | $$| $$      | $$     \| $$     \                    
  \$$$$$$  \$$$$$$ \$$      \$$ \$$       \$$$$$$$$ \$$$$$$$$                    
                                                                                 
                                                                                 
                                                                                 
 __    __   ______   __    __  ________  __      __  _______    ______  ________ 
|  \  |  \ /      \ |  \  |  \|        \|  \    /  \|       \  /      \|        \
| $$  | $$|  $$$$$$\| $$\ | $$| $$$$$$$$ \$$\  /  $$| $$$$$$$\|  $$$$$$\\$$$$$$$$
| $$__| $$| $$  | $$| $$$\| $$| $$__      \$$\/  $$ | $$__/ $$| $$  | $$  | $$   
| $$    $$| $$  | $$| $$$$\ $$| $$  \      \$$  $$  | $$    $$| $$  | $$  | $$   
| $$$$$$$$| $$  | $$| $$\$$ $$| $$$$$       \$$$$   | $$$$$$$ | $$  | $$  | $$   
| $$  | $$| $$__/ $$| $$ \$$$$| $$_____     | $$    | $$      | $$__/ $$  | $$   
| $$  | $$ \$$    $$| $$  \$$$| $$     \    | $$    | $$       \$$    $$  | $$   
 \$$   \$$  \$$$$$$  \$$   \$$ \$$$$$$$$     \$$     \$$        \$$$$$$    \$$   
                                                                                 
                                                                                 
                                                                                 
```     
---

## What is SSH (Super Simple Honeypot)?

Couldn't decide on a name, so let’s call it SSH: **Super Simple Honeypot** — a Python-based, dual-protocol honeypot designed to emulate both SSH and HTTP attack surfaces.

This project simulates a realistic Linux environment and fake login portal to log unauthorized access attempts, study attacker behavior, and visualize results in real time. Built for educational, research, or defensive security monitoring purposes. It is deployable on a VPS, light, modular (somewhat), and easy to extend and modify.

---

## Features

### SSH Honeypot
- Simulates an interactive Linux shell over SSH using `Paramiko`
- Captures and logs:
  - Login attempts (IP, username, password)
  - Attacker shell commands
  - Session disconnects
- Emulates commands like `ls`, `whoami`, `cat`, `ps aux`, `netstat`, `ifconfig`, etc.
- Uses realistic fake banners, prompts, and file permission traps

### HTTP Honeypot
- Fake login form using `Flask`
- Logs submitted credentials with IP and timestamp

### Streamlit Dashboard
- Visualizes:
  - Top IPs attempting login
  - Most executed commands
  - Recent login attempts and command logs
- Built with `pandas` and `Streamlit` for real-time updates

---

## How to use
### 1. Clone and Setup
```bash
git clone https://github.com/twojar/honeypot-ssh.git
cd honeypot-ssh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
### 2. Generate RSA key
```bash 
ssh-keygen -t rsa -b 2048 -f server.key
```
### 3. Run the Honeypot 
- Note: If username and password arguments are left blank, login will always work no matter what credentials are entered.
#### SSH Honeypot:
``` python
python3 main.py -a 0.0.0.0 -p 2224 -u root -pw password --ssh
```
#### HTTP Honeypot:
``` python
python3 main.py -a 0.0.0.0 -p 5000 -u admin -pw admin --http
```
### 4. Launch the Dashboard
```python
steamlit run dashboard.py
```
### Extras:
- When running on VPS, use ```ufw``` to open ports:
- Choose a port greater than ```1024```
```bash
sudo ufw allow 2224/tcp
sudo ufw allow 5000/tcp
ufw status
```
