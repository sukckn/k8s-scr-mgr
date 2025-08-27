
from flask import request, jsonify, Blueprint, current_app
import json
from datetime import datetime, timezone
import subprocess

def create_blueprint(base_url):
    # Create a Blueprint for the pull-scr routes
    bp= Blueprint('pull-scr', __name__, url_prefix=base_url)

##########################################################################################
    @bp.route('/', methods=['GET'])
    @bp.route('/ping', methods=['GET'])
    def ping():
        return jsonify({'message': 'Welcome to Pull SCR Service (Version 0.18)!'}), 200

##########################################################################################
    @bp.route('/pull-scr', methods=['POST'])
    def pull_scr():
        endpoint_available= current_app.config.get('PULL_SCR', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/pull-scr" not available - Check pull-scr config settings if endpoint is switched on.'}), 404

        # Get JSON data from the request
        inputData= request.get_json()

        # set http status code
        status= 200

        # get input parameters
        SCR_NAME= inputData.get('scr_name')
        if not SCR_NAME:
            status= 400
            return jsonify({'error': 'Error: Parameter >scr_name< is required'}), status

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

        SET_DB_SECRET= int(inputData.get('db_secret'))
        if SET_DB_SECRET == None:
            status= 400
            return jsonify({'error': 'Error: Parameter >db_secret< is required'}), status

        # get parameters from config or use default
        namespace= current_app.config.get('NAMESPACE', 'default')
        host= current_app.config.get('HOST', '127.0.0.1')
        port= current_app.config.get('PORT', '8080')

        # Prepare the environment variables for the yaml file
        env= ''
        ENV_VARS= inputData.get('env_vars')
        if ENV_VARS:
            for v in ENV_VARS:
                na= list(v.keys())[0]
                val= v[list(v.keys())[0]]
                env+= f'        - name: "{na}"\n          value: "{val}"\n'

        db_secret_mount= ''
        db_secret_volume= ''
        if SET_DB_SECRET:
            db_secret_mount= '        - name: scr-db-secrets\n          mountPath: /opt/scr/secrets/db'
            db_secret_volume= '      - name: scr-db-secrets\n        secret:\n          secretName: scr-db-secrets\n          items:\n          - key: db.secrets\n            path: db.secrets'

        # Open yaml template and replace placeholders
        with open('./template/scr-template.yaml', 'r') as file:
            yaml_template= file.read()

        yaml_content= yaml_template.replace('<SCR-NAME>', SCR_NAME)
        yaml_content= yaml_content.replace('<APP-OWNER>', APP_OWNER)
        yaml_content= yaml_content.replace('<SCR-TAG>', SCR_TAG)
        yaml_content= yaml_content.replace('<IMAGE-PULL-POLICY>', IMAGE_PULL_POLICY)
        yaml_content= yaml_content.replace('<NAMESPACE>', namespace)
        yaml_content= yaml_content.replace('<HOST>', host)
        yaml_content= yaml_content.replace('<PORT>', port)
        yaml_content= yaml_content.replace('<ENV-VARS>', env)
        yaml_content= yaml_content.replace('<DB-SECRET-MOUNT>', db_secret_mount)
        yaml_content= yaml_content.replace('<DB-SECRET-VOLUME>', db_secret_volume)

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
            'url': f'https://{host}:{port}/{SCR_NAME}'
                    }), 200

##########################################################################################
    @bp.route('/restart-scr', methods=['POST'])
    def restart_scr():
        endpoint_available= current_app.config.get('RESTART_SCR', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/restart-scr" not available - Check pull-scr config settings if endpoint is switched on.'}), 404

        # Get JSON data from the request
        inputData= request.get_json()

        # set http status code
        status= 200

        # get input parameters
        DEPLOYMENT_NAME= inputData.get('deployment_name')
        if not DEPLOYMENT_NAME:
            status= 400
            return jsonify({'error': 'Error: Parameter >deployment_name< is required'}), status

        # get parameters from config or use default
        namespace= current_app.config.get('NAMESPACE', 'default')
        host= current_app.config.get('HOST', '127.0.0.1')
        port= current_app.config.get('PORT', '8080')

        try:
            result= subprocess.run(['kubectl', 'rollout', 'restart', 'deployment', DEPLOYMENT_NAME, '-n', namespace], capture_output=True, text=True)
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
            'url': f'https://{host}:{port}/{DEPLOYMENT_NAME}'
                    }), 200

##########################################################################################
    @bp.route('/list-scr', methods=['GET'])
    def list_scr():
        endpoint_available= current_app.config.get('LIST_SCR', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/list-scr" not available - Check pull-scr config settings if endpoint is switched on.'}), 404

        namespace= current_app.config.get('NAMESPACE', 'default')

        # Run kubectl to get pods 
        command= ["kubectl", "get", "pods", "-n", namespace, "-o", "json"]
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

        list= []
        heading= ['Pod Name', 'Status', 'Age', 'Deployment Name']
        list.append(heading)
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
            list.append([name, status, age_str, deployment_name])
        # Return the list as JSON
        return jsonify({
            'list':list,
            'ns': namespace
            }), 200

##########################################################################################
    @bp.route('/delete-scr', methods=['POST'])
    def delete_scr():
        endpoint_available= current_app.config.get('DELETE_SCR', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/delete-scr" not available - Check pull-scr config settings if endpoint is switched on.'}), 404

        # Get JSON data from the request
        inputData= request.get_json()

        # set http status code
        status= 200

        # get input parameters
        DEPLOYMENT_NAME= inputData.get('deployment_name')
        if not DEPLOYMENT_NAME:
            status= 400
            return jsonify({'error': 'Error: Parameter >deployment_name< is required'}), status

        # get parameters from config or use default
        namespace= current_app.config.get('NAMESPACE', 'default')
        host= current_app.config.get('HOST', '127.0.0.1')
        port= current_app.config.get('PORT', '8080')

        # Delete the deployment
        try:
            result= subprocess.run(['kubectl', 'delete', 'deployment', DEPLOYMENT_NAME, '-n', namespace], capture_output=True, text=True)
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
            result= subprocess.run(['kubectl', 'delete', 'service', DEPLOYMENT_NAME, '-n', namespace], capture_output=True, text=True)
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
            result= subprocess.run(['kubectl', 'delete', 'ingress', DEPLOYMENT_NAME, '-n', namespace], capture_output=True, text=True)
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
            return jsonify({'error': 'Endpoint "/getlog-scr" not available - Check pull-scr config settings if endpoint is switched on.'}), 404

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
        
        # get parameters from config or use default
        namespace= current_app.config.get('NAMESPACE', 'default')

        # Define the command to get podname
        command= f"kubectl get pods --namespace {namespace} | grep {POD_NAME}"

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
            return jsonify({'error': f'Pod with name "{POD_NAME}" not found in namespace "{namespace}".'}), status
        if len(result.stdout.splitlines()) > 1:
            status= 400 # Bad Request
            return jsonify({'error': f'Multiple pods found with name "{POD_NAME}" in namespace "{namespace}". Please specify a more specific pod name.'}), status

        podname= podname[0:podname.find(' ')]  # Extract the pod name from the output

        # Define the command to get log
        command= f"kubectl logs --namespace {namespace} {podname}"

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
    @bp.route('/getlog-mas', methods=['POST'])
    def getlog_mas():
        endpoint_available= current_app.config.get('GETLOG_MAS', False)
        if not endpoint_available:
            return jsonify({'error': 'Endpoint "/getlog-mas" not available - Check pull-scr config settings if endpoint is switched on.'}), 404

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

        prefix_pod_name= 'sas-microanalytic-score'
        # Define the command to get MAS pod namespace
        command= f"kubectl get pods --all-namespaces --no-headers | grep '{prefix_pod_name}' " +"| awk '{print $1}'"

        # get name space
        try:
            # Run the command
            result= subprocess.run(command, shell=True, capture_output=True, text=True)            
            namespace= result.stdout.strip().split('\n')
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error get namespace: {e.stderr.strip()}'
            return jsonify({"error": msg}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'Error get namespace: {e}'}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error get namespace: {result.stderr}'
            return jsonify({'error': f'{msg}'}), status
        if result.stdout[0:5] == 'Error':
            status= 400 # Failed Dependency
            msg= f'Error get namespace: {result.stdout}'
            return jsonify({'error': f'{msg}'}), status
        if not result.stdout:
            status= 404 # Not Found
            return jsonify({'error': f'Namespace not found for MAS pod.'}), status
        if len(result.stdout.splitlines()) > 1:
            status= 400 # Bad Request
            return jsonify({'error': f'Multiple pods found with name "{prefix_pod_name}" in namespace "{namespace}". Please specify a more specific pod name.'}), status

        # Define the command to get pod name
        #command= f"kubectl get pods --namespace {namespace} | grep {prefix_pod_name}"
        #command= ["kubectl", "get", "pods", "--namespace", namespace, "|", "grep", prefix_pod_name]
        command= ["kubectl", "get", "pods", "-n", "viya4"]

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
            return jsonify({'error': f'Pod with name "{prefix_pod_name}" not found in namespace "{namespace}".'}), status
#        if len(result.stdout.splitlines()) > 1:
#            status= 400 # Bad Request
#            return jsonify({'error': f'Multiple pods found with name "{prefix_pod_name}" in namespace "{namespace}". Please specify a more specific pod name.'}), status

        #podname= podname[0:podname.find(' ')]  # Extract the pod name from the output

        # Define the command to get log
        namespace= 'viya4'
#        command= f"kubectl logs --namespace {namespace} {podname}"
        command= ["kubectl", "logs", "--namespace", namespace, "sas-microanalytic-score-865c65779b-5k7t6", "-c", "sas-microanalytic-score"]

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
