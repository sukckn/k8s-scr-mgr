![k8s-scr-mgr logo](./images/k8s-scr-mgr_rm.png)

# `k8s-scr-mgr`: Service Container for SAS Viya SCR
`k8s-scr-mgr` is a service container designed to support developers working with SAS Viya by enabling the loading of SAS Container Runtime (SCR) images into Kubernetes. This tool is especially useful during the development phase when decision flows or models are published to a Docker Registry but developers may not have direct access to the Kubernetes cluster.

## Features
Once deployed, the `k8s-scr-mgr` container provides a service accessible via custom step *ID - K8S SCR Manager* in SAS Studio to:

🔷 **Load** SCR images into Kubernetes<br>
🔷 **Restart** launched SCR containers<br>
🔷 **Delete** SCR container deployments<br>
🔷 **List** all pods running in the dedicated Kubernetes namespace<br>
🔷 **Show** log for SCR container<br>
🔷 **Show MAS** log for information<br>

> ⚠️ For security reasons, all SCR containers are loaded into a **dedicated namespace**. The default namespace is *scr*. You can overwrite the default namespace using parameter *

---

## Installation Guide
Install k8s-scr-mgr using helm chart or you can install it manually.

### Installing via Helm Chart
To install the chart you need to set some required parameters - see below. <br>
here a list of common parameters used to install the chart:

| | Parameter | Comment | Required |
| --- | --- | --- | --- |
| | namespace | The namespace where *k8s-scr-mrg* is going to be installed.<br>**Default**: default | No |
| set | installName | The name under which *k8s-scr-mrg* is going to be installed.<br>**Default**: \<release name\>-\<chart name\> | No |
| set | k8sScrMgr.viya_namespace | The namespace where Viya is installed.<br>**Default**: viya | No |
| set | k8sScrMgr.host | The external URL where *k8s-scr-mrg* is going to be installed. | Yes |
| set-file | k8sScrMgr.kubeconfig | Fully qualified file name for the kubectl config file | Yes |
| set | dockerCredentials.baseRepoURL | The container registry location (URI) | Yes |
| set | dockerCredentials.registryId | The container registry user ID | Yes |
| set | dockerCredentials.registryPassword | The container registry password | Yes |
| set | dbCredentials.connectionstring | Database connection string. Use the same string that is used in Viya Environment manager to connect from MAS.<br>**Note**: Enclose connection string in double quotes! | No |


Example to install the chart with the release name *k8s-scr-mrg*:

```
helm install k8s-scr-mgr helm install k8s-scr-mgr oci://ghcr.io/sukckn/k8sscrmgr \
--namespace k8sscrmgr \
--create-namespace \
--set installName=k8s-scr-mgr \
--set k8sScrMgr.viya_namespace=viya4 \
--set k8sScrMgr.host=my-server.net.sas.com \
--set-file k8sScrMgr.kubeconfig=$HOME/.kube/config \
--set dockerCredentials.baseRepoURL=myregistry.azurecr.io \
--set dockerCredentials.registryId=myregistry \
--set dockerCredentials.registryPassword=NRoQbVCvdcBOcZZgURtIRKLq+ACRAbPpCz \
--set dbCredentials.connectionstring="driver=sql;conopts=((driver=postgres;catalog=public;uid=mysas;pwd='asddsa';server= pg-demo-postgresql.default.svc.cluster.local;port=5431;DB=postgres;))"
``` 

<details>
<summary>Additional install parameters</summary>

| | Parameter | Comment | Required |
| --- | --- | --- | --- |
| set | k8sScrMgr.container_prefix | The prefix will be added to the SCR image name. All created components in Kubernetes will have the prefix. E.g.: If prefix 'scr' is set and the SCR image is called 'abc' the created componentes in Kubernetes are named 'scr-abc'<br>**Default:** scr | No |
| set | k8sScrMgr.mas_pod | The prefix name of the MAS pod.<br>**Default:** sas-microanalytic-score | No |
| set | k8sScrMgr.list_scr | Enables the /list-scr endpoint to display pod statuses in the namespace.<br>**Default:** True | No |
| set | k8sScrMgr.pull_scr | Enables the /k8s-scr-mgr endpoint to pull images from the Docker registry and load them into Kubernetes.<br>**Default:** True | No |
| set | k8sScrMgr.restart_scr | Enables the /restart-scr endpoint to restart pods.<br>**Default:** True | No |
| set | k8sScrMgr.delete_scr | Enables the /delete-scr endpoint to delete pods and deployments.<br>**Default:** True | No |
| set | k8sScrMgr.getlog_scr | Enables the /getlog-scr endpoint to receive the log for a scr container.<br>**Default:** True | No |
| set | k8sScrMgr.getlog_mas | Enables the /getlog-mas endpoint to receive the log for MAS.<br>**Default:** True | No |
| set-file | k8sScrMgr.scr_yaml_template | Fully qualified file name for the scr yaml file to load the SCR container. See [Yaml file to load SCR Container](#yaml-file-to-load-scr-container) for more information.<br>**Default:** If not used the default SCR yaml template is used. | No |
| set | namespace.ns_scr | Set namespace to which the scr containers are loaded.<br>**Default:** scr | No |
</details>

> :bulb: **Tip**: See annotation *helm.sh/uninstall* in Kubernetes deployment for helm uninstall command.

#### Yaml file to load SCR Container
By default a yaml file template is used to load the SCR container into Kubernetes. You can overwrite the default template to adjust Kubernetes settings when loading a SCR container.
Download the [template file](./data/config/scr-template.yaml) and edit the file as appropriate.
You can load the template file using helm parameter *k8sScrMgr.scr_yaml_template*

---


### Manual Installation Guide
See [instructions](manual-install.md) for manual install.

---

## ID - K8S SCR Manager
The **ID - K8S SCR Manager** custom step allows you to interact with the k8s-scr-mgr service from within SAS Viya using SAS Studio. This step supports operations such as:<br>

🔷 **Load** SCR images into Kubernetes<br>
🔷 **Restart** launched SCR containers<br>
🔷 **Delete** SCR container deployments<br>
🔷 **List** all pods running in the dedicated Kubernetes namespace<br>
🔷 **Show** log for SCR container<br>
🔷 **Show MAS** log for information<br>

---

### Importing the Custom Step
To import custom step *ID - K8S SCR Manager*:
* Open SAS Studio.
* In your home folder (My Folder), create a sub-folder named ```custom steps```.
* Upload file [ID - K8S SCR Manager.step](./data/custom_step/ID%20-%20K8S%20SCR%20Manager.step) into the *custom steps* folder.

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
* **Get log**<br>
    Retrive the log for a container in the dedicated namespace.

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
* **SCR is using database**
    * Tick this box if the SCR image is accessing a database. If this box is ticked a database secret needs to be set. [See Create Database Secret](#2-create-database-secret).    
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

Run the step to receive a list of all pods running in the namespace linked to k8s-scr-mgr.

---

#### Get log
![](./images/get-log.jpg)

* **Pod name**<br>
The name of the pod for wich you want the log information.<br>
You don't need to type in the complete pod name, partions of it will work. E.g.: if the pod name is 'scr-mypod-7b7c55d84b-2fm87' you can just tyep 'mypod'.

* **Show rows in log**
This indecates how many rows from the log will be shown.
    * All rows<br>
    Shows the complete log
    * Top rows<br>
    Show the top number of rows as set in field **Number of rows**
    * Bottom rows<br>
    Show last number of rows as set in field **Number of rows**

#### Get MAS log
![](./images/get-MAS-log.jpg)

* **Show rows in log**
This indecates how many rows from the log will be shown.
    * All rows<br>
    Shows the complete log
    * Top rows<br>
    Show the top number of rows as set in field **Number of rows**
    * Bottom rows<br>
    Show last number of rows as set in field **Number of rows**

    > By default it will show the last 30 rows in the log.

<br>

---

### Options
![](./images/options.jpg)

Configure the URL for the *k8s-scr-mgr* service. The default is:
```
k8s-scr-mgr.default.svc.cluster.local
```
If *k8s-scr-mgr* is not deployed to namespace ```default```, update the URL using the format:
```
<pod-name>.<namespace>.svc.cluster.local
```
Alternatively, you can set the Service URL by setting macro ```K8S_SCR_MGR_URL```. This could be done in the *SAS Studio Autoexec file*, to automatically set the URL every time you start *SAS Studio*.:
```
%let k8s_scr_mgr_url= %nrquote(k8s-scr-mgr.mynamespace.svc.cluster.local);

```

