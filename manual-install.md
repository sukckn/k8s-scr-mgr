## Manual Installation Guide
> ❗**Note**: By default *k8s-scr-mgr* will be installed into namespace ```default```. The default namespace to load the scr containers is ```scr```. Both namespaces can be changed if necessary.

### Create a Dedicated Namespace
If you don't have a dedicated namespace yet, you need to create one. The default namespace to load the scr images is ```scr```. To create a namespace `scr`, run:

```
kubectl create namespace scr
```

### Creating ConfigMaps for k8s-scr-mgr
To configure the k8s-scr-mgr container, you need to create three ConfigMaps. Follow the steps below to prepare your environment and apply the necessary configurations.

---
#### 1. Prepare the Working Directory
On the server where you access Kubernetes (e.g., via MobaXterm), open a terminal and create a working directory:
```
cd ~
mkdir k8s-scr-mgr
cd k8s-scr-mgr
```

---
#### 2. Configure k8s-scr-mgr

Download file [k8s-scr-mgr.config](./data/config/k8s-scr-mgr.config) and edit it to set the required parameters for your *k8s-scr-mgr* instance:
| *Name* | *Comment* |
| ---    | ---       |
| HOST | External host address (typically the hostname) where *k8s-scr-mgr* is accessible. (E.g., myserver.sas.com) |
| NAMESPACE | Kubernetes namespace dedicated to load SCR containers.<br>**Default:** scr |
| CONTAINER_PREFIX | The prefix will be added to the SCR image name. All created components in Kubernetes will have the prefix. E.g.: If prefix 'scr' is set and the SCR image is called 'abc' the created componentes in Kubernetes are named 'scr-abc'<br>***Default:*** no prefix
| VIYA_NAMESPACE | The Kubernetes namespace where Viya is installed |
| MAS_POD | The prefix of the MAS POD.<br>***Default:*** *sas-microanalytic-score* |
| LIST_SCR | Enables the /list-scr endpoint to display pod statuses in the namespace.<br>***Default:*** True |
| PULL_SCR | Enables the /k8s-scr-mgr endpoint to pull images from the Docker registry and load them into Kubernetes.<br>***Default:*** True |
| RESTART_SCR | Enables the /restart-scr endpoint to restart pods.<br>***Default:*** True |
| DELETE_SCR | Enables the /delete-scr endpoint to delete pods and deployments.<br>***Default:*** True |
| GETLOG_SCR | Enables the /getlog-scr endpoint to receive the log for a scr container.<br>***Default:*** True |
| GETLOG_MAS | Enables the /getlog-mas endpoint to receive the log for MAS.<br>***Default:*** True |
| NS_TO_REGISTRY_MAP | Maping between scr namespace and container registry. In a JSON structure as key:value pair set <scr namespace>:<container registry> |

Copy the following file into directory ```~/k8s-scr-mgr```

#### 3. Review scr-template.yaml

The file *scr-template.yaml* is a template used to generate Kubernetes manifests for SCR images. It uses tokens that are replaced at runtime. You may customize this file if needed before creating the ConfigMap.

Download file [scr-template.yaml](./data/config/scr-template.yaml) and copy it into directory ```~/k8s-scr-mgr```:

#### 4. Kubernetes config file

We use the Kubernetes config information from your home directory, assuming the Kubernetes config file is in ```$HOME/.kube/config```. If the Kubernetes config file is in a different location you need to change the command "*3. Create ConfigMap for kubectl configuration*" in the next step (*Create ConfigMaps*) to point to your Kubernetes config file.

#### 5. Create ConfigMaps

Format to create a ConfigMap:<br>
```kubectl create configmap <config map name> --from-file=<key>=<file> --namespace=<namespace>```

Use the following commands to create the required ConfigMaps:
>❗**Note**: By default, *k8s-scr-mgr* is deployed in namespace```default```. If you use a different namespace, **set K8S_SCR_MGR_NAMESPACE to the correct value** below:

```
# Set the namespace (!!change if needed!!)
K8S_SCR_MGR_NAMESPACE="default"

# 1. Create ConfigMap for k8s-scr-mgr configuration
kubectl create configmap k8s-scr-mgr-config \
  --from-file=config=$HOME/k8s-scr-mgr/k8s-scr-mgr.config \
  --namespace=$K8S_SCR_MGR_NAMESPACE

# 2. Create ConfigMap for the SCR template
kubectl create configmap scr-yaml-template \
  --from-file=template=$HOME/k8s-scr-mgr/scr-template.yaml \
  --namespace=$K8S_SCR_MGR_NAMESPACE

# 3. Create ConfigMap for kubectl configuration. 
# Assuming the kubectl config file is in default location in the home directory
kubectl create configmap kubectl-config \
  --from-file=config=$HOME/.kube/config \
  --namespace=$K8S_SCR_MGR_NAMESPACE
```
### Load into Kubernetes
#### 1. Create Image Pull Secret
To load *k8s-scr-mgr* into Kubernetes, you must first create a Kubernetes secret to pull the SCR image from your Docker registry.

1. Download file [scr-secret-docker.yaml](./data/yaml/scr-secret-docker.yaml)
    >❗**Note**: If you don't use the default namespace ```scr``` to load the SCR containers you need to change *namespace: scr* in file *scr-secret-docker.yaml* to the correct namespace.

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

3. Copy the file to the server directory ```~/k8s-scr-mgr```.

4. Register secret in Kubernetes.
    ```
    cd ~/k8s-scr-mgr
    kubectl apply -f scr-secret-docker.yaml
    ```
---

#### 2. Create Database Secret
If the SCR image accesses a database, you must create a database secret. You can skip this step if you are not accessing a database.

1. Download file [scr-secret-db.yaml](./data/yaml/scr-secret-db.yaml)
    >❗**Note**: If you don't use the default namespace ```scr``` to load the SCR containers you need to change *namespace: scr* in file *scr-secret-db.yaml* to the correct namespace.

2. Open the file and replace &lt;DB-SECRET&gt; with your database connection string.

    **Example: PostgreSQL Connection**
    * Example connection string:
        ```
        connectionstring=DRIVER=SQL; CONOPTS=(DRIVER=POSTGRES; CATALOG=public; UID=MyUID; PWD=MyPWD; SERVER=MyServer.sas.com; PORT=5432; DB=MyDB;)
        ```
        >💡**Tip:** After the key word *connectionstring=* you can use the same connection string you use with MAS.

    * **Base64 encode** the connection string:
        ```
        Y29ubmVjdGlvbnN0cmluZz1kcml2ZXI9c3FsO2Nvbm9wdHM9KChkcml2ZXI9cG9zdGdyZXM7Y2F0YWxvZz1wdWJsaWM7dWlkPXNhcztwd2Q9J2xueHNhcyc7c2VydmVyPSBwZy1hZ2VudGljLWFpLXBvc3RncmVzcWwuYWdlbnRpYy1haS5zdmMuY2x1c3Rlci5sb2NhbDtwb3J0PTU0MzE7REI9cG9zdGdyZXM7KSk=
        ```

    * Replace the token &lt;DB-SECRET&gt; in file ```scr-secret-db.yaml``` with this encoded string.

    📘 See [Configuring a Database Connection](https://go.documentation.sas.com/doc/en/mascrtcdc/default/mascrtag/n15q5afwsfkjl5n1cfvcn7xz4x22.htm) for information on all supported databases.

3. Copy the file to ```~/k8s-scr-mgr```

4. Register secret in Kubernetes.
    ```
    cd ~/k8s-scr-mgr
    kubectl apply -f scr-secret-db.yaml
    ```
---
#### 3. Deploy k8s-scr-mgr to Kubernetes
1. Download the following files:
    * [k8s-scr-mgr.yaml](./data/yaml/k8s-scr-mgr.yaml)
    * [k8s-scr-mgr-role.yaml](./data/yaml/k8s-scr-mgr-role.yaml)
    * [mas-log-reader.yaml](./data/yaml/mas-log-reader.yaml)<br>

2. Open file k8s-scr-mgr.yaml and set the host URL. At lines 102 and 105 set the URL where you deploy K8S SCR Manager to. 
    
    >❗**Note**: If you don't use the default namespace ```scr``` to load the SCR containers you need to change *namespace: scr* in file *k8s-scr-mgr-role.yaml* to the correct namespace.

    >❗**Note**: By default, *k8s-scr-mgr* is deployed in namespace```default```. If you use a different namespace, update *namespace: default* in *k8s-scr-mgr.yaml* and *k8s-scr-mgr-role.yaml* to the correct namespace.

    >❗**Note**: In file mas-log-reader.yaml verify that the namespace for Viya is correct. By default it is pointing at *namespace: viya4*.

3. Copy the files to ```~/k8s-scr-mgr```:

4. Apply the deployment:
    ```
    cd ~/k8s-scr-mgr
    kubectl apply -f k8s-scr-mgr.yaml
    kubectl apply -f k8s-scr-mgr-role.yaml 
    kubectl apply -f mas-log-reader.yaml 
    ```
5. Verify Deployment<br>
    After applying both files, verify that the *k8s-scr-mgr* service is running in Kubernetes.
    ```
    kubectl get pods --namespace default | grep k8s-scr-mgr
    ```

---

### Configuration for more than one Viya Publishing Destination
If you publish to different container registries and therefore have more than one Docker publishing destination in Viya, you can configure *k8s-scr-mgr* to pull from a spcific publishing destination. Each container registry (publishing destinaton) will have its own dedicated namespace and database connection details. 

To register a second container registry (publishing destinaton) you need to repeat some of the above steps and adjust the templates for SCR load namespace:

* Create another [namespace](#create-a-dedicated-namespace)
* Create second [Image Pull Secret](#1-create-image-pull-secret)<br>
Crrate a pull secret for the secon container registry. Ensure to change the default namespace *scr* to point to the appropriate namespace.
* Create second [Database Secret](#2-create-database-secret)<br>
Create a database secret for the namespace. Ensure to change the default namespace *scr* to point to the appropriate namespace.
Set [Kubernetes Role Binding](#3-deploy-k8s-scr-mgr-to-kubernetes)<br>
Set the role bindings for the new namespace. Adjust settings in [k8s-scr-mgr-role.yaml](./data/yaml/k8s-scr-mgr-role.yaml). Ensure to change the default namespace *scr* to point to the appropriate namespace.



