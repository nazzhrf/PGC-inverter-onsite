import subprocess
import time

def run_main():
    #return subprocess.Popen(['xvfb-run', '-a', '/usr/bin/python3', '/home/pi/main.py']) # run headless on terminal using xvfb
    return subprocess.Popen(['/usr/bin/python3', '/home/pi/main.py']) #run on GUI

def restart_main():
    main_process = None
    prev_hour = (time.localtime()).tm_hour  # Initialize the previous hour
    #prev_minute = (time.localtime()).tm_min  # for testing

    while True:
        current_time = time.localtime()
        current_hour = current_time.tm_hour
        current_minute = current_time.tm_min
        
        # restart main program every hour
        if (current_hour - prev_hour) >= 1:
        #if (current_minute - prev_minute) >= 1: # for testing
            if main_process is not None:
                main_process.terminate()
                main_process.wait()  # Wait for the process to terminate gracefully
                print("Main program terminated")
            main_process = run_main()
            print("Main program restarted")
            prev_hour = current_hour
            #prev_minute = current_minute # for testing

        # reboot device at 00:00
        if (current_hour == 0 or current_hour == 24) and current_minute == 0:
            subprocess.run(['sudo', 'reboot'])

        time.sleep(30)  # Sleep for 30 seconds before checking again

if __name__ == "__main__":
    restart_main()