from sseclient import SSEClient
import time
import json

def sse_client(url):
    while True:
        try:
            messages = SSEClient(url)
            print("Connected to SSE server")
            for msg in messages:
                if msg.data:
                    data_json = json.loads(msg.data)
                    readLiveSetPointFromCloud(data_json)
        except Exception as e:
            print("Error:", e)

def readLiveSetPointFromCloud(data_json):
    print("Receive Data from Cloud!")
    try:
        if "take_photos" in data_json:
            printTakePhoto()
        else:
            if "temperature" in data_json:
                temperature_data = data_json["temperature"]
                print("temperature: " + str(temperature_data))
            if "humidity" in data_json:
                humidity_data = data_json["humidity"]
                print("humidity: " + str(humidity_data))
            if "intensity" in data_json:
                intensity_data = data_json["intensity"]
                print("intensity: " + str(intensity_data))
            if "mode" in data_json:
                mode_data = data_json["mode"]
                print("mode: " + mode_data)      
    except Exception as e:
        print("Error on reading live data from Cloud:", e)

def printTakePhoto():
    print("Take photo....")

if __name__ == "__main__":
    url = "https://api.smartfarm.id/condition/getsetpoint/10?device_key=bb090a4b72e73d29408ed6b854d358a4be9c363f11adf6bc37c0cf12cab98a47187a1257159dd898e33eafa21f1b5f6c6b02328b7d22ee"
    sse_client(url)
