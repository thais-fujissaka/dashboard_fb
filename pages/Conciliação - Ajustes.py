import streamlit as st
import pandas as pd
from utils.functions.general_functions_conciliacao import *
from utils.constants.general_constants import casas_validas
from utils.functions.general_functions import config_sidebar
from utils.functions.ajustes import *
from utils.queries_conciliacao import *
import datetime


casas_validas = [c for c in casas_validas if c != "All bar"]

st.set_page_config(
  page_title="Conciliação FB - Ajustes",
  page_icon=":material/instant_mix:",
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
  st.title(":material/instant_mix: Ajustes")
with col2:
  st.button(label='Atualizar dados', key='atualizar_forecast', on_click=st.cache_data.clear)
st.divider()

# Recuperando dados
df_casas = GET_CASAS()

# Filtrando por casa e ano
datas = calcular_datas()
col1, col2 = st.columns(2)

# Seletor de casa
with col1: 
  casas = df_casas['Casa'].tolist()

  casas = ["Todas as casas" if c == "All bar" else c for c in casas]
  casa = st.selectbox("Selecione uma casa:", casas)
  if casa == "Todas as casas":
    nome_casa = "Todas as casas"
    casa = "All bar"
  else:
     nome_casa = casa

  # Definindo um dicionário para mapear nomes de casas a IDs de casas
  mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))

  # Obtendo o ID da casa selecionada
  id_casa = mapeamento_casas[casa]

# Seletor de ano
with col2:
  ano_atual = datas['ano_atual'] 
  anos = list(range(2024, ano_atual+1))
  index_padrao = anos.index(ano_atual)
  ano = st.selectbox("Selecione um ano:", anos, index=index_padrao)

st.divider()

# Define df usados nos gráficos individuais de casa (de acordo com casa e data dos seletores)
df_ajustes_filtrado = define_df_ajustes(id_casa, ano)
lista_ajustes_pos_mes_fmt, lista_ajustes_neg_mes_fmt = total_ajustes_mes(df_ajustes_filtrado)
lista_qtd_ajustes_mes = qtd_ajustes_mes(df_ajustes_filtrado)


# Cria a lista da qtd de ajustes por mês de cada casa usando list comprehension
lista_ajustes_casas = [lista_ajustes_casa(casa, ano) for casa in casas_validas]

# Exibe gráfico de todos os meses e todas as casas
if nome_casa == 'Todas as casas':
  with st.container(border=True):
    col1, col2, col3 = st.columns([0.05, 4, 0.05], vertical_alignment="center")
    with col2:
      st.subheader("Contagem de ajustes por mês e por casa")
      grafico_ajustes_todas_casas(casas_validas, nomes_meses, lista_ajustes_casas)


with st.container(border=True):
  if (len(lista_ajustes_pos_mes_fmt) == 0 and len(lista_ajustes_neg_mes_fmt) == 0) and all(v == 0 for v in lista_qtd_ajustes_mes):
    st.warning(f"Não há ajustes a serem exibidos para {nome_casa}")
  else: 
    col1, col2, col3 = st.columns([0.1, 3, 0.1], vertical_alignment="center")
    with col2:
      # Exibe gráfico da contagem de ajustes por mês
      st.subheader(f"Contagem total de ajustes por mês - {nome_casa}")
      grafico_qtd_ajustes_mes(lista_qtd_ajustes_mes)
      st.divider()

      # Exibe gráfico de valor total de ajustes por mês
      st.subheader(f"Valor total de ajustes por mês - {nome_casa}")
      grafico_total_ajustes_mes(df_ajustes_filtrado, lista_ajustes_pos_mes_fmt, lista_ajustes_neg_mes_fmt)
      
  

