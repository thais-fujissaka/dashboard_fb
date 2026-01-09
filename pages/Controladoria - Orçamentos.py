import streamlit as st
import pandas as pd
import pymysql
from utils.functions.general_functions import config_sidebar
from utils.queries_conciliacao import GET_CASAS
from utils.components import button_download


# Conexão com o banco de dados
conn = pymysql.connect(
    host='homolog.cvuwkhnpr3rt.us-east-2.rds.amazonaws.com',
    user='fb_catarina_scabelli',
    password='wwAcH2xEFk2P3aUW',
    port=6303,
    database='EPM_FB',
    autocommit=True
)
c = conn.cursor()

# Consulta para recuperar class. cont. 1 de cada class_cont_2 da primeira coluna de forma confiável
query_class_cont = f'''
SELECT 
    tccg2.DESCRICAO AS Descricao_2,
    tccg1.DESCRICAO AS Descricao_1
FROM T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2
LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON (tccg2.FK_GRUPO_1 = tccg1.ID)
WHERE tccg2.DESCRICAO = %s
AND tccg1.FK_VERSAO_PLANO_CONTABIL = 103
'''

st.set_page_config(
    page_title="Subir Orçamentos",
    page_icon=":material/list:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/list: Subir Orçamentos")
st.divider()

# Seletor de casa
df_casas = GET_CASAS()
casas = ['Arcos', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Léo - Centro', 'Blue Note - São Paulo', 'BNSP', 'Edificio Rolim', 'Girondino ', 'Girondino - CCBB', 'Jacaré', 'Love Cabaret', 'Terraço Notiê', 'The Cavern', 'Orfeu', 'Riviera Bar']
casa = st.selectbox("Selecione a casa referente ao arquivo de Descontos:", casas)

# Recupera id da casa
mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))
if casa != 'BNSP' and casa != 'Terraço Notiê':
    id_casa = mapeamento_casas[casa]
elif casa == 'Terraço Notiê':
    id_casa = 162
elif casa == 'BNSP':
    id_casa = 131

st.divider()


# Dar upload na planilha de descontos da zig
uploaded_file = st.file_uploader("Selecione um arquivo .xlsx do seu computador:", type="xlsx")

if not uploaded_file:
    st.write("Adicione um arquivo .xlsx de Orçamento para transformá-lo")

# Se arquivo adicionado, prossegue
else:
    # Lê o arquivo adicionado
    df = pd.read_excel(uploaded_file, skiprows=3)
    st.divider()
    st.subheader('Tabela original')
    st.dataframe(df, hide_index=True)
    st.divider()

    df_transformado = df.copy()
    st.subheader('Tabela transformada')

    # Removendo colunas e linhas desnecessárias 
    df_transformado = df_transformado.drop(columns=['Unnamed: 1', 'Unnamed: 2', 'Unnamed: 3', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 6', '1º TRIMESTRE', '2º TRIMESTRE', '3º TRIMESTRE', '4º TRIMESTRE'])
    df_transformado = df_transformado.dropna(subset=['Unnamed: 0'])
    
    indice = df_transformado[df_transformado['Unnamed: 0'] == 'TOTAL - DESPESAS OPERATIVAS'].index # Remove todas as linhas abaixo disso
    if not indice.empty:
        df_transformado = df_transformado.loc[:indice[0] - 1]
    df_transformado = df_transformado.iloc[:-1]

    # Remove linhas que não são de orçamento / apenas títulos
    col = (
        df_transformado['Unnamed: 0']
        # .astype(str)
        # .str.replace('\xa0', ' ', regex=False)  # espaço invisível
        # .str.replace(r'\s+', ' ', regex=True)  # normaliza espaços
        # .str.strip()
    )
   
    contem_parenteses_negativo = col.str.contains(r'\(-\)', na=False) 
    contem_parenteses_positivo = col.str.contains(r'\(\+\)', na=False) 
    contem_cargos = col.str.contains(
        r'squad|chef|gerente|coord|adm|maitre|hostess|garçon|chop|cumin|bar|cozinh|saladeiro|pia|confeiteiro|copeiro|pizza|boqueta|churras|ajud|estoquista|aux|porteiro|bilheteiro|caixa|operador',
        case=False,
        na=False
    )

    excluir_exatos = {
        'FATURAMENTO BRUTO',
        'Eventos',
        '% sobre Receita Bruta',
        'RECEITA LÍQUIDA',
        '% sobre Receita Líquida',
        'Custos Artístico',
        'Custos Ténico de Som',
        '% sobre Receita Artístico',
        'MDO',
        'Serviços de Terceiros - Eventos',
        'Material de Consumo',
        'Manutenção Geral',
        'Transportes',
        'Locações',
        'Repasses Locação de Espaço',
        '% sobre Receita de Eventos',
        'MARGEM BRUTA DE CONTRIBUIÇÃO',
        '% sobre Receita',
        'PESSOAL',
        'E-Staff',
        '% sobre Receita c/ Squad', 
        '% sobre Receita s/ Squad',
        'Custo de Ocupação',
        'Utilidades',
        'Informática e TI',
        'Despesas Gerais',
        'Marketing',
        'Serviços de Terceiros',
        'Locação de Equipamentos',
        'Sistema de Franquias',
    }

    df_transformado = df_transformado[
        (~col.isin(excluir_exatos)) &    # remove títulos
        (~contem_parenteses_negativo) &  # remove (-)
        (~contem_parenteses_positivo) &  # remove (+)
        (~contem_cargos)                 # remove cargos de PJ e Salários
    ]

    # Renomeia nomes da planilha para class. cont. 2
    condicao = df_transformado['Unnamed: 0'] == 'Alimentação D'
    df_transformado.loc[condicao, 'Unnamed: 0'] = 'Insumos - Alimentos'

    condicao = df_transformado['Unnamed: 0'] == 'Bebida D'
    df_transformado.loc[condicao, 'Unnamed: 0'] = 'Insumos - Bebidas'

    condicao = df_transformado['Unnamed: 0'] == 'Embalagens'
    df_transformado.loc[condicao, 'Unnamed: 0'] = 'Insumos - Embalagens'

    condicao = df_transformado['Unnamed: 0'] == 'PJ'
    df_transformado.loc[condicao, 'Unnamed: 0'] = 'Mão de Obra - PJ'

    condicao = df_transformado['Unnamed: 0'] == 'Salários'
    df_transformado.loc[condicao, 'Unnamed: 0'] = 'Mão de Obra - Salários'
    
    
    # Cria coluna de class. cont. 2
    df_transformado['Classificacao 2'] = df_transformado['Unnamed: 0']
    
    lista_class_cont_2_primeira_coluna = df_transformado['Unnamed: 0'].tolist()

    for item in lista_class_cont_2_primeira_coluna:
        c.execute(query_class_cont, (item,))
        res = c.fetchone()

        if res:
            class_cont_1 = res[1]
        else:
            class_cont_1 = None  # 'Não encontrado'

        condicao = df_transformado['Unnamed: 0'] == item
        df_transformado.loc[condicao, 'Classificacao 1'] = class_cont_1
        
    st.dataframe(df_transformado, hide_index=True)
    

    # Mostra o resultado
    # col1, col2 = st.columns([4, 1])
    # with col1:
    #     st.subheader('Descontos categorizados') 
    # with col2:
    #     button_download(df_download, f"{casa} - {mes_ano}", f"Descontos - {casa}")

    # st.info('Atenção para as células com categoria vazia, caso haja.')
    # st.dataframe(df_categorizado, hide_index=True)
    
