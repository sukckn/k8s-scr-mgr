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
For security reasons *scr-pull* does works for only one dedicated Kubernetes namespace per instance. All SCRs will be loaded into the same namespace. It different namespaces are requred need to start several instances of *scr-pull*

If you don't have a dedicated namespace yet, you need to create it. To create namespace *scr* run the below command.
```
kubectl create namespace scr
```

### Create ConfigMaps
You need to create three ConfigMaps that are required by the *pull-scr* container. On the server from where you access Kubernetes open a command prompt (e.g. using MobaXterm) and create *scr-pull* subdirectory in you home directory.
```
cd ~
mkdir scr-pull
cd scr-pull
```
Copy files [config.cfg](./data/config/config.cfg) and [scr-template.yaml](./data/config/scr-template.yaml) to server directory ```~/scr-pull```.

#### Set scr-pull configuration
The file *config.cfg* contains the parameters to set for the *scr-pull* instance. Open file in an editor and set the correct values for the parameters.
| *Name* | *Comment* |
| ---    | ---       |
| BASE_URL | This is the base endpoint (root address) of the scr-pull container.<br> If you run several insances of scr-pull you need to assign a unique endpoint per instance.<br>**Note:** Default is */pull-scr*. Only change this value if you run more than on instance.|
| PORT | The target port for *scr-pull*. |
| HOST | The external host address under which scr-pull can be reached. Typically this is the host name. |
| NAMESPACE | This is the dedicated namespace in Kubernetes for with scr-pull is working. E.g.: *scr*

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


