import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query
from utils.constants.general_constants import casas_validas


@st.cache_data
def GET_DESCONTOS():
    df_descontos = dataframe_query('''
      SELECT 
        td.FK_CASA,
        td.FUNCIONARIO,
        td.DATA,
        td.CLIENTES,
        td.JUSTIFICATIVA,
        td.CATEGORIA,
        td.PORCENTAGEM,
        td.DESCONTO,
        td.PRODUTOS     
      FROM T_DESCONTOS AS td
      WHERE td.FK_CASA IS NOT NULL
      AND td.FK_CASA != 0                                                                                                                                                     
      ''')
    return df_descontos

