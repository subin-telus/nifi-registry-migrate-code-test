# nifi-registry-flow-migrate
This repository contains the Code for migrating a flow from one Nifi Registry to another.

## Table of Contents
* [Required Structure of flow on Nifi Canvas](#Required-Structure-of-flow-on-Nifi-Canvas)
* [Procedure for Promoting a flow](#Procedure-for-Promoting-a-flow)
* [Flow Diagram of Code](#Flow-Diagram-of-Codes)
* [Notes](#Notes)

## Required Structure of flow on Nifi Canvas
![alt text](/images/accepted_flow_structure_in_canvas.jpg)

The above structure is required for the code to migrate the flow from 1 registry to another.

## Procedure for Promoting a flow

**Branches for Use**
| Branch type | Branch name |
| --- | --- |
| Production | master |
| Development | dev |

A pull of the `dev` branch is required and create a new branch with `feat-<request_id>-<target_env>-<processor_group_name>`. Once the `properties` files are updated, A PR can be raised to merge the contents with the `master` branch.

**Following env codes can be used in feature branch name:**

| Environment name | Short form |
| --- | --- |
| Production | prod |
| Pre Production | preprod |
| Development | dev |

Example, If `processor group = test_processor_group01` has to be promoted from `dev` to `preprod`, then `target_env = preprod` and a request is been raised for the same with `request_id = 1111`, the feature branch name is expected to be: `feat-1111-preprod-test_processor_group01`.

The feature branch needs to be modified with the Properties files, `source.properties` and `target.properties` for the following values:

**For source.properties file**
| Key | Value | Description |
| --- | --- | --- |
| secured_nifi_url | https://<nifi_host>:port | Secured Nifi URL for Source of processor group: test_processor_group01 |
| processor_group | test_processor_group01 | Processor group name which has the flow, that needs to be promoted |

**For target.properties file**
| Key | Value | Description |
| --- | --- | --- |
| secured_nifi_url | https://<nifi_host>:port | Secured Nifi URL for Target of processor group: test_processor_group01 |
| processor_group | test_processor_group01 | Processor group name which has the flow, that needs to be promoted |

## Flow Diagram of Code
![alt text](/images/nifi_flow_migration_diagram.jpg)

## Notes
```
The USERNAME and PASSWORD used for flow migration are added in secrets.
The CA cert file is added to this repository in ca_cert dir.
Make sure self hosted runner is attached to this repository before triggering the migrate scripts.
```
