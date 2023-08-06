import subprocess
import time

def run_main():
    return subprocess.Popen(['/usr/bin/python3', '/home/pi/main.py']) #run on GUI

def restart_main():
    main_process = run_main()
    prev_hour = (time.localtime()).tm_hour  # Initialize the previous hour
    
    while True:
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        current_minute = current_time.tm_min
        
        # restart main program every hour
        if (current_hour - prev_hour) >= 1:
            if main_process is not None:
                main_process.terminate()
                main_process.wait()  # Wait for the process to terminate gracefully
                print("Main program terminated")
            time.sleep(1)
            main_process = run_main()
            print("Main program restarted")
            prev_hour = current_hour
        
        # reboot device at 00:00
        if (current_hour == 0 or current_hour == 24) and current_minute == 0:
            print("Device will reboot on 30 seconds..")
            time.sleep(30) # sleep 30 seconds before reboot device
            subprocess.run(['sudo', 'reboot'])

        time.sleep(30)  # Sleep for 30 seconds before checking again

if __name__ == "__main__":
    restart_main()