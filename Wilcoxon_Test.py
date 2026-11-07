
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, rankdata
from statsmodels.stats.multitest import multipletests
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ==================================================
# 1. CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / (
    "Merged_Driving_Simulator_Participant_Data.xlsx"
)

OUTPUT_FILE = BASE_DIR / (
    "Wilcoxon_Publication_Results.xlsx"
)

SHEET_NAME = "Merged_Participants"

ALPHA = 0.05

AREAS = {
    "INFO": "Advance Warning",
    "TRANS": "Transition",
    "CONST": "Activity",
    "REDIR": "Termination"
}

VARIABLES = {
    "Speed": ("Mean speed", "km/h"),
    "Acceleration": ("Mean acceleration", "m/s²"),
    "Deceleration": ("Mean deceleration", "m/s²"),
    "Lane_Changes": ("Lane changes", "count")
}

# ==================================================
# 2. LOAD DATA
# ==================================================

df = pd.read_excel(
    INPUT_FILE,
    sheet_name=SHEET_NAME
)

if df["Participant_ID"].duplicated().any():
    raise ValueError("Duplicate participant IDs detected.")

# ==================================================
# 3. WILCOXON SIGNED-RANK TESTS
# ==================================================

results = []

for variable, (variable_name, unit) in VARIABLES.items():

    for code, area in AREAS.items():

        yellow_col = f"{variable}_Yellow_{code}"
        blue_col = f"{variable}_Blue_{code}"

        if yellow_col not in df.columns or blue_col not in df.columns:
            raise ValueError(
                f"Missing columns: {yellow_col}, {blue_col}"
            )

        paired = df[
            [yellow_col, blue_col]
        ].apply(
            pd.to_numeric,
            errors="coerce"
        ).dropna()

        yellow = paired[yellow_col].to_numpy(dtype=float)
        blue = paired[blue_col].to_numpy(dtype=float)

        n = len(paired)

        if n < 2:
            raise ValueError(
                f"Insufficient paired observations: "
                f"{variable_name}, {area}"
            )

        # Positive differences indicate Yellow > Blue
        differences = yellow - blue

        # ----------------------------------------------
        # Descriptive statistics
        # ----------------------------------------------

        mean_y = np.mean(yellow)
        mean_b = np.mean(blue)

        sd_y = np.std(yellow, ddof=1)
        sd_b = np.std(blue, ddof=1)

        median_y = np.median(yellow)
        median_b = np.median(blue)

        mean_diff = np.mean(differences)
        median_diff = np.median(differences)

        # ----------------------------------------------
        # Wilcoxon signed-rank test
        # ----------------------------------------------

        nonzero = differences[differences != 0]

        if len(nonzero) == 0:

            W_stat = 0.0
            p_value = 1.0

        else:

            test = wilcoxon(
                differences,
                alternative="two-sided",
                zero_method="wilcox",
                correction=False,
                method="auto"
            )

            W_stat = float(test.statistic)
            p_value = float(test.pvalue)

        # ----------------------------------------------
        # Rank-biserial correlation
        # ----------------------------------------------

        if len(nonzero) > 0:

            ranks = rankdata(np.abs(nonzero))

            W_positive = np.sum(
                ranks[nonzero > 0]
            )

            W_negative = np.sum(
                ranks[nonzero < 0]
            )

            rank_biserial = (
                (W_positive - W_negative)
                / (W_positive + W_negative)
            )

        else:

            rank_biserial = 0.0

        # ----------------------------------------------
        # Store results
        # ----------------------------------------------

        results.append({
            "Variable": variable_name,
            "Area": area,
            "Unit": unit,
            "N": n,
            "Mean_Yellow": mean_y,
            "SD_Yellow": sd_y,
            "Mean_Blue": mean_b,
            "SD_Blue": sd_b,
            "Median_Yellow": median_y,
            "Median_Blue": median_b,
            "Mean_Difference": mean_diff,
            "Median_Paired_Difference": median_diff,
            "W_statistic": W_stat,
            "p_value": p_value,
            "Rank_Biserial_r": rank_biserial,
            "N_Yellow_Greater": int(np.sum(differences > 0)),
            "N_Blue_Greater": int(np.sum(differences < 0)),
            "N_Equal": int(np.sum(differences == 0))
        })

# ==================================================
# 4. MULTIPLE-COMPARISON ADJUSTMENT
# ==================================================

results_df = pd.DataFrame(results)

# Each variable is treated as a separate family.
# The Transition Area is the prespecified treatment
# comparison. Other areas are secondary.

results_df["p_Holm_Secondary"] = np.nan

for variable_name in results_df["Variable"].unique():

    mask = (
        (results_df["Variable"] == variable_name)
        & (results_df["Area"] != "Transition")
    )

    adjusted = multipletests(
        results_df.loc[mask, "p_value"],
        method="holm"
    )[1]

    results_df.loc[
        mask, "p_Holm_Secondary"
    ] = adjusted

# The Transition Area uses the raw p-value.
# Secondary areas use Holm-adjusted p-values.

results_df["p_Reported"] = np.where(
    results_df["Area"] == "Transition",
    results_df["p_value"],
    results_df["p_Holm_Secondary"]
)

results_df["Significant_0.05"] = (
    results_df["p_Reported"] < ALPHA
)

# ==================================================
# 5. CREATE PUBLICATION TABLE
# ==================================================

def format_p(p):
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "<0.001"
    return f"{p:.3f}"

publication_rows = []

for _, row in results_df.iterrows():

    publication_rows.append({
        "Variable": row["Variable"],
        "Work-zone area": row["Area"],
        "N": int(row["N"]),
        "Yellow (Mean ± SD)": (
            f"{row['Mean_Yellow']:.2f} ± "
            f"{row['SD_Yellow']:.2f}"
        ),
        "Blue (Mean ± SD)": (
            f"{row['Mean_Blue']:.2f} ± "
            f"{row['SD_Blue']:.2f}"
        ),
        "Mean Δ (Y−B)": (
            f"{row['Mean_Difference']:.2f}"
        ),
        "W": f"{row['W_statistic']:.1f}",
        "p-value": format_p(row["p_Reported"]),
        "r_rb": f"{row['Rank_Biserial_r']:.3f}",
        "Significant": (
            "Yes" if row["Significant_0.05"] else "No"
        )
    })

publication_df = pd.DataFrame(publication_rows)

# ==================================================
# 6. PRINT RESULTS
# ==================================================

print("\nPUBLICATION TABLE")
print("=" * 120)

print(
    publication_df.to_string(index=False)
)

print("\nDETAILED RESULTS")
print("=" * 120)

print(
    results_df.round(4).to_string(index=False)
)

# ==================================================
# 7. EXPORT TO EXCEL
# ==================================================

with pd.ExcelWriter(
    OUTPUT_FILE,
    engine="openpyxl"
) as writer:

    publication_df.to_excel(
        writer,
        sheet_name="Publication_Table",
        index=False
    )

    results_df.to_excel(
        writer,
        sheet_name="Detailed_Results",
        index=False
    )

    # Separate results for each variable
    for variable_name in results_df["Variable"].unique():

        subset = results_df[
            results_df["Variable"] == variable_name
        ]

        sheet_name = variable_name.replace(" ", "_")

        subset.to_excel(
            writer,
            sheet_name=sheet_name[:31],
            index=False
        )

    # ----------------------------------------------
    # Format publication table
    # ----------------------------------------------

    ws = writer.sheets["Publication_Table"]

    header_fill = PatternFill(
        start_color="17365D",
        end_color="17365D",
        fill_type="solid"
    )

    header_font = Font(
        bold=True,
        color="FFFFFF"
    )

    treatment_fill = PatternFill(
        start_color="E8F0FA",
        end_color="E8F0FA",
        fill_type="solid"
    )

    significant_font = Font(
        bold=True,
        color="006100"
    )

    for cell in ws[1]:

        cell.fill = header_fill
        cell.font = header_font

        cell.alignment = Alignment(
            horizontal="center",
            vertical="center"
        )

    for row in ws.iter_rows(
        min_row=2,
        max_row=ws.max_row
    ):

        area = row[1].value

        if area == "Transition":

            for cell in row:
                cell.fill = treatment_fill

        # Highlight statistically significant p-values
        if row[9].value == "Yes":
            row[7].font = significant_font

    # Column widths
    widths = {
        "A": 22,
        "B": 20,
        "C": 8,
        "D": 23,
        "E": 23,
        "F": 17,
        "G": 12,
        "H": 12,
        "I": 12,
        "J": 14
    }

    for col, width in widths.items():
        ws.column_dimensions[col].width = width

    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions

print(f"\nResults saved to: {OUTPUT_FILE}")
