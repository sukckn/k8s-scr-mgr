![pull-scr logo](./images/pull-scr%20logo.png)

Service container for SAS Viya to load SAS Container Runtime (SCR) images into Kubernetes.
This service container is intended to support developers during the development phase when decision flows, or models are published to a Docker Registry and loaded into Kubernetes. It is not always possible that developers have access to the server to load a decision flow or model into Kubernetes when it is published to a Docker Registry.

The pull-scr container is getting loaded into Kubernetes and offers a service through a custom step in SAS Studio to:
* Load a SCR image into Kubernetes
* Restart launched SCR containers
* Delete the deployment of a SCR container
* Show a list of all pod that run in a dedicated namespace in Kubernetes

For security reasons all SCR containers will get loaded into the same dedicated namespace in Kubernetes.

## Installation
### Namespace
For security reasons *pull-scr* does works for only one dedicated Kubernetes namespace per instance. All SCRs will be loaded into the same namespace. It different namespaces are requred need to start several instances of *pull-scr*

If you don't have a dedicated namespace yet, you need to create it. To create namespace *scr* run the below command.
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
Copy files [config.cfg](./data/config/config.cfg) and [scr-template.yaml](./data/config/scr-template.yaml) to server directory ```~/pull-scr```.

#### Set pull-scr configuration
The file *config.cfg* contains the parameters to set for the *pull-scr* instance. Open file in an editor and set the correct values for the parameters.
| *Name* | *Comment* |
| ---    | ---       |
| BASE_URL | This is the base endpoint (root address) of the pull-scr container.<br> If you run several insances of pull-scr you need to assign a unique endpoint per instance.<br>**Note:** Default is */pull-scr*. Only change this value if you run more than on instance.|
| PORT | The target port for *pull-scr*. |
| HOST | The external host address under which pull-scr can be reached. Typically this is the host name. |
| NAMESPACE | This is the dedicated namespace in Kubernetes for with pull-scr is working. E.g.: *scr* |
| LIST_SCR | Switch to enable endpoint */list-scr* <br>This endpoint shows a list of all pod with status in the dedicated namespace <br> Default is False |
| PULL_SCR | Switch to enable endpoint */pull-scr* <br>This endpoint pulls the image from the docker registry and loads it into the namespace in Kubernetes <br> Default is False |
| RESTART_SCR | Switch to enable endpoint */restart-scr* <br>This endpoint restart the pod for a docker container <br> Default is False |
| DELETE_SCR | Switch to enable endpoint */delete-scr* <br>This endpoint deletes the pod and deployment of a SCR container <br> Default is False |

#### Create ConfigMaps<br>
The Kubernetes command to create a ConfigMap is:<br>
```kubectl create configmap <config map name> --from-file=<key>=<file> --namespace=<namespace>```<br>
E.g.:
```
kubectl create configmap pull-scr-config --from-file=config=$HOME/pull-scr/app/config.cfg --namespace=scr
kubectl create configmap scr-yaml-template --from-file=template=$HOME/pull-scr/template/scr-template.yaml --namespace=scr
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


