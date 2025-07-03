import streamlit as st
import pandas as pd
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries import *
from utils.functions.parcelas import *
from streamlit_echarts import st_echarts
from utils.functions.faturamento import *

def grafico_barras_vencimento_x_recebimento(df_parcelas_recebimento, df_parcelas_vencimento, id_casa):

    if id_casa != -1:
        df_parcelas_vencimento = df_parcelas_vencimento[df_parcelas_vencimento['ID Casa'] == id_casa].copy()
        df_parcelas_recebimento = df_parcelas_recebimento[df_parcelas_recebimento['ID Casa'] == id_casa].copy()

    if df_parcelas_recebimento.empty or df_parcelas_vencimento.empty:
        st.error("Não há dados de eventos disponíveis para o gráfico.")
        return
    
    # Extrai mês e ano da coluna 'Data_Vencimento'
    df_parcelas_vencimento['Mes'] = df_parcelas_vencimento['Data_Vencimento'].dt.month
    df_parcelas_recebimento['Mes'] = df_parcelas_recebimento['Data_Recebimento'].dt.month

    # Agrupa os valores por mês
    df_vencimento_agrupado = df_parcelas_vencimento.groupby('Mes')['Valor_Parcela'].sum().reset_index()
    df_recebimento_agrupado = df_parcelas_recebimento.groupby('Mes')['Valor_Parcela'].sum().reset_index()

    # Cria lista de meses
    nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_meses = pd.DataFrame({'Mes': list(range(1, 13)), 'Nome_Mes': nomes_meses})
    
    df_vencimento_agrupado = df_meses.merge(df_vencimento_agrupado, how='left', on='Mes')
    df_recebimento_agrupado = df_meses.merge(df_recebimento_agrupado, how='left', on='Mes')
    
    df_vencimento_agrupado.fillna(0, inplace=True)
    df_recebimento_agrupado.fillna(0, inplace=True)

    # Cria lista de valores
    total_vencimento = df_vencimento_agrupado['Valor_Parcela'].round(2).tolist()
    total_recebimento = df_recebimento_agrupado['Valor_Parcela'].round(2).tolist()

    # Labels formatados
    labels_vencimento = [format_brazilian(v) for v in total_vencimento]
    labels_recebimento = [format_brazilian(v) for v in total_recebimento]

    # Dados com labels
    dados_vencimentos_com_labels = [{"value": v, "label": {"show": False, "position": "top", "color": "#000", "rotate": 70, "formatter": lbl}} for v, lbl in zip(total_vencimento, labels_vencimento)]
    dados_recebimentos_com_labels = [{"value": v, "label": {"show": False, "position": "top", "color": "#000","rotate": 70, "formatter": lbl}} for v, lbl in zip(total_recebimento, labels_recebimento)]

    # Options do grafico
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "shadow"
            }
        },
        "legend": {
            "show": True,
            "data": ["Vencimento", "Recebimento"],
            "top": "top",
            "textStyle": {"color": "#000"}
        },
        "grid": {
            "left": "3%",
            "right": "4%",
            "bottom": "0%",
            "containLabel": True
        },
        "xAxis": [
            {
                "type": "category",
                "data": nomes_meses
            }
        ],
        "yAxis": [
            {
                "type": "value"
            }
        ],
        "series": [
            {
                "name": "Vencimento",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_vencimentos_com_labels,
                "itemStyle": {
                    "color": "#5470C6"
                }
            },
            {
                "name": "Recebimento",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_recebimentos_com_labels,
                "itemStyle": {
                    "color": "#FAC858"
                }
            }
        ]
    }

    # Evento de clique
    events = {
        "click": "function(params) { return params.name; }"
    }

    # Exibir gráfico com captura de clique
    mes_selecionado = st_echarts(option, events=events, height="320px", width="100%", key="chart_vencimento_recebimento")

    # Dicionário para mapear os meses
    meses = {
        "Jan": "01",
        "Fev": "02",
        "Mar": "03",
        "Abr": "04",
        "Mai": "05",
        "Jun": "06",
        "Jul": "07",
        "Ago": "08",
        "Set": "09",
        "Out": "10",
        "Nov": "11",
        "Dez": "12"
    }
    
    # Obter o mês correspondente ao mês selecionado
    if mes_selecionado != None:
        mes_selecionado = meses[mes_selecionado]
        
        col1, col2, col3 = st.columns([1, 12, 1])
        with col2:
            df_parcelas_recebimento = df_filtrar_mes(df_parcelas_recebimento, 'Data_Recebimento', mes_selecionado)
            df_parcelas_recebimento.drop(columns=['Mes'], inplace=True)

            df_parcelas_recebimento = df_formata_datas_sem_horario(df_parcelas_recebimento, ['Data_Vencimento', 'Data_Recebimento', 'Data_Evento'])
            df_parcelas_recebimento = rename_colunas_parcelas(df_parcelas_recebimento)
            df_parcelas_recebimento = format_columns_brazilian(df_parcelas_recebimento, ['Valor Parcela'])

            df_parcelas_vencimento = df_filtrar_mes(df_parcelas_vencimento, 'Data_Vencimento', mes_selecionado)
            df_parcelas_vencimento.drop(columns=['Mes'], inplace=True)
            
            df_parcelas_vencimento = df_formata_datas_sem_horario(df_parcelas_vencimento, ['Data_Vencimento', 'Data_Recebimento', 'Data_Evento'])
            df_parcelas_vencimento = rename_colunas_parcelas(df_parcelas_vencimento)
            df_parcelas_vencimento = format_columns_brazilian(df_parcelas_vencimento, ['Valor Parcela'])

            # Inverter o dicionário
            meses_invertido = meses_invertido = {
                "01": "Janeiro",
                "02": "Fevereiro",
                "03": "Março",
                "04": "Abril",
                "05": "Maio",
                "06": "Junho",
                "07": "Julho",
                "08": "Agosto",
                "09": "Setembro",
                "10": "Outubro",
                "11": "Novembro",
                "12": "Dezembro"
            }
            nome_mes = meses_invertido[f'{mes_selecionado}'] 

        df_parcelas_recebimento['ID Evento'] = df_parcelas_recebimento['ID Evento'].astype(int)
        df_parcelas_vencimento['ID Evento'] = df_parcelas_vencimento['ID Evento'].astype(int)
        df_parcelas_recebimento['ID Casa'] = df_parcelas_recebimento['ID Casa'].astype(int)
        df_parcelas_vencimento['ID Casa'] = df_parcelas_vencimento['ID Casa'].astype(int)

        df_parcelas_recebimento = df_parcelas_recebimento.style.apply(colorir_parcelas_recebidas, axis=1)
        df_parcelas_vencimento = df_parcelas_vencimento.style.apply(colorir_parcelas_vencidas, axis=1)

        st.markdown(f"### Parcelas Recebidas em {nome_mes}")
        st.dataframe(df_parcelas_recebimento, use_container_width=True, hide_index=True)

        # Legenda de cores
        st.markdown("""
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: #fff9c4; border: 1px solid #ccc; margin-right: 10px;"></div>
                <span>Parcelas recebidas em atraso (podem ter a data de vencimento em outros meses)</span>
            </div>
        """, unsafe_allow_html=True)

        st.write("")

        st.markdown(f"### Parcelas com Vencimento em {nome_mes}")
        st.dataframe(df_parcelas_vencimento, use_container_width=True, hide_index=True)
        
        # Legenda de cores
        st.markdown("""
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: #fff9c4; border: 1px solid #ccc; margin-right: 10px;"></div>
                <span>Parcelas recebidas em atraso</span>
                </div>
                <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: #ffcccc; border: 1px solid #ccc; margin-right: 10px;"></div>
                <span>Parcelas vencidas e não recebidas</span>
            </div>
        """, unsafe_allow_html=True)
        st.write("")
    else:
        st.markdown("Selecione um mês no gráfico para visualizar as parcelas recebidas e com vencimento no mês selecionado.")