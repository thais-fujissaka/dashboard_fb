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
            comissao = valor_recebido * 0.015
        else:
            comissao = valor_recebido * 0.01
    