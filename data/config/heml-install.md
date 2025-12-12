## K8S-SCR-MGR Heml Chart
You can install k8s-scr-mgr using helm chart.

### Installing the Chart
To install the chart you have to set some parameters: 
| Parameter | Comment | Required |
| --- | --- | --- |
| --namespace | The namespace where *k8s-scr-mrg is going to be installed.<br>**Default**: default | No |
| --set installName | The name under which *k8s-scr-mrg* is going to be installed.<br>**Default**: Releasename-Chartname | No |
| --set k8sScrMgr.viya_namespace | The namespace where Viya is installed.<br>**Default**: viya | No |
| --set k8sScrMgr.host | The external URL where *k8s-scr-mrg* is going to be installed. | Yes |
| --set dockerCredentials.baseRepoURL | The container registry location (URI) | Yes |
| --set dockerCredentials.registryId | The container registry user ID | Yes |
| --set dockerCredentials.registryPassword | The container registry password | Yes |
| --set-file kubeconfig | Fully qualified file name for the kubectl config file | Yes |



