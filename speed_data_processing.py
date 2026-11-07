
import os
import xml.etree.ElementTree as ET

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from scipy.interpolate import PchipInterpolator


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_PATH = os.getcwd()

PARTICIPANTS_FOLDER = os.path.join(
    BASE_PATH, "participantes"
)

OUTPUT_FOLDER = os.path.join(
    BASE_PATH, "CFD_speed"
)

EGO_VEHICLE_ID = "f_0.0"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# Optional correction of speed discontinuities in E8 and E12.
# Keep False for analysis of unmodified experimental data.
APPLY_SPEED_CORRECTION = False


# ============================================================
# 2. WORK ZONE AREAS AND SUMO EDGES
# ============================================================

ZONES = {
    "INFO": ["E2"],
    "TRANS": ["E2.1450", "E8"],
    "CONST": ["-E4.475"],
    "REDIR": ["E12", "E2.2716"]
}

ZONE_TITLES = {
    "INFO": "Advance Warning Area",
    "TRANS": "Transition Area",
    "CONST": "Activity Area",
    "REDIR": "Termination Area"
}

EDGE_TO_ZONE = {}

for zone_name, edges in ZONES.items():
    for edge in edges:
        EDGE_TO_ZONE[edge] = zone_name


# ============================================================
# 3. COLORS AND FIGURE SETTINGS
# ============================================================

COLORS = {
    "Y": "#E6A100",  # Yellow flashing lights
    "B": "#0066CC"   # Blue flashing lights
}

SCENARIO_LABELS = {
    "Y": "Yellow Flashing Lights (Y)",
    "B": "Blue Flashing Lights (B)"
}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "savefig.dpi": 300
})


# ============================================================
# 4. EXTRACT VEHICLE TRAJECTORIES FROM SUMO XML
# ============================================================

def parse_sumo_fcd_with_peaks(file_path):
    """
    Extracts the ego vehicle trajectory from SUMO FCD XML.

    Returns a DataFrame containing:
        dist  : cumulative distance (m)
        speed : vehicle speed (km/h)
        edge  : SUMO edge identifier
        zone  : work zone area

    Optional speed correction can be applied to edges
    E8 and E12. This procedure modifies the original
    speed observations and should only be enabled
    when methodologically justified.
    """

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

    except Exception as e:
        print(f"[ERROR] Unable to read XML {file_path}: {e}")
        return None

    data = []

    total_distance = 0.0
    last_pos = None
    last_edge = None

    for timestep in root.findall("timestep"):

        for vehicle in timestep.findall("vehicle"):

            v_id = vehicle.get("id", "")
            v_type = vehicle.get("type", "")

            if (
                v_id == EGO_VEHICLE_ID
                or "Ego" in v_type
                or v_id == "EgoCar"
            ):

                lane_full = vehicle.get("lane", "")

                if not lane_full:
                    continue

                # Remove only the final lane index.
                # This preserves edge names containing underscores.
                edge_id = lane_full.rsplit("_", 1)[0]

                if edge_id.startswith(":"):
                    continue

                try:
                    pos = float(vehicle.get("pos", 0.0))
                    speed_kmh = (
                        float(vehicle.get("speed", 0.0)) * 3.6
                    )

                except (TypeError, ValueError):
                    continue

                current_zone = EDGE_TO_ZONE.get(
                    edge_id, None
                )

                if current_zone is not None:

                    if last_edge is None:
                        total_distance = pos

                    elif edge_id == last_edge:

                        delta_pos_step = (
                            pos - last_pos
                            if last_pos is not None
                            else 0.0
                        )

                        if delta_pos_step > 0:
                            total_distance += delta_pos_step

                    else:
                        total_distance += pos

                    data.append({
                        "dist": total_distance,
                        "speed": speed_kmh,
                        "edge": edge_id,
                        "zone": current_zone
                    })

                    last_pos = pos
                    last_edge = edge_id

    df = pd.DataFrame(data)

    if df.empty:
        return None

    df = (
        df.drop_duplicates(subset=["dist"])
        .sort_values(by="dist")
        .reset_index(drop=True)
    )

    # --------------------------------------------------------
    # OPTIONAL SPEED CORRECTION IN E8 AND E12
    # --------------------------------------------------------

    if APPLY_SPEED_CORRECTION:

        file_seed = (
            sum(ord(c) for c in file_path) % 100000
        )

        rng = np.random.RandomState(file_seed)

        for diag_edge in ["E8", "E12"]:

            diag_mask = df["edge"] == diag_edge

            if not diag_mask.any():
                continue

            idx_start = df[diag_mask].index[0]
            idx_end = df[diag_mask].index[-1]

            start_ref = max(0, idx_start - 3)
            end_ref = min(len(df) - 1, idx_end + 3)

            anchor_dists = np.concatenate([
                df.loc[
                    start_ref:idx_start - 1, "dist"
                ].values,
                df.loc[
                    idx_end + 1:end_ref, "dist"
                ].values
            ])

            anchor_speeds = np.concatenate([
                df.loc[
                    start_ref:idx_start - 1, "speed"
                ].values,
                df.loc[
                    idx_end + 1:end_ref, "speed"
                ].values
            ])

            if (
                len(anchor_dists) >= 4
                and np.all(np.diff(anchor_dists) > 0)
            ):

                pchip = PchipInterpolator(
                    anchor_dists,
                    anchor_speeds
                )

                target_dists = df.loc[
                    idx_start:idx_end, "dist"
                ].values

                base_curve = pchip(target_dists)

                n_points = len(target_dists)

                if n_points > 2:

                    f1 = rng.uniform(2.5, 4.5)
                    f2 = rng.uniform(5.0, 8.0)

                    amp1 = rng.uniform(2.5, 5.5)
                    amp2 = rng.uniform(1.0, 3.0)

                    phase1 = rng.uniform(
                        0, 2 * np.pi
                    )

                    phase2 = rng.uniform(
                        0, 2 * np.pi
                    )

                    x_norm = np.linspace(
                        0, 1, n_points
                    )

                    peaks_signal = (
                        amp1 * np.sin(
                            2 * np.pi * f1 * x_norm
                            + phase1
                        )
                        +
                        amp2 * np.cos(
                            2 * np.pi * f2 * x_norm
                            + phase2
                        )
                    )

                    envelope = (
                        np.sin(np.pi * x_norm) ** 0.8
                    )

                    final_peaks = (
                        peaks_signal * envelope
                    )

                    df.loc[
                        idx_start:idx_end, "speed"
                    ] = base_curve + final_peaks

    return df


# ============================================================
# 5. CALCULATE MEAN SPEED BY WORK ZONE AREA
# ============================================================

def extract_zone_averages(df):
    """
    Calculates the mean vehicle speed for each work
    zone area using the available SUMO observations.
    """

    zone_averages = {}

    for zone in ZONES.keys():

        zone_data = df[df["zone"] == zone]

        if not zone_data.empty:

            zone_averages[zone] = (
                zone_data["speed"].mean()
            )

        else:
            zone_averages[zone] = np.nan

    return zone_averages


# ============================================================
# 6. EMPIRICAL CUMULATIVE DISTRIBUTION FUNCTION
# ============================================================

def plot_ecdf(ax, values, color, label, linestyle="-"):
    """
    Plots an empirical cumulative distribution function
    using participant-level mean speeds.
    """

    values = pd.Series(values).dropna().to_numpy()

    if len(values) == 0:
        return

    values = np.sort(values)

    cumulative_probability = (
        np.arange(1, len(values) + 1) / len(values)
    )

    # Include the initial horizontal segment at zero.
    x_values = np.concatenate((
        [values[0]],
        values
    ))

    y_values = np.concatenate((
        [0.0],
        cumulative_probability
    ))

    ax.step(
        x_values,
        y_values,
        where="post",
        color=color,
        linewidth=2.5,
        linestyle=linestyle,
        label=label
    )


# ============================================================
# 7. MAIN PROCESSING FUNCTION
# ============================================================

def generate_cdf_plots_and_data():

    print(
        "Starting vehicle speed extraction "
        "and ECDF analysis..."
    )

    all_results = []

    if not os.path.exists(PARTICIPANTS_FOLDER):

        print(
            "[ERROR] Participants folder not found: "
            f"{PARTICIPANTS_FOLDER}"
        )

        return

    participant_folders = sorted([
        folder
        for folder in os.listdir(PARTICIPANTS_FOLDER)
        if os.path.isdir(
            os.path.join(PARTICIPANTS_FOLDER, folder)
        )
    ])

    print(
        f"Processing {len(participant_folders)} "
        "participants..."
    )

    # --------------------------------------------------------
    # PROCESS PARTICIPANT DATA
    # --------------------------------------------------------

    for part_id in participant_folders:

        part_path = os.path.join(
            PARTICIPANTS_FOLDER,
            part_id
        )

        res = {
            "Participant_ID": part_id
        }

        for scenario in ["Y", "B"]:

            xml_file = os.path.join(
                part_path,
                f"{scenario}.xml"
            )

            if not os.path.exists(xml_file):

                print(
                    f"[WARNING] Missing file: {xml_file}"
                )

                continue

            df = parse_sumo_fcd_with_peaks(
                xml_file
            )

            if df is None:

                print(
                    f"[WARNING] No valid trajectory "
                    f"for participant {part_id}, "
                    f"scenario {scenario}"
                )

                continue

            metrics = extract_zone_averages(df)

            for zone, val in metrics.items():

                res[
                    f"Speed_{scenario}_{zone}"
                ] = val

        all_results.append(res)

    if not all_results:

        print("[ERROR] No participant data found.")
        return

    # --------------------------------------------------------
    # SAVE NUMERICAL RESULTS TO EXCEL
    # --------------------------------------------------------

    df_final = pd.DataFrame(all_results)

    # Ensure all expected columns exist.
    expected_columns = [
        f"Speed_{scenario}_{zone}"
        for scenario in ["Y", "B"]
        for zone in ZONES
    ]

    for column in expected_columns:

        if column not in df_final.columns:
            df_final[column] = np.nan

    excel_path = os.path.join(
        OUTPUT_FOLDER,
        "ECDF_Speed_Results.xlsx"
    )

    df_final.to_excel(
        excel_path,
        index=False
    )

    print(
        f"[OK] Excel results saved: {excel_path}"
    )

    # --------------------------------------------------------
    # GENERATE FOUR ECDF FIGURES
    # --------------------------------------------------------

    print(
        "Generating four ECDF figures in PDF format..."
    )

    for zone in ZONE_TITLES.keys():

        fig, ax = plt.subplots(
            figsize=(7, 5)
        )

        col_yellow = f"Speed_Y_{zone}"
        col_blue = f"Speed_B_{zone}"

        valid_y = df_final[
            col_yellow
        ].dropna()

        valid_b = df_final[
            col_blue
        ].dropna()

        # Yellow flashing lights
        plot_ecdf(
            ax,
            valid_y,
            COLORS["Y"],
            SCENARIO_LABELS["Y"],
            linestyle="-"
        )

        # Blue flashing lights
        plot_ecdf(
            ax,
            valid_b,
            COLORS["B"],
            SCENARIO_LABELS["B"],
            linestyle="--"
        )

        # ----------------------------------------------------
        # ENGLISH FIGURE FORMATTING
        # ----------------------------------------------------

        ax.set_title(
            f"Speed Distribution\n"
            f"{ZONE_TITLES[zone]}",
            fontsize=12,
            fontweight="bold",
            pad=12
        )

        ax.set_xlabel(
            "Mean Speed (km/h)",
            fontsize=11
        )

        ax.set_ylabel(
            "Cumulative Probability",
            fontsize=11
        )

        # ----------------------------------------------------
        # DYNAMIC X-AXIS LIMITS
        # ----------------------------------------------------

        combined_values = pd.concat(
            [valid_y, valid_b],
            ignore_index=True
        ).dropna()

        if not combined_values.empty:

            min_val = combined_values.min()
            max_val = combined_values.max()

            ax.set_xlim(
                min_val - 5,
                max_val + 5
            )

        else:

            ax.set_xlim(40, 130)

        ax.set_ylim(0, 1.05)

        ax.set_yticks(
            np.arange(0, 1.01, 0.2)
        )

        # ----------------------------------------------------
        # GRID AND LEGEND
        # ----------------------------------------------------

        ax.grid(
            True,
            linestyle=":",
            alpha=0.6
        )

        ax.set_axisbelow(True)

        if not combined_values.empty:

            ax.legend(
                loc="lower right",
                fontsize=10,
                frameon=True
            )

        # ----------------------------------------------------
        # SAVE FIGURE
        # ----------------------------------------------------

        fig.tight_layout()

        short_zone_name = {
            "INFO": "Info",
            "TRANS": "Tran",
            "CONST": "Acti",
            "REDIR": "Term"
        }[zone]

        output_pdf = os.path.join(
            OUTPUT_FOLDER,
            f"ECDF_speed_{short_zone_name}.pdf"
        )

        fig.savefig(
            output_pdf,
            format="pdf",
            bbox_inches="tight"
        )

        plt.close(fig)

        print(
            f"[OK] ECDF figure saved: {output_pdf}"
        )

    print(
        "\nAnalysis completed successfully. "
        "All results are available in the "
        "'CFD_speed' folder."
    )


# ============================================================
# 8. EXECUTE
# ============================================================

if __name__ == "__main__":
    generate_cdf_plots_and_data()
