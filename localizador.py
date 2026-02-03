import streamlit as st
import requests
import pandas as pd
import time
import random
import math
import os
import re 
import textwrap 
from typing import Dict, Any, List, Set, Tuple
from io import BytesIO

# --- 0. AUTO-CONFIGURAÇÃO DE TEMA ---
def setup_theme_config():
    config_dir = ".streamlit"
    config_path = os.path.join(config_dir, "config.toml")
    toml_content = """
[theme]
primaryColor = "#FFAF04"
backgroundColor = "#0093E2"
secondaryBackgroundColor = "#006da8"
textColor = "#FFFFFF"
font = "sans serif"
"""
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    if not os.path.exists(config_path):
        with open(config_path, "w") as f:
            f.write(toml_content)
        return True
    return False

theme_changed = setup_theme_config()

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Localizador SQG", 
    page_icon="🏢", 
    layout="wide", 
    initial_sidebar_state="expanded" 
)

if theme_changed:
    st.warning("⚠️ TEMA ATUALIZADO! Pare o terminal (Ctrl+C) e rode novamente para aplicar.")
    st.stop()

# --- CORES ---
COLOR_BLUE = "#0093E2"       
COLOR_YELLOW = "#FFAF04"     
COLOR_WHITE = "#FFFFFF"      
COLOR_BG_SIDEBAR = "#006da8" 
COLOR_TABLE_BG = "#FFFFFF"   
COLOR_TABLE_TEXT = "#333333" 

# --- CSS V31 (A SETINHA FLUTUANTE) ---
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Poppins:wght@400;600;700&display=swap');

    /* 1. MATA O CABEÇALHO PRETO (Suma daqui!) */
    [data-testid="stHeader"] {{
        display: none !important;
    }}

    /* 2. FORÇA A SETINHA A APARECER FLUTUANDO (O Resgate) */
    [data-testid="stSidebarCollapsedControl"] {{
        display: block !important;
        position: fixed !important; /* Isso solta ela do header */
        top: 15px;
        left: 15px;
        z-index: 1000000 !important; /* Fica em cima de tudo */
        background-color: {COLOR_BG_SIDEBAR}; /* Fundo azul pra destacar */
        color: {COLOR_WHITE} !important;
        padding: 0.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        transition: all 0.3s;
    }}
    
    [data-testid="stSidebarCollapsedControl"]:hover {{
        background-color: {COLOR_YELLOW};
        color: black !important;
        transform: scale(1.1);
    }}
    
    /* Garante que o ícone SVG dentro dela fique branco (ou preto no hover) */
    [data-testid="stSidebarCollapsedControl"] svg {{
        fill: currentColor !important;
    }}

    /* Remove instruções de input */
    [data-testid="InputInstructions"] {{ display: none !important; }}
    
    /* Ajuste do topo da página */
    .block-container {{ padding-top: 3rem !important; }}

    /* FONTES E CORES GERAIS */
    h1, h2, h3, button {{ font-family: 'Poppins', sans-serif !important; }}
    html, body, p, label, .stMarkdown, li, input, .stDataFrame {{ font-family: 'Inter', sans-serif !important; }}

    h1, h2, h3, p, label, .stMarkdown, li, div[data-testid="stMetricValue"], div[data-testid="stMetricLabel"] {{
        color: {COLOR_WHITE} !important;
    }}
    
    .stTextInput input, .stNumberInput input {{
        background-color: {COLOR_WHITE};
        color: #000000 !important;
        border-radius: 8px;
        border: none;
        font-weight: 500;
    }}
    ::placeholder {{ color: #888888 !important; opacity: 1; }}

    .stButton > button, div[data-testid="stDownloadButton"] > button {{
        background-color: {COLOR_YELLOW} !important;
        color: {COLOR_WHITE} !important;
        border: none;
        font-weight: 700;
        text-transform: uppercase;
        border-radius: 8px;
        transition: all 0.2s ease;
        text-shadow: 0px 1px 2px rgba(0,0,0,0.2);
    }}
    .stButton > button:hover, div[data-testid="stDownloadButton"] > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        background-color: #ffc300 !important;
    }}

    /* TABELA */
    [data-testid="stDataFrame"] {{ 
        background-color: {COLOR_TABLE_BG} !important;
        padding: 5px; 
        border-radius: 12px; 
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
    }}
    [data-testid="stDataFrame"] * {{ color: {COLOR_TABLE_TEXT} !important; }}
    [data-testid="stDataFrame"] a {{ color: #006da8 !important; text-decoration: underline; }}
    div[data-testid="stDataFrame"] div[role="columnheader"] {{
        background-color: {COLOR_BG_SIDEBAR} !important; 
        color: {COLOR_WHITE} !important;
        font-weight: 600;
    }}

    .stAlert {{
        background-color: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        color: {COLOR_WHITE} !important;
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-left: 5px solid {COLOR_YELLOW};
    }}
    
    /* TUTORIAL CARD */
    .tutorial-card {{
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 15px;
        padding: 25px;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }}
    .step-number {{
        background-color: {COLOR_YELLOW};
        color: white;
        font-weight: bold;
        padding: 5px 12px;
        border-radius: 50%;
        margin-right: 10px;
        text-shadow: 0px 1px 1px rgba(0,0,0,0.2);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO ---
if 'pool_of_ids' not in st.session_state: st.session_state.pool_of_ids = [] 
if 'seen_ids' not in st.session_state: st.session_state.seen_ids = set() 
if 'current_leads' not in st.session_state: st.session_state.current_leads = [] 
if 'geo_context' not in st.session_state: st.session_state.geo_context = None
if 'cep_digitado' not in st.session_state: st.session_state.cep_digitado = ""

# --- FUNÇÕES ---
def formatar_cep():
    valor_atual = st.session_state.cep_digitado
    apenas_numeros = re.sub(r'\D', '', valor_atual)
    apenas_numeros = apenas_numeros[:8]
    if len(apenas_numeros) > 5:
        novo_valor = f"{apenas_numeros[:5]}-{apenas_numeros[5:]}"
    else:
        novo_valor = apenas_numeros
    st.session_state.cep_digitado = novo_valor

def calculate_distance_km(lat1, lon1, lat2, lon2):
    R = 6371.0 
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

# --- API ---
# GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"] 
GOOGLE_API_KEY = "AIzaSyAQs7DaqMl4i4aSRYBiXy_0Xjyss0bBW5Y" 

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
NEARBY_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

def get_offset_coordinate(lat: float, lng: float, distance_km: float, bearing_deg: float) -> Tuple[float, float]:
    R = 6378.1 
    brng = math.radians(bearing_deg)
    d = distance_km
    lat1 = math.radians(lat)
    lon1 = math.radians(lng)
    lat2 = math.asin(math.sin(lat1)*math.cos(d/R) + math.cos(lat1)*math.sin(d/R)*math.cos(brng))
    lon2 = lon1 + math.atan2(math.sin(brng)*math.sin(d/R)*math.cos(lat1), math.cos(d/R)-math.sin(lat1)*math.sin(lat2))
    return (math.degrees(lat2), math.degrees(lon2))

def generate_search_points(lat: float, lng: float, radius_km: float) -> List[Tuple[float, float]]:
    points = [(lat, lng)]
    if radius_km >= 2.0:
        offset_dist = radius_km * 0.7 
        points.append(get_offset_coordinate(lat, lng, offset_dist, 0))   # N
        points.append(get_offset_coordinate(lat, lng, offset_dist, 90))  # L
        points.append(get_offset_coordinate(lat, lng, offset_dist, 180)) # S
        points.append(get_offset_coordinate(lat, lng, offset_dist, 270)) # O
    return points

def geocode_cep(cep: str) -> Dict[str, Any]:
    cep_clean = re.sub(r'\D', '', cep)
    params = {"address": f"{cep_clean}, Brasil", "key": GOOGLE_API_KEY, "language": "pt-BR", "region": "br"}
    r = requests.get(GEOCODE_URL, params=params, timeout=30)
    data = r.json()
    if data.get("status") != "OK" or not data.get("results"):
        raise ValueError(f"Erro no Geocode: {data.get('status')}")
    result = data["results"][0]
    loc = result["geometry"]["location"]
    
    bairro = "Região"
    for comp in result.get("address_components", []):
        if "sublocality" in comp.get("types", []) or "neighborhood" in comp.get("types", []):
            bairro = comp.get("long_name")
            break
            
    return {
        "lat": loc["lat"], "lng": loc["lng"],
        "formatted_address": result.get("formatted_address"),
        "bairro": bairro
    }

@st.cache_data(show_spinner=False, ttl=3600*24) 
def scan_area_for_ids(origin_lat: float, origin_lng: float, radius_km: float) -> List[Dict[str, Any]]:
    search_points = generate_search_points(origin_lat, origin_lng, radius_km)
    unique_places = {} 
    radius_m = int(radius_km * 1000)
    
    for pt_lat, pt_lng in search_points:
        next_page_token = None
        while True:
            params = {
                "location": f"{pt_lat},{pt_lng}", "radius": radius_m, "type": "bakery",
                "keyword": "padaria panificadora", "key": GOOGLE_API_KEY, "language": "pt-BR"
            }
            if next_page_token: params["pagetoken"] = next_page_token
            try:
                r = requests.get(NEARBY_URL, params=params, timeout=10)
                data = r.json()
                results = data.get("results", [])
                for res in results:
                    pid = res.get("place_id")
                    place_loc = res.get("geometry", {}).get("location")
                    if place_loc and pid and pid not in unique_places:
                        place_lat = place_loc["lat"]
                        place_lng = place_loc["lng"]
                        dist_real = calculate_distance_km(origin_lat, origin_lng, place_lat, place_lng)
                        if dist_real <= (radius_km + 0.1):
                            unique_places[pid] = res 
                next_page_token = data.get("next_page_token")
                if not next_page_token or len(unique_places) >= 600: 
                    break
                time.sleep(2)
            except:
                break
    return list(unique_places.values())

def fetch_details_for_leads(place_ids: List[str]) -> List[Dict[str, Any]]:
    detailed_leads = []
    progress_bar = st.progress(0, text="Extraindo dados...")
    total = len(place_ids)
    for i, pid in enumerate(place_ids):
        params = {
            "place_id": pid, "key": GOOGLE_API_KEY, "language": "pt-BR",
            "fields": "name,formatted_address,address_component,international_phone_number,formatted_phone_number,website,url"
        }
        try:
            r = requests.get(DETAILS_URL, params=params, timeout=10)
            data = r.json().get("result", {})
            bairro = "N/A"
            for comp in data.get("address_components", []):
                if "sublocality" in comp.get("types", []) or "neighborhood" in comp.get("types", []):
                    bairro = comp.get("long_name")
                    break
            contact = data.get("international_phone_number") or data.get("formatted_phone_number") or data.get("website") or "Sem contato"
            detailed_leads.append({
                "Nome": data.get("name"),
                "Bairro": bairro,
                "Contato": contact,
                "Endereço": data.get("formatted_address"),
                "Maps": data.get("url"),
                "Place ID": pid
            })
        except:
            pass
        progress_bar.progress((i + 1) / total)
    progress_bar.empty()
    return detailed_leads

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.markdown("### 🏢 Localizador SQG") 

    st.markdown("---")
    st.header("1. Alvo")
    
    st.text_input(
        "CEP Central", 
        placeholder="Ex: 01303-020",
        key="cep_digitado",
        max_chars=9, 
        on_change=formatar_cep 
    )
    
    raio_input = st.slider("Raio (km)", 1.0, 50.0, 3.0, 0.5)
    
    if st.button("🔍 Buscar", type="primary"):
        cep_atual = st.session_state.cep_digitado
        
        if not cep_atual:
            st.warning("Insira um CEP.")
        else:
            try:
                with st.spinner("Buscando..."):
                    st.session_state.seen_ids = set() 
                    st.session_state.current_leads = [] 
                    geo = geocode_cep(cep_atual)
                    st.session_state.geo_context = geo
                    raw_places = scan_area_for_ids(geo["lat"], geo["lng"], raio_input)
                    st.session_state.pool_of_ids = raw_places
                    bairro_nome = geo.get('bairro', 'Região')
                    st.success(f"Pronto! Foram encontradas {len(raw_places)} padarias no raio de {raio_input}km de {bairro_nome}.")
            except Exception as e:
                st.error(str(e))

    st.markdown("---")
    opacity = "1" if st.session_state.pool_of_ids else "0.5"
    st.markdown(f'<div style="opacity: {opacity}">', unsafe_allow_html=True)
    st.header("2. Extração")
    
    if st.session_state.pool_of_ids:
        all_ids = [p["place_id"] for p in st.session_state.pool_of_ids]
        available_ids = [pid for pid in all_ids if pid not in st.session_state.seen_ids]
        count_avail = len(available_ids)
        count_seen = len(st.session_state.seen_ids)
        
        st.markdown(f"""
        <div style="background-color:rgba(255,255,255,0.1); padding:15px; border-radius:8px; margin-bottom:15px; border-left: 4px solid {COLOR_YELLOW}">
            <span style="font-size: 14px; opacity: 0.8">Disponíveis:</span><br>
            <span style="font-size: 24px; font-weight: 600; color:{COLOR_YELLOW}">{count_avail}</span><br>
            <hr style="margin: 8px 0; opacity: 0.2">
            <span style="font-size: 14px; opacity: 0.8">Já Extraídos:</span><br>
            <span style="font-size: 18px; font-weight: 600">{count_seen}</span>
        </div>
        """, unsafe_allow_html=True)
        
        if count_avail > 0:
            qtd = st.number_input("Qtd. de padarias a listar", 1, count_avail, min(10, count_avail))
            if st.button("Listar dados"):
                selected_ids = random.sample(available_ids, qtd)
                new_leads = fetch_details_for_leads(selected_ids)
                st.session_state.current_leads.extend(new_leads) 
                for pid in selected_ids:
                    st.session_state.seen_ids.add(pid)
                st.rerun()
        else:
            st.warning("Área zerada!")
    else:
        st.info("Insira o CEP para começar.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- ÁREA PRINCIPAL ---

if st.session_state.geo_context:
    st.title("Localizador SQG Pro")
    st.markdown(f"**📍 Base:** {st.session_state.geo_context['formatted_address']}")

    if st.session_state.current_leads:
        df = pd.DataFrame(st.session_state.current_leads)
        display_df = df.drop(columns=["Place ID"], errors='ignore')
        
        st.markdown(f"### 📋 Lista de Padarias ({len(df)})")
        
        st.dataframe(
            display_df,
            column_config={
                "Maps": st.column_config.LinkColumn("Link", display_text="Abrir Mapa"),
            },
            use_container_width=True,
            hide_index=True
        )
        
        col1, col2 = st.columns(2)
        with col1:
            csv = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button("🔽 Baixar CSV Completo", csv, "leads_sqg.csv", "text/csv", use_container_width=True)
        with col2:
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                display_df.to_excel(writer, index=False)
            st.download_button("🔽 Baixar Excel Completo", output.getvalue(), "leads_sqg.xlsx", "application/vnd", use_container_width=True)
else:
    st.title("Bem-vindo ao Localizador SQG")
    st.markdown("### Inteligência Georreferenciada para Prospecção Ativa")
    st.markdown("---")
    
    col_tut1, col_tut2 = st.columns([0.6, 0.4])
    
    with col_tut1:
        st.markdown(textwrap.dedent(f"""
        <div class="tutorial-card">
            <h4>⚙️ Como usar a ferramenta</h4>
            <p style="margin-top:15px"><span class="step-number">1</span> <b>Defina o Alvo:</b><br>
            Insira o CEP de referência na barra lateral e o <b>Raio de busca</b> desejado.</p>
            <p><span class="step-number">2</span> <b>Pesquisa Inteligente:</b><br>
            Clique em 'Buscar'. O sistema fará uma pesquisa completa na região para identificar todas as padarias dentro da área selecionada.</p>
            <p><span class="step-number">3</span> <b>Extração de Dados:</b><br>
            Com as padarias identificadas, defina quantas deseja listar e clique em 'Listar dados' para revelar telefones, sites e endereços validados.</p>
            <p><span class="step-number">4</span> <b>Finalização:</b><br>
            Baixe a planilha (Excel/CSV) para sua prospecção ou clique no link da tabela para abrir a localização exata no Google Maps.</p>
        </div>
        """), unsafe_allow_html=True)
        
    with col_tut2:
        st.markdown(textwrap.dedent(f"""
        <div class="tutorial-card" style="border-left: 5px solid {COLOR_YELLOW}">
            <h4>💡 Dica de Ouro</h4>
            <p style="font-size: 14px; opacity: 0.9">
            <b>A precisão é sua melhor amiga.</b><br><br>
            Recomendamos realizar buscas focadas em raios estratégicos (entre 3km e 5km).<br><br>
            Isso garante rotas logísticas mais densas, economiza tempo de deslocamento da equipe e otimiza a assertividade dos dados extraídos.
            </p>
        </div>
        """), unsafe_allow_html=True)
