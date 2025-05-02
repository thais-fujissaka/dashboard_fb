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
		'Comercial_Responsavel',
		'Status_Evento',
		'Observacoes',
		'Motivo_Declinio',
		'ID_Evento',
		'Nome_do_Evento',
		'Valor_Total',
		'Valor_AB',
		'Num_Pessoas',
		'Tipo_Evento',
		'Modelo_Evento'
	], inplace=True, axis=1)
	return df

def rename_colunas_eventos(df):
	df.rename(columns={
		'ID_Nome_Evento': 'Evento',
		'Comercial_Responsavel': 'Comercial Responsável',
		'Data_Contratacao': 'Data Contratação',
		'Data_Evento': 'Data Evento',
		'Valor_Locacao_Aroo_1': 'Valor Locação Aroo 1',
		'Valor_Locacao_Aroo_2': 'Valor Locação Aroo 2',
		'Valor_Locacao_Aroo_3': 'Valor Locação Aroo 3',
		'Valor_Locacao_Anexo': 'Valor Locação Anexo',
		'Valor_Locacao_Notie': 'Valor Locação Notiê',
		'Valor_Imposto': 'Imposto',
		'Total_Gazit': 'Total Gazit'
	}, inplace=True)
	return df

def rename_colunas_parcelas(df):
	df.rename(columns={
		'ID_Evento': 'Evento',
		'ID_Parcela': 'ID Parcela',
		'Nome_do_Evento': 'Nome do Evento',
		'Categoria_Parcela': 'Categoria Parcela',
		'Valor_Parcela': 'Valor Parcela',
		'Data_Vencimento': 'Data Vencimento',
		'Status_Pagamento': 'Status Pagamento',
		'Data_Recebimento': 'Data Recebimento',
		'Repasse_Gazit': 'Repasse Gazit'
	}, inplace=True)
	return df


def calcular_repasses_gazit_parcelas(df):
	if not 'Repasse_Gazit' in df.columns:
		df['Repasse_Gazit'] = 0
	# Zero se a categoria for "A&B"
	df['Repasse_Gazit'] = df.apply(lambda x: 0 if x['Categoria_Parcela'] == 'A&B' else None, axis=1)

	return df
	

