import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
from docx import Document
import pandas as pd
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    ListFlowable, ListItem
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
import re
import markdown

# === CONFIGURACIÓN CLIENTE OPENAI ===
client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

# === ESTILOS Y GRÁFICOS ===
logo_path = "logo-grupo-epm (1).png"
img = Image.open(logo_path)
buffered = io.BytesIO()
img.save(buffered, format="PNG")
img_b64 = base64.b64encode(buffered.getvalue()).decode()
st.markdown(f"""
<div style='position: absolute; top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999;'>
    <img src="data:image/png;base64,{img_b64}" width="233px"/>
</div>
""", unsafe_allow_html=True)
st.markdown("<div style='margin-top: 220px;'></div>", unsafe_allow_html=True)

# Fondo y tipografía
image_path = "fondo-julius-epm.png"
img = Image.open(image_path)
buffered = io.BytesIO()
img.save(buffered, format="PNG")
img_b64 = base64.b64encode(buffered.getvalue()).decode()
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat&display=swap');
html, body, [class*="css"] {{ font-family: 'Montserrat', sans-serif !important; }}
.stApp {{ background-image: url("data:image/jpeg;base64,{img_b64}"); background-repeat: no-repeat; background-position: top center; background-size: auto; background-attachment: scroll; }}
.stApp .main .block-container {{ background-image: linear-gradient(to bottom, transparent 330px, #240531 330px) !important; background-repeat: no-repeat !important; background-size: 100% 100% !important; border-radius: 20px !important; padding: 50px !important; max-width: 800px !important; margin: 2rem auto !important; }}
label, .stSelectbox label, .stMultiSelect label {{ color: white !important; font-size: 0.9em; }}
div.stButton > button {{ background-color: #ff5722; color: #ffffff !important; font-weight: bold; font-size: 16px; padding: 12px 24px; border-radius: 50px; border: none; width: 100%; margin-top: 10px; }}
div.stButton > button:hover {{ background-color: #e64a19; color:#4B006E !important; }}
</style>
""", unsafe_allow_html=True)

# === TÍTULOS PRINCIPALES ===
st.markdown(
    """
    <div style='position: relative; z-index: 1; padding-top: 50px;'>
        <h1 style='text-align: center;'>Simulador de crisis con IA</h1>
    </div>
    """, unsafe_allow_html=True)
st.markdown(
    """
    <div style='position: relative; z-index: 1;'>
        <h2 style='text-align: center;'>Sube tu briefing para iniciar la simulación</h2>
    </div>
    """, unsafe_allow_html=True)

# === CARGA DE PROMPT BASE ===
try:
    base_doc = Document("Prompt_base.docx")
    base_prompt = "\n".join(p.text for p in base_doc.paragraphs)
except Exception:
    st.error("No se pudo cargar 'Prompt_base.docx'. Asegúrate de tener el archivo en el directorio.")
    st.stop()

# === UPLOADER PARA BRIEFING ===
brief_file = st.file_uploader("Briefing", type=["docx", "txt", "csv"])

# === CAMPOS DE INPUT ADICIONALES ===
contexto = st.text_area("Contexto", disabled=True)
escenario1 = st.text_area("Escenario 1", disabled=True)
escenario2 = st.text_area("Escenario 2", disabled=True)
escenario3 = st.text_area("Escenario 3 (opcional)", disabled=True)

# === FUNCIONES AUXILIARES ===
def md_to_html(md_text: str) -> str:
    """Convierte Markdown a HTML válido usando la librería markdown"""
    return markdown.markdown(md_text)

# === GENERACIÓN DE INFORME PDF ===
def generar_informe(md_sections: list[str], output_path: str = "informe.pdf"):
    """Toma una lista de secciones en Markdown y genera un PDF formateado correctamente"""
    doc = SimpleDocTemplate(output_path)
    styles = getSampleStyleSheet()
    flowables = []

    for sec in md_sections:
        html = md_to_html(sec)
        para = Paragraph(html, styles['Normal'])
        flowables.append(para)
        flowables.append(Spacer(1, 0.5 * cm))

    doc.build(flowables)

# === LÓGICA PRINCIPAL ===
if brief_file:
    # Leer contenido
    if brief_file.type == "text/plain":
        text = str(brief_file.read(), 'utf-8')
    elif brief_file.type == "text/csv":
        df = pd.read_csv(brief_file)
        text = df.to_markdown()
    else:
        docx = Document(brief_file)
        text = "\n".join(p.text for p in docx.paragraphs)

    # Dividir en secciones según encabezados Markdown
    sections = re.split(r"(?m)^##+\s*", text)
    sections = [f"## {s}" for s in sections if s.strip()]

    # Generar informe
    generar_informe(sections, output_path="informe_copia.pdf")
    with open("informe_copia.pdf", "rb") as f:
        st.download_button("Descargar Informe", f, file_name="informe.pdf")
else:
    st.info("Sube un briefing para generar el informe.")

# === LOGO FINAL ===
final_logo_path = "logo-julius.png"
final_img = Image.open(final_logo_path)
buffered = io.BytesIO()
final_img.save(buffered, format="PNG")
final_img_b64 = base64.b64encode(buffered.getvalue()).decode()
st.markdown(
    f"""
    <div style='display: flex; justify-content: center; align-items: center; margin-top: 60px; margin-bottom: 40px;'>
        <img src="data:image/png;base64,{final_img_b64}" width="96" height="69"/>
    </div>
    """,
    unsafe_allow_html=True
)
