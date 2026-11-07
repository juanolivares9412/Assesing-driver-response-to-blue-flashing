
# ==========================================================
# FIGURA 5.13 - PERCEPCIONES SOBRE LAS LUCES DESTELLANTES AZULES
# ==========================================================

# ---------- Columnas de la encuesta (ajustar si cambia el nombre)
conciencia = (
    df["¿Notó el cambio de color de las luces destellantes?"]
    .value_counts()
    .reindex(["No","Sí"])
    .fillna(0)
)
conciencia_pct = conciencia / conciencia.sum() * 100

recuerdo = (
    df["¿Recuerda haber observado luces destellantes azules?"]
    .value_counts()
    .reindex(["No","Sí"])
    .fillna(0)
)
recuerdo_pct = recuerdo / recuerdo.sum() * 100

impresion = (
    df["¿Qué impresión le generaron las luces destellantes azules?"]
    .value_counts()
    .reindex(["Mayor alerta","Curiosidad"])
    .fillna(0)
)
impresion_pct = impresion / impresion.sum() * 100

reduccion = (
    df["¿Considera que redujo su velocidad al observar las luces azules?"]
    .value_counts()
    .reindex(["No","Sí"])
    .fillna(0)
)
reduccion_pct = reduccion / reduccion.sum() * 100

efectividad = (
    df["Comparación de efectividad de las luces azules respecto a las ámbar"]
    .value_counts()
    .reindex([
        "Menos efectiva",
        "Igualmente efectiva",
        "Más efectiva",
        "Sin opinión"
    ])
    .fillna(0)
)
efectividad_pct = efectividad / efectividad.sum() * 100

seguridad = (
    df["¿Considera que las luces azules mejoran la seguridad en zonas de obra?"]
    .value_counts()
    .reindex(["No","Sí","No estoy seguro"])
    .fillna(0)
)
seguridad_pct = seguridad / seguridad.sum() * 100


# ==========================================================
# FIGURA COMPUESTA 2x3
# ==========================================================

fig, axs = plt.subplots(
    2, 3,
    figsize=(15,9),
    dpi=600,
    constrained_layout=True
)

# -------- (a) Conciencia
bars = axs[0,0].bar(
    conciencia.index,
    conciencia.values,
    color=[AZUL, VERDE],
    edgecolor="black"
)
axs[0,0].set_title("Conciencia del cambio en las luces destellantes", fontsize=10)
axs[0,0].set_ylabel("Número de participantes")
axs[0,0].set_xlabel("Respuesta")

for b,p in zip(bars, conciencia_pct):
    axs[0,0].text(
        b.get_x()+b.get_width()/2,
        b.get_height()+0.2,
        f"{p:.0f}%",
        ha="center",
        fontsize=8,
        fontweight="bold"
    )

axs[0,0].text(
    0.5,-0.22,
    "(a) Conciencia del cambio de color de las luces",
    transform=axs[0,0].transAxes,
    ha="center",
    fontsize=9
)


# -------- (b) Recuerdo
bars = axs[0,1].bar(
    recuerdo.index,
    recuerdo.values,
    color=[AZUL, VERDE],
    edgecolor="black"
)

axs[0,1].set_title("Recuerdo de las luces destellantes azules", fontsize=10)
axs[0,1].set_ylabel("Número de participantes")
axs[0,1].set_xlabel("Respuesta")

for b,p in zip(bars, recuerdo_pct):
    axs[0,1].text(
        b.get_x()+b.get_width()/2,
        b.get_height()+0.2,
        f"{p:.0f}%",
        ha="center",
        fontsize=8,
        fontweight="bold"
    )

axs[0,1].text(
    0.5,-0.22,
    "(b) Recuerdo de las luces destellantes azules",
    transform=axs[0,1].transAxes,
    ha="center",
    fontsize=9
)


# -------- (c) Impresión
bars = axs[0,2].bar(
    impresion.index,
    impresion.values,
    color=[AZUL, VERDE],
    edgecolor="black"
)

axs[0,2].set_title("Impresión generada por las luces destellantes azules", fontsize=10)
axs[0,2].set_ylabel("Número de participantes")
axs[0,2].set_xlabel("Impresión reportada")

for b,p in zip(bars, impresion_pct):
    axs[0,2].text(
        b.get_x()+b.get_width()/2,
        b.get_height()+0.2,
        f"{p:.0f}%",
        ha="center",
        fontsize=8,
        fontweight="bold"
    )

axs[0,2].text(
    0.5,-0.22,
    "(c) Impresión generada por las luces destellantes azules",
    transform=axs[0,2].transAxes,
    ha="center",
    fontsize=9
)


# -------- (d) Reducción de velocidad
bars = axs[1,0].bar(
    reduccion.index,
    reduccion.values,
    color=[AZUL, VERDE],
    edgecolor="black"
)

axs[1,0].set_title("Reducción de velocidad autopercibida", fontsize=10)
axs[1,0].set_ylabel("Número de participantes")
axs[1,0].set_xlabel("Respuesta")

for b,p in zip(bars, reduccion_pct):
    axs[1,0].text(
        b.get_x()+b.get_width()/2,
        b.get_height()+0.2,
        f"{p:.0f}%",
        ha="center",
        fontsize=8,
        fontweight="bold"
    )

axs[1,0].text(
    0.5,-0.22,
    "(d) Reducción de velocidad autopercibida",
    transform=axs[1,0].transAxes,
    ha="center",
    fontsize=9
)


# -------- (e) Efectividad
bars = axs[1,1].bar(
    efectividad.index,
    efectividad.values,
    color=[AZUL, VERDE, ROJO, GRIS],
    edgecolor="black"
)

axs[1,1].set_title("Efectividad percibida (Luz Azul vs Luz Ámbar)", fontsize=10)
axs[1,1].set_ylabel("Número de participantes")
axs[1,1].set_xlabel("Nivel de respuesta")

for b,p in zip(bars, efectividad_pct):
    axs[1,1].text(
        b.get_x()+b.get_width()/2,
        b.get_height()+0.2,
        f"{p:.0f}%",
        ha="center",
        fontsize=8,
        fontweight="bold"
    )

axs[1,1].tick_params(axis="x", rotation=10)

axs[1,1].text(
    0.5,-0.22,
    "(e) Efectividad percibida de las luces destellantes azules",
    transform=axs[1,1].transAxes,
    ha="center",
    fontsize=9
)


# -------- (f) Seguridad
bars = axs[1,2].bar(
    seguridad.index,
    seguridad.values,
    color=[GRIS, VERDE, ROJO],
    edgecolor="black"
)

axs[1,2].set_title("Mejora de seguridad percibida", fontsize=10)
axs[1,2].set_ylabel("Número de participantes")
axs[1,2].set_xlabel("Respuesta")

for b,p in zip(bars, seguridad_pct):
    axs[1,2].text(
        b.get_x()+b.get_width()/2,
        b.get_height()+0.2,
        f"{p:.0f}%",
        ha="center",
        fontsize=8,
        fontweight="bold"
    )

axs[1,2].text(
    0.5,-0.22,
    "(f) Mejora de seguridad percibida",
    transform=axs[1,2].transAxes,
    ha="center",
    fontsize=9
)


# Cuadrícula ligera
for eje in axs.flat:
    eje.grid(axis="y", linestyle="--", alpha=0.3)

# Guardar figura completa
fig.savefig(
    os.path.join(carpeta, "Figura_5_13_Percepciones_Luces_Azules_Completa.png"),
    dpi=600,
    bbox_inches="tight",
    facecolor="white"
)

plt.close(fig)

print("Figura 5.13 guardada correctamente en Figuras_Capitulo5.")