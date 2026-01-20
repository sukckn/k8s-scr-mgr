class Config:
    HOST= 'my-server.sas.com'
    CONTAINER_PREFIX= 'scr'
    VIYA_NAMESPACE= 'viya4'
    MAS_POD= 'sas-microanalytic-score'
    LIST_SCR= True
    PULL_SCR= True
    RESTART_SCR= True
    DELETE_SCR= True
    GETLOG_SCR= True
    GETLOG_MAS= True
    GETINFO_SCR= True
    PUBLISHING_DESTINATIONS= {
        'AzureDocker-PG': {
            'namespace': 'scr',
            'registry': 'myregistry.azurecr.io',
            'setDbSecret': True
        }
    }
