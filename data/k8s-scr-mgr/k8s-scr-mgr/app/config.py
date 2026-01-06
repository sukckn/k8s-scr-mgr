class Config:
    HOST= 'my-server.sas.com'
    PORT= '8080'
    NAMESPACE= 'scr'
    CONTAINER_PREFIX= 'scr'
    VIYA_NAMESPACE= 'viya4'
    MAS_POD= 'sas-microanalytic-score'
    LIST_SCR= True
    PULL_SCR= True
    RESTART_SCR= True
    DELETE_SCR= True
    GETLOG_SCR= True
    GETLOG_MAS= True
    NS_TO_REGISTRY_MAP= {
                        'scr': 'myregistry.azurecr.io'
                        } 