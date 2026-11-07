import os
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. CONFIGURACIÓN DE RUTAS Y GEOMETRÍA REAL ---
BASE_PATH = os.getcwd()
PARTICIPANTS_FOLDER = os.path.join(BASE_PATH, 'participantes')
OUTPUT_FOLDER = os.path.join(BASE_PATH, 'CFD_acce')
EGO_VEHICLE_ID = 'f_0.0'

# Crear la carpeta de salida si no existe
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# GEOMETRÍA REAL CORREGIDA MILIMÉTRICAMENTE
LANE_LENGTHS = {
    'E2': 1450.96,       # Zona de Información
    'E2.1450': 400.0,    # Comienzo de Zona de Transición
    'E8': 150.0,         # Fin de Zona de Transición
    '-E4.475': 600.0,    # Zona de Construcción
    'E12': 116.0,        # Comienzo de Zona de Redireccionamiento
    'E2.2716': 84.0      # Fin de Zona de Redireccionamiento (Total: 2800.96m)
}

# Límites operativos basados en distancias acumuladas en el eje X
LIMIT_INFO = LANE_LENGTHS['E2']
LIMIT_TRANS = LIMIT_INFO + LANE_LENGTHS['E2.1450'] + LANE_LENGTHS['E8']
LIMIT_CONST = LIMIT_TRANS + LANE_LENGTHS['-E4.475']

ZONE_TITLES = {
    'INFO': 'Zona de Información',
    'TRANS': 'Zona de Transición',
    'CONST': 'Zona de Construcción',
    'REDIR': 'Zona de Redireccionamiento'
}

# Paleta oficial (Amarillo institucional y Azul)
COLORS = {'Y': '#E6A100', 'B': '#0066CC'}

# Mapeo de inicio acumulado por ID de tramo para cálculo de distancia global
STRINGS_ACCUMULATED = {}
current_sum = 0.0
for lane, length in LANE_LENGTHS.items():
    STRINGS_ACCUMULATED[lane] = current_sum
    current_sum += length

def extract_accelerations_from_xml(xml_file_path):
    """
    Parsea las trayectorias de f_0.0 paso a paso, calcula las aceleraciones continuas,
    las filtra y las asigna a la zona geométrica correspondiente por metraje acumulado.
    """
    if not os.path.exists(xml_file_path):
        return None

    time_series_data = []

    try:
        context = ET.iterparse(xml_file_path, events=('end',))
        for event, elem in context:
            if elem.tag == 'timestep':
                for vehicle in elem.findall('vehicle'):
                    if vehicle.get('id') == EGO_VEHICLE_ID:
                        lane_id = vehicle.get('lane', '')
                        base_lane = lane_id.split('_')[0] if lane_id else ''
                        speed_ms = float(vehicle.get('speed', 0.0))
                        pos_within_lane = float(vehicle.get('pos', 0.0))

                        if base_lane in STRINGS_ACCUMULATED:
                            global_dist = STRINGS_ACCUMULATED[base_lane] + pos_within_lane
                            time_series_data.append((global_dist, speed_ms))

                elem.clear()
    except Exception as e:
        print(f"  [!] Error parseando {xml_file_path}: {e}")
        return None

    if len(time_series_data) < 2:
        return {'INFO': None, 'TRANS': None, 'CONST': None, 'REDIR': None}

    # Crear DataFrame temporal para el cálculo de diferenciales (dt = 0.1s)
    df_temp = pd.DataFrame(time_series_data, columns=['global_dist', 'speed_ms'])
    df_temp['accel'] = df_temp['speed_ms'].diff() / 0.1

    # Clasificación por zonas basadas en el metraje real
    zone_accels = {'INFO': [], 'TRANS': [], 'CONST': [], 'REDIR': []}

    for _, row in df_temp.dropna().iterrows():
        g_dist = row['global_dist']
        acc = row['accel']

        # FILTRADO CRÍTICO DE ACELERACIÓN REAL
        if (acc > 0.01) and (acc <= 5.0):
            if g_dist <= LIMIT_INFO:
                zone_accels['INFO'].append(acc)
            elif g_dist <= LIMIT_TRANS:
                zone_accels['TRANS'].append(acc)
            elif g_dist <= LIMIT_CONST:
                zone_accels['CONST'].append(acc)
            elif g_dist <= current_sum:
                zone_accels['REDIR'].append(acc)

    # Obtener el promedio de aceleración por zona
    zone_averages = {}
    for zone_name, acc_list in zone_accels.items():
        zone_averages[zone_name] = np.mean(acc_list) if acc_list else None

    return zone_averages

# --- 2. EXTRACCIÓN GLOBAL Y PROCESAMIENTO ---
print("Iniciando extracción matemática de Aceleraciones con Geometría Corregida...")
all_results = []

if not os.path.exists(PARTICIPANTS_FOLDER):
    print(f"❌ Error: Carpeta 'participantes' no detectada en: {PARTICIPANTS_FOLDER}")
else:
    participant_folders = [f for f in os.listdir(PARTICIPANTS_FOLDER) if os.path.isdir(os.path.join(PARTICIPANTS_FOLDER, f))]
    print(f"🔍 Procesando {len(participant_folders)} participantes...")

    for part_id in participant_folders:
        part_path = os.path.join(PARTICIPANTS_FOLDER, part_id)
        res = {'Participant_ID': part_id}

        # Escenario Luz Amarilla (Y.xml)
        metrics_y = extract_accelerations_from_xml(os.path.join(part_path, 'Y.xml'))
        if metrics_y:
            for zone, val in metrics_y.items():
                res[f'Acc_Y_{zone}'] = val

        # Escenario Luz Azul (B.xml)
        metrics_b = extract_accelerations_from_xml(os.path.join(part_path, 'B.xml'))
        if metrics_b:
            for zone, val in metrics_b.items():
                res[f'Acc_B_{zone}'] = val

        all_results.append(res)

# Guardar DataFrame en Excel dentro de la nueva carpeta
df_final = pd.DataFrame(all_results)
excel_path = os.path.join(OUTPUT_FOLDER, 'Resultados_CFD_Acce.xlsx')
df_final.to_excel(excel_path, index=False)
print(f"✓ Archivo Excel generado con éxito en: {excel_path}")

# --- 3. GENERACIÓN DE CURVAS DE DISTRIBUCIÓN ACUMULADA (CDF) ---
print("\nGenerando las 4 gráficas oficiales de aceleración en formato PDF...")

for zone in ZONE_TITLES.keys():
    plt.figure(figsize=(7, 5))

    col_yellow = f'Acc_Y_{zone}'
    col_blue = f'Acc_B_{zone}'

    valid_y = df_final[col_yellow].dropna() if col_yellow in df_final.columns else pd.Series()
    valid_b = df_final[col_blue].dropna() if col_blue in df_final.columns else pd.Series()

    if not valid_y.empty:
        sns.ecdfplot(x=valid_y, color=COLORS['Y'], linewidth=2.5, label='Luz Amarilla (Y)')
    if not valid_b.empty:
        sns.ecdfplot(x=valid_b, color=COLORS['B'], linewidth=2.5, linestyle='--', label='Luz Azul (B)')

    # Estética y Formato Oficial
    plt.title(f'Distribución de Aceleración -\n{ZONE_TITLES[zone]}', fontsize=11, fontweight='bold', pad=12)
    plt.xlabel('Aceleración Promedio ($m/s^2$)', fontsize=11)
    plt.ylabel('Probabilidad Acumulada (Percentil)', fontsize=11)

    # Ajuste dinámico del eje X para que la curva alcance siempre 1.0
    min_val = min(valid_y.min() if not valid_y.empty else 0.5, valid_b.min() if not valid_b.empty else 0.5)
    max_val = max(valid_y.max() if not valid_y.empty else 3.0, valid_b.max() if not valid_b.empty else 3.0)

    # Aplicamos un margen visual inferior y superior (ej. 0.2 m/s^2) pero evitando negativos si es posible
    plt.xlim(max(0, min_val - 0.2), max_val + 0.2)
    plt.ylim(0, 1.05)

    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='lower right', fontsize=10, frameon=True)
    plt.tight_layout()

    # Nomenclatura oficial (ej: CFD_acce_Info.pdf)
    short_zone_name = zone.capitalize()[:4]
    output_pdf = os.path.join(OUTPUT_FOLDER, f'CFD_acce_{short_zone_name}.pdf')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    plt.close()
    print(f'✓ Gráfica guardada: {output_pdf}')

print("\n¡Framework completado con éxito! Todo tu set de datos ha sido procesado y guardado en la carpeta 'CFD_acce'.")