import datetime
import pandas as pd
import concurrent.futures
from utils.functions.cmv_teorico import *
from utils.functions.cmv import *
from utils.queries_cmv import *
from utils.functions.general_functions import *
from utils.components import *
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta


TIPOS_DADOS_ITENS_VENDIDOS = {
    'Valor Unitário': float,
    'Quantidade': float,
    'Desconto': float,
    'Faturamento Bruto': float,
    'Faturamento Líquido': float
}

def grafico_cmv_orcado(df_cmv_orcado):

    dados_cmv_orcado_em_reais = df_cmv_orcado['Valor Orçamento CMV'].astype(float).tolist()
    dados_cmv_orcado_porcentagem = df_cmv_orcado['% CMV Orçado'].astype(float).tolist()

    dict_meses = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    meses = [dict_meses[mes] for mes in df_cmv_orcado['Mês']]

    option = {
        "title": {
            "text": "CMV Orçado",
            "left": "center",
            "textStyle": {
            "fontSize": 18,
            "fontWeight": "bold",
            "color": "#333"
        }
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["Valor CMV Orçado (R$)", "CMV Orçado (%)"],
            "bottom": 0,
            "left": "center"
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "top": "15%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": meses
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Valor CMV Orçado (R$)",
                "position": "left",
                "axisLine": {"lineStyle": {"color": "#1E3A8A"}},
                "axisLabel": {"formatter": "R${value}"}
            },
            {
                "type": "value",
                "name": "% CMV Orçado",
                "position": "right",
                "axisLine": {"lineStyle": {"color": "#22C55E"}},
                "axisLabel": {"formatter": "{value}%"}
            }
        ],
        "series": [
            {
                "name": "Valor CMV Orçado (R$)",
                "type": "line",
                "yAxisIndex": 0,
                "data": dados_cmv_orcado_em_reais,
                "color": "#1E3A8A"
            },
            {
                "name": "CMV Orçado (%)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dados_cmv_orcado_porcentagem,
                "color": "#22C55E"
            }
        ]
    }

    st_echarts(options=option, height="400px", key="grafico_cmv_orcado")


def calcular_cmv_teorico_ano(ano, mes_atual, id_casa, df_fichas_itens_vendidos, df_fichas_itens_producao, df_precos_insumos_de_estoque, df_itens_vendidos_dia, insumos_necessarios_estoque_casa):

    df_cmv_teorico = pd.DataFrame()
    
    # Tratamento de data
    ano_selecionado = ano
    ano_atual = get_this_year()
    if ano_selecionado != ano_atual:
        if ano_selecionado < ano_atual:
            mes_atual = 12
        if ano_selecionado > ano_atual:
            mes_atual = 12

    for mes in range(1, mes_atual + 1):
        
        ultimo_dia_mes = calendar.monthrange(ano, mes)[1]
        data_inicio = datetime.datetime(ano, mes, 1).strftime('%Y-%m-%d')
        data_fim = datetime.datetime(ano, mes, ultimo_dia_mes).strftime('%Y-%m-%d')
        
        insumos_necessarios_estoque_casa_mes = pd.concat(
            [
                insumos_necessarios_estoque_casa,
                df_fichas_itens_producao.loc[
                    df_fichas_itens_producao['ID Casa'] == id_casa,
                    ['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque']
                ].drop_duplicates()
            ],
            ignore_index=True
        ).drop_duplicates()

        df_precos_insumos_producao_mes, df_precos_itens_producao_completo_mes, df_precos_insumos_de_estoque_mes = calcular_precos_itens_producao_mes_casa(df_fichas_itens_producao, df_precos_insumos_de_estoque, insumos_necessarios_estoque_casa_mes, id_casa, mes, ano)

        ### CUSTO ITENS VENDIDOS
        
        df_precos_itens_vendidos_mes, df_fichas_itens_vendidos_mes, df_fichas_itens_vendidos_auditoria_mes = calcular_custos_itens_vendidos(df_fichas_itens_vendidos, df_precos_insumos_de_estoque_mes, df_precos_itens_producao_completo_mes)

        # Ordena colunas
        df_precos_itens_vendidos_mes = df_precos_itens_vendidos_mes.sort_values(by=['Custo Item'], ascending=False)
        df_fichas_itens_vendidos_mes = df_fichas_itens_vendidos_mes.sort_values(by=['Item Vendido Zig', 'Custo Item'], ascending=False)
        df_precos_insumos_de_estoque_mes = df_precos_insumos_de_estoque_mes.sort_values(by=['Preço Médio Insumo Estoque'], ascending=False)
        df_precos_itens_producao_completo_mes = df_precos_itens_producao_completo_mes.sort_values(by=['Custo Item Produzido'], ascending=False)
        df_precos_insumos_producao_mes = df_precos_insumos_producao_mes.sort_values(by=['Custo Ficha'], ascending=False)

        df_precos_insumos_producao_mes = df_precos_insumos_producao_mes.drop(columns={'Produção?'})

        df_itens_vendidos_dia_mes = df_itens_vendidos_dia[(df_itens_vendidos_dia['Data Venda'] >= data_inicio) & (df_itens_vendidos_dia['Data Venda'] <= data_fim)]
        df_itens_vendidos_dia_mes = df_itens_vendidos_dia_mes.sort_values(by=['ID Casa', 'Product ID'], ascending=False)
        df_itens_vendidos_dia_mes = df_itens_vendidos_dia_mes.groupby(
            ['ID Casa', 'Casa', 'Product ID', 'ID Item Zig', 'Item Vendido Zig', 'Categoria', 'Tipo']).aggregate({
                'ID Casa': 'first',
                'Casa': 'first',
                'Product ID': 'first',
                'ID Item Zig': 'first',
                'Categoria': 'first',
                'Tipo': 'first',
                'Item Vendido Zig': 'first',
                'Data Venda': 'first',
                'Valor Unitário': 'first',
                'Quantidade': 'sum',
                'Faturamento Bruto': 'sum',
                'Faturamento Líquido': 'sum',
                'Desconto': 'sum'
            })
        df_itens_vendidos_dia_mes = df_itens_vendidos_dia_mes[df_itens_vendidos_dia_mes['ID Casa'] == id_casa]
        
        df_itens_vendidos_dia_mes = df_itens_vendidos_dia_mes.astype(TIPOS_DADOS_ITENS_VENDIDOS, errors='ignore')

        # Merge faturamento com custos das fichas (% CMV Unit.)
        df_precos_itens_vendidos_mes = pd.merge(df_precos_itens_vendidos_mes, df_itens_vendidos_dia_mes[['Categoria', 'Tipo', 'Valor Unitário', 'Quantidade', 'Desconto', 'Faturamento Bruto', 'Faturamento Líquido']], how='left', on=['ID Casa', 'Casa', 'ID Item Zig'])
        df_precos_itens_vendidos_mes['% CMV Unit.'] = (df_precos_itens_vendidos_mes['Custo Item'] / df_precos_itens_vendidos_mes['Valor Unitário'])
        df_precos_itens_vendidos_mes.sort_values(by=['% CMV Unit.'], ascending=False, inplace=True)
        
        # CMV Teórico em R$
        df_precos_itens_vendidos_mes['CMV Teórico'] = df_precos_itens_vendidos_mes['Custo Item'] * df_precos_itens_vendidos_mes['Quantidade']

        # Remove itens duplicados (erro com fichas duplicadas)
        df_precos_itens_vendidos_mes = df_precos_itens_vendidos_mes.drop_duplicates(subset=['ID Item Zig'])
        
        # Métricas gerais
        cmv_teorico = df_precos_itens_vendidos_mes['CMV Teórico'].sum()
        vendas_brutas_ab = df_precos_itens_vendidos_mes['Faturamento Bruto'].sum()
        vendas_liquidas_ab = df_precos_itens_vendidos_mes['Faturamento Líquido'].sum()
        if vendas_brutas_ab > 0:
            cmv_teorico_bruto_porcentagem = round(cmv_teorico / vendas_brutas_ab * 100, 2)
        else:
            cmv_teorico_bruto_porcentagem = 0
        if vendas_liquidas_ab > 0:
            cmv_teorico_liquido_porcentagem = round(cmv_teorico / vendas_liquidas_ab * 100, 2)
        else:
            cmv_teorico_liquido_porcentagem = 0

        linha_cmv_teorico_mes = pd.DataFrame({'Mês': [mes], 'CMV Teórico (R$)': [cmv_teorico], 'CMV Teórico (% Venda Bruta)': [cmv_teorico_bruto_porcentagem], 'CMV Teórico (% Venda Líquida)': [cmv_teorico_liquido_porcentagem]})
        df_cmv_teorico = pd.concat([df_cmv_teorico, linha_cmv_teorico_mes], ignore_index=True)

    # Zera valores invalidos (pode não conter faturamento para o mês corrente)
    df_cmv_teorico = df_cmv_teorico.fillna(0)
    return df_cmv_teorico


def grafico_cmv_teorico(df_cmv_teorico):
    dados_cmv_teorico_em_reais = df_cmv_teorico['CMV Teórico (R$)'].astype(float).round(2).tolist()
    dados_cmv_teorico_bruto_porcentagem = df_cmv_teorico['CMV Teórico (% Venda Bruta)'].astype(float).round(2).tolist()
    dados_cmv_teorico_liquido_porcentagem = df_cmv_teorico['CMV Teórico (% Venda Líquida)'].astype(float).round(2).tolist()
    dict_meses = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    meses = [dict_meses[mes] for mes in df_cmv_teorico['Mês']]

    option = {
        "title": {
            "text": "CMV Teórico",
            "left": "center",
            "textStyle": {
            "fontSize": 18,
            "fontWeight": "bold",
            "color": "#333"
        }
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["Valor CMV Teórico (R$)", "CMV Teórico (% Venda Bruta)", "CMV Teórico (% Venda Líquida)"],
            "bottom": 0,
            "left": "center"
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "top": "15%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": meses
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Valor CMV Teórico (R$)",
                "position": "left",
                "axisLine": {"lineStyle": {"color": "#1E3A8A"}},
                "axisLabel": {"formatter": "R${value}"}
            },
            {
                "type": "value",
                "name": "CMV Teórico (%)",
                "position": "right",
                "axisLine": {"lineStyle": {"color": "#22C55E"}},
                "axisLabel": {"formatter": "{value}%"}
            },
        ],
        "series": [
            {
                "name": "Valor CMV Teórico (R$)",
                "type": "line",
                "yAxisIndex": 0,
                "data": dados_cmv_teorico_em_reais,
                "color": "#1E3A8A"
            },
            {
                "name": "CMV Teórico (% Venda Bruta)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dados_cmv_teorico_bruto_porcentagem,
                "color": "#22C55E"
            },
            {
                "name": "CMV Teórico (% Venda Líquida)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dados_cmv_teorico_liquido_porcentagem,
                "color": "#91CC75"
            }
        ]
    }

    st_echarts(options=option, height="400px", key="grafico_cmv_teorico")


def calcula_cmv_real_mes(ano, mes, casa):
    data_inicio = datetime.datetime(ano, mes, 1)
    data_fim = datetime.datetime(ano, mes, calendar.monthrange(ano, mes)[1])

    data_inicio_mes_anterior = (data_inicio.replace(day=1) - timedelta(days=1)).replace(day=1)
    data_fim_mes_anterior = data_inicio.replace(day=1) - timedelta(days=1)

     # Thread pool para funções independentes
    with ThreadPoolExecutor(max_workers=os.cpu_count()*3) as executor:
        # map de funções independentes
        futures = {
            executor.submit(config_faturamento_bruto_zig, data_inicio, data_fim, casa): 'faturamento_bruto_zig',
            executor.submit(config_compras, data_inicio, data_fim, casa): 'compras',
            executor.submit(config_valoracao_estoque, data_inicio, data_fim, casa): 'valoracao_estoque',
            executor.submit(config_valoracao_estoque, data_inicio_mes_anterior, data_fim_mes_anterior, casa): 'valoracao_estoque_mes_anterior',
            executor.submit(config_transferencias_gastos, data_inicio, data_fim, casa): 'transferencias_gastos',
            executor.submit(config_valoracao_producao, data_inicio, casa): 'valoracao_producao',
            executor.submit(config_valoracao_producao, data_inicio_mes_anterior, casa): 'valoracao_producao_mes_anterior'
        }
        results = {}
        for future in as_completed(futures):
            results[futures[future]] = future.result()

    # Desempacotar resultados
    df_faturamento_delivery, df_faturamento_zig, faturamento_bruto_alimentos, faturamento_bruto_bebidas, faturamento_alimentos_delivery, faturamento_bebidas_delivery = results['faturamento_bruto_zig']
    df_compras, compras_alimentos, compras_bebidas = results['compras']
    df_valoracao_estoque_atual = results['valoracao_estoque']
    df_valoracao_estoque_mes_anterior = results['valoracao_estoque_mes_anterior']
    df_transf_e_gastos, saida_alimentos, saida_bebidas, entrada_alimentos, entrada_bebidas, consumo_interno, quebras_e_perdas = results['transferencias_gastos']
    df_producao_alimentos, df_producao_bebidas, valor_producao_alimentos, valor_producao_bebidas = results['valoracao_producao']
    df_producao_alimentos_mes_anterior, df_producao_bebidas_mes_anterior, valor_producao_alimentos_mes_anterior, valor_producao_bebidas_mes_anterior = results['valoracao_producao_mes_anterior']

    df_faturamento_eventos, faturamento_alimentos_eventos, faturamento_bebidas_eventos = config_faturamento_eventos(data_inicio, data_fim, casa, faturamento_bruto_alimentos, faturamento_bruto_bebidas)
    df_variacao_estoque, variacao_estoque_alimentos, variacao_estoque_bebidas = config_variacao_estoque(df_valoracao_estoque_atual, df_valoracao_estoque_mes_anterior)
    df_producao_total = config_producao_agregada(df_producao_alimentos, df_producao_bebidas, df_producao_alimentos_mes_anterior, df_producao_bebidas_mes_anterior)


    df_producao_alimentos.drop(columns=['ID_Loja', 'Loja'], inplace=True)
    df_producao_bebidas.drop(columns=['ID_Loja', 'Loja'], inplace=True)
    df_valoracao_estoque_atual.drop(columns=['ID_Loja', 'Loja'], inplace=True)


    df_valoracao_estoque_atual = format_columns_brazilian(df_valoracao_estoque_atual, ['Valor_em_Estoque', 'Quantidade'])
    df_producao_alimentos = format_columns_brazilian(df_producao_alimentos, ['Valor_Total', 'Quantidade', 'Valor_Unidade_Medida'])
    df_producao_bebidas = format_columns_brazilian(df_producao_bebidas, ['Valor_Total', 'Quantidade', 'Valor_Unidade_Medida'])
    df_producao_total = format_columns_brazilian(df_producao_total, ['Valor Produção Mês Anterior', 'Valor Produção Atual'])
    diferenca_producao_alimentos = valor_producao_alimentos - valor_producao_alimentos_mes_anterior
    diferenca_producao_bebidas = valor_producao_bebidas - valor_producao_bebidas_mes_anterior

    cmv_alimentos = compras_alimentos - variacao_estoque_alimentos - saida_alimentos + entrada_alimentos - consumo_interno - diferenca_producao_alimentos
    cmv_bebidas = compras_bebidas - variacao_estoque_bebidas - saida_bebidas + entrada_bebidas - diferenca_producao_bebidas
    cmv_alimentos_e_bebidas = cmv_alimentos + cmv_bebidas
    faturamento_total_alimentos = faturamento_bruto_alimentos + faturamento_alimentos_delivery + faturamento_alimentos_eventos
    faturamento_total_bebidas = faturamento_bruto_bebidas + faturamento_bebidas_delivery + faturamento_bebidas_eventos

    if faturamento_total_alimentos != 0 and faturamento_total_bebidas != 0:
        cmv_percentual_geral = ((cmv_alimentos + cmv_bebidas)/(faturamento_total_alimentos+faturamento_total_bebidas)) * 100
    else:
        cmv_percentual_geral = 0

    return pd.DataFrame({
        'Mês': [mes],
        'CMV Real (R$)': [cmv_alimentos_e_bebidas],
        'CMV Real (%)': [cmv_percentual_geral]
    })
    

def calcula_cmv_real_ano_paralelo(ano, mes_atual, casa):
    df_cmv_real = pd.DataFrame()

    # Tratamento de data
    ano_selecionado = ano
    ano_atual = get_this_year()
    if ano_selecionado != ano_atual:
        if ano_selecionado < ano_atual:
            mes_atual = 12
        if ano_selecionado > ano_atual:
            mes_atual = 12

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(calcula_cmv_real_mes, ano, mes, casa): mes for mes in range(1, mes_atual + 1)}

        for future in as_completed(futures):
            df_cmv_real = pd.concat([df_cmv_real, future.result()], ignore_index=True)

    df_cmv_real.fillna(0, inplace=True)
    df_cmv_real.sort_values('Mês', inplace=True)
    return df_cmv_real


def grafico_cmv_real(df_cmv_real):

    dados_cmv_real_em_reais = df_cmv_real['CMV Real (R$)'].astype(float).round(2).tolist()
    dados_cmv_real_porcentagem = df_cmv_real['CMV Real (%)'].astype(float).round(2).tolist()

    dict_meses = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    meses = [dict_meses[mes] for mes in df_cmv_real['Mês']]

    option = {
        "title": {
            "text": "CMV Real",
            "left": "center",
            "textStyle": {
            "fontSize": 18,
            "fontWeight": "bold",
            "color": "#333"
        }
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["Valor CMV Real (R$)", "CMV Real (%)"],
            "bottom": 0,
            "left": "center"
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "top": "15%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": meses
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Valor CMV Real (R$)",
                "position": "left",
                "axisLine": {"lineStyle": {"color": "#1E3A8A"}},
                "axisLabel": {"formatter": "R${value}"}
            },
            {
                "type": "value",
                "name": "% CMV Real",
                "position": "right",
                "axisLine": {"lineStyle": {"color": "#22C55E"}},
                "axisLabel": {"formatter": "{value}%"}
            }
        ],
        "series": [
            {
                "name": "Valor CMV Real (R$)",
                "type": "line",
                "yAxisIndex": 0,
                "data": dados_cmv_real_em_reais,
                "color": "#1E3A8A"
            },
            {
                "name": "CMV Real (%)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dados_cmv_real_porcentagem,
                "color": "#22C55E"
            }
        ]
    }

    st_echarts(options=option, height="400px", key="grafico_cmv_real")
