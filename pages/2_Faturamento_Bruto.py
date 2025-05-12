import streamlit as st
import pandas as pd
import datetime
from workalendar.america import Brazil
import warnings
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries import *
from utils.functions.parcelas import *
from utils.functions.faturamento import *

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_title="Faturamento Bruto",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

st.markdown(" <style>iframe{ height: 300px !important } ", unsafe_allow_html=True)

config_sidebar()

# Recupera dados dos eventos e parcelas
df_eventos = GET_EVENTOS_PRICELESS()
df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()

# Formata tipos de dados do dataframe de eventos
tipos_de_dados_eventos = {
	'Valor_Locacao_Aroo_1': float,
	'Valor_Locacao_Aroo_2': float,
	'Valor_Locacao_Aroo_3': float,
	'Valor_Locacao_Anexo': float,
	'Valor_Locacao_Notie': float,
	'Valor_Imposto': float,
	'Valor_AB': float,
	'Valor_Total': float,
	'Valor_Locacao_Total': float
}
df_eventos = df_eventos.astype(tipos_de_dados_eventos, errors='ignore')

# Formata tipos de dados do dataframe de parcelas
tipos_de_dados_parcelas = {
	'Valor_Parcela': float,
	'Categoria_Parcela': str
}
df_parcelas = df_parcelas.astype(tipos_de_dados_parcelas, errors='ignore')

# Adiciona coluna de concatenação de ID e Nome do Evento
df_eventos['ID_Nome_Evento'] = df_eventos['ID_Evento'].astype(str) + " - " + df_eventos['Nome_do_Evento']

# Calcula o valor de repasse para Gazit
df_eventos = calcular_repasses_gazit(df_eventos)

st.title("Faturamento Bruto")
st.divider()

# Seletor de ano
col1, col2 = st.columns([1, 3])
with col1:
	ano = seletor_ano(2025, 2025, key='ano_faturamento')

df_filtrar_ano(df_parcelas, 'Data_Vencimento', ano)

# Calcula o valor de repasse para Gazit das parcelas
df_parcelas = calcular_repasses_gazit_parcelas(df_parcelas, df_eventos)

# FATURAMENTO #

# Gráfico de barras de Faturamento Bruto por mês, ver exemplo do faturamento por dia do dash da Luana
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Total de Eventos", "Locação Aroo", "Locação Anexo", "Locação Notiê", "Alimentos e Bebidas"])

with tab1:
    st.markdown("### Faturamento Total de Eventos")
    mes_faturamento_eventos = grafico_barras_total_eventos(df_parcelas)

with tab2:
	st.markdown("### Faturamento - Locação Aroo")
	mes_aroo = grafico_barras_locacao_aroo(df_parcelas, df_eventos)

with tab3:
	st.markdown("### Faturamento - Locação Anexo")
	mes_anexo = grafico_barras_locacao_anexo(df_parcelas, df_eventos)

with tab4:
	st.markdown("### Faturamento - Locação Notiê")
	mes_notie = grafico_barras_locacao_notie(df_parcelas, df_eventos)

with tab5:
	st.markdown("### Faturamento - Alimentos e Bebidas")
	mes_AB = grafico_barras_faturamento_AB(df_parcelas)
