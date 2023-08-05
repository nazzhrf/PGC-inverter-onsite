import subprocess
import time

def run_main():
    #return subprocess.Popen(['xvfb-run', '-a', '/usr/bin/python3', '/home/pi/main.py']) # run headless on terminal using xvfb
    return subprocess.Popen(['/usr/bin/python3', '/home/pi/main.py']) #run on GUI

def restart_main():
    main_process = None
    while True:
        if main_process is not None:
            main_process.terminate()
            main_process.wait()
        main_process = run_main()
        time.sleep(1800)  # Restart every 1/2 hour (1800 seconds)

if __name__ == "__main__":
    restart_main()