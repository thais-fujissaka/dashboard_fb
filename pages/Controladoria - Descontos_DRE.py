import streamlit as st
import pandas as pd
import numpy as np
from utils.functions.general_functions import config_sidebar
from utils.functions.controladoria_descontos_dre import *
from utils.queries_conciliacao import GET_CASAS
from utils.queries_descontos_dre import *
from utils.components import button_download, seletor_ano, seletor_mes

pd.set_option('future.no_silent_downcasting', True)


st.set_page_config(
    page_title="Descontos DRE",
    page_icon=":material/percent_discount:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/percent_discount: Descontos DRE")
st.divider()

# Define variáveis importantes
df_casas = GET_CASAS()
df_descontos = GET_DESCONTOS()
id_casa = None
nome_casa = None
CMV = 0.29
DEDUCAO_FAT_ALIM = 0.43
DEDUCAO_FAT_BEB = 0.57

# Seletor de casa e ano
col1, col2, col3 = st.columns(3)

with col1:
    # casas = df_casas['Casa'].tolist()
    casas = ['Todas as casas', 'Arcos', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Léo - Centro', 'Blue Note - São Paulo', 'BNSP', 'Edificio Rolim', 'Girondino ', 'Girondino - CCBB', 'Jacaré', 'Love Cabaret', 'Orfeu', 'Riviera Bar', 'Terraço Notiê', 'The Cavern']
    casa = st.selectbox("Selecione uma casa:", casas)
    if casa == 'Todas as casas':
        nome_casa = Noneid_casa = None
    else:
        if casa == 'BNSP':
            nome_casa = 'Blue Note SP (Novo)'
        else:
            nome_casa = casa

        # Recupera id da casa
        mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))
        id_casa = mapeamento_casas[nome_casa]

with col2:
    mes = seletor_mes("Selecione o mês:", key="seletor_mes_descontos_dre")
    
with col3:
    ano = seletor_ano(2025, 2026, 'ano', 'Selecione o ano:')

st.divider()

df_descontos_filtrado = df_descontos[
    (df_descontos['DATA'].dt.month == int(mes)) &
    (df_descontos['DATA'].dt.year == ano)
].copy()

# Se selecionou uma casa específica, filtra
if id_casa is not None:
    df_descontos_filtrado = df_descontos_filtrado[
        df_descontos_filtrado['FK_CASA'] == id_casa
    ]

df_descontos_filtrado['Mês'] = df_descontos_filtrado['DATA'].dt.month
df_categorias_mes = df_descontos_filtrado.groupby(['FK_CASA', 'Mês', 'CATEGORIA'], as_index=False)['DESCONTO'].sum()
df_categorias_mes['CMV'] = CMV

# Calcula 'Aloca no Centro de Custo' par todas as categorias (menos EVENTOS)
df_categorias_mes['DESCONTO'] = df_categorias_mes['DESCONTO'].astype(float)
df_categorias_mes['CMV'] = df_categorias_mes['CMV'].astype(float)

condicao = ~df_categorias_mes['CATEGORIA'].isin(['EVENTO', 'EVENTOS'])
df_categorias_mes.loc[condicao, 'Aloca no Centro de Custo'] = df_categorias_mes['DESCONTO'] * df_categorias_mes['CMV']


if not df_categorias_mes.empty:
    # Mapeamento - Centro de Custo
    df_categorias_mes_centro_custo = mapeamento_centro_custo(casa, df_categorias_mes)

    # Calcula 'Permanece no Desconto' de acordo com 'Centro de Custo'
    df_categorias_mes_centro_custo["Permanece no Desconto"] = np.where(
        (df_categorias_mes_centro_custo["Centro de Custo"].isna()), # se é NULO
        df_categorias_mes_centro_custo["DESCONTO"], # usa o valor total do desconto
        df_categorias_mes_centro_custo["DESCONTO"] - df_categorias_mes_centro_custo["Aloca no Centro de Custo"]  # senão faz desconto menos 'Aloca no Centro de Custo'
    )   

    # Calcula Dedução de A&B para EVENTOS
    condicao = df_categorias_mes_centro_custo['CATEGORIA'].isin(['EVENTO', 'EVENTOS'])
    df_categorias_mes_centro_custo.loc[condicao, 'Dedução  Faturamento - Alimento'] = df_categorias_mes_centro_custo['DESCONTO'] * DEDUCAO_FAT_ALIM
    df_categorias_mes_centro_custo.loc[condicao, 'Dedução  Faturamento - Bebida'] = df_categorias_mes_centro_custo['DESCONTO'] * DEDUCAO_FAT_BEB

    # Mapeamento - Descontos - DRE
    df_categorias_mes_descontos_dre = mapeamento_descontos_dre(casa, df_categorias_mes_centro_custo)



st.dataframe(df_categorias_mes_descontos_dre, hide_index=True)
