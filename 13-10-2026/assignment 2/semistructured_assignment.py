import json
import pandas as pd

with open('smart_home_devices.json', 'r') as f:
    data = json.load(f)

for device in data:
    print(device.get('device_id'), device.get('device_type'), device.get('room'))

for device in data:
    if device.get('status') == 'Active':
        print(device)

for device in data:
    if device.get('metrics', {}).get('battery', 100) < 60:
        print(device)

for device in data:
    if 'temperature' in device.get('metrics', {}):
        print(device.get('metrics').get('temperature'))

for device in data:
    if 'alerts' in device:
        print(device)

df_json = pd.json_normalize(data)
print(df_json['device_type'].value_counts())

for device in data:
    battery = device.get('metrics', {}).get('battery', 0)
    if battery >= 70:
        device['health'] = 'Good'
    elif 50 <= battery <= 69:
        device['health'] = 'Moderate'
    else:
        device['health'] = 'Low'

with open('device_health_report.json', 'w') as f:
    json.dump(data, f, indent=4)

df_norm = pd.json_normalize(data)
print(df_norm[['device_id', 'device_type', 'room', 'status', 'metrics.battery', 'health']])

for device in data:
    if device.get('status') == 'Active' and device.get('metrics', {}).get('battery', 100) < 70:
        print(device)