import streamlit as st
import pandas as pd
from utils.components import *
from streamlit_echarts import st_echarts
from utils.functions.general_functions import *
from utils.functions.parcelas import *


def calcular_comissao_casa(row, orcamento_mes, meta_atingida):
    """
    Calcula a comissão com base na meta atingida e no valor recebido, de acordo com a regra de cada casa.
    """

    
    if row['ID Casa'] in [156, 115, 104, 114, 148]: # Girondino, Riviera, Orfeu, Bar Brahma - Centro, Bar Brahma - Granja
        if meta_atingida:
            comissao = round(row['Valor da Parcela'] * 0.015, 2)
        else:
            comissao = round(row['Valor da Parcela'] * 0.01, 2)
    elif row['ID Casa'] == 149: # Priceless
        # if meta_atingida:
        #     if row['Cargo'] == 'Analista de Eventos':
        #         comissao = round(valor_recebido * 0.01, 2)
        #     elif row['Cargo'] == 'Analista Sênior de Eventos':
        #         comissao = round(valor_recebido * 0.015, 2)
        # else:
        #     if row['Cargo'] == 'Analista de Eventos':
        #         comissao = round(valor_recebido * 0.005, 2)
        #     elif row['Cargo'] == 'Analista Sênior de Eventos':
        #         comissao = round(valor_recebido * 0.01, 2)
        if meta_atingida:
            comissao = round(row['Valor da Parcela'] * 0.015, 2)
        else:
            comissao = round(row['Valor da Parcela'] * 0.01, 2)

    elif row['ID Casa'] == 105: # Jacaré
        #2,5% de locação + 3,5% de A&B + 5% 'de Repasse artístico e Fornecedores     
        if row['Categoria Parcela'] == 'Locação':
            comissao = round(row['Valor da Parcela'] * 0.025, 2)
        elif row['Categoria Parcela'] == 'A&B':
            comissao = round(row['Valor da Parcela'] * 0.035, 2)
        # elif row['Categoria Parcela'] == 'Repasse Artistico':
        #     comissao = round(row['Valor Total Parcelas'] * 0.05, 2)
        else:
            comissao = 0.0

    return comissao


def calcular_comissao(df_recebimentos, orcamento_mes, meta_atingida):
    """
    Calcula a comissão total com base nos recebimentos e orçamentos.
    """
    # Calcula a comissão para cada recebimento
    if not df_recebimentos.empty:
        df_recebimentos['Comissão'] = df_recebimentos.apply(calcular_comissao_casa, axis=1, args=(orcamento_mes, meta_atingida))
        # Soma as comissões
        total_comissao = df_recebimentos['Comissão'].sum()
    else:
        total_comissao = 0

    #st.dataframe(df_recebimentos)

    return total_comissao


def highlight_total_row(row):
    if row['Casa'] == 'Total':
        return ['background-color: #f0f2f6; color: black;'] * len(row)
    else:
        return [''] * len(row)