import streamlit as st
import pandas as pd
from utils.components import *
from streamlit_echarts import st_echarts
from utils.functions.general_functions import *
from utils.functions.parcelas import *

def get_parcelas_por_tipo_data(df_parcelas, df_eventos, filtro_data, ano):
    if filtro_data == 'Competência':

        df = df_parcelas.merge(
            df_eventos[['Data_Evento', 'ID_Evento']],
            how='left',
            on='ID_Evento'
        )
        df = df_filtrar_ano(df, 'Data_Evento', ano)
        return df
    elif filtro_data == 'Recebimento (Caixa)':
        df = df_filtrar_ano(df_parcelas, 'Data_Recebimento', ano)
        return df
    elif filtro_data == 'Vencimento':
        df = df_filtrar_ano(df_parcelas, 'Data_Vencimento', ano)
        return df


def montar_tabs_geral(df_parcelas, casa, id_casa, tipo_data, df_orcamentos):

    if tipo_data == 'Competência':
        tipo_data = 'Data_Evento'
    elif tipo_data == 'Recebimento (Caixa)':
        tipo_data = 'Data_Recebimento'
    elif tipo_data == 'Vencimento':
        tipo_data = 'Data_Vencimento'

    tab_names = ['**Total de Eventos**', '**Alimentos e Bebidas**', '**Couvert**', '**Locação**', '**Serviço**']
    tabs = st.tabs(tab_names)
    with tabs[0]:
        st.markdown(f"#### Faturamento Total de Eventos - {casa}")
        grafico_barras_total_eventos(df_parcelas, tipo_data, df_orcamentos, id_casa)
    with tabs[1]:
        st.markdown("#### Alimentos e Bebidas")
        grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'A&B', df_orcamentos, id_casa)
    with tabs[2]:
        st.markdown("#### Couvert")
        grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'Couvert', df_orcamentos, id_casa)
    with tabs[3]:
        st.markdown("#### Locação")
        grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'Locação', df_orcamentos, id_casa)
    with tabs[4]:
        st.markdown("#### Serviço")
        grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'Serviço', df_orcamentos, id_casa)


def montar_tabs_priceless(df_parcelas_casa, id_casa, df_eventos, tipo_data, df_orcamentos):

    if tipo_data == 'Competência':
        tipo_data = 'Data_Evento'
    elif tipo_data == 'Recebimento (Caixa)':
        tipo_data = 'Data_Recebimento'
    elif tipo_data == 'Vencimento':
        tipo_data = 'Data_Vencimento'
    
    df_parcelas = calcular_repasses_gazit_parcelas(df_parcelas_casa, df_eventos)
    tab_names = ['**Total de Eventos - Priceless**', '**Locação Aroo**', '**Locação Anexo**', '**Locação Notiê**', '**Locação Mirante**', '**Alimentos e Bebidas**', '**Couvert**', '**Serviço**']
    tabs = st.tabs(tab_names)

    with tabs[0]:
        st.markdown("### Total de Eventos - Priceless")
        grafico_barras_total_eventos(df_parcelas, tipo_data, df_orcamentos, 149)
    with tabs[1]:
        st.markdown("### Locação Aroo")
        grafico_barras_locacao_priceless(df_parcelas, df_eventos, tipo_data, "Aroo", f"Aroo-{tipo_data}")
    with tabs[2]:
        st.markdown("### Locação Anexo")
        grafico_barras_locacao_priceless(df_parcelas, df_eventos, tipo_data, "Anexo", f"Anexo-{tipo_data}")
    with tabs[3]:
        st.markdown("### Locação Notiê")
        grafico_barras_locacao_priceless(df_parcelas, df_eventos, tipo_data, "Notiê", f"Notie-{tipo_data}")
    with tabs[4]:
        st.markdown("### Locação Mirante")
        grafico_barras_locacao_priceless(df_parcelas, df_eventos, tipo_data, "Mirante", f"Mirante-{tipo_data}")
    with tabs[5]:
        st.markdown("### Alimentos e Bebidas")
        grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'A&B', df_orcamentos, id_casa)
    with tabs[6]:
        st.markdown("### Couvert")
        grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'Couvert', df_orcamentos, id_casa)
    with tabs[7]:
        st.markdown("### Serviço")
        grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, 'Serviço', df_orcamentos, id_casa)


def valores_labels_formatados(lista_valores):
    # Labels formatados
    labels = [format_brazilian(v) for v in lista_valores]

    # Dados com labels
    lista_valores_formatados = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(lista_valores, labels)]

    return lista_valores_formatados


# Total de Eventos
def grafico_barras_total_eventos(df_parcelas, tipo_data, df_orcamentos, id_casa):
    # Extrai mês e ano da coluna 'Data_Vencimento'
    df_parcelas['Mes'] = df_parcelas[tipo_data].dt.month

    # Agrupa os valores por mês
    df_parcelas_agrupado = df_parcelas.groupby('Mes')['Valor_Parcela'].sum().reset_index()
    
    # Cria lista de meses
    nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_meses = pd.DataFrame({'Mes': list(range(1, 13)), 'Nome_Mes': nomes_meses})
    df_parcelas_agrupado = df_meses.merge(df_parcelas_agrupado, how='left', on='Mes')
    df_parcelas_agrupado.fillna(0, inplace=True)

    # Cria lista de valores
    total_eventos = df_parcelas_agrupado['Valor_Parcela'].tolist()
    if id_casa == -1:
        valores_orcamentos = df_orcamentos.copy().groupby(['Mês'])['Valor'].sum().reset_index()
    else:
        valores_orcamentos = df_orcamentos[df_orcamentos['ID Casa'] == id_casa].copy().groupby(['Mês'])['Valor'].sum().reset_index()

    # Labels formatados
    labels = [format_brazilian(v) for v in total_eventos]

    # Dados com labels
    dados_eventos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(total_eventos, labels)]
    dados_orcamentos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(valores_orcamentos['Valor'], valores_orcamentos['Valor'].apply(format_brazilian))]
    
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
            "data": ["Orçamento de Eventos", "Faturamento de Eventos"],
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
                "name": "Orçamento de Eventos",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_orcamentos_com_labels,
                "itemStyle": {
                    "color": "#5470C6"
                }
            },
            {
                "name": "Faturamento de Eventos",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_eventos_com_labels,
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

    mes_selecionado = st_echarts(option, events=events, height="300px", width="100%", key=f"chart_total_eventos_{tipo_data}")
    
    
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
            df_parcelas = df_filtrar_mes(df_parcelas, tipo_data, mes_selecionado)
            if 'Total_Gazit' in df_parcelas.columns:
                df_parcelas.drop(columns=['Total_Gazit'], inplace=True)
            if 'Repasse_Gazit_Bruto' in df_parcelas.columns:
                df_parcelas.drop(columns=['Repasse_Gazit_Bruto'], inplace=True)
            if 'Repasse_Gazit_Liquido' in df_parcelas.columns:
                df_parcelas.drop(columns=['Repasse_Gazit_Liquido'], inplace=True)
            if 'Valor_Locacao_Total' in df_parcelas.columns:
                df_parcelas.drop(columns=['Valor_Locacao_Total'], inplace=True)
            df_parcelas.drop(columns=['Mes'], inplace=True)
            df_parcelas = df_formata_datas_sem_horario(df_parcelas, ['Data_Vencimento', 'Data_Recebimento', 'Data_Evento'])
            df_parcelas = rename_colunas_parcelas(df_parcelas)
            df_parcelas = format_columns_brazilian(df_parcelas, ['Valor Parcela', 'Valor Bruto Repasse Gazit', 'Total Locação'])
        st.markdown("#### Parcelas")
        st.dataframe(df_parcelas, use_container_width=True, hide_index=True)
    else:
        st.markdown("### Parcelas")
        st.markdown("Selecione um mês para visualizar as parcelas correspondentes ao faturamento do mês.")


# Locação

def df_fracao_locacao_espacos(df_eventos):
    # Adiciona coluna de cálculo de fração de cada espaço em relação ao valor total de locação
    # Aroo
    df_eventos['Fracao_Aroo'] = (df_eventos['Valor_Locacao_Aroo_1'] + df_eventos['Valor_Locacao_Aroo_2'] + df_eventos['Valor_Locacao_Aroo_3']) / df_eventos['Valor_Locacao_Total']
    df_eventos['Fracao_Aroo'] = df_eventos['Fracao_Aroo'].fillna(0)

    # Anexo
    df_eventos['Fracao_Anexo'] = df_eventos['Valor_Locacao_Anexo'] / df_eventos['Valor_Locacao_Total']
    df_eventos['Fracao_Anexo'] = df_eventos['Fracao_Anexo'].fillna(0)

    # Notie
    df_eventos['Fracao_Notie'] = df_eventos['Valor_Locacao_Notie'] / df_eventos['Valor_Locacao_Total']
    df_eventos['Fracao_Notie'] = df_eventos['Fracao_Notie'].fillna(0)

    # Mirante
    df_eventos['Fracao_Mirante'] = df_eventos['Valor_Locacao_Mirante'] / df_eventos['Valor_Locacao_Total']
    df_eventos['Fracao_Mirante'] = df_eventos['Fracao_Mirante'].fillna(0)

    return df_eventos


def calcula_valor_parcela_locacao_espaco(df_parcelas, df_eventos):

    df_eventos = df_fracao_locacao_espacos(df_eventos)

    # Merge df_parcelas com fracoes de cada espaço
    df_parcelas = df_parcelas.merge(df_eventos[['ID_Evento', 'Fracao_Aroo', 'Fracao_Anexo', 'Fracao_Notie', 'Fracao_Mirante']], how='left', on='ID_Evento')
    
    df_parcelas['Valor_Parcela_Aroos'] = df_parcelas['Valor_Parcela'] * df_parcelas['Fracao_Aroo']
    df_parcelas['Valor_Parcela_Anexo'] = df_parcelas['Valor_Parcela'] * df_parcelas['Fracao_Anexo']
    df_parcelas['Valor_Parcela_Notie'] = df_parcelas['Valor_Parcela'] * df_parcelas['Fracao_Notie']
    df_parcelas['Valor_Parcela_Mirante'] = df_parcelas['Valor_Parcela'] * df_parcelas['Fracao_Mirante']

    return df_parcelas


# Gráficos de Locação dos espaços Priceless (Aroo, Anexo, Notiê e Mirante)
def grafico_barras_locacao_priceless(df_parcelas, df_eventos, tipo_data, espaco, key):
    df_parcelas = df_parcelas.copy()

    # Normaliza
    df_parcelas['Categoria_Parcela'] = df_parcelas['Categoria_Parcela'].str.replace('ç', 'c')

    # Filtra pela categoria 'Locação'
    df_parcelas = (
    df_parcelas
    .loc[df_parcelas['Categoria_Parcela'] == 'Locacão']
    .copy()
    )

    df_parcelas = calcula_valor_parcela_locacao_espaco(df_parcelas, df_eventos)

    # Define o nome da coluna de valor da parcela de acordo com o espaço
    dict_espacos = {
        'Aroo': 'Valor_Parcela_Aroos',
        'Anexo': 'Valor_Parcela_Anexo',
        'Notiê': 'Valor_Parcela_Notie',
        'Mirante': 'Valor_Parcela_Mirante'
    }


    # Extrai mês e ano da coluna 'Data_Vencimento'
    df_parcelas['Mes'] = df_parcelas[tipo_data].dt.month
    df_parcelas['Ano'] = df_parcelas[tipo_data].dt.year

    # Agrupa os valores por mês e ano
    df_parcelas_agrupado = df_parcelas.groupby(['Mes', 'Ano'])[dict_espacos[espaco]].sum().reset_index()

    # Cria lista de meses
    meses = df_parcelas_agrupado['Mes'].unique().tolist()
    nomes_meses_pt = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
    nomes_meses = [nomes_meses_pt[mes - 1] for mes in meses]
    
    # Cria lista de valores
    total_espaco = df_parcelas_agrupado[dict_espacos[espaco]].tolist()

    # Valores e labels formatados
    total_espaco_formatados = valores_labels_formatados(total_espaco)

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
                "name": f"Faturamento de Locação {espaco}",
                "type": "bar",
                "barWidth": "60%",
                "data": total_espaco_formatados,
                "itemStyle": {
                    "color": "#FAC858"
                },
                "label": {
                "show": True,
                "position": "top",
                "color": "#000"  # cor do texto
                }
            }
        ]
    }

    # Evento de clique
    events = {
        "click": "function(params) { return params.name; }"
    }

    # Exibir gráfico com captura de clique
    mes_selecionado = st_echarts(option, events=events, height=300, width="100%", key=key)
    
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
        
        col1, col2, col3 = st.columns([1, 12, 1])
        with col2:
            df_parcelas = df_filtrar_mes(df_parcelas, tipo_data, mes_selecionado)
            df_parcelas.drop(columns=['Mes', 'Ano', 'Valor_Locacao_Total', 'Total_Gazit', 'Repasse_Gazit_Bruto', 'Fracao_Aroo', 'Fracao_Anexo', 'Fracao_Notie', 'Fracao_Mirante', 'Repasse_Gazit_Liquido'], inplace=True)
            df_parcelas = df_formata_datas_sem_horario(df_parcelas, ['Data_Vencimento', 'Data_Recebimento', 'Data_Evento'])
            df_parcelas = rename_colunas_parcelas(df_parcelas)
            df_parcelas = format_columns_brazilian(df_parcelas, ['Valor Parcela', 'Valor Bruto Repasse Gazit', 'Total Locação', 'Valor Parcela Aroos', 'Valor Parcela Anexo', 'Valor Parcela Notiê', 'Valor Parcela Mirante'])
        st.markdown("#### Parcelas")
        st.dataframe(df_parcelas, use_container_width=True, hide_index=True)
    else:
        st.markdown("### Parcelas")
        st.markdown("Selecione um mês para visualizar as parcelas correspondentes ao faturamento do mês.")

# Gráfico de Faturamento por Categoria de Evento
def grafico_barras_faturamento_categoria_evento(df_parcelas, tipo_data, categoria_evento, df_orcamentos, id_casa):
    
    df_parcelas = df_parcelas.copy()
    # Extrai mês e ano da coluna 'Data_Vencimento'
    df_parcelas['Mes'] = df_parcelas[tipo_data].dt.month

    # Filtra pela categoria
    df_parcelas = (
    df_parcelas
    .loc[df_parcelas['Categoria_Parcela'] == categoria_evento]
    .copy()
    )

    # Agrupa os valores por mês e ano
    df_parcelas_agrupado = df_parcelas.groupby(['Mes'])['Valor_Parcela'].sum().reset_index()

    # Cria lista de meses
    nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
    df_meses = pd.DataFrame({'Mes': list(range(1, 13)), 'Nome_Mes': nomes_meses})
    df_parcelas_agrupado = df_meses.merge(df_parcelas_agrupado, how='left', on='Mes')
    df_parcelas_agrupado.fillna(0, inplace=True)
    
    # Cria lista de valores
    total_categoria = df_parcelas_agrupado['Valor_Parcela'].tolist()
    if id_casa == -1:
        df_valores_orcamentos = df_orcamentos[df_orcamentos['Categoria Orcamento'] == categoria_evento].copy().groupby(['Mês', 'Categoria Orcamento'])['Valor'].sum().reset_index()
    else:
        df_valores_orcamentos = df_orcamentos[(df_orcamentos['ID Casa'] == id_casa) & (df_orcamentos['Categoria Orcamento'] == categoria_evento)].copy().groupby(['Mês', 'Categoria Orcamento'])['Valor'].sum().reset_index()

    # Valores e labels formatados
    labels = [format_brazilian(v) for v in total_categoria]
    df_valores_orcamentos['Valor'] = df_valores_orcamentos['Valor'].round(2)

    # Dados com labels
    dados_categoria_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(total_categoria, labels)]
    dados_orcamentos_com_labels = [{"value": v, "label": {"show": True, "position": "top", "color": "#000", "formatter": lbl}} for v, lbl in zip(df_valores_orcamentos['Valor'], df_valores_orcamentos['Valor'].apply(format_brazilian))]

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
            "data": ["Orçamento de Eventos", "Faturamento de Eventos"],
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
                "type": "value",
                "max": "dataMax"
            }
        ],
        "series": [
            {
                "name": "Orçamento de Eventos",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_orcamentos_com_labels,
                "itemStyle": {
                    "color": "#5470C6"
                }
            },
            {
                "name": "Faturamento de Eventos",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_categoria_com_labels,
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
    mes_selecionado = st_echarts(option, events=events, height="300px", width="100%", key=f"chart_faturamento_{categoria_evento}")
    
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
            df_parcelas = df_filtrar_mes(df_parcelas, tipo_data, mes_selecionado)
            df_parcelas.drop(columns=['Mes'], inplace=True)
            if 'Total_Gazit' in df_parcelas.columns:
                df_parcelas.drop(columns=['Total_Gazit'], inplace=True)
            if 'Repasse_Gazit_Bruto' in df_parcelas.columns:
                df_parcelas.drop(columns=['Repasse_Gazit_Bruto'], inplace=True)
            if 'Repasse_Gazit_Liquido' in df_parcelas.columns:
                df_parcelas.drop(columns=['Repasse_Gazit_Liquido'], inplace=True)
            if 'Valor_Locacao_Total' in df_parcelas.columns:
                df_parcelas.drop(columns=['Valor_Locacao_Total'], inplace=True)
            df_parcelas = df_formata_datas_sem_horario(df_parcelas, ['Data_Vencimento', 'Data_Recebimento', 'Data_Evento'])
            df_parcelas = rename_colunas_parcelas(df_parcelas)
            df_parcelas = format_columns_brazilian(df_parcelas, ['Valor Parcela'])
        st.markdown("#### Parcelas")
        st.dataframe(df_parcelas, use_container_width=True, hide_index=True)
    else:
        st.markdown("### Parcelas")
        st.markdown("Selecione um mês para visualizar as parcelas correspondentes ao faturamento do mês.")

def colorir_parcelas_recebidas(row):
    # Converta as datas se ainda não estiverem em datetime
    venc = pd.to_datetime(row['Data Vencimento'], format='%d-%m-%Y', errors='coerce')
    receb = pd.to_datetime(row['Data Recebimento'], format='%d-%m-%Y', errors='coerce')

    if pd.isna(venc) or pd.isna(receb):
        return [''] * len(row)

    if receb > venc:
        return ['background-color: #fff9c4'] * len(row)  # Atrasado
    else:
        return [''] * len(row)  # Em dia


def colorir_parcelas_vencidas(row):
    # Converta as datas se ainda não estiverem em datetime
    venc = pd.to_datetime(row['Data Vencimento'], format='%d-%m-%Y', errors='coerce')
    receb = pd.to_datetime(row['Data Recebimento'], format='%d-%m-%Y', errors='coerce')

    if pd.isna(receb) and venc < pd.Timestamp.now():
        return ['background-color: #ffcccc'] * len(row)  # Atrasado
    elif venc < receb:
        return ['background-color: #fff9c4'] * len(row)
    else:
        return [''] * len(row)  # Em dia
    

def grafico_barras_vencimento_x_recebimento(df_parcelas_recebimento, df_parcelas_vencimento):
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
    mes_selecionado = st_echarts(option, events=events, height="300px", width="100%", key="chart_vencimento_recebimento")

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
            if 'Total_Gazit' in df_parcelas_recebimento.columns:
                df_parcelas_recebimento.drop(columns=['Total_Gazit'], inplace=True)
            if 'Repasse_Gazit_Bruto' in df_parcelas_recebimento.columns:
                df_parcelas_recebimento.drop(columns=['Repasse_Gazit_Bruto'], inplace=True)
            if 'Repasse_Gazit_Liquido' in df_parcelas_recebimento.columns:
                df_parcelas_recebimento.drop(columns=['Repasse_Gazit_Liquido'], inplace=True)
            if 'Valor_Locacao_Total' in df_parcelas_recebimento.columns:
                df_parcelas_recebimento.drop(columns=['Valor_Locacao_Total'], inplace=True)

            df_parcelas_recebimento = df_formata_datas_sem_horario(df_parcelas_recebimento, ['Data_Vencimento', 'Data_Recebimento', 'Data_Evento'])
            df_parcelas_recebimento = rename_colunas_parcelas(df_parcelas_recebimento)
            df_parcelas_recebimento = format_columns_brazilian(df_parcelas_recebimento, ['Valor Parcela'])

            df_parcelas_vencimento = df_filtrar_mes(df_parcelas_vencimento, 'Data_Vencimento', mes_selecionado)
            df_parcelas_vencimento.drop(columns=['Mes'], inplace=True)
            if 'Total_Gazit' in df_parcelas_vencimento.columns:
                df_parcelas_vencimento.drop(columns=['Total_Gazit'], inplace=True)
            if 'Repasse_Gazit_Bruto' in df_parcelas_vencimento.columns:
                df_parcelas_vencimento.drop(columns=['Repasse_Gazit_Bruto'], inplace=True)
            if 'Repasse_Gazit_Liquido' in df_parcelas_vencimento.columns:
                df_parcelas_vencimento.drop(columns=['Repasse_Gazit_Liquido'], inplace=True)
            if 'Valor_Locacao_Total' in df_parcelas_vencimento.columns:
                df_parcelas_vencimento.drop(columns=['Valor_Locacao_Total'], inplace=True)
            
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

        df_parcelas_recebimento = df_parcelas_recebimento.style.apply(colorir_parcelas_recebidas, axis=1)
        df_parcelas_vencimento = df_parcelas_vencimento.style.apply(colorir_parcelas_vencidas, axis=1)

        st.markdown(f"### Parcelas Recebidas em {nome_mes}")
        st.dataframe(df_parcelas_recebimento, use_container_width=True, hide_index=True)
        st.markdown("""
            <div style="display: flex; align-items: center;">
                <div style="width: 20px; height: 20px; background-color: #fff9c4; border: 1px solid #ccc; margin-right: 10px;"></div>
                <span>Parcelas recebidas em atraso</span>
            </div>
        """, unsafe_allow_html=True)

        st.write("")

        st.markdown(f"### Parcelas com Vencimento em {nome_mes}")
        st.dataframe(df_parcelas_vencimento, use_container_width=True, hide_index=True)
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
        st.markdown(f"### Parcelas Recebidas")
        st.markdown("Selecione um mês no gráfico para visualizar as parcelas recebidas no mês selecionado.")
        st.markdown(f"### Parcelas com Vencimento")
        st.markdown("Selecione um mês no gráfico para visualizar as parcelas com vencimento no mês selecionado.")
