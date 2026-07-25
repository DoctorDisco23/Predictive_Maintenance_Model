import pandas as pd

# 1. These are the "Tags" that were missing
column_names = [
    'Lever_Position', 'Ship_Speed', 'GT_Torque', 'GT_RPM', 'GG_RPM', 
    'Starboard_Torque', 'Port_Torque', 'GT_Turbine_Exit_Temp', 
    'Comp_Inlet_Temp', 'Comp_Outlet_Temp', 'Turbine_Exit_Pressure', 
    'Comp_Inlet_Pressure', 'Comp_Outlet_Pressure', 'Exhaust_Pressure', 
    'Turbine_Control', 'Fuel_Flow', 'Compressor_Health', 'Turbine_Health'
]

# 2. This line is the "Magic". 
# sep=r'\s+' tells Python: "Every time you see a bunch of spaces, start a new column"
df = pd.read_csv('navalplantmaintenance.csv', sep=r'\s+', header=None, names=column_names)

# 3. We save it as a NEW file that Excel will understand (using commas)
df.to_csv('NAVY_DATA_CLEAN.csv', index=False)

print("--- CLEANING COMPLETE ---")
print("I have created a new file: NAVY_DATA_CLEAN.csv")
print("You can now open this new file in Excel and it will have 18 separate columns!")