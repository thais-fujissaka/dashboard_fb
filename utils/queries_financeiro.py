import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query

@st.cache_data
def GET_DESPESAS():
  return dataframe_query(f'''
  SELECT 
    tdr.ID AS ID,
    te.NOME_FANTASIA AS Loja,
    tf.CORPORATE_NAME AS Fornecedor,
    tdr.NF AS Doc_Serie,
    STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d') AS Data_Emissao,
    STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d') AS Data_Vencimento,
    CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE), '%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes,
    tdr.OBSERVACAO AS Descricao,
    tdr.VALOR_LIQUIDO AS Valor_Liquido,
    tccg2.DESCRICAO AS Classificacao_Contabil_2,
    tccg1.DESCRICAO AS Classificacao_Contabil_1,
    CASE 
      WHEN tdr.FK_Status = 'Provisionado' THEN 'Provisionado'
      ELSE 'Real'
    END AS Status
  FROM T_DESPESA_RAPIDA tdr
  JOIN T_EMPRESAS te ON tdr.FK_LOJA = te.ID
  LEFT JOIN T_FORNECEDOR tf ON tdr.FK_FORNECEDOR = tf.ID
  LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID
  LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON tccg2.FK_GRUPO_1 = tccg1.ID
  WHERE tccg1.FK_VERSAO_PLANO_CONTABIL = 103
    AND NOT EXISTS (
      SELECT 1
      FROM T_DESPESA_RAPIDA_ITEM tdri
      WHERE tdri.FK_DESPESA_RAPIDA = tdr.ID);
''')


@st.cache_data
def GET_ORCAMENTOS_DESPESAS():
  return dataframe_query(f'''
  SELECT
    to2.ID AS ID_Orcamento,
    te.NOME_FANTASIA AS Loja,
    tccg2.DESCRICAO AS Classificacao_Contabil_2,
    tccg1.DESCRICAO AS Classificacao_Contabil_1,
    to2.VALOR AS Orcamento,
    cast(date_format(cast(CONCAT(to2.ANO, '-', to2.MES, '-01') AS date), '%Y-%m-01') as date) AS Primeiro_Dia_Mes
  FROM
    T_ORCAMENTOS to2 
  LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON to2.FK_CLASSIFICACAO_2 = tccg2.ID
  LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg1 ON tccg2.FK_GRUPO_1 = tccg1.ID
  LEFT JOIN T_EMPRESAS te ON to2.FK_EMPRESA = te.ID;
''')