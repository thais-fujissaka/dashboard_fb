import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.user import *
from utils.functions.cmv_teorico_fichas_tecnicas import *
from utils.queries_compras import *
from datetime import date, datetime, timedelta

st.set_page_config(
	page_icon="📦",
	page_title="Relatório de Insumos - Suprimentos",
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
		st.title("📦 Relatório de Insumos - Suprimentos")
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
		inputsExpenses = inputs_expenses(data_inicio, data_fim)
		
		# Filtro de Casas
		row_companies = st.columns([1, 1, 1])
		with row_companies[1]:
			companies_filtered = st.multiselect(
				'Selecione a(s) Casa(s):',
				options=sorted(inputsExpenses['Casa'].dropna().unique()),
				placeholder='Casas'
			)
		# Caso nenhum esteja selecionado mostra todos
		if not companies_filtered:
			companies_filtered = inputsExpenses['Casa'].dropna().unique()

		inputsExpenses_filtered = inputsExpenses[inputsExpenses['Casa'].isin(companies_filtered)]

		# Agrupa por Casa e Categoria
		inputsExpenses_n2 = (
			inputsExpenses_filtered.groupby(['Casa', 'Nivel 2'])[['Valor Insumo']]
			.sum().reset_index().sort_values(by=['Casa', 'Valor Insumo'], ascending=[True, False])
		)
		
		input_total_value = function_format_number_columns(valor=inputsExpenses_n2['Valor Insumo'].sum())  # valor total antes de formatar
		inputsExpenses_n2 = function_format_number_columns(inputsExpenses_n2, columns_money=['Valor Insumo'])

		# Agrupa por Categoria
		categoryN2_grafic = (
			inputsExpenses_filtered.groupby('Nivel 2')[['Valor Insumo']]
			.sum().reset_index().sort_values(by='Valor Insumo', ascending=False)
		)
		categoryN2_grafic['Percentual'] = (categoryN2_grafic['Valor Insumo'] / categoryN2_grafic['Valor Insumo'].sum() * 100).round(1)
		categoryN2_grafic['Label'] = categoryN2_grafic.apply(lambda x: f"{x['Nivel 2']} ({x['Percentual']}%)", axis=1)

		row = st.columns([2, 1, 2])
		with row[1]:
			if st.session_state.get("base_theme") == "dark":
				color_back = "#222"
				color_font = "#ffffff"
			else:
				color_back = "#ffffff"
				color_font = "#000000"
			st.write(f"""
				<div style='background: {color_back};border-radius: 20px;border: 1px solid #8B0000;
				padding: 15px 0;margin: 8px 0;text-align: center;font-family: "Segoe UI", "Arial", sans-serif;'>
				<div style='font-size: 13px; color: #D14D4D; font-weight: 500;'>💰 Valor Total dos Insumos</div>
				<div style='font-size: 18px; color: {color_font}; font-weight: bold; margin-top: 2px;'>{input_total_value}</div>
				</div>
			""", unsafe_allow_html=True)

		col1, col2 = st.columns([1, 0.8])
		with col1:
			st.markdown('### Insumos por Casa e Categoria')
			dataframe_aggrid(inputsExpenses_n2, 'Insumos por Casa e Categoria')
		with col2:
			st.markdown('### Gastos por Categoria')
			component_plotPizzaChart(categoryN2_grafic['Label'], categoryN2_grafic['Valor Insumo'], 'Gastos por Categoria', 19)

		st.markdown('---')

		# Filtro por categoria N2
		row_categoryN2 = st.columns([1, 1, 1])
		with row_categoryN2[1]:
			categorias_disponiveis = sorted(inputsExpenses_filtered['Nivel 2'].dropna().unique())
			categoryN2_selected = st.multiselect(
				'Selecione a(s) Categoria(s) (Nivel 2):',
				options=categorias_disponiveis,
				placeholder='Categorias'
			)
		if not categoryN2_selected:
			categoryN2_selected = categorias_disponiveis

		inputs_expenses_filtered_by_cat = inputsExpenses_filtered[inputsExpenses_filtered['Nivel 2'].isin(categoryN2_selected)]

		# Gastos por fornecedor insumo N5
		with st.expander('Gastos por Fornecedor insumo N5', expanded=False):
			supplierExpenseN5 = supplier_expense_n5(data_inicio, data_fim)
			supplierExpenseN5 = supplierExpenseN5[supplierExpenseN5['Casa'].isin(companies_filtered)]

			row_expenses = st.columns([1, 1, 1])
			with row_expenses[1]:
				supplierExpenseN5_selected = st.multiselect(
					'Selecione o(s) Fornecedor(es):',
					options=sorted(supplierExpenseN5['Fornecedor'].dropna().unique()),
					placeholder='Fornecedores'
				)
			
			if not supplierExpenseN5_selected:
				supplierExpenseN5_selected = supplierExpenseN5['Fornecedor'].dropna().unique()

			supplierExpenseN5_filtered = supplierExpenseN5[supplierExpenseN5['Fornecedor'].isin(supplierExpenseN5_selected)]
			supplierExpenseN5_filtered = function_format_number_columns(supplierExpenseN5_filtered, columns_money=['Valor Insumo', 'Valor Med Por Insumo'])

			st.markdown('### Despesas por Fornecedor')
			dataframe_aggrid(supplierExpenseN5_filtered, 'Despesas por Fornecedor')
			function_copy_dataframe_as_tsv(supplierExpenseN5_filtered)

		# Insumos por Casa e Fornecedor
		col3, col4 = st.columns([1, 1])
		with col3:
			categoryN2_supplier_companies = (
				inputs_expenses_filtered_by_cat.groupby(['Casa', 'Fornecedor'])[['Valor Insumo']]
				.sum().reset_index().sort_values(by=['Casa', 'Valor Insumo'], ascending=[True, False])
			)
			categoryN2_supplier_companies = function_format_number_columns(categoryN2_supplier_companies, columns_money=['Valor Insumo'])

			st.markdown('### Insumos por Casa e Fornecedor')
			dataframe_aggrid(categoryN2_supplier_companies, 'Insumos por Casa e Fornecedor')
			function_copy_dataframe_as_tsv(categoryN2_supplier_companies)

		with col4:
			categoryN2_supplier = (
				inputs_expenses_filtered_by_cat.groupby('Fornecedor')[['Valor Insumo']]
				.sum().reset_index().sort_values(by='Valor Insumo', ascending=False)
			)
			categoryN2_supplier['Percentual'] = (categoryN2_supplier['Valor Insumo'] / categoryN2_supplier['Valor Insumo'].sum() * 100).round(1)
			categoryN2_supplier = function_format_number_columns(categoryN2_supplier, columns_money=['Valor Insumo'])
			categoryN2_supplier['Valor Gasto (R$)'] = categoryN2_supplier['Valor Insumo']
			st.markdown('### Compras Sem Pedido')
			st.dataframe(
				categoryN2_supplier[['Fornecedor', 'Valor Gasto (R$)', 'Percentual']],
				column_config={
					"Percentual": st.column_config.ProgressColumn("Percentual", format="%.1f%%", min_value=0, max_value=100)
				},
				hide_index=True
			)

		st.markdown('---')

		# Detalhamento por insumo
		categoryN2_inputs = (
			inputs_expenses_filtered_by_cat.groupby('Insumo')[['Valor Insumo', 'Quantidade Insumo']]
			.sum().reset_index()
		)
		categoryN2_inputs['Preco Medio'] = categoryN2_inputs['Valor Insumo'] / categoryN2_inputs['Quantidade Insumo']
		categoryN2_inputs['Percentual Repres'] = (categoryN2_inputs['Valor Insumo'] / categoryN2_inputs['Valor Insumo'].sum() * 100).round(1)
		categoryN2_inputs = categoryN2_inputs.sort_values(by='Valor Insumo', ascending=False)

		# Calcula preço médio mês anterior
		last_day_last_month = datetime.today().replace(day=1) - pd.Timedelta(days=1)
		first_day_last_month = last_day_last_month.replace(day=1)

		categoryN2_inputs_last_month = inputs_expenses(first_day_last_month.strftime('%Y-%m-%d'), last_day_last_month.strftime('%Y-%m-%d'))
		categoryN2_inputs_last_month = (
			categoryN2_inputs_last_month.groupby('Insumo')[['Valor Insumo', 'Quantidade Insumo']]
			.sum().reset_index()
		)
		categoryN2_inputs_last_month['Preco Medio Anterior'] = categoryN2_inputs_last_month['Valor Insumo'] / categoryN2_inputs_last_month['Quantidade Insumo']
		categoryN2_inputs_last_month = categoryN2_inputs_last_month[['Insumo', 'Preco Medio Anterior']]

		# Merge e variação percentual
		categoryN2_inputs_merged = categoryN2_inputs.merge(categoryN2_inputs_last_month, on='Insumo', how='left')
		categoryN2_inputs_merged['Variação Percentual'] = (
			(categoryN2_inputs_merged['Preco Medio'] - categoryN2_inputs_merged['Preco Medio Anterior'])
			/ categoryN2_inputs_merged['Preco Medio Anterior'] * 100
		)

		# Formatação
		categoryN2_inputs_merged = function_format_number_columns(
			categoryN2_inputs_merged,
			columns_money=['Valor Insumo', 'Preco Medio', 'Preco Medio Anterior'],
			columns_number=['Quantidade Insumo']
		)
		categoryN2_inputs_merged['Percentual Repres'] = categoryN2_inputs_merged['Percentual Repres'].map(lambda x: f"{x:.1f}%")
		categoryN2_inputs_merged['Variação Percentual'] = categoryN2_inputs_merged['Variação Percentual'].map(lambda x: f"{x:+.1f}%" if pd.notnull(x) else '-')
		categoryN2_inputs_merged_style = categoryN2_inputs_merged.style.map(function_highlight_percentage, subset=['Variação Percentual'], invert_color=True)
		
		st.markdown('### Detalhamento por Insumo')
		st.dataframe(categoryN2_inputs_merged_style, hide_index=True, use_container_width=True)
		function_copy_dataframe_as_tsv(categoryN2_inputs_merged)

if __name__ == '__main__':
	main()
