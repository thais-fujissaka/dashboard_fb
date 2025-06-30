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

	st.markdown(" <style>iframe{ height: 320px !important } ", unsafe_allow_html=True)
	config_sidebar()

	# Header
	col1, col2, col3 = st.columns([6, 1, 1])
	with col1:
		st.title(":moneybag: Faturamento Bruto")
	with col2:
		st.button(label='Atualizar', key='atualizar_faturamento', on_click=st.cache_data.clear)
	with col3:
		if st.button('Logout', key='logout_faturamento'):
			logout()
	st.divider()

	# Recupera dados dos eventos e parcelas
	df_eventos = GET_EVENTOS_PRICELESS()
	df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()
	df_orcamentos = GET_ORCAMENTOS_EVENTOS()

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

	# Formata tipos de dados do dataframe de orcamentos
	tipos_de_dados_orcamentos = {
		'Valor': float
	}
	df_orcamentos = df_orcamentos.astype(tipos_de_dados_orcamentos, errors='ignore')

	# Adiciona coluna de concatenação de ID e Nome do Evento
	df_eventos['ID_Nome_Evento'] = df_eventos['ID_Evento'].astype(str) + " - " + df_eventos['Nome_do_Evento']

	# Calcula o valor de repasse para Gazit
	df_eventos = calcular_repasses_gazit(df_eventos)
	
	# Seletores
	col1, col2, col3 = st.columns([1, 1, 1], gap="large")
	with col1:
		lista_retirar_casas = ['Arcos', 'Bar Léo - Centro', 'Bar Léo - Vila Madalena', 'Blue Note - São Paulo', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Girondino - CCBB', 'Love Cabaret']
		id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='faturamento_bruto')
	with col2:
		ano = seletor_ano(2024, 2025, key='ano_faturamento')
	with col3:
		options_status_evento = ['Confirmado', 'Em negociação', 'Declinado']
		filtros_status_evento_faturamento = st.segmented_control('Status dos Eventos:', options_status_evento, selection_mode='multi', default=['Confirmado', 'Em negociação'], key='filtros_status_eventos')		
	st.divider()

	if not filtros_status_evento_faturamento:
			st.warning("Por favor, selecione pelo menos um status de evento.")
			st.stop()

	# Faturamento por Categoria
	with st.container(border=True):
		col1, col2, col3, col4 = st.columns([0.1, 1.2, 1.4, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown("## Faturamento Por Categoria")
			st.write("")
		with col3:
			filtro_data_categoria = "Competência"
			filtro_data_categoria = st.segmented_control(
				label="Por Data de:",
				options=["Competência", "Recebimento (Caixa)", "Vencimento"],
				selection_mode="single",
				default="Competência",
			)
		st.write("")

		# Filtros parcelas
		df_parcelas_filtradas_por_status = filtrar_por_classe_selecionada(df_parcelas, 'Status Evento', filtros_status_evento_faturamento)
		df_parcelas_filtradas_por_data = get_parcelas_por_tipo_data(df_parcelas_filtradas_por_status, df_eventos, filtro_data_categoria, ano)

		# Filtros orcamentos
		df_orcamentos = filtrar_por_classe_selecionada(df_orcamentos, 'Ano', [ano])
		if casa != "Todas as Casas":
			df_orcamentos = filtrar_por_classe_selecionada(df_orcamentos, 'ID Casa', [id_casa])
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			if filtro_data_categoria is None:
				st.warning("Por favor, selecione um filtro de data.")
			if casa == "Todas as Casas":
				montar_tabs_geral(df_parcelas_filtradas_por_data, casa, id_casa, filtro_data_categoria, df_orcamentos)
			else:
				df_parcelas_casa = df_filtrar_casa(df_parcelas_filtradas_por_data, casa)
				if casa == "Priceless":
					montar_tabs_priceless(df_parcelas_casa, id_casa, df_eventos, filtro_data_categoria, df_orcamentos)
				else:
					montar_tabs_geral(df_parcelas_casa, casa, id_casa, filtro_data_categoria, df_orcamentos)
	st.write("")

	# Faturamento por tipo de evento
	with st.container(border=True):
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown("## Faturamento Por Tipo de Evento*")
			st.write("")
			df_eventos_tipo_evento = filtrar_por_classe_selecionada(df_eventos, 'Status_Evento', filtros_status_evento_faturamento)
			df_eventos_tipo_evento = df_filtrar_ano(df_eventos_tipo_evento, 'Data_Evento', ano)
			grafico_linhas_faturamento_tipo_evento(df_eventos_tipo_evento, id_casa)
			st.markdown("*Por mês de competência do evento.")
	st.write("")

	# Faturamento por tipo de evento
	with st.container(border=True):
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown("## Faturamento Por Modelo de Evento*")
			st.write("")
			df_eventos_modelo_evento = filtrar_por_classe_selecionada(df_eventos, 'Status_Evento', filtros_status_evento_faturamento)
			df_eventos_modelo_evento = df_filtrar_ano(df_eventos_modelo_evento, 'Data_Evento', ano)
			grafico_linhas_faturamento_modelo_evento(df_eventos_modelo_evento, id_casa)
			st.markdown("*Por mês de competência do evento.")
	st.write("")

	# Recebido X Vencimento
	with st.container(border=True):
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown("## Recebido X Vencimento")
			st.write("")
			df_parcelas_recebimento = get_parcelas_por_tipo_data(df_parcelas_filtradas_por_status, df_eventos, "Recebimento (Caixa)", ano)
			df_parcelas_vencimento = get_parcelas_por_tipo_data(df_parcelas_filtradas_por_status, df_eventos, "Vencimento", ano)
			grafico_barras_vencimento_x_recebimento(df_parcelas_recebimento, df_parcelas_vencimento, id_casa)
	
	# Farol de Parcelas Atrasadas
	with st.container(border=True):
		col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
		with col2:
			st.markdown(f"## Farol de Parcelas Atrasadas")
			if not id_casa == -1:
				df_farol = df_filtrar_casa(df_parcelas_filtradas_por_status, id_casa)
				df_farol = filtra_parcelas_atrasadas(df_farol)
			else:
				df_farol = filtra_parcelas_atrasadas(df_parcelas_filtradas_por_status)
			df_farol = format_columns_brazilian(df_farol, ['Valor_Parcela'])
			df_farol = df_format_date_columns_brazilian(df_farol, ['Data_Vencimento', 'Data_Recebimento'])
			df_farol = rename_colunas_parcelas(df_farol)
			df_farol = df_farol.drop(columns=['ID Casa'], errors='ignore')
			st.dataframe(df_farol, use_container_width=True, hide_index=True)
			st.markdown("Todas as parcelas ainda sem pagamento após a Data de Vencimento.")

	
if __name__ == '__main__':
  main()