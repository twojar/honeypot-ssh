# LIBRARIES
import streamlit as st
import pandas as pd
import re
st.title("Honeypot Dashboard")

#load data from audit files into structure
@st.cache_data
def load_audits():
    with open("audits.log", "r") as f:
        lines = f.readlines()
    data = []
    pattern = r"Client ([\d\.]+) attempted connection with username: (\S+), password: (\S+)"
    for line in lines:
        match = re.search(pattern,line)
        if match:
            ip,username,password = match.groups()
            data.append({"ip": ip, "username": username, "password": password})
    return pd.DataFrame(data)

@st.cache_data
def load_cmd_audits():
    with open("cmdAudits.log", "r") as f:
        lines = f.readlines()
    cmd_data = []
    pattern = r"Command b'(.*?)' executed by ([\d\.]+)"
    for line in lines:
        match = re.search(pattern,line)
        if match:
            command,ip = match.groups()
            cmd_data.append({"command": command, "ip": ip})
    return pd.DataFrame(cmd_data)

#load data frames
df_audits = load_audits()
df_cmd_audits = load_cmd_audits()

#display login attempts
st.subheader("Top IPs")
st.bar_chart(df_audits['ip'].value_counts().head(10))

#display most executed commands
st.subheader("Most Executed Commands")
st.bar_chart(df_cmd_audits['command'].value_counts().head(10))

#show logs
st.subheader("CMD Logs")
st.dataframe(df_cmd_audits.tail(20))

st.subheader("IP Logs")
st.dataframe(df_audits.tail(20))






