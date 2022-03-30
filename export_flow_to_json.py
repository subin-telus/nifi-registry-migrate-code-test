#!/usr/bin/python3

import sys
import nipyapi
import json


# disable TLS check
nipyapi.config.nifi_config.verify_ssl = False
nipyapi.config.registry_config.verify_ssl = False

# Input arguments
devNifiurl = sys.argv[1]
devprocessorgroupName = sys.argv[2]
export_json_file = sys.argv[3]

# connect to Nifi
devNifi = devNifiurl + "/nifi"
devNifiapi = devNifiurl + "/nifi-api"
nipyapi.utils.set_endpoint(devNifiapi)

# Check if Nifi up
#nipyapi.security.service_login(service="nifi", username="81285d95-1fbc-4839-929c-e26f652d0c90", password="b14G5O/N0PCrgSjl+538Vur8xQ5thgXJ")
print("\n\t" + "Attepmting to connect to Nifi")
print("\t" + "Dev Nifi = " + devNifi)
print("\t" + "Dev Nifi API = " + devNifiapi)
connected = nipyapi.utils.wait_to_complete(test_function=nipyapi.utils.is_endpoint_up,endpoint_url=devNifi,nipyapi_delay=nipyapi.config.long_retry_delay,nipyapi_max_wait=nipyapi.config.short_max_wait)
print("\t" + "Connection to Nifi successful. Proceeding...")

# Check Process Group on the Canvas
print("\n\t" + "Checking if Processor Group " + devprocessorgroupName + " available in Nifi")
processor_group = nipyapi.canvas.get_process_group(devprocessorgroupName, greedy=False)
if processor_group is None:
	print("\t" + "Processor Group " + devprocessorgroupName + " not found. Exiting...")
	exit(1)
else:
	print("\t" + "Processor Group " + devprocessorgroupName + " found. Proceeding...")

# Check if any uncommitted changes on the Canvas
print("\n\t" + "Checking for any Uncommitted Changes for Processor Group " + devprocessorgroupName)
diff = nipyapi.nifi.apis.process_groups_api.ProcessGroupsApi().get_local_modifications(processor_group.id)
diffn = len(diff.component_differences)
if diffn > 0:
	print("\t" + "Processor Group " + devprocessorgroupName + " has Uncommitted Changes. Exiting...")
	exit(1)
else:
	print("\t" + "Processor Group " + devprocessorgroupName + " has no Uncommitted Changes. Proceeding...")

# Get Nifi Registry details from Nifi
reg_clients = nipyapi.versioning.list_registry_clients()
registry_client = None

# Get the first registry client, assuming we have only 1 client registered
for client in reg_clients.registries:
	registry_client = client.component
	break
devRegistryurl = registry_client.uri
devRegistry = devRegistryurl + "/nifi-registry"
devRegistryapi = devRegistryurl + "/nifi-registry-api"

# Connect to Nifi Registry
nipyapi.utils.set_endpoint(devRegistryapi)

# Check if Nifi Registry up
print("\n\t" + "Attepmting to connect to Nifi Registry")
print("\t" + "Dev Nifi Registry = " + devRegistry)
print("\t" + "Dev Nifi Registry API = " + devRegistryapi)
connected = nipyapi.utils.wait_to_complete(test_function=nipyapi.utils.is_endpoint_up,endpoint_url=devRegistry,nipyapi_delay=nipyapi.config.long_retry_delay,nipyapi_max_wait=nipyapi.config.short_max_wait)
print("\t" + "Connection to Nifi Registry successful. Proceeding...")

# Check Process Group in the Registry
print("\n\t" + "Checking if Processor Group " + devprocessorgroupName + " available in Nifi Registry")
processor_group_registry = processor_group.component.version_control_information
if processor_group_registry is None:
	print("\t" + "Processor Group " + devprocessorgroupName + " not found. Exiting...")
	exit(1)
else:
	print("\t" + "Processor Group " + devprocessorgroupName + " found. Proceeding...")

# Get the bucket ID for export
print("\n\t" + "Getting Bucket Details of " + devprocessorgroupName + " for export")
devbucketName = processor_group.component.version_control_information.bucket_name
print("\t" + "Bucket Name = " + devbucketName)
devbucketID = processor_group.component.version_control_information.bucket_id
print("\t" + "Bucket ID = " + devbucketID)

# Get the workflow ID for export
print("\n\t" + "Getting workflow Details of " + devprocessorgroupName + " for export")
devworkflowName = processor_group.component.version_control_information.flow_name
print("\t" + "WorkFlow Name = " + devworkflowName)
devworkflowID = processor_group.component.version_control_information.flow_id
print("\t" + "WorkFlow ID = " + devworkflowID)

# Export the flow to a json file
print("\n\t" + "Exporting workflow: " + devworkflowName + " to JSON file" )
nipyapi.versioning.export_flow_version(devbucketID, devworkflowID, version=None, file_path=export_json_file, mode='json')
print("\t" + "Exported WorkFlow = " + export_json_file)
