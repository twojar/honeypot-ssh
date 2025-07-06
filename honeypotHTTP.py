# LIBRARIES
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for

# CONSTANTS
LOGGING_FORMAT = logging.Formatter('%(asctime)s - %(message)s')

# LOGGING
funnelLogger = logging.getLogger('FunnelLogger')
funnelLogger.setLevel(logging.INFO)
#custom handler to log attacks
funnelHandler = RotatingFileHandler('httpAudits.log', maxBytes=2000, backupCount=5)
funnelHandler.setFormatter(LOGGING_FORMAT)
#add Handler to Logger
funnelLogger.addHandler(funnelHandler)

# BASELINE HONEYPOT
def honeypot_web(input_username="admin", input_password="password"):
    #create Flask instance
    app = Flask(__name__)
    @app.route('/')
    def index():
        return render_template('sample_admin.html')
    @app.route('/login', methods=['POST'])
    def login():
        #get credentials from html file
        username = request.form['username']
        password = request.form['password']
        ip_address = request.remote_addr
        funnelLogger.info(f'Client {ip_address} entered username: {username}, password: {password}')
        if username == input_username and password == input_password:
            return ':3'
        else:
            return "Invalid Credentials. Try Again."
    return app

def run_honeypot_web(port=5000,input_username="admin", input_password="password"):
    run_honeypot_web_app = honeypot_web(input_username, input_password)
    run_honeypot_web_app.run(debug=True, port=port, host="0.0.0.0")
    return run_honeypot_web_app