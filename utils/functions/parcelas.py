import streamlit as st
import pandas as pd
from utils.components import *

def calcular_repasses_gazit(df):
    # Dataframe com valores de repasse para Gazit
	df['Total Gazit Aroos'] = df['Valor_Locacao_Aroo_1'] * 0.7 + df['Valor_Locacao_Aroo_2'] * 0.7 + df['Valor_Locacao_Aroo_3'] * 0.7
	df['Total Gazit Anexo'] = df['Valor_Locacao_Anexo'] * 0.3
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
		'Modelo_Evento': 'Modelo Evento',
		'Num_Pessoas': 'Num Pessoas',
		'Valor_AB': 'Valor A&B',
		'Valor_Locacao_Aroo_1': 'Valor Locação Aroo 1',
		'Valor_Locacao_Aroo_2': 'Valor Locação Aroo 2',
		'Valor_Locacao_Aroo_3': 'Valor Locação Aroo 3',
		'Valor_Locacao_Anexo': 'Valor Locação Anexo',
		'Valor_Locacao_Notie': 'Valor Locação Notiê',
		'Valor_Locacao_Mirante': 'Valor Locação Mirante',
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
    df = df.copy()
    df.rename(columns={
		'ID_Parcela': 'ID Parcela',
		'ID_Evento': 'ID Evento',
		'Nome_do_Evento': 'Nome do Evento',
		'Categoria_Parcela': 'Categoria Parcela',
		'Valor_Parcela': 'Valor Parcela',
		'Data_Vencimento': 'Data Vencimento',
		'Status_Pagamento': 'Status Pagamento',
		'Data_Recebimento': 'Data Recebimento',
		'Repasse_Gazit_Bruto': 'Valor Total Bruto Gazit',
		'Repasse_Gazit_Liquido': 'Valor Total Líquido Gazit',
		'Valor_Locacao_Total': 'Total Locação',
		'Valor_Parcela_Aroos': 'Valor Parcela Aroos',
		'Valor_Parcela_Anexo': 'Valor Parcela Anexo',
		'Valor_Parcela_Notie': 'Valor Parcela Notiê',
		'Valor_Parcela_Mirante': 'Valor Parcela Mirante',
		'Repasse Gazit Bruto Aroos': 'AROO Valor Bruto Gazit',
		'Repasse Gazit Liquido Aroos': 'AROO Valor Líquido Gazit',
		'Repasse Gazit Bruto Anexo': 'ANEXO Valor Bruto Gazit',
		'Repasse Gazit Liquido Anexo': 'ANEXO Valor Líquido Gazit'
	}, inplace=True)
    return df


def calcular_repasses_gazit_parcelas(df_parcelas, df_eventos):
	df_eventos['Valor Locacao Total Aroos'] = df_eventos['Valor_Locacao_Aroo_1'] + df_eventos['Valor_Locacao_Aroo_2'] + df_eventos['Valor_Locacao_Aroo_3']
	df_parcelas = df_parcelas.merge(df_eventos[['ID_Evento', 'Total_Gazit', 'Total Gazit Aroos', 'Total Gazit Anexo', 'Valor_Locacao_Total', 'Valor Locacao Total Aroos', 'Valor_Locacao_Anexo', 'Valor_Locacao_Notie', 'Valor_Locacao_Mirante']], how='inner', on='ID_Evento')

	# Cria colunas de repasse totais 
	if not 'Repasse_Gazit_Bruto' in df_parcelas.columns:
		df_parcelas['Repasse_Gazit_Bruto'] = 0
	if not 'Repasse_Gazit_Liquido' in df_parcelas.columns:
		df_parcelas['Repasse_Gazit_Liquido'] = 0

	# Cria colunas de repasse Gazit para Aroos
	if not 'Repasse Gazit Bruto Aroos' in df_parcelas.columns:
		df_parcelas['Repasse Gazit Bruto Aroos'] = 0
	if not 'Repasse Gazit Liquido Aroos' in df_parcelas.columns:
		df_parcelas['Repasse Gazit Liquido Aroos'] = 0
	
	# Cria colunas de repasse Gazit para Anexo
	if not 'Repasse Gazit Bruto Anexo' in df_parcelas.columns:
		df_parcelas['Repasse Gazit Bruto Anexo'] = 0
	if not 'Repasse Gazit Liquido Anexo' in df_parcelas.columns:
		df_parcelas['Repasse Gazit Liquido Anexo'] = 0

	# Cria colunas dos valores da parcela para cada tipo de locação
	if not 'Valor Parcela AROO' in df_parcelas.columns:
		df_parcelas['Valor Parcela AROO'] = 0
	if not 'Valor Parcela ANEXO' in df_parcelas.columns:
		df_parcelas['Valor Parcela ANEXO'] = 0
	if not 'Valor Parcela Notie' in df_parcelas.columns:
		df_parcelas['Valor Parcela Notie'] = 0
	if not 'Valor Parcela Mirante' in df_parcelas.columns:
		df_parcelas['Valor Parcela Mirante'] = 0

	# Calcula Valor Bruto de Repasse para categoria "Locação"
	for idx, row in df_parcelas.iterrows():
		if row['Categoria_Parcela'] == 'Locação':
			# Se o valor da locação é zero, repasse é igual a zero
			if row['Valor_Locacao_Total'] != 0:
				# Porcentagem do valor da parcela em relação ao valor total de locação
				porcentagem = df_parcelas.loc[idx, 'Valor_Parcela'] / df_parcelas.loc[idx, 'Valor_Locacao_Total']
				# Porcentagem do espaço de locação espaco em relação ao total de locação da parcela
				porcentagem_aroo = df_parcelas.loc[idx, 'Valor Locacao Total Aroos'] / df_parcelas.loc[idx, 'Valor_Locacao_Total']
				porcentagem_anexo = df_parcelas.loc[idx, 'Valor_Locacao_Anexo'] / df_parcelas.loc[idx, 'Valor_Locacao_Total']
				porcentagem_notie = df_parcelas.loc[idx, 'Valor_Locacao_Notie'] / df_parcelas.loc[idx, 'Valor_Locacao_Total']
				porcentagem_mirante = df_parcelas.loc[idx, 'Valor_Locacao_Mirante'] / df_parcelas.loc[idx, 'Valor_Locacao_Total']
				df_parcelas.at[idx, 'Valor Parcela AROO'] = round(row['Valor_Parcela'] * porcentagem_aroo, 2)
				df_parcelas.at[idx, 'Valor Parcela ANEXO'] = round(row['Valor_Parcela'] * porcentagem_anexo, 2)
				df_parcelas.at[idx, 'Valor Parcela Notie'] = round(row['Valor_Parcela'] * porcentagem_notie, 2)
				df_parcelas.at[idx, 'Valor Parcela Mirante'] = round(row['Valor_Parcela'] * porcentagem_mirante, 2)

				# Calcula o valor de repasse bruto total
				df_parcelas.at[idx, 'Repasse_Gazit_Bruto'] = round(row['Total_Gazit'] * porcentagem, 2)
				# Calcula os valores de repasse para cada tipo de locação
				df_parcelas.at[idx, 'Repasse Gazit Bruto Aroos'] = round(row['Total Gazit Aroos'] * porcentagem, 2)
				df_parcelas.at[idx, 'Repasse Gazit Bruto Anexo'] = round(row['Total Gazit Anexo'] * porcentagem, 2)
		else:
			df_parcelas.at[idx, 'Repasse_Gazit_Bruto'] = 0.00
			df_parcelas.at[idx, 'Repasse Gazit Bruto Aroos'] = 0.00
			df_parcelas.at[idx, 'Repasse Gazit Bruto Anexo'] = 0.00
			df_parcelas.at[idx, 'Valor Parcela AROO'] = 0.00
			df_parcelas.at[idx, 'Valor Parcela ANEXO'] = 0.00
			df_parcelas.at[idx, 'Valor Parcela Notie'] = 0.00
			df_parcelas.at[idx, 'Valor Parcela Mirante'] = 0.00
			

	# Calcula Valor Liquido de Repasse para categoria "Locação"
	for idx, row in df_parcelas.iterrows():
		if row['Categoria_Parcela'] == 'Locação':
			df_parcelas.at[idx, 'Repasse_Gazit_Liquido'] = round(row['Repasse_Gazit_Bruto'] * 0.8547, 2)
			df_parcelas.at[idx, 'Repasse Gazit Liquido Aroos'] = round(row['Repasse Gazit Bruto Aroos'] * 0.8547, 2)
			df_parcelas.at[idx, 'Repasse Gazit Liquido Anexo'] = round(row['Repasse Gazit Bruto Anexo'] * 0.8547, 2)
	
	return df_parcelas
   

