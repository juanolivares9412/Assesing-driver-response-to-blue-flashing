import os
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. CONFIGURACIÓN DE RUTAS Y GEOMETRÍA REAL ---
BASE_PATH = os.getcwd()
PARTICIPANTS_FOLDER = os.path.join(BASE_PATH, 'participantes')
OUTPUT_FOLDER = os.path.join(BASE_PATH, 'Headmap_CC')
EGO_VEHICLE_ID = 'f_0.0'

# Crear la carpeta de salida si no existe
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

# GEOMETRÍA REAL ACUMULADA
LANE_LENGTHS = {
    'E2': 1450.96,       # Zona de Información
    'E2.1450': 400.0,    # Comienzo de Zona de Transición
    'E8': 150.0,         # Fin de Zona de Transición
    '-E4.475': 600.0,    # Zona de Construcción
    'E12': 116.0,        # Comienzo de Zona de Redireccionamiento
    'E2.2716': 84.0      # Fin de Zona de Redireccionamiento
}

# Calcular los hitos acumulados para las divisiones visuales
STRINGS_ACCUMULATED = {}
current_sum = 0.0
for lane, length in LANE_LENGTHS.items():
    STRINGS_ACCUMULATED[lane] = current_sum
    current_sum += length

TOTAL_DISTANCE = current_sum

# Hitos métricos exactos de las 4 zonas para clasificación
HITO_INFO_FIN = LANE_LENGTHS['E2']
HITO_TRANS_FIN = HITO_INFO_FIN + LANE_LENGTHS['E2.1450'] + LANE_LENGTHS['E8']
HITO_CONST_FIN = HITO_TRANS_FIN + LANE_LENGTHS['-E4.475']

def get_zone_from_distance(distance):
    """Clasifica la zona vial según el metraje acumulado."""
    if distance <= HITO_INFO_FIN:
        return 'Zona 1: Información'
    elif distance <= HITO_TRANS_FIN:
        return 'Zona 2: Transición'
    elif distance <= HITO_CONST_FIN:
        return 'Zona 3: Construcción'
    else:
        return 'Zona 4: Redirección'

def extract_lane_changes(xml_file_path, scenario_name, participant_id):
    """Extrae cambios de carril, calcula la dirección y asigna la zona."""
    events = []
    if not os.path.exists(xml_file_path):
        return events
    try:
        context = ET.iterparse(xml_file_path, events=('end',))
        last_lane = None
        for event, elem in context:
            if elem.tag == 'timestep':
                for vehicle in elem.findall('vehicle'):
                    if vehicle.get('id') == EGO_VEHICLE_ID:
                        current_lane = vehicle.get('lane', '')

                        if current_lane and last_lane and current_lane != last_lane:
                            base_lane = current_lane.split('_')[0]
                            pos_within_lane = float(vehicle.get('pos', 0.0))

                            # Determinar dirección de cambio (Índice mayor = Izquierda)
                            try:
                                last_idx = int(last_lane.split('_')[-1])
                                curr_idx = int(current_lane.split('_')[-1])
                                if curr_idx > last_idx:
                                    direction = 'Derecha a Izquierda'
                                else:
                                    direction = 'Izquierda a Derecha'
                            except ValueError:
                                direction = 'Desconocida'

                            if base_lane in STRINGS_ACCUMULATED:
                                global_distance = STRINGS_ACCUMULATED[base_lane] + pos_within_lane
                                zone = get_zone_from_distance(global_distance)

                                events.append({
                                    'Participante': participant_id,
                                    'Escenario': scenario_name,
                                    'Zona': zone,
                                    'Dirección': direction,
                                    'Distancia_m': round(global_distance, 2)
                                })
                        last_lane = current_lane
                elem.clear()
    except Exception as e:
        print(f"Error procesando {xml_file_path}: {e}")
    return events

# --- 2. EXTRACCIÓN MASIVA DE EVENTOS ---
print("Detectando maniobras cinemáticas de cambio de carril (CC)...")
all_events = []
if os.path.exists(PARTICIPANTS_FOLDER):
    participant_folders = [f for f in os.listdir(PARTICIPANTS_FOLDER) if os.path.isdir(os.path.join(PARTICIPANTS_FOLDER, f))]
    for part_id in participant_folders:
        part_path = os.path.join(PARTICIPANTS_FOLDER, part_id)
        all_events.extend(extract_lane_changes(os.path.join(part_path, 'Y.xml'), 'Luz Amarilla (Y)', part_id))
        all_events.extend(extract_lane_changes(os.path.join(part_path, 'B.xml'), 'Luz Azul (B)', part_id))

df_lc = pd.DataFrame(all_events)

if df_lc.empty:
    print("⚠️ No se detectaron datos. Verifica las rutas corporativas.")
else:
    # --- 3. GENERACIÓN DE REPORTE EXCEL ---
    excel_path = os.path.join(OUTPUT_FOLDER, 'Headmap_CC.xlsx')

    # Crear un resumen agregado
    df_summary = df_lc.groupby(['Zona', 'Escenario', 'Dirección']).size().reset_index(name='Total_Cambios')

    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Resumen_Zonas', index=False)
        df_lc.to_excel(writer, sheet_name='Registro_Detallado', index=False)

    print(f"✓ Archivo Excel con detalle de direcciones guardado en: {excel_path}")

    # --- 4. ALGORITMO DE MAPA DE CALOR ---
    dmin, dmax = 0, int(TOTAL_DISTANCE)
    n_bins = 600
    grid = np.linspace(dmin, dmax, n_bins)
    decay_m = 50.0

    def nearest_event_distance(grid_vals, event_positions):
        if event_positions.size == 0: return np.full_like(grid_vals, np.inf)
        x = np.sort(event_positions)
        idxs = np.searchsorted(x, grid_vals, side="left")
        idx_left = np.clip(idxs - 1, 0, len(x) - 1)
        idx_right = np.clip(idxs, 0, len(x) - 1)
        return np.minimum(np.abs(grid_vals - x[idx_left]), np.abs(grid_vals - x[idx_right]))

    rows, index_labels = [], []
    # Aseguramos el orden consistente de los ejes en la gráfica
    for scen in ['Luz Amarilla (Y)', 'Luz Azul (B)']:
        if scen in df_lc['Escenario'].values:
            events = df_lc[df_lc['Escenario'] == scen]['Distancia_m'].to_numpy()
            intensity = np.exp(-nearest_event_distance(grid, events) / decay_m)
            rows.append(intensity)
            index_labels.append(scen)

    heatmap_data = pd.DataFrame(rows, index=index_labels, columns=np.round(grid, 1))

    # --- 5. GRAFICACIÓN AVANZADA CON HITOS DE TRÁNSITO ---
    fig, ax = plt.subplots(figsize=(14, 5.5))

    sns.heatmap(
        heatmap_data, cmap="coolwarm", cbar=True, vmin=0.0, vmax=1.0, ax=ax,
        cbar_kws={'label': 'Intensidad de Cambios de Carril', 'orientation': 'horizontal', 'pad': 0.15}
    )

    # Mapeo de coordenadas del Grid para posicionar las líneas verticales de forma exacta
    def m_to_grid_idx(meters):
        return np.argmin(np.abs(grid - meters))

    # Dibujar líneas divisorias de infraestructura vial
    idx_info = m_to_grid_idx(HITO_INFO_FIN)
    idx_trans = m_to_grid_idx(HITO_TRANS_FIN)
    idx_const = m_to_grid_idx(HITO_CONST_FIN)

    ax.axvline(x=idx_info, color='black', linestyle='--', linewidth=1.8, alpha=0.8)
    ax.axvline(x=idx_trans, color='black', linestyle='--', linewidth=1.8, alpha=0.8)
    ax.axvline(x=idx_const, color='black', linestyle='--', linewidth=1.8, alpha=0.8)

    # Inyección de Etiquetas de Texto Flotante (Estructura de Carretera)
    ax.text(idx_info / 2, -0.12, "ZONA DE INFORMACIÓN", ha='center', va='center', fontsize=9, fontweight='bold', color='#333333')
    ax.text(idx_info + (idx_trans - idx_info) / 2, -0.12, "ZONA DE TRANSICIÓN", ha='center', va='center', fontsize=9, fontweight='bold', color='#333333')
    ax.text(idx_trans + (idx_const - idx_trans) / 2, -0.12, "ZONA DE CONSTRUCCIÓN", ha='center', va='center', fontsize=9, fontweight='bold', color='#333333')
    ax.text(idx_const + (n_bins - idx_const) / 2, -0.12, "ZONA DE REDIRECCIÓN", ha='center', va='center', fontsize=9, fontweight='bold', color='#333333')

    # Ajustes finos de formato del Eje X
    ax.set_xlabel("Distancia Recorrida (m)", fontsize=11, labelpad=8)
    ax.set_ylabel("Escenario", fontsize=11)

    tick_step = 40
    ax.set_xticks(np.arange(0, n_bins, tick_step))
    ax.set_xticklabels([f"{int(grid[i])}" for i in np.arange(0, n_bins, tick_step)], rotation=0, fontsize=9)

    plt.title("Mapa de Calor de Cambios de Carril (CC)", fontsize=13, fontweight='bold', pad=35)

    output_pdf = os.path.join(OUTPUT_FOLDER, 'Headmap_CC.pdf')
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    plt.close()

    print(f"✓ ¡Mapa de calor guardado con éxito en PDF!: {output_pdf}")
    print("\n¡Todo tu entorno analítico está ahora 100% unificado, corregido y estandarizado! 🚀")