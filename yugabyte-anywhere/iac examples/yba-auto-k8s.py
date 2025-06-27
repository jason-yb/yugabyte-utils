#!/usr/bin/env python3

import requests, json, time, configparser, urllib3, uuid, sys
from datetime import datetime, date, timedelta

# delay between checks on task
waitTime = 10

# set your ini file and default section
iniFile = "k8s-api.ini"
iniSection = "demo"

# defaults - no change required
env = {}
url = {}
verify_ssl = True
auto_exit = False

def read_config(ini_file,ini_section):
    global env
    global verify_ssl
    # Read config as dict object
    config = configparser.ConfigParser()
    config.read(ini_file)
    if config.has_section(ini_section):
        for name, value in config.items(ini_section):
            env[name] = value
        if env["verify_ssl"].upper()=='NO':
            verify_ssl = False
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)   
    else:
        print(f"ERROR: Section not found - {ini_section}")
        exit()

    return config

def read_ini_sections():
    config = configparser.ConfigParser()
    config.read(iniFile)
    return config.sections()
            
def select_ini_section():
    config = configparser.ConfigParser()
    config.read(iniFile)
    sections_list=config.sections()
    print("\nSelect an ini section:")
    for i, section in enumerate(sections_list, start=1):
        print(f"{i}. {section}")
    while True:
        try:
            user_input = int(input("Enter the number of the section:"))
            if 1 <= user_input <= len(sections_list):
                return sections_list[user_input - 1]
            else:
                print("Invalid input. Please enter a valid number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
def set_urls():
    global url
    global env
    # Set all base URLs
    url['base'] = f"https://{env['host_url']}/api/v1"
    url['register'] = f"{url['base']}/register"
    url['customer'] = f"{url['base']}/customers/{env['customer_id']}"
    url['providers'] = f"{url['customer']}/providers"
    url['provider'] = f"{url['customer']}/providers/{env['provider_id']}"
    url['cluster'] = f"{url['customer']}/universes/clusters"
    url['universe'] = f"{url['customer']}/universes/{env['universe_id']}"
    url['universes'] = f"{url['customer']}/universes"
    url['release'] = f"{url['customer']}/ybdb_release"
    url['k8s-override'] = f"{url['universe']}/upgrade/kubernetes_overrides"
    url['gflags'] = f"{url['universe']}/upgrade/gflags"
    url['configs'] = f"{url['customer']}/configs"
    url['backup-schedule'] = f"{url['customer']}/create_backup_schedule"
    url['tasks'] = f"{url['customer']}/tasks/"
    url['task-list'] = f"{url['customer']}/tasks_list"
    url['tables'] = f"{url['universe']}/tables"
    url['perf-rec'] = f"{url['customer']}/performance_recommendations/page"
    url['users'] = f"{url['customer']}/users"

def print_menu():
    print("\nMenu:")
    print("1. Register System")
    print("2. Create Provider")
    print("3. Create S3 Storage")
    print("4. Create Universe")
    print("5. Create Backup Schedule")
    print("6. List Universes")
    print("7. List Recent Tasks")
    print("8. List Tables")
    print("9. Delete Universe")
    print("10. Update Universe - add k8s override")
    print("11. Update Universe - add gflag")
    print("12. Update Universe - add 3 nodes")   
    print("13. Performance Advisor")  
    print("14. Lists Users")  
    print("15. Add 100 Users")      
    print("16. Update Universe - k8s set dedicated nodes")
    print("17. Update Universe - k8s shrink master")
    print("18. Add Release")  
    print("s. Switch INI Section")
    print("x. Exit")
    print("Config:")
    print(f"ini section: {iniSection}")
    print("")
    
def register_system(config):
    print("Registering System")
    print(url['register'])
    headers = {
        'Content-Type': "application/json"}

    querystring = {"generateApiToken":"true"}

    register = {
        "code": "api-demo",
        "email": env["admin_email"],
        "name": env["admin_name"],
        "password": env["admin_password"]
    }

    # register
    try:
        response = requests.post(url['register'], headers=headers, json=register, params=querystring, verify=verify_ssl)
        
        if response.status_code != 200: 
            print("Error occurred during the request.")
            print("Status code:", response.status_code)
            print("Error message:", response.json().get("error"))
        else:
            print("Request was successful.")
            register_result=json.loads(response.text)
            apiToken=register_result['apiToken']
            customerUUID=register_result['customerUUID']
                    
            config.set(iniSection, f"api_token", apiToken)
            config.set(iniSection, f"customer_id", customerUUID)
            with open(iniFile, 'w') as config_file:
                config.write(config_file)

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the server: {e}")
               
def create_provider(config):
    print("Reading Suggested k8s Provider")
    
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
    }
    
    response = requests.get(f"{url['providers']}/suggested_kubernetes_config", headers=headers, verify=verify_ssl)
    suggested_config=json.loads(response.text)
    provider = {
        'code': suggested_config['code'],
        'name': 'api-provider',
        'details': {
            'cloudInfo': {
                'kubernetes': {
                    'kubernetesImageRegistry': suggested_config['config']['KUBECONFIG_IMAGE_REGISTRY'],
                    'kubernetesProvider': suggested_config['config']['KUBECONFIG_PROVIDER'].lower(),
                    'kubernetesPullSecretContent': suggested_config['config']['KUBECONFIG_PULL_SECRET_CONTENT'],
                    'kubernetesPullSecretName': suggested_config['config']['KUBECONFIG_PULL_SECRET_NAME'],
                    'kubernetesImagePullSecretName': suggested_config['config']['KUBECONFIG_IMAGE_PULL_SECRET_NAME']
                }
            }
        },
        'regions': [
            {
                'code': suggested_config['regionList'][0]['code'],
                'name': suggested_config['regionList'][0]['name'],
                'zones': [
                    {
                        'code': zone['code'],
                        'name': zone['name'],
                        'details': {
                            'cloudInfo': {
                                'kubernetes': {
                                    'kubernetesStorageClass': env['storage_class'],
                                    'overrides':  
"""
nodeSelector:
  yugabyte: 'ybdb'
master:
  podLabels:
    sidecar.istio.io/inject: 'false'
tserver:
  podLabels:
    sidecar.istio.io/inject: 'false'"""           }
                            }
                        }
                    } for zone in suggested_config['regionList'][0]['zoneList']
                ]
            }
        ]
    }
    # create provider
    print("Creating Provider")
    response = requests.post(url['providers'], headers=headers, json=provider, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")
        create_result=json.loads(response.text)
        taskUUID=create_result['taskUUID']
        resourceUUID=create_result['resourceUUID']
        print(f"Task is running - polling status every {waitTime} seconds.")
        while True:
            response = requests.get(f"{url['tasks']}{taskUUID}", headers=headers, verify=verify_ssl)
            taskStatusJson = json.loads(response.text)
            if taskStatusJson["status"] == "Running":
                print(f"Current task status is: {taskStatusJson['status']} - {taskStatusJson['percent']} Percent")
                time.sleep(waitTime)
            else:
                print(f"Task finished. Result: {taskStatusJson['status']}.")
                break
            
        config.set(iniSection, f"provider_id", resourceUUID)
        with open(iniFile, 'w') as config_file:
            config.write(config_file)    

def create_zone(code, name, kube_config_content):
    return {
        "code": code,
        "name": name,
        "details": {
            "cloudInfo": {
                "kubernetes": {
                    "kubeConfigContent": kube_config_content,
                    "kubeConfigName": f"kubeconf-{code}.conf",
                    "kubePodAddressTemplate": "{pod_name}.{namespace}.svc.{cluster_domain}",
                    "kubernetesStorageClass": "yb-sc",
                    "overrides": "istioCompatibility:\n  enabled: true\nmulticluster:\n  createServicePerPod: true\nnodeSelector:\n  yugabyte: ybdb"
                }
            }
        }
    }

def create_region(code, name, kube_config_content, zones):
    return {
        "code": code,
        "name": name,
        "zones": [create_zone(zone_code, zone_name, kube_config_content) for zone_code, zone_name in zones],
        "details": {
            "cloudInfo": {
                "kubernetes": {}
            }
        }
    }


def create_multi_provider(config):
    
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
    }

    with open('/Users/jnorwood/Documents/emea-secret.yaml', 'r') as secret_file:
        kubernetes_pull_secret_content = secret_file.read()

    with open('/Users/jnorwood/environments/l-and-g/azure-test/kubeconf-uk-south.conf', 'r') as kubeconf_south_file:
        kubeconf_uk_south = kubeconf_south_file.read()

    with open('/Users/jnorwood/environments/l-and-g/azure-test/kubeconf-north-europe.conf', 'r') as kubeconf_north_file:
        kubeconf_eu_north = kubeconf_north_file.read()
        
    with open('/Users/jnorwood/environments/l-and-g/azure-test/kubeconf-west-europe.conf', 'r') as kubeconf_west_file:
        kubeconf_eu_west = kubeconf_west_file.read()

    # Define the zones for each region
    uksouth_zones = [("uksouth-1", "uksouth-1"), ("uksouth-2", "uksouth-2"), ("uksouth-3", "uksouth-3")]
    northeurope_zones = [("northeurope-1", "northeurope-1"), ("northeurope-2", "northeurope-2"), ("northeurope-3", "northeurope-3")]
    westeurope_zones = [("westeurope-1", "westeurope-1"), ("westeurope-2", "westeurope-2"), ("westeurope-3", "westeurope-3")]

    # Define the regions
    regions = [
        create_region("uksouth", "UK South", kubeconf_uk_south, uksouth_zones),
        create_region("northeurope", "North Europe", kubeconf_eu_north, northeurope_zones),
        create_region("westeurope", "West Europe", kubeconf_eu_west, westeurope_zones)
    ]

    provider = {
        "code": "kubernetes",
        "name": "aks-istio-multi",
        "details": {
            "cloudInfo": {
                "kubernetes": {
                    "kubernetesImageRegistry": "quay.io/yugabyte/yugabyte",
                    "kubernetesProvider": "aks",
                    "kubernetesPullSecretContent": kubernetes_pull_secret_content,
                    "kubernetesPullSecretName": "emea-secret.yaml",
                    "kubernetesImagePullSecretName": "yugabyte-k8s-emea"
                }
            }
        },
        "regions": regions
    }

    # create provider
    print("Creating Provider")
    response = requests.post(url['providers'], headers=headers, json=provider, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")
        create_result=json.loads(response.text)
        taskUUID=create_result['taskUUID']
        resourceUUID=create_result['resourceUUID']
        print(f"Task is running - polling status every {waitTime} seconds.")
        while True:
            response = requests.get(f"{url['tasks']}{taskUUID}", headers=headers, verify=verify_ssl)
            taskStatusJson = json.loads(response.text)
            if taskStatusJson["status"] == "Running":
                print(f"Current task status is: {taskStatusJson['status']} - {taskStatusJson['percent']} Percent")
                time.sleep(waitTime)
            else:
                print(f"Task finished. Result: {taskStatusJson['status']}.")
                break
            
        config.set(iniSection, f"provider_id", resourceUUID)
        with open(iniFile, 'w') as config_file:
            config.write(config_file) 

def create_multi_provider_UK(config):
    
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
    }

    with open('/Users/jnorwood/Documents/emea-secret.yaml', 'r') as secret_file:
        kubernetes_pull_secret_content = secret_file.read()

    with open('uk-south1-kubeconf.conf', 'r') as kubeconf_1_file:
        kubeconf_1 = kubeconf_1_file.read()

    with open('uk-south2-kubeconf.conf', 'r') as kubeconf_2_file:
        kubeconf_2 = kubeconf_2_file.read()
        
    with open('uk-west0-kubeconf.conf', 'r') as kubeconf_3_file:
        kubeconf_3 = kubeconf_3_file.read()

    # Define the zones for each region
    uksouth_zones = [("uksouth-1", "uksouth-1"), ("uksouth-2", "uksouth-2")]
    ukwest_zones = [("0", "0")]

    # Define the regions
    regions = [
        create_region("uksouth", "UK South", kubeconf_1, uksouth_zones),
        create_region("ukwest", "UK West", kubeconf_3, ukwest_zones)
    ]

    provider = {
        "code": "kubernetes",
        "name": "aks-istio-multi",
        "details": {
            "cloudInfo": {
                "kubernetes": {
                    "kubernetesImageRegistry": "quay.io/yugabyte/yugabyte",
                    "kubernetesProvider": "aks",
                    "kubernetesPullSecretContent": kubernetes_pull_secret_content,
                    "kubernetesPullSecretName": "emea-secret.yaml",
                    "kubernetesImagePullSecretName": "yugabyte-k8s-emea"
                }
            }
        },
        "regions": regions
    }

    # create provider
    print("Creating Provider")
    response = requests.post(url['providers'], headers=headers, json=provider, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")
        create_result=json.loads(response.text)
        taskUUID=create_result['taskUUID']
        resourceUUID=create_result['resourceUUID']
        print(f"Task is running - polling status every {waitTime} seconds.")
        while True:
            response = requests.get(f"{url['tasks']}{taskUUID}", headers=headers, verify=verify_ssl)
            taskStatusJson = json.loads(response.text)
            if taskStatusJson["status"] == "Running":
                print(f"Current task status is: {taskStatusJson['status']} - {taskStatusJson['percent']} Percent")
                time.sleep(waitTime)
            else:
                print(f"Task finished. Result: {taskStatusJson['status']}.")
                break
            
        config.set(iniSection, f"provider_id", resourceUUID)
        with open(iniFile, 'w') as config_file:
            config.write(config_file) 

def create_s3_storage(config):
    print("Creating S3 Storage")
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
        }
    
    storage = {
        "type": "STORAGE",
        "name": "S3",
        "configName": "s3Backup",
        "data": {
            "BACKUP_LOCATION": f"s3://{env['s3_bucket']}",
            "IAM_INSTANCE_PROFILE": "true"
        }
    }

    response = requests.post(url['configs'], headers=headers, json=storage, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")
        backup_result=json.loads(response.text)
        resource=backup_result['configUUID']

        config.set(iniSection, f"backup_storage_id", resource)
        with open(iniFile, 'w') as config_file:
            config.write(config_file)
    
def create_universe(config):
    print("Creating Universe")
    
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
        }

    # read provider region
    response = requests.get(url['provider'], headers=headers, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")
        prov_result=json.loads(response.text)
        region_list = [region['uuid'] for region in prov_result['regions']]
        # define universe
        universe = {
            "enableYbc": True,
            "clusters": [
                {
                    "clusterType": "PRIMARY",
                    "userIntent": {
                        "universeName": f"{iniSection.replace('.', '-')}-api-demo", 
                        "providerType": "kubernetes",
                        "provider": env["provider_id"],
                        "regionList": region_list,
                        "numNodes": env["rf"],
                        "replicationFactor": env["rf"],
                        "masterK8SNodeResourceSpec": {
                            "memoryGib": env["master_mem"],
                            "cpuCoreCount": env["master_cores"]
                        },
                        "tserverK8SNodeResourceSpec": {
                            "memoryGib": env["tserver_mem"],
                            "cpuCoreCount": env["tserver_cores"]
                        },
                        #"instanceType": env["instance_type"],
                        "deviceInfo": {
                            "numVolumes": 1,
                            "volumeSize": env["volume_size"],
                            "storageClass": "standard",
                        },
                        "useTimeSync": True,
                        "enableYSQL": True,
                        "enableYEDIS": False,
                        "enableYCQL": True,
                        "enableYSQLAuth": False,
                        "enableNodeToNodeEncrypt": False,
                        "enableClientToNodeEncrypt": False,
                        "ybSoftwareVersion": env["version"],
                    },
                }
            ],
        }
        # create
        response = requests.post(url['cluster'], headers=headers, json=universe, verify=verify_ssl)
        if response.status_code != 200: 
            print("Error occurred during the request.")
            print("Status code:", response.status_code)
            print("Error message:", response.json().get("error"))
        else:
            print("Request was successful.")
            create_result=json.loads(response.text)
            taskUUID=create_result['taskUUID']
            resourceUUID=create_result['resourceUUID']
            print(f"Task is running - polling status every {waitTime} seconds.")
            time.sleep(waitTime)
            while True:
                response = requests.get(f"{url['tasks']}{taskUUID}", headers=headers, verify=verify_ssl)
                taskStatusJson = json.loads(response.text)
                if taskStatusJson["status"] == "Running":
                    print(f"Current task status is: {taskStatusJson['status']} - {taskStatusJson['percent']} Percent")
                    time.sleep(waitTime)
                else:
                    print(f"Task finished. Result: {taskStatusJson['status']}.")
                    break
                
            config.set(iniSection, f"universe_id", resourceUUID)
            with open(iniFile, 'w') as config_file:
                config.write(config_file)

def create_backup_schedule():
    print("Creating Backup Schedule")
    
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
        }
    
    #define backup
    backup = {
        "backupType": "PGSQL_TABLE_TYPE",
        "storageConfigUUID": env['backup_storage_id'],
        "universeUUID": env['universe_id'],
        # all databases
        "keyspaceTableList": [],
        # keep forever
        "timeBeforeDelete": 0,
        "scheduleName": "apitest-12h-full-60m-inc",
        # frequency is milliseconds - so this is 12 hours
        "schedulingFrequency": 43200000,
        # this is the display unit in the UI - so will show 12 hours for the above
        "frequencyTimeUnit": "HOURS",
        # frequency is milliseconds - so this is 1 hour
        "incrementalBackupFrequency": 3600000,
        # this is the display unit in the UI - so will show 60 minutes for the above
        "incrementalBackupFrequencyTimeUnit": "MINUTES"
    }

    response = requests.post(url['backup-schedule'], headers=headers, json=backup, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")    
        backup_result=json.loads(response.text)

def list_universes():

    print("Listing Universes")
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
    }
    response = requests.request("GET", url['universes'], headers=headers, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful, listing universes")    
        list_result=json.loads(response.text)
        for uni in list_result:
            print(f"NAME - {uni['name']}, Nodes - {uni['resources']['numNodes']}, YB - {uni['universeDetails']['clusters'][0]['userIntent']['ybSoftwareVersion']}, YBC - {uni['universeDetails']['ybcSoftwareVersion']}, UUID - {uni['universeUUID']}")
            
def list_tables():
    print("Listing Tables")
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
    }
    response = requests.request("GET", url['tables'], headers=headers, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful, listing tables")    
        list_result=json.loads(response.text)
        for table in list_result:
            print(f"KEYSPACE - {table['keySpace']}, TABLE - {table['tableName']}, TYPE - {table['tableType']}, SIZE - {table['sizeBytes']}, WAL SIZE - {table['walSizeBytes']}")            

def get_users():
    print("Listing Users")
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
    }
    response = requests.request("GET", url['users'], headers=headers, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful, listing users")    
        list_result=json.loads(response.text)
        for user in list_result:
            print(f"uuid - {user['uuid']}, email - {user['email']}, role - {user['role']}")  

def add_users():
    print("Adding 100 Dummy Users")
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
    }
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')  # Timestamp for uniqueness

    for i in range(1, 102):
        user = {
            "email": f"my_example_user_{i}_{timestamp}@norwood.me",
            "password": "Never_g01ng_1n!",
            "role": "ReadOnly"
        }

    # Make the request
        response = requests.request("POST", url['users'], headers=headers, json=user, verify=verify_ssl)

        if response.status_code != 200: 
            print(f"Error occurred during the request for user {i}.")
            print("Status code:", response.status_code)
            print("Error message:", response.json().get("error"))
        else:
            print(f"Request was successful, added user {i}.")

def add_release():
    version = env['release']
    version_helm = '.'.join(version.split('.')[:3])

    # Build the URLs
    url_vm = f"https://releases.yugabyte.com/{version}/yugabyte-{version}-centos-x86_64.tar.gz"
    url_helm = f"https://releases.yugabyte.com/{version}/helm/yugabyte-{version_helm}.tgz"

    print(url_helm)
    print(url_vm)

    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
    }

    release = {
        "url": url_vm
    }
    response = requests.post(url['release']+"/extract_metadata", headers=headers, json=release, verify=verify_ssl)
    print("Checking VM for release")
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        create_result=json.loads(response.text)
        resourceUUID=create_result['resourceUUID']
        print(f"Extract Metadata is running - polling status every {waitTime} seconds.")
        time.sleep(waitTime)
        while True:
            response = requests.get(f"{url['release']}/extract_metadata/{resourceUUID}", headers=headers, verify=verify_ssl)
            taskStatusJson = json.loads(response.text)
            if taskStatusJson["status"] == "Running":
                print(f"Current task status is: {taskStatusJson['status']}.")
                time.sleep(waitTime)
            else:
                print(f"Extract Metadata Completed.")
                break

        print("Adding VM Release")
        release = {
            "version": taskStatusJson["version"],
            "release_tag": "",
            "yb_type": taskStatusJson["yb_type"],
            "artifacts": [
                {
                    "platform": taskStatusJson["platform"],
                    "architecture": taskStatusJson["architecture"],
                    "package_url": url_vm
                }
            ],
            "release_type": taskStatusJson["release_type"],
            "release_date_msecs": taskStatusJson["release_date_msecs"],
        }
        response = requests.post(url['release'], headers=headers, json=release, verify=verify_ssl)
        
        if response.status_code != 200: 
            print("Error occurred during the request.")
            print("Status code:", response.status_code)
            print("Error message:", response.json().get("error"))
        else:
            print("Request was successful.")      
            ReleaseJson = json.loads(response.text)
            
            print("Adding Helm Chart for release")
            response = requests.get(f"{url['release']}/{ReleaseJson["resourceUUID"]}", headers=headers, verify=verify_ssl)
            release_json=json.loads(response.text)
            release_json["artifacts"].append({
                "platform": "KUBERNETES",
                "package_url": url_helm
            })
            response = requests.put(f"{url['release']}/{ReleaseJson["resourceUUID"]}", headers=headers, json=release_json, verify=verify_ssl)
            if response.status_code != 200: 
                print("Error occurred during the request.")
                print("Status code:", response.status_code)
                print("Error message:", response.json().get("error"))
            else:
                print("Request was successful.")      

def list_tasks():
    print("Listing Tasks for 24 hours")
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
    }
    task_count = 0
    failed_task_count = 0

    response = requests.request("GET", url['task-list'], headers=headers, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful, listing tasks")    
        list_result=json.loads(response.text)
        for task in list_result:
            task_count += 1 
            if datetime.strptime(task['createTime'], '%Y-%m-%dT%H:%M:%S%z').date()  > date.today() - timedelta(1):      
                print(json.dumps(task, indent=4))
                print(f"RESULT - {task['status']}, FOR - {task['title']}, ID - {task['id']}, DATETIME - {task['createTime']}")
                if task["status"]=="Failure":
                    failed_task_count += 1
                    subtask_response = requests.request("GET", f"{url['tasks']}{task['id']}/failed", headers=headers, verify=verify_ssl)
                    subtask_result=json.loads(subtask_response.text)
                    for subtask in subtask_result['failedSubTasks']:
                        print(f"SUBTASKTYPE - {subtask['subTaskType']}, SUBTASKSTATE - {subtask['subTaskState']}, SUBTASKGROUPTYPE - {subtask['subTaskGroupType']}, ERROR - {subtask['errorString'][:80]}")
    
    print(f"Total tasks found: {task_count}")
    print(f"Total failed tasks: {failed_task_count}")

def perf_rec():
    print("Listing Perf Advisor Recommendations")
    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
    }
    #define query
    data = {
        "filter": {
            "universeId": env['universe_id']
        },
        "sortBy": "recommendationTimestamp",
        "direction": "ASC",
        "offset": 0,
        "limit":50
    }

    response = requests.request("POST", url['perf-rec'], headers=headers, json=data, verify=verify_ssl)
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful, listing recommendations")    
        list_result=json.loads(response.text)
        if 'entities' in list_result:
            for entity in list_result['entities']:
                entity_json = json.dumps(entity, indent=4)  # Pretty-print for readability
                print(entity_json)
    
def delete_universe(config):
    print("Deleting Universe")
    if env["universe_id"] == 'deleted':
        print('ERROR: Universe already deleted')
    else:
        headers = {
            'Content-Type': "application/json",
            'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
            }

        response = requests.delete(url['universe'], headers=headers, verify=verify_ssl)
        if response.status_code != 200: 
            print("Error occurred during the request.")
            print("Status code:", response.status_code)
            print("Error message:", response.json().get("error"))
        else:
            print("Request was successful.")
            create_result=json.loads(response.text)
            taskUUID=create_result['taskUUID']
            print(f"Task is running - polling status every {waitTime} seconds.")
            while True:
                response = requests.get(f"{url['tasks']}{taskUUID}", headers=headers, verify=verify_ssl)
                taskStatusJson = json.loads(response.text)
                if taskStatusJson["status"] == "Running":
                    print(f"Current task status is: {taskStatusJson['status']} - {taskStatusJson['percent']} Percent")
                    time.sleep(waitTime)
                else:
                    print(f"Task finished. Result: {taskStatusJson['status']}.")
                    break
                
            config.set(iniSection, f"universe_id", "deleted")
            with open(iniFile, 'w') as config_file:
                config.write(config_file)
                
def update_universe_override():
    print("Updating Universe Adding Override")

    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
        }

    response = requests.get(url['universe'] , headers=headers, verify=verify_ssl)
    univ_result=json.loads(response.text)
    universe=univ_result["universeDetails"]
    # care when adding - make sure you do not remove existing - plus yaml formatting
    k8s_override = (universe['clusters'][0]['userIntent']['universeOverrides'])
    k8s_override = {
        "universeOverrides": f"{k8s_override}\n  memoryLimitHardPercentage: 60"
    }  

    response = requests.post(url['k8s-override'], headers=headers, json=k8s_override, verify=verify_ssl)
    
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")
        create_result=json.loads(response.text)
        taskUUID=create_result['taskUUID']
        print(f"Task is running - polling status every {waitTime} seconds.")
        time.sleep(waitTime)
        while True:
            response = requests.get(f"{url['tasks']}{taskUUID}", headers=headers, verify=verify_ssl)
            taskStatusJson = json.loads(response.text)
            if taskStatusJson["status"] == "Running":
                print(f"Current task status is: {taskStatusJson['status']} - {taskStatusJson['percent']} Percent")
                time.sleep(waitTime)
            else:
                print(f"Task finished. Result: {taskStatusJson['status']}.")
                break

def update_universe_node():
    print("Updating Universe Adding 3 Nodes")

    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
        }

    response = requests.get(url['universe'] , headers=headers, verify=verify_ssl)
    univ_result=json.loads(response.text)
    universe=univ_result["universeDetails"]

    universe["clusters"][0]["userIntent"]["numNodes"]=universe["clusters"][0]["userIntent"]["numNodes"]+3
    print(f"Increasing to Nodes: {universe['clusters'][0]['userIntent']['numNodes']}")
    response = requests.put(url['universe']+"/clusters/primary", headers=headers, json=universe, verify=verify_ssl)
    
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")
        create_result=json.loads(response.text)
        taskUUID=create_result['taskUUID']
        print(f"Task is running - polling status every {waitTime} seconds.")
        time.sleep(waitTime)
        while True:
            response = requests.get(f"{url['tasks']}{taskUUID}", headers=headers, verify=verify_ssl)
            taskStatusJson = json.loads(response.text)
            if taskStatusJson["status"] == "Running":
                print(f"Current task status is: {taskStatusJson['status']} - {taskStatusJson['percent']} Percent")
                time.sleep(waitTime)
            else:
                print(f"Task finished. Result: {taskStatusJson['status']}.")
                break

def update_universe_master():
    print("Updating Universe - shrink master")

    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
        }

    response = requests.get(url['universe'] , headers=headers, verify=verify_ssl)
    univ_result=json.loads(response.text)
    universe=univ_result["universeDetails"]
    #del universe["clusters"][0]["userIntent"]["instanceType"]
    universe["clusters"][0]["userIntent"]["masterK8SNodeResourceSpec"]["memoryGib"]= 4
    universe["clusters"][0]["userIntent"]["masterK8SNodeResourceSpec"]["cpuCoreCount"]= 2
    #universe["clusters"][0]["userIntent"]["dedicatedNodes"]= "true" 
    print(f"Setting master to: {universe['clusters'][0]['userIntent']['masterK8SNodeResourceSpec']}")
    print(f"Setting dedicatedNodes to: {universe['clusters'][0]['userIntent']['dedicatedNodes']}")

    response = requests.put(url['universe']+"/clusters/primary", headers=headers, json=universe, verify=verify_ssl)
    
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")
        create_result=json.loads(response.text)
        taskUUID=create_result['taskUUID']
        print(f"Task is running - polling status every {waitTime} seconds.")
        time.sleep(waitTime)
        while True:
            response = requests.get(f"{url['tasks']}{taskUUID}", headers=headers, verify=verify_ssl)
            taskStatusJson = json.loads(response.text)
            if taskStatusJson["status"] == "Running":
                print(f"Current task status is: {taskStatusJson['status']} - {taskStatusJson['percent']} Percent")
                time.sleep(waitTime)
            else:
                print(f"Task finished. Result: {taskStatusJson['status']}.")
                break

def update_universe_dedicated():
    print("Updating Universe - set dedicated nodes")

    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
        }

    response = requests.get(url['universe'] , headers=headers, verify=verify_ssl)
    univ_result=json.loads(response.text)
    universe=univ_result["universeDetails"]
    universe["clusters"][0]["userIntent"]["dedicatedNodes"]= "true" 
    print(f"Setting dedicatedNodes to: {universe['clusters'][0]['userIntent']['dedicatedNodes']}")

    response = requests.put(url['universe']+"/clusters/primary", headers=headers, json=universe, verify=verify_ssl)
    
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")
        create_result=json.loads(response.text)
        taskUUID=create_result['taskUUID']
        print(f"Task is running - polling status every {waitTime} seconds.")
        time.sleep(waitTime)
        while True:
            response = requests.get(f"{url['tasks']}{taskUUID}", headers=headers, verify=verify_ssl)
            taskStatusJson = json.loads(response.text)
            if taskStatusJson["status"] == "Running":
                print(f"Current task status is: {taskStatusJson['status']} - {taskStatusJson['percent']} Percent")
                time.sleep(waitTime)
            else:
                print(f"Task finished. Result: {taskStatusJson['status']}.")
                break

def update_universe_gflag():
    print("Updating Universe Setting Adding GFlag yb_enable_read_committed_isolation")

    headers = {
        'Content-Type': "application/json",
        'X-AUTH-YW-API-TOKEN': f"{env['api_token']}"
        }

    response = requests.get(url['universe'] , headers=headers, verify=verify_ssl)
    univ_result=json.loads(response.text)
    universe=univ_result["universeDetails"]
    universe['clusters'][0]['userIntent']['specificGFlags']['perProcessFlags']['value']['TSERVER']['yb_enable_read_committed_isolation'] = "true"  
    print(f"Adding Gflag")
    response = requests.post(url['universe']+"/upgrade/gflags", headers=headers, json=universe, verify=verify_ssl)
    
    if response.status_code != 200: 
        print("Error occurred during the request.")
        print("Status code:", response.status_code)
        print("Error message:", response.json().get("error"))
    else:
        print("Request was successful.")
        create_result=json.loads(response.text)
        taskUUID=create_result['taskUUID']
        print(f"Task is running - polling status every {waitTime} seconds.")
        time.sleep(waitTime)
        while True:
            response = requests.get(f"{url['tasks']}{taskUUID}", headers=headers, verify=verify_ssl)
            taskStatusJson = json.loads(response.text)
            if taskStatusJson["status"] == "Running":
                print(f"Current task status is: {taskStatusJson['status']} - {taskStatusJson['percent']} Percent")
                time.sleep(waitTime)
            else:
                print(f"Task finished. Result: {taskStatusJson['status']}.")
                break

if __name__ == "__main__":
    sections_list=read_ini_sections()
    iniSection = sections_list[0]
    while True and not auto_exit:
        if len(sys.argv) > 1:
            user_input = sys.argv[1]
            auto_exit = True
        else:
            print_menu()
            user_input = input("Select an option (1-18,s,x), x to exit:")

        if user_input.lower() == 'x':
            print("Exiting the program.")
            break  # Break out of the loop if the user enters 'x'

        try:
            if user_input.lower() == 's':
                iniSection = select_ini_section()
            else:
                option = int(user_input)
                if 1 <= option <= 18:
                    api_config = read_config(iniFile,iniSection)
                    set_urls()
                    if option == 1:
                        register_system(api_config)
                    elif option == 2:
                        create_multi_provider_UK(api_config)
                    elif option == 3:
                        create_s3_storage(api_config)
                    elif option == 4:
                        create_universe(api_config)
                    elif option == 5:
                        create_backup_schedule()        
                    elif option == 6:
                        list_universes()      
                    elif option == 7:                                                    
                        list_tasks()       
                    elif option == 8:
                        list_tables()                                              
                    elif option == 9:
                        delete_universe(api_config)
                    elif option == 10:
                        update_universe_override()                                            
                    elif option == 11:
                        update_universe_gflag()            
                    elif option == 12:
                        update_universe_node()            
                    elif option == 13:
                        perf_rec()      
                    elif option == 14:
                        get_users()  
                    elif option == 15:
                        add_users()  
                    elif option == 16:
                        update_universe_dedicated()
                    elif option == 17:
                        update_universe_master()
                    elif option == 18:
                        add_release()                        
                    else:
                        print("Invalid option. Select an option (1-18,s,x), x to exit:")
        except ValueError:
            print("Invalid input. Select an option (1-18,s,x), x to exit:")

