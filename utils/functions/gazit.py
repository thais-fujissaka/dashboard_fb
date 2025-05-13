import streamlit as st
from streamlit_echarts import st_echarts
from utils.functions.general_functions import *

def grafico_barras_repasse_mensal(df_parcelas):
    # Extrai mês e ano da coluna 'Data_Vencimento'
    df_parcelas['Mes'] = df_parcelas['Data_Vencimento'].dt.month
    df_parcelas['Ano'] = df_parcelas['Data_Vencimento'].dt.year

    # Agrupa os valores por mês e ano
    df_parcelas_agrupado = df_parcelas.groupby(['Mes', 'Ano']).agg({
        'Repasse_Gazit_Bruto': 'sum',
        'Repasse_Gazit_Liquido': 'sum'
    }).reset_index()

    df_parcelas_agrupado['Repasse_Gazit_Bruto'] = df_parcelas_agrupado['Repasse_Gazit_Bruto'].round(2)
    df_parcelas_agrupado['Repasse_Gazit_Liquido'] = df_parcelas_agrupado['Repasse_Gazit_Liquido'].round(2)

    # Cria lista de meses
    meses = df_parcelas_agrupado['Mes'].unique().tolist()
    nomes_meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    nomes_meses = [nomes_meses_pt[mes - 1] for mes in meses]
    
    # Cria lista de valores
    total_repasse_bruto = df_parcelas_agrupado['Repasse_Gazit_Bruto'].tolist()
    total_repasse_liquido = df_parcelas_agrupado['Repasse_Gazit_Liquido'].tolist()

    # Labels formatados
    labels_brutos = [format_brazilian(v) for v in total_repasse_bruto]
    labels_liquidos = [format_brazilian(v) for v in total_repasse_liquido]

    # Dados com labels
    dados_brutos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(total_repasse_bruto, labels_brutos)]
    dados_liquidos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(total_repasse_liquido, labels_liquidos)]
    
    # Options do grafico
    # Montar gráfico
    option = {
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "legend": {
            "show": True,
            "data": ["Repasse Bruto Gazit", "Repasse Líquido Gazit"],
            "top": "top",
            "textStyle": {"color": "#000"}
        },
        "grid": {
            "left": "3%", "right": "4%", "bottom": "3%", "containLabel": True
        },
        "xAxis": [{"type": "category", "data": nomes_meses}],
        "yAxis": [{"type": "value"}],
        "series": [
            {
                "name": "Repasse Bruto Gazit",
                "type": "bar",
                "barWidth": "35%",
                "data": dados_brutos_com_labels,
                "itemStyle": {"color": "#FAC858"}
            },
            {
                "name": "Repasse Líquido Gazit",
                "type": "bar",
                "barWidth": "35%",
                "barGap": "5%",
                "data": dados_liquidos_com_labels,
                "itemStyle": {"color": "#5470C6"}
            }
        ]
    }

    # Evento de clique
    events = {
        "click": "function(params) { return params.name; }"
    }

    # Exibir gráfico com captura de clique
    mes_selecionado = st_echarts(option, events=events, height=300, width="100%", key="chart_total_repasse_mensal")
    
    # Dicionário para mapear os meses
    meses = {
        "Janeiro": "01",
        "Fevereiro": "02",
        "Março": "03",
        "Abril": "04",
        "Maio": "05",
        "Junho": "06",
        "Julho": "07",
        "Agosto": "08",
        "Setembro": "09",
        "Outubro": "10",
        "Novembro": "11",
        "Dezembro": "12"
    }
    
    # Obter o mês correspondente ao mês selecionado
    if mes_selecionado != None:
        mes_selecionado = meses[mes_selecionado]
    
    return mes_selecionado


