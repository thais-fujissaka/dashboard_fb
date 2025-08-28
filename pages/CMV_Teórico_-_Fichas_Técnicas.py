import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.user import *
from utils.functions.cmv_teorico_fichas_tecnicas import *

st.set_page_config(
	page_icon=":material/rubric:",
	page_title="CMV Teórico - Fichas Técnicas",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
	
	# Sidebar
	config_sidebar()
	col1, col2, col3 = st.columns([6, 1, 1])
	with col1:
		st.title(":material/rubric: CMV Teórico - Fichas Técnicas")
	with col2:
		st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
	with col3:
		if st.button('Logout', key='logout'):
			logout()
	st.divider()
	
	# Seletores
	periodo = input_periodo_datas(key='data_inicio')
	data_inicio = periodo[0]
	data_fim = periodo[1]
	
	# Validação de data
	if data_inicio > data_fim:
		st.warning('📅 Data Inicio deve ser menor que Data Final')
	else:
		averageInputN5Price = average_inputN5_price(data_inicio.strftime('%Y-%m-%d'), data_fim.strftime('%Y-%m-%d'))
		averageInputN5Price_n5_not_associated = averageInputN5Price.copy()
		averageInputN5Price_itemsold = averageInputN5Price.copy()
		averageInputN5Price_itemsold['QUANTIDADE DRI'] = averageInputN5Price_itemsold['QUANTIDADE DRI'].replace(['None', None, '', 'nan', 'NaN'], '0').astype(str).str.replace(',', '.', regex=False).astype(float)
		averageInputN5Price_itemsold['PROPORÇÃO ACE'] = averageInputN5Price_itemsold['PROPORÇÃO ACE'].replace(['None', None, '', 'nan', 'NaN'], '0').astype(str).str.replace(',', '.', regex=False).astype(float)
		averageInputN5Price_itemsold['Volume Total'] = averageInputN5Price_itemsold['QUANTIDADE DRI'] * averageInputN5Price_itemsold['PROPORÇÃO ACE']
		averageInputN5Price_itemsold = averageInputN5Price_itemsold.groupby(['EMPRESA', 'Insumo de Estoque']).agg({'Volume Total': 'sum', 'VALOR DRI': 'sum'})
		averageInputN5Price_itemsold['Média Preço (Insumo Estoque)'] = averageInputN5Price_itemsold['VALOR DRI'].astype(str).str.replace(',', '.', regex=False).astype(float) / averageInputN5Price_itemsold['Volume Total'].astype(str).str.replace(',', '.', regex=False).astype(float)
		averageInputN5Price_itemsold = averageInputN5Price_itemsold.reset_index()
		averageInputN5Price_itemsold = averageInputN5Price_itemsold[['EMPRESA', 'Insumo de Estoque', 'Média Preço (Insumo Estoque)']].reindex()

		row_averageInputN5Price_filters = st.columns([1,1,1,1])
		with row_averageInputN5Price_filters[1]:
			enterprise_selected = st.multiselect('Selecione a(s) Casa(s):', options=sorted(averageInputN5Price['EMPRESA'].dropna().unique()), placeholder='Casas', key='enterprise_selected')
		
		if enterprise_selected:
			available_inputs = averageInputN5Price[averageInputN5Price['EMPRESA'].isin(enterprise_selected)]['INSUMO N5'].dropna().unique()
		else:
			available_inputs = averageInputN5Price['INSUMO N5'].dropna().unique()

		with row_averageInputN5Price_filters[2]:
			input_selected = st.multiselect('Selecione o(s) Insumo(s):', options=sorted(available_inputs), placeholder='Insumos')
		
		if enterprise_selected:
			averageInputN5Price = averageInputN5Price[averageInputN5Price['EMPRESA'].isin(enterprise_selected)]

		if input_selected:
			averageInputN5Price = averageInputN5Price[averageInputN5Price['INSUMO N5'].isin(input_selected)]

		averageInputN5Price = averageInputN5Price.drop(columns=['VALOR DRI', 'QUANTIDADE DRI', 'PROPORÇÃO ACE'])
		function_format_number_columns(averageInputN5Price, columns_money=['Média Preço (Insumo de Compra)', 'Média Preço (Insumo Estoque)'])
		dataframe_aggrid(averageInputN5Price, 'Preço Médio de Insumo N5')

		st.write('---')
		itemSold = item_sold()
		itemSold['ID Insumo de Estoque'] = itemSold['ID Insumo de Estoque'].astype(str)
		itemSold_merged = itemSold.merge(averageInputN5Price_itemsold, how='left', on=['Insumo de Estoque', 'EMPRESA'])
		itemSold_merged_debug = itemSold_merged.copy()
		itemSold_merged['Unidade de Medida na Ficha'] = itemSold_merged.apply(function_format_amount, axis=1)

		valor_do_item = itemSold_merged['VALOR DO ITEM'].copy()
		itemSold_merged = itemSold_merged.drop(columns=['VALOR DO ITEM'])
		itemSold_merged = itemSold_merged[['EMPRESA','Item Vendido', 'CATEGORIA', 'Insumo de Estoque', 'Unidade Medida', 'Média Preço (Insumo Estoque)', 'Quantidade na Ficha', 'Unidade de Medida na Ficha']]

		inputProduced = input_produced(data_inicio.strftime('%Y-%m-%d'), data_fim.strftime('%Y-%m-%d'))
		inputProduced_grouped = (inputProduced.groupby(['EMPRESA', 'ITEM PRODUZIDO', 'RENDIMENTO'])[['VALOR PRODUÇÃO']].sum().reset_index())
		inputProduced_grouped['VALOR DO KG'] = (inputProduced_grouped['VALOR PRODUÇÃO'] * 1000) / inputProduced_grouped['RENDIMENTO']
		inputProduced_grouped = inputProduced_grouped.rename(columns={'ITEM PRODUZIDO': 'INSUMO_DE_ESTOQUE', 'VALOR DO KG': 'VALOR_DO_KG'})
		
		inputProduced_merged = inputProduced.copy()

		while True:
			merge_temp = inputProduced_merged.merge(
				inputProduced_grouped[['INSUMO_DE_ESTOQUE', 'VALOR_DO_KG']],
				left_on='Insumo de Estoque',
				right_on='INSUMO_DE_ESTOQUE',
				how='left'
			)
			before_null = merge_temp['MÉDIA PREÇO NO ITEM KG'].isna().sum()
			merge_temp['MÉDIA PREÇO NO ITEM KG'] = merge_temp['MÉDIA PREÇO NO ITEM KG'].fillna(merge_temp['VALOR_DO_KG'])
			merge_temp['VALOR_PRODUÇÃO_ATUAL'] = merge_temp['VALOR PRODUÇÃO']
			mask = merge_temp['VALOR_PRODUÇÃO_ATUAL'].isna() & merge_temp['MÉDIA PREÇO NO ITEM KG'].notna()
			merge_temp.loc[mask, 'VALOR PRODUÇÃO'] = (merge_temp.loc[mask, 'QUANTIDADE INSUMO'] / 1000) * merge_temp.loc[mask, 'MÉDIA PREÇO NO ITEM KG']
			merge_temp = merge_temp.drop(columns=['INSUMO_DE_ESTOQUE', 'VALOR_DO_KG', 'VALOR_PRODUÇÃO_ATUAL'])
			after_null = merge_temp['MÉDIA PREÇO NO ITEM KG'].isna().sum()
			if after_null == before_null:
				break
			inputProduced_merged = merge_temp

		inputProduced_items = (inputProduced_merged.groupby(['EMPRESA', 'ITEM PRODUZIDO', 'RENDIMENTO'])[['VALOR PRODUÇÃO']].sum().reset_index())

		if 'VALOR DO KG' not in inputProduced_items.columns:
			inputProduced_items['VALOR DO KG'] = (inputProduced_items['VALOR PRODUÇÃO'] * 1000) / inputProduced_items['RENDIMENTO']

		itemSold_merged['Valor na Ficha'] = itemSold_merged.apply(
			lambda row: (row['Média Preço (Insumo Estoque)'] / 1000) * row['Quantidade na Ficha'] 
			if row['Unidade Medida'] in ['KG', 'LT'] 
			else row['Média Preço (Insumo Estoque)'], 
			axis=1
		)

		inputProduced_items_dict = dict(zip(inputProduced_items['ITEM PRODUZIDO'], inputProduced_items['VALOR DO KG']))
		
		itemSold_merged['Média Preço (Insumo Estoque)'] = itemSold_merged.apply(
			lambda row: inputProduced_items_dict.get(row['Insumo de Estoque'], row['Média Preço (Insumo Estoque)']), 
			axis=1
		)
		itemSold_merged['Valor na Ficha'] = itemSold_merged.apply(
			lambda row: (row['Quantidade na Ficha'] / 1000) * row['Média Preço (Insumo Estoque)']
			if row['Insumo de Estoque'] in inputProduced_items_dict
			else (row['Média Preço (Insumo Estoque)'] / 1000) * row['Quantidade na Ficha'] if row['Unidade Medida'] in ['KG', 'LT'] else row['Média Preço (Insumo Estoque)'], 
			axis=1
		)

		item_valuer = itemSold_merged.copy()
		item_valuer['Valor Vendido'] = valor_do_item
		item_valuer = item_valuer.groupby(['EMPRESA', 'Item Vendido', 'CATEGORIA', 'Valor Vendido']).agg({'Valor na Ficha': 'sum'}).reset_index()
		item_valuer['Custo do Item'] = item_valuer['Valor na Ficha']
		item_valuer = item_valuer[['EMPRESA', 'Item Vendido', 'CATEGORIA', 'Custo do Item', 'Valor Vendido']]
		item_valuer['CMV'] = (item_valuer['Custo do Item'].astype(float) / item_valuer['Valor Vendido'].astype(float)) * 100
		item_valuer['Lucro do Item'] = item_valuer['Valor Vendido'].astype(float) - item_valuer['Custo do Item'].astype(float)

		if enterprise_selected:
			item_valuer = item_valuer[item_valuer['EMPRESA'].isin(enterprise_selected)]

		function_format_number_columns(item_valuer, columns_money=['Custo do Item', 'Valor Vendido', 'Lucro do Item'], columns_percent=['CMV'])
		dataframe_aggrid(item_valuer, 'Valor dos Itens Vendidos')
		function_copy_dataframe_as_tsv(item_valuer)

		st.write('---')

		if enterprise_selected:
			itemValuer_enterprise = itemSold_merged[itemSold_merged['EMPRESA'].isin(enterprise_selected)]['Item Vendido'].dropna().unique()
			itemSold_merged = itemSold_merged[itemSold_merged['EMPRESA'].isin(enterprise_selected)]
		else:
			itemValuer_enterprise = itemSold_merged['Item Vendido'].dropna().unique()

		row_itemValuer_selected = st.columns(3)
		with row_itemValuer_selected[1]:
			itemValuer_selected = st.multiselect('Selecione o(s) Item(s) Vendido(s):', options=sorted(itemValuer_enterprise), placeholder='Itens Vendidos')                

		if itemValuer_selected:
			itemSold_merged = itemSold_merged[itemSold_merged['Item Vendido'].isin(itemValuer_selected)]
			inputProduced_merged['Insumos para Produção'] = inputProduced_merged['Insumo de Estoque']
			inputProduced_merged['Insumo de Estoque'] = inputProduced_merged['ITEM PRODUZIDO']
			inputProduced_merged = inputProduced_merged[['Insumo de Estoque', 'RENDIMENTO', 'Insumos para Produção', 'QUANTIDADE INSUMO', 'MÉDIA PREÇO NO ITEM KG', 'VALOR PRODUÇÃO']]
			function_format_number_columns(itemSold_merged, columns_money=['Média Preço (Insumo Estoque)', 'Valor na Ficha'], columns_number=['RENDIMENTO', 'QUANTIDADE INSUMO'])
			function_format_number_columns(inputProduced_merged, columns_money=['MÉDIA PREÇO NO ITEM KG', 'VALOR PRODUÇÃO'])
			dataframe_aggrid(itemSold_merged, 'Itens Vendidos Detalhado', df_details=inputProduced_merged, coluns_merge_details='Insumo de Estoque', coluns_name_details='EMPRESA')

		st.write('---')
			
		itemSold_merged_debug = itemSold_merged_debug[['EMPRESA', 'Item Vendido', 'VALOR DO ITEM', 'CATEGORIA', 'ID Insumo de Estoque','Insumo de Estoque', 'Unidade Medida', 'Média Preço (Insumo Estoque)', 'Quantidade na Ficha']]
		itemSold_merged_debug.rename(columns={'Média Preço (Insumo Estoque)': 'Media Preço do Insumo','Quantidade na Ficha': 'Quantidade para Produção', 'VALOR DO ITEM': 'Valor Vendido'}, inplace=True)
		itemSold_merged_debug['Unidade de Medida Produção'] = itemSold_merged_debug.apply(function_format_amount, axis=1)
		itemSold_merged_debug['Valor para Produção'] = itemSold_merged_debug['Media Preço do Insumo'] / itemSold_merged_debug['Quantidade para Produção']
		function_format_number_columns(itemSold_merged_debug, columns_money=['Media Preço do Insumo', 'Valor Vendido', 'Valor para Produção'], columns_number=['Quantidade para Produção'])
		itemSold_merged_full, len_df = dataframe_aggrid(itemSold_merged_debug, 'Itens Vendidos Completo')
		function_copy_dataframe_as_tsv(itemSold_merged_full)
		
		averageInputN5Price_n5_not_associated = averageInputN5Price_n5_not_associated[averageInputN5Price_n5_not_associated['Insumo de Estoque'].isna()]
		function_format_number_columns(averageInputN5Price_n5_not_associated, columns_money=['Média Preço (Insumo de Compra)', 'Média Preço (Insumo Estoque)', 'VALOR DRI'], columns_number=['QUANTIDADE DRI'])
		averageInputN5Price_null, len_df = dataframe_aggrid(averageInputN5Price_n5_not_associated, 'Insumos Sem Associação')
		row_averageInputN5Price_filters = st.columns([1.8,1,1])
		with row_averageInputN5Price_filters[0]:
			function_copy_dataframe_as_tsv(averageInputN5Price_null)
		with row_averageInputN5Price_filters[1]:
			function_box_lenDf(len_df, averageInputN5Price_n5_not_associated, item='itens')

	# Layout
	col1, col2, col3 = st.columns([1, 1, 1])

if __name__ == '__main__':
	main()
