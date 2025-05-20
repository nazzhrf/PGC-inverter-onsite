import subprocess
import time

def run_main():
    #return subprocess.Popen(['xvfb-run', '-a', '/usr/bin/python3', '/home/pi/main.py']) # run headless on terminal using xvfb
    return subprocess.Popen(['/usr/bin/python3', '/home/pi/main.py']) #run on GUI

def get_pid_by_command(command):
    try:
        result = subprocess.check_output(['pgrep', '-f', command])
        pid_list = result.decode('utf-8').strip().split('\n')
        pid_list = [int(pid) for pid in pid_list]
        pid_list.sort(reverse=True)  # Sort the PID list in descending order
        return pid_list[0]
    except subprocess.CalledProcessError:
        return None

def restart_main():
    main_process = run_main()
    prev_minute = (time.localtime()).tm_min

    while True:
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        current_minute = current_time.tm_min
        
        # restart main program every hour
        if (current_minute - prev_minute) >= 1: # for testing
            if main_process is not None:
                pid = get_pid_by_command('python3')
                subprocess.run(["kill", "-9", str(pid)])
                print("Main program terminated")
            main_process = run_main()
            print("Main program restarted")
            prev_minute = current_minute # for testing

        # reboot device at 00:00
        if (current_hour == 0 or current_hour == 24) and current_minute == 0:
            subprocess.run(['sudo', 'reboot'])

        time.sleep(30)  # Sleep for 30 seconds before checking again

if __name__ == "__main__":
    restart_main()