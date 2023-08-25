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
with open('address_objects.csv', 'r') as csvfile:
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
print(response)

# Parse the XML response
root = ET.fromstring(response.content)

addresses_from_panorama = {}
for entry in root.findall(".//entry"):
    object_name = entry.attrib['name']
    ip_netmask = entry.find('ip-netmask')
    if ip_netmask is not None:
        addresses_from_panorama[object_name] = ip_netmask.text

# Compare and add if not exist or update existing groups
for group_name, addresses_list in address_groups_from_csv.items():
    if group_name in address_groups_from_panorama:
        current_members = address_groups_from_panorama[group_name]
        new_members = [addr for addr in addresses_list if addr not in current_members]
        
        # If there are new members to add
        if new_members:
            for member in new_members:
                member_xml = f"<member>{member}</member>"
                update_params = {
                    'type': 'config',
                    'action': 'set',
                    'xpath': f"/config/shared/address-group/entry[@name='{group_name}']/static",
                    'element': member_xml,
                    'key': api_key
                }
                update_response = requests.post(url, params=update_params, verify=False)
                if "<msg>command succeeded</msg>" in update_response.text:
                    print(f"Successfully added {member} to address group {group_name} in Panorama.")
                else:
                    print(f"Failed to add {member} to address group {group_name}. Please check the API response and permissions.")
        else:
            print(f"Address group {group_name} already has all the addresses from the CSV.")

    else:
        print(f"Address group {group_name} does not exist in Panorama! Creating it...")
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
            print(f"Successfully created address group {group_name} with members {', '.join(addresses_list)} in Panorama.")
        else:
            print(f"Failed to create address group {group_name}. Please check the API response and permissions.")