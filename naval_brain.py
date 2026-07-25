import pandas as pd

# 1. Define the Column Tags (The 'Secret Map')
column_names = [
    'Lever_Pos', 'Speed', 'Torque', 'GT_RPM', 'GG_RPM', 
    'STBD_Torque', 'Port_Torque', 'GT_Turbine_Temp', 
    'C_In_Temp', 'C_Out_Temp', 'T_Exit_Press', 
    'C_In_Press', 'C_Out_Press', 'Exh_Press', 
    'Control_Val', 'Fuel_Flow', 'Compressor_Health', 'Turbine_Health'
]

# 2. Load and Clean the data
print("⌛ Loading Naval Data...")
try:
    # sep=r'\s+' fixes the 'one column' problem you saw in Excel
    df = pd.read_csv('navalplantmaintenance.csv', sep=r'\s+', header=None, names=column_names)
    print("✅ Data Loaded Successfully!")
except FileNotFoundError:
    print("❌ ERROR: I can't find 'navalplantmaintenance.csv' in this folder!")
    exit()

# 3. The RUL Math (The logic for your 79.7 Hours)
# We look at 'Compressor_Health' (starts at 1.0, fails at 0.95)
start_h = df['Compressor_Health'].iloc[0]
current_h = df['Compressor_Health'].iloc[-1]

# How much did it drop across the whole file?
total_drop = start_h - current_h
# How many 'steps' or rows are in this file?
total_rows = len(df)

# If there is a drop, calculate how much life is left
if total_drop > 0:
    drop_per_row = total_drop / total_rows
    # How far away are we from the 0.95 'Death Point'?
    gap_to_failure = current_h - 0.95
    rul_estimate = gap_to_failure / drop_per_row
else:
    rul_estimate = 999.9 # Engine is perfectly new

# 4. Display the Results (The CLI Dashboard)
print("\n" + "="*30)
print("   NAVAL PROPULSION BRAIN")
print("="*30)
print(f"CURRENT TEMP:    {df['GT_Turbine_Temp'].iloc[-1]} C")
print(f"HEALTH INDEX:    {current_h * 100:.2f}%")
print(f"DEGRADATION:     -{total_drop:.4f} units")
print("-" * 30)
print(f"ESTIMATED RUL:   {rul_estimate:.1f} HOURS")
print("="*30)