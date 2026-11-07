# ==========================================================
# FIGURA 5.13b - IMPRESIÓN GENERADA POR LAS LUCES DESTELLANTES AZULES
# Versión para tesis (etiquetas cortas + leyenda inferior)
# ==========================================================

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import os

# ----------------------------------------------------------
# CONFIGURACIÓN
# ----------------------------------------------------------

archivo = r"C:\Users\danie\Desktop\PC\maestría\articulo 03.- luz parpadeante\encuesta_luces_destellantes\encuesta_participantes.xlsx"

carpeta_salida = os.path.join(os.path.dirname(archivo), "Figuras_Capitulo5")
os.makedirs(carpeta_salida, exist_ok=True)

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["axes.titlesize"] = 10
mpl.rcParams["axes.labelsize"] = 9
mpl.rcParams["xtick.labelsize"] = 8
mpl.rcParams["ytick.labelsize"] = 8

AZUL = "#0000FF"
VERDE = "#008000"
ROJO = "#FF0000"
GRIS = "#808080"

# ----------------------------------------------------------
# CARGAR ENCUESTA
# ----------------------------------------------------------

df = pd.read_excel(
    archivo,
    sheet_name="Respuestas_Encuesta",
    header=2
)

df = df[df["ID Participante"].notna()].copy()

# ----------------------------------------------------------
# RESPUESTAS DE LA PREGUNTA "REACCIÓN PRINCIPAL"
# ----------------------------------------------------------

# Mantener siempre el mismo orden de aparición
orden_reaccion = [
    "Reduje mi velocidad.",
    "Me preparé para detenerme o disminuir la marcha.",
    "Incrementó mi atención al entorno vial.",
    "No tuve ninguna reacción particular."
]

reaccion = (
    df["Reacción Principal"]
    .astype(str)
    .str.strip()
    .replace({
        "Reduje mi velocidad": "Reduje mi velocidad.",
        "Me preparé para detenerme o disminuir la marcha": "Me preparé para detenerme o disminuir la marcha.",
        "Incrementó mi atención al entorno vial": "Incrementó mi atención al entorno vial.",
        "No tuve ninguna reacción particular": "No tuve ninguna reacción particular."
    })
    .value_counts()
    .reindex(orden_reaccion, fill_value=0)
)

reaccion_pct = reaccion / reaccion.sum() * 100

# ----------------------------------------------------------
# ETIQUETAS CORTAS PARA EL EJE X
# ----------------------------------------------------------

etiquetas = ["R1", "R2", "R3", "R4"]

descripcion = [
    "R1 = Reduje mi velocidad.",
    "R2 = Me preparé para detenerme o disminuir la marcha.",
    "R3 = Incrementó mi atención al entorno vial.",
    "R4 = No tuve ninguna reacción particular."
]

# ----------------------------------------------------------
# CREAR FIGURA
# ----------------------------------------------------------

fig, ax = plt.subplots(figsize=(6.5,5.4), dpi=600)

barras = ax.bar(
    etiquetas,
    reaccion.values,
    color=[AZUL, VERDE, ROJO, GRIS],
    edgecolor="black",
    linewidth=1.0
)

ax.set_title("Impresión generada por las luces destellantes azules")
ax.set_xlabel("Reacción reportada")
ax.set_ylabel("Número de participantes")

ax.grid(axis="y", linestyle="--", alpha=0.35)

ax.set_ylim(0, max(reaccion.values)+max(reaccion.values)*0.20+1)

# Porcentajes sobre las barras
for barra, porcentaje in zip(barras, reaccion_pct):

    ax.text(
        barra.get_x()+barra.get_width()/2,
        barra.get_height()+0.35,
        f"{porcentaje:.0f}%",
        ha="center",
        fontsize=8,
        fontweight="bold"
    )

# ----------------------------------------------------------
# LEYENDA INFERIOR (NO SE ENCIMAN LOS TEXTOS)
# ----------------------------------------------------------

leyenda = "\n".join(descripcion)

ax.text(
    0.01,
    -0.28,
    leyenda,
    transform=ax.transAxes,
    fontsize=8,
    va="top",
    ha="left"
)

# Subfigura
ax.text(
    0.5,
    -0.54,
    "(b) Impresión generada por las luces destellantes azules",
    transform=ax.transAxes,
    ha="center",
    fontsize=9
)

plt.tight_layout()

fig.savefig(
    os.path.join(
        carpeta_salida,
        "Figura_5_13b_Reaccion_Principal.png"
    ),
    dpi=600,
    bbox_inches="tight",
    facecolor="white"
)

plt.close()

print("Figura 5.13b generada correctamente.")