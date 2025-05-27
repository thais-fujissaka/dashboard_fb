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
from utils.user import *

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_title="Faturamento Bruto",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():

	st.markdown(" <style>iframe{ height: 300px !important } ", unsafe_allow_html=True)

	config_sidebar()

	col1, col2, col3 = st.columns([6, 1, 1])
	with col1:
		st.title(":moneybag: Faturamento Bruto")
	with col2:
		st.button(label='Atualizar', key='atualizar_gazit', on_click=st.cache_data.clear)
	with col3:
		if st.button('Logout', key='logout_gazit'):
			logout()
	st.divider()

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
		'Valor_Locacao_Mirante': float,
		'Valor_Imposto': float,
		'Valor_AB': float,
		'Valor_Total': float,
		'Valor_Locacao_Total': float
	}
	df_eventos = df_eventos.astype(tipos_de_dados_eventos, errors='ignore')
	df_eventos['Data_Contratacao'] = pd.to_datetime(df_eventos['Data_Contratacao'], errors='coerce')
	df_eventos['Data_Evento'] = pd.to_datetime(df_eventos['Data_Evento'], errors='coerce')

	# Formata tipos de dados do dataframe de parcelas
	tipos_de_dados_parcelas = {
		'Valor_Parcela': float,
		'Categoria_Parcela': str
	}
	df_parcelas = df_parcelas.astype(tipos_de_dados_parcelas, errors='ignore')
	df_parcelas['Data_Vencimento'] = pd.to_datetime(df_parcelas['Data_Vencimento'], errors='coerce')
	df_parcelas['Data_Recebimento'] = pd.to_datetime(df_parcelas['Data_Recebimento'], errors='coerce')

	# Adiciona coluna de concatenação de ID e Nome do Evento
	df_eventos['ID_Nome_Evento'] = df_eventos['ID_Evento'].astype(str) + " - " + df_eventos['Nome_do_Evento']

	# Calcula o valor de repasse para Gazit
	df_eventos = calcular_repasses_gazit(df_eventos)

	# Seletor de ano
	col0, col1, col2 = st.columns(3, gap="large", vertical_alignment="center")
	with col0:
		id_casa, casa, id_zigpay = input_selecao_casas(key='faturamento_bruto')
	with col1:
		filtro_data = st.segmented_control(
			label="Filtrar por Data de:",
			options=["Competência", "Recebimento (Caixa)"],
			selection_mode="single",
			default="Competência"
		)
	with col2:
		ano = seletor_ano(2024, 2025, key='ano_faturamento')
	
	st.divider()

	df_parcelas_filtradas_por_data = get_parcelas_por_tipo_data(df_parcelas, df_eventos, filtro_data, ano)
	
	if casa == "Todas as Casas":
		st.markdown("## Por Categoria")
		montar_tabs_geral(df_parcelas_filtradas_por_data, casa, filtro_data)
				
	else:
		df_parcelas_casa = df_filtrar_casa(df_parcelas_filtradas_por_data, casa)
		if casa == "Priceless":
			st.markdown("## Por Categoria")
			montar_tabs_priceless(df_parcelas_casa, df_eventos, filtro_data)
			
		else:
			montar_tabs_geral(df_parcelas_casa, casa, filtro_data)

	# st.markdown("### Por Tipo de Evento", help="Social, Corporativo, Turismo, Filmagem ou Sessão de Fotos")
	# st.markdown("### Por Modelo de Evento", help="Pacote Exclusivo, Consumação Mínima, Comanda Aberta / Couvert Antecipado ou Locação de Espaço")


if __name__ == '__main__':
  main()