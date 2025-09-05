import streamlit as st
import pandas as pd
import datetime
from workalendar.america import Brazil
import warnings
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.functions.eventos_auditoria_alteracao_confirmados import *
from utils.queries import *
from utils.functions.parcelas import *
from utils.user import *

warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_icon=":no_entry_sign:",
	page_title="Auditoria de Eventos - Preenchimento dos Lançamentos",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')


# Remove logs de eventos com apenas o primeiro log (de confirmação)
def remove_logs_eventos_sem_alteração(df):
	df = df.copy()
	df_contador = df[['ID Evento', 'Data/Hora Log']].groupby('ID Evento').count()
	df_contador.rename(columns={'Data/Hora Log': 'Quantidade de Logs'}, inplace=True)

	df = df.merge(df_contador, how='left', on='ID Evento')
	df = df[df['Quantidade de Logs'] > 1]

	return df

 
def main():
	config_sidebar()

	col1, col2, col3 = st.columns([6, 1, 1])
	with col1:
		st.header(":no_entry_sign: Auditoria de Eventos - Alteração de Confirmados")
	with col2:
		st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
	with col3:
		if st.button('Logout', key='logout'):
			logout()
	st.divider()

	st.warning(':warning: Eventos e parcelas de eventos não devem ser alterados após a confirmação do evento.')

	# Recupera logs de eventos, logs de parcelas e eventos confirmados
	df_logs_eventos = GET_LOGS_EVENTOS()
	df_logs_parcelas = GET_LOGS_PARCELAS_EVENTOS()
	df_eventos_confirmados = GET_EVENTOS_CONFIRMADOS()

	df_datetime_confirmacao_eventos = GET_DATETIME_CONFIRMACAO_EVENTOS()

	# Seletores
	col1, col2 = st.columns(2)
	with col1:
		# Filtro de casa:
		lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim']
		id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='seletor_casas_eventos_confirmados')
		if id_casa != -1:
			df_logs_eventos = df_logs_eventos[df_logs_eventos['ID Casa'] == id_casa]
			df_eventos_confirmados = df_eventos_confirmados[df_eventos_confirmados['ID Casa'] == id_casa]
	with col2:
		# Filtro Eventos
		lista_eventos_confirmados = df_eventos_confirmados['ID Evento'].tolist()
		id_evento_selecionado = st.multiselect('ID do Evento', lista_eventos_confirmados, key='seletor_id_eventos_confirmados')
		df_logs_eventos_selecionados = df_logs_eventos[df_logs_eventos['ID Evento'].isin(id_evento_selecionado)]	
	
	# Adiciona coluna bit de confirmação
	df_logs_eventos_confirmados = df_logs_eventos_selecionados.copy()
	df_logs_eventos_confirmados.loc[:, "Confirmação"] = 0
	if df_logs_eventos_confirmados is not None:
		# Cria set de confirmações
		confirmacoes = set(
			zip(df_datetime_confirmacao_eventos['ID Evento'], df_datetime_confirmacao_eventos['Data Confirmação'])
		)
		df_logs_eventos_confirmados['Confirmação'] = df_logs_eventos_confirmados.apply(lambda x: 1 if (x['ID Evento'], x['Data/Hora Log']) in confirmacoes else 0, axis=1)

	# Mantém apenas Data/Hora maiores que o a do log de confirmação
	df_logs_eventos_confirmados = df_logs_eventos_confirmados.merge(df_datetime_confirmacao_eventos, how='left', on='ID Evento')

	# Ordena pela Data/Hora Log
	df_logs_eventos_confirmados.sort_values(by=['ID Evento','Data/Hora Log'], inplace=True)

	# Colunas que queremos monitorar alterações
	colunas_verificar_eventos = [
		'ID Casa', 'Casa', 'Nome Usuário', 'Email Usuário', 'Comercial Responsável',
		'Nome Evento', 'Cliente', 'Data Contratação', 'Data Evento', 'Modelo Evento',
		'Segmento Evento', 'Valor Total Evento', 'Num Pessoas', 'Valor AB',
		'Valor Taxa Serviço', 'Valor Locação Aroo 1', 'Valor Locação Aroo 2',
		'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Bar',
		'Valor Locação Notie', 'Valor Locação Espaço', 'Valor Locação Mirante',
		'Valor Locação Gerador', 'Valor Locação Mobiliário', 'Valor Locação Utensílios',
		'Valor Mão de Obra Extra', 'Valor Taxa Administrativa', 'Valor Comissão BV',
		'Valor Extras Gerais', 'Valor Contratação Artístico',
		'Valor Contratação Técnico de Som',
		'Valor Contratação Bilheteria/Couvert Artístico',
		'Valor Acréscimo Forma de Pagamento', 'Valor Imposto', 'Status Evento',
		'Observações', 'Motivo Declínio', 'Observações Motivo Declínio'
	]
	# Remove logs em que não houve alteração (saves sem alterações)
	df_logs_eventos_confirmados = df_logs_eventos_confirmados.drop_duplicates(subset=colunas_verificar_eventos, keep='first')
	df_logs_eventos_confirmados = remove_logs_eventos_sem_alteração(df_logs_eventos_confirmados)

	# Formatação das colunas
	df_logs_eventos_confirmados = format_columns_brazilian(df_logs_eventos_confirmados, ['Valor Total Evento', 'Valor AB', 'Valor Taxa Serviço', 'Valor Locação Aroo 1', 'Valor Locação Aroo 2', 'Valor Locação Aroo 3', 'Valor Locação Anexo', 'Valor Locação Bar', 'Valor Locação Notie', 'Valor Locação Espaço', 'Valor Locação Mirante', 'Valor Locação Gerador', 'Valor Locação Mobiliário', 'Valor Locação Utensílios', 'Valor Mão de Obra Extra', 'Valor Taxa Administrativa', 'Valor Comissão BV', 'Valor Extras Gerais', 'Valor Contratação Artístico', 'Valor Contratação Técnico de Som', 'Valor Contratação Bilheteria/Couvert Artístico', 'Valor Acréscimo Forma de Pagamento', 'Valor Imposto'])
	df_logs_eventos_confirmados = df_format_date_columns_brazilian(df_logs_eventos_confirmados, ['Data Evento', 'Data Contratação'])

	df_logs_eventos_confirmados_styled = highlight_event_log_changes(df_logs_eventos_confirmados)

	st.markdown('### Alterações de Eventos Confirmados')
	st.dataframe(df_logs_eventos_confirmados_styled, use_container_width=True, hide_index=True)


	# Filtra parcelas de eventos confirmados
	df_logs_parcelas_confirmados = df_logs_parcelas[df_logs_parcelas['ID Evento'].isin(id_evento_selecionado)].copy()

	# Associa com o momento de confirmação do evento
	df_logs_parcelas_confirmados = df_logs_parcelas_confirmados.merge(df_datetime_confirmacao_eventos, how='left', on='ID Evento')

	
	df_logs_parcelas_confirmados = df_logs_parcelas_confirmados[(df_logs_parcelas_confirmados['Data Log'] >= df_logs_parcelas_confirmados['Data Confirmação'])]
	
	df_logs_parcelas_confirmados.sort_values(by=['ID Evento', 'ID Parcela', 'Data/Hora Log'], inplace=True)

	colunas_verificar_parcelas = [
				'ID Evento', 'Nome Usuário', 'Email Usuário', 'Nome do Evento', 'Categoria Parcela', 'Valor Parcela', 'Data Vencimento', 'Conta Bancária', 'Forma de Pagamento'
			]
	df_logs_parcelas_confirmados = df_logs_parcelas_confirmados.drop_duplicates(subset=colunas_verificar_parcelas, keep='first')
	df_logs_parcelas_confirmados = remove_logs_parcelas_sem_alteração(df_logs_parcelas_confirmados)

	df_logs_parcelas_confirmados_styled = highlight_parcelas_log_changes(df_logs_parcelas_confirmados)

	st.markdown('### Alterações de Parcelas de Eventos Confirmados')
	st.dataframe(df_logs_parcelas_confirmados_styled, use_container_width=True, hide_index=True)


if __name__ == '__main__':
  main()