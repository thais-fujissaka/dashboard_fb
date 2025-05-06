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
                "boundaryGap": True,
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
                "name": "Faturamento de Eventos",
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
    grafico = st_echarts(option, height=300, width="100%", key="chart_total_eventos")

def df_fracao_locacao_aroo(df_eventos):
    df_eventos['Fracao_Aroo'] = (df_eventos['Valor_Locacao_Aroo_1'] + df_eventos['Valor_Locacao_Aroo_2'] + df_eventos['Valor_Locacao_Aroo_3']) / df_eventos['Valor_Locacao_Total']
    df_eventos['Fracao_Aroo'] = df_eventos['Fracao_Aroo'].fillna(0)

    return df_eventos

def calculo_valor_aroos_parcela_locacao(df_parcelas, df_eventos):

    df_eventos = df_fracao_locacao_aroo(df_eventos)

    # Merge df_parcelas com fracoes de Aroo
    df_parcelas = df_parcelas.merge(df_eventos[['ID_Evento', 'Fracao_Aroo']], how='left', on='ID_Evento')
    
    df_parcelas['Valor_Parcela_Aroos'] = df_parcelas['Valor_Parcela'] * df_parcelas['Fracao_Aroo']

    return df_parcelas


def grafico_barras_locacao_aroo(df_parcelas, df_eventos):
    # Normaliza
    df_parcelas['Categoria_Parcela'] = df_parcelas['Categoria_Parcela'].str.replace('ç', 'c')

    # Filtra pela categoria 'Locação'
    df_parcelas = (
    df_parcelas
    .loc[df_parcelas['Categoria_Parcela'] == 'Locacão']
    .copy()
    )
    
    # Calcula coluna 'Valor_Parcela_Aroos'
    df_parcelas = calculo_valor_aroos_parcela_locacao(df_parcelas, df_eventos)

    # Extrai mês e ano da coluna 'Data_Vencimento'
    df_parcelas['Mes'] = df_parcelas['Data_Vencimento'].dt.month
    df_parcelas['Ano'] = df_parcelas['Data_Vencimento'].dt.year

    # Agrupa os valores por mês e ano
    df_parcelas_agrupado = df_parcelas.groupby(['Mes', 'Ano'])['Valor_Parcela_Aroos'].sum().reset_index()

    # Cria lista de meses
    meses = df_parcelas_agrupado['Mes'].unique().tolist()
    nomes_meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    nomes_meses = [nomes_meses_pt[mes - 1] for mes in meses]
    
    # Cria lista de valores
    total_aroos = df_parcelas_agrupado['Valor_Parcela_Aroos'].tolist()

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
                "boundaryGap": True,
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
                "data": total_aroos,
                "itemStyle": {
                    "color": "#FAC858"
                }
            }
        ]
    }

    # Cria o gráfico de barras
    grafico = st_echarts(option, height=300, width="100%", key="chart_aroos")

