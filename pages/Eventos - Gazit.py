import streamlit as st
import pandas as pd
import datetime
from workalendar.america import Brazil
import warnings
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries_eventos import *
from utils.functions.parcelas import *
from utils.functions.faturamento import *
from utils.functions.gazit import *
from utils.user import *
import math

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
	df_eventos = GET_EVENTOS_E_ADITIVOS_PRICELESS()
	df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()

	df_eventos = df_eventos[
		(df_eventos['Valor Locação Aroo 1'] > 0) |
		(df_eventos['Valor Locação Aroo 2'] > 0) |
		(df_eventos['Valor Locação Aroo 3'] > 0) |
		(df_eventos['Valor Locação Anexo'] > 0)
	]
	# Formata tipos de dados do dataframe de eventos
	tipos_de_dados_eventos = {
		'Valor Locação Aroo 1': float,
		'Valor Locação Aroo 2': float,
		'Valor Locação Aroo 3': float,
		'Valor Locação Anexo': float,
		'Valor Locação Notie': float,
		'Valor Locação Bar': float,
		'Valor Locação Mirante': float,
		'Valor Imposto': float,
		'Valor AB': float,
		'Valor Total Evento': float,
		'Valor Total Locação': float
	}
	df_eventos = df_eventos.astype(tipos_de_dados_eventos, errors='ignore')

	# Fillna em colunas de valores monetários
	df_eventos.fillna({
    'Valor Locação Aroo 1': 0,
    'Valor Locação Aroo 2': 0,
    'Valor Locação Aroo 3': 0,
    'Valor Locação Anexo': 0,
    'Valor Locação Notie': 0,
	'Valor Locação Bar': 0,
    'Valor Locação Mirante': 0,
    'Valor Imposto': 0,
    'Valor AB': 0,
    'Valor Total Evento': 0,
    'Valor Total Locação': 0
	}, inplace=True)

	# Formata tipos de dados do dataframe de parcelas
	tipos_de_dados_parcelas = {
		'Valor Parcela': float,
		'Categoria Parcela': str
	}
	df_parcelas = df_parcelas.astype(tipos_de_dados_parcelas, errors='ignore')

	# Adiciona coluna de concatenação de ID e Nome Evento
	df_eventos['ID_Nome_Evento'] = df_eventos['ID Evento'].astype(str) + " - " + df_eventos['Nome Evento']

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

	df_parcelas_vencimento = df_filtrar_ano(df_parcelas, 'Data Vencimento', ano)
	df_parcelas_recebimento = df_filtrar_ano(df_parcelas, 'Data Recebimento', ano)

	# Formata colunas de eventos
	df_eventos = df_format_date_columns_brazilian(df_eventos, ['Data Contratação', 'Data Evento'])

	# Repasses Gazit #
 
	tab1, tab2 = st.tabs(["Projeção por Vencimento", "Valor Realizado (R$)"])
	with tab1:
		# Gráfico de barras de Faturamento Bruto por mês, ver exemplo do faturamento por dia do dash da Luana
		st.markdown("### Projeção por Vencimento")

		mes_vencimento = grafico_barras_repasse_mensal_vencimento(df_parcelas_vencimento)

		if mes_vencimento != None:
			st.markdown("#### Parcelas")
				
			# Filtra parcelas pelo mês da Data Vencimento
			df_parcelas_vencimento = df_filtrar_mes(df_parcelas_vencimento, 'Data Vencimento', mes_vencimento)

			# Drop colunas desnecessárias
			df_parcelas_vencimento.drop(columns=['Mes', 'Ano', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo', 'Valor Total Locação', 'ID Casa', 'Casa'], inplace=True)

			# Formata datas: datetime[ns] -> str
			df_parcelas_vencimento = df_formata_datas_sem_horario(df_parcelas_vencimento, ['Data Vencimento', 'Data Recebimento'])

			# Formatacao de colunas
			df_parcelas_vencimento = rename_colunas_parcelas(df_parcelas_vencimento)
			df_parcelas_vencimento = format_columns_brazilian(df_parcelas_vencimento, ['Valor Parcela', 'Valor Parcela AROO', 'Valor Parcela ANEXO', 'Valor Parcela Notie', 'Valor Parcela Mirante', 'Valor Total Bruto Gazit', 'Valor Total Líquido Gazit', 'AROO Valor Bruto Gazit', 'AROO Valor Líquido Gazit', 'ANEXO Valor Bruto Gazit', 'ANEXO Valor Líquido Gazit'])
			df_eventos_vencimento = format_columns_brazilian(df_eventos, ['Total Gazit Aroos', 'Total Gazit Anexo', 'Valor Locacao Total Aroos'])

			df_eventos_vencimento = df_eventos[df_eventos['ID Evento'].isin(df_parcelas_vencimento['ID Evento'])]
			df_eventos_vencimento = df_eventos_vencimento[df_eventos_vencimento['Status Evento'] != 'Declinado']

			df_parcelas_vencimento = df_parcelas_vencimento[df_parcelas_vencimento['ID Evento'].isin(df_eventos_vencimento['ID Evento'])]

			# Ordem das colunas
			df_parcelas_vencimento = df_parcelas_vencimento[['ID Evento', 'Nome Evento', 'ID Parcela', 'Categoria Parcela', 'Valor Parcela', 'Valor Parcela AROO', 'Valor Parcela ANEXO', 'Valor Parcela Notie', 'Valor Parcela Mirante', 'Data Vencimento', 'Data Recebimento', 'Status Pagamento', 'AROO Valor Bruto Gazit', 'AROO Valor Líquido Gazit', 'ANEXO Valor Bruto Gazit', 'ANEXO Valor Líquido Gazit', 'Valor Total Bruto Gazit', 'Valor Total Líquido Gazit']]  # nova ordem
			st.dataframe(df_parcelas_vencimento, use_container_width=True, hide_index=True)

			st.markdown("#### Eventos")
			df_eventos_vencimento = df_eventos_vencimento.drop(columns=['ID_Nome_Evento', 'Motivo Declínio', 'Observações', 'Status Evento'])
			df_eventos_vencimento = df_eventos_vencimento[['ID Evento', 'Nome Evento', 'Cliente', 'Data Contratação', 'Data Evento', 'Tipo Evento', 'Valor Total Evento', 'Valor AB', 'Valor Total Locação', 'Valor Locacao Total Aroos', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Bar', 'Valor Locação Mirante', 'Valor Imposto', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo']]
			df_eventos_vencimento = format_columns_brazilian(df_eventos_vencimento, ['Valor Total Evento', 'Valor AB', 'Valor Total Locação', 'Valor Locacao Total Aroos', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Bar', 'Valor Locação Mirante', 'Valor Imposto', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo'])
			st.dataframe(df_eventos_vencimento, use_container_width=True, hide_index=True)
		
		else:
			st.markdown("#### Parcelas")
			st.markdown("Clique em um mês no gráfico para visualizar parcelas.")

	with tab2:
		st.markdown("### Valor Realizado (R$)")

		mes_recebimento = grafico_barras_repasse_mensal_recebimento(df_parcelas_recebimento)

		if mes_recebimento != None:
			st.markdown("#### Parcelas")

			# Filtra parcelas pelo mês da Data Recebimento
			df_parcelas_recebimento = df_filtrar_mes(df_parcelas_recebimento, 'Data Recebimento', mes_recebimento)
			# Drop colunas desnecessárias
			df_parcelas_recebimento.drop(columns=['Mes', 'Ano', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo', 'Valor Total Locação', 'ID Casa'], inplace=True)

			# Formata datas: datetime[ns] -> str
			df_parcelas_recebimento = df_formata_datas_sem_horario(df_parcelas_recebimento, ['Data Vencimento', 'Data Recebimento'])

			# Formatacao de colunas
			df_parcelas_recebimento = rename_colunas_parcelas(df_parcelas_recebimento)

			total_recebimento_aroo = df_parcelas_recebimento['Valor Parcela AROO'].sum()
			total_recebimento_anexo = df_parcelas_recebimento['Valor Parcela ANEXO'].sum()

			df_parcelas_recebimento = format_columns_brazilian(df_parcelas_recebimento, ['Valor Parcela', 'Valor Parcela AROO', 'Valor Parcela ANEXO', 'Valor Parcela Notie', 'Valor Parcela Mirante', 'Valor Total Bruto Gazit', 'Valor Total Líquido Gazit', 'AROO Valor Bruto Gazit', 'AROO Valor Líquido Gazit', 'ANEXO Valor Bruto Gazit', 'ANEXO Valor Líquido Gazit'])

			df_parcelas_recebimento = df_parcelas_recebimento[['ID Evento', 'Nome Evento', 'ID Parcela', 'Categoria Parcela', 'Valor Parcela', 'Valor Parcela AROO', 'Valor Parcela ANEXO', 'Valor Parcela Notie', 'Valor Parcela Mirante', 'Data Vencimento', 'Data Recebimento', 'Status Pagamento', 'AROO Valor Bruto Gazit', 'AROO Valor Líquido Gazit', 'ANEXO Valor Bruto Gazit', 'ANEXO Valor Líquido Gazit', 'Valor Total Bruto Gazit', 'Valor Total Líquido Gazit']]  # nova ordem
			st.dataframe(df_parcelas_recebimento, use_container_width=True, hide_index=True)

			st.markdown("#### Eventos")
			df_eventos_recebimento = df_eventos[df_eventos['ID Evento'].isin(df_parcelas_recebimento['ID Evento'])]
			df_eventos_recebimento = df_eventos_recebimento.drop(columns=['ID_Nome_Evento', 'Motivo Declínio', 'Observações', 'Status Evento'])
			df_eventos_recebimento = df_eventos_recebimento[['ID Evento', 'Nome Evento', 'Cliente', 'Data Contratação', 'Data Evento', 'Tipo Evento', 'Valor Total Evento', 'Valor AB', 'Valor Total Locação', 'Valor Locacao Total Aroos', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Bar', 'Valor Locação Mirante', 'Valor Imposto', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo']]
			df_eventos_recebimento = format_columns_brazilian(df_eventos_recebimento, ['ID Evento', 'Nome Evento', 'Cliente', 'Data Contratação', 'Data Evento', 'Tipo Evento', 'Valor Total Evento', 'Valor AB', 'Valor Total Locação', 'Valor Locacao Total Aroos', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Bar', 'Valor Locação Mirante', 'Valor Imposto', 'Total Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo'])
			st.dataframe(df_eventos_recebimento, use_container_width=True, hide_index=True)

			# Tabela Gazit
			st.markdown("#### Resumo de Vendas - Gazit")

			total_de_vendas = total_recebimento_anexo * 0.3 + total_recebimento_aroo * 0.7
			retencao_impostos = math.floor(total_de_vendas * 0.1453 * 100) / 100
			# retencao_impostos = total_de_vendas * 0.1453
			valor_liquido_a_pagar = total_de_vendas - retencao_impostos

			resumo_vendas_gazit(total_de_vendas, retencao_impostos, valor_liquido_a_pagar, total_recebimento_anexo, total_recebimento_aroo)
		
		else:
			st.markdown("#### Parcelas")
			st.markdown("Clique em um mês no gráfico para visualizar parcelas.")

if __name__ == '__main__':
    main()