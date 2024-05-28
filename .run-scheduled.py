import subprocess
import time
import os

# execute main program
def run_main():
    prefixPath = "/home/pi"
    try:
        if not os.path.isfile(os.path.join(prefixPath, ".main.py")):
            raise FileNotFoundError
    except FileNotFoundError:
        prefixPath = "/home/sgc/pi"
    return subprocess.Popen(['/usr/bin/python3', os.path.join(prefixPath, ".main.py")])

# get latest python3 execution task
def get_pid_by_command(command):
    try:
        result = subprocess.check_output(['pgrep', '-f', command])
        pid_list = result.decode('utf-8').strip().split('\n')
        pid_list = [int(pid) for pid in pid_list]
        pid_list.sort(reverse=True)  # Sort the PID list in descending order
        return pid_list[0]
    except subprocess.CalledProcessError:
        return None

# manage run main program, restart program, and reboot schedule
def scheduler_main():
    main_process = run_main()
    prev_day = (time.localtime()).tm_mday  # Initialize the previous day
    while True:
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        current_minute = current_time.tm_min
        current_day = current_time.tm_mday
        # restart main program every day
        if (current_day != prev_day):
            if main_process is not None:
                pid = get_pid_by_command('python3')
                subprocess.run(["kill", "-9", str(pid)])
                print("Main program terminated")
            time.sleep(0.5)
            main_process = run_main()
            print("Main program restarted")
            prev_day = current_day
        # reboot device every month
        if current_day == 1 and current_hour == 0 and current_minute == 1:
            subprocess.run(['sudo', 'reboot'])
        time.sleep(30)  # Sleep for 30 seconds before checking again

if __name__ == "__main__":
    scheduler_main()