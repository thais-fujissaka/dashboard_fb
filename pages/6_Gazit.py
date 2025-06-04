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
from utils.functions.gazit import *
from utils.user import *

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_title="Gazit",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
	st.markdown(" <style>iframe{ height: 300px !important } ", unsafe_allow_html=True)

	config_sidebar()

	# Recupera dados dos eventos e parcelas
	df_eventos = GET_EVENTOS_PRICELESS()
	df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()

	df_eventos = df_eventos[(df_eventos['Valor_Locacao_Aroo_1'] > 0) | (df_eventos['Valor_Locacao_Aroo_2'] > 0) | (df_eventos['Valor_Locacao_Aroo_3'] > 0) | (df_eventos['Valor_Locacao_Anexo'] > 0)]
	
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

	# Fillna em colunas de valores monetários
	df_eventos.fillna({
		'Valor_Locacao_Aroo_1': 0,
		'Valor_Locacao_Aroo_2': 0,
		'Valor_Locacao_Aroo_3': 0,
		'Valor_Locacao_Anexo': 0,
		'Valor_Locacao_Notie': 0,
		'Valor_Locacao_Mirante': 0,
		'Valor_Imposto': 0,
		'Valor_AB': 0,
		'Valor_Total': 0,
		'Valor_Locacao_Total': 0
	}, inplace=True)

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

	col1, col2, col3 = st.columns([6, 1, 1])
	with col1:
		st.title(":shopping_bags: Gazit")
	with col2:
		st.button(label='Atualizar', key='atualizar_gazit', on_click=st.cache_data.clear)
	with col3:
		if st.button('Logout', key='logout_gazit'):
			logout()
	st.divider()

	# Seletor de ano
	col1, col2 = st.columns([1, 3])
	with col1:
		ano = seletor_ano(2024, 2025, key='ano_faturamento')
	st.divider()

	df_parcelas = calcular_repasses_gazit_parcelas(df_parcelas, df_eventos)
	
	df_parcelas_vencimento = df_filtrar_ano(df_parcelas, 'Data_Vencimento', ano)
	df_parcelas_recebimento = df_filtrar_ano(df_parcelas, 'Data_Recebimento', ano)

	# Formata colunas de eventos
	df_eventos = rename_colunas_eventos(df_eventos)
	df_eventos = df_format_date_columns_brazilian(df_eventos, ['Data Contratação', 'Data Evento'])
	df_eventos = format_columns_brazilian(df_eventos, ['Valor Total', 'Valor A&B', 'Total Locação', 'Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Notiê', 'Valor Locação Mirante', 'Imposto', 'Total Gazit'])

	# Repasses Gazit #
 
	tab1, tab2 = st.tabs(["Projeção por Vencimento", "Valor Realizado (R$)"])
	with tab1:
		# Gráfico de barras de Faturamento Bruto por mês, ver exemplo do faturamento por dia do dash da Luana
		st.markdown("### Projeção por Vencimento")

		mes_vencimento = grafico_barras_repasse_mensal_vencimento(df_parcelas_vencimento)

		if mes_vencimento != None:
			st.markdown("#### Parcelas")
				
			# Filtra parcelas pelo mês da Data_Vencimento
			df_parcelas_vencimento = df_filtrar_mes(df_parcelas_vencimento, 'Data_Vencimento', mes_vencimento)

			# Drop colunas desnecessárias
			df_parcelas_vencimento.drop(columns=['Mes', 'Ano', 'Total_Gazit', 'Valor_Locacao_Total'], inplace=True)

			# Formata datas: datetime[ns] -> str
			df_parcelas_vencimento = df_formata_datas_sem_horario(df_parcelas_vencimento, ['Data_Vencimento', 'Data_Recebimento'])

			# Formatacao de colunas
			df_parcelas_vencimento = rename_colunas_parcelas(df_parcelas_vencimento)
			df_parcelas_vencimento = format_columns_brazilian(df_parcelas_vencimento, ['Valor Parcela', 'Valor Bruto Repasse Gazit', 'Total Locação', 'Valor Liquido Repasse Gazit'])

			st.dataframe(df_parcelas_vencimento, use_container_width=True, hide_index=True)

			st.markdown("#### Eventos")
			df_eventos_vencimento = df_eventos[df_eventos['ID Evento'].isin(df_parcelas_vencimento['ID Evento'])]
			st.dataframe(df_eventos_vencimento, use_container_width=True, hide_index=True)
		
		else:
			st.markdown("#### Parcelas")
			st.markdown("Clique em um mês no gráfico para visualizar parcelas.")

	with tab2:
		st.markdown("### Valor Realizado (R$)")

		mes_recebimento = grafico_barras_repasse_mensal_recebimento(df_parcelas_recebimento)

		if mes_recebimento != None:
			st.markdown("#### Parcelas")

			# Filtra parcelas pelo mês da Data_Recebimento
			df_parcelas_recebimento = df_filtrar_mes(df_parcelas_recebimento, 'Data_Recebimento', mes_recebimento)

			# Drop colunas desnecessárias
			df_parcelas_recebimento.drop(columns=['Mes', 'Ano', 'Total_Gazit', 'Valor_Locacao_Total'], inplace=True)

			# Formata datas: datetime[ns] -> str
			df_parcelas_recebimento = df_formata_datas_sem_horario(df_parcelas_recebimento, ['Data_Vencimento', 'Data_Recebimento'])

			# Formatacao de colunas
			df_parcelas_recebimento = rename_colunas_parcelas(df_parcelas_recebimento)
			df_parcelas_recebimento = format_columns_brazilian(df_parcelas_recebimento, ['Valor Parcela', 'Valor Bruto Repasse Gazit', 'Total Locação', 'Valor Liquido Repasse Gazit'])

			st.dataframe(df_parcelas_recebimento, use_container_width=True, hide_index=True)

			st.markdown("#### Eventos")
			df_eventos_recebimento = df_eventos[df_eventos['ID Evento'].isin(df_parcelas_vencimento['ID Evento'])]
			st.dataframe(df_eventos_recebimento, use_container_width=True, hide_index=True)
		
		else:
			st.markdown("#### Parcelas")
			st.markdown("Clique em um mês no gráfico para visualizar parcelas.")

if __name__ == '__main__':
    main()