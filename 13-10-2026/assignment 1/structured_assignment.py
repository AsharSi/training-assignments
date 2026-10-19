import pandas as pd

df = pd.read_csv('structured_data.csv')
#
# print(df[['Shipment_ID', 'Origin', 'Destination', 'C']])
#
# print(df[df['Mode'] == 'Road'])
#
# print(df[df['Weight_Kg'] > 150])

# df['Cost_Per_Km'] = df['C'] / df['Distance_Km']
# print(df['Cost_Per_Km'])

# print(df['C'].mean())
# print(df['C'].max())
# print(df['C'].min())

# print(df.groupby('Mode')['C'].sum())

# print(df.groupby('Mode')['Weight_Kg'].mean())

# print(df.sort_values(by=['C'], ascending=False))

# print(df[(df['Delivery_Days'] <= 1) & (df['C'] < 5000)])
