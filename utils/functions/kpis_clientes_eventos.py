import streamlit as st
from streamlit_echarts import st_echarts
from utils.functions.general_functions import *


def grafico_ranking_clientes_por_num_eventos(df, key):
    clientes_data = df['Cliente'].to_list()
    num_eventos_data = df['N° Eventos'].to_list()
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"}
        },
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {
            "type": "category",
            "data": clientes_data
        },
        "series": [{
            "name": "Nº Eventos",
            "type": "bar",
            "label": {"show": True, "position": "right"},
            "data": num_eventos_data,
            "itemStyle": {"color": "#FAC858"}
        }]
    }

    st_echarts(options=option, height="500px", key=f'{key}')

def grafico_ranking_clientes_por_valor_eventos(df, key):
    # Cria series de dados para o gráfico
    clientes = df['Cliente'].to_list()
    valores = df['Valor Total Eventos'].astype(float).to_list()

    # Labels formatados
    labels = [format_brazilian(valor) for valor in valores]

    # Dados com labels
    valores_com_labels = [{"value": v, "label": {"show": True, "position": "right", "color": "#000", "formatter": lbl}} for v, lbl in zip(valores, labels)]
    
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"}
        },
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": {"type": "value"},
        "yAxis": {
            "type": "category",
            "data": clientes
        },
        "series": [{
            "name": "Nº Eventos",
            "type": "bar",
            "label": {"show": True, "position": "right"},
            "data": valores_com_labels,
            "itemStyle": {"color": "#FAC858"}
        }]
    }

    st_echarts(options=option, height="500px", key=key)