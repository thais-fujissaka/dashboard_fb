import streamlit as st
import pandas as pd
import datetime
import calendar
from utils.functions.general_functions_conciliacao import *
from utils.functions.general_functions import config_sidebar
from utils.functions.conciliacoes import *
from utils.queries_conciliacao import *


st.set_page_config(
    page_title="Conciliação FB - Casas",
    page_icon=":material/money_bag:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

col1, col2 = st.columns([5, 1], vertical_alignment='center')
with col1:
    st.title(":material/money_bag: Conciliação por casa")
with col2:
    st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Recuperando dados
df_casas = GET_CASAS()

# Filtrando Datas
datas = calcular_datas()


# Campos de seleção de data
col1, col2 = st.columns(2)

with col1:
    d_inicial = st.date_input("Data de início", value=datas['jan_ano_atual'], min_value=datas['jan_ano_passado'], max_value=datas['dez_ano_atual'], format="DD/MM/YYYY")
with col2:
    d_final = st.date_input("Data de fim", value=datas['fim_mes_atual'], min_value=datas['jan_ano_passado'], max_value=datas['dez_ano_atual'], format="DD/MM/YYYY")

# Convertendo as datas dos inputs para datetime
start_date = pd.to_datetime(d_inicial)
end_date = pd.to_datetime(d_final)

if start_date > end_date:
    st.warning("A data de fim deve ser maior que a data de início!")

else:
    # Filtrando casas
    casas = df_casas['Casa'].tolist()
    
    # Troca o valor na lista
    casas = ["Todas as casas" if c == "All bar" else c for c in casas]
    casa = st.selectbox("Casa", casas)
    if casa == "Todas as casas":
        casa = "All bar"

    # Definindo um dicionário para mapear nomes de casas a IDs de casas
    mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))

    # Obtendo o ID da casa selecionada
    id_casa = mapeamento_casas[casa]
    
    st.divider()

    if casa == 'All bar': # Todas as casas
        conciliacao_inicial(id_casa, casa, start_date, end_date, "Geral")
    
    else: # Selecionou uma casa
        tab1, tab2, tab3 = st.tabs(['Geral', 'Contas a Pagar', 'Contas a Receber'])
        with tab1: # Exibe conciliação geral
            conciliacao_inicial(id_casa, casa, start_date, end_date, "Geral")
            
        with tab2: # Exibe apenas itens do Contas a Pagar
            conciliacao_inicial(id_casa, casa, start_date, end_date, "Contas a Pagar")

        with tab3: # Exibe apenas itens do Contas a Receber
            conciliacao_inicial(id_casa, casa, start_date, end_date, "Contas a Receber")


    