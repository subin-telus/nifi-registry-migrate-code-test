#!/usr/bin/python3

import sys
import nipyapi
import json
import logging
import os
import jproperties
from jproperties import Properties

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
logging.getLogger('nipyapi.utils').setLevel(logging.INFO)
logging.getLogger('nipyapi.security').setLevel(logging.INFO)
logging.getLogger('nipyapi.versioning').setLevel(logging.INFO)
logging.getLogger('nipyapi.config').setLevel(logging.INFO)
logging.getLogger('nipyapi.canvas').setLevel(logging.INFO)

# Importing Input values from dev.properties
connect_properties = Properties()
with open('dev.properties', 'rb') as config_file:
	connect_properties.load(config_file)


# Enable TLS check
nipyapi.config.nifi_config.verify_ssl = True
nipyapi.config.registry_config.verify_ssl = True

# Input arguments
Nifiurl = connect_properties.get("secured_nifi_url").data
processorgroupName = connect_properties.get("processor_group").data 
ca_file = connect_properties.get("cafile").data
#ldap_user = connect_properties.get("username").data
ldap_user = os.environ['USERNAME']
#ldap_password = connect_properties.get("password").data
ldap_password = os.environ['PASSWORD']
export_json_file = connect_properties.get("workflow_export_file").data

# Check if exported json file already present
if os.path.exists(export_json_file):
	os.remove(export_json_file)

# Nifi
Nifi = Nifiurl + "/nifi"
Nifiapi = Nifiurl + "/nifi-api"

# Check if Nifi up
print("\n" + "Attepmting to connect to Nifi")
print("Dev Nifi = " + Nifi)
print("Dev Nifi API = " + Nifiapi + "\n")
nipyapi.utils.set_endpoint(Nifiapi)

# Setting SSL context
nipyapi.security.set_service_ssl_context(
    service='nifi',
    ca_file=ca_file
)

# Test Connection
connected = nipyapi.utils.wait_to_complete(
    test_function=nipyapi.security.service_login,
    service='nifi',
    username=ldap_user,
    password=ldap_password,
    bool_response=True,
    nipyapi_delay=nipyapi.config.long_retry_delay,
    nipyapi_max_wait=nipyapi.config.long_max_wait
)
print("\nConnection to Nifi successful. Proceeding...\n")
nifi_status = nipyapi.security.get_service_access_status(service='nifi')
print("\n" + "Nifi Connection Status:")
print(nifi_status)

#print('nipyapi_secured_nifi CurrentUser: ' + nifi_user.access_status.identity)

# Check Process Group on the Canvas
print("\n" + "Checking if Processor Group " + processorgroupName + " available in Nifi")
processor_group = nipyapi.canvas.get_process_group(
	processorgroupName, 
	greedy=False
)
if processor_group is None:
	print("Processor Group " + processorgroupName + " not found. Exiting...")
	exit(1)
else:
	print("Processor Group " + processorgroupName + " found. Proceeding...")

# Check if any uncommitted changes on the Canvas
print("\n" + "Checking for any Uncommitted Changes for Processor Group " + processorgroupName)
diff = nipyapi.nifi.apis.process_groups_api.ProcessGroupsApi().get_local_modifications(processor_group.id)
diffn = len(diff.component_differences)
if diffn > 0:
	print("Processor Group " + processorgroupName + " has Uncommitted Changes. Exiting...")
	exit(1)
else:
	print("Processor Group " + processorgroupName + " has no Uncommitted Changes. Proceeding...")

# Get Nifi Registry details from Nifi
reg_clients = nipyapi.versioning.list_registry_clients()
registry_client = None

# Get the first registry client, assuming we have only 1 client registered
for client in reg_clients.registries:
	registry_client = client.component
	break

# Nifi Registry
Registryurl = registry_client.uri
Registry = Registryurl + "/nifi-registry"
Registryapi = Registryurl + "/nifi-registry-api"

# Check if Nifi Registry up
print("\n" + "Attepmting to connect to Nifi Registry")
print("Dev Nifi Registry = " + Registry)
print("Dev Nifi Registry API = " + Registryapi + "\n")
nipyapi.utils.set_endpoint(Registryapi)

# Setting SSL context
nipyapi.security.set_service_ssl_context(
	service='registry',
	ca_file=ca_file
)

# Test Connection
connected = nipyapi.utils.wait_to_complete(
    test_function=nipyapi.security.service_login,
    service='registry',
    username=ldap_user,
    password=ldap_password,
    bool_response=True,
    nipyapi_delay=nipyapi.config.long_retry_delay,
    nipyapi_max_wait=nipyapi.config.long_max_wait
)
print("\nConnection to Nifi Registry successful. Proceeding...\n")
registry_status = nipyapi.security.get_service_access_status(service='registry')
print("\n" + "Registry Connection Status:")
print(registry_status)

# Check Process Group in the Registry
print("\n" + "Checking if Processor Group " + processorgroupName + " available in Nifi Registry")
processor_group_registry = processor_group.component.version_control_information
if processor_group_registry is None:
	print("Processor Group " + processorgroupName + " not found. Exiting...")
	exit(1)
else:
	print("Processor Group " + processorgroupName + " found. Proceeding...")

# Get the bucket ID for export
print("\n" + "Getting Bucket Details of " + processorgroupName + " for export")
bucketName = processor_group.component.version_control_information.bucket_name
print("Bucket Name = " + bucketName)
bucketID = processor_group.component.version_control_information.bucket_id
print("Bucket ID = " + bucketID)

# Get the workflow ID for export
print("\n" + "Getting workflow Details of " + processorgroupName + " for export")
workflowName = processor_group.component.version_control_information.flow_name
print("WorkFlow Name = " + workflowName)
workflowID = processor_group.component.version_control_information.flow_id
print("WorkFlow ID = " + workflowID)

# Export the flow to a json file
print("\n" + "Exporting workflow: " + workflowName + " to JSON file" )
nipyapi.versioning.export_flow_version(
	bucketID, 
	workflowID, 
	version=None, 
	file_path=export_json_file, 
	mode='json'
)
print("Exported WorkFlow = " + export_json_file + "\n")
