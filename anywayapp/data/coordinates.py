import csv
import json

accidents_file = "H20101042AccData.csv"

coordinates = []
for accident in csv.DictReader(open(accidents_file)):
	coordinates.append({"x": accident["X"], "y": accident["Y"]})

open("coordinates.json","w").write(json.dumps(coordinates))



