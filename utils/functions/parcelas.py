import streamlit as st
import pandas as pd
from utils.components import *

def calcular_repasses_gazit(df):
    # Dataframe com valores de repasse para Gazit
	df['Total_Gazit'] = df['Valor_Locacao_Aroo_1'] * 0.7 + df['Valor_Locacao_Aroo_2'] * 0.7 + df['Valor_Locacao_Aroo_3'] * 0.7 + df['Valor_Locacao_Anexo'] * 0.3
	return df


def drop_colunas_eventos(df):
	df.drop(columns=[
		'Casa',
		'ID_Evento',
		'Comercial_Responsavel',
		'Status_Evento',
		'Observacoes',
		'Motivo_Declinio',
		'ID_Evento',
		'Nome_do_Evento',
		'Valor_AB',
		'Num_Pessoas',
		'Tipo_Evento',
		'Modelo_Evento'
	], inplace=True, axis=1)
	return df

def rename_colunas_eventos(df):
	df.rename(columns={
		'ID_Evento': 'ID Evento',
		'Nome_do_Evento': 'Nome do Evento',
		'ID_Nome_Evento': 'Evento',
		'Comercial_Responsavel': 'Comercial Responsável',
		'Data_Contratacao': 'Data Contratação',
		'Data_Evento': 'Data Evento',
		'Tipo_Evento': 'Tipo Evento',
		'Modelo_Evento': 'Modelo Evento',
		'Num_Pessoas': 'Num Pessoas',
		'Valor_AB': 'Valor A&B',
		'Valor_Locacao_Aroo_1': 'Valor Locação Aroo 1',
		'Valor_Locacao_Aroo_2': 'Valor Locação Aroo 2',
		'Valor_Locacao_Aroo_3': 'Valor Locação Aroo 3',
		'Valor_Locacao_Anexo': 'Valor Locação Anexo',
		'Valor_Locacao_Notie': 'Valor Locação Notiê',
		'Valor_Imposto': 'Imposto',
		'Total_Gazit': 'Total Gazit',
		'Valor_Locacao_Total': 'Total Locação',
		'Valor_Total': 'Valor Total',
		'Status_Evento': 'Status Evento',
		'Observacoes': 'Observações',
		'Motivo_Declinio': 'Motivo Declínio'
	}, inplace=True)
	return df

def rename_colunas_parcelas(df):
	df.rename(columns={
		'ID_Parcela': 'ID Parcela',
		'ID_Evento': 'ID Evento',
		'Nome_do_Evento': 'Nome do Evento',
		'Categoria_Parcela': 'Categoria Parcela',
		'Valor_Parcela': 'Valor Parcela',
		'Data_Vencimento': 'Data Vencimento',
		'Status_Pagamento': 'Status Pagamento',
		'Data_Recebimento': 'Data Recebimento',
		'Repasse_Gazit_Bruto': 'Valor Bruto Repasse Gazit',
		'Repasse_Gazit_Liquido': 'Valor Liquido Repasse Gazit',
		'Valor_Locacao_Total': 'Total Locação',
		'Valor_Parcela_Aroos': 'Valor Parcela Aroos',
		'Valor_Parcela_Anexo': 'Valor Parcela Anexo',
		'Valor_Parcela_Notie': 'Valor Parcela Notiê'
	}, inplace=True)
	return df


def calcular_repasses_gazit_parcelas(df_parcelas, df_eventos):

	df_parcelas = df_parcelas.merge(df_eventos[['ID_Evento', 'Total_Gazit', 'Valor_Locacao_Total']], how='left', on='ID_Evento')

	if not 'Repasse_Gazit_Bruto' in df_parcelas.columns:
		df_parcelas['Repasse_Gazit_Bruto'] = 0
	# Zero se a categoria for "A&B"
	#df_parcelas['Repasse_Gazit_Bruto'] = df_parcelas.apply(lambda x: 0 if x['Categoria_Parcela'] == 'A&B' else None, axis=1)

	if not 'Repasse_Gazit_Liquido' in df_parcelas.columns:
		df_parcelas['Repasse_Gazit_Liquido'] = 0
	# df_parcelas['Repasse_Gazit_Liquido'] = df_parcelas.apply(lambda x: 0 if x['Categoria_Parcela'] == 'A&B' else None, axis=1)

	# Calcula Valor Bruto de Repasse para categoria "Locação"
	for idx, row in df_parcelas.iterrows():
		if row['Categoria_Parcela'] == 'Locação':
			porcentagem = df_parcelas.loc[idx, 'Valor_Parcela'] / df_parcelas.loc[idx, 'Valor_Locacao_Total']
			df_parcelas.at[idx, 'Repasse_Gazit_Bruto'] = round(row['Total_Gazit'] * porcentagem, 2)

	# Calcula Valor Liquido de Repasse para categoria "Locação"
	for idx, row in df_parcelas.iterrows():
		if row['Categoria_Parcela'] == 'Locação':
			df_parcelas.at[idx, 'Repasse_Gazit_Liquido'] = round(row['Repasse_Gazit_Bruto'] * 0.8547, 2)

	return df_parcelas
   

