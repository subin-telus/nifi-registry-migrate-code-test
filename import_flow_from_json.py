#!/usr/bin/python3

import sys
import nipyapi
from nipyapi import versioning
import json
from os.path import exists
import time

# disable TLS check
nipyapi.config.nifi_config.verify_ssl = False
nipyapi.config.registry_config.verify_ssl = False

# Input arguments
preprodNifiurl = sys.argv[1]
preprodprocessorgroupName = sys.argv[2]
export_json_file = sys.argv[3]

# connect to Nifi
preprodNifi = preprodNifiurl + "/nifi"
preprodNifiapi = preprodNifiurl + "/nifi-api"
nipyapi.utils.set_endpoint(preprodNifiapi)

# Check if Nifi up
#nipyapi.security.service_login(service="nifi", username="81285d95-1fbc-4839-929c-e26f652d0c90", password="b14G5O/N0PCrgSjl+538Vur8xQ5thgXJ")
print("\n\t" + "Attepmting to connect to Nifi")
print("\t" + "Pre-Prod Nifi = " + preprodNifi)
print("\t" + "Pre-Prod Nifi API = " + preprodNifiapi)
connected = nipyapi.utils.wait_to_complete(test_function=nipyapi.utils.is_endpoint_up,endpoint_url=preprodNifi,nipyapi_delay=nipyapi.config.long_retry_delay,nipyapi_max_wait=nipyapi.config.short_max_wait)
print("\t" + "Connection to Nifi successful. Proceeding...")

# Get Nifi Registry details from Nifi
reg_clients = nipyapi.versioning.list_registry_clients()
registry_client = None

# Get the first registry client, assuming we have only 1 client registered
for client in reg_clients.registries:
	registry_client = client.component
	break
preprodRegistryurl = registry_client.uri
preprodRegistry = preprodRegistryurl + "/nifi-registry"
preprodRegistryapi = preprodRegistryurl + "/nifi-registry-api"

# Connect to Nifi Registry
nipyapi.utils.set_endpoint(preprodRegistryapi)

# Check if Nifi Registry up
print("\n\t" + "Attepmting to connect to Nifi Registry")
print("\t" + "Pre-Prod Nifi Registry = " + preprodRegistry)
print("\t" + "Pre-Prod Nifi Registry API = " + preprodRegistryapi)
connected = nipyapi.utils.wait_to_complete(test_function=nipyapi.utils.is_endpoint_up,endpoint_url=preprodRegistry,nipyapi_delay=nipyapi.config.long_retry_delay,nipyapi_max_wait=nipyapi.config.short_max_wait)
print("\t" + "Connection to Nifi Registry successful. Proceeding...")

# Load json file from export location
file_exists = exists(export_json_file)
if file_exists is True:
	print("\n\t" + "Attepmting to load file " + export_json_file)
	with open(export_json_file) as json_data:
		import_json = json.load(json_data)
	print("\t" + "Loading JSON file " + export_json_file + "  successful. Proceeding...")
else:
	print("Loading JSON file " + export_json_file + " failed. Exiting...")
	exit(1)

# Get Bucket and Flow names
preprodbucketName = import_json["bucket"]["name"]
preprodFlowName = import_json["flow"]["name"]

# Check if bucket, processor group  exist
print("\n\t" + "Get Bucket details from exported JSON flow")
print("\t" + "Bucket Name = " + preprodbucketName)
# Check if bucket exists
check_bucket_exist = nipyapi.versioning.get_registry_bucket(preprodbucketName)
if check_bucket_exist is None:
	print("\n\t" + "Bucket " + preprodbucketName + " do not exist. Creating...")
	create_bucket = nipyapi.versioning.create_registry_bucket(preprodbucketName)
	check_bucket_exist = nipyapi.versioning.get_registry_bucket(preprodbucketName)
	if check_bucket_exist is None:
		print("\t" + "Cannot create Bucket " + preprodbucketName + ". Exiting...")
		exit(1)
	else:
		print("\t" + "Created Bucket = " + preprodbucketName)
		bucketID = nipyapi.versioning.get_registry_bucket(preprodbucketName).identifier
		print("\t" + "Bucket ID = " + bucketID)
	# Check if Processor Group exists in Nifi Canvas
	print("\n\t" + "Checking if Processor Group " + preprodprocessorgroupName + " available in Nifi")
	check_process_group_canvas = nipyapi.canvas.get_process_group(preprodprocessorgroupName, greedy=False)
	if check_process_group_canvas is not None:
		print("\t" + "Processor group " + preprodprocessorgroupName + " exist on Nifi Canvas, but not in Nifi Registry. Exiting...")
		exit(1)
	else:
		print("\t" + "Processor group " + preprodprocessorgroupName + " do not exist on Nifi Canvas. Proceeding...")
else:
	print("\t" + "Bucket " + preprodbucketName + " exist. Proceeding...")
	# Get bucket ID
	bucketID = nipyapi.versioning.get_registry_bucket(preprodbucketName).identifier
	print("\t" + "Bucket ID = " + bucketID)
	# Check if flow exist
	check_flow = nipyapi.versioning.get_flow_in_bucket(bucketID, preprodFlowName, greedy=False)
	# Check if Processor Group exists in Nifi Canvas
	print("\t" + "Checking if Processor Group " + preprodprocessorgroupName + " available in Nifi")
	check_process_group_canvas = nipyapi.canvas.get_process_group(preprodprocessorgroupName, greedy=False)
	if check_flow is None and check_process_group_canvas is not None:
		print("\t" + "Processor group " + preprodprocessorgroupName + " exist on Nifi Canvas, but not in Nifi Registry. Exiting...")
		exit(1)
	if check_process_group_canvas is not None:
		print("\t" + "Processor Group " + preprodprocessorgroupName + " found. Proceeding...")
		print("\t" + "Checking for any Uncommitted Changes for Processor Group " + preprodprocessorgroupName)
		diff = nipyapi.nifi.apis.process_groups_api.ProcessGroupsApi().get_local_modifications(check_process_group_canvas.id)
		diffn = len(diff.component_differences)
		if check_flow is not None and check_process_group_canvas is not None and diffn > 0:
			print("\t" + "Processor Group " + preprodprocessorgroupName + " has Uncommitted Changes. Exiting...")
			exit(1)
	else:
		print("\t" + "Processor group " + preprodprocessorgroupName + " do not exist on Nifi Canvas. Proceeding...")

# Get root canvas element ID
print("\n\t" + "Getting Root Canvas element ID")
root_processor_group_ID = nipyapi.canvas.get_root_pg_id()
print("\t" + "Root Element ID = " + root_processor_group_ID)

# Check if Flow exists in bucket
print("\n\t" + "Checking if WorkFlow exists in Bucket")
check_flow_exists = nipyapi.versioning.get_flow_in_bucket(bucketID, preprodFlowName)
if check_flow_exists is None:
	print("\t" + "WorkFlow " + preprodFlowName + " not found. Proceeding...")
	# Importing flow from JSON
	print("\n\t" + "Importing WorkFlow into Pre-Prod Nifi Registry")
	import_flow_to_registry = nipyapi.versioning.import_flow_version(bucketID,encoded_flow=None,file_path=export_json_file,flow_name=preprodFlowName,flow_id=None)
	time.sleep(5)
	if import_flow_to_registry is not None:
		print("\t" + "Importing of workflow " + preprodFlowName + " to Pre-Prod Nifi Registry successful. Proceeding...")
		flowID = nipyapi.versioning.get_flow_in_bucket(bucketID, preprodFlowName).identifier
		print("\t" + "WorkFlow ID = " + flowID)
	else:
		print("\t" + "Importing of workflow  " + preprodbucketName + " to Pre-Prod Nifi Registry failed. Exiting...")
		exit(1)
	print("\n\t" + "Importing WorkFlow into Pre-Prod Nifi Canvas")
	import_flow_to_canvas = nipyapi.versioning.deploy_flow_version(parent_id=root_processor_group_ID,location=(0, 0),bucket_id=bucketID,flow_id=flowID,reg_client_id=registry_client.id)
	if import_flow_to_canvas is not None:
		print("\t" + "Importing of workflow " + preprodFlowName + " to Pre-Prod Nifi Canvas successful. Proceeding...")
	else:
		print("\t" + "Importing of workflow  " + preprodbucketName + " to Pre-Prod Nifi Canvas failed. Exiting...")
		exit(1)
else:
	print("\t" + "WorkFlow " + preprodFlowName + " exist. Proceeding...")
	# Updating the flow from JSON
	print("\n\t" + "Updating WorkFlow " + preprodFlowName + " in " + preprodbucketName)
	flowID = nipyapi.versioning.get_flow_in_bucket(bucketID, preprodFlowName).identifier
	print("\t" + "WorkFlow ID = " + flowID)
	update_flow_to_registry = nipyapi.versioning.import_flow_version(bucketID,encoded_flow=None,file_path=export_json_file,flow_name=None,flow_id=flowID)
	time.sleep(5)
	if update_flow_to_registry is not None:
		print("\t" + "Updating workflow " + preprodFlowName + " to Pre-Prod Nifi Registry successful. Proceeding...")
		flowID = nipyapi.versioning.get_flow_in_bucket(bucketID, preprodFlowName).identifier
		print("\t" + "WorkFlow ID = " + flowID)
	else:
		print("\t" + "Updating workflow " + preprodbucketName + " to Pre-Prod Nifi Registry failed. Exiting...")
		exit(1)
	# Check if Nifi Canvas has the processor group
	print("\n\t" + "Checking if Processor Group " + preprodprocessorgroupName + " available in Nifi")
	check_process_group_canvas = nipyapi.canvas.get_process_group(preprodprocessorgroupName, greedy=False)
	if check_process_group_canvas is None:
		print("\t" + "Processor Group " + preprodprocessorgroupName + " not found. Proceeding...")
		print("\t" + "Updating Processor Group " + preprodprocessorgroupName + " from Pre-Prod Nifi Registry")
		import_flow_to_canvas = nipyapi.versioning.deploy_flow_version(parent_id=root_processor_group_ID,location=(0,0),bucket_id=bucketID,flow_id=flowID,reg_client_id=registry_client.id)
	else:
		print("\t" + "Please manually update the Processor Group's Version to latest")
		# Update Work Flow version
		#print("\t" + "Updating WorkFlow " + preprodFlowName  + " Version to Latest")
		#update_flow_ver = nipyapi.versioning.update_flow_ver(check_process_group_canvas)
		#if update_flow_ver is True:
		#	print("\t" + "Updating WorkFlow " + preprodFlowName  + " version successful.")
		#else:
		#	print("\t" + "Updating WorkFlow " + preprodFlowName  + " version Failed. Exiting...")
		#	exit(1)
