import streamlit as st
import pandas as pd
from utils.functions.general_functions_conciliacao import *
from utils.functions.general_functions import config_sidebar
from utils.functions.ajustes import *
from utils.queries_conciliacao import *
from datetime import datetime


st.set_page_config(
  page_title="Conciliação FB - Ajustes",
  page_icon=":material/instant_mix:",
  layout="wide",
  initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Main.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/instant_mix: Ajustes")
st.divider()

# Recuperando dados
df_casas = GET_CASAS()

# Filtrando por casa e ano
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
  ano_atual = datetime.now().year 
  anos = list(range(2024, ano_atual+1))
  index_padrao = anos.index(ano_atual)
  ano = st.selectbox("Selecione um ano:", anos, index=index_padrao)

st.divider()

# Define df usados nos gráficos individuais de casa (de acordo com casa e data dos seletores)
df_ajustes_filtrado = define_df_ajustes(id_casa, ano)
lista_ajustes_pos_mes_fmt, lista_ajustes_neg_mes_fmt = total_ajustes_mes(df_ajustes_filtrado)
lista_qtd_ajustes_mes = qtd_ajustes_mes(df_ajustes_filtrado)


# Lista nomes das casas válidas
casas_validas = ['Arcos', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Brahma Paulista', 'Bar Léo - Centro', 'Blue Note - São Paulo', 'Edificio Rolim', 'Escritório Fabrica de Bares', 'Girondino', 'Girondino - CCBB', 'Jacaré', 'Love Cabaret', 'Orfeu', 'Priceless', 'Riviera Bar', 'Sanduiche comunicação LTDA', 'Tempus Fugit  Ltda', 'Ultra Evil Premium Ltda']

# Lista de quantidade de ajustes por mês de cada casa
lista_qtd_ajustes_arcos = lista_ajustes_casa("Arcos", ano)
lista_qtd_ajustes_b_centro = lista_ajustes_casa("Bar Brahma - Centro", ano)
lista_qtd_ajustes_b_granja = lista_ajustes_casa("Bar Brahma - Granja", ano)
lista_qtd_ajustes_b_paulista = lista_ajustes_casa("Bar Brahma Paulista", ano)
lista_qtd_ajustes_leo_centro = lista_ajustes_casa("Bar Léo - Centro", ano)
lista_qtd_ajustes_blue_note = lista_ajustes_casa("Blue Note - São Paulo", ano)
lista_qtd_ajustes_rolim = lista_ajustes_casa("Edifício Rolim", ano)
lista_qtd_ajustes_fb = lista_ajustes_casa("Escritório Fabrica de Bares", ano)
lista_qtd_ajustes_girondino = lista_ajustes_casa("Girondino ", ano)
lista_qtd_ajustes_girondino_ccbb = lista_ajustes_casa("Girondino - CCBB", ano)
lista_qtd_ajustes_jacare = lista_ajustes_casa("Jacaré", ano)
lista_qtd_ajustes_love = lista_ajustes_casa("Love Cabaret", ano)
lista_qtd_ajustes_orfeu = lista_ajustes_casa("Orfeu", ano)
lista_qtd_ajustes_priceless = lista_ajustes_casa("Priceless", ano)
lista_qtd_ajustes_riviera = lista_ajustes_casa("Riviera Bar", ano)
lista_qtd_ajustes_sanduiche = lista_ajustes_casa("Sanduiche comunicação LTDA ", ano)
lista_qtd_ajustes_tempus = lista_ajustes_casa("Tempus Fugit  Ltda ", ano)
lista_qtd_ajustes_ultra = lista_ajustes_casa("Ultra Evil Premium Ltda ", ano)


lista_ajustes_casas = [
  lista_qtd_ajustes_arcos,
  lista_qtd_ajustes_b_centro,
  lista_qtd_ajustes_b_granja,
  lista_qtd_ajustes_b_paulista,
  lista_qtd_ajustes_leo_centro,
  lista_qtd_ajustes_blue_note,
  lista_qtd_ajustes_rolim,
  lista_qtd_ajustes_fb,
  lista_qtd_ajustes_girondino,
  lista_qtd_ajustes_girondino_ccbb,
  lista_qtd_ajustes_jacare,
  lista_qtd_ajustes_love,
  lista_qtd_ajustes_orfeu,
  lista_qtd_ajustes_priceless,
  lista_qtd_ajustes_riviera,
  lista_qtd_ajustes_sanduiche,
  lista_qtd_ajustes_tempus,
  lista_qtd_ajustes_ultra
]


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
      
  

