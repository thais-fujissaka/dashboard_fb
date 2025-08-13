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
from utils.user import *

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_icon="🔎",
	page_title="Informações de Eventos",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')
 
def main():
	config_sidebar()

	# Recupera dados dos eventos e parcelas
	df_eventos = GET_EVENTOS()
	df_aditivos = GET_ADITIVOS()
	df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()
	
	df_eventos_aditivos_agrupado = GET_EVENTOS_E_ADITIVOS_PRICELESS()
	
	# Formata tipos de dados do dataframe de eventos
	tipos_de_dados_eventos = {
		'Valor Locação Aroo 1': float,
		'Valor Locação Aroo 2': float,
		'Valor Locação Aroo 3': float,
		'Valor Locação Anexo': float,
		'Valor Locação Notie': float,
		'Valor Locação Mirante': float,
		'Valor Imposto': float,
		'Valor AB': float,
		'Valor Total Evento': float,
		'Valor Total Locação': float,
		'Valor Locação Gerador': float,
		'Valor Locação Mobiliário': float,
		'Valor Locação Utensílios': float,
		'Valor Mão de Obra Extra': float,
		'Valor Taxa Administrativa': float,
		'Valor Comissão BV': float,
		'Valor Extras Gerais': float,
		'Valor Taxa Serviço': float,
		'Valor Acréscimo Forma de Pagamento': float
	}
	df_eventos = df_eventos.astype(tipos_de_dados_eventos, errors='ignore')
	df_eventos['Data Contratação'] = pd.to_datetime(df_eventos['Data Contratação'], errors='coerce')
	df_eventos['Data Evento'] = pd.to_datetime(df_eventos['Data Evento'], errors='coerce')

	# Formata tipos de dados do dataframe de parcelas
	tipos_de_dados_parcelas = {
		'Valor Parcela': float,
		'Categoria Parcela': str
	}
	df_parcelas = df_parcelas.astype(tipos_de_dados_parcelas, errors='ignore')
	df_parcelas['Data Vencimento'] = pd.to_datetime(df_parcelas['Data Vencimento'], errors='coerce')
	df_parcelas['Data Recebimento'] = pd.to_datetime(df_parcelas['Data Recebimento'], errors='coerce')
 
	# Adiciona coluna de concatenação de ID e Nome Evento
	df_eventos['ID_Nome_Evento'] = df_eventos['ID Evento'].astype(str) + " - " + df_eventos['Nome Evento']

	# Calcula o valor de repasse para Gazit
	df_eventos = calcular_repasses_gazit(df_eventos)

	# Seleciona apenas colunas do tipo float
	float_cols = df_eventos.select_dtypes(include=['float'])
    # Preenche NaN com 0 nessas colunas
	df_eventos[float_cols.columns] = float_cols.fillna(0)

	# Cabeçalho
	col1, col2, col3 = st.columns([6, 1, 1])
	with col1:
		st.title("🔎 Informações de Eventos")
	with col2:
		st.button(label='Atualizar', key='atualizar_informacoes_eventos', on_click=st.cache_data.clear)
	with col3:
		if st.button('Logout', key='logout_informacoes_eventos'):
			logout()
	st.divider()

	# Seletores de eventos
	col1, col2 = st.columns([1, 3])
	with col1:
		lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim']
		id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='casas_informacoes_eventos')

	# Filtro por Casa
	if id_casa != -1:
		df_eventos = df_eventos[df_eventos['ID Casa'] == id_casa]
		df_aditivos = df_aditivos[df_aditivos['ID Casa'] == id_casa]
		df_parcelas = df_parcelas[df_parcelas['ID Casa'] == id_casa]
	
	# Lista de eventos para o filtro
	eventos_unicos = df_eventos['ID_Nome_Evento'].unique().tolist()
	eventos_id_options = ['Todos os Eventos'] + sorted(eventos_unicos)
	
	with col2:
		eventos = st.multiselect("Eventos", options=eventos_id_options, key='informacoes_eventos', placeholder='Procurar eventos')
	st.divider()	

	# Janela de visualização
	if eventos:
		if 'Todos os Eventos' not in eventos:
			# Filtra os eventos, aditivos e parcelas dos eventos selecionados
			df_eventos = df_eventos[df_eventos['ID_Nome_Evento'].isin(eventos)]
			df_aditivos = df_aditivos[df_aditivos['ID Evento do Aditivo'].isin(df_eventos['ID Evento'])]
			df_parcelas = df_parcelas[(df_parcelas['ID Evento'].isin(df_eventos['ID Evento']) | df_parcelas['ID Evento'].isin(df_aditivos['ID Evento do Aditivo']))]

		# Formata datas: datetime[ns] -> str
		df_eventos = df_formata_data_sem_horario(df_eventos, 'Data Contratação')
		df_eventos = df_formata_data_sem_horario(df_eventos, 'Data Evento')
		df_aditivos = df_formata_data_sem_horario(df_aditivos, 'Data Contratação')
		df_aditivos = df_formata_data_sem_horario(df_aditivos, 'Data Evento')
		df_parcelas = df_formata_data_sem_horario(df_parcelas, 'Data Vencimento')
		df_parcelas = df_formata_data_sem_horario(df_parcelas, 'Data Recebimento')

		# Calcula o valor de repasse para Gazit das parcelas
		df_parcelas = calcular_repasses_gazit_parcelas(df_parcelas, df_eventos)
		
		# Formata valores monetários brasileiro
		df_eventos = format_columns_brazilian(df_eventos, ['Valor Total Evento', 'Valor Total Locação', 'Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Imposto'])
		df_aditivos = format_columns_brazilian(df_aditivos, ['Valor Total Aditivo', 'Valor Total Locação', 'Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Espaço', 'Valor Locação Mirante', 'Valor Contratação Artístico', 'Valor Contratação Técnico de Som', 'Valor Contratação Bilheteria/Couvert Artístico', 'Valor Locação Gerador', 'Valor Locação Mobiliário', 'Valor Locação Utensílios', 'Valor Mão de Obra Extra', 'Valor Taxa Administrativa', 'Valor Comissão BV', 'Valor Extras Gerais', 'Valor Acréscimo Forma de Pagamento', 'Valor Imposto', 'Valor AB', 'Valor Taxa Serviço'])
		df_parcelas = format_columns_brazilian(df_parcelas, ['Valor Parcela', 'Valor Bruto Repasse Gazit', 'Valor Liquido Repasse Gazit', 'Valor Total Bruto Gazit', 'Valor Total Líquido Gazit', 'Valor Parcela AROO', 'Valor Parcela ANEXO', 'Valor Parcela Notie', 'Valor Parcela Mirante', 'AROO Valor Bruto Gazit', 'AROO Valor Líquido Gazit', 'ANEXO Valor Bruto Gazit', 'ANEXO Valor Líquido Gazit'])

		df_eventos = df_eventos.drop(columns=['ID_Nome_Evento', 'Valor Locacao Total Aroos', 'Total Gazit Aroos', 'Total Gazit Anexo', 'Total Gazit'])

		st.markdown("## Eventos")
		st.dataframe(df_eventos, 
			use_container_width=True,
			hide_index=True, 
			column_config={
				'Evento': st.column_config.Column(
					width="large"
				),
				'Total Gazit': st.column_config.Column(
					width="medium",
				)
			}
		)

		st.markdown("## Aditivos")
		if not df_aditivos.empty and df_aditivos is not None:
			st.dataframe(df_aditivos, use_container_width=True, hide_index=True)
		else:
			st.warning("Nenhum aditivo encontrado.")

		st.markdown("## Parcelas")
		if df_parcelas is not None:
			df_parcelas = df_parcelas.drop(columns=['ID Casa', 'Total Gazit Aroos', 'Total Gazit Anexo', 'Status Evento', 'Valor Total Locação', 'Total Gazit', 'Valor Locacao Total Aroos', 'Valor Locação Anexo', 'Valor Locação Notie', 'Valor Locação Mirante', 'Repasse_Gazit_Bruto', 'Repasse_Gazit_Liquido', 'Repasse Gazit Bruto Aroos', 'Repasse Gazit Liquido Aroos', 'Repasse Gazit Bruto Anexo', 'Repasse Gazit Liquido Anexo'])
			st.dataframe(df_parcelas, use_container_width=True, hide_index=True)
		else:
			st.warning("Nenhuma parcela encontrada.")
		

	else:
		st.warning("Por favor, selecione pelo menos um evento.")

	st.markdown("")

if __name__ == '__main__':
  main()