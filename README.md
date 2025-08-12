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
The Kubernetes command to create a ConfigMap is:<br>
```kubectl create configmap <config map name> --from-file=<key>=<file> --namespace=<namespace>```<br>
E.g.:
```
# Set or change namespace if necessary
export PULL_SCR_NAMESPACE="scr"
kubectl create configmap pull-scr-config --from-file=config=$HOME/pull-scr/pull-scr.config --namespace=$PULL_SCR_NAMESPACE
kubectl create configmap scr-yaml-template --from-file=template=$HOME/pull-scr/scr-template.yaml --namespace=$PULL_SCR_NAMESPACE
```
You also need to create a ConfigMap for the kubectl configuration. Assuming for kubectl config file is in you default home directory run the following command:
```
kubectl create configmap kubectl-config --from-file=config=$HOME/.kube/config --namespace=scr
```

### Load into Kubernetes
You can now load *pull-scr* into Kubernetes.<br>
Copy files [pull-scr.yaml](./data/yaml/pull-scr.yaml) and [ns-role.yaml](./data/yaml/ns-role.yaml) to server directory ```~/pull-scr```.

To load *pull-scr* run:
```
cd ~/pull-scr
kubectl apply -f pull-scr.yaml
```
> **Note:** The yaml file will load *pull-scr* into namespace *default*. If you would like to load it into a defferent namespace to adjust *pull-scr.yaml* accordingly.

You also need to make sure the correct use rights are set for the namespace. Run file [ns-role](./data/yaml/ns-role.yaml) to set the correct user rights.
```
cd ~/pull-scr
kubectl apply -f ns-role.yaml
```
> **Note:** The yaml file will set the user rights for namespace *scr* if you are using a different namespace you need to adjust the yaml file accordingly.

When both file have run successlully check in kubernetes that *pull-scr* ir running.

### Custom Step 
To call pull-scr from within SAS Viya you can use the SAS Studio custom step ```ID - Deploy SCR```.
#### Import custom step
To import ID - Deploy SCR
* Go to SAS Studio
* In your home folder (My Folder) create sub-folder *custom steps*
* Upload [ID - Deploy SCR](./data/custom_step/ID%20-%20Deploy%20SCR.step) into sub-folder

## ID - Deploy SCR
To load a SCR container into Kubernetes open step ID - Deploy SCR in SAS Studio (open in tab)

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


