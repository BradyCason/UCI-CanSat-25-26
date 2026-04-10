import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Configuration
CSV_FILE = "Flight_1083_telemetry_2026-04-04_11-15-24.csv"  # Update with your CSV filename
OUTPUT_DIR = "plots"

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Read the CSV file
try:
    df = pd.read_csv(CSV_FILE)
    print(f"Successfully loaded CSV file with {len(df)} rows")
    print(f"Columns: {df.columns.tolist()}")
except FileNotFoundError:
    print(f"Error: Could not find {CSV_FILE}")
    exit(1)

# Create figure with multiple subplots
fig, axes = plt.subplots(3, 2, figsize=(15, 12))
fig.suptitle('CanSat Telemetry Data', fontsize=16, fontweight='bold')

# 1. Altitude vs Packet Count
axes[0, 0].plot(df['PACKET_COUNT'], df['ALTITUDE'], marker='o', linestyle='-', linewidth=1, markersize=3, color='blue')
axes[0, 0].set_title('Altitude vs Packet Count')
axes[0, 0].set_xlabel('Packet Count')
axes[0, 0].set_ylabel('Altitude (m)')
axes[0, 0].grid(True, alpha=0.3)

# 2. Acceleration (X, Y, Z)
axes[0, 1].plot(df['PACKET_COUNT'], df['ACCEL_R'], label='ACCEL_R', marker='o', linestyle='-', linewidth=1, markersize=2)
axes[0, 1].plot(df['PACKET_COUNT'], df['ACCEL_P'], label='ACCEL_P', marker='s', linestyle='-', linewidth=1, markersize=2)
axes[0, 1].plot(df['PACKET_COUNT'], df['ACCEL_Y'], label='ACCEL_Y', marker='^', linestyle='-', linewidth=1, markersize=2)
axes[0, 1].set_title('Acceleration (°/s²)')
axes[0, 1].set_xlabel('Packet Count')
axes[0, 1].set_ylabel('Acceleration (°/s²)')
axes[0, 1].legend(loc='best')
axes[0, 1].grid(True, alpha=0.3)

# 3. Rotation Rate (X, Y, Z)
axes[1, 0].plot(df['PACKET_COUNT'], df['GYRO_R'], label='GYRO_R', marker='o', linestyle='-', linewidth=1, markersize=2)
axes[1, 0].plot(df['PACKET_COUNT'], df['GYRO_P'], label='GYRO_P', marker='s', linestyle='-', linewidth=1, markersize=2)
axes[1, 0].plot(df['PACKET_COUNT'], df['GYRO_Y'], label='GYRO_Y', marker='^', linestyle='-', linewidth=1, markersize=2)
axes[1, 0].set_title('Rotation Rate (°/s)')
axes[1, 0].set_xlabel('Packet Count')
axes[1, 0].set_ylabel('Rotation Rate (°/s)')
axes[1, 0].legend(loc='best')
axes[1, 0].grid(True, alpha=0.3)

# 4. Current vs Packet Count
axes[1, 1].plot(df['PACKET_COUNT'], df['CURRENT'], marker='o', linestyle='-', linewidth=1, markersize=3, color='green')
axes[1, 1].set_title('Current vs Packet Count')
axes[1, 1].set_xlabel('Packet Count')
axes[1, 1].set_ylabel('Current (A)')
axes[1, 1].grid(True, alpha=0.3)

# 5. Voltage vs Packet Count
axes[2, 0].plot(df['PACKET_COUNT'], df['VOLTAGE'], marker='o', linestyle='-', linewidth=1, markersize=3, color='red')
axes[2, 0].set_title('Voltage vs Packet Count')
axes[2, 0].set_xlabel('Packet Count')
axes[2, 0].set_ylabel('Voltage (V)')
axes[2, 0].grid(True, alpha=0.3)

# 6. Temperature and Pressure
ax_temp = axes[2, 1]
ax_press = ax_temp.twinx()

line1 = ax_temp.plot(df['PACKET_COUNT'], df['TEMPERATURE'], marker='o', linestyle='-', linewidth=1, markersize=2, color='orange', label='Temperature')
line2 = ax_press.plot(df['PACKET_COUNT'], df['PRESSURE'], marker='s', linestyle='-', linewidth=1, markersize=2, color='purple', label='Pressure')

ax_temp.set_title('Temperature and Pressure vs Packet Count')
ax_temp.set_xlabel('Packet Count')
ax_temp.set_ylabel('Temperature (°C)', color='orange')
ax_press.set_ylabel('Pressure (hPa)', color='purple')
ax_temp.tick_params(axis='y', labelcolor='orange')
ax_press.tick_params(axis='y', labelcolor='purple')
ax_temp.grid(True, alpha=0.3)

# Combine legends
lines = line1 + line2
labels = [l.get_label() for l in lines]
ax_temp.legend(lines, labels, loc='best')

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'telemetry_overview.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'telemetry_overview.png')}")

# Create individual high-detail plots
fig2, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['PACKET_COUNT'], df['ALTITUDE'], marker='o', linestyle='-', linewidth=2, markersize=4, color='blue')
ax.set_title('Altitude Profile (Detailed)', fontsize=14, fontweight='bold')
ax.set_xlabel('Packet Count', fontsize=12)
ax.set_ylabel('Altitude (m)', fontsize=12)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'altitude_detailed.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'altitude_detailed.png')}")

# Create acceleration detailed plot
fig3, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['PACKET_COUNT'], df['ACCEL_R'], label='ACCEL_R (Roll)', linewidth=2, marker='o', markersize=3)
ax.plot(df['PACKET_COUNT'], df['ACCEL_P'], label='ACCEL_P (Pitch)', linewidth=2, marker='s', markersize=3)
ax.plot(df['PACKET_COUNT'], df['ACCEL_Y'], label='ACCEL_Y (Yaw)', linewidth=2, marker='^', markersize=3)
ax.set_title('Acceleration Data (Detailed)', fontsize=14, fontweight='bold')
ax.set_xlabel('Packet Count', fontsize=12)
ax.set_ylabel('Acceleration (°/s²)', fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'acceleration_detailed.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'acceleration_detailed.png')}")

# Create rotation rate detailed plot
fig4, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['PACKET_COUNT'], df['GYRO_R'], label='GYRO_R (Roll)', linewidth=2, marker='o', markersize=3)
ax.plot(df['PACKET_COUNT'], df['GYRO_P'], label='GYRO_P (Pitch)', linewidth=2, marker='s', markersize=3)
ax.plot(df['PACKET_COUNT'], df['GYRO_Y'], label='GYRO_Y (Yaw)', linewidth=2, marker='^', markersize=3)
ax.set_title('Rotation Rate Data (Detailed)', fontsize=14, fontweight='bold')
ax.set_xlabel('Packet Count', fontsize=12)
ax.set_ylabel('Rotation Rate (°/s)', fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'rotation_rate_detailed.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'rotation_rate_detailed.png')}")

# Create power profile plot
fig5, ax = plt.subplots(figsize=(12, 6))
ax.plot(df['PACKET_COUNT'], df['VOLTAGE'], label='Voltage (V)', linewidth=2, marker='o', markersize=3, color='red')
ax.plot(df['PACKET_COUNT'], df['CURRENT'], label='Current (A)', linewidth=2, marker='s', markersize=3, color='green')
ax.set_title('Power System Data (Voltage & Current)', fontsize=14, fontweight='bold')
ax.set_xlabel('Packet Count', fontsize=12)
ax.set_ylabel('Value', fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'power_profile.png'), dpi=150, bbox_inches='tight')
print(f"Saved: {os.path.join(OUTPUT_DIR, 'power_profile.png')}")

# Print statistics
print("\n=== Telemetry Statistics ===")
print(f"Altitude: {df['ALTITUDE'].min():.2f}m to {df['ALTITUDE'].max():.2f}m")
print(f"Temperature: {df['TEMPERATURE'].min():.2f}°C to {df['TEMPERATURE'].max():.2f}°C")
print(f"Voltage: {df['VOLTAGE'].min():.2f}V to {df['VOLTAGE'].max():.2f}V")
print(f"Current: {df['CURRENT'].min():.2f}A to {df['CURRENT'].max():.2f}A")

plt.show()