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
    else: return

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
    tab_names = ['**Total de Eventos - Priceless**', '**Locação Aroo**', '**Locação Anexo**', '**Locação Notiê**', '**Locação Mirante**', '**Alimentos e Bebidas**']
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
            "left": "0",
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
                "show": False
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

    mes_selecionado = st_echarts(option, events=events, height="320px", width="100%", key=f"chart_total_eventos_{tipo_data}")
    
    
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
            if df_parcelas is not None and not df_parcelas.empty:
                total_parcelas_mes = format_brazilian(df_parcelas['Valor Parcela'].sum())
            df_parcelas = format_columns_brazilian(df_parcelas, ['Valor Parcela', 'Valor Bruto Repasse Gazit', 'Total Locação'])
        st.markdown("#### Parcelas")
        st.dataframe(df_parcelas, use_container_width=True, hide_index=True)
        if df_parcelas is not None and not df_parcelas.empty:
            st.markdown(f"**Valor Total das Parcelas: R$ {total_parcelas_mes}**")
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


# def calcula_valor_parcela_locacao_espaco(df_parcelas, df_eventos):

#     df_eventos = df_fracao_locacao_espacos(df_eventos)

#     st.dataframe(df_eventos[['ID_Evento', 'Fracao_Aroo', 'Fracao_Anexo', 'Fracao_Notie', 'Fracao_Mirante']])
#     st.dataframe(df_parcelas)

#     # Merge df_parcelas com fracoes de cada espaço
#     df_parcelas = df_parcelas.merge(df_eventos[['ID_Evento', 'Fracao_Aroo', 'Fracao_Anexo', 'Fracao_Notie', 'Fracao_Mirante']], how='left', on='ID_Evento')
    
#     df_parcelas['Valor_Parcela_Aroos'] = df_parcelas['Valor_Parcela'] * df_parcelas['Fracao_Aroo']
#     df_parcelas['Valor_Parcela_Anexo'] = df_parcelas['Valor_Parcela'] * df_parcelas['Fracao_Anexo']
#     df_parcelas['Valor_Parcela_Notie'] = df_parcelas['Valor_Parcela'] * df_parcelas['Fracao_Notie']
#     df_parcelas['Valor_Parcela_Mirante'] = df_parcelas['Valor_Parcela'] * df_parcelas['Fracao_Mirante']

#     st.dataframe(df_parcelas)
#     duplicadas = df_parcelas.columns[df_parcelas.columns.duplicated()].tolist()
#     if duplicadas:
#         st.warning(f"Colunas duplicadas detectadas: {duplicadas}")
#     return df_parcelas


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

    #df_parcelas = calcula_valor_parcela_locacao_espaco(df_parcelas, df_eventos)

    # Define o nome da coluna de valor da parcela de acordo com o espaço
    dict_espacos = {
        'Aroo': 'Valor Parcela AROO',
        'Anexo': 'Valor Parcela ANEXO',
        'Notiê': 'Valor Parcela Notie',
        'Mirante': 'Valor Parcela Mirante'
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
            df_parcelas.drop(columns=['Mes', 'Ano', 'Valor_Locacao_Total', 'Total_Gazit', 'Repasse_Gazit_Bruto', 'Repasse_Gazit_Liquido'], inplace=True)
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
            "data": ["Orçamento", "Faturamento"],
            "top": "top",
            "textStyle": {"color": "#000"}
        },
        "grid": {
            "left": "0",
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
                "show": False
            }
        ],
        "series": [
            {
                "name": "Orçamento",
                "type": "bar",
                "barWidth": "40%",
                "barGap": "5%",
                "data": dados_orcamentos_com_labels,
                "itemStyle": {
                    "color": "#5470C6"
                }
            },
            {
                "name": "Faturamento",
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
    mes_selecionado = st_echarts(option, events=events, height="320px", width="100%", key=f"chart_faturamento_{categoria_evento}")
    
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


def grafico_linhas_faturamento_tipo_evento(df_eventos_tipo_evento, id_casa):

    if id_casa != -1:
        df_eventos_tipo_evento = df_eventos_tipo_evento[df_eventos_tipo_evento['ID Casa'] == id_casa].copy()

    if df_eventos_tipo_evento.empty:
        st.error("Não há dados de eventos disponíveis para o gráfico.")
        return
    
    df_eventos_tipo_evento['Mês'] = df_eventos_tipo_evento['Data_Evento'].dt.month
    df_eventos_tipo_evento = df_eventos_tipo_evento.groupby(['Mês', 'Tipo Evento'])['Valor_Total'].sum().reset_index()
    meses = {
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
    nomes_meses = list(meses.values())

    # Dataframe com meses
    df_meses = pd.DataFrame({'Mês': list(range(1, 13)), 'Nome_Mes': list(meses.values())})
    # Dataframe com os tipos de eventos
    tipos_evento = df_eventos_tipo_evento['Tipo Evento'].unique().tolist()
    df_tipos_evento = pd.DataFrame({'Tipo Evento': tipos_evento})
    # Dataframe com a combinação de meses e tipos de eventos
    df_tipos_evento_meses = pd.merge(df_meses.assign(key=1), df_tipos_evento.assign(key=1), on='key').drop('key', axis=1)
    df_eventos_tipo_evento = df_tipos_evento_meses.merge(df_eventos_tipo_evento, how='left', on=['Mês', 'Tipo Evento'])
    df_eventos_tipo_evento['Valor_Total'].fillna(0, inplace=True)
    
    # Cria lista de valores e labels por mês de cada tipo de evento
    valores_tipo_evento = {}
    for tipo in tipos_evento:
        # Cria lista de valores por mês de cada tipo de evento
        valores = df_eventos_tipo_evento[df_eventos_tipo_evento['Tipo Evento'] == tipo]['Valor_Total'].round(2).tolist()
        labels = [format_brazilian(v) for v in valores]
    
        valores_tipo_evento[tipo] = [
            {
                "value": v,
                "label": {
                    "show": False
                }
            }
            for v, lbl in zip(valores, labels)
        ]

    legenda = list(valores_tipo_evento.keys())

    series = []
    for tipo, valores in valores_tipo_evento.items():
        series.append(
            {
                "name": f"{tipo}",
                "type": "line",
                "stack": "Total",
                "label": {
                    "show": True,
                    "position": "top"
                },
                "areaStyle": {},
                "emphasis": {
                    "focus": "series"
                },
                "data": valores
            }
        )
    # Cria grafico de linhas
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross",
                "label": {
                    "backgroundColor": "#6a7985"
                }
            }
        },
        "legend": {
            "data": legenda
        },
        "toolbox": {
            "feature": {
                "saveAsImage": {}
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
                "boundaryGap": False,
                "data": nomes_meses
            }
        ],
        "yAxis": [
            {
                "type": "value"
            }
        ],
        "series": series
    }

    # Exibe o gráfico no Streamlit
    st_echarts(options=option, height="320px")



def grafico_linhas_faturamento_modelo_evento(df_eventos_modelo_evento, id_casa):

    if id_casa != -1:
        df_eventos_modelo_evento = df_eventos_modelo_evento[df_eventos_modelo_evento['ID Casa'] == id_casa].copy()

    if df_eventos_modelo_evento.empty:
        st.error("Não há dados de eventos disponíveis para o gráfico.")
        return
    
    df_eventos_modelo_evento['Mês'] = df_eventos_modelo_evento['Data_Evento'].dt.month
    df_eventos_modelo_evento = df_eventos_modelo_evento.groupby(['Mês', 'Modelo Evento'])['Valor_Total'].sum().reset_index()
    meses = {
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
    nomes_meses = list(meses.values())

    # Dataframe com meses
    df_meses = pd.DataFrame({'Mês': list(range(1, 13)), 'Nome_Mes': list(meses.values())})
    # Dataframe com os tipos de eventos
    modelos_evento = df_eventos_modelo_evento['Modelo Evento'].unique().tolist()
    df_modelos_evento = pd.DataFrame({'Modelo Evento': modelos_evento})
    # Dataframe com a combinação de meses e tipos de eventos
    df_modelos_evento_meses = pd.merge(df_meses.assign(key=1), df_modelos_evento.assign(key=1), on='key').drop('key', axis=1)
    df_eventos_modelo_evento = df_modelos_evento_meses.merge(df_eventos_modelo_evento, how='left', on=['Mês', 'Modelo Evento'])
    df_eventos_modelo_evento['Valor_Total'].fillna(0, inplace=True)
    
    # Cria lista de valores e labels por mês de cada tipo de evento
    valores_modelo_evento = {}
    for modelo in modelos_evento:
        # Cria lista de valores por mês de cada tipo de evento
        valores = df_eventos_modelo_evento[df_eventos_modelo_evento['Modelo Evento'] == modelo]['Valor_Total'].round(2).tolist()
        labels = [format_brazilian(v) for v in valores]
    
        valores_modelo_evento[modelo] = [
            {
                "value": v,
                "label": {
                    "show": False
                }
            }
            for v, lbl in zip(valores, labels)
        ]

    legenda = list(valores_modelo_evento.keys())

    series = []
    for modelo, valores in valores_modelo_evento.items():
        series.append(
            {
                "name": f"{modelo}",
                "type": "line",
                "stack": "Total",
                "label": {
                    "show": True,
                    "position": "top"
                },
                "areaStyle": {},
                "emphasis": {
                    "focus": "series"
                },
                "data": valores
            }
        )
    # Cria grafico de linhas
    option = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {
                "type": "cross",
                "label": {
                    "backgroundColor": "#6a7985"
                }
            }
        },
        "legend": {
            "data": legenda
        },
        "toolbox": {
            "feature": {
                "saveAsImage": {}
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
                "boundaryGap": False,
                "data": nomes_meses
            }
        ],
        "yAxis": [
            {
                "type": "value"
            }
        ],
        "series": series
    }

    # Exibe o gráfico no Streamlit
    st_echarts(options=option, height="320px")