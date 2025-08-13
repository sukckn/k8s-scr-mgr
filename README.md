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
> ❗**Note**: By default *pull-scr* will be installed into namespace ```default```. The default namespace to load the scr containers is ```scr```. Both namespaces can be changed if necessary.

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
>❗**Note**: By default, *pull-scr* is deployed in the ```default``` namespace. If you use a different namespace, update the namespace in the commands below and also in the following files:

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
### Load into Kubernetes
#### 1. Create Image Pull Secret
To load pull-scr into Kubernetes, you must first create a Kubernetes secret to pull the SCR image from your Docker registry.

1. Copy the file [scr-secret-docker.yaml](./data/yaml/scr-secret-docker.yaml) to the server directory ```~/pull-scr```.

2. Open the file in an editor and replace the placeholder &lt;DOCKER-PULL-SECRET&gt; with your Docker registry credentials.

    **Example: Azure Docker Registry**
    * Update the JSON structure with your registry details:
        ```
        {
            "auths": {
                "<Azure Docker Registry Name>.azurecr.io": {
                "username": "<Azure Docker Registry User Name>",
                "password": "<Azure Docker Registry Password>",
                "auth": "Base64 encode: <username>:<password>"
                }
            }
        }
        ```
    * Base64 encode the auth value: \<username\>:\<password\>:<br>
    Example: sasscr:myPassword → Base64 encode:  c2Fzc2NyOm15UGFzc3dvcmQ=

    * Final JSON structure:
        ```
        {
            "auths": {
                "sasscr.azurecr.io": {
                "username": "sasscr",
                "password": "myPassword",
                "auth": "c2Fzc2NyOm15UGFzc3dvcmQ="
                }
            }
        }
        ```
    * **Base64 encode** the entire JSON structure:
        ```
        ewoJImF1dGhzIjogewoJCSJzYXNzY3IuYXp1cmVjci5pbyI6IHsKCQkJInVzZXJuYW1lIjogInNhc3NjciIsCgkJCSJwYXNzd29yZCI6ICJteVBhc3N3b3JkIiwKCQkJImF1dGgiOiAiYzJGemMyTnlPbTE1VUdGemMzZHZjbVE9IgoJCX0KCX0KfQ==
        ```
    * Replace the token &lt;DOCKER-PULL-SECRET&gt; in ```scr-secret-docker.yaml``` with this encoded string.

    📘 Refer to [Kubernetes documentation](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/#registry-secret-existing-credentials) for more details on creating secrets from existing credentials.

3. Register secret in Kubernetes.
    ```
    cd ~/pull-scr
    kubectl apply -f scr-secret-docker.yaml
    ```
---
#### 2. Create Database Secret
If the SCR image accesses a database, you must create a database secret. You can skip this step if you are not accessing a database.
1. Copy the file [scr-secret-db.yaml](./data/yaml/scr-secret-db.yaml) to ```~/pull-scr```

2. Open the file and replace &lt;DB-SECRET&gt; with your database connection string.

    **Example: PostgreSQL Connection**
    * Example connection string:
        ```
        connectionstring=DRIVER=SQL; CONOPTS=(DRIVER=POSTGRES; CATALOG=public; UID=MyUID; PWD=MyPWD; SERVER=MyServer.sas.com; PORT=5432; DB=MyDB;)
        ```
        >💡**Tip:** After the key word *connectionstring=* you can use the same connection string you use with MAS.

    * Base64 encode the connection string:
        ```
        Y29ubmVjdGlvbnN0cmluZz1kcml2ZXI9c3FsO2Nvbm9wdHM9KChkcml2ZXI9cG9zdGdyZXM7Y2F0YWxvZz1wdWJsaWM7dWlkPXNhcztwd2Q9J2xueHNhcyc7c2VydmVyPSBwZy1hZ2VudGljLWFpLXBvc3RncmVzcWwuYWdlbnRpYy1haS5zdmMuY2x1c3Rlci5sb2NhbDtwb3J0PTU0MzE7REI9cG9zdGdyZXM7KSk=
        ```

    * Replace the token &lt;DB-SECRET&gt; in file ```scr-secret-db.yaml``` with this encoded string.

    📘 See [Configuring a Database Connection](https://go.documentation.sas.com/doc/en/mascrtcdc/default/mascrtag/n15q5afwsfkjl5n1cfvcn7xz4x22.htm) for information on all supported databases.

3. Register secret in Kubernetes.
    ```
    cd ~/pull-scr
    kubectl apply -f scr-secret-db.yaml
    ```
---
#### 3. Deploy pull-scr to Kubernetes
1. Copy the following files to ```~/pull-scr```:
    * [pull-scr.yaml](./data/yaml/pull-scr.yaml)
    * [ns-role.yaml](./data/yaml/ns-role.yaml)

2. Apply the deployment:
    >❗**Note:** The yaml file will load *pull-scr* into namespace *default*. If you load *pull-scr* into a different namespace you need to **adjust pull-scr.yaml** accordingly.
    ```
    cd ~/pull-scr
    kubectl apply -f pull-scr.yaml
    ```
3. Set namespace permissions:
    >❗**Note:** *ns-role.yaml* sets user rights for *pull-scr* to access the scr namespace.<br>
    >* If using a different namespace, update ```namespace: default```
    >* If SCR containers are loaded into a different namespace than *scr*, update ```namespace: scr``` accordingly

4. Verify Deployment<br>
    After applying both files, verify that the *pull-scr* service is running in Kubernetes.

## ID - Deploy SCR
The **ID - Deploy SCR** custom step allows you to interact with the pull-scr service from within SAS Viya using SAS Studio. This step supports operations such as:<br>

🔷 pulling container images, <br>
🔷 restarting pods, <br>
🔷 deleting deployments, <br>
🔷 listing pods in the dedicated Kubernetes namespace.<br>

---
### Importing the Custom Step
To import custom step *ID - Deploy SCR*:
* Open SAS Studio.
* In your home folder (My Folder), create a sub-folder named ```custom steps```.
* Upload file [ID - Deploy SCR.step](./data/custom_step/ID%20-%20Deploy%20SCR.step) into the *custom steps* folder.

---
### User Interface
#### Modus
Use this section to choose the operation you want to perform:

* **Pull Image**<br>
    Load a new SCR image from the Docker registry into Kubernetes.
* **Restart** pod<br>
    Restart a pod, typically after publishing a new version of an SCR image.
* **Delete deployment**<br>
    Remove an SCR deployment from Kubernetes.
* **Get list of pods in namespace**<br>
    Retrieve a list of pods in the *scr-pull* namespace, including status and age information.

    ![](./images/pull-image.jpg)

#### Pull image
* **Container Image Name**<br>
The name of the SCR container image in the Docker registry
* **Container Image Tag**<br>
The tag name of the image you want to load. E.g.: latest or 6
* **Owner**<br>
Set a Kubernetes lable for the owner of the scr image. Information who to contact by question about the image
* **Image Pull Policy**,br
Set how the image should get pulled if the pod gets restarted.<br>
Options:
    * Always (default)<br>
    The Kubelet will always attempt to pull the image from the registry every time a container is launched
    * IfNotPresent<br>
    The Kubelet will only pull the image if it is not already present on the node. If a local copy exists, it will be used without checking the registry for updates
    * Never<br>
    It will only use a locally available image. If the image is not found locally, the container launch will fail. This policy is typically used for development or air-gapped environments where images are pre-loaded onto nodes
* **Environment Variables**<br>
Set the number of environment variables you want to set for the scr container
* **Environment Variable**<br>
    * **Name**<br>
    Name of the environment variable
    * **Value**<br>
    Environment variable value

>❗**Note:** The deployment and pod created in Kubernetes are prefixed with **scr-** followed by the image name.<br>
**Example:** For an image named *my-id-flow*, the deployment and pod will be named *scr-my-id-flow*.

---
#### Restart pod
![](./images/restart-pod.jpg)

* **Deployment name**<br>
Set the name of the scr deployment you want to re-start.
---

#### Delete deployment
![](./images/delete-deployment.jpg)

* **Deployment name**<br>
Set the name of the scr deployment you want to delete.
---

#### Get list of pods in namespace
![](./images/list-pods.jpg)

Run the step to receive a list of all pods running in the namespace linked to pull-scr.

---
### Options
![](./images/options.jpg)

Configure the URL for the *pull-scr* service. The default is:
```
pull-scr.default.svc.cluster.local
```
If *pull-scr* is not deployed namespace ```scr```, update the URL using the format:
```
<pod-name>.<namespace>.svc.cluster.local
```
Alternatively, you can set a different URL by setting macro ```PULL_SCR_URL```. This could be done in *SAS Studio Autoexec file*, to automatically set the URL every time you start *SAS Studio*.:
```
%let pull_scr_url= %nrquote(pull-scr.mynamespace.svc.cluster.local);
```
