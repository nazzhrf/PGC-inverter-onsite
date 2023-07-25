import subprocess

df2 = subprocess.check_output("v4l2-ctl --list-devices", shell=True)
print(df2.decode('utf8').split('\n'))
