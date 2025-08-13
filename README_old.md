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

### Create ConfigMaps
You need to create three ConfigMaps that are required by the *pull-scr* container. On the server from where you access Kubernetes open a command prompt (e.g. using MobaXterm) and create *pull-scr* subdirectory in you home directory.
```
cd ~
mkdir pull-scr
cd pull-scr
```
Copy files [pull-scr.config](./data/config/pull-scr.config) and [scr-template.yaml](./data/config/scr-template.yaml) to server directory ```~/pull-scr```.

#### Set pull-scr configuration
The file *pull-scr.config* contains the parameters to set for the *pull-scr* instance. Open file in an editor and set the correct values for the parameters.
| *Name* | *Comment* |
| ---    | ---       |
| BASE_URL | This is the base endpoint (root address) of the pull-scr container.<br> If you run several insances of pull-scr you need to assign a unique endpoint per instance.<br>**Note:** Default is */pull-scr*. Only change this value if you run more than on instance.|
| PORT | The target port for *pull-scr*. |
| HOST | The external host address under which pull-scr can be reached. Typically this is the host name. |
| NAMESPACE | This is the dedicated namespace in Kubernetes for with pull-scr is working. E.g.: *scr* |
| LIST_SCR | Switch to enable endpoint */list-scr* <br>This endpoint shows a list of all pod with status in the dedicated namespace <br> Default is False |
| PULL_SCR | Switch to enable endpoint */pull-scr* <br>This endpoint pulls the image from the docker registry and loads it into the namespace in Kubernetes <br> Default is False |
| RESTART_SCR | Switch to enable endpoint */restart-scr* <br>This endpoint restarts the pod for a docker container <br> Default is False |
| DELETE_SCR | Switch to enable endpoint */delete-scr* <br>This endpoint deletes the pod and deployment of a SCR container <br> Default is False |

#### scr-template
scr-template.yaml is the template yaml file to load scr images into Kubernetes. The template is using tokens to generate the required yaml file at run time. You can customize the template file if necessary before loading it into ConfigMaps.

#### Create ConfigMaps<br>
> **Note:** By default *pull-scr* is loaded into namespace ```default```. If you want load it into a different namespace, you need to change the namespace for the *create configmap* commands below. You also need to adjust the namespace in yaml files [pull-scr.yaml](./data/yaml/pull-scr.yaml) and [ns-role.yaml](./data/yaml/ns-role.yaml)

The Kubernetes command to create a ConfigMap is:<br>
```kubectl create configmap <config map name> --from-file=<key>=<file> --namespace=<namespace>```<br>
```
# Change namespace if necessary
export PULL_SCR_NAMESPACE="default"
kubectl create configmap pull-scr-config --from-file=config=$HOME/pull-scr/pull-scr.config --namespace=$PULL_SCR_NAMESPACE
kubectl create configmap scr-yaml-template --from-file=template=$HOME/pull-scr/scr-template.yaml --namespace=$PULL_SCR_NAMESPACE
```
You also need to create a ConfigMap for the kubectl configuration. Assuming for kubectl config file is in you default home directory run the following command:
```
kubectl create configmap kubectl-config --from-file=config=$HOME/.kube/config --namespace=$PULL_SCR_NAMESPACE
```

### Load into Kubernetes
#### Pull image secret
To load *pull-scr* into Kubernetes you need to create a Kubernetes secret to pull the scr image from the docker registry.<br>
Copy file [scr-secret-docker.yaml](./data/yaml/scr-secret-docker.yaml) to server directory ```~/pull-scr```.<br>
Open file in editor and set the pull secret. Replace ```<DOCKER-PULL-SECRET>``` with the connection credentials to your docker registry.<br>
This example is pulling a docker image from *Azure Docker Registry*<br>
- Set parameters in the JSON structure below to connect to you your docker registry.
    ```
    {
        "auths": {
            "<Azure Docker Registry Name>.azurecr.io": {
                "username": "<Azure Docker Registry User Name>",
                "password": "<Azure Docker Registry Password>",
                "auth": "Base64 encode: <Azure Docker Registry User Name>:<Azure Docker Registry Password>"
            }
        }
    }
    ```
- First Base64 encode the value for parameter "auth"<br>
  For example: sasscr:myPassword => Base64 encode: c2Fzc2NyOm15UGFzc3dvcmQ=
- Set the parameter "auth" value together with other values in JSON structure<br>
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
- Base64 encode the the JSON structure<br>
  ```
  ewoJImF1dGhzIjogewoJCSJzYXNzY3IuYXp1cmVjci5pbyI6IHsKCQkJInVzZXJuYW1lIjogInNhc3NjciIsCgkJCSJwYXNzd29yZCI6ICJteVBhc3N3b3JkIiwKCQkJImF1dGgiOiAiYzJGemMyTnlPbTE1VUdGemMzZHZjbVE9IgoJCX0KCX0KfQ==
  ```
- Use this Base64 encoded string to replace the token \<DOCKER-PULL-SECRET\>
- See also [Create a Secret based on existing credentials](https://kubernetes.io/docs/tasks/configure-pod-container/pull-image-private-registry/#registry-secret-existing-credentials) in Kubernetes documentation

#### Set database secret
If decision flows in a scr image access a database you need to crerate a database secret.<br>
Copy file [scr-secret-db.yaml](./data/yaml/scr-secret-db.yaml) to server directory ```~/pull-scr```.
Open file in editor and set the database secret. Replace ```<DB-SECRET>``` with the database credentials to cpnnect to the database.<br>

- The connection string to connect to Postgres looks like:<br>
  connectionstring=DRIVER=SQL; CONOPTS=(DRIVER=POSTGRES; CATALOG=public; UID=MyUID; PWD=MyPWD; SERVER=MyServer.sas.com; PORT=5432; DB=MyDB;)

    > :bulb: **Tip**: After the key word *connectionstring=* you can set the connection credentials you have used to connect to MAS.<br>

- For the installed Postgres database the connection string looks like:
    ```
    connectionstring=driver=sql;conopts=((driver=postgres;catalog=public;uid=sas;pwd='lnxsas';server= pg-agentic-ai-postgresql.agentic-ai.svc.cluster.local;port=5431;DB=postgres;))
    ```
- Base64 encode the connection string<br>
  This is the encoded connection string for the installed Postgres database
    ```
    Y29ubmVjdGlvbnN0cmluZz1kcml2ZXI9c3FsO2Nvbm9wdHM9KChkcml2ZXI9cG9zdGdyZXM7Y2F0YWxvZz1wdWJsaWM7dWlkPXNhcztwd2Q9J2xueHNhcyc7c2VydmVyPSBwZy1hZ2VudGljLWFpLXBvc3RncmVzcWwuYWdlbnRpYy1haS5zdmMuY2x1c3Rlci5sb2NhbDtwb3J0PTU0MzE7REI9cG9zdGdyZXM7KSk=
    ```
- Replace token \<DB-SECRET\> with the encoded connection string

See [Configuring a Database Connection](https://go.documentation.sas.com/doc/en/mascrtcdc/default/mascrtag/n15q5afwsfkjl5n1cfvcn7xz4x22.htm) for information on all supported database.

#### Load *pull-scr* into Kubernetes
You can now load *pull-scr* into Kubernetes.<br>
Copy files [pull-scr.yaml](./data/yaml/pull-scr.yaml) and [ns-role.yaml](./data/yaml/ns-role.yaml) to server directory ```~/pull-scr```.

To load *pull-scr* run:
```
cd ~/pull-scr
kubectl apply -f pull-scr.yaml
```
> **Note:** The yaml file will load *pull-scr* into namespace *default*. If you load it into a defferent namespace to adjust *pull-scr.yaml* accordingly.

You also need to make sure the correct use rights are set for the namespace. Run file [ns-role](./data/yaml/ns-role.yaml) to set the correct user rights.
```
cd ~/pull-scr
kubectl apply -f ns-role.yaml
```
> **Note:** The yaml file will set the user rights for *pull-scr* so the service can access the scr namespace correctly. If you don't use the default setting you need to adjust the file.<br>
>* If you have loaded *pull-scr* into a different namespace you need to adjust the setting *namespace: default*<br>
>* If you don't use namespace *scr* to load the scr containers you need to adjust setting *namespace: scr*

#### Verify pull-scr service
When both file have run successlully check in kubernetes that *pull-scr* is running.

## ID - Deploy SCR
To call pull-scr from within SAS Viya you can use the SAS Studio custom step ```ID - Deploy SCR```.
#### Import custom step
To import ID - Deploy SCR
* Go to SAS Studio
* In your home folder (My Folder) create sub-folder *custom steps*
* Upload [ID - Deploy SCR](./data/custom_step/ID%20-%20Deploy%20SCR.step) into sub-folder

### User Interface
#### Modus
In this section you switch between the different operations you want to perform.

* **Pull Image**<br>
With this UI you can load a new SCR image from the Docker registry into Kubernetes
* **Restart** pod<br>
Use this modus to restart a pod for example when you have published a new version of a SCR to Docker registry
* **Delete deployment**<br>
Use this modus if you need to delete a SCR deployment from Kubernetes
* **Get list of pods in namespace**<br>
Use this modus to receive a list of pods in the dedicated namespace with status and age imformation

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

> **Note:** The created deployment and pod in Kubernetes are prefixed with ```scr-``` followed by the scr image name. E.g. if the scr image is called *my-id-flow*, the deploment and pod are called *scr-my-id-flow*
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

Set the url for the pull-scr service. The default address is ```pull-scr.default.svc.cluster.local```. By default *pull-scr* is loaded into namespace ```default```. If you have loaded it into a different namespace you can set the url here.<br> 
The step is using the internal DNS by default. If you are not using the default namespace you can set a different url using this format:<br>
```<pod-name>.<namespace>.svc.cluster.local```<br>
<br>
You can also set a different url by setting macro ```PULL_SCR_URL```. This could be done in *SAS Studio Autoexec file*, so it is automatically set every time you start *SAS Studio*. E.g.:
```
%let pull_scr_url= %nrquote(pull-scr.mynamespace.svc.cluster.local);
```


