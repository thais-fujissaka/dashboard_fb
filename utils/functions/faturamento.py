import streamlit as st
import pandas as pd
from utils.components import *
from streamlit_echarts import st_echarts


def grafico_barras_total_eventos(df_parcelas):
    # Extrai mês e ano da coluna 'Data_Vencimento'
    df_parcelas['Mes'] = df_parcelas['Data_Vencimento'].dt.month
    df_parcelas['Ano'] = df_parcelas['Data_Vencimento'].dt.year

    # Agrupa os valores por mês e ano
    df_parcelas_agrupado = df_parcelas.groupby(['Mes', 'Ano'])['Valor_Parcela'].sum().reset_index()

    # Cria lista de meses
    meses = df_parcelas_agrupado['Mes'].unique().tolist()
    nomes_meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    nomes_meses = [nomes_meses_pt[mes - 1] for mes in meses]
    
    # Cria lista de valores
    total_eventos = df_parcelas_agrupado['Valor_Parcela'].tolist()

    # Options do grafico
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "3%",
            "containLabel": True
        },
        "xAxis": [
            {
                "type": "category",
                "data": nomes_meses,
                "axisTick": {
                    "alignWithLabel": True
                }
            }
        ],
        "yAxis": [
            {
                "type": "value"
            }
        ],
        "series": [
            {
                "name": "Direct",
                "type": "bar",
                "barWidth": "60%",
                "data": total_eventos,
                "itemStyle": {
                    "color": "#FAC858"
                }
            }
        ]
    }

    # Cria o gráfico de barras
    grafico = st_echarts(options=option)