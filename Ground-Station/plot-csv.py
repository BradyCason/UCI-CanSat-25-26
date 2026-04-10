import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from pathlib import Path

# Configuration
# CSV_FILE = "Flight_1083_telemetry_2026-04-10_09-03-54.csv"  # Update with your CSV filename
CSV_FILE = "Flight_1083_telemetry_2026-04-04_11-15-24.csv"
OUTPUT_DIR = "plots"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read the CSV file
try:
    df = pd.read_csv(CSV_FILE)
    print(f"Successfully loaded CSV file with {len(df)} rows")
    print(f"Columns: {df.columns.tolist()}")
    
    # The second column (MISSION_TIME in header) actually contains TEAM_ID values
    # The third column (PACKET_COUNT in header) actually contains MISSION_TIME values
    # So we need to swap them
    if 'MISSION_TIME' in df.columns and 'PACKET_COUNT' in df.columns:
        # Check if MISSION_TIME contains time format (HH:MM:SS) in third column
        actual_mission_time = df.columns[2]  # This should be PACKET_COUNT but contains times
        if df.iloc[0][2].__class__.__name__ == 'str' and ':' in str(df.iloc[0][2]):
            # Swap the data
            temp = df['MISSION_TIME'].copy()
            df['MISSION_TIME'] = df['PACKET_COUNT']
            df['PACKET_COUNT'] = temp
            print("Note: Swapped MISSION_TIME and PACKET_COUNT columns (they were misaligned)")
    
    # Convert numeric columns to float, replacing any non-numeric values with NaN
    numeric_columns = ['ALTITUDE', 'ACCEL_R', 'ACCEL_P', 'ACCEL_Y', 'GYRO_R', 'GYRO_P', 'GYRO_Y', 
                       'CURRENT', 'VOLTAGE', 'TEMPERATURE', 'PRESSURE', 'PACKET_COUNT']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Keep MISSION_TIME as string for x-axis (more reliable for plotting)
    df['MISSION_TIME'] = df['MISSION_TIME'].astype(str)
    
    # Convert MISSION_TIME to datetime for better x-axis formatting
    df['MISSION_TIME_DT'] = pd.to_datetime(df['MISSION_TIME'], format='%H:%M:%S', errors='coerce')
    
    # Check for data before and after cleaning
    print(f"Rows before cleaning: {len(df)}")
    print(f"Sample data:\n{df.head()}")
    
    # Drop rows with NaN values in numeric columns only
    df = df.dropna(subset=['ALTITUDE'])
    print(f"After cleaning: {len(df)} rows with valid data")
    print(f"Data types:\n{df.dtypes}")
    print(f"\nData summary:\n{df[['MISSION_TIME', 'ALTITUDE', 'ACCEL_R', 'VOLTAGE', 'CURRENT']].head(10)}")
    
except FileNotFoundError:
    print(f"Error: Could not find {CSV_FILE}")
    exit(1)

# Create figure with multiple subplots
fig, axes = plt.subplots(3, 2, figsize=(15, 12))
fig.suptitle(f'CanSat Telemetry Data - {CSV_FILE}', fontsize=16, fontweight='bold')

# 1. Altitude vs Mission Time
axes[0, 0].plot(df['MISSION_TIME_DT'], df['ALTITUDE'], marker='o', linestyle='-', linewidth=1, markersize=3, color='blue')
axes[0, 0].set_title('Altitude vs Mission Time')
axes[0, 0].set_xlabel('Mission Time')
axes[0, 0].set_ylabel('Altitude (m)')
axes[0, 0].xaxis.set_major_locator(mdates.AutoDateLocator())
axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
axes[0, 0].tick_params(axis='x', rotation=45)
axes[0, 0].grid(True, alpha=0.3)

# 2. Acceleration (X, Y, Z)
axes[0, 1].plot(df['MISSION_TIME_DT'], df['ACCEL_R'], label='ACCEL_R', marker='o', linestyle='-', linewidth=1, markersize=2)
axes[0, 1].plot(df['MISSION_TIME_DT'], df['ACCEL_P'], label='ACCEL_P', marker='s', linestyle='-', linewidth=1, markersize=2)
axes[0, 1].plot(df['MISSION_TIME_DT'], df['ACCEL_Y'], label='ACCEL_Y', marker='^', linestyle='-', linewidth=1, markersize=2)
axes[0, 1].set_title('Acceleration (°/s²)')
axes[0, 1].set_xlabel('Mission Time')
axes[0, 1].set_ylabel('Acceleration (°/s²)')
axes[0, 1].xaxis.set_major_locator(mdates.AutoDateLocator())
axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
axes[0, 1].tick_params(axis='x', rotation=45)
axes[0, 1].legend(loc='best')
axes[0, 1].grid(True, alpha=0.3)

# 3. Rotation Rate (X, Y, Z)
axes[1, 0].plot(df['MISSION_TIME_DT'], df['GYRO_R'], label='GYRO_R', marker='o', linestyle='-', linewidth=1, markersize=2)
axes[1, 0].plot(df['MISSION_TIME_DT'], df['GYRO_P'], label='GYRO_P', marker='s', linestyle='-', linewidth=1, markersize=2)
axes[1, 0].plot(df['MISSION_TIME_DT'], df['GYRO_Y'], label='GYRO_Y', marker='^', linestyle='-', linewidth=1, markersize=2)
axes[1, 0].set_title('Rotation Rate (°/s)')
axes[1, 0].set_xlabel('Mission Time')
axes[1, 0].set_ylabel('Rotation Rate (°/s)')
axes[1, 0].xaxis.set_major_locator(mdates.AutoDateLocator())
axes[1, 0].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
axes[1, 0].tick_params(axis='x', rotation=45)
axes[1, 0].legend(loc='best')
axes[1, 0].grid(True, alpha=0.3)

# 4. Current and Voltage vs Mission Time (dual y-axis)
ax_current = axes[1, 1]
ax_voltage = ax_current.twinx()

line1 = ax_current.plot(df['MISSION_TIME_DT'], df['CURRENT'], marker='o', linestyle='-', linewidth=2, markersize=3, color='green', label='Current')
line2 = ax_voltage.plot(df['MISSION_TIME_DT'], df['VOLTAGE'], marker='s', linestyle='-', linewidth=2, markersize=3, color='red', label='Voltage')

ax_current.set_title('Current and Voltage vs Mission Time')
ax_current.set_xlabel('Mission Time')
ax_current.set_ylabel('Current (A)', color='green')
ax_voltage.set_ylabel('Voltage (V)', color='red')
ax_current.tick_params(axis='y', labelcolor='green')
ax_voltage.tick_params(axis='y', labelcolor='red')
ax_current.xaxis.set_major_locator(mdates.AutoDateLocator())
ax_current.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
ax_current.tick_params(axis='x', rotation=45)
ax_current.grid(True, alpha=0.3)

# Combine legends
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax_current.legend(lines, labels, loc='best')

# 5. Temperature and Pressure (moved to position [2, 0])
axes[2, 0].clear()
ax_temp = axes[2, 0]
ax_press = ax_temp.twinx()

line1 = ax_temp.plot(df['MISSION_TIME_DT'], df['TEMPERATURE'], marker='o', linestyle='-', linewidth=1, markersize=2, color='orange', label='Temperature')
line2 = ax_press.plot(df['MISSION_TIME_DT'], df['PRESSURE'], marker='s', linestyle='-', linewidth=1, markersize=2, color='purple', label='Pressure')

ax_temp.set_title('Temperature and Pressure vs Mission Time')
ax_temp.set_xlabel('Mission Time')
ax_temp.set_ylabel('Temperature (°C)', color='orange')
ax_press.set_ylabel('Pressure (hPa)', color='purple')
ax_temp.tick_params(axis='y', labelcolor='orange')
ax_temp.xaxis.set_major_locator(mdates.AutoDateLocator())
ax_temp.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
ax_temp.tick_params(axis='x', rotation=45)
ax_press.tick_params(axis='y', labelcolor='purple')
ax_temp.grid(True, alpha=0.3)

# Combine legends
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax_temp.legend(lines, labels, loc='best')


# # 6. Packet Count vs Mission Time
# axes[2, 1].plot(df['MISSION_TIME_DT'], df['PACKET_COUNT'], marker='o', linestyle='-', linewidth=1, markersize=3, color='darkblue')
# axes[2, 1].set_title('Packet Count vs Mission Time')
# axes[2, 1].set_xlabel('Mission Time')
# axes[2, 1].set_ylabel('Packet Count')
# axes[2, 1].xaxis.set_major_locator(mdates.AutoDateLocator())
# axes[2, 1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
# axes[2, 1].tick_params(axis='x', rotation=45)
# axes[2, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'telemetry_overview.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'telemetry_overview.png')}")

# Create individual high-detail plots
fig2, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['MISSION_TIME_DT'], df['ALTITUDE'], marker='o', linestyle='-', linewidth=2, markersize=4, color='blue')
ax.set_title('Altitude Profile (Detailed)', fontsize=14, fontweight='bold')
ax.set_xlabel('Mission Time', fontsize=12)
ax.set_ylabel('Altitude (m)', fontsize=12)
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
ax.tick_params(axis='x', rotation=45)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'altitude_detailed.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'altitude_detailed.png')}")

# Create acceleration detailed plot
fig3, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['MISSION_TIME_DT'], df['ACCEL_R'], label='ACCEL_R (Roll)', linewidth=2, marker='o', markersize=3)
ax.plot(df['MISSION_TIME_DT'], df['ACCEL_P'], label='ACCEL_P (Pitch)', linewidth=2, marker='s', markersize=3)
ax.plot(df['MISSION_TIME_DT'], df['ACCEL_Y'], label='ACCEL_Y (Yaw)', linewidth=2, marker='^', markersize=3)
ax.set_title('Acceleration Data (Detailed)', fontsize=14, fontweight='bold')
ax.set_xlabel('Mission Time', fontsize=12)
ax.set_ylabel('Acceleration (°/s²)', fontsize=12)
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
ax.tick_params(axis='x', rotation=45)
ax.legend(loc='best', fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'acceleration_detailed.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'acceleration_detailed.png')}")

# Create rotation rate detailed plot
fig4, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['MISSION_TIME_DT'], df['GYRO_R'], label='GYRO_R (Roll)', linewidth=2, marker='o', markersize=3)
ax.plot(df['MISSION_TIME_DT'], df['GYRO_P'], label='GYRO_P (Pitch)', linewidth=2, marker='s', markersize=3)
ax.plot(df['MISSION_TIME_DT'], df['GYRO_Y'], label='GYRO_Y (Yaw)', linewidth=2, marker='^', markersize=3)
ax.set_title('Rotation Rate Data (Detailed)', fontsize=14, fontweight='bold')
ax.set_xlabel('Mission Time', fontsize=12)
ax.set_ylabel('Rotation Rate (°/s)', fontsize=12)
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
ax.tick_params(axis='x', rotation=45)
ax.legend(loc='best', fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'rotation_rate_detailed.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'rotation_rate_detailed.png')}")

# Create power profile plot
fig5, ax = plt.subplots(figsize=(12, 6))
ax_current = ax
ax_voltage = ax.twinx()

line1 = ax_current.plot(df['MISSION_TIME_DT'], df['CURRENT'], marker='o', linestyle='-', linewidth=2, markersize=3, color='green', label='Current (A)')
line2 = ax_voltage.plot(df['MISSION_TIME_DT'], df['VOLTAGE'], marker='s', linestyle='-', linewidth=2, markersize=3, color='red', label='Voltage (V)')

ax_current.set_title('Power System Data (Voltage & Current)', fontsize=14, fontweight='bold')
ax_current.set_xlabel('Mission Time', fontsize=12)
ax_current.set_ylabel('Current (A)', fontsize=12, color='green')
ax_voltage.set_ylabel('Voltage (V)', fontsize=12, color='red')
ax_current.tick_params(axis='y', labelcolor='green')
ax_voltage.tick_params(axis='y', labelcolor='red')
ax_current.xaxis.set_major_locator(mdates.AutoDateLocator())
ax_current.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
ax_current.tick_params(axis='x', rotation=45)
ax_current.grid(True, alpha=0.3)

# Combine legends
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax_current.legend(lines, labels, loc='best', fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'power_profile.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'power_profile.png')}")

# Create temperature and pressure detailed plot
fig6, ax = plt.subplots(figsize=(12, 6))
ax_temp = ax
ax_press = ax_temp.twinx()

line1 = ax_temp.plot(df['MISSION_TIME_DT'], df['TEMPERATURE'], marker='o', linestyle='-', linewidth=2, markersize=3, color='orange', label='Temperature (°C)')
line2 = ax_press.plot(df['MISSION_TIME_DT'], df['PRESSURE'], marker='s', linestyle='-', linewidth=2, markersize=3, color='purple', label='Pressure (hPa)')

ax_temp.set_title('Temperature and Pressure Data (Detailed)', fontsize=14, fontweight='bold')
ax_temp.set_xlabel('Mission Time', fontsize=12)
ax_temp.set_ylabel('Temperature (°C)', fontsize=12, color='orange')
ax_press.set_ylabel('Pressure (hPa)', fontsize=12, color='purple')
ax_temp.tick_params(axis='y', labelcolor='orange')
ax_temp.xaxis.set_major_locator(mdates.AutoDateLocator())
ax_temp.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
ax_temp.tick_params(axis='x', rotation=45)
ax_press.tick_params(axis='y', labelcolor='purple')
ax_temp.grid(True, alpha=0.3)

# Combine legends
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax_temp.legend(lines, labels, loc='best', fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'temperature_pressure_detailed.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'temperature_pressure_detailed.png')}")

# Print statistics
print("\n=== Telemetry Statistics ===")
print(f"Altitude: {df['ALTITUDE'].min():.2f}m to {df['ALTITUDE'].max():.2f}m")
print(f"Temperature: {df['TEMPERATURE'].min():.2f}°C to {df['TEMPERATURE'].max():.2f}°C")
print(f"Voltage: {df['VOLTAGE'].min():.2f}V to {df['VOLTAGE'].max():.2f}V")
print(f"Current: {df['CURRENT'].min():.2f}A to {df['CURRENT'].max():.2f}A")

plt.show()