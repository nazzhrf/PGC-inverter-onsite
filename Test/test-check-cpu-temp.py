def get_cpu_temperature():
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as file:
            temp = float(file.read()) / 1000.0
            return temp
    except FileNotFoundError:
        return None

if __name__ == "__main__":
    cpu_temp = get_cpu_temperature()
    if cpu_temp is not None:
        print(f"CPU Temperature: {cpu_temp:.2f} °C")
    else:
        print("Failed to read CPU temperature.")