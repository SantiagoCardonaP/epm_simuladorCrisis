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
from reportlab.lib.styles import getSampleStyleSheet
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
        <h3 style='text-align: center;'>Escribe un contexto y sus posibles escenarios para iniciar la simulación</h3>
    </div>
    """, unsafe_allow_html=True)

st.markdown(
    """
    <div style='position: relative; z-index: 1;'>
        <h6 style='text-align: center;'>El simulador esta pre cargado con información para efectos de la demostración</h6>
    </div>
    """, unsafe_allow_html=True)

# === CARGA DE PROMPT BASE ===
try:
    base_doc = Document("Prompt_base.docx")
    base_prompt = "\n".join(p.text for p in base_doc.paragraphs)
except Exception:
    st.error("No se pudo cargar 'Prompt_base.docx'. Asegúrate de tener el archivo en el directorio.")
    st.stop()

# === CAMPOS DE INPUT PRELLENADOS ===
contexto = st.text_area(
    "Contexto",
    value="Durante la segunda jornada del Foro de las Américas, la principal empresa de servicios públicos de del país con operación en Antioquia con presencia en energía, agua y gas. Su filial Ticsa en México, fueron víctimas de un ataque de tipo ransomware que comprometió el sistema de medición y facturación de consumos, dejando suspendido el servicio para más de 7 millones de usuarios, incluidos hogares, grandes clientes industriales y hospitales. La filtración de una imagen del sistema SCADA, difundida sin contexto técnico, desató una ola de desinformación en redes sociales que escaló rápidamente hacia teorías conspirativas y narrativas de sabotaje.\n\nLa magnitud del incidente, su sincronización con un evento internacional de alta visibilidad y la falta inicial de contención comunicacional, generaron un entorno de pánico ciudadano, presión política y riesgo de sanciones regulatorias.\n\nEl escenario pone en riesgo no solo la continuidad operativa y comercial de la compañía, sino también su reputación como actor estratégico en la infraestructura crítica del país y su credibilidad frente a audiencias clave como gobierno, inversionistas y opinión pública.",
    height=200
)
escenario1 = st.text_area(
    "Escenario 1",
    value="Los medios de comunicación priorizan una narrativa escandalosa. Con titulares incendiarios, los influenciadores crean teorías de conspiración con alta Credibilidad entre las audiencias. El plan de mitigación no presenta resultados que mejoren la percepción y disminuyan los titulares y los contenidos virales negativos.",
    height=150
)
escenario2 = st.text_area(
    "Escenario 2",
    value="Los medios de comunicación se tornan informativos y dejan atrás titulares incendiarios. Se concentran en informar el minuto a minuto y la desinformación de contenidos virales comienza a bajar gracias a los contenidos informativos que la marca despliegue a través de influenciadores, embajadores de marca y canales oficiales.",
    height=150
)
escenario3 = st.text_area(
    "Escenario 3 (opcional)",
    value="Los medios de comunicación se tornan agresivos, sus titulares se tornan políticos, la superintendencia y los entes reguladores acusan a la compañía de ineficiente. Los contenidos virales se controlan gracias al despliegue de contenidos digitales que educan sobre el tema técnico, el plan de acción y las campañas de consciencia de uso adecuado de los servicios públicos.",
    height=150
)

# === FUNCIONES AUXILIARES ===
def md_to_html(text: str) -> str:
    """Reemplaza negritas Markdown por HTML"""
    return re.sub(r"\*\*(.+?)\*\**", r"<b>\1</b>", text)


def parse_markdown(md_text: str):
    """Convierte un texto en Markdown a una lista de flowables de ReportLab"""
    styles = getSampleStyleSheet()
    story = []
    table_buffer = []
    in_table = False

    def flush_table():
        nonlocal table_buffer, in_table
        if not table_buffer:
            return
        tbl = Table(table_buffer, hAlign='LEFT')
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ff5722')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 12))
        table_buffer = []
        in_table = False

    for line in md_text.splitlines():
        if re.match(r"^\s*\|[-\s|]+$", line):
            continue
        if line.startswith('|') and line.count('|') > 1:
            cells = [c.strip() for c in line.strip('|').split('|')]
            table_buffer.append(cells)
            in_table = True
            continue
        if in_table:
            flush_table()
        if line.startswith('###### '):
            story.append(Paragraph(md_to_html(line[7:]), styles['Heading6']))
        elif line.startswith('##### '):
            story.append(Paragraph(md_to_html(line[6:]), styles['Heading5']))
        elif line.startswith('#### '):
            story.append(Paragraph(md_to_html(line[5:]), styles['Heading4']))
        elif line.startswith('### '):
            story.append(Paragraph(md_to_html(line[4:]), styles['Heading3']))
        elif line.startswith('## '):
            story.append(Paragraph(md_to_html(line[3:]), styles['Heading2']))
        elif line.startswith('# '):
            story.append(Paragraph(md_to_html(line[2:]), styles['Heading1']))
        elif re.match(r"^\d+\.\s+", line):
            num, text = re.match(r"^(\d+)\.\s+(.+)", line).groups()
            item = Paragraph(md_to_html(text), styles['Normal'])
            story.append(ListFlowable([ListItem(item, value=int(num))], bulletType='1', leftIndent=12))
        elif line.startswith('- '):
            item = Paragraph(md_to_html(line[2:]), styles['Normal'])
            story.append(ListFlowable([ListItem(item)], bulletType='bullet', leftIndent=12))
        else:
            if not line.strip():
                story.append(Spacer(1, 8))
            else:
                story.append(Paragraph(md_to_html(line), styles['Normal']))
    if in_table:
        flush_table()
    return story

# === LÓGICA PRINCIPAL ===
if st.button('Simular escenarios'):
    briefing = f"Contexto:\n{contexto}\n\nEscenario 1:\n{escenario1}\n\nEscenario 2:\n{escenario2}\n\nEscenario 3:\n{escenario3}"
    prompt_md = f"""
Por favor, genera un informe estructurado del escenario más probable con el título: 'Escenario de Crisis'.

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

    # Generar PDF
    buffer_pdf = io.BytesIO()
    doc_pdf = SimpleDocTemplate(buffer_pdf,
                                 rightMargin=2*cm, leftMargin=2*cm,
                                 topMargin=2*cm, bottomMargin=2*cm)
    story = parse_markdown(md)
    doc_pdf.build(story)
    pdf_bytes = buffer_pdf.getvalue()

    b64 = base64.b64encode(pdf_bytes).decode()
    download_html = f"""
<div style="display:flex;justify-content:center;align-items:center;margin:20px 0;"> 
  <a href="data:application/pdf;base64,{b64}" download="informe_crisis.pdf" style="color:#ffffff;font-weight:bold;padding:12px 24px;border-radius:50px;text-decoration:none;font-size:16px;">Descargar informe PDF</a>
</div>
"""
    st.markdown(download_html, unsafe_allow_html=True)

# === PREGUNTAS ABIERTAS ===
st.markdown("<h3>¿Tienes alguna pregunta adicional sobre la simulación?</h3>", unsafe_allow_html=True)
with st.form("preguntas_form"):
    user_input = st.text_area("Escribe tu pregunta aquí…")
    submit = st.form_submit_button("Generar respuesta")
    if submit and user_input:
        prompt_q = f"""
Toma el siguiente briefing y responde a la pregunta de forma clara:

Briefing:
{contexto}\n\n{escenario1}\n\n{escenario2}\n\n{escenario3}

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
