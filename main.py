"""
Gateway Subsistem
Smart Growth Chamber
Thesis by Muhammad Arbi Minanda (23220344)
"""

#libraries
from PyQt5 import QtCore, QtWidgets, QtSerialPort, QtNetwork
from PyQt5.QtWidgets import QApplication, QStackedWidget, QWidget, QMainWindow, QLabel, QPushButton, QSpinBox, QSlider, QCheckBox, QLineEdit, QFileDialog 
from PyQt5.QtGui import QPixmap
from PyQt5 import uic
from PyQt5.QtCore import QThread
import sseclient
import sys 
import time; 
import json
import requests
import cv2
import os.path
import subprocess
import os

os.environ.pop("QT_QPA_PLATFORM_PLUGIN_PATH")

# thread to read data from API
class Worker(QThread):
    data_json = QtCore.pyqtSignal(dict)
    def __init__(self, endpoint):
        super().__init__()
        self.endpoint = endpoint
        
    def run(self) :
        url = self.endpoint
        while True:
            try:
                messages = sseclient.SSEClient(url)
                for msg in messages:
                    try:
                        data = json.loads(msg.data)
                        if (data == {}):
                            pass
                        else:
                            self.data_json.emit(data)
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                print("Error:", e)
                # Add a delay before attempting reconnect SSE
                time.sleep(5)

class UI(QMainWindow):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("UI/main.ui", self)
        
        self._manager = QtNetwork.QNetworkAccessManager()
        
        #hardware parameter
        self.mode = "auto"
        self.actTemp = ""
        self.actHum = ""
        self.actLight = ""
        self.SPTemp = "30"
        self.SPHum = "70"
        self.SPLight = "4000"
        self.pwmHeater = 0
        self.pwmFan = 0
        self.manHeater = False
        self.manComp = False
        self.manHum = False
        self.manLight = 0
        
        #day or night parameter
        self.SPTempDay = "30"
        self.SPHumDay = "70"
        self.SPLightDay = "4000"
        self.SPTempNight = "23"
        self.SPHumNight = "90"
        self.SPLightNight = "0"
        self.startDay = "6"
        self.startNight = "18"
        
        #boolean variable
        self.receiveCloud = False
        self.connected = False
        self.lastMinuteTouch = (time.localtime()).tm_min

        #camera devices
        self.topCameraDevice = 'HX-USB Camera: HX-USB Camera (usb-0000:01:00.0-1.2.4):'
        self.bottomCameraDevice = 'USB_2.0_Webcam: USB_2.0_Webcam (usb-0000:01:00.0-1.2.2):'
        self.userCameraDevice = 'HP Webcam: HP Webcam (usb-0000:01:00.0-1.2.3):'

        #variable for chamber identifier
        self.deviceId = "3"
        self.deviceKey = "e8866d201336427ac4057dafb408eaea6bf2f574fb553809da0fa0abe659eea09a5daf2a8c115525f8b115f8add7d7aca7bbb864c3d21f"
        self.baseUrl = 'https://api.smartfarm.id'
        self.urlGetLiveSetpoint = self.baseUrl + '/condition/getsetpoint/' + self.deviceId + '?device_key=' + self.deviceKey
        self.urlPostLiveCond = self.baseUrl + '/condition/data/' + self.deviceId
        self.urlPostCondToDB = self.baseUrl + '/condition/create'
        self.urlPostPhoto = self.baseUrl + '/file/kamera'

        #variable for photo
        self.pathTopPhoto = 'Image/top_chamber' + self.deviceId + '.png'
        self.pathBottomPhoto = 'Image/bottom_chamber' + self.deviceId + '.png'
        self.pathUserPhoto = 'Image/user_chamber' + self.deviceId + '.png'
        self.currentPhoto = self.pathTopPhoto
        self.intervalSendUserPhoto = 1
        
        #waiting till internet connection exist for initialize app
        while (self.connected == False):
            try:
                requests.get('https://reqres.in/api/users/1')
                self.connected = True
            except:
                self.connected = False
        
        #pages
        self.stackedWidget = self.findChild(QStackedWidget, "stackedWidget")
        self.dashboardPage = self.findChild(QWidget, "dashboardPage")
        self.tempPage = self.findChild(QWidget, "tempPage")
        self.humPage = self.findChild(QWidget, "humPage")
        self.lightPage = self.findChild(QWidget, "lightPage")
        self.photoPage = self.findChild(QWidget, "photoPage")
        
        #parent element
        self.fullscreenButton = self.findChild(QPushButton, "fullscreenButton")
        self.toPhotoPageButton = self.findChild(QPushButton, "toPhotoPage")
        self.shutdownButton = self.findChild(QPushButton, "shutdown")
        self.actualTime = self.findChild(QLabel, "actualTime")
        self.actualDay = self.findChild(QLabel, "actualDay")
        self.actualDate = self.findChild(QLabel, "actualDate")
        self.actualMode = self.findChild(QLabel, "actualMode")
        
        #dashboard page element
        self.toTempPageButton = self.findChild(QPushButton, "toTempPage")
        self.toHumPageButton = self.findChild(QPushButton, "toHumPage")
        self.toLightPageButton = self.findChild(QPushButton, "toLightPage")
        self.actualTemp = self.findChild(QLabel, "actualTempVal")
        self.actualHum = self.findChild(QLabel, "actualHumVal")
        self.actualLight = self.findChild(QLabel, "actualLightVal")
        self.cameraHome = self.findChild(QLabel, "cameraHome")
        self.actualPosition = self.findChild(QLabel, "actPosition")
        self.takePhoto = self.findChild(QPushButton, "takePhoto")

        #temp page element
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
        
        #hum page element
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

        #light page element
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

        #camera page element
        self.cameraTop = self.findChild(QLabel, "cameraTop")
        self.cameraBottom = self.findChild(QLabel, "cameraBottom")
        self.cameraUser = self.findChild(QLabel, "cameraUser")
        self.subTakePhoto = self.findChild(QPushButton, "subTakePhoto")
        self.backFromCamera = self.findChild(QPushButton, "goDashboardFromCamera")

        #initial display
        self.showMaximized()
        self.stackedWidget.setCurrentWidget(self.dashboardPage)
        self.showFullScreen()
        self.fullscreenButton.setText("↙")
        #self.cameraTop.setPixmap(QPixmap(self.pathTopPhoto).scaled(301, 231, QtCore.Qt.KeepAspectRatio))
        #self.cameraBottom.setPixmap(QPixmap(self.pathBottomPhoto).scaled(301, 231, QtCore.Qt.KeepAspectRatio))
        #self.cameraHome.setPixmap(QPixmap(self.currentPhoto).scaled(621, 481, QtCore.Qt.KeepAspectRatio))
        self.actualPosition.setText("Top")
        self.actualMode.setText("Current Mode: Auto")
        self.setpointTempDay.setText(self.SPTempDay)
        self.setpointTempNight.setText(self.SPTempNight)
        self.setpointHumDay.setText(self.SPHumDay)
        self.setpointHumNight.setText(self.SPHumNight)
        self.setpointLightDay.setText(self.SPLightDay)
        self.setpointLightNight.setText(self.SPLightNight)
        
        #initial state of button
        self.heaterButton.setEnabled(False)
        self.coolerButton.setEnabled(False)
        self.humidifierButton.setEnabled(False)
        self.lampSlider.setEnabled(False)

        # disable manual mode
        """
        self.manualTempButton.setEnabled(False)
        self.manualHumButton.setEnabled(False)
        self.manualLightButton.setEnabled(False)
        """

        #disable toPhotoPage button
        self.toPhotoPageButton.setEnabled(False)
        
        #behaviour on central widget
        self.toPhotoPageButton.clicked.connect(lambda:self.toPhotoPageButton_clicked())
        self.fullscreenButton.clicked.connect(lambda:self.fullscreenButton_clicked())
        self.takePhoto.clicked.connect(lambda:self.sendPhotoTop())
        self.takePhoto.clicked.connect(lambda:self.sendPhotoBottom())
        
        #behaviour on dashboard page
        self.shutdownButton.clicked.connect(lambda:self.shutdownButton_clicked())
        self.toTempPageButton.clicked.connect(lambda:self.toTempPageButton_clicked())
        self.toHumPageButton.clicked.connect(lambda:self.toHumPageButton_clicked())
        self.toLightPageButton.clicked.connect(lambda:self.toLightPageButton_clicked())
        
        #behaviour on temp page
        self.manualTempButton.stateChanged.connect(lambda:self.manualTempButton_clicked())
        self.dayTempButton.stateChanged.connect(lambda:self.dayTempButton_clicked())
        self.nightTempButton.stateChanged.connect(lambda:self.nightTempButton_clicked())
        self.tempButton.clicked.connect(lambda:self.tempButton_clicked())
        self.heaterButton.stateChanged.connect(lambda:self.heaterButton_clicked())
        self.coolerButton.stateChanged.connect(lambda:self.coolerButton_clicked())
        self.oneButtonTemp.clicked.connect(lambda:self.oneButtonTemp_clicked())
        self.twoButtonTemp.clicked.connect(lambda:self.twoButtonTemp_clicked())
        self.threeButtonTemp.clicked.connect(lambda:self.threeButtonTemp_clicked())
        self.fourButtonTemp.clicked.connect(lambda:self.fourButtonTemp_clicked())
        self.fiveButtonTemp.clicked.connect(lambda:self.fiveButtonTemp_clicked())
        self.sixButtonTemp.clicked.connect(lambda:self.sixButtonTemp_clicked())
        self.sevenButtonTemp.clicked.connect(lambda:self.sevenButtonTemp_clicked())
        self.eightButtonTemp.clicked.connect(lambda:self.eightButtonTemp_clicked())
        self.nineButtonTemp.clicked.connect(lambda:self.nineButtonTemp_clicked())
        self.zeroButtonTemp.clicked.connect(lambda:self.zeroButtonTemp_clicked())
        self.delButtonTemp.clicked.connect(lambda:self.delButtonTemp_clicked())
        self.commaButtonTemp.clicked.connect(lambda:self.commaButtonTemp_clicked())
        self.backFromTemp.clicked.connect(lambda:self.backFromTemp_clicked())
        
        #behaviour on hum page
        self.manualHumButton.stateChanged.connect(lambda:self.manualHumButton_clicked())
        self.dayHumButton.stateChanged.connect(lambda:self.dayHumButton_clicked())
        self.nightHumButton.stateChanged.connect(lambda:self.nightHumButton_clicked())
        self.humButton.clicked.connect(lambda:self.humButton_clicked())
        self.humidifierButton.stateChanged.connect(lambda:self.humidifierButton_clicked())
        self.oneButtonHum.clicked.connect(lambda:self.oneButtonHum_clicked())
        self.twoButtonHum.clicked.connect(lambda:self.twoButtonHum_clicked())
        self.threeButtonHum.clicked.connect(lambda:self.threeButtonHum_clicked())
        self.fourButtonHum.clicked.connect(lambda:self.fourButtonHum_clicked())
        self.fiveButtonHum.clicked.connect(lambda:self.fiveButtonHum_clicked())
        self.sixButtonHum.clicked.connect(lambda:self.sixButtonHum_clicked())
        self.sevenButtonHum.clicked.connect(lambda:self.sevenButtonHum_clicked())
        self.eightButtonHum.clicked.connect(lambda:self.eightButtonHum_clicked())
        self.nineButtonHum.clicked.connect(lambda:self.nineButtonHum_clicked())
        self.zeroButtonHum.clicked.connect(lambda:self.zeroButtonHum_clicked())
        self.delButtonHum.clicked.connect(lambda:self.delButtonHum_clicked())
        self.commaButtonHum.clicked.connect(lambda:self.commaButtonHum_clicked())
        self.backFromHum.clicked.connect(lambda:self.backFromHum_clicked())
        
        #behaviour on light page
        self.manualLightButton.stateChanged.connect(lambda:self.manualLightButton_clicked())
        self.dayLightButton.stateChanged.connect(lambda:self.dayLightButton_clicked())
        self.nightLightButton.stateChanged.connect(lambda:self.nightLightButton_clicked())
        self.lightButton.clicked.connect(lambda:self.lightButton_clicked())
        self.lightSlider.sliderReleased.connect(lambda:self.lampSlider_released())
        self.lightSlider.valueChanged.connect(lambda:self.lampSlider_changed())
        self.oneButtonLight.clicked.connect(lambda:self.oneButtonLight_clicked())
        self.twoButtonLight.clicked.connect(lambda:self.twoButtonLight_clicked())
        self.threeButtonLight.clicked.connect(lambda:self.threeButtonLight_clicked())
        self.fourButtonLight.clicked.connect(lambda:self.fourButtonLight_clicked())
        self.fiveButtonLight.clicked.connect(lambda:self.fiveButtonLight_clicked())
        self.sixButtonLight.clicked.connect(lambda:self.sixButtonLight_clicked())
        self.sevenButtonLight.clicked.connect(lambda:self.sevenButtonLight_clicked())
        self.eightButtonLight.clicked.connect(lambda:self.eightButtonLight_clicked())
        self.nineButtonLight.clicked.connect(lambda:self.nineButtonLight_clicked())
        self.zeroButtonLight.clicked.connect(lambda:self.zeroButtonLight_clicked())
        self.delButtonLight.clicked.connect(lambda:self.delButtonLight_clicked())
        self.commaButtonLight.clicked.connect(lambda:self.commaButtonLight_clicked())
        self.backFromLight.clicked.connect(lambda:self.backFromLight_clicked())
        
        #behaviour on photo page
        self.backFromCamera.clicked.connect(lambda:self.backFromCamera_clicked())
        self.subTakePhoto.clicked.connect(lambda:self.sendPhotoTop())
        self.subTakePhoto.clicked.connect(lambda:self.sendPhotoBottom())

        #check user behaviour
        self.toPhotoPageButton.clicked.connect(lambda:self.checkLastTouch())
        self.fullscreenButton.clicked.connect(lambda:self.checkLastTouch())
        self.takePhoto.clicked.connect(lambda:self.checkLastTouch())
        self.toTempPageButton.clicked.connect(lambda:self.checkLastTouch())
        self.toHumPageButton.clicked.connect(lambda:self.checkLastTouch())
        self.toLightPageButton.clicked.connect(lambda:self.checkLastTouch())

        #send data to cloud scheduling
        self.sendDataCloudTimer = QtCore.QTimer()
        self.sendDataCloudTimer.timeout.connect(lambda:self.sendDataCloud())
        self.sendDataCloudTimer.start(10010)
        
        #send data to DB in cloud scheduling
        self.sendDataToDBcloudTimer = QtCore.QTimer()
        self.sendDataToDBcloudTimer.timeout.connect(lambda:self.sendDataToDBcloud())
        self.sendDataToDBcloudTimer.start(1800000)
        
        #send data to mcu scheduling
        """
        self.sendDataMCUTimer = QtCore.QTimer()
        self.sendDataMCUTimer.timeout.connect(lambda:self.sendDataMCU())
        self.sendDataMCUTimer.start(5000)
        """
        
        #save data to local file scheduling
        self.saveDataToLocalFileTimer = QtCore.QTimer()
        self.saveDataToLocalFileTimer.timeout.connect(lambda:self.saveDataToLocalFile())
        self.saveDataToLocalFileTimer.start(120000)

        #update time scheduling
        self.updateTimeTimer = QtCore.QTimer()
        self.updateTimeTimer.timeout.connect(lambda:self.updateTime())
        self.updateTimeTimer.start(500)

        #update actual data display scheduling
        self.updateActualDataDisplayTimer = QtCore.QTimer()
        self.updateActualDataDisplayTimer.timeout.connect(lambda:self.updateActualDataDisplay())
        self.updateActualDataDisplayTimer.start(10000)

        #update photo home scheduling
        self.updatePhotoTimer = QtCore.QTimer()
        self.updatePhotoTimer.timeout.connect(lambda:self.updatePhoto())
        self.updatePhotoTimer.start(5000)
        
        #camera scheduling
        self.sendPhotoTopTimer = QtCore.QTimer()
        self.sendPhotoTopTimer.timeout.connect(lambda:self.sendPhotoTop())
        self.sendPhotoTopTimer.start(3600000)
        self.sendPhotoBottomTimer = QtCore.QTimer()
        self.sendPhotoBottomTimer.timeout.connect(lambda:self.sendPhotoBottom())
        self.sendPhotoBottomTimer.start(3600000)
        
        #create thread to get/subscribe live setpoint
        self.thread = Worker(self.urlGetLiveSetpoint)
        self.thread.data_json.connect(self.readLiveSetPointFromCloud)
        self.thread.start()
        
        #wired serial to hardware
        self.serial = QtSerialPort.QSerialPort('/dev/ttyAMA0', baudRate=QtSerialPort.QSerialPort.Baud9600, readyRead=self.receive)
        if not self.serial.isOpen():
            self.serial.open(QtCore.QIODevice.ReadWrite)

    #function to change fullscreen status
    def fullscreenButton_clicked(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreenButton.setText("↗")
        else:
            self.showFullScreen()
            self.fullscreenButton.setText("↙")
    
    #function for moving to temp page
    def toTempPageButton_clicked(self):
        self.stackedWidget.setCurrentWidget(self.tempPage)

    #function for shutdown raspberry
    def shutdownButton_clicked(self):
        os.system("sudo shutdown -h now")

    #function for moving to hum page
    def toHumPageButton_clicked(self):
        self.stackedWidget.setCurrentWidget(self.humPage)

    #function for moving to light page
    def toLightPageButton_clicked(self):
        self.stackedWidget.setCurrentWidget(self.lightPage)

    #function for moving to photo page
    def toPhotoPageButton_clicked(self):
        self.stackedWidget.setCurrentWidget(self.photoPage)

    #function for moving to dashboard page
    def backFromTemp_clicked(self):
        self.stackedWidget.setCurrentWidget(self.dashboardPage)
    def backFromHum_clicked(self):
        self.stackedWidget.setCurrentWidget(self.dashboardPage)
    def backFromLight_clicked(self):
        self.stackedWidget.setCurrentWidget(self.dashboardPage)
    def backFromCamera_clicked(self):
        self.stackedWidget.setCurrentWidget(self.dashboardPage)

    #function if all manual button is clicked    
    def manualTempButton_clicked(self):
        if (self.manualTempButton.isChecked() == True):
            self.heaterButton.setEnabled(True)
            self.coolerButton.setEnabled(True)
            self.humidifierButton.setEnabled(True)
            self.lightSlider.setEnabled(True)
            self.tempButton.setEnabled(False)
            self.humButton.setEnabled(False)
            self.lightButton.setEnabled(False)
            self.oneButtonTemp.setEnabled(False)
            self.twoButtonTemp.setEnabled(False)
            self.threeButtonTemp.setEnabled(False)
            self.fourButtonTemp.setEnabled(False)
            self.fiveButtonTemp.setEnabled(False)
            self.sixButtonTemp.setEnabled(False)
            self.sevenButtonTemp.setEnabled(False)
            self.eightButtonTemp.setEnabled(False)
            self.nineButtonTemp.setEnabled(False)
            self.zeroButtonTemp.setEnabled(False)
            self.commaButtonTemp.setEnabled(False)
            self.delButtonTemp.setEnabled(False)
            self.oneButtonHum.setEnabled(False)
            self.twoButtonHum.setEnabled(False)
            self.threeButtonHum.setEnabled(False)
            self.fourButtonHum.setEnabled(False)
            self.fiveButtonHum.setEnabled(False)
            self.sixButtonHum.setEnabled(False)
            self.sevenButtonHum.setEnabled(False)
            self.eightButtonHum.setEnabled(False)
            self.nineButtonHum.setEnabled(False)
            self.zeroButtonHum.setEnabled(False)
            self.commaButtonHum.setEnabled(False)
            self.delButtonHum.setEnabled(False)
            self.manualTempButton.setChecked(True)
            self.manualHumButton.setChecked(True)
            self.manualLightButton.setChecked(True)
            self.mode = "manual"
            self.actualMode.setText("Current Mode: Manual")
        elif (self.manualTempButton.isChecked() == False):
            self.heaterButton.setEnabled(False)
            self.coolerButton.setEnabled(False)
            self.humidifierButton.setEnabled(False)
            self.lightSlider.setEnabled(False)
            self.tempButton.setEnabled(True)
            self.humButton.setEnabled(True)
            self.lightButton.setEnabled(True)
            self.oneButtonTemp.setEnabled(True)
            self.twoButtonTemp.setEnabled(True)
            self.threeButtonTemp.setEnabled(True)
            self.fourButtonTemp.setEnabled(True)
            self.fiveButtonTemp.setEnabled(True)
            self.sixButtonTemp.setEnabled(True)
            self.sevenButtonTemp.setEnabled(True)
            self.eightButtonTemp.setEnabled(True)
            self.nineButtonTemp.setEnabled(True)
            self.zeroButtonTemp.setEnabled(True)
            self.commaButtonTemp.setEnabled(True)
            self.delButtonTemp.setEnabled(True)
            self.oneButtonHum.setEnabled(True)
            self.twoButtonHum.setEnabled(True)
            self.threeButtonHum.setEnabled(True)
            self.fourButtonHum.setEnabled(True)
            self.fiveButtonHum.setEnabled(True)
            self.sixButtonHum.setEnabled(True)
            self.sevenButtonHum.setEnabled(True)
            self.eightButtonHum.setEnabled(True)
            self.nineButtonHum.setEnabled(True)
            self.zeroButtonHum.setEnabled(True)
            self.commaButtonHum.setEnabled(True)
            self.delButtonHum.setEnabled(True)
            self.oneButtonLight.setEnabled(True)
            self.twoButtonLight.setEnabled(True)
            self.threeButtonLight.setEnabled(True)
            self.fourButtonLight.setEnabled(True)
            self.fiveButtonLight.setEnabled(True)
            self.sixButtonLight.setEnabled(True)
            self.sevenButtonLight.setEnabled(True)
            self.eightButtonLight.setEnabled(True)
            self.nineButtonLight.setEnabled(True)
            self.zeroButtonLight.setEnabled(True)
            self.commaButtonLight.setEnabled(True)
            self.delButtonLight.setEnabled(True)
            self.manualTempButton.setChecked(False)
            self.manualHumButton.setChecked(False)
            self.manualLightButton.setChecked(False)
            self.mode = "auto"
            self.actualMode.setText("Current Mode: Auto")
        self.sendDataCloud()
        self.sendDataMCU()
    
    def manualHumButton_clicked(self):
        if (self.manualHumButton.isChecked() == True):
            self.heaterButton.setEnabled(True)
            self.coolerButton.setEnabled(True)
            self.humidifierButton.setEnabled(True)
            self.lightSlider.setEnabled(True)
            self.tempButton.setEnabled(False)
            self.humButton.setEnabled(False)
            self.lightButton.setEnabled(False)
            self.oneButtonTemp.setEnabled(False)
            self.twoButtonTemp.setEnabled(False)
            self.threeButtonTemp.setEnabled(False)
            self.fourButtonTemp.setEnabled(False)
            self.fiveButtonTemp.setEnabled(False)
            self.sixButtonTemp.setEnabled(False)
            self.sevenButtonTemp.setEnabled(False)
            self.eightButtonTemp.setEnabled(False)
            self.nineButtonTemp.setEnabled(False)
            self.zeroButtonTemp.setEnabled(False)
            self.commaButtonTemp.setEnabled(False)
            self.delButtonTemp.setEnabled(False)
            self.oneButtonHum.setEnabled(False)
            self.twoButtonHum.setEnabled(False)
            self.threeButtonHum.setEnabled(False)
            self.fourButtonHum.setEnabled(False)
            self.fiveButtonHum.setEnabled(False)
            self.sixButtonHum.setEnabled(False)
            self.sevenButtonHum.setEnabled(False)
            self.eightButtonHum.setEnabled(False)
            self.nineButtonHum.setEnabled(False)
            self.zeroButtonHum.setEnabled(False)
            self.commaButtonHum.setEnabled(False)
            self.delButtonHum.setEnabled(False)
            self.manualTempButton.setChecked(True)
            self.manualHumButton.setChecked(True)
            self.manualLightButton.setChecked(True)
            self.mode = "manual"
            self.actualMode.setText("Current Mode: Manual")
        elif (self.manualHumButton.isChecked() == False):
            self.heaterButton.setEnabled(False)
            self.coolerButton.setEnabled(False)
            self.humidifierButton.setEnabled(False)
            self.lightSlider.setEnabled(False)
            #self.setpointTemp.setDisabled(False)
            #self.setpointHum.setDisabled(False)
            #self.setpointLight.setDisabled(False)
            self.tempButton.setEnabled(True)
            self.humButton.setEnabled(True)
            self.lightButton.setEnabled(True)
            self.oneButtonTemp.setEnabled(True)
            self.twoButtonTemp.setEnabled(True)
            self.threeButtonTemp.setEnabled(True)
            self.fourButtonTemp.setEnabled(True)
            self.fiveButtonTemp.setEnabled(True)
            self.sixButtonTemp.setEnabled(True)
            self.sevenButtonTemp.setEnabled(True)
            self.eightButtonTemp.setEnabled(True)
            self.nineButtonTemp.setEnabled(True)
            self.zeroButtonTemp.setEnabled(True)
            self.commaButtonTemp.setEnabled(True)
            self.delButtonTemp.setEnabled(True)
            self.oneButtonHum.setEnabled(True)
            self.twoButtonHum.setEnabled(True)
            self.threeButtonHum.setEnabled(True)
            self.fourButtonHum.setEnabled(True)
            self.fiveButtonHum.setEnabled(True)
            self.sixButtonHum.setEnabled(True)
            self.sevenButtonHum.setEnabled(True)
            self.eightButtonHum.setEnabled(True)
            self.nineButtonHum.setEnabled(True)
            self.zeroButtonHum.setEnabled(True)
            self.commaButtonHum.setEnabled(True)
            self.delButtonHum.setEnabled(True)
            self.oneButtonLight.setEnabled(True)
            self.twoButtonLight.setEnabled(True)
            self.threeButtonLight.setEnabled(True)
            self.fourButtonLight.setEnabled(True)
            self.fiveButtonLight.setEnabled(True)
            self.sixButtonLight.setEnabled(True)
            self.sevenButtonLight.setEnabled(True)
            self.eightButtonLight.setEnabled(True)
            self.nineButtonLight.setEnabled(True)
            self.zeroButtonLight.setEnabled(True)
            self.commaButtonLight.setEnabled(True)
            self.delButtonLight.setEnabled(True)
            self.manualTempButton.setChecked(False)
            self.manualHumButton.setChecked(False)
            self.manualLightButton.setChecked(False)
            self.mode = "auto"
            self.actualMode.setText("Current Mode: Auto")
        self.sendDataCloud()
        self.sendDataMCU()

    def manualLightButton_clicked(self):
        if (self.manualLightButton.isChecked() == True):
            self.heaterButton.setEnabled(True)
            self.coolerButton.setEnabled(True)
            self.humidifierButton.setEnabled(True)
            self.lightSlider.setEnabled(True)
            self.humButton.setEnabled(False)
            self.lightButton.setEnabled(False)
            self.oneButtonTemp.setEnabled(False)
            self.twoButtonTemp.setEnabled(False)
            self.threeButtonTemp.setEnabled(False)
            self.fourButtonTemp.setEnabled(False)
            self.fiveButtonTemp.setEnabled(False)
            self.sixButtonTemp.setEnabled(False)
            self.sevenButtonTemp.setEnabled(False)
            self.eightButtonTemp.setEnabled(False)
            self.nineButtonTemp.setEnabled(False)
            self.zeroButtonTemp.setEnabled(False)
            self.commaButtonTemp.setEnabled(False)
            self.delButtonTemp.setEnabled(False)
            self.oneButtonHum.setEnabled(False)
            self.twoButtonHum.setEnabled(False)
            self.threeButtonHum.setEnabled(False)
            self.fourButtonHum.setEnabled(False)
            self.fiveButtonHum.setEnabled(False)
            self.sixButtonHum.setEnabled(False)
            self.sevenButtonHum.setEnabled(False)
            self.eightButtonHum.setEnabled(False)
            self.nineButtonHum.setEnabled(False)
            self.zeroButtonHum.setEnabled(False)
            self.commaButtonHum.setEnabled(False)
            self.delButtonHum.setEnabled(False)
            self.manualTempButton.setChecked(True)
            self.manualHumButton.setChecked(True)
            self.manualLightButton.setChecked(True)
            self.mode = "manual"
            self.actualMode.setText("Current Mode: Manual")
        elif (self.manualLightButton.isChecked() == False):
            self.heaterButton.setEnabled(False)
            self.coolerButton.setEnabled(False)
            self.humidifierButton.setEnabled(False)
            self.lightSlider.setEnabled(False)
            self.tempButton.setEnabled(True)
            self.humButton.setEnabled(True)
            self.lightButton.setEnabled(True)
            self.oneButtonTemp.setEnabled(True)
            self.twoButtonTemp.setEnabled(True)
            self.threeButtonTemp.setEnabled(True)
            self.fourButtonTemp.setEnabled(True)
            self.fiveButtonTemp.setEnabled(True)
            self.sixButtonTemp.setEnabled(True)
            self.sevenButtonTemp.setEnabled(True)
            self.eightButtonTemp.setEnabled(True)
            self.nineButtonTemp.setEnabled(True)
            self.zeroButtonTemp.setEnabled(True)
            self.commaButtonTemp.setEnabled(True)
            self.delButtonTemp.setEnabled(True)
            self.oneButtonHum.setEnabled(True)
            self.twoButtonHum.setEnabled(True)
            self.threeButtonHum.setEnabled(True)
            self.fourButtonHum.setEnabled(True)
            self.fiveButtonHum.setEnabled(True)
            self.sixButtonHum.setEnabled(True)
            self.sevenButtonHum.setEnabled(True)
            self.eightButtonHum.setEnabled(True)
            self.nineButtonHum.setEnabled(True)
            self.zeroButtonHum.setEnabled(True)
            self.commaButtonHum.setEnabled(True)
            self.delButtonHum.setEnabled(True)
            self.oneButtonLight.setEnabled(True)
            self.twoButtonLight.setEnabled(True)
            self.threeButtonLight.setEnabled(True)
            self.fourButtonLight.setEnabled(True)
            self.fiveButtonLight.setEnabled(True)
            self.sixButtonLight.setEnabled(True)
            self.sevenButtonLight.setEnabled(True)
            self.eightButtonLight.setEnabled(True)
            self.nineButtonLight.setEnabled(True)
            self.zeroButtonLight.setEnabled(True)
            self.commaButtonLight.setEnabled(True)
            self.delButtonLight.setEnabled(True)
            self.manualTempButton.setChecked(False)
            self.manualHumButton.setChecked(False)
            self.manualLightButton.setChecked(False)
            self.mode = "auto"
            self.actualMode.setText("Current Mode: Auto")
        self.sendDataCloud()
        self.sendDataMCU()

    def dayTempButton_clicked(self):
        if (self.dayTempButton.isChecked() == True):
            self.nightTempButton.setDisabled(True)
        elif (self.dayTempButton.isChecked() == False):
            self.nightTempButton.setDisabled(False)
    
    def nightTempButton_clicked(self):
        if (self.nightTempButton.isChecked() == True):
            self.dayTempButton.setDisabled(True)
        elif (self.nightTempButton.isChecked() == False):
            self.dayTempButton.setDisabled(False)
    
    def dayHumButton_clicked(self):
        if (self.dayHumButton.isChecked() == True):
            self.nightHumButton.setDisabled(True)
        elif (self.dayHumButton.isChecked() == False):
            self.nightHumButton.setDisabled(False)

    def nightHumButton_clicked(self):
        if (self.nightHumButton.isChecked() == True):
            self.dayHumButton.setDisabled(True)
        elif (self.nightHumButton.isChecked() == False):
            self.dayHumButton.setDisabled(False)
    
    def dayLightButton_clicked(self):
        if (self.dayLightButton.isChecked() == True):
            self.nightLightButton.setDisabled(True)
        elif (self.dayLightButton.isChecked() == False):
            self.nightLightButton.setDisabled(False)

    def nightLightButton_clicked(self):
        if (self.nightLightButton.isChecked() == True):
            self.dayLightButton.setDisabled(True)
        elif (self.nightLightButton.isChecked() == False):
            self.dayLightButton.setDisabled(False)

    #function if set optimum temp button is clicked
    def tempButton_clicked(self):
        self.sendDataCloud()
        self.sendDataMCU()
    
    #function if set optimum hum button is clicked
    def humButton_clicked(self):
        self.sendDataCloud()
        self.sendDataMCU()

    #function if set optimum light button is clicked
    def lightButton_clicked(self):
        self.sendDataCloud()
        self.sendDataMCU()
    
    #function if set heater state is clicked
    def heaterButton_clicked(self):
        if self.heaterButton.isChecked() == True:
            self.manHeater = True
        else:
            self.manHeater = False
        self.sendDataCloud()
        self.sendDataMCU()
    
    #function if set cooler state is clicked
    def coolerButton_clicked(self):
        if self.coolerButton.isChecked() == True:
            self.manComp = True
        else:
            self.manComp = False
        self.sendDataCloud()
        self.sendDataMCU()
    
    #function if set humidifier state is clicked
    def humidifierButton_clicked(self):
        if self.humidifierButton.isChecked() == True:
            self.manHum = True
        else:
            self.manHum = False
        self.sendDataCloud()
        self.sendDataMCU()
    
    #function if lamp slider is released
    def lampSlider_released(self):
        self.manLight = self.lampSlider.value()/4
        self.sendDataCloud()
        self.sendDataMCU()
    
    #function if lamp slider value is changed
    def lampSlider_changed(self):
        if self.receiveCloud == True:
            self.manLight = self.lampSlider.value()/4
            self.sendDataCloud()
            self.sendDataMCU()
            self.receiveCloud = False
    
    #function if button one for type temp optimum value is clicked
    def oneButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '1'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '1'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button one for type hum optimum value is clicked
    def oneButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '1'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '1'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button one for type light optimum value is clicked
    def oneButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '1'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '1'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button two for type temp optimum value is clicked
    def twoButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '2'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '2'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button two for type hum optimum value is clicked
    def twoButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '2'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '2'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button two for type light optimum value is clicked
    def twoButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '2'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '2'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button three for type temp optimum value is clicked
    def threeButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '3'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '3'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button three for type hum optimum value is clicked
    def threeButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '3'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '3'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button three for type light optimum value is clicked
    def threeButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '3'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '3'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button four for type temp optimum value is clicked
    def fourButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '4'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '4'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button four for type hum optimum value is clicked
    def fourButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '4'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '4'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button four for type light optimum value is clicked
    def fourButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '4'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '4'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button five for type temp optimum value is clicked
    def fiveButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '5'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '5'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button five for type hum optimum value is clicked
    def fiveButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '5'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '5'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button five for type light optimum value is clicked
    def fiveButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '5'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '5'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button six for type temp optimum value is clicked
    def sixButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '6'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '6'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button six for type hum optimum value is clicked
    def sixButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '6'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '6'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button six for type light optimum value is clicked
    def sixButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '6'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '6'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button seven for type temp optimum value is clicked
    def sevenButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '7'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '7'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button seven for type hum optimum value is clicked
    def sevenButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '7'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '7'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button seven for type light optimum value is clicked
    def sevenButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '7'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '7'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button eight for type temp optimum value is clicked
    def eightButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '8'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '8'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button eight for type hum optimum value is clicked
    def eightButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '8'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '8'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button eight for type light optimum value is clicked
    def eightButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '8'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '8'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button nine for type temp optimum value is clicked
    def nineButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '9'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '9'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button nine for type hum optimum value is clicked
    def nineButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '9'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '9'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button nine for type light optimum value is clicked
    def nineButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '9'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '9'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button zero for type temp optimum value is clicked
    def zeroButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '0'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '0'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button zero for type hum optimum value is clicked
    def zeroButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '0'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '0'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button zero for type light optimum value is clicked
    def zeroButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '0'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '0'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button comma for type temp optimum value is clicked
    def commaButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text() + '.'
            self.setpointTempDay.setText(self.SPTempDay)
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text() + '.'
            self.setpointTempNight.setText(self.SPTempNight)

    #function if button comma for type hum optimum value is clicked
    def commaButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text() + '.'
            self.setpointHumDay.setText(self.SPHumDay)
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text() + '.'
            self.setpointHumNight.setText(self.SPHumNight)
    
    #function if button comma for type light optimum value is clicked
    def commaButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text() + '.'
            self.setpointLightDay.setText(self.SPLightDay)
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text() + '.'
            self.setpointLightNight.setText(self.SPLightNight)
    
    #function if button delete for type temp optimum value is clicked
    def delButtonTemp_clicked(self):
        if self.dayTempButton.isChecked() == True:
            self.SPTempDay = self.setpointTempDay.text()
            self.setpointTempDay.setText(self.SPTempDay[:-1])
        elif self.nightTempButton.isChecked() == True:
            self.SPTempNight = self.setpointTempNight.text()
            self.setpointTempNight.setText(self.SPTempNight[:-1])

    #function if button delete for type hum optimum value is clicked
    def delButtonHum_clicked(self):
        if self.dayHumButton.isChecked() == True:
            self.SPHumDay = self.setpointHumDay.text()
            self.setpointHumDay.setText(self.SPHumDay[:-1])
        elif self.nightHumButton.isChecked() == True:
            self.SPHumNight = self.setpointHumNight.text()
            self.setpointHumNight.setText(self.SPHumNight[:-1])

    #function if button delete for type light optimum value is clicked
    def delButtonLight_clicked(self):
        if self.dayLightButton.isChecked() == True:
            self.SPLightDay = self.setpointLightDay.text()
            self.setpointLightDay.setText(self.SPLightDay[:-1])
        elif self.nightLightButton.isChecked() == True:
            self.SPLightNight = self.setpointLightNight.text()
            self.setpointLightNight.setText(self.SPLightNight[:-1])

    #update actual data display
    def updateActualDataDisplay(self):
        self.actualTemp.setText(self.actTemp)
        self.actualHum.setText(self.actHum)
        self.actualLight.setText(self.actLight)
    
    #function to update time on display
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
        
    #function for updating photo on dashboard
    def updatePhoto(self):
        if (self.currentPhoto == self.pathTopPhoto):
            self.currentPhoto = self.pathBottomPhoto
            self.actualPosition.setText("Bottom")
        else:
            self.currentPhoto = self.pathTopPhoto
            self.actualPosition.setText("Top")
        self.cameraHome.setPixmap(QPixmap(self.currentPhoto).scaled(621, 481, QtCore.Qt.KeepAspectRatio))

    #function for save data to local file
    def saveDataToLocalFile(self):
        if ((time.localtime()).tm_hour >= int(self.startDay)) and ((time.localtime()).tm_hour < int(self.startNight)):
            self.SPTemp = self.SPTempDay
            self.SPHum = self.SPHumDay
            self.SPLight = self.SPLightDay
        else:
            self.SPTemp = self.SPTempNight
            self.SPHum = self.SPHumNight
            self.SPLight = self.SPLightNight
        data_local = str(time.localtime().tm_hour) + ":" + str(time.localtime().tm_min) + ":" + str(time.localtime().tm_sec) + "_" + str(time.localtime().tm_mday) + "/" + str(time.localtime().tm_mon) + "/" + str(time.localtime().tm_year) + "," + str(self.mode) + "," + str(self.SPTemp) + "," + str(self.SPHum) + "," + str(self.SPLight) + "," + str(self.actTemp) + "," + str(self.actHum) + "," + str(self.actLight) + "," + str(self.manHeater) + "," + str(self.manComp) + "," + str(self.manLight) + "," + str(self.manHum) + "\n"
        header = "timestamp,mode,SPTemp,SPHum,SPLight,actTemp,actHum,actLight,manHeater,manComp,manLight,manHum" + "\n"
        dbFilename = "Data/Data " + str(time.localtime().tm_mon) + "_" + str(time.localtime().tm_year) + ".csv"
        if (os.path.exists(dbFilename) == True):
            f = open(dbFilename, "a")
            f.write(data_local)
        else:
            f = open(dbFilename, "a")
            f.write(header)
            f.write(data_local)
        print("Data saved to local file (" + dbFilename + ")")
    
    #function for checking duration from last touch
    def checkLastTouch(self):
        currentTouch = (time.localtime()).tm_min
        differenceTouchTime = currentTouch - self.lastMinuteTouch
        if (differenceTouchTime < 0):
            differenceTouchTime = differenceTouchTime + 60
        if (differenceTouchTime >= self.intervalSendUserPhoto):
            self.sendPhotoUser()
            print("New User Detected, Photo User sent to Cloud")
        self.lastMinuteTouch = currentTouch 

    #send current live data in hardware to cloud
    def sendDataCloud(self) :
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
                "device_id" : self.deviceId,
                "mode" : self.mode,
                "SPTemp" : self.SPTemp,
                "SPHum" : self.SPHum,
                "SPLight" : self.SPLight,
                "temperature" : float(self.actTemp),
                "humidity" : float(self.actHum),
                "intensity" : float(self.actLight),
                "sHeater" : self.manHeater,
                "sComp" : self.manComp,
                "sLight" : self.manLight*4,
                "sHum" : self.manHum,
            }
            header = {
                'Content-Type': 'application/json',
                'device_key': self.deviceKey,
            }
            response = requests.request("POST", self.urlPostLiveCond, headers=header, data=json.dumps(data_json))
            print("Live Data sent to Cloud")
        except (requests.ConnectionError, requests.Timeout) as exception:
            pass
            print("Failed sent Live Data to Cloud")
        

    #send current live data in hardware to be saved in DB cloud
    def sendDataToDBcloud(self) :
        try:
            data = {
                "temperature" : float(self.actTemp),
                "humidity" : float(self.actHum),
                "intensity" : float(self.actLight),
                "device_id" : int(self.deviceId)
            }
            header = {
                'Content-Type': 'application/json',
                'device_key': self.deviceKey,
            }
            response = requests.request("POST", self.urlPostCondToDB, headers=header, data=json.dumps(data))
        except (requests.ConnectionError, requests.Timeout) as exception:
            pass
            print("Send data to database cloud failed")
        

    #function to read live setpoint data from cloud
    def readLiveSetPointFromCloud(self, data_json):
        print("Receive Set Point Data from Cloud!")
        try:
            self.receiveCloud = True
            if ("take_photos" in data_json):
                self.sendPhotoTop()
                self.sendPhotoBottom()
                self.sendPhotoUser()
            else: 
                if ("temperature" in data_json):
                    if (data_json.get("mode") == "Day"):
                        self.SPTempDay = str(data_json.get("temperature"))
                        self.setpointTempDay.setText(self.SPTempDay)
                    else:
                        self.SPTempNight = str(data_json.get("temperature"))
                        self.setpointTempNight.setText(self.SPTempNight)
                if ("humidity" in data_json):
                    if (data_json.get("mode") == "Day"):
                        self.SPHumDay = str(data_json.get("humidity"))
                        self.setpointHumDay.setText(self.SPHumDay)
                    else:
                        self.SPHumNight = str(data_json.get("humidity"))
                        self.setpointHumNight.setText(self.SPHumNight)
                if ("intensity" in data_json):
                    if (data_json.get("mode") == "Day"):
                        self.SPLightDay = str(data_json.get("intensity"))
                        self.setpointLightDay.setText(self.SPLightDay)
                    else:
                        self.SPLightNight = str(data_json.get("intensity"))
                        self.setpointLightNight.setText(self.SPLightNight)
                if ("take_photos" in data_json):
                    self.sendPhotoTop()
                    self.sendPhotoBottom()
                    self.sendPhotoUser()
                self.sendDataMCU()
        except:
            print("Error on reading live data from Cloud")

    #function for sending data to hardware
    def sendDataMCU(self):
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
        self.serial.write(payloadMCU)
        print("Data sent to MCU")

    #function for sending top photo to cloud
    def sendPhotoTop(self):
        try:
            df2 = subprocess.check_output("v4l2-ctl --list-devices", shell=True)
            df2Byte = df2.decode('utf8').split('\n')
            indexTopCam = df2Byte.index(self.topCameraDevice)
            indexTopVideo = df2Byte[indexTopCam+1][-1]
            cam = cv2.VideoCapture(int(indexTopVideo))
            if cam.isOpened():
                ret, image = cam.read()
                if ret:
                    cv2.imwrite(self.pathTopPhoto, image)
                    print("Top Image Captured and Saved")
                cam.release()
            #self.cameraTop.setPixmap(QPixmap(self.pathTopPhoto).scaled(301, 231, QtCore.Qt.KeepAspectRatio))
            try:
                files = {'files': open(self.pathTopPhoto,'rb')}
                values = {'device_id': int(self.deviceId)}
                header = {
                    'device_key': self.deviceKey,
                }
                response = requests.post(self.urlPostPhoto, headers=header, files=files, data=values)
                print("Successfully sent Top Photo")
            except:
                print("Failed sent Top Photo")
        except:
            print("Top Camera not found")
    
    #function for sending bottom photo to cloud
    def sendPhotoBottom(self):
        try:
            df2 = subprocess.check_output("v4l2-ctl --list-devices", shell=True)
            df2Byte = df2.decode('utf8').split('\n')
            indexBottomCam = df2Byte.index(self.bottomCameraDevice)
            indexBottomVideo = df2Byte[indexBottomCam+1][-1]
            cam2 = cv2.VideoCapture(int(indexBottomVideo))
            if cam2.isOpened():
                ret, image = cam2.read()
                if ret:
                    cv2.imwrite(self.pathBottomPhoto, image)
                    print("Bottom Image Captured and Saved")
                cam2.release()
            #self.cameraBottom.setPixmap(QPixmap(self.pathBottomPhoto).scaled(301, 231, QtCore.Qt.KeepAspectRatio))
            try:
                files = {'files': open(self.pathBottomPhoto,'rb')}
                values = {'device_id': int(self.deviceId)}
                header = {
                    'device_key': self.deviceKey,
                }
                response = requests.post(self.urlPostPhoto, headers=header, files=files, data=values)
                print("Successfully sent Bottom Photo")
            except:
                print("Failed sent Bottom Photo")
        except:
            print("Bottom Camera not found")
    
    #function for sending user photo to cloud
    def sendPhotoUser(self):
        try:
            df2 = subprocess.check_output("v4l2-ctl --list-devices", shell=True)
            df2Byte = df2.decode('utf8').split('\n')
            indexUserCam = df2Byte.index(self.userCameraDevice)
            indexUserVideo = df2Byte[indexUserCam+1][-1]
            cam4 = cv2.VideoCapture(int(indexUserVideo))
            if cam4.isOpened():
                ret, image = cam4.read()
                if ret:
                    cv2.imwrite(self.pathUserPhoto, image)
                    print("User Image Captured and Saved")
                cam4.release()
            #self.cameraUser.setPixmap(QPixmap(self.pathUserPhoto).scaled(301, 231, QtCore.Qt.KeepAspectRatio))
            try:
                files = {'files': open(self.pathUserPhoto,'rb')}
                values = {'device_id': int(self.deviceId)}
                header = {
                    'device_key': self.deviceKey,
                }
                response = requests.post(self.urlPostPhoto, headers=header, files=files, data=values)
                print(response)
                print("Successfully sent User Photo")
            except:
                print("Failed sent User Photo")
        except:
            print("User Camera not found")
    
    #function for receiving serial message from mcu
    @QtCore.pyqtSlot()
    def receive(self):
        self.serial.open(QtCore.QIODevice.ReadWrite)
        while self.serial.canReadLine():
            buffer = self.serial.readLine().data().decode(errors='ignore')
            print(buffer)
            try:
                data = json.loads(buffer.encode().decode())
                tempTemp = data.get("actTemp")
                self.actTemp = tempTemp[0:len(tempTemp)-1]
                self.subActualTemp.setText(self.actTemp)
                tempHum = data.get("actHum")
                self.actHum = tempHum[0:len(tempHum)-3]
                self.subActualHum.setText(self.actHum)
                tempLight = data.get("actLight")
                self.actLight = tempLight[0:len(tempLight)-3]
                self.subActualLight.setText(self.actLight)
                self.pwmHeater = data.get("pwmHeater")
            except json.JSONDecodeError:
                pass

#initialize app
QtWidgets.QApplication.setStyle("fussion")
app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()
