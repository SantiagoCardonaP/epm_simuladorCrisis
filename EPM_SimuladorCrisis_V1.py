import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
from docx import Document
import pandas as pd
from fpdf import FPDF

# === CONFIGURACIÓN CLIENTE OPENAI ===
client = OpenAI(api_key=st.secrets['OPENAI_API_KEY'])

# === ESTILOS Y GRÁFICOS ===
# Logo superior
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
st.markdown("<div style='margin-top: 120px;'></div>", unsafe_allow_html=True)

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
st.markdown("<h1 style='text-align: center;'>Simulador de crisis con IA</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Sube tu briefing para iniciar la simulación</h2>", unsafe_allow_html=True)

# === CARGA DE PROMPT BASE ===
base_doc = Document("Prompt_base.docx")
base_prompt = "\n".join(p.text for p in base_doc.paragraphs)

# === UPLOADER PARA BRIEFING ===
brief_file = st.file_uploader("Briefing", type=["docx", "txt", "csv"] )

if brief_file:
    # Leer contenido del briefing
    if brief_file.name.lower().endswith('.docx'):
        doc = Document(brief_file)
        briefing = "\n".join(p.text for p in doc.paragraphs)
    elif brief_file.name.lower().endswith('.txt'):
        briefing = brief_file.read().decode('utf-8')
    else:  # csv
        df_br = pd.read_csv(brief_file)
        briefing = df_br.to_csv(index=False)

    # Botón para generar y descargar informe
    if st.button('Descargar informe'):
        # Construir prompt para GPT
        prompt = f"""
{base_prompt}

Contexto y escenarios:
{briefing}

Con base en este briefing, analiza el escenario más factible y genera un informe con percepciones y recomendaciones detalladas.
"""
        with st.spinner('Generando informe...'):
            resp = client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=[{'role':'user','content':prompt}],
                temperature=0.4
            )
        informe = resp.choices[0].message.content

        # Crear PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.set_font('Arial', size=12)
        for line in informe.split('\n'):
            pdf.multi_cell(0, 10, line)
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        b64 = base64.b64encode(pdf_bytes).decode()
        href = f"<a href='data:application/octet-stream;base64,{b64}' download='informe_crisis.pdf'>Descargar informe PDF</a>"
        st.markdown(href, unsafe_allow_html=True)

# === PREGUNTAS ABIERTAS ==
st.markdown("<h3>¿Tienes alguna pregunta adicional sobre la simulación?</h3>", unsafe_allow_html=True)
user_input = st.text_area("Escribe tu pregunta aquí...", "")
if user_input:
    if st.button('Generar respuesta'):
        prompt_q = f"""
{base_prompt}

Briefing:
{briefing if brief_file else ''}

Pregunta:
{user_input}
"""
        with st.spinner('Generando respuesta...'):
            resp_q = client.chat.completions.create(
                model='gpt-3.5-turbo',
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
