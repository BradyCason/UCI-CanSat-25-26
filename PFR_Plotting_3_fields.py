import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# =====================================================
# CONFIGURATION
# =====================================================

CSV_FILE = "Ground-Station/flight-csv/Flight_1083.csv"

# Mission time column (HH:MM:SS)
TIME_COLUMN = "MISSION_TIME"

# Plot type: "line" or "scatter"
PLOT_TYPE = "line"

# Plot title
TITLE = "Gyro"

# X-axis label
X_AXIS_LABEL = "Mission Time"

# Maximum number of x-axis labels displayed
MAX_X_TICKS = 12

# =====================================================
# DATA SERIES 1
# =====================================================

Y1_COLUMN = "GYRO_R"
Y1_LABEL = "Gyro Roll"
Y1_COLOR = "tab:blue"

# =====================================================
# DATA SERIES 2
# =====================================================

Y2_COLUMN = "GYRO_P"
Y2_LABEL = "Gyro Pitch"
Y2_COLOR = "tab:red"

# =====================================================
# DATA SERIES 3
# =====================================================

Y3_COLUMN = "GYRO_Y"
Y3_LABEL = "Gyro Yaw"
Y3_COLOR = "tab:green"

# =====================================================
# AXIS OPTIONS
# =====================================================

# True = all data on one Y axis
# False = separate Y axes for each series
USE_SHARED_Y_AXIS = True

# Shared axis label (only used when USE_SHARED_Y_AXIS=True)
SHARED_Y_LABEL = "Gyro (°/s)"

# =====================================================
# LOAD DATA
# =====================================================

df = pd.read_csv(CSV_FILE)

# Convert HH:MM:SS to seconds
df["_mission_seconds"] = pd.to_timedelta(
    df[TIME_COLUMN]
).dt.total_seconds()

# =====================================================
# FIGURE SETUP
# =====================================================

fig, ax1 = plt.subplots(figsize=(14, 7))

# =====================================================
# SHARED Y AXIS MODE
# =====================================================

if USE_SHARED_Y_AXIS:

    if Y1_COLUMN:
        if PLOT_TYPE == "line":
            ax1.plot(
                df["_mission_seconds"],
                df[Y1_COLUMN],
                label=Y1_LABEL,
                color=Y1_COLOR,
                linewidth=2.5
            )
        else:
            ax1.scatter(
                df["_mission_seconds"],
                df[Y1_COLUMN],
                label=Y1_LABEL,
                color=Y1_COLOR
            )

    if Y2_COLUMN:
        if PLOT_TYPE == "line":
            ax1.plot(
                df["_mission_seconds"],
                df[Y2_COLUMN],
                label=Y2_LABEL,
                color=Y2_COLOR,
                linewidth=2.5
            )
        else:
            ax1.scatter(
                df["_mission_seconds"],
                df[Y2_COLUMN],
                label=Y2_LABEL,
                color=Y2_COLOR
            )

    if Y3_COLUMN:
        if PLOT_TYPE == "line":
            ax1.plot(
                df["_mission_seconds"],
                df[Y3_COLUMN],
                label=Y3_LABEL,
                color=Y3_COLOR,
                linewidth=2.5
            )
        else:
            ax1.scatter(
                df["_mission_seconds"],
                df[Y3_COLUMN],
                label=Y3_LABEL,
                color=Y3_COLOR
            )

    ax1.set_ylabel(SHARED_Y_LABEL)

    ax1.legend()

# =====================================================
# SEPARATE Y AXES MODE
# =====================================================

else:

    ax2 = ax1.twinx()
    ax3 = ax1.twinx()

    # Move third axis outward
    ax3.spines["right"].set_position(("outward", 70))

    # ----- Series 1 -----
    if PLOT_TYPE == "line":
        ax1.plot(
            df["_mission_seconds"],
            df[Y1_COLUMN],
            color=Y1_COLOR,
            label=Y1_LABEL,
            linewidth=2.5
        )
    else:
        ax1.scatter(
            df["_mission_seconds"],
            df[Y1_COLUMN],
            color=Y1_COLOR,
            label=Y1_LABEL
        )

    ax1.set_ylabel(Y1_LABEL, color=Y1_COLOR)
    ax1.tick_params(axis="y", labelcolor=Y1_COLOR)

    # ----- Series 2 -----
    if PLOT_TYPE == "line":
        ax2.plot(
            df["_mission_seconds"],
            df[Y2_COLUMN],
            color=Y2_COLOR,
            label=Y2_LABEL,
            linewidth=2.5
        )
    else:
        ax2.scatter(
            df["_mission_seconds"],
            df[Y2_COLUMN],
            color=Y2_COLOR,
            label=Y2_LABEL
        )

    ax2.set_ylabel(Y2_LABEL, color=Y2_COLOR)
    ax2.tick_params(axis="y", labelcolor=Y2_COLOR)

    # ----- Series 3 -----
    if PLOT_TYPE == "line":
        ax3.plot(
            df["_mission_seconds"],
            df[Y3_COLUMN],
            color=Y3_COLOR,
            label=Y3_LABEL,
            linewidth=2.5
        )
    else:
        ax3.scatter(
            df["_mission_seconds"],
            df[Y3_COLUMN],
            color=Y3_COLOR,
            label=Y3_LABEL
        )

    ax3.set_ylabel(Y3_LABEL, color=Y3_COLOR)
    ax3.tick_params(axis="y", labelcolor=Y3_COLOR)

    # Combined legend
    lines = (
        ax1.get_lines() +
        ax2.get_lines() +
        ax3.get_lines()
    )

    labels = [line.get_label() for line in lines]

    ax1.legend(lines, labels, loc="upper left")

# =====================================================
# X AXIS FORMATTING
# =====================================================

n_points = len(df)

tick_count = min(MAX_X_TICKS, n_points)

tick_indices = np.linspace(
    0,
    n_points - 1,
    tick_count,
    dtype=int
)

tick_positions = df["_mission_seconds"].iloc[tick_indices]

tick_labels = df[TIME_COLUMN].iloc[tick_indices]

ax1.set_xticks(tick_positions)
ax1.set_xticklabels(
    tick_labels,
    rotation=45,
    ha="right"
)

# =====================================================
# FINAL FORMATTING
# =====================================================

ax1.set_xlabel(X_AXIS_LABEL)
ax1.set_title(TITLE)

ax1.grid(
    True,
    linestyle="--",
    alpha=0.4
)

plt.tight_layout()
plt.show()