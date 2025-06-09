import streamlit as st
import pandas as pd
from utils.components import *
from streamlit_echarts import st_echarts
from utils.functions.general_functions import *
from utils.functions.parcelas import *


def calculo_comissao(meta_atingida, valor_recebido, id_casa):
    """
    Calcula a comissão com base na meta atingida e no valor recebido, de acordo com a regra de cada casa.
    """
    if id_casa in [156, 115, 104, 114, 148]: # Girondino, Riviera, Orfeu, Bar Brahma - Centro, Bar Brahma - Granja
        if meta_atingida:
            comissao = round(valor_recebido * 0.015, 2)
        else:
            comissao = round(valor_recebido * 0.01, 2)
    elif id_casa == 149: # Priceless
        # Adicionar lógica para cargo do Priceless
        if meta_atingida:
            comissao = round(valor_recebido * 0.015, 2)
        else:
            comissao = round(valor_recebido * 0.01, 2)
    elif id_casa == 105: # Jacaré
        #2,5% de locação + 3,5% de A&B + 5% 'de Repasse artístico e Fornecedores     
        print("Jacaré")
    return comissao
    