import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('renewable_energy.csv')

print(df[df['Energy_Type'].isin(['Solar', 'Wind'])])

df['Efficiency_Percent'] = (df['Actual Output MW'] / df['Capacity_MW']) * 100

print(df[df['Efficiency_Percent'] > 85])

print(df.groupby('Energy_Type')['Efficiency_Percent'].mean())

print(df.groupby('Energy_Type')['Maintenance_Cost'].sum())

print(df.loc[df['Actual_Output_MW'].idxmax()])

df['Cost_Per_MW'] = df['Maintenance_Cost'] / df['Actual_Output_MW']

print(df.sort_values(by='Cost_Per_MW', ascending=True))

print(df[(df['Efficiency_Percent'] > 80) & (df['Maintenance_Cost'] < 70000)])

plt.figure(figsize=(10, 5))
plt.bar(df['Plant Name'], df['Efficiency_Percent'], color='skyblue')
plt.xlabel('Plant Name')
plt.ylabel('Efficiency Percent')
plt.title('Plant Name vs Efficiency Percent')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()