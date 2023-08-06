import subprocess

def get_pid_by_command(command):
    try:
        result = subprocess.check_output(['pgrep', '-f', command])
        pid_list = result.decode('utf-8').strip().split('\n')
        pid_list = [int(pid) for pid in pid_list]
        pid_list.sort(reverse=True)  # Sort the PID list in descending order
        return pid_list[1]
    except subprocess.CalledProcessError:
        return None

pid = get_pid_by_command('python3')
subprocess.run(["kill", "-9", str(pid)])