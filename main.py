"""
Gateway Subsystem
Plant Growth Chamber
Thesis by Muhammad Arbi Minanda (23220344)
"""

# libraries
from PyQt5 import QtCore, QtSerialPort, QtGui, uic ,QtWidgets 
from PyQt5.QtWidgets import QApplication, QStackedWidget, QWidget, QMainWindow, QLabel, QPushButton, QSpinBox, QSlider, QCheckBox, QLineEdit, QFileDialog, QFrame, QTableWidget, QGridLayout
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
import sseclient, sys, time, json, requests, cv2, os, subprocess
from severity_handler import init_severity_page


# comment this if make script error
#os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")

# Untuk real hardware
# import firebase
# import arduino
# import client
# import LCD

# Untuk testing dummy
# from dummy import firebase, arduino, client, LCD


# functions for get params
def load_params(prefix_path):
    params_local_path = prefix_path + "params-local.json"
    with open(params_local_path, 'r') as file:
        params = json.load(file)
    return params

# define devices, prefix path, and get params local from .params-local.json
prefixPath = ""
device = "Raspberry"
try:
    params_local = load_params(prefixPath)
except (FileNotFoundError, json.JSONDecodeError):
    prefixPath = "/home/sgc/pi/"
    device = "Beelink"
    params_local = load_params(prefixPath)

# set device variable from json params local
deviceId = params_local["deviceId"]
deviceKey = params_local["deviceKey"]
portUART = params_local["portUART"]
isThreeCameras = params_local["isThreeCameras"]
isLandscape = params_local["isLandscape"]
topCameraDevice = params_local["topCameraDevice"]
bottomCameraDevice = params_local["bottomCameraDevice"]
userCameraDevice = params_local["userCameraDevice"]
topRightCameraDevice = params_local["topRightCameraDevice"]
bottomRightCameraDevice = params_local["bottomRightCameraDevice"]

# conditional library import and setup based on device type
if device == "Beelink":
    import numpy as np
    sys.path.insert(0, r"./.local/lib/python3.10/site-packages")
    black = np.load(prefixPath + "outfile.npy")

class UI(QMainWindow):


    def __init__(self):
        # variable for server related
        self.baseUrl = 'https://api.smartfarm.id'
        self.urlGetLiveSetpoint = self.baseUrl + '/condition/getsetpoint/' + deviceId + '?device_key=' + deviceKey
        self.urlPostLiveCond = self.baseUrl + '/condition/data/' + deviceId
        self.urlPostLiveCallback = self.baseUrl + '/condition/events-callback/' + deviceId
        self.urlPostCondToDB = self.baseUrl + '/condition/create'
        self.urlPostPhoto = self.baseUrl + '/file/kamera'
        self.requestHeader = {
            'Content-Type': 'application/json',
            'device_key': deviceKey,
        }

        # variable for managing callback
        self.receiveSetPoint = 0
        self.receiveCameraCommand = 0

        # initiate GUI
        super(UI, self).__init__()
        if (device == "Beelink") :
            uic.loadUi(prefixPath + "UI/UIFINAL.ui", self)
        else :
            if (isLandscape == True) :
                uic.loadUi(prefixPath + "UI/UIFINAL.ui", self)
            else :
                uic.loadUi(prefixPath + "UI/UIFINAL.ui", self)

        # hardware parameter
        self.mode = "auto"
        self.manLight = 0
        self.manHeater, self.manComp, self.manHum = False, False, False
        self.waterStatus = "1"

        # set actual condition parameter
        self.actTemp, self.actHum, self.actLight = "", "", ""

        # try get last actual data
        self.lastActualDataFilename = prefixPath + "Actual/Last_Actual_Data.csv"
        if (os.path.exists(self.lastActualDataFilename) == True):
            try:
                with open(self.lastActualDataFilename, "r") as file:
                    lines = file.readlines()
                self.actTemp = lines[0].strip()
                self.actHum = lines[1].strip()
                self.actLight = lines[2].strip()
                self.mode = lines[3].strip()
                self.manHeater = lines[4].strip() == "True"
                self.manComp = lines[5].strip() == "True"
                self.manHum = lines[6].strip() == "True"
                self.manLight = float(lines[7].strip())
                print("Success get last actual condition data")
            except:
                print("Failed get last actual condition data")

        # set point parameter
        self.SPTemp, self.SPTempDay, self.prevSPTempDay = "27", "27", "27"
        self.SPHum, self.SPHumDay, self.prevSPHumDay = "70", "70", "70"
        self.SPLight, self.SPLightDay, self.prevSPLightDay = "4000", "4000", "4000"
        self.SPTempNight, self.prevSPTempNight = "23", "23"
        self.SPHumNight, self.prevSPHumNight = "90", "90"
        self.SPLightNight, self.prevSPLightNight = "0", "0"

        # try get last set point data
        self.lastSPDataFilename = prefixPath + "Actual/Last_SP_Data.csv"
        if (os.path.exists(self.lastSPDataFilename) == True):
            try:
                with open(self.lastSPDataFilename, "r") as file:
                    lines = file.readlines()
                self.SPTempDay = lines[0].strip()
                self.prevSPTempDay = self.SPTempDay
                self.SPHumDay = lines[1].strip()
                self.prevSPHumDay = self.SPHumDay
                self.SPLightDay = lines[2].strip()
                self.prevSPLightDay = self.SPLightDay
                self.SPTempNight = lines[3].strip()
                self.prevSPTempNight = self.SPTempNight
                self.SPHumNight = lines[4].strip()
                self.prevSPHumNight = self.SPHumNight
                self.SPLightNight = lines[5].strip()
                self.prevSPLightNight = self.SPLightNight
                print("Success get last set point data")
            except:
                print("Failed get last set point data")

        # day or night parameter
        self.startDay, tempStartDay = "6", "6"
        self.startNight, tempStartNight = "8", "8"

        # try get last day night start time data
        self.lastDayNightDataFilename = prefixPath + "Actual/Last_DayNight_Data.csv"
        if (os.path.exists(self.lastDayNightDataFilename) == True):
            try:
                with open(self.lastDayNightDataFilename, "r") as file:
                    lines = file.readlines()
                self.startDay = lines[0].strip()
                self.tempStartDay = self.startDay
                self.startNight = lines[1].strip()
                self.tempStartNight = self.startNight
                print("Success get last day night start time data")
            except:
                print("Failed get last day night start time data")

        # set point limiter
        self.upLimitSPTemp = 100
        self.bottomLimitSPTemp = 0
        self.upLimitSPHum = 90
        self.bottomLimitSPHum = 30
        self.upLimitSPLight = 30000
        self.bottomLimitSPLight = 0
        
        # variable for any onsite user touch the screen
        self.lastMinuteTouch = (time.localtime()).tm_min

        # variable for photo
        self.pathTopPhoto = prefixPath + 'Image/top_chamber' + deviceId + '.png'
        self.pathBottomPhoto = prefixPath + 'Image/bottom_chamber' + deviceId + '.png'
        self.pathUserPhoto = prefixPath + 'Image/user_chamber' + deviceId + '.png'
        self.pathTopRightPhoto = prefixPath + 'Image/topRight_chamber' + deviceId + '.png'
        self.pathBottomRightPhoto = prefixPath + 'Image/bottomRight_chamber' + deviceId + '.png'
        self.currentPhoto = self.pathTopPhoto
        self.intervalSendUserPhoto = 1
        
        # SSE related variables
        self.sseManager, self.sseRequest = None, None

        # pages
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.dashboardPage = self.findChild(QWidget, "dashboardPage")
        self.tempPage = self.findChild(QWidget, "tempPage")
        self.humPage = self.findChild(QWidget, "humPage")
        self.lightPage = self.findChild(QWidget, "lightPage")
        self.dayNightPage = self.findChild(QWidget, "dayNightPage")
        self.severityPage = self.findChild(QWidget, "severityPage")
        
        # parent element
        self.fullscreenButton = self.findChild(QPushButton, "fullscreenButton")
        self.shutdownButton = self.findChild(QPushButton, "shutdown")
        self.toDayNightPageButton = self.findChild(QPushButton, "dayNightSetting")
        self.actualTime = self.findChild(QLabel, "actualTime")
        self.actualDay = self.findChild(QLabel, "actualDay")
        self.actualDate = self.findChild(QLabel, "actualDate")
        self.actualMode = self.findChild(QLabel, "actualMode")
        
        # dashboard page element
        self.toTempPageButton = self.findChild(QPushButton, "toTempPage")
        self.toHumPageButton = self.findChild(QPushButton, "toHumPage")
        self.toLightPageButton = self.findChild(QPushButton, "toLightPage")
        self.actualTemp = self.findChild(QLabel, "actualTempVal")
        self.actualHum = self.findChild(QLabel, "actualHumVal")
        self.actualLight = self.findChild(QLabel, "actualLightVal")
        self.cameraHome = self.findChild(QLabel, "cameraHome")
        self.actualPosition = self.findChild(QLabel, "actPosition")
        self.takePhoto = self.findChild(QPushButton, "takePhoto")
        self.camFrame = self.findChild(QFrame, "camFrame")
        self.dashboardFrame = self.findChild(QFrame, "dashboardFrame")
        self.toSeverityPage = self.findChild(QPushButton, "toSeverityPage")
        if self.toSeverityPage is None:
            print("toSeverityPage not found in UI!")
        else:
            self.toSeverityPage.clicked.connect(lambda: self.buttonToPage_clicked(self.severityPage))
        

        # temp page element
        self.subActualTemp = self.findChild(QLabel, "subActualTempVal")
        self.manualTempButton = self.findChild(QCheckBox, "manualTempCheckBox")
        self.heaterButton = self.findChild(QCheckBox, "heaterOnOff")
        self.coolerButton = self.findChild(QCheckBox, "coolerOnOff")
        self.setpointTempDay = self.findChild(QLineEdit, "tempSetPointDay")
        self.setpointTempNight = self.findChild(QLineEdit, "tempSetPointNight")
        self.dayTempButton = self.findChild(QCheckBox, "tempDayOnOff")
        self.nightTempButton = self.findChild(QCheckBox, "tempNightOnOff")
        self.tempButton = self.findChild(QPushButton, "setTemp")
        self.oneButtonTemp = self.findChild(QPushButton, "buttonOneTemp")
        self.twoButtonTemp = self.findChild(QPushButton, "buttonTwoTemp")
        self.threeButtonTemp = self.findChild(QPushButton, "buttonThreeTemp")
        self.fourButtonTemp = self.findChild(QPushButton, "buttonFourTemp")
        self.fiveButtonTemp = self.findChild(QPushButton, "buttonFiveTemp")
        self.sixButtonTemp = self.findChild(QPushButton, "buttonSixTemp")
        self.sevenButtonTemp = self.findChild(QPushButton, "buttonSevenTemp")
        self.eightButtonTemp = self.findChild(QPushButton, "buttonEightTemp")
        self.nineButtonTemp = self.findChild(QPushButton, "buttonNineTemp")
        self.zeroButtonTemp = self.findChild(QPushButton, "buttonZeroTemp")
        self.delButtonTemp = self.findChild(QPushButton, "buttonDelTemp")
        self.commaButtonTemp = self.findChild(QPushButton, "buttonCommaTemp")
        self.backFromTemp = self.findChild(QPushButton, "goDashboardFromTemp")
        self.tempFrame = self.findChild(QFrame, "tempFrame")
        
        # hum page element
        self.Humframe = self.findChild(QWidget, "Humframe")
        self.subActualHum = self.findChild(QLabel, "subActualHumVal")
        self.manualHumButton = self.findChild(QCheckBox, "manualHumCheckBox")
        self.humidifierButton = self.findChild(QCheckBox, "humOnOff")
        self.setpointHumDay = self.findChild(QLineEdit, "humSetPointDay")
        self.setpointHumNight = self.findChild(QLineEdit, "humSetPointNight")
        self.dayHumButton = self.findChild(QCheckBox, "humDayOnOff")
        self.nightHumButton = self.findChild(QCheckBox, "humNightOnOff")
        self.humButton = self.findChild(QPushButton, "setHum")
        self.oneButtonHum = self.findChild(QPushButton, "buttonOneHum")
        self.twoButtonHum = self.findChild(QPushButton, "buttonTwoHum")
        self.threeButtonHum = self.findChild(QPushButton, "buttonThreeHum")
        self.fourButtonHum = self.findChild(QPushButton, "buttonFourHum")
        self.fiveButtonHum = self.findChild(QPushButton, "buttonFiveHum")
        self.sixButtonHum = self.findChild(QPushButton, "buttonSixHum")
        self.sevenButtonHum = self.findChild(QPushButton, "buttonSevenHum")
        self.eightButtonHum = self.findChild(QPushButton, "buttonEightHum")
        self.nineButtonHum = self.findChild(QPushButton, "buttonNineHum")
        self.zeroButtonHum = self.findChild(QPushButton, "buttonZeroHum")
        self.delButtonHum = self.findChild(QPushButton, "buttonDelHum")
        self.commaButtonHum = self.findChild(QPushButton, "buttonCommaHum")
        self.backFromHum = self.findChild(QPushButton, "goDashboardFromHum")

        # light page element
        self.subActualLight = self.findChild(QLabel, "subActualLightVal")
        self.manualLightButton = self.findChild(QCheckBox, "manualLightCheckBox")
        self.lightSlider = self.findChild(QSlider, "lampSlider")
        self.setpointLightDay = self.findChild(QLineEdit, "lightSetPointDay")
        self.setpointLightNight = self.findChild(QLineEdit, "lightSetPointNight")
        self.dayLightButton = self.findChild(QCheckBox, "lightDayOnOff")
        self.nightLightButton = self.findChild(QCheckBox, "lightNightOnOff")
        self.lightButton = self.findChild(QPushButton, "setLight")
        self.oneButtonLight = self.findChild(QPushButton, "buttonOneLight")
        self.twoButtonLight = self.findChild(QPushButton, "buttonTwoLight")
        self.threeButtonLight = self.findChild(QPushButton, "buttonThreeLight")
        self.fourButtonLight = self.findChild(QPushButton, "buttonFourLight")
        self.fiveButtonLight = self.findChild(QPushButton, "buttonFiveLight")
        self.sixButtonLight = self.findChild(QPushButton, "buttonSixLight")
        self.sevenButtonLight = self.findChild(QPushButton, "buttonSevenLight")
        self.eightButtonLight = self.findChild(QPushButton, "buttonEightLight")
        self.nineButtonLight = self.findChild(QPushButton, "buttonNineLight")
        self.zeroButtonLight = self.findChild(QPushButton, "buttonZeroLight")
        self.delButtonLight = self.findChild(QPushButton, "buttonDelLight")
        self.commaButtonLight = self.findChild(QPushButton, "buttonCommaLight")
        self.backFromLight = self.findChild(QPushButton, "goDashboardFromLight")
        self.lightFrame = self.findChild(QFrame, "lightFrame")
        

        # day night start time setting page
        self.startTimeDay = self.findChild(QLineEdit, "startTimeDay")
        self.startTimeNight = self.findChild(QLineEdit, "startTimeNight")
        self.dayButton = self.findChild(QCheckBox, "startDayOnOff")
        self.nightButton = self.findChild(QCheckBox, "startNightOnOff")
        self.setStartTimeButton = self.findChild(QPushButton, "setStartTime")
        self.oneButtonStartTime = self.findChild(QPushButton, "buttonOneStartTime")
        self.twoButtonStartTime = self.findChild(QPushButton, "buttonTwoStartTime")
        self.threeButtonStartTime = self.findChild(QPushButton, "buttonThreeStartTime")
        self.fourButtonStartTime = self.findChild(QPushButton, "buttonFourStartTime")
        self.fiveButtonStartTime = self.findChild(QPushButton, "buttonFiveStartTime")
        self.sixButtonStartTime = self.findChild(QPushButton, "buttonSixStartTime")
        self.sevenButtonStartTime = self.findChild(QPushButton, "buttonSevenStartTime")
        self.eightButtonStartTime = self.findChild(QPushButton, "buttonEightStartTime")
        self.nineButtonStartTime = self.findChild(QPushButton, "buttonNineStartTime")
        self.zeroButtonStartTime = self.findChild(QPushButton, "buttonZeroStartTime")
        self.delButtonStartTime = self.findChild(QPushButton, "buttonDelStartTime")
        self.backFromDayNight = self.findChild(QPushButton, "goDashboardFromDayNight")
        self.dayNightFrame = self.findChild(QFrame, "dayNightFrame")

        #severity page element
        self.severityTable = self.findChild(QTableWidget, "severityTable")
        self.trayCamera = self.findChild(QFrame, "trayCamera")
        self.yearMonthLine = self.findChild(QtWidgets.QLineEdit, "yearMonthLine")
        self.yearMonthLine_2 = self.findChild(QtWidgets.QLineEdit, "yearMonthLine_2")
        self.yearMonthLine_3 = self.findChild(QtWidgets.QLineEdit, "yearMonthLine_3")
        self.submitDateTime = self.findChild(QtWidgets.QPushButton, "submitDateTime")
        self.submitDateTime_2 = self.findChild(QtWidgets.QPushButton, "submitDateTime_2")
        self.dateAndTimeList = self.findChild(QtWidgets.QListWidget, "dateAndTimeList")
        self.backFromSeverity = self.findChild(QPushButton, "goDashboardFromSeverity")

        # initial display
        self.showMaximized()
        self.stackedWidget.setCurrentWidget(self.dashboardPage)
        self.showFullScreen()
        self.fullscreenButton.setText("↙")
        self.actualPosition.setText("Top")
        if (self.mode == "auto"):
            self.heaterButton.setEnabled(False)
            self.coolerButton.setEnabled(False)
            self.humidifierButton.setEnabled(False)
            self.lightSlider.setEnabled(False)
            self.tempButton.setEnabled(True)
            self.humButton.setEnabled(True)
            self.lightButton.setEnabled(True)
            self.manualTempButton.setChecked(False)
            self.manualHumButton.setChecked(False)
            self.manualLightButton.setChecked(False)
            self.dayTempButton.setDisabled(False)
            self.dayHumButton.setDisabled(False)
            self.dayLightButton.setDisabled(False)
            self.nightTempButton.setDisabled(False)
            self.nightHumButton.setDisabled(False)
            self.nightLightButton.setDisabled(False)
            self.actualMode.setText("Current Mode: Auto")
        else:
            self.heaterButton.setEnabled(True)
            self.coolerButton.setEnabled(True)
            self.humidifierButton.setEnabled(True)
            self.heaterButton.setChecked(self.manHeater)
            self.coolerButton.setChecked(self.manComp)
            self.humidifierButton.setChecked(self.manHum)
            self.lightSlider.setEnabled(True)
            self.lampSlider.setValue(self.manLight)
            self.tempButton.setEnabled(False)
            self.humButton.setEnabled(False)
            self.lightButton.setEnabled(False)
            self.manualTempButton.setChecked(True)
            self.manualHumButton.setChecked(True)
            self.manualLightButton.setChecked(True)
            self.dayTempButton.setDisabled(True)
            self.dayHumButton.setDisabled(True)
            self.dayLightButton.setDisabled(True)
            self.nightTempButton.setDisabled(True)
            self.nightHumButton.setDisabled(True)
            self.nightLightButton.setDisabled(True)
            self.actualMode.setText("Current Mode: Manual")
        self.setpointTempDay.setText(self.SPTempDay)
        self.setpointTempNight.setText(self.SPTempNight)
        self.setpointHumDay.setText(self.SPHumDay)
        self.setpointHumNight.setText(self.SPHumNight)
        self.setpointLightDay.setText(self.SPLightDay)
        self.setpointLightNight.setText(self.SPLightNight)
        self.startTimeDay.setText(self.startDay)
        self.startTimeNight.setText(self.startNight)
        
        # behaviour on central widget
        
        self.fullscreenButton.clicked.connect(lambda:self.fullscreenButton_clicked())
        self.takePhoto.clicked.connect(lambda:self.sendPhoto(topCameraDevice, self.pathTopPhoto, "Top"))
        self.takePhoto.clicked.connect(lambda:self.sendPhoto(bottomCameraDevice, self.pathBottomPhoto, "Bottom"))

        # if device has 5 cameras
        if not isThreeCameras:
            self.takePhoto.clicked.connect(lambda:self.sendPhoto(topRightCameraDevice, self.pathTopRightPhoto, "Top Right"))
            self.takePhoto.clicked.connect(lambda:self.sendPhoto(bottomRightCameraDevice, self.pathBottomRightPhoto, "Bottom Right"))
        
        # behaviour on dashboard page
        self.shutdownButton.clicked.connect(lambda:self.shutdownButton_clicked())
        self.toTempPageButton.clicked.connect(lambda:self.buttonToPage_clicked(self.tempPage))
        self.toHumPageButton.clicked.connect(lambda:self.buttonToPage_clicked(self.humPage))
        self.toLightPageButton.clicked.connect(lambda:self.buttonToPage_clicked(self.lightPage))
        self.toDayNightPageButton.clicked.connect(lambda:self.buttonToPage_clicked(self.dayNightPage)) 
        #self.toSeverityPage.clicked.connect(lambda:[self.populate_severity_table(),self.buttonToPage_clicked(self.severityPage),self.gotoSeverityPage()])
        self.viewTray.clicked.connect(self.showTrayImage)
        
        # behaviour on temp page
        self.manualTempButton.stateChanged.connect(lambda: self.manualButton_clicked(self.manualTempButton))
        self.dayTempButton.stateChanged.connect(lambda:self.weatherSetPointButton_clicked("Day", "Temp"))
        self.nightTempButton.stateChanged.connect(lambda:self.weatherSetPointButton_clicked("Night", "Temp"))
        self.tempButton.clicked.connect(lambda:self.setButton_clicked("Temp"))
        self.heaterButton.stateChanged.connect(lambda:self.setActuatorButton_clicked("heater"))
        self.coolerButton.stateChanged.connect(lambda:self.setActuatorButton_clicked("cooler"))
        self.oneButtonTemp.clicked.connect(lambda:self.digitButton_clicked('1', "Temp"))
        self.twoButtonTemp.clicked.connect(lambda:self.digitButton_clicked('2', "Temp"))
        self.threeButtonTemp.clicked.connect(lambda:self.digitButton_clicked('3', "Temp"))
        self.fourButtonTemp.clicked.connect(lambda:self.digitButton_clicked('4', "Temp"))
        self.fiveButtonTemp.clicked.connect(lambda:self.digitButton_clicked('5', "Temp"))
        self.sixButtonTemp.clicked.connect(lambda:self.digitButton_clicked('6', "Temp"))
        self.sevenButtonTemp.clicked.connect(lambda:self.digitButton_clicked('7', "Temp"))
        self.eightButtonTemp.clicked.connect(lambda:self.digitButton_clicked('8', "Temp"))
        self.nineButtonTemp.clicked.connect(lambda:self.digitButton_clicked('9', "Temp"))
        self.zeroButtonTemp.clicked.connect(lambda:self.digitButton_clicked('0', "Temp"))
        self.delButtonTemp.clicked.connect(lambda:self.delButton_clicked("Temp"))
        self.commaButtonTemp.clicked.connect(lambda:self.digitButton_clicked('.', "Temp"))
        self.backFromTemp.clicked.connect(lambda:self.buttonToPage_clicked(self.dashboardPage))
        
        # behaviour on hum page
        self.manualHumButton.stateChanged.connect(lambda:self.manualButton_clicked(self.manualHumButton))
        self.dayHumButton.stateChanged.connect(lambda:self.weatherSetPointButton_clicked("Day", "Hum"))
        self.nightHumButton.stateChanged.connect(lambda:self.weatherSetPointButton_clicked("Night", "Hum"))
        self.humButton.clicked.connect(lambda:self.setButton_clicked("Hum"))
        self.humidifierButton.stateChanged.connect(lambda:self.setActuatorButton_clicked("humidifier"))
        self.oneButtonHum.clicked.connect(lambda:self.digitButton_clicked('1', "Hum"))
        self.twoButtonHum.clicked.connect(lambda:self.digitButton_clicked('2', "Hum"))
        self.threeButtonHum.clicked.connect(lambda:self.digitButton_clicked('3', "Hum"))
        self.fourButtonHum.clicked.connect(lambda:self.digitButton_clicked('4', "Hum"))
        self.fiveButtonHum.clicked.connect(lambda:self.digitButton_clicked('5', "Hum"))
        self.sixButtonHum.clicked.connect(lambda:self.digitButton_clicked('6', "Hum"))
        self.sevenButtonHum.clicked.connect(lambda:self.digitButton_clicked('7', "Hum"))
        self.eightButtonHum.clicked.connect(lambda:self.digitButton_clicked('8', "Hum"))
        self.nineButtonHum.clicked.connect(lambda:self.digitButton_clicked('9', "Hum"))
        self.zeroButtonHum.clicked.connect(lambda:self.digitButton_clicked('0', "Hum"))
        self.delButtonHum.clicked.connect(lambda:self.delButton_clicked("Hum"))
        self.commaButtonHum.clicked.connect(lambda:self.digitButton_clicked('.', "Hum"))
        self.backFromHum.clicked.connect(lambda:self.buttonToPage_clicked(self.dashboardPage))
        
        # behaviour on light page
        self.manualLightButton.stateChanged.connect(lambda:self.manualButton_clicked(self.manualLightButton))
        self.dayLightButton.stateChanged.connect(lambda:self.weatherSetPointButton_clicked("Day", "Light"))
        self.nightLightButton.stateChanged.connect(lambda:self.weatherSetPointButton_clicked("Night", "Light"))
        self.lightButton.clicked.connect(lambda:self.setButton_clicked("Light"))
        self.lightSlider.sliderReleased.connect(lambda:self.lampSlider_released())
        self.oneButtonLight.clicked.connect(lambda:self.digitButton_clicked('1', "Light"))
        self.twoButtonLight.clicked.connect(lambda:self.digitButton_clicked('2', "Light"))
        self.threeButtonLight.clicked.connect(lambda:self.digitButton_clicked('3', "Light"))
        self.fourButtonLight.clicked.connect(lambda:self.digitButton_clicked('4', "Light"))
        self.fiveButtonLight.clicked.connect(lambda:self.digitButton_clicked('5', "Light"))
        self.sixButtonLight.clicked.connect(lambda:self.digitButton_clicked('6', "Light"))
        self.sevenButtonLight.clicked.connect(lambda:self.digitButton_clicked('7', "Light"))
        self.eightButtonLight.clicked.connect(lambda:self.digitButton_clicked('8', "Light"))
        self.nineButtonLight.clicked.connect(lambda:self.digitButton_clicked('9', "Light"))
        self.zeroButtonLight.clicked.connect(lambda:self.digitButton_clicked('0', "Light"))
        self.delButtonLight.clicked.connect(lambda:self.delButton_clicked("Light"))
        self.commaButtonLight.clicked.connect(lambda:self.digitButton_clicked('.', "Light"))
        self.backFromLight.clicked.connect(lambda:self.buttonToPage_clicked(self.dashboardPage))

        # behaviour on day night start time setting page
        self.dayButton.stateChanged.connect(lambda:self.dayNightStartTimeCheckbox_clicked("Day"))
        self.nightButton.stateChanged.connect(lambda:self.dayNightStartTimeCheckbox_clicked("Night"))
        self.setStartTimeButton.clicked.connect(lambda:self.setDayNightButton_clicked())
        self.oneButtonStartTime.clicked.connect(lambda:self.digitButton_clicked('1', "DayNight"))
        self.twoButtonStartTime.clicked.connect(lambda:self.digitButton_clicked('2', "DayNight"))
        self.threeButtonStartTime.clicked.connect(lambda:self.digitButton_clicked('3', "DayNight"))
        self.fourButtonStartTime.clicked.connect(lambda:self.digitButton_clicked('4', "DayNight"))
        self.fiveButtonStartTime.clicked.connect(lambda:self.digitButton_clicked('5', "DayNight"))
        self.sixButtonStartTime.clicked.connect(lambda:self.digitButton_clicked('6', "DayNight"))
        self.sevenButtonStartTime.clicked.connect(lambda:self.digitButton_clicked('7', "DayNight"))
        self.eightButtonStartTime.clicked.connect(lambda:self.digitButton_clicked('8', "DayNight"))
        self.nineButtonStartTime.clicked.connect(lambda:self.digitButton_clicked('9', "DayNight"))
        self.zeroButtonStartTime.clicked.connect(lambda:self.digitButton_clicked('0', "DayNight"))
        self.delButtonStartTime.clicked.connect(lambda:self.delButton_clicked("DayNight"))
        self.backFromDayNight.clicked.connect(lambda:self.buttonToPage_clicked(self.dashboardPage))

        #behaviour on severityPage
        #self.toSeverityPage.clicked.connect(self.gotoSeverityPage)
        self.backFromSeverity.clicked.connect(lambda:self.buttonToPage_clicked(self.dashboardPage))
        init_severity_page(self)
        self.yearMonthLine.installEventFilter(self) # VIRTUAL KEYBOARD
        self.yearMonthLine_2.installEventFilter(self) # VIRTUAL KEYBOARD
        self.yearMonthLine_3.installEventFilter(self) # VIRTUAL KEYBOARD
        
        # check user behaviour
        self.fullscreenButton.clicked.connect(lambda:self.checkLastTouch())
        self.takePhoto.clicked.connect(lambda:self.checkLastTouch())
        self.toTempPageButton.clicked.connect(lambda:self.checkLastTouch())
        self.toHumPageButton.clicked.connect(lambda:self.checkLastTouch())
        self.toLightPageButton.clicked.connect(lambda:self.checkLastTouch())
        self.toDayNightPageButton.clicked.connect(lambda:self.checkLastTouch())
        self.toSeverityPage.clicked.connect(lambda:self.checkLastTouch())

        # function to create QT timer
        def createQTimer(slot, interval):
            timer = QtCore.QTimer()
            timer.timeout.connect(slot)
            timer.start(interval)
            return timer
        self.sendDataCloudTimer = createQTimer(self.sendDataCloud, 10010) # send data to cloud scheduling
        self.sendCallbackTimer = createQTimer(self.sendCallbackCloud, 1005) # send callback to cloud scheduling
        self.sendDataToDBcloudTimer = createQTimer(self.sendDataToDBcloud, 120000) # send data to DB in cloud scheduling
        self.saveDataToLocalFileTimer = createQTimer(self.saveDataToLocalFile, 120000) # save data to local file scheduling
        self.updateTimeTimer = createQTimer(self.updateTime, 500) # update time scheduling
        self.updateActualDataDisplayTimer = createQTimer(self.updateActualDataDisplay, 10000) # update actual data display scheduling
        self.sendDataMCUTimer = createQTimer(self.sendDataMCU, 5000) # send data to mcu scheduling
        self.updatePhotoTimer = createQTimer(self.updatePhoto, 5000) # update photo on onsite UI scheduling
        self.sseRefreshTimer = createQTimer(self.refreshSSEConnection, 30000) # start the timer for SSE connection refresh
        
        # wired serial to hardware
        try:
            self.serial = QtSerialPort.QSerialPort(portUART, baudRate=QtSerialPort.QSerialPort.Baud9600, readyRead=self.receive)
        except:
            print("Serial UART port not available")

        # start the SSE connection
        self.subscribeSSE()
        self.keyboard_active = False # VIRTUAL KEYBOARD

        # take photo when program start and on day
        if ((time.localtime()).tm_hour >= int(self.startDay)) and ((time.localtime()).tm_hour < int(self.startNight)):
            self.sendPhoto(topCameraDevice, self.pathTopPhoto, "Top")
            self.sendPhoto(bottomCameraDevice, self.pathBottomPhoto, "Bottom")
            if not isThreeCameras:
                self.sendPhoto(topRightCameraDevice, self.pathTopRightPhoto, "Top Right")
                self.sendPhoto(bottomRightCameraDevice, self.pathBottomRightPhoto, "Bottom Right")
    
    def gotoSeverityPage(self):
        image_path = "dummy_images/chili_detection_order.jpg"
        pixmap = QtGui.QPixmap(image_path)
        self.trayCamera.setPixmap(pixmap)
        self.trayCamera.setScaledContents(True)
        self.buttonToPage_clicked(self.severityPage)


    def populate_severity_table(self):
        data = [
            ["1","2024-05-14", "19:00", "Level 0"],
            ["2","2024-05-13", "20:00", "Level 1"],
            ["3","2024-05-12", "21:00", "Level 3"],
            ["4","2024-05-11", "22:00", "Level 5"],
            ["5","2024-05-10", "23:00", "Level 7"],
        ]

        self.severityTable.setRowCount(len(data))
        self.severityTable.setColumnCount(4)
        self.severityTable.setHorizontalHeaderLabels(["Cabe", "Date", "Time", "Level"])

        for row_idx, row_data in enumerate(data):
            for col_idx, item in enumerate(row_data):
                self.severityTable.setItem(row_idx, col_idx, QtWidgets.QTableWidgetItem(item))


    # create sse connection
    def subscribeSSE(self):
        try:
            if self.sseManager is not None:
                self.sseManager.deleteLater()
            self.sseManager = QNetworkAccessManager()
            url = QtCore.QUrl(self.urlGetLiveSetpoint)
            request = QNetworkRequest(url)
            request.setRawHeader(b"Cache-Control", b"no-cache")
            request.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.AlwaysNetwork)
            self.sseRequest = self.sseManager.get(request)
            print("Connected to SSE Server")
            self.sseRequest.readyRead.connect(self.onSSEDataReady)
        except:
            print("Failed connect to SSE Server")
    
    # function to handle any received event sse from cloud
    def onSSEDataReady(self):
        try:
            if self.sseRequest.error() == QNetworkReply.NoError:
                data = self.sseRequest.readAll().data().decode(errors='ignore')
                if data:
                    try:
                        json_start_idx = data.find("{")
                        if json_start_idx != -1:
                            json_str = data[json_start_idx:]
                            data_json = json.loads(json_str)
                            print("Received SSE data:", data_json)
                            self.readLiveSetPointFromCloud(data_json)
                    except json.JSONDecodeError as e:
                        print("Error while decoding JSON data:", e)
                else:
                    print("Empty data received from SSE.")
            else:
                print("Error while receiving SSE:", self.sseRequest.errorString())
        except:
            print("Failed Receiving Data from SSE")
    
    # function to parse live data from cloud
    def readLiveSetPointFromCloud(self, data_json):
        print("Receive Set Point Data from Cloud!")
        try:
            if ("take_photos" in data_json):
                self.sendPhoto(topCameraDevice, self.pathTopPhoto, "Top")
                self.sendPhoto(bottomCameraDevice, self.pathBottomPhoto, "Bottom")
                self.sendPhoto(userCameraDevice, self.pathUserPhoto, "User")
                if not isThreeCameras:
                    self.sendPhoto(topRightCameraDevice, self.pathTopRightPhoto, "Top Right")
                    self.sendPhoto(bottomRightCameraDevice, self.pathBottomRightPhoto, "Bottom Right")
                self.receiveCameraCommand = 1
            elif ("temperature" in data_json) and ("humidity" in data_json) and ("intensity" in data_json):
                if (data_json.get("mode") == "Day"):
                    self.SPTempDay = str(data_json.get("temperature"))
                    self.prevSPTempDay = self.SPTempDay
                    self.setpointTempDay.setText(self.SPTempDay)
                    self.SPHumDay = str(data_json.get("humidity"))
                    self.prevSPHumDay = self.SPHumDay
                    self.setpointHumDay.setText(self.SPHumDay)
                    self.SPLightDay = str(data_json.get("intensity"))
                    self.prevSPLightDay = self.SPLightDay
                    self.setpointLightDay.setText(self.SPLightDay)
                else:
                    self.SPTempNight = str(data_json.get("temperature"))
                    self.prevSPTempNight = self.SPTempNight
                    self.setpointTempNight.setText(self.SPTempNight)
                    self.SPHumNight = str(data_json.get("humidity"))
                    self.prevSPHumNight = self.SPHumNight
                    self.setpointHumNight.setText(self.SPHumNight)
                    self.SPLightNight = str(data_json.get("intensity"))
                    self.prevSPLightNight = self.SPLightNight
                    self.setpointLightNight.setText(self.SPLightNight)
                self.saveSPDataToLocalFile()
                self.receiveSetPoint = 1
        except:
            print("Error on reading live data from Cloud")

    # function to refresh sse connection
    def refreshSSEConnection(self):
        try:
            if self.sseRequest is not None:
                self.sseRequest.abort()  # Abort the ongoing request, disconnecting from the previous connection
                self.sseRequest.deleteLater()  # Clean up the request object
                print("Previous SSE Connection disconnected")
            print("Refreshing SSE connection...")
            self.subscribeSSE()
        except:
            print("Failed refresh SSE connection")
    
    # function to change fullscreen status
    def fullscreenButton_clicked(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreenButton.setText("↗")
        else:
            self.showFullScreen()
            self.fullscreenButton.setText("↙")

    # function for moving page by click any button
    def buttonToPage_clicked(self, destinationPage):
        if destinationPage is None:
            print("[ERROR] destinationPage is None — check object name.")
            return  
        self.stackedWidget.setCurrentWidget(destinationPage)
    
    # function for shutdown raspberry
    def shutdownButton_clicked(self):
        if (device == "Beelink") :
            os.system("shutdown -h now")
        else :
            os.system("sudo shutdown -h now")

    # function to handle manual checkbox button
    def manualButton_clicked(self, button):
        if button.isChecked():
            self.heaterButton.setEnabled(True)
            self.coolerButton.setEnabled(True)
            self.humidifierButton.setEnabled(True)
            self.heaterButton.setChecked(self.manHeater)
            self.coolerButton.setChecked(self.manComp)
            self.humidifierButton.setChecked(self.manHum)
            self.lightSlider.setEnabled(True)
            self.lampSlider.setValue(self.manLight)
            self.tempButton.setEnabled(False)
            self.humButton.setEnabled(False)
            self.lightButton.setEnabled(False)
            self.manualTempButton.setChecked(True)
            self.manualHumButton.setChecked(True)
            self.manualLightButton.setChecked(True)
            self.dayTempButton.setDisabled(True)
            self.dayHumButton.setDisabled(True)
            self.dayLightButton.setDisabled(True)
            self.nightTempButton.setDisabled(True)
            self.nightHumButton.setDisabled(True)
            self.nightLightButton.setDisabled(True)
            self.mode = "manual"
            self.actualMode.setText("Current Mode: Manual")
        else:
            self.heaterButton.setEnabled(False)
            self.coolerButton.setEnabled(False)
            self.humidifierButton.setEnabled(False)
            self.lightSlider.setEnabled(False)
            self.tempButton.setEnabled(True)
            self.humButton.setEnabled(True)
            self.lightButton.setEnabled(True)
            self.manualTempButton.setChecked(False)
            self.manualHumButton.setChecked(False)
            self.manualLightButton.setChecked(False)
            self.dayTempButton.setDisabled(False)
            self.dayHumButton.setDisabled(False)
            self.dayLightButton.setDisabled(False)
            self.nightTempButton.setDisabled(False)
            self.nightHumButton.setDisabled(False)
            self.nightLightButton.setDisabled(False)
            self.mode = "auto"
            self.actualMode.setText("Current Mode: Auto")
        self.sendDataCloud()
        self.sendDataMCU()

    # function if day or night set point checkbox is clicked
    def weatherSetPointButton_clicked(self, weather_type, setpoint_type):
        if weather_type == "Day":
            if setpoint_type == "Temp":
                if self.dayTempButton.isChecked():
                    self.nightTempButton.setDisabled(True)
                else:
                    self.nightTempButton.setDisabled(False)
            elif setpoint_type == "Hum":
                if self.dayHumButton.isChecked():
                    self.nightHumButton.setDisabled(True)
                else:
                    self.nightHumButton.setDisabled(False)
            elif setpoint_type == "Light":
                if self.dayLightButton.isChecked():
                    self.nightLightButton.setDisabled(True)
                else:
                    self.nightLightButton.setDisabled(False)
        else:
            if setpoint_type == "Temp":
                if (self.nightTempButton.isChecked() == True):
                    self.dayTempButton.setDisabled(True)
                elif (self.nightTempButton.isChecked() == False):
                    self.dayTempButton.setDisabled(False)
            elif setpoint_type == "Hum":
                if (self.nightHumButton.isChecked() == True):
                    self.dayHumButton.setDisabled(True)
                elif (self.nightHumButton.isChecked() == False):
                    self.dayHumButton.setDisabled(False)
            elif setpoint_type == "Light":
                if (self.nightLightButton.isChecked() == True):
                    self.dayLightButton.setDisabled(True)
                elif (self.nightLightButton.isChecked() == False):
                    self.dayLightButton.setDisabled(False)
    
    # function if day or night start time set checkbox is clicked
    def dayNightStartTimeCheckbox_clicked(self, weather_type):
        if weather_type == "Day":
            if self.dayButton.isChecked():
                self.nightButton.setDisabled(True)
            else:
                self.nightButton.setDisabled(False)
        else:
            if self.nightButton.isChecked():
                self.dayButton.setDisabled(True)
            else:
                self.dayButton.setDisabled(False)

    # function if set optimum button is clicked
    def setButton_clicked(self, setpoint_type):
        if setpoint_type == "Temp":
            if ((float(self.SPTempDay) > self.upLimitSPTemp) or (float(self.SPTempDay) < self.bottomLimitSPTemp) or (float(self.SPTempNight) > self.upLimitSPTemp) or (float(self.SPTempNight) < self.bottomLimitSPTemp)):
                self.SPTempDay = self.prevSPTempDay
                self.SPTempNight = self.prevSPTempNight
                self.setpointTempDay.setText(self.SPTempDay)
                self.setpointTempNight.setText(self.SPTempNight)
            else:
                self.prevSPTempDay = self.SPTempDay
                self.prevSPTempNight = self.SPTempNight
                self.sendDataCloud()
                self.sendDataMCU()
                self.saveSPDataToLocalFile()
        elif setpoint_type == "Hum":
            if ((float(self.SPHumDay) > self.upLimitSPHum) or (float(self.SPHumDay) < self.bottomLimitSPHum) or (float(self.SPHumNight) > self.upLimitSPHum) or (float(self.SPHumNight) < self.bottomLimitSPHum)):
                self.SPHumDay = self.prevSPHumDay
                self.SPHumNight = self.prevSPHumNight
                self.setpointHumDay.setText(self.SPHumDay)
                self.setpointHumNight.setText(self.SPHumNight)
            else:
                self.prevSPHumDay = self.SPHumDay
                self.prevSPHumNight = self.SPHumNight
                self.sendDataCloud()
                self.sendDataMCU()
                self.saveSPDataToLocalFile()
        elif setpoint_type == "Light":
            if ((float(self.SPLightDay) > self.upLimitSPLight) or (float(self.SPLightDay) < self.bottomLimitSPLight) or (float(self.SPLightNight) > self.upLimitSPLight) or (float(self.SPLightNight) < self.bottomLimitSPLight)):
                self.SPLightDay = self.prevSPLightDay
                self.SPLightNight = self.prevSPLightNight
                self.setpointLightDay.setText(self.SPLightDay)
                self.setpointLightNight.setText(self.SPLightNight)
            else:
                self.prevSPLightDay = self.SPLightDay
                self.prevSPLightNight = self.SPLightNight
                self.sendDataCloud()
                self.sendDataMCU()
                self.saveSPDataToLocalFile()

    # function when set day night start time button is clicked
    def setDayNightButton_clicked(self):
        if ((float(self.tempStartDay) > float(self.tempStartNight)) or (float(self.tempStartDay) < 0) or (float(self.tempStartNight) < 0) or (float(self.tempStartDay) > 24) or (float(self.tempStartNight) > 24)):
            self.tempStartDay = self.startDay
            self.tempStartNight = self.startNight
            self.startTimeDay.setText(self.startDay)
            self.startTimeNight.setText(self.startNight)
        else:
            self.startDay = self.tempStartDay
            self.startNight = self.tempStartNight
            self.saveDayNightDataToLocalFile()
    
    # function if set actuator state is clicked
    def setActuatorButton_clicked(self, actuator_type):
        if actuator_type == "heater":
            if self.heaterButton.isChecked():
                self.manHeater = True
            else:
                self.manHeater = False
        elif actuator_type == "cooler":
            if self.coolerButton.isChecked():
                self.manComp = True
            else:
                self.manComp = False
        elif actuator_type == "humidifier":
            if self.humidifierButton.isChecked():
                self.manHum = True
            else:
                self.manHum = False
        self.sendDataMCU()

    # function if lamp slider is released
    def lampSlider_released(self):
        self.manLight = self.lampSlider.value()/4
        self.sendDataMCU()
    
    # function if button digit for optimum value is clicked
    def digitButton_clicked(self, digit, setpoint_type):
        if setpoint_type == "Temp":
            if self.dayTempButton.isChecked():
                self.SPTempDay += digit
                self.setpointTempDay.setText(self.SPTempDay)
            elif self.nightTempButton.isChecked():
                self.SPTempNight += digit
                self.setpointTempNight.setText(self.SPTempNight)
        elif setpoint_type == "Hum":
            if self.dayHumButton.isChecked():
                self.SPHumDay += digit
                self.setpointHumDay.setText(self.SPHumDay)
            elif self.nightHumButton.isChecked():
                self.SPHumNight += digit
                self.setpointHumNight.setText(self.SPHumNight)
        elif setpoint_type == "Light":
            if self.dayLightButton.isChecked():
                self.SPLightDay += digit
                self.setpointLightDay.setText(self.SPLightDay)
            elif self.nightLightButton.isChecked():
                self.SPLightNight += digit
                self.setpointLightNight.setText(self.SPLightNight)
        elif setpoint_type == "DayNight":
            if self.dayButton.isChecked():
                self.tempStartDay += digit
                self.startTimeDay.setText(self.tempStartDay)
            elif self.nightButton.isChecked():
                self.tempStartNight += digit
                self.startTimeNight.setText(self.tempStartNight)
    
    # function if button delete for optimum value is clicked
    def delButton_clicked(self, setpoint_type):
        if setpoint_type == "Temp":
            if self.dayTempButton.isChecked():
                self.setpointTempDay.setText(self.SPTempDay[:-1])
                self.SPTempDay = self.setpointTempDay.text()
            elif self.nightTempButton.isChecked():
                self.setpointTempNight.setText(self.SPTempNight[:-1])
                self.SPTempNight = self.setpointTempNight.text()
        elif setpoint_type == "Hum":
            if self.dayHumButton.isChecked():
                self.setpointHumDay.setText(self.SPHumDay[:-1])
                self.SPHumDay = self.setpointHumDay.text()
            elif self.nightHumButton.isChecked():
                self.setpointHumNight.setText(self.SPHumNight[:-1])
                self.SPHumNight = self.setpointHumNight.text()
        elif setpoint_type == "Light":
            if self.dayLightButton.isChecked():
                self.setpointLightDay.setText(self.SPLightDay[:-1])
                self.SPLightDay = self.setpointLightDay.text()
            elif self.nightLightButton.isChecked():
                self.setpointLightNight.setText(self.SPLightNight[:-1])
                self.SPLightNight = self.setpointLightNight.text()
        elif setpoint_type == "DayNight":
            if self.dayButton.isChecked():
                self.startTimeDay.setText(self.tempStartDay[:-1])
                self.tempStartDay = self.startTimeDay.text()
            elif self.nightButton.isChecked():
                self.startTimeNight.setText(self.tempStartNight[:-1])
                self.tempStartNight = self.startTimeNight.text()

    # update actual data display
    def updateActualDataDisplay(self):
        self.actualTemp.setText(self.actTemp)
        self.actualHum.setText(self.actHum)
        self.actualLight.setText(self.actLight)
    
    # function to update time on display
    def updateTime(self):
        gmt = time.localtime()
        if (len(str(gmt.tm_min)) == 1):
            str_seconds = "0" + str(gmt.tm_min)
        else:
            str_seconds = str(gmt.tm_min)
        self.str_time = str(gmt.tm_hour) + ":" + str_seconds
        self.actualTime.setText(self.str_time)
        self.str_day = ""
        if (gmt.tm_wday == 0):
            self.str_day = "Monday"
        elif (gmt.tm_wday == 1):
            self.str_day = "Tuesday"
        elif (gmt.tm_wday == 2):
            self.str_day = "Wednesday"
        elif (gmt.tm_wday == 3):
            self.str_day = "Thursday"
        elif (gmt.tm_wday == 4):
            self.str_day = "Friday"
        elif (gmt.tm_wday == 5):
            self.str_day = "Saturday"
        else:
            self.str_day = "Sunday"
        self.str_date = self.str_day + ",  " + str(gmt.tm_mday) + "/" + str(gmt.tm_mon) + "/" + str(gmt.tm_year)
        self.actualDate.setText(self.str_date)
        
    #for showing tray image
    def showTrayImage(self):
            image_path = "dummy_images/chili_detection_order.jpg"  # Replace with your actual image path
            pixmap = QtGui.QPixmap(image_path)
            self.cameraHome.setPixmap(pixmap)
            self.cameraHome.setScaledContents(True)


    # function for updating photo on dashboard
    def updatePhoto(self):
        if (self.currentPhoto == self.pathTopPhoto):
            if isThreeCameras:
                self.currentPhoto = self.pathBottomPhoto
                self.actualPosition.setText("Bottom")
            else:
                self.currentPhoto = self.pathTopRightPhoto
                self.actualPosition.setText("Top Right")
        elif (self.currentPhoto == self.pathTopRightPhoto):
            self.currentPhoto = self.pathBottomPhoto
            self.actualPosition.setText("Bottom")
        elif (self.currentPhoto == self.pathBottomPhoto):
            if isThreeCameras:
                self.currentPhoto = self.pathTopPhoto
                self.actualPosition.setText("Top")
            else:
                self.currentPhoto = self.pathBottomRightPhoto
                self.actualPosition.setText("Bottom Right")
        else:
            self.currentPhoto = self.pathTopPhoto
            self.actualPosition.setText("Top")
        self.cameraHome.setPixmap(QtGui.QPixmap(self.currentPhoto).scaled(621, 481, QtCore.Qt.KeepAspectRatio))
    
    # function for save data to local file
    def saveDataToLocalFile(self):
        try:
            if ((time.localtime()).tm_hour >= int(self.startDay)) and ((time.localtime()).tm_hour < int(self.startNight)):
                self.SPTemp = self.SPTempDay
                self.SPHum = self.SPHumDay
                self.SPLight = self.SPLightDay
            else:
                self.SPTemp = self.SPTempNight
                self.SPHum = self.SPHumNight
                self.SPLight = self.SPLightNight
            cpu_temp = self.get_cpu_temperature()
            data_local = str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec) + "_" + str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" + str(time.localtime().tm_year) + "," + str(self.mode) + "," + str(self.SPTemp) + "," + str(self.SPHum) + "," + str(self.SPLight) + "," + str(self.actTemp) + "," + str(self.actHum) + "," + str(self.actLight) + "," + str(self.manHeater) + "," + str(self.manComp) + "," + str(self.manLight) + "," + str(self.manHum) + "," + f"{cpu_temp:.2f}" + "\n"
            header = "timestamp,mode,SPTemp,SPHum,SPLight,actTemp,actHum,actLight,manHeater,manComp,manLight,manHum,cpuTemp" + "\n"
            dbFilename = prefixPath + "Data/Data " + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_year) + ".csv"
            if (os.path.exists(dbFilename) == True):
                f = open(dbFilename, "a")
                f.write(data_local)
            else:
                f = open(dbFilename, "a")
                f.write(header)
                f.write(data_local)
            print("Data saved to local file (" + dbFilename + ")")
        except:
            print("Failed save data to local file as excel")
    
    # function for save last actual data
    def saveActualDataToLocalFile(self):
        try:
            data_local = str(self.actTemp) + "\n" + str(self.actHum) + "\n" + str(self.actLight) + "\n" + str(self.mode) + "\n" + str(self.manHeater) + "\n" + str(self.manComp) + "\n" + str(self.manHum) + "\n" + str(self.manLight)
            with open(self.lastActualDataFilename, "w") as f:
                f.write(data_local)
            print(data_local)
            print("Actual condition data saved to local file (" + self.lastActualDataFilename + ")")
        except:
            print("Failed save actual condition data to local file as excel")
    
    # function for save last set point data
    def saveSPDataToLocalFile(self):
        try:
            data_local = str(self.SPTempDay) + "\n" + str(self.SPHumDay) + "\n" + str(self.SPLightDay) + "\n" + str(self.SPTempNight) + "\n" + str(self.SPHumNight) + "\n" + str(self.SPLightNight)
            with open(self.lastSPDataFilename, "w") as f:
                f.write(data_local)
            print("Set point data saved to local file (" + self.lastSPDataFilename + ")")
        except:
            print("Failed save set point data to local file as excel")

    # function for save last set day night start timer
    def saveDayNightDataToLocalFile(self):
        try:
            data_local = str(self.startDay) + "\n" + str(self.startNight)
            with open(self.lastDayNightDataFilename, "w") as f:
                f.write(data_local)
            print("Day night start time data saved to local file (" + self.lastDayNightDataFilename + ")")
        except:
            print("Failed save day night start time data to local file as excel")
    
    # function for checking duration from last touch
    def checkLastTouch(self):
        currentTouch = (time.localtime()).tm_min
        differenceTouchTime = currentTouch - self.lastMinuteTouch
        if (differenceTouchTime < 0):
            differenceTouchTime = differenceTouchTime + 60
        if (differenceTouchTime >= self.intervalSendUserPhoto):
            self.sendPhoto(userCameraDevice, self.pathUserPhoto, "User")
            print("New User Detected, Photo User sent to Cloud")
        self.lastMinuteTouch = currentTouch 

    def get_cpu_temperature(self):
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as file:
                temp = float(file.read()) / 1000.0
                return temp
        except FileNotFoundError:
            return None

    # send current live data in hardware to cloud
    def sendDataCloud(self) :
        if (self.actTemp != "") or (self.actHum != "") or (self.actLight != ""):
            try:
                if ((time.localtime()).tm_hour >= int(self.startDay)) and ((time.localtime()).tm_hour < int(self.startNight)):
                    self.SPTemp = self.SPTempDay
                    self.SPHum = self.SPHumDay
                    self.SPLight = self.SPLightDay
                else:
                    self.SPTemp = self.SPTempNight
                    self.SPHum = self.SPHumNight
                    self.SPLight = self.SPLightNight
                cpu_temp = self.get_cpu_temperature()
                data_json ={
                    "device_id" : deviceId,
                    "mode" : self.mode,
                    "temperature": float(self.actTemp),
                    "humidity": float(self.actHum),
                    "intensity": float(self.actLight),
                    "SPTemp" : self.SPTemp,
                    "SPHum" : self.SPHum,
                    "SPLight" : self.SPLight,
                    "gateway_temp": 0,
                    "water_status" : self.waterStatus,
                }
                print(data_json)
                response = requests.request("POST", self.urlPostLiveCond, headers=self.requestHeader, data=json.dumps(data_json), timeout=10)
                print("Live Data sent to Cloud")
            except (requests.ConnectionError, requests.Timeout) as exception:
                pass
                print("Failed sent Live Data to Cloud")
    
    # send callback to cloud
    def sendCallbackCloud(self) :
        if (self.receiveCameraCommand == 1) or (self.receiveSetPoint == 1):
            try:
                if (self.receiveSetPoint == 1):
                    msg = "Setpoint settings received"
                    self.receiveSetPoint = 0
                else:
                    msg = "Camera command received"
                    self.receiveCameraCommand = 0
                data_callback = {
                    "message": msg
                }
                response = requests.request("POST", self.urlPostLiveCallback, headers=self.requestHeader, data=json.dumps(data_callback), timeout=10)
                print("Any callback sent to Cloud")
            except (requests.ConnectionError, requests.Timeout) as exception:
                pass
                print("Failed sent callback to Cloud")

    # send current live data in hardware to be saved in DB cloud
    def sendDataToDBcloud(self) :
        if (self.actTemp != "") or (self.actHum != "") or (self.actLight != ""):
            try:
                cpu_temp = self.get_cpu_temperature()
                data = {
                    "device_id" : int(deviceId),
                    "temperature": float(self.actTemp),
                    "humidity": float(self.actHum),
                    "intensity": float(self.actLight),
                    "SPTemp" : self.SPTemp,
                    "SPHum" : self.SPHum,
                    "SPLight" : self.SPLight,
                    "gateway_temp": 0,
                    "water_status" : self.waterStatus,
                }
                print(data)
                response = requests.request("POST", self.urlPostCondToDB, headers=self.requestHeader, data=json.dumps(data), timeout=10)
                print("Data sent to Cloud Database")
            except (requests.ConnectionError, requests.Timeout) as exception:
                pass
                print("Send data to database cloud failed")

    # function for sending data to hardware
    def sendDataMCU(self):
        try:
            if ((time.localtime()).tm_hour >= int(self.startDay)) and ((time.localtime()).tm_hour < int(self.startNight)):
                self.SPTemp = self.SPTempDay
                self.SPHum = self.SPHumDay
                self.SPLight = self.SPLightDay
            else:
                self.SPTemp = self.SPTempNight
                self.SPHum = self.SPHumNight
                self.SPLight = self.SPLightNight
            data_json ={
                "mode"        : self.mode,
                "SPTemp"    : self.SPTemp,
                "SPHum"        : self.SPHum,
                "SPLight"    : self.SPLight,
                "sHeater"    : self.manHeater,
                "sComp"        : self.manComp,
                "sLight"    : self.manLight,
                "sHum"        : self.manHum,
            }
            payloadMCU = str.encode(json.dumps(data_json)+'\n')
            print(payloadMCU)
            self.serial.open(QtCore.QIODevice.ReadWrite)
            self.serial.write(payloadMCU)
            print("Data sent to MCU")
        except:
            print("Failed send data to MCU")

    # function for sending photo to cloud
    def sendPhoto(self, camera_device, file_path, photo_type):
        try:
            # Gunakan gambar dummy lokal sebagai pengganti capture kamera
            dummy_image_path = 'dummy_images/tray.jpg'  # Ganti sesuai lokasi file dummy kamu
            if os.path.exists(dummy_image_path):
                image = cv2.imread(dummy_image_path)
                cv2.imwrite(file_path, image)
                print(f"[DUMMY] {photo_type} Dummy Image copied to {file_path}")
            else:
                print(f"[DUMMY] Dummy image not found at {dummy_image_path}")
                return

            # Simulasikan pengiriman ke cloud (tidak sungguhan kirim)
            print(f"[DUMMY] Successfully 'sent' {photo_type} Photo to cloud (simulated)")
        
        except Exception as e:
            print(f"[DUMMY] Error in sendPhoto (dummy mode): {e}")

    
    # function for receiving serial message from mcu
    @QtCore.pyqtSlot()
    def receive(self):
        try:
            self.serial.open(QtCore.QIODevice.ReadWrite)
            while self.serial.canReadLine():
                buffer = self.serial.readLine().data().decode(errors='ignore')
                print(f"Received data from MCU: {buffer}")
                try:
                    data = json.loads(buffer.encode().decode())
                    tempTemp = data.get("actTemp")
                    tempHum = data.get("actHum")
                    tempLight = data.get("actLight")
                    tempWaterStatus = data.get("actWater")
                    self.actTemp = str(round(float(tempTemp), 1))
                    self.subActualTemp.setText(self.actTemp)
                    self.actHum = str(int(float(tempHum)))
                    self.subActualHum.setText(self.actHum)
                    self.actLight = str(int(float(tempLight)))
                    self.subActualLight.setText(self.actLight)
                    if (tempWaterStatus != None):
                        self.waterStatus = str(int(tempWaterStatus))
                    self.saveActualDataToLocalFile()
                    print("Successfully receive data from MCU and save to Local File")
                except json.JSONDecodeError:
                    print("Data received from MCU but not saved to variable and Local File")
        except:
            print("Failed receiving data from MCU")

    # VIRTUAL KEYBOARD
    def eventFilter(self, source, event):
        if event.type() == QtCore.QEvent.FocusIn:
            if source in [self.yearMonthLine, self.yearMonthLine_2, self.yearMonthLine_3]:
                if not self.keyboard_active:
                    self.keyboard_active = True
                    self.keyboard = VirtualKeyboard(source, self)
                    self.keyboard.show()
        return super().eventFilter(source, event)

# EDIT
class VirtualKeyboard(QWidget):
    def __init__(self, target_input, main_ui):
        super().__init__()
        self.target_input = target_input
        self.main_ui = main_ui  # referensi ke UI utama
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Keyboard")
        self.setFixedSize(400, 200)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        layout = QGridLayout()
        keys = [
            ['1','2','3','4','5','6','7','8','9','0'],
            ['Q','W','E','R','T','Y','U','I','O','P'],
            ['A','S','D','F','G','H','J','K','L'],
            ['Z','X','C','V','B','N','M'],
            ['-', '/', '_', 'del', 'Space', 'OK'],
            ['←','→','↑','↓']  # baris tambahan
        ]

        for row_idx, row in enumerate(keys):
            for col_idx, key in enumerate(row):
                btn = QPushButton(key)
                btn.setFixedHeight(40)
                btn.setStyleSheet("font-size: 16px;")
                btn.clicked.connect(self.on_button_clicked)
                layout.addWidget(btn, row_idx, col_idx)

        self.setLayout(layout)

    def on_button_clicked(self):
        key = self.sender().text()
        current = self.target_input.text()

        if key == 'del':
            self.target_input.setText(current[:-1])
        elif key == 'Space':
            self.target_input.setText(current + ' ')
        elif key == 'OK':
            self.main_ui.keyboard_active = False
            self.target_input.clearFocus()
            self.hide()
        elif key == '←':
            self.target_input.cursorBackward(False, 1)
        elif key == '→':
            self.target_input.cursorForward(False, 1)
        elif key == '↑':
            self.target_input.cursorUp(False, 1)
        elif key == '↓':
            self.target_input.cursorDown(False, 1)
        else:
            self.target_input.setText(current + key)

    def closeEvent(self, event):
        self.main_ui.keyboard_active = False
        self.target_input.clearFocus()
        event.accept()


# initialize app
QApplication.setStyle("fussion")
app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()



