import requests
import time
import json

def sse_client(url):
    headers = {
        "Accept": "text/event-stream",
    }
    retry_delay = 1  # Initial retry delay in seconds
    max_retry_delay = 32  # Maximum retry delay in seconds

    while True:
        try:
            response = requests.get(url, headers=headers, stream=True)
            if response.status_code == 200:
                print("Connected to SSE server")
                for line in response.iter_lines(decode_unicode=True):
                    if line.strip() and ":heartbeat" not in line:
                        data_json = json.loads(line.replace("data: ", ""))
                        print("Received message:", data_json)
                        readLiveSetPointFromCloud(data_json)
            else:
                print("Failed to connect. Retrying in {} seconds...".format(retry_delay))
        except requests.exceptions.RequestException as e:
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
            print("Taking photo...")
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

if __name__ == "__main__":
    url = "https://api.smartfarm.id/condition/getsetpoint/3?device_key=e8866d201336427ac4057dafb408eaea6bf2f574fb553809da0fa0abe659eea09a5daf2a8c115525f8b115f8add7d7aca7bbb864c3d21f"
    sse_client(url)

