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



# Read address groups from CSV into a dictionary
address_groups_from_csv = {}
with open('address_groups.csv', 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        group_name = row['GroupName']
        addresses = row['Addresses']
        expanded_addresses = addresses.split(';')  # This handles multiple addresses separated by semicolons
        
        # If the group name already exists in the dictionary, extend the list. Otherwise, create a new entry.
        if group_name in address_groups_from_csv:
            address_groups_from_csv[group_name].extend(expanded_addresses)
        else:
            address_groups_from_csv[group_name] = expanded_addresses


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