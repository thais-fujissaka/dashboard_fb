import streamlit as st
from streamlit_echarts import st_echarts

def grafico_valor_insumos_temporal(df, ano_filtro_grafico):
	# Cria uma coluna "Período"
	df = df.copy()
	df["Período"] = df["Mês"].astype(str).str.zfill(2) + "-" + df["Ano"].astype(str)
	# Pivota os dados: cada Nivel 2 vira uma série
	pivot = df.pivot_table(index="Período", columns="Nivel 2", values="Valor Insumo", aggfunc="sum").fillna(0)
	pivot = pivot.sort_index()

	option = {
		"title": {
			"text": f"Gastos por Categoria - {ano_filtro_grafico}",
			"left": "center"
		},
		"tooltip": {"trigger": "axis", "axisPointer": {"type": "cross"}},
		"legend": {
			"top": 50,
			"data": list(pivot.columns)
		},
		"toolbox": {"feature": {"saveAsImage": {}}},
		"xAxis": [{"type": "category", "boundaryGap": False, "data": list(pivot.index)}],
		"yAxis": [{"type": "value"}],
		"series": [
			{
				"name": col,
				"type": "line",
				"stack": "Total",
				"areaStyle": {},
				"emphasis": {"focus": "series"},
				"data": pivot[col].tolist()
			}
			for col in pivot.columns
		],
		"grid": {
			"top": 120
		}
	}
	
	st.write('')
	st_echarts(options=option, height="500px")