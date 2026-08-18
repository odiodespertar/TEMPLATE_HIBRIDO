import json
import io
import pandas as pd
import streamlit as st 
from streamlit.components.v1 import html  
from supabase import create_client
from reglas import reglas_ruteo, MAPA_ORIGENES, PREGUNTAS_FRECUENTES

st.set_page_config(page_title="Monitor Logístico - Liliana García", layout="wide", initial_sidebar_state="collapsed")

# 🟢 INYECCIÓN LIMPIA DIRECTA AL DOM PARA OCULTAR ELEMENTOS NATIVOS
st.markdown("""
    <script>
        try {
            const css = `
                [data-testid="stViewerBadge"],
                .stAppViewerBlock,
                div[class*="stViewerBadge"],
                iframe[title="streamlit_badge"],
                footer,
                header[data-testid="stHeader"] {
                    display: none !important;
                    visibility: hidden !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                }
            `;
            const style = window.parent.document.createElement('style');
            style.type = 'text/css';
            style.appendChild(window.parent.document.createTextNode(css));
            window.parent.document.head.appendChild(style);
        } catch (e) {
            console.log("Ignorado");
        }
    </script>
""", unsafe_allow_html=True)

URL_MAPA = "https://drive.google.com/thumbnail?id=1M4GLEwFzhLrZjV-zmvGrdTQhC6IjwxOJ&sz=w1000"

# ==========================================
# CONEXIÓN ANÓNIMA Y LECTURA DE NOTAS DE SUPABASE
# ==========================================
@st.cache_resource
def init_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        return None

supabase = init_supabase()

def obtener_notas_svc():
    """Consulta todas las notas de SVC almacenadas en Supabase."""
    if not supabase:
        return []
    try:
        response = supabase.table("notas_svc").select("*").execute()
        return response.data
    except Exception as e:
        return []

# ==========================================
# CSS GENERAL DE LA APLICACIÓN
# ========================================== 
st.markdown("""
    <style>
    header, header[data-testid="stHeader"], .stAppHeader, div[data-testid="stToolbar"],
    footer, .stAppFooter, #MainMenu, section[data-testid="stSidebar"],
    button[title="View app source"], button[title="Edit this app"], a[href*="github.com"],
    [data-testid="stViewerBadge"], .stAppViewerBlock, div[class*="stViewerBadge"],
    iframe[title="streamlit_badge"] {
        display: none !important;
        visibility: hidden !important;
        height: 0px !important;
        padding: 0px !important;
        margin: 0px !important;
        opacity: 0 !important;
    }

    html, body, .stApp {
        overflow-x: hidden !important;
        background-color: #25282b;
    }
    
    .main .block-container, div[data-testid="stAppViewBlockContainer"] {
        margin-top: -4rem !important;
        padding-bottom: 0rem !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    .block-container { padding: 0rem !important; }
    .poligono-bloque {
        letter-spacing: -0.2px; 
        white-space: nowrap;    
        zoom: 0.95; 
    }
    table {
        table-layout: fixed;
        width: 100%;
        word-wrap: break-word;
    }
    </style>
""", unsafe_allow_html=True)

# --- DATOS BASE DE RUTEOS Y PLANES ---
u_SDE = {"Moto Car - 3": [25, 30], "Moto Car Newbie": [25, 25], "Car - 5h": [25, 30], "Car - 5 Extendida": [25, 30], "Car - 3h": [25, 28]}

u_PREC = {      
    "Car - 8h": [70, 75],
    "Small 9h Ext Car": [70, 75] 
}

NOMBRES_PLANES_PREC = ["CHALCO", "COYOACÁN", "IZTAPALAPA", "MILPA ALTA", "TLAHUAC", "TLALPAN NORTE", "TLALPAN SUR", "XOCHIMILCO"]

u_PREC_SMX2 = {
    "Car - 8h": [70, 75],
    "Small 9h Ext Car": [70, 75],
    "Car Zona Extendida": [65, 65]
}
NOMBRES_PLANES_PREG = ["CHALCO", "CHIMAS", "IXTAPALUCA VALLE CHALCO", "IZTAPALAPA 1", "IZTAPALAPA 2", "LA PAZ", "PUEBLOS", "TEXCOCO"]

NOMBRES_PLANES_C1 = [
    "CALKINI", "CAMPECHE", "CANDELARIA", "CHAMPOTÓN", "ESCÁRCEGA",
    "ESCÁRCEGA EXT", "HOLPECHEN", "MAXCANUN", "SEYBAPLAYA", "PLAN 10", "PLAN 11"
]

u_C1 = {
    "Rental Large Van": [100, 100], "Large Van MLP": [100, 100], "Small Van MLP":[100, 100], "Delivery Cell Large Van": [1, 1], "Delivery Cell Small Van": [1, 1]
}

u_C1_SJA1 = { 
    "Small Van MLP foráneo": [110, 120], "Large Van MLP foráneo": [110, 120], "Car MLP": [80, 100],
    "Extra Large Van MLP H&B": [70, 70], "Rental Electric Large Van": [150, 150], "Rental Large Van": [120, 120],
    "Rental Replacement": [120, 120], "Truck 3.5 tons MLP": [1, 1], "Delivery Cell Large Van": [1, 1],
    "Car 8h": [70, 70], "Car Newbie": [70, 70], "Car Zona Extendida": [70, 70], "Moto 3h": [30, 30],
    "Small Van 9h": [70, 70], "Small Van 9h Ext": [70, 70], "Small Van Newbie": [70, 70], "Media Milla SP": [1, 1]
}

NOMBRES_PLANES_C1_SJA1 = [
   "ACTOPAN", "⚠️ CENTRO 1", "⚠️ CENTRO 2", "EJA1 SP", "MISANTLA", "NAOLINCO", "PEROTE", "TEZUITLAN", "TLALTETELA", "TRAPICHE",  
   "TUZAMAPA", "XICO", "CONTINGENCIA CENTRO NODO", "CONTINGENCIA TUZAMAPA", "CONTINGENCIA XICO", "PLAN 16", "PLAN 17"
]

u_C1_SCH1 = { 
    "Car MLP": [110, 120], "Small Van MLP": [110, 120], "Large Van MLP": [110, 120], "Small Van MLP Newbie": [110, 120],
    "Large Van MLP Newbie": [110, 120], "Extra large Van MLP": [110, 120], "Small Van MLP XPT": [110, 120],
    "Small Van MLP foráneo": [110, 120], "Large Van MLP foráneo": [110, 120], "Car MLP foráneo": [110, 120],
    "Extra large Van MLP H&B": [100, 100], "Rental Car": [120, 150], "Rental Electric Large Van": [120, 150],
    "Rental Large Van": [120, 150], "Rental Replacement": [120, 150], "Rental Small Van Electrica": [120, 150],
    "Rental Small Van": [120, 150], "Delivery Cells Car": [1, 1], "Truck 3.5 tons MLP": [1, 1],
    "Delivery Cell Large Van": [1, 1], "Car 8h": [70, 70], "Car Newbie": [50, 50], "Car Zona Extendida": [60, 60],
    "Moto 3h": [30, 30], "Moto Newbie": [25, 25], "Small Van 11h Ext": [70, 70], "Small Van 9h": [70, 70],
    "Small Van 9h Ext": [70, 70], "Small Van Newbie": [70, 70]
}

NOMBRES_PLANES_C1_SCH1 = [
   "AEROPUERTO", "CANTERA", "DELICIAS", "GRANJAS", "MEOQUI", "NORTE", "SUR", "CUAUHTEMOC", "PARRAL", "PLAN 10",  
   "PLAN 11", "PLAN 12", "PLAN 13", "PLAN 14"
]

u_C1_VACIA = { 
    "Car MLP": [110, 120], "Small Van MLP": [110, 120], "Large Van MLP": [110, 120], "Small Van MLP Newbie": [110, 120],
    "Large Van MLP Newbie": [110, 120], "Extra large Van MLP": [110, 120], "Small Van MLP XPT": [110, 120],
    "Small Van MLP foráneo": [110, 120], "Large Van MLP foráneo": [110, 120], "Car MLP foráneo": [110, 120],
    "Extra large Van MLP H&B": [100, 100], "Rental Car": [120, 150], "Rental Electric Large Van": [120, 150],
    "Rental Large Van": [120, 150], "Rental Replacement": [120, 150], "Rental Small Van Electrica": [120, 150],
    "Rental Small Van": [120, 150], "Delivery Cells Car": [1, 1], "Truck 3.5 tons MLP": [1, 1],
    "Delivery Cell Large Van": [1, 1], "Car 8h": [70, 70], "Car Newbie": [50, 50], "Car Zona Extendida": [60, 60],
    "Car 3h": [30,30], "Car 5h": [30, 30], "Moto 3h": [30, 30], "Moto Newbie": [25, 25], "Small Van 11h Ext": [70, 70],
    "Small Van 9h": [70, 70], "Small Van 9h Ext": [70, 70], "Small Van Newbie": [70, 70]
}

NOMBRES_PLANES_C1_VACIA = [
   "PLAN 1", "PLAN 2", "PLAN 3", "PLAN 4", "PLAN 5", "PLAN 6", "PLAN 7", "PLAN 8", "PLAN 9", "PLAN 10",  
   "PLAN 11", "PLAN 12", "PLAN 13", "PLAN 14"
]

u_C1_SMD1 = { 
    "Car MLP": [110, 120], "Small Van MLP": [110, 120], "Large Van MLP": [110, 120], "Small Van MLP Newbie": [110, 120],
    "Large Van MLP Newbie": [110, 120], "Extra large Van MLP": [110, 120], "Small Van MLP XPT": [110, 120],
    "Small Van MLP foráneo": [110, 120], "Large Van MLP foráneo": [110, 120], "Large Van MLP Bulk": [100, 100],
    "Extra large Van MLP H&B": [50, 50], "Rental Car": [120, 150], "Rental Electric Large Van": [120, 150],
    "Rental Large Van": [120, 150], "Rental Replacement": [120, 150], "Rental Small Van Electrica": [120, 150],
    "Rental Small Van": [120, 150], "Delivery Cells Car": [1, 1], "Truck 3.5 tons MLP": [1, 1],
    "Delivery Cell Large Van": [1, 1], "Car 8h": [70, 70], "Car Newbie": [50, 50], "Car Zona Ext 10h": [70, 70],
    "Moto 3h": [30, 30], "Moto Newbie": [25, 25], "Small Van 11h Ext": [70, 70], "Small Van 9h": [70, 70],
    "Small Van 9h Ext": [70, 70], "Small Van Newbie": [70, 70]
}

NOMBRES_PLANES_C1_SMD1 = [
   "⚠️ CENTRO 1", "⚠️ CENTRO 2", "⚠️ KANASIN", "MOTUL", "MUNA", "⚠️ NORTE", "SEYE", "UMAN", "PLAN 9", "PLAN 10",  
   "PLAN 11", "PLAN 12", "PLAN 13", "PLAN 14"
]

def gen_master_rows(data_dict, table_id):
    rows = ""
    items = list(data_dict.items())
    total_items = len(items)

    nombres_prec = ["CHALCO", "COYOACÁN", "IZTAPALAPA", "MILPA ALTA", "TLAHUAC", "TLALPAN NORTE", "TLALPAN SUR", "XOCHIMILCO"]
    nombres_smx2 = ["CHALCO", "CHIMAS", "IXTAPALUCA VALLE CHALCO", "IZTAPALAPA 1", "IZTAPALAPA 2", "LA PAZ", "PUEBLOS", "TEXCOCO"]

    mostrar_orh_ocup = (table_id in [1, 2, 6, 7, 8, 5, 9])
    num_filas_objetivo = 45 if table_id == "PREC" else 3
    rango_final = max(total_items, num_filas_objetivo)

    for i in range(1, rango_final + 1):
        if (data_dict == u_PREC) and (i-1) < len(nombres_prec):
            p_name = nombres_prec[i-1]
        elif (data_dict == u_PREC_SMX2) and (i-1) < len(nombres_smx2):
            p_name = nombres_smx2[i-1]
        else:
            p_name = f"PLAN {i}"

        if (i-1) < total_items:
            name, spr = items[i-1]
        else:
            name, spr = "", [0, 0]

        if "---" in name:
            colspan = 8 if mostrar_orh_ocup else 5
            rows += f'''
            <tr class="es-divisor" style="background: #25282b !important; color: #25282b; height: 28px;">
                <td colspan="{colspan}" style="text-align: center; font-weight: bold; font-size: 13px; letter-spacing: 3px; border: none; pointer-events: none;"> 
                    {name}
                </td>
                <td class="edit-name" style="display:none;">IGNORAR</td>
                <td class="edit-spr-min" style="display:none;">0</td>
                <td class="edit-spr-max" style="display:none;">0</td>
                <td class="edit-orh" style="display:none;">0</td>
                <td class="edit-ocup" style="display:none;">0</td>
                <td class="f-stock" style="display:none;">0</td>
                <td class="f-left" style="display:none;">0</td>
            </tr>'''
        else:
            st_base = "background: #ebebeb; color: #969696;" if not name else ""
            if mostrar_orh_ocup:
                celdas_orh_ocup = f'''
                <td contenteditable="true" class="edit-orh" oninput="recalc()" style="text-align:center; border:0.2px solid #25282b; width:45px; background:#ffffff; color:#141414;">0</td>
                <td class="orh-hora" style="text-align:center; border:0.2px solid #25282b; width:60px; background:#f5f5f5; color:#141414; font-weight:bold;">00:00 hs</td>
                <td contenteditable="true" class="edit-ocup" oninput="recalc()" style="text-align:center; border:0.2px solid #25282b; width:70px; background:#ffffff; color:#25282b;">0</td>
                '''
            else:
                celdas_orh_ocup = '''
                <td class="edit-orh" style="display:none;">0</td>
                <td class="orh-hora" style="display:none;">00:00 hs</td>
                <td class="edit-ocup" style="display:none;">0</td>
                '''

            rows += f'''
            <tr class="master-row" style="{st_base}">
                <td contenteditable="true" class="edit-name" oninput="recalc()" style="font-weight: bold; text-align: left; padding-left: 10px; border: 0.2px solid #25282b; width: 150px; color: #25282b;">{name}</td>
                {celdas_orh_ocup}
                <td contenteditable="true" class="edit-spr-min" oninput="recalc()" style="text-align: center; border: 0.2px solid #25282b; width: 45px; background-color: #25282b; color: #ffffff;">{spr[0]}</td>
                <td contenteditable="true" class="edit-spr-max" oninput="recalc()" style="text-align: center; border: 0.2px solid #25282b; width: 45px; background-color: #25282b; color: #ffffff;">{spr[1]}</td>
                <td contenteditable="true" class="f-stock" oninput="recalc()" style="text-align: center; border: 0.2px solid #25282b; width: 55px; font-weight: bold; font-size: 13px;">0</td>
                <td class="f-ruteadas" style="text-align: center; border: 0.2px solid #25282b; width: 55px; background-color: #ffffff; font-weight: bold;">0</td>
                <td class="f-left" style="text-align:center; border:0.2px solid #25282b; width:45px; font-weight:bold; color:#25282b; border-radius:2px;">0</td>
            </tr>'''
    return rows

def gen_poligonos(data_target=None):
    polys = ""
    btn_s = "cursor:pointer; border:none; background:rgba(0,0,0,0.08); color:#25282b; font-weight:bold; width:24px; min-width:24px; max-width:24px; height:24px; min-height:24px; max-height:24px; border-radius:4px; flex-shrink:0; display:inline-flex; align-items:center; justify-content:center;"
    
    nombres_prec = ["CHALCO", "COYOACÁN", "IZTAPALAPA", "MILPA ALTA", "TLAHUAC", "TLALPAN NORTE", "TLALPAN SUR", "XOCHIMILCO"]
    nombres_smx2 = ["CHALCO", "CHIMAS", "IXTAPALUCA VALLE CHALCO", "IZTAPALAPA 1", "IZTAPALAPA 2", "LA PAZ", "PUEBLOS", "TEXCOCO"]

    es_c1 = data_target in (u_C1, u_C1_SJA1, u_C1_SCH1, u_C1_SMD1, u_C1_VACIA)
    es_sde = (data_target == u_SDE)
    es_prec = (data_target == u_PREC)

    div_flex = "display: flex; align-items: center; justify-content: space-between; padding: 2px 4px; width: 100%; min-width: 100%; max-width: 100%; box-sizing: border-box;"
    span_num_u = "font-weight: bold; display: inline-block; text-align: center; width: 28px; min-width: 28px; max-width: 28px; flex-shrink: 0;"
    span_num_spr = "font-weight: bold; display: inline-block; text-align: center; width: 38px; min-width: 38px; max-width: 43px; flex-shrink: 0;"
    select_style = "width:160px; max-width: 160px; border:none; background:transparent; font-weight:600; font-size:14px; color:#25282b; padding: 4px; cursor: pointer;"

    fila_inner = f'''
    <tr class="calc-row">
        <td class="u-manual-cell" style="background: #d3f0e5; border: 0.6px solid #25282b; padding: 2px; width: 105px;">
            <div style="{div_flex}">
                <button style="{btn_s}" onclick="stepVal(this, -1, 'u')">-</button>
                <span contenteditable="true" class="u-manual" oninput="manualEdit(this)" style="{span_num_u}color: #25282b !important;">0</span>
                <button style="{btn_s}" onclick="stepVal(this, 1, 'u')">+</button>
            </div>
        </td>
        <td class="spr-real-cell" style="background: #FFFFFF; border: 0.6px solid #25282b; padding: 2px; width: 90px;">
            <div style="{div_flex}">
                <button style="{btn_s}" onclick="stepVal(this, -1, 's')">-</button>
                <span contenteditable="true" class="spr-real-val" oninput="manualEdit(this)" style="{span_num_spr} color: #25282b !important;">0</span>
                <button style="{btn_s}" onclick="stepVal(this, 1, 's')">+</button>
            </div>
        </td>
        <td style="border: 0.5px solid #25282b; padding: 2px; width: 170px;">
            <select class="s-type" onchange="resetRow(this); updateSelectColor(this);" style="{select_style} color: #808080;"> 
                <option value="">Seleccionar...</option>
            </select>
        </td>
        <td style="width: 45px; text-align: center; border: 0.5px solid #25282b;"><input type="checkbox" class="ok-check" style="transform: scale(1.7); accent-color: #9ACD32; cursor: pointer;"></td>
    </tr>'''

    campo_volumen_normal = '''<div style="text-align:center;"><span class="v-total-val" contenteditable="true" oninput="recalc()" style="display:inline-block; min-width:55px; padding:2px 8px; border:none; border-radius:4px; background:#ededed; font-size:22px; font-weight:bold; color:#808080; text-align:center;">0</span></div>'''

    campo_volumen_c1 = '''
<div style="text-align:center;"><span class="v-total-val" contenteditable="true" oninput="recalc()" style="display:inline-block; min-width:55px; padding:2px 8px; border:none; border-radius:4px; background:#ededed; font-size:22px; font-weight:bold; color:#808080; text-align:center;">0</span></div>
<hr style="margin:4px 0; border:none; border-top:2px solid #999;">
<div style="font-size:12px; font-weight:bold; color:#25282b; text-align:center;">
    <div>Nodos:</div>
    <span class="nodos-val" contenteditable="true" style="display:inline-block; min-width:28px; text-align:center; border:none; border-radius:4px; background:#ededed; font-size:16px; font-weight:bold; color:#FF6347; padding:0 4px; margin-top:2px;">0</span>
</div>
'''

    campo_campeche = '''
<div style="text-align:center;"><span class="v-total-val" contenteditable="true" oninput="recalc()" style="display:inline-block; min-width:55px; padding:2px 8px; border-radius:4px; background:#ededed; font-size:22px; font-weight:bold; color:#808080; text-align:center;">0</span></div>
<hr style="margin:4px 0; border:none; border-top:1px solid #999;">
<div style="font-size:13px; font-weight:bold; color:#25282b; text-align:center;">Nodos:
    <div style="margin-top:2px;"><span class="nodos-campeche" contenteditable="true" style="display:inline-block; min-width:28px; text-align:center; border:none; border-radius:4px; background:#ededed; font-size:16px; font-weight:bold; color:#FF6347; padding:0 4px;">0</span></div>
</div>
'''

    if data_target == u_C1_SJA1:
        limite_tablas = len(NOMBRES_PLANES_C1_SJA1) + 1
    elif data_target in (u_C1_SCH1, u_C1_VACIA):
        limite_tablas = 16
    elif data_target == u_C1_SMD1:
        limite_tablas = 20
    elif es_sde:
        limite_tablas = 5
    else:
        limite_tablas = 20
    
    for i in range(1, limite_tablas): 
        if data_target == u_C1_VACIA and (i-1) < len(NOMBRES_PLANES_C1_VACIA):
            nombre_final = NOMBRES_PLANES_C1_VACIA[i-1]
        elif data_target == u_PREC and (i-1) < len(nombres_prec):
            nombre_final = nombres_prec[i-1]
        elif data_target == u_PREC_SMX2 and (i-1) < len(nombres_smx2):
            nombre_final = nombres_smx2[i-1]
        elif data_target == u_C1 and (i-1) < len(NOMBRES_PLANES_C1):
            nombre_final = NOMBRES_PLANES_C1[i-1]
        elif data_target == u_C1_SJA1 and (i-1) < len(NOMBRES_PLANES_C1_SJA1):
            nombre_final = NOMBRES_PLANES_C1_SJA1[i-1]
        elif data_target == u_C1_SCH1 and (i-1) < len(NOMBRES_PLANES_C1_SCH1):
            nombre_final = NOMBRES_PLANES_C1_SCH1[i-1]
        elif data_target == u_C1_SMD1 and (i-1) < len(NOMBRES_PLANES_C1_SMD1):
            nombre_final = NOMBRES_PLANES_C1_SMD1[i-1]
        else:
            nombre_final = f"PLAN {i}"

        if nombre_final == "CAMPECHE":
            contenido_volumen = campo_campeche
        elif es_c1:
            contenido_volumen = campo_volumen_c1
        else:
            contenido_volumen = campo_volumen_normal

        if es_sde or es_prec:
            rowspan_actual = 3
        elif data_target == u_C1_SJA1:
            rowspan_actual = 8 if nombre_final == "⚠️ CENTRO 1" else 5
        elif data_target in (u_C1_SMD1, u_C1_VACIA):
            rowspan_actual = 5
        else:
            rowspan_actual = 3

        if es_sde or es_prec:
            filas_extra = fila_inner * 2
        elif data_target == u_C1_SJA1:
            filas_extra = fila_inner * 7 if nombre_final == "⚠️ CENTRO 1" else fila_inner * 4
        elif data_target in (u_C1_SMD1, u_C1_VACIA):
            filas_extra = fila_inner * 4
        else:
            filas_extra = fila_inner * 2

        polys += f'''
        <div class="poligono-bloque" style="margin-bottom:12px; background: #ededed; border: 1.5px solid #25282b;">           
            <table style="width: 100%; min-width: 630px; border-collapse: collapse; border: 1.5px solid #25282b;">
                <thead>
                    <tr style="background: #25282b; color: white; font-size: 12px; height: 28px;">                        
                        <th style="padding: 0 10px; border-right: 1px solid #25282b; width: 130px;">PLAN</th>
                        <th style="border-right: 1px solid #25282b; width: 85px;">VOL. TOTAL</th>
                        <th style="width: 105px; border-right: 1px solid #25282b;"># USADAS</th>
                        <th style="width: 105px; border-right: 1px solid #25282b;">SPR</th>
                        <th style="width: 180px; border-right: 1px solid #25282b;">TIPO DE UNIDAD</th>
                        <th style="width: 45px; text-align: center;">OK</th> 
                    </tr>
                </thead>
                <tbody>
                    <tr class="calc-row"> 
                        <td class="plan-cell" rowspan="{rowspan_actual}" contenteditable="true" style="background: #dcdcdc; font-weight: bold; text-align:center; border: 1px solid #25282b; padding: 5px; color:#141414;">{nombre_final}</td>
                        <td class="vol-cell" rowspan="{rowspan_actual}" style="color:#808080; font-weight:bold; text-align:center; border:1px solid #25282b; padding:5px;">
                            {contenido_volumen}
                        </td>
                        <td class="u-manual-cell" style="background: #d3f0e5; border: 0.5px solid #25282b; padding: 2px; width: 105px;">
                            <div style="{div_flex}">
                                <button style="{btn_s}" onclick="stepVal(this, -1, 'u')">-</button> 
                                <span contenteditable="true" class="u-manual" oninput="manualEdit(this)" style="{span_num_u} color: #25282b !important;">0</span>
                                <button style="{btn_s}" onclick="stepVal(this, 1, 'u')">+</button>
                            </div>
                        </td>
                        <td class="spr-real-cell" style="background: #FFFFFF; border: 0.5px solid #25282b; padding: 2px; width: 90px;">
                            <div style="{div_flex}">
                                <button style="{btn_s}" onclick="stepVal(this, -1, 's')">-</button>
                                <span contenteditable="true" class="spr-real-val" oninput="manualEdit(this)" style="{span_num_spr}">0</span>
                                <button style="{btn_s}" onclick="stepVal(this, 1, 's')">+</button>
                            </div>
                        </td>
                        <td style="border: 0.5px solid #25282b; padding: 2px;">
                            <select class="s-type" onchange="resetRow(this)" style="{select_style}">
                                <option>Seleccionar...</option>
                            </select>
                        </td>
                        <td style="width: 45px; text-align: center; border: 0.5px solid #25282b;"><input type="checkbox" class="ok-check" style="transform: scale(1.7); accent-color: #9ACD32; cursor: pointer;"></td>
                    </tr>
                    {filas_extra}
                    <tr style="background:#ededed; height: 32px;">
                        <td colspan="3" style="text-align:center; font-weight:bold; border: 1px solid #25282b; font-size: 14px; color:#25282b;">ESTADO:</td>
                        <td class="v-calculado-total" style="font-weight: bold; font-size: 14px; color: #d32f2f; border: 1px solid #25282b; text-align: center;">0</td>
                        <td class="p-diff delta" colspan="2" style="text-align: center; font-weight: bold; border: 1px solid #25282b; font-size: 14px; color: #25282b">VACÍO:</td>
                    </tr>
                </tbody>
                <div style="text-align:center; padding:5px; background:#ededed;">
                    <button onclick="agregarFilaPlan(this)" style="cursor:pointer; margin-right:5px;">➕</button>
                    <button onclick="quitarFilaPlan(this)" style="cursor:pointer;">➖</button>
                    <span class="contador-filas" style="margin-left:10px;font-weight:bold;">Filas: {rowspan_actual}</span>
                </div>     
            </table>
        </div>'''
    return polys

reglas_json = json.dumps(reglas_ruteo)
mapa_origenes_json = json.dumps(MAPA_ORIGENES)
preguntas_faq_json = json.dumps(PREGUNTAS_FRECUENTES)
notas_svc_json = json.dumps(obtener_notas_svc())

app_html = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
    <style>
        tr.master-row:hover, tr.calc-row:hover {{
            background-color: #fffecd !important;
            box-shadow: inset 0 0 2px #ffc107 !important;
            transition: background-color 0.15s ease;
            cursor: pointer;
        }}
        tr.master-row:hover td, tr.calc-row:hover td {{ color: #000 !important; }}

        body {{ font-family: sans-serif; background: #ffffff; padding: 14px; margin: 0; }}

        .meli-table {{
            width: 100% !important; 
            border-collapse: collapse !important;
            table-layout: fixed;
            background: white;
            border: 1px solid #25282b;
        }}

        .meli-table th {{
            background: #f3f3f3 !important;
            color: #222 !important;
            font-size: 14px;
            font-weight: 600;
            border: 1px solid #25282b !important;
            padding: 4px 6px;
            text-align: center;
        }}

        .meli-table td {{
            border: 1px solid #25282b;
            padding: 2px 4px;
            font-size: 14px;
            height: 24px;
            background: white;
            color: #25282b;
        }}

        #fleet-sticky.fleet-floating {{
            position: fixed !important;
            top: 170px;
            left: 50% !important;
            transform: translateX(-50%);
            width: min(1050px, 92vw) !important;
            max-height: 370px !important;
            overflow: hidden !important;
            z-index: 999999 !important;
            background: #ffffff !important;
            border: 3px solid #25282b !important;
            border-radius: 10px !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.50) !important;
            padding: 6px !important;
        }}

        #google-alert {{ 
            position: fixed; top: -100px; left: 50%; transform: translateX(-50%);
            background: #d32f2f; color: white; padding: 15px 25px; border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3); transition: 0.4s; z-index: 10000;
        }}
        #google-alert.show {{ top: 20px; }}

        /* MODO EXCEL */
        body.excel-view #fleet-float, body.excel-view #ruteo-float {{ display: none !important; }}
        body.excel-view .meli-table td {{ padding: 2px 3px !important; font-size: 14px !important; }}
    </style> 
</head>

<body>
<div id="google-alert">⚠️ <span id="alert-msg"></span> [ENTER para cerrar]</div>
<div style="display:flex; flex-direction:column; gap:20px; width:100%;">

<!-- PANEL SUPERIOR -->
<div style="width:100%; padding:0; margin-bottom:10px;">

    <!-- 🟢 SELECTOR DE RUTEO DE LA PANTALLA PRINCIPAL (TEMPLATE ANTERIOR) -->
    <div style="background-color: #25282b; color: white; padding: 12px; border-radius: 6px; font-weight: bold; text-align: center; margin-bottom: 10px; border: 1px solid #3b3f43; display: flex; flex-direction: column; align-items: center; gap: 8px;">
        <div style="font-size: 11px; color: #20B2AA; letter-spacing: 1.5px; text-transform: uppercase;">
            📌 SELECCIONAR RUTEO EN PANTALLA
        </div>
        <select id="ciclo-selector" onchange="cambiarCiclo(this.value)" style="background: #ffffff; color: #000000; border: 2px solid #20B2AA; padding: 6px 15px; border-radius: 6px; font-size: 16px; font-weight: bold; outline: none; cursor: pointer; width: 280px; text-align-last: center;">
            <option value="4" selected>🟢 EXTENDIDO</option>
            <option value="2">🟠 C1 SCP1</option>
            <option value="6">🔴 C1 SJA1</option>
            <option value="7">🔴 C1 SCH1</option>
            <option value="8">🔴 C1 SMD1</option>
            <option value="1">🟡 PREC SMX5</option>
            <option value="5">🟡 PREC SMX2</option>
            <option value="9">🟣 C1 VACÍA</option>
        </select>
    </div>

    <div id="panel-control-unico" style="display: flex; gap: 20px; background: #25282b; padding: 15px; border-radius: 10px; color: white; justify-content: center; align-items: center; margin: 20px 0;">
        <div style="text-align: center;">
            <div id="hora-actual" style="font-size: 22px; font-weight: bold;">00:00:00</div>
            <div style="font-size: 9px; color: #26d0ff; letter-spacing: 1px;">HORA ACTUAL</div>
        </div>
        <div style="text-align: center; border-left: 1px solid #ffffff; padding-left: 20px; min-width: 120px;">
            <div id="proximo-ruteo" style="font-size: 16px; font-weight: bold; color: #20B2AA; line-height: 1.1;">Sin tareas</div>
            <div id="hora-ruteo" style="font-size: 14px; font-weight: bold; color: #ffffff; margin-top: 2px;">--</div>
            <div style="font-size: 9px; color: #d0d0d0; letter-spacing: 1px; margin-top: 2px;">SIGUIENTE RUTEO</div>
        </div>
        <div style="text-align: center; border-left: 1px solid #ffffff; padding-left: 20px;">
            <div id="cuenta-regresiva" style="font-size: 22px; font-weight: bold; color: #7CFFB2;">00:00</div>
            <div style="font-size: 9px; color: #d0d0d0; letter-spacing: 1px;">TIEMPO RESTANTE</div>
        </div>
    </div>

    <div id="resumen-flota-ruteada" style="display: flex; gap: 15px; margin: 15px 0; justify-content: center;">
        <div style="background: #d7e5fa; padding: 8px; border-radius: 5px; border: 1px solid #bbdefb; text-align: center; width: 100px;">
            <div style="font-size: 10px; font-weight: bold; color: #0861c7;">MLP</div>
            <div id="val-mlp-rute-2" style="font-size: 14px; font-weight: bold;">0</div>
        </div>
        <div style="background: #c6f7f3; padding: 8px; border-radius: 5px; border: 1px solid #68b0ac; text-align: center; width: 100px;">
            <div style="font-size: 10px; font-weight: bold; color: #12736d;">RENTAL</div>
            <div id="val-rental-rute-2" style="font-size: 14px; font-weight: bold;">0</div>
        </div>
        <div style="background: #d3f5d3; padding: 8px; border-radius: 5px; border: 1px solid #90EE90; text-align: center; width: 100px;">
            <div style="font-size: 10px; font-weight: bold; color: #209626;">CAR</div>
            <div id="val-car-rute-2" style="font-size: 14px; font-weight: bold;">0</div>
        </div>
    </div>

    <div id="dos-pct-global" style="background:#f5f5f5; border:1px solid #d0d0d0; border-radius:6px; padding:6px; margin-bottom:10px; text-align:center; font-weight:bold; color:#25282b;"></div>

    <div id="fleet-drag-handle" style="display: flex; justify-content: center; align-items: center; gap: 8px; flex-wrap: wrap; padding: 4px 0; margin-bottom: 8px;">
        <button id="fleet-toggle-btn" onclick="toggleFleetFloating();" style="cursor:pointer; border:none; background:#25282b; color:white; padding:4px 9px; border-radius:6px; font-weight:bold; font-size:12px; outline:none;">FLOTAR ☁️</button>
        <button onclick="distribuirAutomatico()" style="cursor:pointer; background: #26d4ca; color: #2e3030; border: none; font-size: 12px; padding: 4px 9px; border-radius: 6px; font-weight: bold; outline: none;">🧠 AUTO-CALCULAR</button>
        <button class="filter-btn" onclick="filterRows(true)" style="cursor:pointer; background: linear-gradient(180deg, #4f4f4f 0%, #25282b 100%); color: white; border: 1px solid #25282b; font-size: 12px; padding: 4px 9px; border-radius: 6px; font-weight: bold; outline: none;">ACTIVAS</button>
        <button class="filter-btn" onclick="filterRows(false)" style="cursor:pointer; background: #808080; color:white; border:none; font-size:12px; padding:4px 9px; border-radius:6px; font-weight:bold; outline: none;">TODAS</button>
        <button onclick="reducirHoras()" style="cursor:pointer; background: #dc3545; color:white; border:none; font-size:12px; padding:4px 9px; border-radius:6px; font-weight:bold; outline: none;" title="Reducir 1 hora">➖ 1h</button>
		<button id="excel-btn" onclick="toggleExcelView()" style="cursor:pointer; background: linear-gradient(180deg, #327332 0%, #5a8f32 100%); color: white; border: 1px solid #008000; font-size: 12px; padding: 4px 9px; border-radius: 6px; font-weight: bold; outline: none;">📊 VISTA EXCEL</button>
    </div>

    <!-- CONTENEDOR DE TABLAS DE DISPONIBILIDAD -->
    <div id="fleet-sticky" class="fleet-normal">
        <div id="tab-2" class="t-content" style="display:none;">
            <table class="meli-table">
                <thead>
                    <tr style="background: linear-gradient(180deg, #0a2e42 0%, #25282b 100%); color: white;">
                        <th style="padding: 4px 8px; font-size: 14px;">UNIDAD</th>
                        <th colspan="2" style="font-size: 11px; width: 105px;">ORH</th>
                        <th style="font-size: 11px; width: 45px;">% OCUP</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MIN</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MAX</th>
                        <th style="font-size:11px; width:60px;">SCHEDULE</th>
                        <th style="font-size:11px; width:57px;">USADAS</th>
                        <th style="font-size:11px; width:50px;">DELTA</th>
                    </tr>
                </thead>
                <tbody id="body-2">{gen_master_rows(u_C1, 2)}</tbody>
            </table>
        </div>

        <div id="tab-6" class="t-content" style="display:none;">
            <table class="meli-table">
                <thead>
                    <tr style="background: linear-gradient(180deg, #0a2e42 0%, #25282b 100%); color: white;">
                        <th style="padding: 4px 8px; font-size: 14px;">UNIDAD</th>
                        <th colspan="2" style="font-size: 11px; width: 105px;">ORH</th>
                        <th style="font-size: 11px; width: 45px;">% OCUP</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MIN</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MAX</th>
                        <th style="font-size:11px; width:60px;">SCHEDULE</th>
                        <th style="font-size:11px; width:57px;">USADAS</th>
                        <th style="font-size:11px; width:50px;">DELTA</th>
                    </tr>
                </thead>
                <tbody id="body-6">{gen_master_rows(u_C1_SJA1, 6)}</tbody>
            </table>
        </div>

        <div id="tab-7" class="t-content" style="display:none;">
            <table class="meli-table">
                <thead>
                    <tr style="background: linear-gradient(180deg, #0a2e42 0%, #25282b 100%); color: white;">
                        <th style="padding: 4px 8px; font-size: 14px;">UNIDAD</th>
                        <th colspan="2" style="font-size: 11px; width: 105px;">ORH</th>
                        <th style="font-size: 11px; width: 45px;">% OCUP</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MIN</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MAX</th>
                        <th style="font-size:11px; width:60px;">SCHEDULE</th>
                        <th style="font-size:11px; width:57px;">USADAS</th>
                        <th style="font-size:11px; width:50px;">DELTA</th>
                    </tr>
                </thead>
                <tbody id="body-7">{gen_master_rows(u_C1_SCH1, 7)}</tbody>
            </table>
        </div>

        <div id="tab-8" class="t-content" style="display:none;">
            <table class="meli-table">
                <thead>
                    <tr style="background: linear-gradient(180deg, #0a2e42 0%, #25282b 100%); color: white;">
                        <th style="padding: 4px 8px; font-size: 14px;">UNIDAD</th>
                        <th colspan="2" style="font-size: 11px; width: 105px;">ORH</th>
                        <th style="font-size: 11px; width: 45px;">% OCUP</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MIN</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MAX</th>
                        <th style="font-size:11px; width:60px;">SCHEDULE</th>
                        <th style="font-size:11px; width:57px;">USADAS</th>
                        <th style="font-size:11px; width:50px;">DELTA</th>
                    </tr>
                </thead>
                <tbody id="body-8">{gen_master_rows(u_C1_SMD1, 8)}</tbody>
            </table>
        </div>

        <div id="tab-1" class="t-content" style="display:none;">
            <table class="meli-table">
                <thead>
                    <tr style="background: linear-gradient(180deg, #0a2e42 0%, #25282b 100%); color: white;">
                        <th style="padding: 4px 8px; font-size: 14px;">UNIDAD</th>
                        <th colspan="2" style="font-size: 11px; width: 105px;">ORH</th>
                        <th style="font-size: 11px; width: 45px;">% OCUP</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MIN</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MAX</th>
                        <th style="font-size:11px; width:60px;">SCHEDULE</th>
                        <th style="font-size:11px; width:57px;">USADAS</th>
                        <th style="font-size:11px; width:50px;">DELTA</th>
                    </tr>
                </thead>
                <tbody id="body-1">{gen_master_rows(u_PREC, 1)}</tbody>
            </table>
        </div>

        <div id="tab-5" class="t-content" style="display:none;">
            <table class="meli-table">
                <thead>
                    <tr style="background: linear-gradient(180deg, #0a2e42 0%, #25282b 100%); color: white;">
                        <th style="padding: 4px 8px; font-size: 14px;">UNIDAD</th>
                        <th colspan="2" style="font-size: 11px; width: 105px;">ORH</th>
                        <th style="font-size: 11px; width: 45px;">% OCUP</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MIN</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MAX</th>
                        <th style="font-size:11px; width:60px;">SCHEDULE</th>
                        <th style="font-size:11px; width:57px;">USADAS</th>
                        <th style="font-size:11px; width:50px;">DELTA</th>
                    </tr>
                </thead>
                <tbody id="body-5">{gen_master_rows(u_PREC_SMX2, 5)}</tbody>
            </table>
        </div>

        <div id="tab-4" class="t-content">
            <table class="meli-table">
                <thead>
                    <tr style="background: linear-gradient(180deg, #0a2e42 0%, #25282b 100%); color: white;">
                        <th style="padding: 4px 8px; font-size: 14px;">UNIDAD</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MIN</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MAX</th>
                        <th style="font-size:11px; width:60px;">SCHEDULE</th>
                        <th style="font-size:11px; width:57px;">USADAS</th>
                        <th style="font-size:11px; width:50px;">DELTA</th>
                    </tr>
                </thead>
                <tbody id="body-4">{gen_master_rows(u_SDE, 4)}</tbody>
            </table>
        </div>

        <div id="tab-9" class="t-content" style="display:none;">
            <table class="meli-table">
                <thead>
                    <tr style="background: linear-gradient(180deg, #0a2e42 0%, #25282b 100%); color: white;">
                        <th style="padding: 4px 8px; font-size: 14px;">UNIDAD</th>
                        <th colspan="2" style="font-size: 11px; width: 105px;">ORH</th>
                        <th style="font-size: 11px; width: 45px;">% OCUP</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MIN</th>
                        <th style="font-size: 11px; width: 45px;">SPR<br>MAX</th>
                        <th style="font-size:11px; width:60px;">SCHEDULE</th>
                        <th style="font-size:11px; width:57px;">USADAS</th>
                        <th style="font-size:11px; width:50px;">DELTA</th>
                    </tr>
                </thead>
                <tbody id="body-9">{gen_master_rows(u_C1_VACIA, 9)}</tbody>
            </table>
        </div>
    </div>
</div>

<!-- POLÍGONOS -->
<div style="width:100%; overflow-y:auto;">
    <div style="background: #25282b; color: #20B2AA; padding: 10px; border-radius: 6px; text-align: center; font-weight: bold; margin-top: 20px; margin-bottom: 10px;">
        📋 PLANIFICACIÓN POR POLÍGONOS
    </div>
    
    <div id="polys-2" class="p-content" style="display:none;">{gen_poligonos(u_C1)}</div>
    <div id="polys-6" class="p-content" style="display:none;">{gen_poligonos(u_C1_SJA1)}</div>
    <div id="polys-7" class="p-content" style="display:none;">{gen_poligonos(u_C1_SCH1)}</div>
    <div id="polys-8" class="p-content" style="display:none;">{gen_poligonos(u_C1_SMD1)}</div>
    <div id="polys-1" class="p-content" style="display:none;">{gen_poligonos(u_PREC)}</div>
    <div id="polys-5" class="p-content" style="display:none;">{gen_poligonos(u_PREC_SMX2)}</div>
    <div id="polys-4" class="p-content">{gen_poligonos(u_SDE)}</div>
    <div id="polys-9" class="p-content" style="display:none;">{gen_poligonos(u_C1_VACIA)}</div>
</div>

<!-- MODAL: NOTAS SVC -->
<div id="modal-notas-svc" style="display: none; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(15, 15, 18, 0.96); z-index: 9999999; padding: 25px; box-sizing: border-box; font-family: sans-serif;">
    <div style="max-width: 600px; margin: 50px auto; background: #25282b; border: 2px solid #20B2AA; border-radius: 12px; padding: 25px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #444; padding-bottom: 12px; margin-bottom: 20px;">
            <h2 style="color: #20B2AA; margin: 0; font-size: 20px;">📝 AGREGAR INFORMACIÓN DE SVC</h2>
            <button onclick="cerrarModalNotasSVC()" style="cursor: pointer; background: #dc3545; color: white; border: none; padding: 6px 12px; border-radius: 4px; font-weight: bold;">✕ CERRAR</button>
        </div>

        <div style="display: flex; flex-direction: column; gap: 15px;">
            <div>
                <label style="color: #d0d0d0; font-size: 13px; font-weight: bold; display: block; margin-bottom: 5px;">SVC / Estación:</label>
                <input type="text" id="input-nota-svc" placeholder="Ej. SJA1" style="width: 100%; box-sizing: border-box; padding: 10px; border-radius: 6px; border: 1px solid #555; background: #141414; color: white; font-size: 14px; font-weight: bold;">
            </div>

            <div>
                <label style="color: #d0d0d0; font-size: 13px; font-weight: bold; display: block; margin-bottom: 5px;">Información Adicional:</label>
                <textarea id="input-contenido-nota-svc" placeholder="Escribe aquí la información adicional..." rows="4" style="width: 100%; box-sizing: border-box; padding: 10px; border-radius: 6px; border: 1px solid #555; background: #141414; color: white; font-size: 14px;"></textarea>
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 10px;">
                <button onclick="cerrarModalNotasSVC()" style="cursor: pointer; background: #555; color: white; border: none; padding: 8px 16px; font-weight: bold; border-radius: 6px;">Cancelar</button>
                <button onclick="guardarNotaDesdeBot()" style="cursor: pointer; background: #20B2AA; color: white; border: none; padding: 8px 20px; font-weight: bold; border-radius: 6px;">💾 GUARDAR INFORMACIÓN</button>
            </div>
        </div>
    </div>
</div>

<script>
    let currentTab = 4;
    let editedRowsPlan = new Set();
    const SUPABASE_URL = "{st.secrets.get('SUPABASE_URL', '')}";
    const SUPABASE_KEY = "{st.secrets.get('SUPABASE_KEY', '')}";
    
    const supabaseClient = (window.supabase && window.supabase.createClient && SUPABASE_URL) 
        ? window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY) 
        : null;

    const REGLAS_RUTEO = {reglas_json};
    const MAPA_ORIGENES = {mapa_origenes_json};
    const PREGUNTAS_FRECUENTES = {preguntas_faq_json};
	let NOTAS_SVC = {notas_svc_json};

    function abrirModalNotasSVC() {{
        cerrarMenuRuteos();
        let modal = document.getElementById("modal-notas-svc");
        if (modal) modal.style.display = "block";
    }}

    function cerrarModalNotasSVC() {{
        let modal = document.getElementById("modal-notas-svc");
        if (modal) modal.style.display = "none";
    }}

    async function guardarNotaDesdeBot() {{
        const inputSvc = document.getElementById("input-nota-svc");
        const inputNota = document.getElementById("input-contenido-nota-svc");

        if (!inputSvc || !inputNota) return;

        const svc = inputSvc.value.trim().toUpperCase();
        const contenido = inputNota.value.trim();

        if (!svc || !contenido) {{
            alert("⚠️ Por favor completa todos los campos.");
            return;
        }}

        if (!supabaseClient) {{
            alert("⚠️ No hay conexión con la base de datos.");
            return;
        }}

        try {{
            const {{ data, error }} = await supabaseClient
                .from("notas_svc")
                .upsert([{{ svc: svc, contenido: contenido }}], {{ onConflict: 'svc' }});

            if (error) {{
                alert("❌ Error al guardar: " + error.message);
                return;
            }}

            let idx = NOTAS_SVC.findIndex(n => String(n.svc).toUpperCase() === svc);
            if (idx !== -1) {{
                NOTAS_SVC[idx].contenido = contenido;
            }} else {{
                NOTAS_SVC.push({{ svc: svc, contenido: contenido }});
            }}

            inputSvc.value = "";
            inputNota.value = "";
            alert("✅ Información guardada para " + svc);
            cerrarModalNotasSVC();
        }} catch (err) {{
            alert("❌ Error al procesar la solicitud.");
        }}
    }}

    function cambiarCiclo(valorTab) {{
        if (!valorTab) return;
        const tabStr = String(valorTab);

        document.querySelectorAll('.t-content, .p-content').forEach(el => {{
            el.style.display = 'none';
        }});

        const tablaActiva = document.getElementById('tab-' + tabStr);
        if (tablaActiva) tablaActiva.style.display = 'block';

        const polyActivo = document.getElementById('polys-' + tabStr);
        if (polyActivo) polyActivo.style.display = 'block';

        currentTab = parseInt(tabStr);
        if (typeof recalc === 'function') recalc();
    }}

    function limpiarPantallaCompleta() {{
        if (!confirm("¿Deseas vaciar los valores editados de la pantalla para iniciar un nuevo ruteo?")) return;
        
        document.querySelectorAll('.v-total-val, .nodos-val, .nodos-campeche').forEach(el => el.innerText = "0");
        document.querySelectorAll('.calc-row').forEach(row => {{
            let uSpan = row.querySelector('.u-manual');
            let sprSpan = row.querySelector('.spr-real-val');
            let selectType = row.querySelector('.s-type');
            let checkOk = row.querySelector('.ok-check');

            if (uSpan) uSpan.innerText = "0";
            if (sprSpan) sprSpan.innerText = "0";
            if (selectType) {{
                selectType.value = "";
                updateSelectColor(selectType);
            }}
            if (checkOk) checkOk.checked = false;
        }});

        document.querySelectorAll('.f-stock').forEach(el => el.innerText = "0");
        if (typeof recalc === 'function') recalc();
        cerrarMenuRuteos();
    }}

    function stepVal(btn, delta, type) {{
        let row = btn.closest('tr');
        let sel = row.querySelector('.s-type').value;
        if (sel === "Seleccionar..." || !sel) return;

        let fRows = Array.from(document.querySelectorAll('#body-' + currentTab + ' tr'));
        let fRow = fRows.find(r => r.querySelector('.edit-name').innerText.trim() === sel);
        if (!fRow) return;

        if (type === 'u') {{
            let span = row.querySelector('.u-manual');
            let val = parseInt(span.innerText) || 0;
            let newVal = Math.max(0, val + delta);
            span.innerText = newVal;
        }} else {{
            let span = row.querySelector('.spr-real-val');
            let val = parseFloat(span.innerText) || 0;
            span.innerText = Math.max(0, Math.round(val + delta));
        }}
        editedRowsPlan.add(row);
        recalc();
    }}

    function recalc() {{
        let fleet = {{}};
        let tabId = currentTab;

        document.querySelectorAll('#body-' + tabId + ' tr').forEach(row => {{
            let nameCell = row.querySelector('.edit-name');
            if (!nameCell) return;
            let name = nameCell.innerText.trim();
            let sch = parseInt(row.querySelector('.f-stock').innerText) || 0;
            let ma = row.querySelector('.edit-spr-max');
            
            if (name !== "" && name !== "IGNORAR") {{
                fleet[name] = {{ max: parseFloat(ma?.innerText)||0, stock: sch, used: 0 }};
            }}
        }});

        let mapeoRuteadas = {{}};
        document.querySelectorAll('#polys-' + tabId + ' .calc-row').forEach(row => {{
            let s = row.querySelector('.s-type').value;
            let u = parseInt(row.querySelector('.u-manual').innerText) || 0;
            if (s && s !== "Seleccionar...") {{
                mapeoRuteadas[s] = (mapeoRuteadas[s] || 0) + u;
            }}
        }});

        document.querySelectorAll('#body-' + tabId + ' tr').forEach(row => {{
            let nameCell = row.querySelector('.edit-name');
            let ruteadaCell = row.querySelector('.f-ruteadas');
            if (nameCell && ruteadaCell) {{
                let name = nameCell.innerText.trim();
                ruteadaCell.innerText = mapeoRuteadas[name] || 0;
            }}
        }});

        document.querySelectorAll('#polys-' + tabId + ' .poligono-bloque').forEach(bl => {{
            let vT = parseFloat(bl.querySelector('.v-total-val').innerText) || 0, vA = 0;
            let vCalcEl = bl.querySelector('.v-calculado-total');

            bl.querySelectorAll('.calc-row').forEach(r => {{
                let sType = r.querySelector('.s-type');
                let uManual = r.querySelector('.u-manual');
                let sp = r.querySelector('.spr-real-val');
                let s = sType.value;
                let u = parseInt(uManual.innerText) || 0;

                if (s !== "Seleccionar..." && s !== "") {{
                    vA += (u * (parseFloat(sp.innerText) || 0));
                }}
            }});

            if (vCalcEl) vCalcEl.innerText = Math.round(vA);
            let d = bl.querySelector('.p-diff');
            if (d) {{
                if (vT === 0) d.innerText = "VACÍO";
                else if (Math.round(vA) === Math.round(vT)) {{ d.innerText = "OK"; d.style.background = "#61b888"; }}
                else if (vA > vT) {{ d.innerText = "EXCESO: " + Math.round(vA - vT); d.style.background = "#f2bd5c"; }}
                else {{ d.innerText = "FALTAN: " + Math.round(vT - vA); d.style.background = "#fc9a88"; }}
            }}
        }});

        updateFleetFloat();
    }}

    function updateFleetFloat() {{
        let totalMLPReal = 0, totalRentalReal = 0, totalCarReal = 0;

        document.querySelectorAll('#polys-' + currentTab + ' .calc-row').forEach(row => {{
            let s = row.querySelector('.s-type').value; 
            let u = parseInt(row.querySelector('.u-manual').innerText) || 0;
            if (!s || s === "Seleccionar...") return;

            let name = s.toLowerCase().trim();
            if (name.includes("mlp")) totalMLPReal += u;
            else if (name.includes("rental")) totalRentalReal += u;
            else totalCarReal += u;
        }});

        let elMlp = document.getElementById("val-mlp-rute-2");
        let elRental = document.getElementById("val-rental-rute-2");
        let elCar = document.getElementById("val-car-rute-2");

        if (elMlp) elMlp.innerText = totalMLPReal;
        if (elRental) elRental.innerText = totalRentalReal;
        if (elCar) elCar.innerText = totalCarReal;
    }}

    function updateSelectColor(selectElement) {{
        if (selectElement.value === "") {{
            selectElement.style.color = "#808080";
        }} else {{
            selectElement.style.color = "#25282b";
        }}
    }}

    function manualEdit(el) {{ recalc(); }}
    function resetRow(sel) {{ updateSelectColor(sel); recalc(); }}
    function filterRows(onlyActive) {{
        const rows = document.querySelectorAll('#body-' + currentTab + ' .master-row');
        rows.forEach(row => {{
            const stock = parseInt(row.querySelector('.f-stock').innerText) || 0;
            row.style.display = (onlyActive && stock === 0) ? 'none' : '';
        }});
    }}

    function toggleFleetFloating() {{
        const panel = document.getElementById("fleet-sticky");
        const btn = document.getElementById("fleet-toggle-btn");
        if (!panel) return;
        if (panel.classList.contains("fleet-floating")) {{
            panel.classList.remove("fleet-floating");
            if (btn) btn.textContent = "FLOTAR ☁️";
        }} else {{
            panel.classList.add("fleet-floating");
            if (btn) btn.textContent = "NORMAL (enter)";
        }}
    }}

    function reducirHoras() {{
        document.querySelectorAll("#body-" + currentTab + " .edit-orh").forEach(celda => {{
            let val = parseFloat(celda.innerText) || 0;
            if (val > 0) celda.innerText = Math.max(0, val - 60);
        }});
        recalc();
    }}

    function toggleExcelView() {{
        document.body.classList.toggle("excel-view");
    }}

    function distribuirAutomatico() {{
        recalc();
    }}

    // RELOJ
    setInterval(() => {{
        const ahora = new Date();
        const el = document.getElementById("hora-actual");
        if (el) el.innerText = ahora.toLocaleTimeString('es-MX');
    }}, 1000);
</script>

<!-- ============================================================
     ☰ MENÚ LATERAL MINIMALISTA
     ============================================================ -->
<style>
    #btn-menu-lateral {
        position: fixed;
        top: 10px;
        left: 10px;
        z-index: 9999999;
        width: 42px;
        height: 42px;
        border: 1px solid #444;
        border-radius: 6px;
        background: #25282b;
        color: white;
        font-size: 22px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 3px 8px rgba(0,0,0,0.45);
    }

    #menu-lateral-ruteos {
       position: fixed;
       top: 0;
       left: -420px;
       width: 400px;
       height: 100vh;
       background: #1e2022;
       z-index: 9999998;
       border-radius: 0 12px 12px 0;
       box-shadow: 8px 0 20px rgba(0, 0, 0, 0.65);
       transition: left 0.3s ease;
       padding: 20px 15px;
       box-sizing: border-box;
       color: white;
       overflow-y: auto;
   }

    #menu-lateral-ruteos.abierto { left: 0; }

    .menu-ruteos-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 15px;
        margin-bottom: 20px;
        border-bottom: 1px solid #444;
    }

    .menu-ruteos-titulo {
        font-size: 15px;
        font-weight: bold;
        color: #66CDAA;
    }

    #cerrar-menu-ruteos {
        border: none;
        background: transparent;
        color: white;
        font-size: 21px;
        cursor: pointer;
    }

    .opcion-menu-ruteos {
        width: 100%;
        box-sizing: border-box;
        padding: 12px 15px;
        margin-bottom: 10px;
        border-radius: 7px;
        border: 1px solid #3b3f43;
        background: #292c30;
        color: #e4e6e8;
        font-size: 14px;
        font-weight: 600;
        text-align: left;
        cursor: pointer;
    }

    .opcion-menu-ruteos:hover {
        background: #363a3f;
        border-color: #66CDAA;
        color: white;
    }
</style>

<button id="btn-menu-lateral" onclick="abrirCerrarMenuRuteos()" title="Abrir menú">☰</button>

<div id="menu-lateral-ruteos">
    <div class="menu-ruteos-header">
        <span class="menu-ruteos-titulo">MENÚ PRINCIPAL</span>
        <button id="cerrar-menu-ruteos" onclick="abrirCerrarMenuRuteos()">✕</button>
    </div>

    <!-- LIMPIAR PANTALLA -->
    <button class="opcion-menu-ruteos" onclick="limpiarPantallaCompleta()">🧹 &nbsp; LIMPIAR PANTALLA</button>

    <!-- OCULTAR PLANES EXTRA -->
    <button id="btn-ocultar-extra-menu" class="opcion-menu-ruteos" onclick="togglePlanesExtra()">👁️ &nbsp; OCULTAR PLANES EXTRA</button>

    <!-- MAPA OPERATIVO -->
    <button class="opcion-menu-ruteos" onclick="toggleMapaOperativo()">🗺️ &nbsp; MAPA DE EXTENDIDO</button>

    <div id="panel-mapa-operativo" style="display: none; margin-top: 10px; padding: 10px; background: #17191b; border-radius: 8px; text-align: center;">
        <img id="img-mapa-operativo" src="https://drive.google.com/thumbnail?id=1M4GLEwFzhLrZjV-zmvGrdTQhC6IjwxOJ&sz=w1000" style="width: 100%; border-radius: 6px;" />
    </div>

    <!-- NOTAS SVC -->
    <button class="opcion-menu-ruteos" onclick="abrirModalNotasSVC()">📝 &nbsp; AGREGAR NOTA SVC</button>

    <!-- ASISTENTE DE RUTEO -->
    <button class="opcion-menu-ruteos" onclick="togglePanelBotLateral()">🤖 &nbsp; ASISTENTE DE RUTEO</button>

    <div id="panel-bot-lateral-contenido" style="display: none; margin-top: 10px; background: #17191b; border: 1px solid #34383d; border-radius: 12px; padding: 10px;">
        <div style="text-align: center; font-size: 20px;">🚚</div>
        <div style="text-align: center; font-size: 11px; font-weight: bold; color: #22c55e; margin-bottom: 8px;">● Routing Online</div>
        
        <div id="box-mensajes-bot" style="max-height: 300px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; font-size: 13px; padding: 4px;">
            <div style="background: #262626; border-left: 3px solid #008218; padding: 8px; border-radius: 6px; color: #ffffff;">
                🤖 <b>Asistente de Ruteo:</b><br>Escribe el código de un SVC para ver prioridades e indicaciones.
            </div>
        </div>

        <div style="display: flex; gap: 6px; margin-top: 10px;">
            <input type="text" id="input-bot-lateral" placeholder="Escribe tu consulta..." onkeydown="if(event.key==='Enter') enviarConsultaBotLateral()" style="flex: 1; padding: 8px; border-radius: 6px; border: 1px solid #444; background: #141414; color: white; font-size: 13px;">
            <button onclick="enviarConsultaBotLateral()" style="cursor: pointer; background: #20B2AA; color: white; border: none; padding: 8px 12px; border-radius: 6px; font-weight: bold;">🚀</button>
        </div>
    </div>
</div>

<script>
    function abrirCerrarMenuRuteos() {{
        const menu = document.getElementById("menu-lateral-ruteos");
        const boton = document.getElementById("btn-menu-lateral"); 
        if (!menu) return;
        menu.classList.toggle("abierto");
        if (boton) boton.style.display = menu.classList.contains("abierto") ? "none" : "block";
    }}

    function cerrarMenuRuteos() {{
        const menu = document.getElementById("menu-lateral-ruteos");
        const boton = document.getElementById("btn-menu-lateral");
        if (menu) menu.classList.remove("abierto");
        if (boton) boton.style.display = "block";
    }}

    function togglePanelBotLateral() {{
        const panel = document.getElementById("panel-bot-lateral-contenido");
        if (!panel) return;
        panel.style.display = (panel.style.display === "none" || panel.style.display === "") ? "block" : "none";
    }}

    function toggleMapaOperativo() {{
        const panel = document.getElementById("panel-mapa-operativo");
        if (!panel) return;
        panel.style.display = (panel.style.display === "none" || panel.style.display === "") ? "block" : "none";
    }}

    let planesExtraOcultos = false;
    function togglePlanesExtra() {{
        planesExtraOcultos = !planesExtraOcultos;
        const btnMenu = document.getElementById("btn-ocultar-extra-menu");

        document.querySelectorAll(".poligono-bloque").forEach(bloque => {{
            const tdPlan = bloque.querySelector("td.plan-cell");
            if (tdPlan) {{
                const nombrePlan = tdPlan.innerText.trim().toUpperCase();
                if (/^PLAN\s+\d+$/i.test(nombrePlan)) {{
                    bloque.style.display = planesExtraOcultos ? "none" : "block";
                }}
            }}
        }});

        if (btnMenu) {{
            btnMenu.innerHTML = planesExtraOcultos ? "👁️ &nbsp; MOSTRAR PLANES EXTRA" : "👁️ &nbsp; OCULTAR PLANES EXTRA";
        }}
    }}

    function enviarConsultaBotLateral() {{
        const input = document.getElementById("input-bot-lateral");
        const box = document.getElementById("box-mensajes-bot");
        if (!input || !box) return;

        let consulta = input.value.trim();
        if (!consulta) return;

        box.innerHTML += `
            <div style="background: #008080; padding: 6px; border-radius: 6px; color: #ffffff; text-align: right; margin-bottom: 4px;">
                <b>Tú:</b> ${{consulta}}
            </div>
        `;
        input.value = "";

        let q = consulta.toLowerCase().trim();
        let respuesta = "";

        // 1. MAPA DE ORIGENES
        if (typeof MAPA_ORIGENES !== "undefined") {{
            Object.keys(MAPA_ORIGENES).forEach(key => {{
                if (q.includes(key.toLowerCase())) {{
                    let info = MAPA_ORIGENES[key];
                    respuesta += `📍 <b>${{key.toUpperCase()}}:</b> Región ${{info.region}} | Origen: ${{info.origen}} | Val: ${{info.val}}<br>`;
                }}
            }});
        }}

        // 2. REGLAS
        if (typeof REGLAS_RUTEO !== "undefined") {{
            Object.keys(REGLAS_RUTEO).forEach(k => {{
                let kClean = k.toLowerCase().replace("_extendido","").replace("_precarga","");
                if (q.includes(kClean)) {{
                    respuesta += `📋 <b>Regla (${{k.toUpperCase()}}):</b><br>${{REGLAS_RUTEO[k].replace(/\\n/g, "<br>")}}<br>`;
                }}
            }});
        }}

        // 3. NOTAS DE LA BASE DE DATOS
        if (typeof NOTAS_SVC !== "undefined" && Array.isArray(NOTAS_SVC)) {{
            let notas = NOTAS_SVC.filter(n => String(n.svc).toLowerCase().includes(q));
            if (notas.length > 0) {{
                respuesta += `📝 <b>Notas adicionales guardadas:</b><br>`;
                notas.forEach(n => {{ respuesta += `• ${{n.contenido}}<br>`; }});
            }}
        }}

        if (!respuesta) {{
            respuesta = "⚠️ No encontré información para esa búsqueda. Intenta consultando el código de una estación de ruteo (ej. SJA1).";
        }}

        setTimeout(() => {{
            box.innerHTML += `
                <div style="background: #cae8e2; border-left: 3px solid #20B2AA; padding: 6px; border-radius: 6px; color: #000000; margin-bottom: 4px;">
                    🤖 <b>Bot:</b><br>${{respuesta}}
                </div>
            `;
            box.scrollTop = box.scrollHeight;
        }}, 150);
    }}
</script>
</body>
</html>
"""

html(app_html, height=1200, scrolling=True)

# CONSOLA RESTADOR INFERIOR
html_limpio = """
<style>
    body { background-color: #25282b; font-family: sans-serif; margin: 0; }
    .main-box { background: #25282b; padding: 5px; display: flex; flex-direction: column; align-items: center; }
    .unified-console { background: #25282b; border-radius: 10px; padding: 10px; text-align: center; width: 100%; max-width: 450px; }
    .display-screen { background: #1a1c1e; border-radius: 8px; padding: 8px; margin-bottom: 8px; border: 1px solid #444; }
    .btn-3d { background: #20B2AA; color: white; border: none; padding: 8px 18px; border-radius: 6px; font-weight: bold; cursor: pointer; }
</style>

<div class="main-box">
    <div class="unified-console"> 
        <div class="display-screen">
            <div style="color: #ffffff; font-size: 10px; margin-bottom: 3px;">RESTADOR / CONVERTIDOR DE HORAS</div>
            <div id="horaReal" style="font-size: 32px; color: #FF00FF; font-weight: bold;">--:--</div>
        </div>
        <div style="display: flex; justify-content: center; align-items: center; gap: 10px;">
            <input type="number" id="minInput" value="10" style="background: #141414; color: #ffffff; border: 1px solid #555; padding: 6px; border-radius: 4px; width: 60px; text-align: center; font-size: 18px; font-weight: bold;">
            <button class="btn-3d" onclick="ejecutarTodo()">CALCULAR</button>
        </div>
    </div>
</div>

<script>
    function ejecutarTodo() {
        const mins = document.getElementById('minInput').value || 0;
        const ahora = new Date();
        const nuevaFecha = new Date(ahora.getTime() - (mins * 60000));
        const h = String(nuevaFecha.getHours()).padStart(2, '0');
        const m = String(nuevaFecha.getMinutes()).padStart(2, '0');
        document.getElementById('horaReal').innerText = h + ":" + m;
    }
    ejecutarTodo();
</script>
"""

st.markdown("---")
html(html_limpio, height=180, scrolling=False)
