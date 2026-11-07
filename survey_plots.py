import os
import matplotlib.pyplot as plt
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd
import seaborn as sns

# =========================================================
# 1. CARGA Y PROCESAMIENTO DE DATOS (LECTURA DE EXCEL)
# =========================================================
print('1. Cargando datos desde Excel...')
archivo_excel = 'encuesta_participantes.xlsx'

df = pd.read_excel(archivo_excel, sheet_name='Respuestas_Encuesta', header=2)
df = df[df['ID Participante'].notna()].copy()

# Limpieza de datos
df['Conduce Autopistas'] = (
    df['Conduce Autopistas'].astype(str).str.strip().str.capitalize()
)
df['Notó Luz Azul'] = (
    df['Notó Luz Azul'].astype(str).str.strip().str.capitalize()
)

# Estadísticas continuas
stats_continuas = []
vars_continuas = [
    ('Edad (años)', 'Edad (años)'),
    ('Años Experiencia', 'Años de Experiencia'),
    ('Realismo Simulador (1-5)', 'Realismo del Simulador (1-5)'),
]

for col, name in vars_continuas:
  s = pd.to_numeric(df[col], errors='coerce')
  stats_continuas.append({
      'Variable': name,
      'Muestra (N)': int(s.count()),
      'Promedio (Media)': round(s.mean(), 2),
      'Desviación Estándar (DE)': round(s.std(), 2),
      'Mediana': round(s.median(), 2),
      'Mínimo': round(s.min(), 2),
      'Máximo': round(s.max(), 2),
  })

df_continuas = pd.DataFrame(stats_continuas)


def crear_tabla_frecuencia(col_name, label_name):
  counts = df[col_name].value_counts(dropna=False)
  pcts = df[col_name].value_counts(normalize=True, dropna=False) * 100
  res = pd.DataFrame({
      'Categoría / Opción': counts.index.astype(str),
      'Frecuencia Absoluta (n)': counts.values,
      'Porcentaje (%)': pcts.values.round(2),
  })
  res.insert(0, 'Variable / Pregunta', label_name)
  return res


cat_tables = [
    crear_tabla_frecuencia('Género', 'Género'),
    crear_tabla_frecuencia(
        'Frecuencia Conducción', 'Frecuencia de Conducción'
    ),
    crear_tabla_frecuencia('Conduce Autopistas', 'Conducción en Autopistas'),
    crear_tabla_frecuencia(
        'Realismo Simulador (1-5)', 'Realismo del Simulador (1-5)'
    ),
    crear_tabla_frecuencia('Dificultad Adaptación', 'Dificultad de Adaptación'),
    crear_tabla_frecuencia(
        'Sintomatología', 'Sintomatología (Cinetosis/Mareo)'
    ),
    crear_tabla_frecuencia('Notó Luz Azul', 'Notó Luz Azul Destellante'),
    crear_tabla_frecuencia(
        'Reacción Principal', 'Reacción Principal del Conductor'
    ),
    crear_tabla_frecuencia(
        'Comparación vs Luz Amarilla', 'Atención: Luz Azul vs Luz Amarilla'
    ),
    crear_tabla_frecuencia(
        'Aporte Seguridad Vial', 'Aporte a la Seguridad Vial'
    ),
]

df_categoricas = pd.concat(cat_tables, ignore_index=True)

# Guardar pestañas formateadas en Excel
with pd.ExcelWriter(
    archivo_excel, engine='openpyxl', mode='a', if_sheet_exists='replace'
) as writer:
  df_continuas.to_excel(
      writer, sheet_name='Estadisticos_Continuos', index=False
  )
  df_categoricas.to_excel(
      writer, sheet_name='Frecuencias_y_Porcentajes', index=False
  )

wb = openpyxl.load_workbook(archivo_excel)
header_fill = PatternFill(
    start_color='1E3A8A', end_color='1E3A8A', fill_type='solid'
)
header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
border_thin = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9'),
)

for sheet_name in ['Estadisticos_Continuos', 'Frecuencias_y_Porcentajes']:
  ws = wb[sheet_name]
  ws.views.sheetView[0].showGridLines = True
  for col in range(1, ws.max_column + 1):
    cell = ws.cell(row=1, column=col)
    cell.fill = header_fill
    cell.font = header_font
    cell.alignment = Alignment(horizontal='center', vertical='center')

  for row in range(2, ws.max_row + 1):
    for col in range(1, ws.max_column + 1):
      cell = ws.cell(row=row, column=col)
      cell.border = border_thin
      if col > 1:
        cell.alignment = Alignment(horizontal='center', vertical='center')

  for col in ws.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = get_column_letter(col[0].column)
    ws.column_dimensions[col_letter].width = max(max_len + 4, 14)

wb.save(archivo_excel)
print('✅ Datos procesados y guardados correctamente en Excel.')

# =========================================================
# 2. GENERACIÓN DE GRÁFICAS (FIGURAS 1, 2 Y 3)
# =========================================================
print('2. Generando gráficas en formato PNG...')
plt.rcParams['font.family'] = 'sans-serif'
plt.style.use('seaborn-v0_8-whitegrid')

# ---------------------------------------------------------
# 2.1 FIGURA 1: Perfil Demográfico
# ---------------------------------------------------------
fig1, axes1 = plt.subplots(1, 3, figsize=(15, 4.5), dpi=300)

sns.histplot(
    pd.to_numeric(df['Edad (años)'], errors='coerce'),
    bins=8,
    kde=True,
    color='#1E3A8A',
    ax=axes1[0],
)
axes1[0].set_title(
    'A) Distribución de Edad de los Participantes', fontweight='bold'
)
axes1[0].set_xlabel('Edad (años)')
axes1[0].set_ylabel('Frecuencia')

gender_counts = df['Género'].value_counts()
wedges, texts, autotexts = axes1[1].pie(
    gender_counts,
    labels=gender_counts.index,
    autopct='%1.1f%%',
    startangle=90,
    colors=['#1E3A8A', '#E65100', '#0D9488'],
    wedgeprops=dict(width=0.4, edgecolor='w'),
    pctdistance=0.75,
)
for autotext in autotexts:
  autotext.set_color('white')
  autotext.set_weight('bold')
axes1[1].set_title('B) Distribución por Género', fontweight='bold')

freq_counts = df['Frecuencia Conducción'].value_counts()
palette_colors = sns.color_palette('Blues_r', len(freq_counts))
bars1 = axes1[2].bar(
    freq_counts.index, freq_counts.values, color=palette_colors
)

total_conductores = freq_counts.sum()
for bar in bars1:
  height = bar.get_height()
  pct = (height / total_conductores) * 100
  axes1[2].text(
      bar.get_x() + bar.get_width() / 2.0,
      height + (total_conductores * 0.015),
      f'{pct:.1f}%',
      ha='center',
      va='bottom',
      fontweight='bold',
      fontsize=9.5,
  )

axes1[2].set_title('C) Frecuencia de Conducción', fontweight='bold')
axes1[2].set_ylabel('Número de Conductores')
axes1[2].margins(y=0.18)

plt.tight_layout()
ruta_fig1 = os.path.abspath('fig1_perfil_conductores.png')
fig1.savefig(ruta_fig1, dpi=300, bbox_inches='tight')
plt.close(fig1)
print(f'✅ Figura 1 guardada en: {ruta_fig1}')

# ---------------------------------------------------------
# 2.2 FIGURA 2: Percepción y Reacción
# ---------------------------------------------------------
fig2, axes2 = plt.subplots(1, 3, figsize=(16, 5), dpi=300)

noto_counts = df['Notó Luz Azul'].value_counts()
wedges, texts, autotexts = axes2[0].pie(
    noto_counts,
    labels=noto_counts.index,
    autopct='%1.1f%%',
    startangle=140,
    colors=['#1E3A8A', '#E65100'],
    textprops=dict(fontweight='bold'),
)
for autotext in autotexts:
  autotext.set_color('white')
  autotext.set_weight('bold')
axes2[0].set_title('Observación de la Luz Azul Destellante', fontweight='bold')

reac_counts = df['Reacción Principal'].value_counts()
colors_reac = ['#1E3A8A', '#2563EB', '#0D9488', '#94A3B8']
wedges, texts, autotexts = axes2[1].pie(
    reac_counts,
    labels=None,
    autopct='%1.1f%%',
    startangle=90,
    colors=colors_reac[: len(reac_counts)],
    pctdistance=0.75,
)
for autotext in autotexts:
  autotext.set_color('white')
  autotext.set_weight('bold')

axes2[1].legend(
    reac_counts.index,
    loc='lower center',
    bbox_to_anchor=(0.5, -0.25),
    fontsize=8,
    frameon=False,
)
axes2[1].set_title('Acción / Reacción de los Conductores', fontweight='bold')

comp_counts = df['Comparación vs Luz Amarilla'].value_counts()
colors_comp = ['#1E3A8A', '#0D9488', '#E65100']
wedges, texts, autotexts = axes2[2].pie(
    comp_counts,
    labels=None,
    autopct='%1.1f%%',
    startangle=90,
    colors=colors_comp[: len(comp_counts)],
    pctdistance=0.75,
)
for autotext in autotexts:
  autotext.set_color('white')
  autotext.set_weight('bold')

axes2[2].legend(
    ['Captó más atención (Sí)', 'Igual atención', 'Captó menos (No)'],
    loc='lower center',
    bbox_to_anchor=(0.5, -0.20),
    fontsize=8,
    frameon=False,
)
axes2[2].set_title('Atención: Luz Azul vs. Luz Amarilla', fontweight='bold')

plt.tight_layout()
ruta_fig2 = os.path.abspath('fig2_resultados_icti_luz_azul.png')
fig2.savefig(ruta_fig2, dpi=300, bbox_inches='tight')
plt.close(fig2)
print(f'✅ Figura 2 guardada en: {ruta_fig2}')

# ---------------------------------------------------------
# 2.3 FIGURA 3: Seguridad Vial y Realismo (CORREGIDO 'crest')
# ---------------------------------------------------------
fig3, axes3 = plt.subplots(1, 2, figsize=(14, 5), dpi=300)

# A) Aporte a la Seguridad Vial
seg_counts = df['Aporte Seguridad Vial'].value_counts()
colors_seg = sns.color_palette('crest', len(seg_counts))
bars_seg = axes3[0].bar(seg_counts.index, seg_counts.values, color=colors_seg)

total_seg = seg_counts.sum()
for bar in bars_seg:
  height = bar.get_height()
  pct = (height / total_seg) * 100
  axes3[0].text(
      bar.get_x() + bar.get_width() / 2.0,
      height + (total_seg * 0.015),
      f'{pct:.1f}%',
      ha='center',
      va='bottom',
      fontweight='bold',
      fontsize=9.5,
  )

axes3[0].set_title(
    'Percepción del Aporte a la Seguridad Vial', fontweight='bold'
)
axes3[0].set_xlabel('Grado de Contribución')
axes3[0].set_ylabel('Número de Participantes')
axes3[0].margins(y=0.18)

# B) Realismo del Simulador
real_counts = df['Realismo Simulador (1-5)'].value_counts().sort_index()
colors_real = sns.color_palette('Blues_r', len(real_counts))
bars_real = axes3[1].bar(
    real_counts.index.astype(str), real_counts.values, color=colors_real
)

total_real = real_counts.sum()
for bar in bars_real:
  height = bar.get_height()
  pct = (height / total_real) * 100
  axes3[1].text(
      bar.get_x() + bar.get_width() / 2.0,
      height + (total_real * 0.015),
      f'{pct:.1f}%',
      ha='center',
      va='bottom',
      fontweight='bold',
      fontsize=9.5,
  )

axes3[1].set_title(
    'Evaluación de Realismo del Simulador (Escala 1 a 5)', fontweight='bold'
)
axes3[1].set_xlabel('Calificación de Realismo')
axes3[1].set_ylabel('Número de Participantes')
axes3[1].margins(y=0.18)

plt.tight_layout()
ruta_fig3 = os.path.abspath('fig3_seguridad_y_simulador.png')
fig3.savefig(ruta_fig3, dpi=300, bbox_inches='tight')
plt.close(fig3)
print(f'✅ Figura 3 guardada en: {ruta_fig3}')

print('\n🎉 ¡Proceso completado exitosamente sin errores!')