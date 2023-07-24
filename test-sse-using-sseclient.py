from sseclient import SSEClient
import time
import json

def sse_client(url):
    retry_delay = 1  # Initial retry delay in seconds
    max_retry_delay = 4  # Maximum retry delay in seconds

    while True:
        try:
            messages = SSEClient(url)
            print("Connected to SSE server")
            for msg in messages:
                if msg.data:
                    data_json = json.loads(msg.data)
                    readLiveSetPointFromCloud(data_json)
                else:
                    messages.close()  # Disconnect from SSE server
                    print("Disconnected from SSE server")
        except Exception as e:
            print("Error:", e)
            print("Retrying in {} seconds...".format(retry_delay))

        # Exponential backoff for retries
        time.sleep(retry_delay)
        retry_delay *= 2
        retry_delay = min(retry_delay, max_retry_delay)

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
    url = "http://localhost:9000/condition/getsetpoint/1?device_key=7580e769d9bc179870133a98255588320d21392803544323019372acbddc559f7ea16813dfaa91dd9b2ab069208cf07fe6988567ea9282"
    sse_client(url)
