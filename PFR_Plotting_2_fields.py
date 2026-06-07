import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator
from mpl_toolkits.mplot3d import Axes3D

# ============================================================
# USER SETTINGS
# ============================================================

CSV_FILE = "Ground-Station/flight-csv/Flight_1083.csv"

# Mission time column (HH:MM:SS format)
TIME_COLUMN = "MISSION_TIME"

# ============================================================
# PRIMARY DATA SERIES
# ============================================================

Y1_COLUMN = "ALTITUDE"
Y1_LABEL = "Altitude (m)"
Y1_COLOR = "tab:blue"

# ============================================================
# SECONDARY DATA SERIES
# Set Y2_COLUMN = None to disable
# ============================================================

Y2_COLUMN = "MAX_ALTITUDE"
Y2_LABEL = "Max Altitude (m)"
Y2_COLOR = "tab:red"

# True = left and right Y axes
# False = both lines on same axis
USE_SECOND_Y_AXIS = True

# ============================================================
# 3D SETTINGS
# ============================================================

ENABLE_3D = False

# Used only when ENABLE_3D = True
Z_COLUMN = "ACCELERATION"
Z_LABEL = "Acceleration"

# Optional color column for 3D scatter
COLOR_COLUMN = None

# ============================================================
# PLOT APPEARANCE
# ============================================================

TITLE = "Max Altitude"
X_LABEL = "Mission Time"

PLOT_TYPE = "line"  # "line" or "scatter"

FIGURE_SIZE = (14, 8)

MAX_POINTS = 5000

SAVE_PLOT = False
OUTPUT_FILE = "plot.png"

# ============================================================
# LOAD CSV
# ============================================================

df = pd.read_csv(CSV_FILE)

# ============================================================
# VERIFY COLUMNS
# ============================================================

required_columns = [TIME_COLUMN, Y1_COLUMN]

if Y2_COLUMN is not None:
    required_columns.append(Y2_COLUMN)

if ENABLE_3D:
    required_columns.append(Z_COLUMN)

for col in required_columns:
    if col not in df.columns:
        raise ValueError(f"Column '{col}' not found in CSV.")

# ============================================================
# CONVERT HH:MM:SS TO SECONDS
# ============================================================

df["_mission_seconds"] = (
    pd.to_timedelta(df[TIME_COLUMN])
    .dt.total_seconds()
)

# ============================================================
# DOWNSAMPLE VERY LARGE FILES
# ============================================================

if len(df) > MAX_POINTS:
    step = max(1, len(df) // MAX_POINTS)
    df = df.iloc[::step].reset_index(drop=True)

# ============================================================
# FORMAT X AXIS AS HH:MM:SS
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

if not ENABLE_3D:

    fig, ax1 = plt.subplots(figsize=FIGURE_SIZE)

    # --------------------------------------------------------
    # PRIMARY SERIES
    # --------------------------------------------------------

    if PLOT_TYPE.lower() == "line":

        ax1.plot(
            df["_mission_seconds"],
            df[Y1_COLUMN],
            color=Y1_COLOR,
            linewidth=2.5,
            label=Y1_LABEL
        )

    else:

        ax1.scatter(
            df["_mission_seconds"],
            df[Y1_COLUMN],
            color=Y1_COLOR,
            s=12,
            label=Y1_LABEL
        )

    ax1.set_ylabel(
        Y1_LABEL,
        color=Y1_COLOR,
        fontsize=12
    )

    ax1.tick_params(
        axis="y",
        labelcolor=Y1_COLOR
    )

    # --------------------------------------------------------
    # SECONDARY SERIES
    # --------------------------------------------------------

    if Y2_COLUMN is not None:

        if USE_SECOND_Y_AXIS:

            ax2 = ax1.twinx()

            if PLOT_TYPE.lower() == "line":

                ax2.plot(
                    df["_mission_seconds"],
                    df[Y2_COLUMN],
                    color=Y2_COLOR,
                    linestyle="--",
                    linewidth=2.5,
                    label=Y2_LABEL
                )

            else:

                ax2.scatter(
                    df["_mission_seconds"],
                    df[Y2_COLUMN],
                    color=Y2_COLOR,
                    s=12,
                    label=Y2_LABEL
                )

            ax2.set_ylabel(
                Y2_LABEL,
                color=Y2_COLOR,
                fontsize=12
            )

            ax2.tick_params(
                axis="y",
                labelcolor=Y2_COLOR
            )

            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()

            ax1.legend(
                lines1 + lines2,
                labels1 + labels2,
                loc="upper left"
            )

        else:

            if PLOT_TYPE.lower() == "line":

                ax1.plot(
                    df["_mission_seconds"],
                    df[Y2_COLUMN],
                    color=Y2_COLOR,
                    linestyle="--",
                    linewidth=2.5,
                    label=Y2_LABEL
                )

            else:

                ax1.scatter(
                    df["_mission_seconds"],
                    df[Y2_COLUMN],
                    color=Y2_COLOR,
                    s=12,
                    label=Y2_LABEL
                )

            ax1.legend(loc="upper left")

    else:

        ax1.legend(loc="upper left")

    # --------------------------------------------------------
    # AXIS FORMATTING
    # --------------------------------------------------------

    ax1.xaxis.set_major_formatter(
        FuncFormatter(format_time)
    )

    ax1.xaxis.set_major_locator(
        MaxNLocator(nbins=8)
    )

    ax1.set_xlabel(X_LABEL, fontsize=12)
    ax1.set_title(TITLE, fontsize=16)

    ax1.grid(True, alpha=0.3)

    plt.xticks(rotation=30)

# ============================================================
# 3D PLOT
# ============================================================

else:

    fig = plt.figure(figsize=FIGURE_SIZE)
    ax = fig.add_subplot(111, projection="3d")

    if COLOR_COLUMN is not None:

        scatter = ax.scatter(
            df["_mission_seconds"],
            df[Y1_COLUMN],
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
                df[Y1_COLUMN],
                df[Z_COLUMN],
                color=Y1_COLOR,
                linewidth=2.5
            )

        else:

            ax.scatter(
                df["_mission_seconds"],
                df[Y1_COLUMN],
                df[Z_COLUMN],
                color=Y1_COLOR,
                s=10
            )

    ax.set_title(TITLE)
    ax.set_xlabel(X_LABEL)
    ax.set_ylabel(Y1_LABEL)
    ax.set_zlabel(Z_LABEL)

# ============================================================
# FINALIZE
# ============================================================

plt.tight_layout()

if SAVE_PLOT:
    plt.savefig(
        OUTPUT_FILE,
        dpi=300,
        bbox_inches="tight"
    )
    print(f"Saved plot to: {OUTPUT_FILE}")

plt.show()