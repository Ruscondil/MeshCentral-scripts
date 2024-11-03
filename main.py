import subprocess
import json
import paramiko
import time
import yaml


def read_secrets(filename):
    try:
        with open(filename, 'r') as file:
            secrets = yaml.safe_load(file)
        return secrets
    except FileNotFoundError:
        print(f"Plik {filename} nie został znaleziony.")
        return None
    except yaml.YAMLError as e:
        print(f"Błąd podczas odczytu pliku YAML {filename}: {e}")
        return None

def get_devices():
    try:
        # Uruchomienie komendy node
        result = subprocess.run(['node', 'meshctrl.js', 'listdevices', '--url', url, '--loginuser', login_user, '--loginpass', login_pass, '--json'], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True, 
                    check=True)
        
        # Odczytanie wyniku
        output = result.stdout
        
        # Parsowanie wyniku jako JSON
        devices = json.loads(output)
        
        return devices
    except subprocess.CalledProcessError as e:
        print("Wystąpił błąd przy uruchamianiu komendy:", e.stderr)
        return None
    except json.JSONDecodeError as e:
        print("Błąd dekodowania JSON:", e)
        return None

def get_selected_devices_names(filename):
    try:
        with open(filename, 'r') as file:
            selected_devices = [line.strip() for line in file.readlines()]
        return selected_devices
    except FileNotFoundError:
        print(f"Plik {filename} nie został znaleziony.")
        return None
    except Exception as e:
        print(f"Wystąpił błąd podczas odczytu pliku {filename}: {e}")
        return None
    
def power_on_selected_devices(devices):
    try:
        device_ids = ','.join([device['_id'] for device in devices])
        result = subprocess.run([
            'node', 'meshctrl.js', 'devicepower', 
            '--id', device_ids, 
            '--url', url, 
            '--loginuser', login_user, 
            '--loginpass', login_pass, 
            '--amton'
        ], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True, 
        check=True)
        print("Urządzenia zostały włączone")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Wystąpił błąd przy uruchamianiu komendy:", e.stderr)
        return None
    
def connectPolluks():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(polluks_ip, username=polluks_login, password=polluks_password)
        print("Connected to Polluks")
        return ssh
    except Exception as e:
        print(f"Error connecting to Polluks: {e}")
        return None

def connect_and_click_button(polluks, device_name):
    
    if polluks is None:
        print(f"Cannot connect to device {device_name}: Polluks connection is None")
        return
       
    device_ssh = paramiko.SSHClient()
    device_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        transport = polluks.get_transport()
        dest_addr = (device_name, 22)
        local_addr = ('127.0.0.1', 22)
        channel = transport.open_channel("direct-tcpip", dest_addr, local_addr)

        device_ssh.connect(device_name, username=polluks_login, password=polluks_password, sock=channel)
        print(f"Connected to device {device_name}") 

        shell = device_ssh.invoke_shell()
        time.sleep(1)
        shell.send('L\n')
        time.sleep(1)

        #output = shell.recv(65535).decode('utf-8')
        #print(output)
        
    except Exception as e:
        print(f"Error connecting to {device_name}: {e}")
    finally:
        device_ssh.close()


secrets = read_secrets('secrets.yaml')
if not secrets:
    exit()

login_user = secrets.get('login_user', None)
login_pass = secrets.get('login_pass', None)
url = secrets.get('url', None)
polluks_ip = secrets.get('polluks_ip', None)
polluks_login = secrets.get('polluks_login', None)
polluks_password = secrets.get('polluks_password', None)

devices = get_devices()
selected_devices_names = get_selected_devices_names('devices.txt')
if devices is not None and selected_devices_names is not None:
    selected_devices = [device for device in devices if device["name"] in selected_devices_names]
    #print(selected_devices)
    power_on_result = power_on_selected_devices(selected_devices)

    #print("Lista urządzeń:", devices)
    
    ssh = connectPolluks()
    time.sleep(30)
    for device in selected_devices:
        connect_and_click_button(ssh, device["name"])
    ssh.close()


   