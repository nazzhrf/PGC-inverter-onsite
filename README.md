# gateway-ui-onsite-growth-chamber

Documentation [here](https://docs.google.com/document/d/14_6l-3nRShH518GohGLufQKyqBomQMMn8HKurVXmP8Q/edit?usp=sharing)

Place this project on this directory:

```
/home/pi
```

Adjust these variable on main.py to setup device:

```
self.deviceId = ""
self.deviceKey = ""
self.portUART = ""
self.isThreeCameras = True/False
self.isLandscape = True/False
```

Adjust camera device on main.py using value from get_camera.py:

```
self.topCameraDevice = ""
self.topRightCameraDevice = ""
self.bottomCameraDevice = ""
self.bottomRightCameraDevice = ""
self.userCameraDevice = ""
```

Run run-scheduled.py to perform auto-restart program hourly functionality:

```
/usr/bin/python3 home/pi/run-scheduled.py
```
