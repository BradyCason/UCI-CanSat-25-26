import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# ==========================================
# CONFIGURATION
# ==========================================

CSV_FILE = "Ground-Station/flight-csv/Flight_1083.csv"

# Columns to use
X_COLUMN = "GPS_LATITUDE_ADJUSTED"
Y_COLUMN = "GPS_LONGITUDE_ADJUSTED"
Z_COLUMN = "GPS_ALTITUDE_ADJUSTED"

# Axis labels
X_LABEL = "Latitude"
Y_LABEL = "Longitude"
Z_LABEL = "Altitude"

# Plot title
TITLE = "3D GPS Coordinates"

# Plot type:
# "line" or "scatter"
PLOT_TYPE = "line"

# Color
COLOR = "tab:blue"

# Marker size (scatter only)
MARKER_SIZE = 10

# ==========================================
# LOAD DATA
# ==========================================

df = pd.read_csv(CSV_FILE)

x = df[X_COLUMN]
y = df[Y_COLUMN]
z = df[Z_COLUMN]

# ==========================================
# CREATE FIGURE
# ==========================================

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

# ==========================================
# PLOT
# ==========================================

if PLOT_TYPE.lower() == "line":
    ax.plot(
        x,
        y,
        z,
        color=COLOR,
        linewidth=2
    )

else:
    ax.scatter(
        x,
        y,
        z,
        color=COLOR,
        s=MARKER_SIZE
    )

# ==========================================
# LABELS
# ==========================================

ax.set_xlabel(X_LABEL)
ax.set_ylabel(Y_LABEL)
ax.set_zlabel(Z_LABEL)

ax.set_title(TITLE)

plt.tight_layout()
plt.show()