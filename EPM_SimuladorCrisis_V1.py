import streamlit as st
from openai import OpenAI
from PIL import Image
import base64
import io
from docx import Document
import pandas as pd
import markdown2
from weasyprint import HTML

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
st.markdown("<div style='margin-top: 120px;'></div>", unsafe_allow_html=True)

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

# === TÍTULO PRINCIPAL ===
st.markdown("<h1 style='text-align: center;'>Simulador de crisis con IA</h1>", unsafe_allow_html=True)
st.markdown("<h2 style='text-align: center;'>Sube tu briefing para iniciar la simulación</h2>", unsafe_allow_html=True)

# === CARGA DE PROMPT BASE ===
try:
    base_doc = Document("Prompt_base.docx")
    base_prompt = "\n".join(p.text for p in base_doc.paragraphs)
except Exception:
    st.error("No se pudo cargar 'Prompt_base.docx'. Asegúrate de tener el archivo en el directorio.")
    st.stop()

# === UPLOADER PARA BRIEFING ===
brief_file = st.file_uploader("Briefing", type=["docx", "txt", "csv"] )

if brief_file:
    # Leer briefing según tipo
    if brief_file.name.lower().endswith('.docx'):
        doc = Document(brief_file)
        briefing = "\n".join(p.text for p in doc.paragraphs)
    elif brief_file.name.lower().endswith('.txt'):
        briefing = brief_file.read().decode('utf-8')
    else:
        df_br = pd.read_csv(brief_file)
        briefing = df_br.to_csv(index=False)

    # Botón para descargar informe en PDF
    if st.button('Descargar informe'):
        prompt_md = f"""
Por favor, genera un informe de crisis en **Markdown** estructurado con:

# Informe de Crisis

## 1. Escenario más factible
- Descripción detallada.

## 2. Percepciones
- Lista de percepciones clave.

## 3. Recomendaciones
- Lista de recomendaciones accionables.

Incluye tablas y placeholders para gráficos cuando aplique. Usa el siguiente contenido como briefing:

{briefing}
"""
        with st.spinner('Generando informe...'):
            resp = client.chat.completions.create(
                model='gpt-4o',
                messages=[{'role':'user','content':prompt_md}],
                temperature=0.3
            )
        md = resp.choices[0].message.content

        # Convertir Markdown a HTML y generar PDF
        html = markdown2.markdown(md)
        css = """
        <style>
        body { font-family: Arial, sans-serif; padding: 1cm; }
        h1, h2, h3 { color: #240531; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #ff5722; color: white; }
        </style>
        """
        html_full = css + html
        pdf_bytes = HTML(string=html_full).write_pdf()

        b64 = base64.b64encode(pdf_bytes).decode()
        href = f"<a href='data:application/pdf;base64,{b64}' download='informe_crisis.pdf'>Descargar informe PDF</a>"
        st.markdown(href, unsafe_allow_html=True)

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
