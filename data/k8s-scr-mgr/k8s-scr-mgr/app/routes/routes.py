from flask import request, jsonify, Blueprint, current_app
import json
from datetime import datetime, timezone
import subprocess
import base64

##########################################################################################
def pub_dest(inputData, lookup):
    msg= ''
    # get settings for publishing destinations from config mapping
    PUBLISHING_DESTINATIONS= current_app.config.get('PUBLISHING_DESTINATIONS', {})
    if not PUBLISHING_DESTINATIONS:
        msg= 'Error: No publishing destinations found in k8s-scr-mgr config.'
        return None, msg

    # get publishing destination from input parameters. If not provided, use the first one from the config mapping
    pub_dest_name= inputData.get('pub_dest_name')
    if not pub_dest_name:
        pub_dest_name= list(PUBLISHING_DESTINATIONS.keys())[0]
    pub_dest_name= pub_dest_name.lower()

    if lookup == 'pub_dest_name':
        return pub_dest_name, msg   

    if not PUBLISHING_DESTINATIONS.get(pub_dest_name):
        msg= f'Error: Publishing destination >{pub_dest_name}< not found in k8s-scr-mgr config.\nAvailable Publishing Destinations: {list(PUBLISHING_DESTINATIONS.keys())}'
        return None, msg

    # get namespace, registry or setDbSecret from publishing destination
    lookup_value= PUBLISHING_DESTINATIONS[pub_dest_name].get(lookup, '')
    if len(lookup_value) == 0:
        msg= f'Error: Parameter >{lookup}< not set for publishing destination >{pub_dest_name}<'
        return None, msg

    return lookup_value, msg

##########################################################################################
def create_blueprint(base_url, k8s_scr_mgr_version):
    # Create a Blueprint for the k8s-scr-mgr routes
    bp= Blueprint('k8s-scr-mgr', __name__, url_prefix=base_url)

##########################################################################################
    @bp.route('/', methods=['GET'])
    @bp.route('/ping', methods=['GET'])
    def ping():
        return jsonify({'message': f'Welcome to K8S SCR Manager Service (Version {k8s_scr_mgr_version})!'}), 200

##########################################################################################
    @bp.route('/pull-scr', methods=['POST'])
    def pull_scr():
        endpoint_available= current_app.config.get('PULL_SCR', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/pull-scr" not available - Check k8s-scr-mgr config settings if endpoint is switched on.'}), 404

        # Get JSON data from the request
        inputData= request.get_json()

        # set http status code
        status= 200

        # get scr image name from input parameters
        IMAGE_NAME= inputData.get('image_name')
        if not IMAGE_NAME:
            status= 400
            return jsonify({'error': 'Error: Parameter >image_name< is required'}), status
        IMAGE_NAME= IMAGE_NAME.lower() # Kubernetes image names must be lowercase

        # get deployment name. If not provided, derive from image name
        SCR_NAME= inputData.get('deployment_name')
        if not SCR_NAME:
            SCR_NAME= IMAGE_NAME.replace('_', '-') # Kubnernetes cannot contain underscores
        else:
            SCR_NAME= SCR_NAME.lower() # Kubernetes deployment names must be lowercase

        # set the endpoint for SCR to be called on. By default it is the same as the deployment name
        SCR_ENDPOINT= inputData.get('scr_endpoint')
        if not SCR_ENDPOINT:
            SCR_ENDPOINT= SCR_NAME   

        # get number of replicas. Default is 1
        REPLICAS= str(inputData.get('replicas', 1))

        # the container image tag in the registry
        SCR_TAG= inputData.get('scr_tag')
        if not SCR_TAG:
            status= 400
            return jsonify({'error': 'Error: Parameter >scr_tag< is required'}), status

        APP_OWNER= inputData.get('app_owner')
        if not APP_OWNER:
            status= 400
            return jsonify({'error': 'Error: Parameter >app_owner< is required'}), status

        IMAGE_PULL_POLICY= inputData.get('image_pull_policy')
        if not IMAGE_PULL_POLICY:
            status= 400
            return jsonify({'error': 'Error: Parameter >image_pull_policy< is required'}), status

        # get namespace from publishing destination
        namespace, msg= pub_dest(inputData, 'namespace')
        if msg:
            status= 400
            return jsonify({'error': msg}), status

        # get indicator if db secret is to be mounted (true/false)
        SET_DB_SECRET, msg= pub_dest(inputData, 'setDbSecret')
        if msg:
            status= 400
            return jsonify({'error': msg}), status

        # get container registry from publishing destination
        container_registry, msg= pub_dest(inputData, 'registry')
        if msg:
            status= 400
            return jsonify({'error': msg}), status

        # get publishing destination name
        pub_dest_name, msg= pub_dest(inputData, 'pub_dest_name')
        if msg:
            status= 400
            return jsonify({'error': msg}), status

        # get docker pull secret name
        docker_pull_secret= f'pull-{pub_dest_name}'.lower()

        # get parameters from config or use default
        host= current_app.config.get('HOST', None)
        if host is None:
            status= 400
            return jsonify({'error': 'Error: Parameter >host< not set in k8s-scr-mgr config.'}), status

        cont_prefix= current_app.config.get('CONTAINER_PREFIX', '')

        # if a prefix for the SCR container is to be set we add an dash (-) to it
        if len(cont_prefix) > 0:
            cont_prefix= cont_prefix + '-'

        # Prepare the environment variables for the yaml file
        env= '        env:\n'
        ENV_VARS= inputData.get('env_vars')
        if ENV_VARS:
            for v in ENV_VARS:
                na= list(v.keys())[0]
                val= v[list(v.keys())[0]]
                env+= f'        - name: "{na}"\n          value: "{val}"\n'

        # set the db secret name. It is: db-<pub_dest_name>
        db_secret_name= f'db-{pub_dest_name}'.lower()
        db_secret_mount= ''
        db_secret_volume= ''
        if SET_DB_SECRET:
            db_secret_mount= '        - name: scr-db-secrets\n          mountPath: /opt/scr/secrets/db'
            db_secret_volume= f'      - name: scr-db-secrets\n        secret:\n          secretName: {db_secret_name}\n          items:\n          - key: db.secrets\n            path: db.secrets'

        # Open yaml template and replace placeholders
        with open('./template/scr-template.yaml', 'r') as file:
            yaml_template= file.read()

        yaml_content= yaml_template.replace('<CONTAINER-REGISTRY>', container_registry)
        yaml_content= yaml_content.replace('<IMAGE-NAME>', IMAGE_NAME)
        yaml_content= yaml_content.replace('<SCR-NAME>', SCR_NAME)
        yaml_content= yaml_content.replace('<APP-OWNER>', APP_OWNER)
        yaml_content= yaml_content.replace('<SCR-TAG>', SCR_TAG)
        yaml_content= yaml_content.replace('<IMAGE-PULL-POLICY>', IMAGE_PULL_POLICY)
        yaml_content= yaml_content.replace('<NAMESPACE>', namespace)
        yaml_content= yaml_content.replace('<HOST>', host)
        yaml_content= yaml_content.replace('<PREFIX>', cont_prefix)
        yaml_content= yaml_content.replace('<ENV-VARS>', env)
        yaml_content= yaml_content.replace('<DB-SECRET-MOUNT>', db_secret_mount)
        yaml_content= yaml_content.replace('<DB-SECRET-VOLUME>', db_secret_volume)
        yaml_content= yaml_content.replace('<SCR-ENDPOINT>', SCR_ENDPOINT)
        yaml_content= yaml_content.replace('<DOCKER-PULL-SECRET>', docker_pull_secret)
        yaml_content= yaml_content.replace('<REPLICAS>', REPLICAS)

        # Write the modified content to a new yaml file
        yaml_file= f'./yaml/scr-{SCR_NAME}.yaml'
        with open(yaml_file, "w", encoding="utf-8") as file:
            file.write(yaml_content)

        # Apply the yaml file using kubectl
        try:
            result= subprocess.run(['kubectl', '--kubeconfig=/tmp/config', 'apply', '-f', yaml_file], capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error: {e.stderr.strip()}'
            return jsonify({"error": msg}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'{e}'}), status
        
        msg= f'\n{result.stdout}'
        if len(result.stderr) > 0:
            msg= f'Error: {result.stderr}'
        # Return a response
        return jsonify({
            'message': msg,
            'url': f'https://{host}/{SCR_ENDPOINT}',
            'url_internal': f'http://{SCR_NAME}.{namespace}.svc.cluster.local/{SCR_ENDPOINT}'
                    }), 200

##########################################################################################
    @bp.route('/restart-scr', methods=['POST'])
    def restart_scr():
        endpoint_available= current_app.config.get('RESTART_SCR', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/restart-scr" not available - Check k8s-scr-mgr config settings if endpoint is switched on.'}), 404

        # Get JSON data from the request
        inputData= request.get_json()

        # set http status code
        status= 200

        # get input parameters
        DEPLOYMENT_NAME= inputData.get('deployment_name')
        if not DEPLOYMENT_NAME:
            status= 400
            return jsonify({'error': 'Error: Parameter >deployment_name< is required'}), status

        # get namespace from publishing destination
        namespace, msg= pub_dest(inputData, 'namespace')
        if msg:
            status= 400
            return jsonify({'error': msg}), status

        # get parameters from config or use default
        host= current_app.config.get('HOST', None)
        if host is None:
            status= 400
            return jsonify({'error': 'Error: Parameter >host< not set in k8s-scr-mgr config.'}), status

        try:
            result= subprocess.run(['kubectl', '--kubeconfig=/tmp/config', 'rollout', 'restart', 'deployment', DEPLOYMENT_NAME, '-n', namespace], capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'{e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

        msg= f'\n{result.stdout}'
        if len(result.stderr) > 0:
            msg= f'Error: {result.stderr}'
        # Return a response
        return jsonify({
            'message': msg,
            'url': f'https://{host}/{DEPLOYMENT_NAME}'
                    }), 200

##########################################################################################
    @bp.route('/list-scr', methods=['GET'])
    def list_scr():
        endpoint_available= current_app.config.get('LIST_SCR', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/list-scr" not available - Check k8s-scr-mgr config settings if endpoint is switched on.'}), 404

        inputData= request.args
        # get namespace from publishing destination
        namespace, msg= pub_dest(inputData, 'namespace')
        if msg:
            status= 400
            return jsonify({'error': msg}), status

        # Run kubectl to get pods 
        command= ["kubectl", '--kubeconfig=/tmp/config', "get", "pods", "-n", namespace, "-o", "json"]
        try:
            result= subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'{e}', 'ns': namespace}), status

        # Parse JSON
        pods= json.loads(result.stdout)

        k8s_list= []
        heading= ['Pod Name', 'Status', 'Age', 'Deployment Name']
        k8s_list.append(heading)
        # Print pod name, status, age, and deployment name
        for pod in pods["items"]:
            name= pod["metadata"]["name"]
            status= pod["status"]["phase"]
            deletion_timestamp = pod["metadata"].get("deletionTimestamp")
            if deletion_timestamp:
                status = "Terminating"
            created_at= pod["metadata"]["creationTimestamp"]
            created_time= datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            age= datetime.now(timezone.utc) - created_time

            # Format age down to seconds
            days= age.days
            hours, remainder= divmod(age.seconds, 3600)
            minutes, seconds= divmod(remainder, 60)
            age_str= f"{days}d {hours}h {minutes}m {seconds}s"

            # Get deployment name from ownerReferences
            owner_refs= pod["metadata"].get("ownerReferences", [])
            replicaset_name= next(
                (ref["name"] for ref in owner_refs if ref["kind"] == "ReplicaSet"),
                "Unknown"
            )

            # Infer deployment name by stripping the hash suffix
            deployment_name= "-".join(replicaset_name.split("-")[:-1]) if replicaset_name != "Unknown" else "Unknown"

            # Append to the list
            k8s_list.append([name, status, age_str, deployment_name])
        # Return the list as JSON
        return jsonify({
            'list':k8s_list,
            'ns': namespace
            }), 200

##########################################################################################
    @bp.route('/delete-scr', methods=['POST'])
    def delete_scr():
        endpoint_available= current_app.config.get('DELETE_SCR', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/delete-scr" not available - Check k8s-scr-mgr config settings if endpoint is switched on.'}), 404

        # Get JSON data from the request
        inputData= request.get_json()

        # set http status code
        status= 200

        # get input parameters
        DEPLOYMENT_NAME= inputData.get('deployment_name')
        if not DEPLOYMENT_NAME:
            status= 400
            return jsonify({'error': 'Error: Parameter >deployment_name< is required'}), status

        # get namespace from publishing destination
        namespace, msg= pub_dest(inputData, 'namespace')
        if msg:
            status= 400
            return jsonify({'error': msg}), status

        # Delete the deployment
        try:
            result= subprocess.run(['kubectl', '--kubeconfig=/tmp/config', 'delete', 'deployment', DEPLOYMENT_NAME, '-n', namespace], capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error delete deployment: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'Error delete deployment: {e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error delete deployment: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

        # Delete the service
        try:
            result= subprocess.run(['kubectl', '--kubeconfig=/tmp/config', 'delete', 'service', DEPLOYMENT_NAME, '-n', namespace], capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error delete service: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'Error delete service: {e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error delete service: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

        # Delete the ingress resource
        try:
            result= subprocess.run(['kubectl', '--kubeconfig=/tmp/config', 'delete', 'ingress', DEPLOYMENT_NAME, '-n', namespace], capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error delete ingress: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'Error delete ingress: {e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error delete ingress: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

        # Return a response
        return jsonify({
            'message': f'Deployment {DEPLOYMENT_NAME} and associated resources deleted successfully.'
                    }), 200

##########################################################################################
    @bp.route('/getlog-scr', methods=['POST'])
    def getlog_scr():
        endpoint_available= current_app.config.get('GETLOG_SCR', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/getlog-scr" not available - Check k8s-scr-mgr config settings if endpoint is switched on.'}), 404

        # Get JSON data from the request
        inputData= request.get_json()

        # set http status code
        status= 200

        # get input parameters
        POD_NAME= inputData.get('pod_name')
        if not POD_NAME:
            status= 400
            return jsonify({'error': 'Error: Parameter >pod_name< is required'}), status
        SHOW_ROWS= inputData.get('show_rows')
        if not SHOW_ROWS:
            status= 400
            return jsonify({'error': 'Error: Parameter >show_rows< is required'}), status
        if SHOW_ROWS not in ['ALL', 'TOP', 'BOTTOM']:
            status= 400
            return jsonify({'error': 'Error: Parameter >show_rows< must be either >ALL< or >TOP< or >BOTTOM<'}), status
        NUM_ROWS= int(inputData.get('num_rows'))
        if not NUM_ROWS:
            status= 400
            return jsonify({'error': 'Error: Parameter >num_rows< is required'}), status
        if NUM_ROWS < 0:
            status= 400
            return jsonify({'error': 'Error: Parameter >num_rows< must be greater than or equal to 0'}), status

        # get namespace from publishing destination
        namespace, msg= pub_dest(inputData, 'namespace')
        if msg:
            status= 400
            return jsonify({'error': msg}), status

        # Define the command to get podname
        command= f"kubectl get pods --kubeconfig=/tmp/config --namespace {namespace} | grep {POD_NAME}"

        # get pod name
        try:
            # Run the command
            result= subprocess.run(command, shell=True, capture_output=True, text=True)            
            podname= result.stdout
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error get podname: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'pod_name': POD_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'Error get podname: {e}', 'ns': namespace, 'pod_name': POD_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error get podname: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'pod_name': POD_NAME}), status
        if result.stdout[0:5] == 'Error':
            status= 400 # Failed Dependency
            msg= f'Error get podname: {result.stdout}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'pod_name': POD_NAME}), status
        if not result.stdout:
            status= 404 # Not Found
            return jsonify({'error': f'Pod with name >{POD_NAME}< not found in namespace >{namespace}<.'}), status
        if len(result.stdout.splitlines()) > 1:
            status= 400 # Bad Request
            return jsonify({'error': f'Multiple pods found with name >{POD_NAME}< in namespace >{namespace}<. Please specify a more specific pod name.'}), status

        podname= podname[0:podname.find(' ')]  # Extract the pod name from the output

        # Define the command to get log
        command= f"kubectl logs --kubeconfig=/tmp/config --namespace {namespace} {podname}"

        log= []
        try:
            # Run the command
            result= subprocess.run(command, shell=True, capture_output=True, text=True)

            # get log line by line
            for line in result.stdout.splitlines():
                log.append(line.strip())
        
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error get log: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'pod_name': POD_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'Error get log: {e}', 'ns': namespace, 'pod_name': POD_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error get log: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'pod_name': POD_NAME}), status
        if result.stdout[0:5] == 'Error':
            status= 400 # Failed Dependency
            msg= f'Error get log: {result.stdout}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'pod_name': POD_NAME}), status

        if SHOW_ROWS == 'TOP':
            log= log[:NUM_ROWS] # Limit the number of log lines to top NUM_ROWS
        elif SHOW_ROWS == 'BOTTOM':
            log= log[len(log)-NUM_ROWS:] # Limit the number of log lines to bottom NUM_ROWS

        log.insert(0, 'Log')  # Add a header to the log list
        # Return the list as JSON
        return jsonify({
            'log':log,
            'ns': namespace,    
            'pod_name': podname
            }), 200

##########################################################################################
    @bp.route('/getinfo-scr', methods=['POST'])
    def getinfo_scr():
        endpoint_available= current_app.config.get('GETINFO_SCR', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/getinfo-scr" not available - Check k8s-scr-mgr config settings if endpoint is switched on.'}), 404

        # Get JSON data from the request
        inputData= request.get_json()

        # set http status code
        status= 200

        # get input parameters
        DEPLOYMENT_NAME= inputData.get('deployment_name')
        if not DEPLOYMENT_NAME:
            status= 400
            return jsonify({'error': 'Error: Parameter >deployment_name< is required'}), status

        # get namespace from publishing destination
        namespace, msg= pub_dest(inputData, 'namespace')
        if msg:
            status= 400
            return jsonify({'error': msg}), status

        ##############################################################################################################################
        # Define the command to get environment information
        command= f"kubectl get deployment {DEPLOYMENT_NAME} -n {namespace} " + "-o jsonpath={.spec.template.spec.containers[*].env}"
        try:
            # Run the command
            result= subprocess.run(command, shell=True, capture_output=True, text=True)            
            env_vars= result.stdout
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error get environment variables: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response
            return jsonify({'error': f'Error get environment variables: {e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error getting environment information: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

        ##############################################################################################################################
        # Define the command to get host from ingress
        command= f"kubectl get ingress {DEPLOYMENT_NAME} -n {namespace} " + "-o jsonpath={.spec.rules[*].host}"        
        try:
            # Run the command
            result= subprocess.run(command, shell=True, capture_output=True, text=True)
            host= result.stdout
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response
            msg= f'Error get host from ingress: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response
            return jsonify({'error': f'Error get host from ingress: {e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error getting host from ingress: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

        ##############################################################################################################################
        # Define the command to get path from ingress
        command= f"kubectl get ingress {DEPLOYMENT_NAME} -n {namespace} " + "-o jsonpath={.spec.rules[0].http.paths[0].path}"        
        try:
            # Run the command
            result= subprocess.run(command, shell=True, capture_output=True, text=True)
            path= result.stdout
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response
            msg= f'Error get path from ingress: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response
            return jsonify({'error': f'Error get path from ingress: {e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error getting path from ingress: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

        ##############################################################################################################################
        # Define the command to get number of replicas from deployment
        command= f"kubectl get deployment {DEPLOYMENT_NAME} -n {namespace} " + "-o jsonpath={.spec.replicas}"        
        try:
            # Run the command
            result= subprocess.run(command, shell=True, capture_output=True, text=True)
            replicas= result.stdout
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response
            msg= f'Error get replicas from deployment: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response
            return jsonify({'error': f'Error get replicas from deployment: {e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error getting replicas from deployment: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

        ##############################################################################################################################
        # Define the command to get app-owner from deployment
        command= f"kubectl get deployment {DEPLOYMENT_NAME} -n {namespace} " + "-o jsonpath={.metadata.labels.app-owner}"        
        try:
            # Run the command
            result= subprocess.run(command, shell=True, capture_output=True, text=True)
            app_owner= result.stdout
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response
            msg= f'Error get app-owner from deployment: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response
            return jsonify({'error': f'Error get app-owner from deployment: {e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error getting app-owner from deployment: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

        ##############################################################################################################################
        # Define the command to get image info from deployment
        command= f"kubectl get deployment {DEPLOYMENT_NAME} -n {namespace} " + "-o jsonpath={.spec.template.spec.containers[*].image}"        
        try:
            # Run the command
            result= subprocess.run(command, shell=True, capture_output=True, text=True)
            image_info= result.stdout
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response
            msg= f'Error get image info from deployment: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response
            return jsonify({'error': f'Error get image info from deployment: {e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error getting image info from deployment: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

        # extract tag from image info
        if ':' in image_info:
            tag= image_info.split(':')[-1]
        else:
            tag= 'latest'

        # extract container registry from image info
        if '/' in image_info:
            container_registry= '/'.join(image_info.split('/')[:-1])
        else:
            container_registry= 'Did not find container registry in image info'
        
        # extract image name from image info
        image_name= image_info.split('/')[-1].split(':')[0]
        if not image_name:
            image_name= 'Did not find image name in image info'

         ##############################################################################################################################
        # Define the command to get imagePullPolicy from deployment
        command= f"kubectl get deployment {DEPLOYMENT_NAME} -n {namespace} " + "-o jsonpath={.spec.template.spec.containers[*].imagePullPolicy}"        
        try:
            # Run the command
            result= subprocess.run(command, shell=True, capture_output=True, text=True)
            imagePullPolicy= result.stdout
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response
            msg= f'Error get imagePullPolicy info from deployment: {e.stderr.strip()}'
            return jsonify({"error": msg, 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response
            return jsonify({'error': f'Error get imagePullPolicy info from deployment: {e}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error getting imagePullPolicy info from deployment: {result.stderr}'
            return jsonify({'error': f'{msg}', 'ns': namespace, 'deployment_name': DEPLOYMENT_NAME}), status

       ##############################################################################################################################
        # Return result as JSON
        return jsonify({
            'env_vars': env_vars,
            'replicas': replicas,
            'app_owner': app_owner,
            'image_name': image_name,
            'container_registry': container_registry,
            'tag': tag,
            'imagePullPolicy': imagePullPolicy,
            'url': f'https://{host}{path}',
            'url_internal': f'http://{DEPLOYMENT_NAME}.{namespace}.svc.cluster.local{path}',
            'ns': namespace,
            'deployment_name': DEPLOYMENT_NAME
        }), 200


##########################################################################################
    @bp.route('/getlog-mas', methods=['POST'])
    def getlog_mas():
        endpoint_available= current_app.config.get('GETLOG_MAS', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/getlog-mas" not available - Check k8s-scr-mgr config settings if endpoint is switched on.'}), 404

        # Get JSON data from the request
        inputData= request.get_json()

        # set http status code
        status= 200

        # get input parameters
        SHOW_ROWS= inputData.get('show_rows')
        if not SHOW_ROWS:
            status= 400
            return jsonify({'error': 'Error: Parameter >show_rows< is required'}), status
        if SHOW_ROWS not in ['ALL', 'TOP', 'BOTTOM']:
            status= 400
            return jsonify({'error': 'Error: Parameter >show_rows< must be either >ALL< or >TOP< or >BOTTOM<'}), status
        NUM_ROWS= int(inputData.get('num_rows'))
        if not NUM_ROWS:
            status= 400
            return jsonify({'error': 'Error: Parameter >num_rows< is required'}), status
        if NUM_ROWS < 0:
            status= 400
            return jsonify({'error': 'Error: Parameter >num_rows< must be greater than or equal to 0'}), status

        prefix_pod_name= current_app.config.get('MAS_POD', 'sas-microanalytic-score')
        # get parameters from config
        namespace= current_app.config.get('VIYA_NAMESPACE', 'default')

        command= ["kubectl", '--kubeconfig=/tmp/config', "get", "pods", "-n", namespace]

        # get podname
        try:
            # Run the command
            result = subprocess.run(command, check=True, capture_output=True, text=True)

            # Process the output
            lines = result.stdout.strip().split('\n')
            matching_pods = [line.split()[0] for line in lines if prefix_pod_name in line]
            podname = matching_pods[0] if matching_pods else None
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error get podname: {e.stderr.strip()}'
            return jsonify({"error": msg}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'Error  get podname: {e}'}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error get podname: {result.stderr}'
            return jsonify({'error': f'{msg}'}), status
        if result.stdout[0:5] == 'Error':
            status= 400 # Failed Dependency
            msg= f'Error get podname: {result.stdout}'
            return jsonify({'error': f'{msg}'}), status
        if not result.stdout:
            status= 404 # Not Found
            return jsonify({'error': f'Pod with name >{prefix_pod_name}< not found in namespace >{namespace}<.'}), status

        # Define the command to get log
        command= ["kubectl", '--kubeconfig=/tmp/config', "logs", "--namespace", namespace, podname, "-c", "sas-microanalytic-score"]

        log= []
        try:
            # Run the command
            result= subprocess.run(command, capture_output=True, text=True)

            # get log line by line
            for line in result.stdout.splitlines():
                log.append(line.strip())
        
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error get log: {e.stderr.strip()}'
            return jsonify({"error": msg,'ns': namespace, 'pod_name': podname}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'Error  get log: {e}','ns': namespace, 'pod_name': podname}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error get log: {result.stderr}'
            return jsonify({'error': f'{msg}','ns': namespace, 'pod_name': podname}), status
        if result.stdout[0:5] == 'Error':
            status= 400 # Failed Dependency
            msg= f'Error get log: {result.stdout}'
            return jsonify({'error': f'{msg}','ns': namespace, 'pod_name': podname}), status

        if SHOW_ROWS == 'TOP':
            log= log[:NUM_ROWS] # Limit the number of log lines to top NUM_ROWS
        elif SHOW_ROWS == 'BOTTOM':
            log= log[len(log)-NUM_ROWS:] # Limit the number of log lines to bottom NUM_ROWS

        log.insert(0, 'Log')  # Add a header to the log list
        # Return the list as JSON
        return jsonify({
            'log':log,
            'ns': namespace,    
            'pod_name': podname
            }), 200

##########################################################################################
    # Return the Blueprint object
    return bp
