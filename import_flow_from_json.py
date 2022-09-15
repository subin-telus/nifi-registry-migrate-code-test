#!/usr/bin/python3

import sys
import nipyapi
import json
import os
import time
import logging
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
with open('pre_prod.properties', 'rb') as config_file:
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
export_json_file = connect_properties.get("workflow_import_file").data

# Nifi
Nifi = Nifiurl + "/nifi"
Nifiapi = Nifiurl + "/nifi-api"

# Check if Nifi up
print("\n" + "Attepmting to connect to Nifi")
print("Pre-Prod Nifi = " + Nifi)
print("Pre-Prod Nifi API = " + Nifiapi + "\n")
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
nifi_status = nipyapi.security.get_service_access_status(service='nifi').access_status
print("\n" + "Nifi Connection Status:")
print(nifi_status)
#print('nipyapi_secured_nifi CurrentUser: ' + nifi_user.access_status.identity)

# Get Nifi Registry details from Nifi
reg_clients = nipyapi.versioning.list_registry_clients()
registry_client = None

# Get the first registry client, assuming we have only 1 client registered
for client in reg_clients.registries:
	registry_client = client.component
	break

# Registry
Registryurl = registry_client.uri
Registry = Registryurl + "/nifi-registry"
Registryapi = Registryurl + "/nifi-registry-api"

# Check if Nifi Registry up
print("\n" + "Attepmting to connect to Nifi Registry")
print("Pre-Prod Nifi Registry = " + Registry)
print("Pre-Prod Nifi Registry API = " + Registryapi + "\n")
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
registry_status = nipyapi.security.get_service_access_status(service='registry').identity
print("\n" + "Registry Connected User: " + registry_status)

# Load json file from export location
file_exists = os.path.exists(export_json_file)
if file_exists is True:
	print("\n" + "Attepmting to load file " + export_json_file)
	with open(export_json_file) as json_data:
		import_json = json.load(json_data)
	print("Loading JSON file " + export_json_file + "  successful. Proceeding...")
else:
	print("Loading JSON file " + export_json_file + " failed. Exiting...")
	exit(1)

# Get Bucket and Flow names
bucketName = import_json["bucket"]["name"]
FlowName = import_json["flow"]["name"]

# Fallback function to delete on exit commands, if anything created!
created = {'is_bucket_created':'nill', 'is_processor_group_created':'nill'}
def fall_back(**created):
	if created['is_bucket_created'] != 'nill':
		delete_bucket = nipyapi.versioning.delete_registry_bucket(created['is_bucket_created']).name
		print("Deleted bucket: " + delete_bucket + "\n")

# Check if bucket, processor group  exist
print("\n" + "Get Bucket details from exported JSON flow")
print("Bucket Name = " + bucketName)
# Check if bucket exists
check_bucket_exist = nipyapi.versioning.get_registry_bucket(bucketName)
bucket_created = 'nill'
if check_bucket_exist is None:
	print("\n" + "Bucket " + bucketName + " do not exist. Creating...")
	create_bucket = nipyapi.versioning.create_registry_bucket(bucketName)
	check_bucket_exist = nipyapi.versioning.get_registry_bucket(bucketName)
	if check_bucket_exist is None:
		print("Cannot create Bucket " + bucketName + ". Exiting...")
		exit(1)
	else:
		print("Created Bucket = " + bucketName)
		bucketID = nipyapi.versioning.get_registry_bucket(bucketName).identifier
		print("Bucket ID = " + bucketID)
		bucket_created = check_bucket_exist
	# Check if Processor Group exists in Nifi Canvas
	print("\n" + "Checking if Processor Group " + processorgroupName + " available in Nifi")
	check_process_group_canvas = nipyapi.canvas.get_process_group(
		processorgroupName, 
		greedy=False
	)
	if check_process_group_canvas is not None:
		print("Processor group " + processorgroupName + " exist on Nifi Canvas, but not in Nifi Registry. Exiting...")
		created = {'is_bucket_created':bucket_created, 'is_processor_group_created':'nill'}
		fall_back(**created)
		exit(1)
	else:
		print("Processor group " + processorgroupName + " do not exist on Nifi Canvas. Proceeding...")
else:
	print("Bucket " + bucketName + " exist. Proceeding...")
	# Get bucket ID
	bucketID = nipyapi.versioning.get_registry_bucket(bucketName).identifier
	print("Bucket ID = " + bucketID)
	# Check if flow exist
	check_flow = nipyapi.versioning.get_flow_in_bucket(
		bucketID, 
		FlowName, 
		greedy=False
	)
	# Check if Processor Group exists in Nifi Canvas
	print("Checking if Processor Group " + processorgroupName + " available in Nifi")
	check_process_group_canvas = nipyapi.canvas.get_process_group(
		processorgroupName, 
		greedy=False
	)
	if check_flow is None and check_process_group_canvas is not None:
		print("Processor group " + processorgroupName + " exist on Nifi Canvas, but not in Nifi Registry. Exiting...")
		exit(1)
	if check_process_group_canvas is not None:
		print("Processor Group " + processorgroupName + " found. Proceeding...")
		print("Checking for any Uncommitted Changes for Processor Group " + processorgroupName)
		diff = nipyapi.nifi.apis.process_groups_api.ProcessGroupsApi().get_local_modifications(check_process_group_canvas.id)
		diffn = len(diff.component_differences)
		if check_flow is not None and check_process_group_canvas is not None and diffn > 0:
			print("Processor Group " + processorgroupName + " has Uncommitted Changes. Exiting...")
			exit(1)
	else:
		print("\t" + "Processor group " + processorgroupName + " do not exist on Nifi Canvas. Proceeding...")

# Get root canvas element ID
print("\n" + "Getting Root Canvas element ID")
root_processor_group_ID = nipyapi.canvas.get_root_pg_id()
print("Root Element ID = " + root_processor_group_ID)

# Check if Flow exists in bucket
print("\n" + "Checking if WorkFlow exists in Bucket")
check_flow_exists = nipyapi.versioning.get_flow_in_bucket(
	bucketID, 
	FlowName
)
if check_flow_exists is None:
	print("WorkFlow " + FlowName + " not found. Proceeding...")
	# Importing flow from JSON
	print("\n" + "Importing WorkFlow into Pre-Prod Nifi Registry")
	import_flow_to_registry = nipyapi.versioning.import_flow_version(
		bucketID, 
		encoded_flow=None, 
		file_path=export_json_file, 
		flow_name=FlowName, 
		flow_id=None
	)
	time.sleep(5)
	if import_flow_to_registry is not None:
		print("Importing of workflow " + FlowName + " to Pre-Prod Nifi Registry successful. Proceeding...")
		flowID = nipyapi.versioning.get_flow_in_bucket(bucketID, FlowName).identifier
		print("WorkFlow ID = " + flowID)
	else:
		print("Importing of workflow  " + FlowName + " to Pre-Prod Nifi Registry failed. Exiting...")
		created = {'is_bucket_created':bucket_created, 'is_processor_group_created':'nill'}
		fall_back(**created)
		exit(1)
	print("\n" + "Importing WorkFlow into Pre-Prod Nifi Canvas")
	import_flow_to_canvas = nipyapi.versioning.deploy_flow_version(
		parent_id=root_processor_group_ID, 
		location=(0, 0), 
		bucket_id=bucketID, 
		flow_id=flowID, 
		reg_client_id=registry_client.id
	)
	if import_flow_to_canvas is not None:
		print("Importing of workflow " + FlowName + " to Pre-Prod Nifi Canvas successful." + "\n")
	else:
		print("Importing of workflow  " + FlowName +  " to Pre-Prod Nifi Canvas failed. Exiting...")
		created = {'is_bucket_created':bucket_created, 'is_processor_group_created':'nill'}
		fall_back(**created)
		exit(1)
else:
	print("WorkFlow " + FlowName + " exist. Proceeding...")
	# Updating the flow from JSON
	print("\n" + "Updating WorkFlow " + FlowName + " in " + bucketName)
	flowID = nipyapi.versioning.get_flow_in_bucket(bucketID, FlowName).identifier
	print("WorkFlow ID = " + flowID)
	update_flow_to_registry = nipyapi.versioning.import_flow_version(
		bucketID, 
		encoded_flow=None, 
		file_path=export_json_file, 
		flow_name=None, 
		flow_id=flowID
	)
	time.sleep(5)
	if update_flow_to_registry is not None:
		print("Updating workflow " + FlowName + " to Pre-Prod Nifi Registry successful. Proceeding...")
		flowID = nipyapi.versioning.get_flow_in_bucket(bucketID, FlowName).identifier
		print("WorkFlow ID = " + flowID)
	else:
		print("Updating workflow " + FlowName + " to Pre-Prod Nifi Registry failed. Exiting...")
		exit(1)
	# Check if Nifi Canvas has the processor group
	print("\n" + "Checking if Processor Group " + processorgroupName + " available in Nifi")
	check_process_group_canvas = nipyapi.canvas.get_process_group(
		processorgroupName, 
		greedy=False
	)
	if check_process_group_canvas is None:
		print("Processor Group " + processorgroupName + " not found. Proceeding...")
		print("Creating Processor Group " + processorgroupName + " and importing flow " + FlowName + " to pre-prod Nifi")
		import_flow_to_canvas = nipyapi.versioning.deploy_flow_version(
			parent_id=root_processor_group_ID, 
			location=(0,0), 
			bucket_id=bucketID, 
			flow_id=flowID, 
			reg_client_id=registry_client.id
		)
		print("Created Processor Group " + processorgroupName + " and imported flow " + FlowName + " to pre-prod Nifi")
		print("\n")
	else:
		# Update Work Flow version
		print("Processor Group " + processorgroupName + " available in Nifi")
		print("Updating WorkFlow " + FlowName  + " Version to Latest")
		update_flow_ver = nipyapi.versioning.update_flow_ver(check_process_group_canvas).request.complete
		if update_flow_ver is True:
			print("Updating WorkFlow " + FlowName  + " version successful.")
			print("\n")
		else:
			print("Updating WorkFlow " + FlowName  + " version, Failed. Exiting...")
			print("Please manually update the Processor Group's Version to latest")
			exit(1)
			print("\n")
