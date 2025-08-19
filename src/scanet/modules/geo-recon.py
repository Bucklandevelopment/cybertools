import sys
import requests
import json
from colorama import Fore, Back, Style
import os
from modules.commands import command
from modules.commands import listCommand
from modules.helps import help
from modules.welcome import welcome
from modules.getData import getGeo
from modules.checkIp import check
from modules.nmapVerify import verify
from modules.myip import myIp
import io

def get_osint(ip):
    # Create a string buffer to capture the output
    output_buffer = io.StringIO()
    sys.stdout = output_buffer

    # Verify if the user has nmap, if not it will install automatic
    verify()

    if ip == 'localhost':
        ip = myIp()

    getGeo(ip)
    check(ip)

    # Restore stdout
    sys.stdout = sys.__stdout__

    return output_buffer.getvalue()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        ip = sys.argv[1]
        print(get_osint(ip))
    else:
        print("Please provide an IP address.")
