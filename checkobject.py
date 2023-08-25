from netaddr import IPNetwork, cidr_merge
import requests
import xml.etree.ElementTree as ET
import json
import urllib3
import re
import os
import csv
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv('PAN_API_KEY')
device_group = os.getenv('DEVICE_GROUP')
fw_host = os.getenv("FW_HOST")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print(f"Device Group: {device_group}")
print(f"Hostname: {fw_host}")



# Read addresses from CSV into a dictionary
addresses_from_csv = {}
with open('shared_objects.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        addresses_from_csv[row['Name']] = row['Address']


# REST API URL
url_prerule = f"https://{fw_host}/restapi/v10.2/Policies/SecurityPreRules?location=device-group&device-group={device_group}"
url_postrule = f"https://{fw_host}/restapi/v10.2/Policies/SecurityPostRules?location=device-group&device-group={device_group}"

# Headers
headers = {
    'X-PAN-KEY': api_key,
}

# Define the parameters for showing objects
params = {
    'type': 'config',
    'action': 'get',
    'xpath': '/config/shared/address',  # Example: to fetch all address objects
    'key': api_key
}

url = f"https://{fw_host}/api/"

# Make the API request
response = requests.get(url, params=params, verify=False)  # Setting verify to False if you want to skip SSL verification

# Parse the XML response
root = ET.fromstring(response.content)

addresses_from_panorama = {}
for entry in root.findall(".//entry"):
    object_name = entry.attrib['name']
    ip_netmask = entry.find('ip-netmask')
    if ip_netmask is not None:
        addresses_from_panorama[object_name] = ip_netmask.text

# Compare and add if not exist
for name, address in addresses_from_csv.items():
    if name in addresses_from_panorama:
        if addresses_from_csv[name] == addresses_from_panorama[name]:
            print(f"Matched: {name} with address {address}")
        else:
            print(f"Name {name} exists but with a different address in Panorama!")
    else:
        print(f"Name {name} does not exist in Panorama! Creating it...")
        # Create the address object
        creation_params = {
            'type': 'config',
            'action': 'set',
            'xpath': f"/config/shared/address/entry[@name='{name}']",
            'element': f"<ip-netmask>{address}</ip-netmask>",
            'key': api_key
        }

        creation_response = requests.post(url, params=creation_params, verify=False)

        if "<msg>command succeeded</msg>" in creation_response.text:
            print(f"Successfully created address {name} with IP {address} in Panorama.")
        else:
            print(f"Failed to create address {name}. Please check the API response and permissions.")
