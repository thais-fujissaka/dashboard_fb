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
    page_title="Categorização de descontos",
    page_icon=":material/list:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/list: Categorização - Descontos")
st.divider()

# Seletor de casa
casas = ['Arcos', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Léo - Centro', 'Blue Note - São Paulo', 'BNSP', 'Edifício Rolim', 'Girondino', 'Girondino - CCBB', 'Jacaré', 'Love Cabaret', 'Terraço Notiê', 'The Cavern', 'Orfeu', 'Riviera']
casa = st.selectbox("Selecione a casa referente ao arquivo de Descontos:", casas)
st.divider()

if casa == 'Notiê - Priceless' or casa == 'Terraço Notiê':
    regras_categoria = {
        'funcionario|funcionário|funcionaria|funcionária': "COLABORADOR (30%)",
        'gerência|gerencia|coord': 'CONSUMO GERENCIAL',
        'master|mastecard|mastetcard': 'CONVÊNIO',
        'taxa rolha|taxa de rolha|rolha': 'CORTESIA',
        'marketing': 'MARKETING',
        # 'ajuste': 'OPERACIONAL',
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
        "11|12": "MARKETING",
        "18": "MÚSICOS",
        "20": "PROMOÇÃO",
        'teste': 'TESTE',
        '14': None
    }

if casa == 'Bar Brahma - Centro':
    regras_categoria = {
        "gerencial|gerente|garçonete|garconete|gerencia|coord|vitorino|tia luiza|tua luiza|técnico|tecnico|almoço robson|almoço jéssica|chef|israel": "CONSUMO GERENCIAL",
        "aoas": "CONTA ASSINADA", 
        "evento": "EVENTOS",
        "market|marketing|mkt": "MARKETING",
        "voucher|vaucher|cantor|dj|banda|musico|músico|música|naninha|samba|criole|mágicos": "MÚSICOS",
        "troco|serviço|operac": "OPERACIONAL",
        "polícia|pm|policia": "OUTROS",
        "dois por um|2x1|2por1|2 por 1|2por 1|gourmet": "PROMOÇÃO",
        "reunião ti": "REUNIÃO - TI",
        "treinamento": "TREINAMENTO"
    }

if casa == 'Bar Brahma - Granja':
    regras_categoria = {
        'funcionário|funcionario': 'COLABORADOR (30%)',
        'refeição|coord|cordenador|maicon|técnico som|dupla jornada': 'CONSUMO GERENCIAL',
        'musico|dj|música|thais|técnico de som': 'MÚSICOS',
        'logista|logísta|nilsem|nielsemm|nilsemm|nilsennm|lojista|lojistq|santander|cadastro|meta|flar': 'CONVÊNIO',
        'niver': 'CORTESIA',
        # 'marketing': 'MARKETING',
        'permuta|permura': 'PERMUTA',
        '2por 1|2 por 1|2x1|2,por 1|voucher': 'PROMOÇÃO',
        'teste': 'TESTE',
        'treinamento':  'TREINAMENTO'
    }

if casa == 'Bar Léo - Centro':
    regras_categoria = {
        'logista|lojista|logosta|pz|sps': 'CONVÊNIO',
        'musico': 'MÚSICOS',
        'policia': 'OUTROS',
        'dois por um|2p1|gumer|gulmer|kumer|goume|cps': 'PROMOÇÃO'
    }

if casa == 'Blue Note' or casa == 'BNSP':
    regras_categoria = {
        'consumo coordenação|consumo gerência|consumo gerencia|consumos gerencia|coordenacao|coordenação|coordenador|chef|consumo mkt|alimentação mkt|gerente|alimentação gerencia': 'CONSUMO GERENCIAL',
        'socio|sócio': 'CONTA ASSINADA',
        'porto|azul|membro|mix|safra|inter|itaú|itau|convênio|convenio|condômino|condomínio|fiserv|sul america|sul ameruca': 'CONVÊNIO',
        'niver|cortesia|cheescake|torta belga':' CORTESIA',
        'artístico|artistico|dj|banda|músico|musico': 'MÚSICOS',
        'retirou serviço|correção': 'OPERACIONAL',
        'coworking|coworkimg|permuta': 'PERMUTA',
        'retorno almoço|voucher': 'PROMOÇÃO', 
        'treinamento': 'TREINAMENTO',
        'evento': 'EVENTOS',
        'reunião eventos': 'REUNIÃO - EVENTOS',
        'reunião t.i': 'REUNIÃO - TI'
    }

if casa == 'Girondino':
    regras_categoria = {
        'funcionário|funcionario|funcionário da casa|funcionario da casa|desconto funcionário|desconto funcionario|desconto funça|staff da casa|estaff': 'COLABORADOR (30%)',
        'mkt': 'MARKETING',
        'consumo|alimentação segurança|alimentacao seguranca|almoço liderança|almoco lideranca': 'CONSUMO GERENCIAL',
        'niver': 'CORTESIA',
        'serviço': 'OPERACIONAL'
    }

if casa == 'Girondino - CCBB': 
    regras_categoria = {
        'ourocard|scolaboradorbb|colaboraforbb|bb|cbb|colaboraorbb|colaborado rbb|colabiradorbb': 'CONVÊNIO',
        'colaboradorfb|colabrador fb|volaboradpr': 'COLABORADOR (30%)',
        'colaborador fb- ccbb|colaborador fb - ccbb|colaborador fb-ccbb|consumo|socio': 'CONSUMO GERENCIAL',
        'mkt': 'MARKETING'
    }

if casa == 'Jacaré':
    regras_categoria = {
        'suchef|subchef|gerente|coordenador|chef|sub': 'CONSUMO GERENCIAL',
        'alvaro': 'CONTA ASSINADA',
        'bto': 'CONVÊNIO',
        'niver|anivesario': 'CORTESIA',
        'consumo musico|integrantes': 'MÚSICOS',
        "2 por 1|2 por1|2por 1|2 po 1|fidelidade|mastercard|mastecard|mastcard": 'PROMOÇÃO',
    }

if casa == 'Love Cabaret':
    regras_categoria = {
        '1|cod 1': 'MÚSICOS',
        '2|cod 5': 'CONSUMO GERENCIAL',
        'cod 4': 'CONTA ASSINADA',
        'cod 8|cod 15': 'CONVÊNIO',
        'cod 3|cod 10': 'CORTESIA',
        'cod 11|cod 12': 'MARKETING',
        'cod 9|cod 09': 'OPERACIONAL',
        'cod 14': 'TESTE'
    }

if casa == 'Edifício Rolim':
    regras_categoria = {
        'funcionario|desconto fb|ator': 'COLABORADOR (30%)',
        'niver': 'CORTESIA',
        'mkt': 'MARKETING'
    }

if casa == 'Orfeu':
    regras_categoria = {
        'colaborador fb': 'COLABORADOR (30%)',
        'coordenação|coordenacao|coordenador|gerente|gerência': 'CONSUMO GERENCIAL',
        'niver|níver': 'CORTESIA',
        'sem troco': 'OPERACIONAL',
        'permuta': 'PERMUTA'
    }

if casa == 'Riviera':
    regras_categoria = {
        'desconto func|funcionario|funcionário|bar dos arcos|bar brahma': 'COLABORADOR (30%)',
        'consumo|alimentacao -|alimentação -|coordenacao|oordenacao|coordenação|coordenacai|chef|gerente|lideranca|liderança|luderanca|gerencia|coirdenaxao|coorfenacao|ciordenacao|coirfenacao|coordenaçao|consumação': 'CONSUMO GERENCIAL',
        'morador|convênio|convenio': 'CONVÊNIO',
        'niver|nuver|cortesia|anibersariante|anovetsatio|anivetsario|ani etsatio': 'CORTESIA',
        'evento': 'EVENTOS',
        'marketing|mkt': 'MARKETING',
        'troco|troci|ajuste': 'OPERACIONAL'
    }


# Dar upload na planilha de descontos da zig
uploaded_file = st.file_uploader("Selecione um arquivo .xlsx do seu computador:", type="xlsx")

if not uploaded_file:
    st.write("Adicione um arquivo .xlsx de Descontos para categorizá-los")

# Se arquivo adicionado, prossegue
else:
    # Lê o arquivo adicionado
    df = pd.read_excel(uploaded_file, skiprows=3)
    st.divider()
    st.subheader('Tabela original')
    st.dataframe(df, hide_index=True)
    st.divider()

    # Categorizando
    df_categorizado = df.copy()

    # Problema das planilhas que vem com a justificativa na coluna de categoria (zig)
    if casa == 'Girondino - CCBB' or casa == 'Blue Note' or casa == 'BNSP' or casa == 'Riviera' or casa == 'Terraço Notiê':
        mascara = (
            df_categorizado['Justificativa'].isna() |
            df_categorizado['Justificativa'].str.strip().str.lower().eq('h') |
            df_categorizado['Justificativa'].str.strip().str.lower().eq('g')
        )

        df_categorizado.loc[mascara, 'Justificativa'] = df_categorizado.loc[mascara, 'Categoria']

    # Garante que a coluna existe
    if "Categoria" not in df_categorizado.columns:
        df_categorizado["Categoria"] = None

    # Converte a justificativa para minúsculas (pra facilitar a busca)
    df_categorizado["justificativa_minusculo"] = df_categorizado["Justificativa"].astype(str).str.lower()
    df_categorizado["cliente_minusculo"] = df_categorizado["Clientes"].astype(str).str.lower()

    # Aplica as regras uma a uma
    for padrao, categoria in regras_categoria.items():
        if 'banda' in padrao or 'criole' in padrao or 'musico' in padrao or 'músico' in padrao: # Bar Brahma - Centro
            condicao = (
                df_categorizado["cliente_minusculo"].str.contains(padrao, na=False) |
                df_categorizado["justificativa_minusculo"].str.contains(padrao, na=False) 
            )
        elif 'aoas' in padrao: # Bar Brahma - Centro
            condicao = df_categorizado["cliente_minusculo"].str.contains(padrao, na=False)
        
        else:
            condicao = df_categorizado["justificativa_minusculo"].str.contains(padrao, na=False)    
        
        df_categorizado.loc[condicao, "Categoria"] = categoria
        
    # Remove a coluna auxiliar
    df_categorizado.drop(columns=["justificativa_minusculo", "cliente_minusculo"], inplace=True)

    # Renomeando colunas para download em excel e importação na UDF
    df_download = df_categorizado.copy()
    
    # Adiciona coluna da casa para download
    df_download['Empresa'] = casa 

    # Resgata mes e ano dos dados para nomear excel
    df_download['Mes_Ano'] = df_download['Data'].dt.strftime("%m%Y")
    mes_ano = df_download['Mes_Ano'].unique().tolist()
    mes_ano = mes_ano[0]
    
    df_download = df_download[['Empresa', 'Funcionário', 'Data', 'Clientes', 'Justificativa', 'Categoria', 'Produtos', 'Porcentagem', 'Desconto']]
    df_download = df_download.rename(columns={
        'Empresa': 'EMPRESA',
        'Funcionário': 'FUNCIONARIO',
        'Data': 'DATA',
        'Clientes': 'CLIENTES',
        'Justificativa': 'JUSTIFICATIVA',
        'Categoria': 'CATEGORIA',
        'Produtos': 'PRODUTOS',
        'Porcentagem': 'PORCENTAGEM',
        'Desconto': 'DESCONTO'
    })
    
    # Mostra o resultado
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader('Descontos categorizados') 
    with col2:
        button_download(df_download, f"Descontos - {casa} - {mes_ano}", f"Descontos - {casa}")

    st.info('Atenção para as células com categoria vazia, caso haja.')
    st.dataframe(df_categorizado, hide_index=True)
    
