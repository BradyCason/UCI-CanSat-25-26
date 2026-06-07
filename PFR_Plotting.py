import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from mpl_toolkits.mplot3d import Axes3D

# ============================================================
# USER SETTINGS
# ============================================================

CSV_FILE = "Ground-Station/flight-csv/Flight_1083.csv"

# Column names from CSV
X_COLUMN = "MISSION_TIME"
Y_COLUMN = "PRESSURE"

# Set to None for a 2D plot
Z_COLUMN = None

# Optional color column
COLOR_COLUMN = None

TITLE = "Pressure"
X_LABEL = "Mission Time"
Y_LABEL = "Pressure (KPa)"
Z_LABEL = "Velocity"

PLOT_TYPE = "line"  # "line" or "scatter"

MAX_POINTS = 5000

SAVE_PLOT = False
OUTPUT_FILE = "plot.png"

FIGURE_SIZE = (12, 7)

# ============================================================
# LOAD CSV
# ============================================================

df = pd.read_csv(CSV_FILE)

# ============================================================
# CONVERT HH:MM:SS TO SECONDS
# ============================================================

time_delta = pd.to_timedelta(df[X_COLUMN])

df["_mission_seconds"] = time_delta.dt.total_seconds()

# ============================================================
# DOWNSAMPLE IF DATASET IS HUGE
# ============================================================

if len(df) > MAX_POINTS:
    step = max(1, len(df) // MAX_POINTS)
    df = df.iloc[::step].reset_index(drop=True)

# ============================================================
# TIME FORMATTER
# ============================================================

def format_time(seconds, pos):
    seconds = int(seconds)

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# ============================================================
# STYLE
# ============================================================

plt.style.use("ggplot")

# ============================================================
# 2D PLOT
# ============================================================

if Z_COLUMN is None:

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    if PLOT_TYPE.lower() == "line":

        ax.plot(
            df["_mission_seconds"],
            df[Y_COLUMN],
            linewidth=2
        )

    elif PLOT_TYPE.lower() == "scatter":

        if COLOR_COLUMN:

            scatter = ax.scatter(
                df["_mission_seconds"],
                df[Y_COLUMN],
                c=df[COLOR_COLUMN],
                s=10
            )

            cbar = plt.colorbar(scatter)
            cbar.set_label(COLOR_COLUMN)

        else:

            ax.scatter(
                df["_mission_seconds"],
                df[Y_COLUMN],
                s=10
            )

    ax.xaxis.set_major_formatter(
        FuncFormatter(format_time)
    )

    # Automatically choose ~8 labels
    ax.xaxis.set_major_locator(
        MaxNLocator(nbins=8)
    )

    ax.set_title(TITLE, fontsize=16)
    ax.set_xlabel(X_LABEL)
    ax.set_ylabel(Y_LABEL)

    ax.grid(True, alpha=0.3)

    plt.xticks(rotation=30)

# ============================================================
# 3D PLOT
# ============================================================

else:

    fig = plt.figure(figsize=FIGURE_SIZE)
    ax = fig.add_subplot(111, projection='3d')

    if COLOR_COLUMN:

        scatter = ax.scatter(
            df["_mission_seconds"],
            df[Y_COLUMN],
            df[Z_COLUMN],
            c=df[COLOR_COLUMN],
            s=10
        )

        cbar = plt.colorbar(scatter)
        cbar.set_label(COLOR_COLUMN)

    else:

        if PLOT_TYPE.lower() == "line":

            ax.plot(
                df["_mission_seconds"],
                df[Y_COLUMN],
                df[Z_COLUMN],
                linewidth=2
            )

        else:

            ax.scatter(
                df["_mission_seconds"],
                df[Y_COLUMN],
                df[Z_COLUMN],
                s=10
            )

    ax.xaxis.set_major_formatter(
        FuncFormatter(format_time)
    )

    ax.set_title(TITLE, fontsize=16)
    ax.set_xlabel(X_LABEL)
    ax.set_ylabel(Y_LABEL)
    ax.set_zlabel(Z_LABEL)

# ============================================================
# FINISH
# ============================================================

plt.tight_layout()

if SAVE_PLOT:
    plt.savefig(
        OUTPUT_FILE,
        dpi=300,
        bbox_inches="tight"
    )
    print(f"Saved plot to {OUTPUT_FILE}")

plt.show()