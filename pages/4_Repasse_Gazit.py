import streamlit as st
import pandas as pd
import datetime
from workalendar.america import Brazil
import warnings
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries import *
from utils.functions.repasses_gazit import *

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_title="Repasses - Gazit",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

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

# Lista de eventos para o filtro
eventos_id_options = df_eventos['ID_Nome_Evento'].unique().tolist()

st.title("Repasses - Gazit")

# Seletores de eventos
eventos = st.multiselect("Eventos", options=eventos_id_options, key='eventos_repasses_gazit', placeholder='Procurar eventos')

# Janela de visualização
if eventos:
	# Filtra os eventos e parcelas dos eventos selecionados
	df_eventos = df_eventos[df_eventos['ID_Nome_Evento'].isin(eventos)]
	df_parcelas = df_parcelas[df_parcelas['ID_Evento'].isin(df_eventos['ID_Evento'])]

	# Formata datas: datetime[ns] -> str
	df_eventos = df_formata_data_sem_horario(df_eventos, 'Data_Contratacao')
	df_eventos = df_formata_data_sem_horario(df_eventos, 'Data_Evento')
	df_parcelas = df_formata_data_sem_horario(df_parcelas, 'Data_Vencimento')

	# Calcula o valor de repasse para Gazit das parcelas
	df_parcelas = calcular_repasses_gazit_parcelas(df_parcelas, df_eventos)

	# Renomeia colunas
	df_eventos = rename_colunas_eventos(df_eventos)
	df_parcelas = rename_colunas_parcelas(df_parcelas)
	
	# Formata valores monetários brasileiro
	df_eventos = format_columns_brazilian(df_eventos, ['Valor Total', 'Total Gazit', 'Total Locação', 'Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Notiê', 'Imposto'])
	df_parcelas = format_columns_brazilian(df_parcelas, ['Valor Parcela', 'Repasse Gazit'])

	# Eventos
	st.markdown("## Eventos")
	st.dataframe(df_eventos, 
		use_container_width=True,
		hide_index=True, 
		# column_order=('Evento', 'Comercial Responsável', 'Data Contratação', 'Data Evento', 'Valor Total', 'Total Gazit', 'Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Notiê', 'Imposto'),
		column_config={
			'Evento': st.column_config.Column(
				width="large"
			),
			'Total Gazit': st.column_config.Column(
				width="medium",
			)
		}
	)
	# Parcelas
	st.markdown("## Parcelas")
	st.dataframe(df_parcelas[['ID Parcela', 'ID Evento', 'Nome do Evento', 'Categoria Parcela', 'Data Vencimento', 'Valor Parcela', 'Repasse Gazit']], 
		use_container_width=True, 
		hide_index=True,
		column_config={
			'Nome do Evento': st.column_config.Column(
				width="large"
			)
		}
	)
	

else:
	st.warning("Por favor, selecione pelo menos um evento.")

st.markdown("")
