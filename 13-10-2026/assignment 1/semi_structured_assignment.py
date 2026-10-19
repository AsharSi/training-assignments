import json
import pandas as pd

from collections import Counter

with open('semi_structured_data.json') as json_file:
    data = json.load(json_file)

# for item in data:
#     print("incident id:", item["incident_id"])

# for item in data:
#     print(item["incident_id"], item["location"]["city"])

# for item in data:
#     if item["severity"] == "High":
#         print(item["incident_id"])

# for item in data:
#     if item["category"] == "Safety":
#         print(item["incident_id"])

# for item in data:
#     if item.get("actions") is None:
#         print("No actions recorded")
#     else:
#         print(item.get("actions"))

# counts = Counter(item.get("severity", "unknown") for item in data)
# print(counts)

# for item in data:
#     item["status"] = "Open"
#
# with open('semi_structured_data.json', 'w') as outfile:
#     json.dump(data, outfile)
#
# print("File updated successfully")


# df = pd.json_normalize(data)
#
# print(df[["incident_id", "severity", "category", "location.city", "location.site"]])
