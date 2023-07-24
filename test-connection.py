import subprocess

def get_default_interface():
    try:
        output = subprocess.check_output(['ip', 'route', 'show', 'default'], text=True)
        default_route = output.split()
        print("Success get network interface")
        return default_route[4] if len(default_route) >= 5 else None
    except subprocess.CalledProcessError:
        print("Failed get network interface")
        return None

def toggle_network_connection():
        network_interface = get_default_interface()
        def is_network_connected():
            try:
                subprocess.check_call(['ping', '-c', '1', '8.8.8.8'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True
                print("There is network connection")
            except subprocess.CalledProcessError:
                print("No network connection")
                return False
        def connect_network():
            subprocess.run(['sudo', 'ip', 'link', 'set', 'dev', network_interface, 'up'])
            print("Success connect to " + network_interface + " network interface")
        def disconnect_network():
            subprocess.run(['sudo', 'ip', 'link', 'set', 'dev', network_interface, 'down'])
            print("Success disconnect from " + network_interface + " network interface")
        if network_interface and is_network_connected():
            disconnect_network()
            connect_network()

toggle_network_connection()

"""
To test on terminal:

ip route show default, ex output: default via 169.254.1.1 dev eth0
sudo ifdown {{network_interface}}, ex: sudo ifdown eth0
sudo ifup {{network_interface}}
"""