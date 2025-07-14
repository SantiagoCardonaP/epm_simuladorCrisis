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
def md_to_html(txt):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", txt)

def parse_markdown(md_text):
    styles = getSampleStyleSheet()
    story = []
    table_buffer = []
    in_table = False

    def flush_table():
        nonlocal table_buffer, in_table
        table = Table(table_buffer, hAlign='LEFT')
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff5722')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))
        table_buffer = []
        in_table = False

    for line in md_text.split("\n"):
        # tabla markdown
        if re.match(r"^\s*\|[-\s|]+$", line):
            continue
        if line.startswith('|') and line.count('|') > 1:
            cells = [c.strip() for c in line.strip('|').split('|')]
            table_buffer.append(cells)
            in_table = True
            continue
        if in_table:
            flush_table()
        # encabezados
        if line.startswith('# '):
            story.append(Paragraph(md_to_html(line[2:]), styles['Heading1']))
        elif line.startswith('## '):
            story.append(Paragraph(md_to_html(line[3:]), styles['Heading2']))
        # listas numeradas
        elif re.match(r"^\d+\.\s+", line):
            num, text = re.match(r"^(\d+)\.\s+(.+)", line).groups()
            item = Paragraph(md_to_html(text), styles['Normal'])
            story.append(ListFlowable([ListItem(item, value=int(num))], bulletType='1', leftIndent=12))
        # viñetas
        elif line.startswith('- '):
            item = Paragraph(md_to_html(line[2:]), styles['Normal'])
            story.append(ListFlowable([ListItem(item)], bulletType='bullet', leftIndent=12))
        # párrafo normal
        else:
            if not line.strip():
                story.append(Spacer(1, 8))
            else:
                story.append(Paragraph(md_to_html(line), styles['Normal']))
    if in_table:
        flush_table()
    return story

if brief_file:
    if brief_file.name.lower().endswith('.docx'):
        doc = Document(brief_file)
        briefing = "\n".join(p.text for p in doc.paragraphs)
    elif brief_file.name.lower().endswith('.txt'):
        briefing = brief_file.read().decode('utf-8')
    else:
        df_br = pd.read_csv(brief_file)
        briefing = df_br.to_csv(index=False)

    # Botón para generar y descargar informe
    if st.button('Generar informe'):
        prompt_md = f"""
Por favor, genera un informe estructurado con el título: 'Escenarios de Crisis'.

Este es el prompt que debes usar como base:
{base_prompt}

Incluye tablas cuando aplique. Usa el siguiente contenido como brief:
{briefing}
"""
        with st.spinner('Generando informe...'):
            resp = client.chat.completions.create(
                model='gpt-4o',
                messages=[{'role':'user','content':prompt_md}],
                temperature=0.3
            )
        md = resp.choices[0].message.content

        # Generar PDF usando ReportLab
        buffer_pdf = io.BytesIO()
        doc_pdf = SimpleDocTemplate(buffer_pdf,
                                     rightMargin=2*cm, leftMargin=2*cm,
                                     topMargin=2*cm, bottomMargin=2*cm)
        story = parse_markdown(md)
        doc_pdf.build(story)
        pdf_bytes = buffer_pdf.getvalue()

        # Botón de descarga centrado y estilizado
        b64 = base64.b64encode(pdf_bytes).decode()
        download_html = f"""
<div style=\"display:flex;justify-content:center;align-items:center;margin:20px 0;\"> 
  <a href=\"data:application/pdf;base64,{b64}\" download=\"informe_crisis.pdf\" style=\"color:#ffffff;font-weight:bold;padding:12px 24px;border-radius:50px;text-decoration:none;font-size:16px;\">Descargar informe PDF</a>
</div>
"""
        st.markdown(download_html, unsafe_allow_html=True)

    # === PREGUNTAS ABIERTAS EN FORMULARIO ===
    st.markdown("<h3>¿Tienes alguna pregunta adicional sobre la simulación?</h3>", unsafe_allow_html=True)
    with st.form("preguntas_form"):
        user_input = st.text_area("Escribe tu pregunta aquí…")
        submit = st.form_submit_button("Generar respuesta")
        if submit and user_input:
            prompt_q = f"""
Toma el siguiente briefing y responde a la pregunta de forma clara:

Briefing:
{briefing}

Pregunta:
{user_input}
"""
            with st.spinner('Generando respuesta…'):
                resp_q = client.chat.completions.create(
                    model='gpt-4o',
                    messages=[{'role':'user','content':prompt_q}],
                    temperature=0.3
                )
            answer = resp_q.choices[0].message.content
            st.markdown("### Respuesta de la IA")
            st.write(answer)

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
