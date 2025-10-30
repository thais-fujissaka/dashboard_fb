import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.queries_conciliacao import GET_CASAS
from utils.components import button_download


# --- PATCH para ignorar cores inválidas no openpyxl ---
from openpyxl.styles.colors import WHITE, RGB
__old_rgb_set__ = RGB.__set__

def __rgb_set_fixed__(self, instance, value):
    try:
        __old_rgb_set__(self, instance, value)
    except ValueError as e:
        if e.args[0] == 'Colors must be aRGB hex values':
            __old_rgb_set__(self, instance, WHITE)  # substitui por branco

RGB.__set__ = __rgb_set_fixed__
# --- FIM DO PATCH ---


st.set_page_config(
    page_title="Forecast",
    page_icon=":material/event_upcoming:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title("Descontos")

# Seletor de casa
casas = ['Abaru - Priceless', 'Arcos', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Léo - Centro', 'Girondino', 'Girondino - CCBB']
casa = st.selectbox("Selecione a casa referente ao arquivo de Descontos:", casas)
st.divider()

if casa == 'Abaru - Priceless':
    regras_categoria = {
        'funcionario|funcionário|funcionaria|funcionária': "COLABORADOR (30%)",
        'gerência|gerencia|coord': 'CONSUMO GERENCIAL',
        'mastercard': 'CONVÊNIO',
        'taxa rolha| taxa de rolha': 'CORTESIA',
        'marketing': 'MARKETING',
        'ajuste': 'OPERACIONAL',
        'surpreend|surreend': 'PROMOÇÃO'
    }

if casa == 'Arcos':
    regras_categoria = {
        "1|2": "COLABORADOR (30%)",
        "4|teatro": "CONVÊNIO",
        "7|niver|cortesia": "CORTESIA",
        "16": "CONSUMO GERENCIAL",
        "10": "CONTA ASSINADA",
        "19": "EVENTOS",
        "12|mkt|marketing": "MARKETING",
        "18": "MÚSICOS",
        "20": "PROMOÇÃO",
        "14": "REUNIÃO - OPERAÇÕES"
    }

if casa == 'Bar Brahma - Centro':
    regras_categoria = {
        "gerencial|gerente|garçonete|garconete|gerencia|coord|vitorino|tia luiza|tua luiza|técnico|tecnico|tec|almoço robson|almoço jéssica|chef|israel": "CONSUMO GERENCIAL",
        "aoas": "CONTA ASSINADA", 
        "evento": "EVENTO",
        "market|marketing": "MARKETING",
        "voucher|cantor|dj|banda|musico|músico|naninha|samba|criole": "MÚSICOS",
        "troco|serviço|operac": "OPERACIONAL",
        "policiais|polícia|pm|policia": "OUTROS",
        "dois por um|2x1|2por1|2 por 1|2por 1|gourmet": "PROMOÇÃO",
        "reunião ti": "REUNIÃO - TI",
        "treinamento": "TREINAMENTO"
    }

if casa == 'Bar Brahma - Granja':
    regras_categoria = {
        'funcionário|funcionario': 'COLABORADOR (30%)',
        'refeição|coord|cordenador|maicon|dupla jornada': 'CONSUMO GERENCIAL',
        'musico|dj|música|thais': 'MÚSICOS',
        'logista|logísta|nilsem|nielsemm|nilsemm|nilsennm|lojista|lojistq|santander|cadastro|meta|flar': 'CONVÊNIO',
        'niver': 'CORTESIA',
        'marketing': 'MARKETING',
        'permuta': 'PERMUTA',
        '2por 1|2 por 1|2x1|2,por 1': 'PROMOÇÃO',
        'treinamento':  'TREINAMENTO'
    }

if casa == 'Bar Léo - Centro':
    regras_categoria = {
        'logista|lojista|logosta|pz|sps': 'CONVÊNIO',
        'musico': 'MÚSICOS',
        'policia': 'OUTROS',
        'dois por um|2p1|gumer|gulmer|kumer|goume|cps': 'PROMOÇÃO'
    }

if casa == 'Girondino':
    regras_categoria = {
        'funcionário|funcionario|funcionário da casa|funcionario da casa|desconto funcionário|desconto funcionario|desconto funça|staff da casa|estaff': 'COLABORADOR (30%)',
        'mkt': 'MARKETING',
        'consumo|alimentação segurança|alimentacao seguranca|almoço liderança|almoco lideranca': 'CONSUMO GERENCIAL',
        'niver': 'CORTESIA',
        'serviço': 'OPERACIONAL'
    }

# if casa == 'Girondino - CCBB': # PROBLEMA
#     regras_categoria = {
#         'colaborador|fb|volaboradpr': 'COLABORADOR (30%)',
#         'colaborador fb- ccbb|colaborador fb - ccbb|colaborador fb-ccbb|consumo|socio': 'CONSUMO GERENCIAL',
#         'ourocard|desconto colaborador': 'CONVÊNIO',
#         'mkt': 'MARKETING'
#     }


# Teste: dar upload na planilha de descontos
uploaded_file = st.file_uploader("Selecione um arquivo .xlsx do seu computador:", type="xlsx")

if not uploaded_file:
    st.write("Adicione um arquivo .xlsx de Descontos para categorizá-los")

# Se arquivo adicionado, prossegue
else:
    # Lê o arquivo adicionado
    df = pd.read_excel(uploaded_file, skiprows=3)
    st.divider()
    st.subheader('Tabela original')
    st.dataframe(df)
    st.divider()

    # Categorizando
    df_categorizado = df.copy()

    # Garante que a coluna existe
    if "Categoria" not in df_categorizado.columns:
        df_categorizado["Categoria"] = None

    # Converte a justificativa para minúsculas (pra facilitar a busca)
    df_categorizado["justificativa_minusculo"] = df_categorizado["Justificativa"].astype(str).str.lower()
    df_categorizado["cliente_minusculo"] = df_categorizado["Clientes"].astype(str).str.lower()

    # Aplica as regras uma a uma
    for padrao, categoria in regras_categoria.items():
        if 'banda' in padrao or 'criole' in padrao or 'musico' in padrao or 'músico' in padrao:
            condicao = (
                df_categorizado["cliente_minusculo"].str.contains(padrao, na=False) |
                df_categorizado["justificativa_minusculo"].str.contains(padrao, na=False) 
            )
        elif 'aoas' in padrao:
            condicao = df_categorizado["cliente_minusculo"].str.contains(padrao, na=False)
        
        else:
            condicao = df_categorizado["justificativa_minusculo"].str.contains(padrao, na=False)    
        
        df_categorizado.loc[condicao, "Categoria"] = categoria
        
    # Remove a coluna auxiliar
    df_categorizado.drop(columns=["justificativa_minusculo", "cliente_minusculo"], inplace=True)

    # Mostra o resultado
    st.divider()
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader('Descontos categorizados') 
    with col2:
        button_download(df_categorizado, f"Descontos - {casa}", f"Descontos - {casa}")

    # if casa == 'Bar Brahma - Centro':
    #     st.warning('As categorias COLABORADOR (30%) e CORTESIA não foram mapeadas.')
    st.info('Atenção para as células com categoria vazia.')
    st.dataframe(df_categorizado)
    
