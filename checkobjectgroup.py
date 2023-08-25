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
address_groups_from_csv = {}
with open('address_groups.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        address_groups_from_csv[row['GroupName']] = row['Addresses']


# REST API URL
url_prerule = f"https://{fw_host}/restapi/v10.2/Policies/SecurityPreRules?location=device-group&device-group={device_group}"
url_postrule = f"https://{fw_host}/restapi/v10.2/Policies/SecurityPostRules?location=device-group&device-group={device_group}"

# Headers
headers = {
    'X-PAN-KEY': api_key,
}

# Retrieve existing address groups from Panorama
params = {
    'type': 'config',
    'action': 'get',
    'xpath': '/config/shared/address-group',
    'key': api_key
}

url = f"https://{fw_host}/api/"

response = requests.get(url, params=params, verify=False)
root = ET.fromstring(response.content)

address_groups_from_panorama = {}
for entry in root.findall(".//entry"):
    group_name = entry.attrib['name']
    members = entry.find('static')
    if members:
        members_list = [m.text for m in members.findall('member')]
        address_groups_from_panorama[group_name] = members_list

# Compare and add if not exist
for group_name, addresses in address_groups_from_csv.items():
    addresses_list = addresses.split(';')
    if group_name in address_groups_from_panorama:
        if set(addresses_list) == set(address_groups_from_panorama[group_name]):
            print(f"Matched: Group {group_name} with addresses {addresses}")
        else:
            print(f"Group {group_name} exists but with different address members in Panorama!")
    else:
        print(f"Group {group_name} does not exist in Panorama! Creating it...")
        # Create the address group
        members_xml = ''.join([f'<member>{address}</member>' for address in addresses_list])
        creation_params = {
            'type': 'config',
            'action': 'set',
            'xpath': f"/config/shared/address-group/entry[@name='{group_name}']/static",
            'element': members_xml,
            'key': api_key
        }

        creation_response = requests.post(url, params=creation_params, verify=False)
        if "<msg>command succeeded</msg>" in creation_response.text:
            print(f"Successfully created address group {group_name} with members {addresses} in Panorama.")
        else:
            print(f"Failed to create address group {group_name}. Please check the API response and permissions.")