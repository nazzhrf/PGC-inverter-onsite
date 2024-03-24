# gateway-ui-onsite-growth-chamber

Documentation [here](https://docs.google.com/document/d/14_6l-3nRShH518GohGLufQKyqBomQMMn8HKurVXmP8Q/edit?usp=sharing)

- Place this project on this directory:

```
/home/pi
```

- Create .params-local.json file and adjust these variable to setup device:

```
deviceId = ""
deviceKey = ""
portUART = ""
isThreeCameras = true/false
isLandscape = true/false
```

Also adjust camera device on .params-local.json using value from .get_camera.py:

```
topCameraDevice = ""
topRightCameraDevice = ""
bottomCameraDevice = ""
bottomRightCameraDevice = ""
userCameraDevice = ""
```

- Use sample_image to create default image file on /.Image directory

```
top_chamber{deviceId}.png
.
.
```

- Add /.Data directory folder

- Adjust /.Actual/Last_SP_Data.csv if you want directly change set point

```
{SPTempDay}
{SPHumDay}
{SPLightDay}
{SPTempNight}
{SPHumNight}
{SPLightNight}
```

- Run .run-scheduled.py to perform auto-restart program hourly functionality:

```
/usr/bin/python3 home/pi/run-scheduled.py
```
