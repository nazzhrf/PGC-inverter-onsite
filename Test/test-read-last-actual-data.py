import os

# hardware parameter
mode = "auto"
pwmHeater, pwmFan, manLight = 0, 0, 0
manHeater, manComp, manHum = False, False, False

# set actual condition parameter
actTemp, actHum, actLight = "", "", ""

# try get last actual data
lastActualDataFilename = "Actual/Last_Actual_Data.csv"
if (os.path.exists(lastActualDataFilename) == True):
    try:
        with open(lastActualDataFilename, "r") as file:
            lines = file.readlines()
        actTemp = lines[0].strip()
        actHum = lines[1].strip()
        actLight = lines[2].strip()
        mode = lines[3].strip()
        manHeater = lines[4].strip() == "True"
        manComp = lines[5].strip() == "True"
        manHum = lines[6].strip() == "True"
        manLight = float(lines[7].strip())
        print("Success get last actual data")
    except:
        print("Failed get last actual data")

print(actTemp)
print(actHum)
print(actLight)
print(mode)
print(manHeater)
print(manComp)
print(manHum)
print(manLight)