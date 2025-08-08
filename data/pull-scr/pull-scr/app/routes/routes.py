
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
        return jsonify({'message': 'Welcome to the Pull SCR Service (version 0.12)!'}), 200

##########################################################################################
    @bp.route('/pull-scr', methods=['POST'])
    def pull_scr():
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
            'url': f'https://{host}:{port}/{DEPLOYMENT_NAME}'
                    }), 200

##########################################################################################
    @bp.route('/list-scr', methods=['GET'])
    def list_scr():
        namespace= current_app.config.get('NAMESPACE', 'default')

        # Run kubectl to get pods in JSON format
        command= ["kubectl", "get", "pods", "-n", namespace, "-o", "json"]
        try:
            result= subprocess.run(command, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error: {e.stderr.strip()}'
            return jsonify({"error": msg}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'{e}'}), status

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
            'ns': namespace,
            }), 200
##########################################################################################
    @bp.route('/delete-scr', methods=['POST'])
    def delete_scr():
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
            msg= f'Error: {e.stderr.strip()}'
            return jsonify({"error": msg}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'{e}'}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error: {result.stderr}'
            return jsonify({'error': f'{msg}'}), status

        # Delete the service
        try:
            result= subprocess.run(['kubectl', 'delete', 'service', DEPLOYMENT_NAME, '-n', namespace], capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error: {e.stderr.strip()}'
            return jsonify({"error": msg}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'{e}'}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error: {result.stderr}'
            return jsonify({'error': f'{msg}'}), status

        # Delete the ingress resource
        try:
            result= subprocess.run(['kubectl', 'delete', 'ingress', DEPLOYMENT_NAME, '-n', namespace], capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            status= 424 # Failed Dependency
            # Return an error response        
            msg= f'Error: {e.stderr.strip()}'
            return jsonify({"error": msg}), status
        except Exception as e:
            status= 424 # Failed Dependency
            # Return an error response  
            return jsonify({'error': f'{e}'}), status
        if len(result.stderr) > 0:
            status= 400 # Failed Dependency
            msg= f'Error: {result.stderr}'
            return jsonify({'error': f'{msg}'}), status

        # Return a response
        return jsonify({
            'message': f'Deployment {DEPLOYMENT_NAME} and associated resources deleted successfully.',
            'url': f'https://{host}:{port}/{DEPLOYMENT_NAME}'
                    }), 200

    return bp
