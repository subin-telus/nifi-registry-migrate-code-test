#!/usr/bin/env bash

### <---- Variables ----> ##
today_date=$(date +%Y-%m-%d)
python_script_export="export_flow_to_json.py"
python_script_import="import_flow_from_json.py"

#-- Dev Variables --#
#
#Get the nifi url from input, expected: "http://192.168.0.2:9090"
dev_nifi_url="$1"
# Get Processor Group from input, expected: "dev-random-generate"
processor_group_name="$2"
workflow_exported_file="/tmp/${processor_group_name}.json"

#-- NonProd Variables --#
#
#Get the nifi url from input, expected: "http://192.168.0.3:9090"
nonprod_nifi_url="$3"


### <---- Main ----> ###
echo -e "\n\n\t\t Migration of ${dev_processor_group_name}. Starting...\n\n"

# Exporting flow to json file
echo -e "[`date --iso-8601=seconds`] - Exporting ${processor_group_name} to JSON:"

if [ -f "${workflow_exported_file}" ]; then
	rm -rf ${workflow_exported_file}
fi

export https_proxy="http://webproxystatic-on.tsl.telus.com:8080"
python3 ${python_script_export} ${dev_nifi_url} ${processor_group_name} ${workflow_exported_file}

laststat=$?
if ([ "${laststat}" == 0 ]) then
	echo -e "\n[`date --iso-8601=seconds`] - Expoting flow to JSON Successful. \n"
else
	echo -e "\n[`date --iso-8601=seconds`] - Expoting flow to JSON Failed."
	echo -e "\n\n\t\t Migration of Flow failed. Exiting...\n\n"
	exit 1;
fi

# Importing flow in another Nifi Registry
#echo -e "[`date --iso-8601=seconds`] - Importing ${processor_group_name} from JSON:\n"
#python3 ${python_script_import} ${nonprod_nifi_url} ${processor_group_name} ${workflow_exported_file}

#laststat=$?
#if ([ "${laststat}" == 0 ]) then
#        echo -e "\n[`date --iso-8601=seconds`] - Importing flow from JSON Successful. Please modify the "Parameter Contexts" or "Variable Registry" as per pre-prod, if used any.\n"
#else
#        echo -e "\n[`date --iso-8601=seconds`] - Importing flow from JSON Failed."
#        echo -e "\n\n\t\t Migration of Flow failed. Exiting...\n\n"
#        exit 1;
#fi

echo -e "\n\n\t\t Migration of Flow completed successfully.\n\n"
