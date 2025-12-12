## K8S-SCR-MGR Heml Chart
You can install k8s-scr-mgr using helm chart.

### Installing the Chart
Common parameter used for install:

| Parameter | Comment | Required |
| --- | --- | --- |
| --namespace | The namespace where *k8s-scr-mrg* is going to be installed.<br>**Default**: default | No |
| --set installName | The name under which *k8s-scr-mrg* is going to be installed.<br>**Default**: Releasename-Chartname | No |
| --set k8sScrMgr.viya_namespace | The namespace where Viya is installed.<br>**Default**: viya | No |
| --set k8sScrMgr.host | The external URL where *k8s-scr-mrg* is going to be installed. | Yes |
| --set dockerCredentials.baseRepoURL | The container registry location (URI) | Yes |
| --set dockerCredentials.registryId | The container registry user ID | Yes |
| --set dockerCredentials.registryPassword | The container registry password | Yes |
| --set-file kubeconfig | Fully qualified file name for the kubectl config file | Yes |




To install the chart with the release name *k8s-scr-mrg* run:

```
helm install k8s-scr-mgr ./k8sscrmgr \
--namespace k8sscrmgr \
--create-namespace \
--set installName=k8s-scr-mgr \
--set k8sScrMgr.viya_namespace=viya4 \
--set k8sScrMgr.host=ck09-sukckn.net.sas.com \
--set dockerCredentials.baseRepoURL=decisioning.azurecr.io \
--set dockerCredentials.registryId=decisioning \
--set dockerCredentials.registryPassword=NRoQbVCvdcBOcZZgURtIRKLq+ACRAbPpCz \
--set-file kubeconfig=$HOME/.kube/config \
--set dbCredentials.connectionstring="driver=sql;conopts=((driver=postgres;catalog=public;uid=sas;pwd='lnxsas';server= pg-demo-postgresql.default.svc.cluster.local;port=5431;DB=postgres;))"
```