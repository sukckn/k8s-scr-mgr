![pull-scr logo](./images/pull-scr%20logo.png)

# `pull-scr`: Service Container for SAS Viya SCR Images
`pull-scr` is a service container designed to support developers working with SAS Viya by enabling the loading of SAS Container Runtime (SCR) images into Kubernetes. This tool is especially useful during the development phase when decision flows or models are published to a Docker Registry but developers may not have direct access to the Kubernetes cluster.

## Features
Once deployed, the `pull-scr` container provides a service accessible via custom step *ID - Deploy SCR* in SAS Studio to:

- **Load** SCR images into Kubernetes
- **Restart** launched SCR containers
- **Delete** SCR container deployments
- **List** all pods running in a dedicated Kubernetes namespace

> ⚠️ For security reasons, all SCR containers are loaded into a **single dedicated namespace**.
---

## Installation Guide
> :exclamation:**Note**: By default *pull-scr* will be installed into namespace ```default```. The default namespace to load the scr containers is ```scr```. Both namespaces can be changed if necessary.

### Create a Dedicated Namespace
`pull-scr` operates within a single Kubernetes namespace per instance. If you require multiple namespaces, you must deploy separate instances of `pull-scr`.

If you don't have a dedicated namespace yet, you need to create one. The default namespace to load the scr images is ```scr```. To create a namespace `scr`, run:

```
kubectl create namespace scr
```

### Creating ConfigMaps for pull-scr
To configure the pull-scr container, you need to create three ConfigMaps. Follow the steps below to prepare your environment and apply the necessary configurations.

---
#### 1. Prepare the Working Directory
On the server where you access Kubernetes (e.g., via MobaXterm), open a terminal and create a working directory:
```
cd ~
mkdir pull-scr
cd pull-scr
```
Copy the following files into the ```~/pull-scr``` directory:
* [pull-scr.config](./data/config/pull-scr.config)
* [scr-template.yaml](./data/config/scr-template.yaml)

---
#### 2. Configure pull-scr
Edit the *pull-scr.config* file to set the required parameters for your pull-scr instance.
| *Name* | *Comment* |
| ---    | ---       |
| BASE_URL | Base endpoint of the pull-scr container. If running multiple instances, assign a unique endpoint per instance <br>***Default:*** /pull-scr |
| PORT | Target port for the *pull-scr* container. |
| HOST | External host address (typically the hostname) where pull-scr is accessible. |
| NAMESPACE | Kubernetes namespace dedicated to *pull-scr* (e.g., scr). |
| LIST_SCR | Enables the /list-scr endpoint to display pod statuses in the namespace.<br>***Default:*** False |
| PULL_SCR | Enables the /pull-scr endpoint to pull and load images from the Docker registry.<br>***Default:*** False |
| RESTART_SCR | Enables the /restart-scr endpoint to restart pods.<br>***Default:*** False |
| DELETE_SCR | Enables the /delete-scr endpoint to delete pods and deployments.<br>***Default:*** False |

#### 3. Review scr-template.yaml
The scr-template.yaml file is a template used to generate Kubernetes manifests for SCR images. It uses tokens that are replaced at runtime. You may customize this file if needed before creating the ConfigMap.

#### 4. Create ConfigMaps
> :exclamation:**Note**: By default, *pull-scr* is deployed in the ```default``` namespace. If you use a different namespace, update the namespace in the commands below and also in the following files:

* [pull-scr.yaml](./data/yaml/pull-scr.yaml)
* [ns-role.yaml](./data/yaml/ns-role.yaml)

Format to create a ConfigMap:<br>
```kubectl create configmap <config map name> --from-file=<key>=<file> --namespace=<namespace>```

Use the following commands to create the required ConfigMaps:
```
# Set the namespace (change if needed)
export PULL_SCR_NAMESPACE="default"

# Create ConfigMap for pull-scr configuration
kubectl create configmap pull-scr-config \
  --from-file=config=$HOME/pull-scr/pull-scr.config \
  --namespace=$PULL_SCR_NAMESPACE

# Create ConfigMap for the SCR template
kubectl create configmap scr-yaml-template \
  --from-file=template=$HOME/pull-scr/scr-template.yaml \
  --namespace=$PULL_SCR_NAMESPACE

# Create ConfigMap for kubectl configuration. 
# Assuming the kubectl config file is in default location in the home directory
kubectl create configmap kubectl-config \
  --from-file=config=$HOME/.kube/config \
  --namespace=$PULL_SCR_NAMESPACE
```
