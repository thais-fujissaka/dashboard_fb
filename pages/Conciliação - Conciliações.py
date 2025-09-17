import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from utils.functions.general_functions_conciliacao import *
from utils.functions.general_functions import config_sidebar
from utils.functions.conciliacoes import *
from utils.queries_conciliacao import *


st.set_page_config(
    page_title="Conciliação FB",
    page_icon=":material/money_bag:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Main.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/money_bag: Conciliação FB")
st.divider()

# Recuperando dados
df_casas = GET_CASAS()

# Filtrando Data
today = datetime.now()
last_year = today.year - 1
jan_last_year = datetime(last_year, 1, 1)
jan_this_year = datetime(today.year, 1, 1)
last_day_of_month = calendar.monthrange(today.year, today.month)[1]
this_month_this_year = datetime(today.year, today.month, last_day_of_month)
dec_this_year = datetime(today.year, 12, 31)

## 5 meses atras
month_sub_3 = today.month - 3
year = today.year

if month_sub_3 <= 0:
    # Se o mês resultante for menor ou igual a 0, ajustamos o ano e corrigimos o mês
    month_sub_3 += 12
    year -= 1

start_of_three_months_ago = datetime(year, month_sub_3, 1)

# Campos de seleção de data
col1, col2 = st.columns(2)

with col1:
    d_inicial = st.date_input("Data de início", value=jan_this_year, min_value=jan_last_year, max_value=dec_this_year, format="DD/MM/YYYY")
with col2:
    d_final = st.date_input("Data de fim", value=this_month_this_year, min_value=jan_last_year, max_value=dec_this_year, format="DD/MM/YYYY")

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


    