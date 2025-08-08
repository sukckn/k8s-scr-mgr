
![pull-scr logo]

# pull-scr
Service container for SAS Viya to load SAS Container Runtime (SCR) images into Kubernetes.
This service container is intended to support developers during the development phase when decision flows, or models are published to a Docker Registry and loaded into Kubernetes. It is not always possible that developers have access to the server to load a decision flow or model into Kubernetes when it is published to a Docker Registry.

The pull-scr container is getting loaded into Kubernetes and offers a service through a custom step in SAS Studio to:
* Load a SCR image into Kubernetes
* Restart launched SCR containers
* Delete the deployment of a SCR container
* Show a list of all pod that run in a dedicated namespace in Kubernetes

For security reasons all SCR containers will get loaded into the same dedicated namespace in Kubernetes.

## Installation

To install the pull-scr service container follow the steps below.
