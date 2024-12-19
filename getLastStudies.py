import requests
import paramiko
from datetime import datetime
from datetime import timedelta
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(message)s",
    datefmt="%Y-%m-%d",
    filename="db_dates.log",
)


session = paramiko.SSHClient()
session.load_system_host_keys()
session.set_missing_host_key_policy(paramiko.AutoAddPolicy())
key_location = os.getenv("KEYLOCATION")
keyfile = paramiko.RSAKey.from_private_key_file(key_location)

session.connect(hostname=os.getenv("HOST"), username=os.getenv("USER"), pkey=keyfile)

today = datetime.today().strftime("%Y-%m-%d")
networks = ["ACN", "CALVARY"]
this_year = (datetime.today() + timedelta(days=365)).strftime("%Y")


for network in networks:
    # Get last uploaded date
    r = requests.get(
        f"https://api.applywithinradio.com/v1/{network}/{today}?end_date={this_year}-12-31"
    )
    response = r.json()
    logging.warning(f"{network}: " + response[0]["airdate"])


ftp = session.open_sftp()
ftp.put("db_dates.log", "/share/db_dates.log")
ftp.close()

session.close()
