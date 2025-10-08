import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query, execute_query


@st.cache_data
def item_sold():
  return dataframe_query(f"""
    WITH ULTIMO_VALOR AS (
      SELECT 
        IV.PRODUCT_ID,
        MAX(IV.TRANSACTION_DATE) AS MAX_DATE,
        IV.UNIT_VALUE
      FROM T_ITENS_VENDIDOS IV
      WHERE IV.UNIT_VALUE > 1
      GROUP BY IV.PRODUCT_ID
    )

    SELECT
        IVC.CASA AS 'EMPRESA',
        AIFT.ID AS 'ID_Assoc',
        IVC.ITEM_VENDIDO AS 'Item Vendido',
        IVC.CATEGORIA AS 'CATEGORIA',
        IE.ID AS 'ID Insumo de Estoque',
        IE.DESCRICAO AS 'Insumo de Estoque',
        UM.UNIDADE_MEDIDA AS 'Unidade Medida',
        AIFT.QUANTIDADE_POR_FICHA AS 'Quantidade na Ficha',
        UV.UNIT_VALUE AS 'VALOR DO ITEM'
    FROM T_ASSOCIATIVA_INSUMOS_FICHA_TECNICA AIFT
    LEFT JOIN T_FICHAS_TECNICAS FT ON AIFT.FK_FICHA_TECNICA = FT.ID
    LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA IVC ON FT.FK_ITEM_VENDIDO_POR_CASA = IVC.ID
    LEFT JOIN T_INSUMOS_ESTOQUE IE ON AIFT.FK_ITEM_ESTOQUE = IE.ID
    LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON IE.FK_UNIDADE_MEDIDA = UM.ID
    LEFT JOIN ULTIMO_VALOR UV ON UV.PRODUCT_ID = IVC.ID_ZIG_ITEM_VENDIDO

    UNION ALL

    SELECT 
        IVC.CASA AS 'EMPRESA',
        AIPFT.ID AS 'ID_Assoc',
        IVC.ITEM_VENDIDO AS 'Item Vendido',
        IVC.CATEGORIA AS 'CATEGORIA',
        'IP' AS 'ID Insumo de Estoque',
        IP.NOME_ITEM_PRODUZIDO AS 'Insumo de Estoque',
        UM.UNIDADE_MEDIDA AS 'Unidade Medida',
        AIPFT.QUANTIDADE AS 'Quantidade na Ficha',
        UV.UNIT_VALUE AS 'VALOR DO ITEM'
    FROM T_ASSOCIATIVA_ITENS_PRODUCAO_FICHA_TECNICA AIPFT
    LEFT JOIN T_FICHAS_TECNICAS FT ON AIPFT.FK_FICHA_TECNICA = FT.ID
    LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA IVC ON FT.FK_ITEM_VENDIDO_POR_CASA = IVC.ID
    LEFT JOIN T_ITENS_PRODUCAO IP ON AIPFT.FK_ITEM_PRODUCAO = IP.ID
    LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON IP.FK_UNIDADE_MEDIDA = UM.ID
    LEFT JOIN ULTIMO_VALOR UV ON UV.PRODUCT_ID = IVC.ID_ZIG_ITEM_VENDIDO
    ORDER BY `Item Vendido`;
    """)


@st.cache_data
def input_produced(day, day2):
    return dataframe_query(f"""
        SELECT
            E.NOME_FANTASIA AS 'EMPRESA',
            IP.NOME_ITEM_PRODUZIDO AS 'ITEM PRODUZIDO',
            FTP.QUANTIDADE_FICHA AS 'RENDIMENTO',
            COALESCE(IE.DESCRICAO, IP2.NOME_ITEM_PRODUZIDO) AS 'Insumo de Estoque',
            AFTIP.QUANTIDADE AS 'QUANTIDADE INSUMO',
            #(DRI.VALOR / DRI.QUANTIDADE) AS 'Média Preço (Insumo de Compra)',
            ((DRI.VALOR / DRI.QUANTIDADE) / ACE.PROPORCAO) AS 'MÉDIA PREÇO NO ITEM KG',
            (AFTIP.QUANTIDADE / 1000) * ((DRI.VALOR / DRI.QUANTIDADE) / ACE.PROPORCAO) AS 'VALOR PRODUÇÃO'
        FROM T_ITENS_PRODUCAO IP
        LEFT JOIN T_EMPRESAS E ON E.ID = IP.FK_EMPRESA
        LEFT JOIN T_FICHA_TECNICA_PRODUCAO FTP ON FTP.FK_ITEM_PRODUZIDO = IP.ID
        LEFT JOIN T_ASSOCIATIVA_FICHAS_TECNICAS_ITENS_PRODUCAO AFTIP ON AFTIP.FK_FICHA_PRODUCAO = FTP.ID
        LEFT JOIN T_ITENS_PRODUCAO IP2 ON IP2.ID = AFTIP.FK_ITEM_PRODUZIDO 
        LEFT JOIN T_INSUMOS_ESTOQUE IE ON IE.ID = AFTIP.FK_INSUMO_ESTOQUE
        LEFT JOIN T_ASSOCIATIVA_COMPRA_ESTOQUE ACE ON IE.ID = ACE.FK_INSUMO_ESTOQUE
        LEFT JOIN T_INSUMOS_NIVEL_5 N5 ON ACE.FK_INSUMO = N5.ID
        LEFT JOIN T_INSUMOS_NIVEL_4 N4 ON N4.ID = N5.FK_INSUMOS_NIVEL_4
        LEFT JOIN T_INSUMOS_NIVEL_3 N3 ON N3.ID = N4.FK_INSUMOS_NIVEL_3
        LEFT JOIN T_INSUMOS_NIVEL_2 N2 ON N2.ID = N3.FK_INSUMOS_NIVEL_2
        LEFT JOIN T_INSUMOS_NIVEL_1 N1 ON N1.ID = N2.FK_INSUMOS_NIVEL_1
        LEFT JOIN (
            SELECT
                DRI.ID,
                DR.COMPETENCIA,
                E2.NOME_FANTASIA,
                E2.ID AS ID_CASA,
                DRI.FK_INSUMO,
                DRI.QUANTIDADE,
                DRI.VALOR,
                ACE.FK_INSUMO_ESTOQUE,
                ACE.PROPORCAO
            FROM T_DESPESA_RAPIDA_ITEM DRI
            INNER JOIN T_DESPESA_RAPIDA DR ON DR.ID = DRI.FK_DESPESA_RAPIDA
            LEFT JOIN T_ASSOCIATIVA_COMPRA_ESTOQUE ACE ON ACE.FK_INSUMO = DRI.FK_INSUMO
            LEFT JOIN T_EMPRESAS E2 ON E2.ID = DR.FK_LOJA
            WHERE DATE(DR.COMPETENCIA) >= '{day}' AND DATE(DR.COMPETENCIA) <= '{day2}'
            AND DRI.VALOR > 0
            GROUP BY DRI.ID
        ) AS DRI ON DRI.FK_INSUMO = N5.ID
        LEFT JOIN T_CONTAGEM_INSUMOS CI ON CI.FK_INSUMO = N5.ID
        WHERE (DATE(CI.DATA_CONTAGEM) >= '{day}' 
        AND DATE(CI.DATA_CONTAGEM) <= '{day2}' OR CI.DATA_CONTAGEM IS NULL)
        AND FTP.ID IS NOT NULL
        AND N1.DESCRICAO IN ('BEBIDAS','ALIMENTOS')
        GROUP BY E.ID, IP.ID, IE.ID
        ORDER BY IP.NOME_ITEM_PRODUZIDO
""")


@st.cache_data
def GET_AVG_PRICE_INPUT_N5(day, day2):
  return dataframe_query(f"""
SELECT 
    E.ID AS 'CASA ID',
    E.NOME_FANTASIA AS 'EMPRESA',
    N5.ID AS 'ID N5',
    N5.DESCRICAO AS 'INSUMO N5',
    UM.UNIDADE_MEDIDA_NAME AS 'Unidade de  Medida N5',
    SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE) AS 'Média Preço (Insumo de Compra)',
    IE.ID AS 'ID Insumo de Estoque',
    IE.DESCRICAO AS 'Insumo de Estoque',
    UM2.UNIDADE_MEDIDA_NAME AS 'Unidade de Medida Estoque',
    ROUND(CAST(SUM(DRI.VALOR) AS FLOAT), 2) AS 'VALOR DRI',
    ROUND(CAST(SUM(DRI.QUANTIDADE) AS FLOAT), 3) AS 'QUANTIDADE DRI',
    ACE.PROPORCAO AS 'PROPORÇÃO ACE',
    (SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE)) / ACE.PROPORCAO AS 'Média Preço (Insumo Estoque)'
  
    FROM T_DESPESA_RAPIDA_ITEM DRI 
    INNER JOIN T_INSUMOS_NIVEL_5 N5 ON (DRI.FK_INSUMO = N5.ID)
    LEFT JOIN T_INSUMOS_NIVEL_4 N4 ON N4.ID = N5.FK_INSUMOS_NIVEL_4
    LEFT JOIN T_INSUMOS_NIVEL_3 N3 ON N3.ID = N4.FK_INSUMOS_NIVEL_3
    LEFT JOIN T_INSUMOS_NIVEL_2 N2 ON N2.ID = N3.FK_INSUMOS_NIVEL_2
    LEFT JOIN T_INSUMOS_NIVEL_1 N1 ON N1.ID = N2.FK_INSUMOS_NIVEL_1
    INNER JOIN T_DESPESA_RAPIDA DR ON (DRI.FK_DESPESA_RAPIDA = DR.ID)
    INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
    LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON (N5.FK_UNIDADE_MEDIDA = UM.ID)
    LEFT JOIN T_ASSOCIATIVA_COMPRA_ESTOQUE ACE ON (ACE.FK_INSUMO = N5.ID)
    LEFT JOIN T_INSUMOS_ESTOQUE IE ON (IE.ID = ACE.FK_INSUMO_ESTOQUE)
    LEFT JOIN T_UNIDADES_DE_MEDIDAS UM2 ON IE.FK_UNIDADE_MEDIDA = UM2.ID
    WHERE STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d') >= '{day}'
    AND STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d') <= '{day2}'
    AND N1.DESCRICAO IN ('BEBIDAS','ALIMENTOS')
    GROUP BY E.ID, N5.ID
    ORDER BY N5.DESCRICAO
""")


# CMV Teórico

def GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_INSUMOS_ESTOQUE():
    return dataframe_query(f'''
        SELECT
            VIVC.ID_CASA AS 'ID Casa',
            VIVC.CASA AS 'Casa',
            VIVC.ID_ITEM_VENDIDO AS 'ID Item Zig',
            VIVC.ITEM_VENDIDO AS 'Item Vendido Zig',
            FT.ID AS 'ID Ficha Técnica',
            IE.ID AS 'ID Insumo Estoque',
            IE.DESCRICAO AS 'Insumo Estoque',
            AIFT.QUANTIDADE_POR_FICHA AS 'Quantidade na Ficha',
            UM.UNIDADE_MEDIDA AS 'Unidade Medida',
            0 AS 'Produção?'
        FROM T_FICHAS_TECNICAS FT
        LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA VIVC ON FT.FK_ITEM_VENDIDO_POR_CASA = VIVC.ID
        LEFT JOIN T_ASSOCIATIVA_INSUMOS_FICHA_TECNICA AIFT ON AIFT.FK_FICHA_TECNICA = FT.ID
        LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON AIFT.FK_UNIDADE_MEDIDA = UM.ID
        INNER JOIN T_INSUMOS_ESTOQUE IE ON AIFT.FK_ITEM_ESTOQUE = IE.ID
        GROUP BY VIVC.ID_CASA, FT.ID, IE.ID
    ''')


def GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_ITENS_PRODUCAO():
    return dataframe_query(f'''
        SELECT
            VIVC.ID_CASA AS 'ID Casa',
            VIVC.CASA AS 'Casa',
            VIVC.ID_ITEM_VENDIDO AS 'ID Item Zig',
            VIVC.ITEM_VENDIDO AS 'Item Vendido Zig',
            FT.ID AS 'ID Ficha Técnica',
            IP.ID AS 'ID Insumo Produção',
            IP.NOME_ITEM_PRODUZIDO AS 'Insumo Produção',
            AIPFT.QUANTIDADE AS 'Quantidade na Ficha',
            UM.UNIDADE_MEDIDA AS 'Unidade Medida',
            1 AS 'Produção?'
        FROM T_FICHAS_TECNICAS FT
        LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA VIVC ON FT.FK_ITEM_VENDIDO_POR_CASA = VIVC.ID
        LEFT JOIN T_ASSOCIATIVA_ITENS_PRODUCAO_FICHA_TECNICA AIPFT ON AIPFT.FK_FICHA_TECNICA = FT.ID
        LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON AIPFT.FK_UNIDADE_MEDIDA = UM.ID
        INNER JOIN T_ITENS_PRODUCAO IP ON AIPFT.FK_ITEM_PRODUCAO = IP.ID
        GROUP BY VIVC.ID_CASA, FT.ID, IP.ID
    ''')


def GET_FICHAS_TECNICAS_DE_INSUMOS_PRODUCAO():
    return dataframe_query(f'''
        SELECT
            te.ID AS 'ID Casa',
            te.NOME_FANTASIA AS 'Casa',
            tftp.ID AS 'ID Ficha Técnica Produção',
            tip.ID AS 'ID Item Produzido',
            tip.NOME_ITEM_PRODUZIDO AS 'Item Produzido',
            tftp.QUANTIDADE_FICHA AS 'Quantidade Rendimento',
            tudm2.UNIDADE_MEDIDA AS 'U.M. Rendimento',
            tie.ID AS 'ID Insumo Estoque',
            tie.DESCRICAO AS 'Insumo Estoque',
            tip2.ID AS 'ID Insumo Produção',
            tip2.NOME_ITEM_PRODUZIDO AS 'Insumo Produção',
            taftip.QUANTIDADE AS 'Quantidade',
            tudm.UNIDADE_MEDIDA AS 'U.M. Ficha Itens',
            CASE WHEN tip2.ID IS NULL THEN 0 ELSE 1 END AS 'Produção?'
        FROM
            T_FICHA_TECNICA_PRODUCAO tftp
            LEFT JOIN T_ITENS_PRODUCAO tip ON tip.ID = tftp.FK_ITEM_PRODUZIDO
            LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm2 ON tudm2.ID = tftp.FK_UNIDADE_MEDIDA
            LEFT JOIN T_ASSOCIATIVA_FICHAS_TECNICAS_ITENS_PRODUCAO taftip ON taftip.FK_FICHA_PRODUCAO = tftp.ID
            LEFT JOIN T_EMPRESAS te ON te.ID = tip.FK_EMPRESA
            LEFT JOIN T_INSUMOS_ESTOQUE tie ON tie.ID = taftip.FK_INSUMO_ESTOQUE
            LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON tudm.ID = taftip.UNIDADE_MEDIDA
            LEFT JOIN T_ITENS_PRODUCAO tip2 ON tip2.ID = taftip.FK_ITEM_PRODUZIDO
    ''')


@st.cache_data
def GET_PRECOS_INSUMOS_N5_COM_PROPORCAO_ESTOQUE():
    return dataframe_query(f'''
        SELECT 
            E.ID AS 'ID Casa',
            E.NOME_FANTASIA AS 'Casa',
            DATE(DR.COMPETENCIA) AS 'Data Compra',
            MONTH(DR.COMPETENCIA) AS 'Mês Compra',
            YEAR(DR.COMPETENCIA) AS 'Ano Compra',
            N5.ID AS 'ID N5',
            N5.DESCRICAO AS 'Insumo N5',
            UM.UNIDADE_MEDIDA_NAME AS 'U.M. N5',
            ROUND(CAST(SUM(DRI.VALOR) AS FLOAT), 2) AS 'Valor N5',
            ROUND(CAST(SUM(DRI.QUANTIDADE) AS FLOAT), 3) AS 'Quantidade N5',
            SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE) AS 'Preço Médio N5',
            IE.ID AS 'ID Insumo Estoque',
            IE.DESCRICAO AS 'Insumo Estoque',
            UM2.UNIDADE_MEDIDA AS 'U.M. Insumo Estoque',
            ACE.PROPORCAO AS 'Proporção ACE',
            ACE.PROPORCAO * ROUND(CAST(SUM(DRI.QUANTIDADE) AS FLOAT), 3) AS 'Quantidade Insumo Estoque',
            (SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE)) / ACE.PROPORCAO AS 'Preço Médio Insumo N5 Estoque'
        FROM T_DESPESA_RAPIDA_ITEM DRI 
            INNER JOIN T_INSUMOS_NIVEL_5 N5 ON (DRI.FK_INSUMO = N5.ID)
            LEFT JOIN T_INSUMOS_NIVEL_4 N4 ON N4.ID = N5.FK_INSUMOS_NIVEL_4
            LEFT JOIN T_INSUMOS_NIVEL_3 N3 ON N3.ID = N4.FK_INSUMOS_NIVEL_3
            LEFT JOIN T_INSUMOS_NIVEL_2 N2 ON N2.ID = N3.FK_INSUMOS_NIVEL_2
            LEFT JOIN T_INSUMOS_NIVEL_1 N1 ON N1.ID = N2.FK_INSUMOS_NIVEL_1
            INNER JOIN T_DESPESA_RAPIDA DR ON (DRI.FK_DESPESA_RAPIDA = DR.ID)
            INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
            LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON (N5.FK_UNIDADE_MEDIDA = UM.ID)
            LEFT JOIN T_ASSOCIATIVA_COMPRA_ESTOQUE ACE ON (ACE.FK_INSUMO = N5.ID)
            LEFT JOIN T_INSUMOS_ESTOQUE IE ON (IE.ID = ACE.FK_INSUMO_ESTOQUE)
            LEFT JOIN T_UNIDADES_DE_MEDIDAS UM2 ON IE.FK_UNIDADE_MEDIDA = UM2.ID
        WHERE DR.COMPETENCIA >= '2023-01-01'
            AND N1.DESCRICAO IN ('BEBIDAS','ALIMENTOS')
        GROUP BY E.ID, N5.ID
        ORDER BY E.NOME_FANTASIA ASC, N5.DESCRICAO
''')


def GET_CASAS_ITENS_PRODUCAO():
    return dataframe_query(f'''
        SELECT
        ID AS 'ID Insumo Produção',
        FK_EMPRESA AS 'ID Casa Produção'
        FROM T_ITENS_PRODUCAO
    ''')


@st.cache_data
def GET_FATURAMENTO_ITENS_VENDIDOS_DIA():
  return dataframe_query(f'''
    SELECT 
      tivd.FK_CASA AS 'ID Casa',
      te.NOME_FANTASIA AS 'Casa',
      tvivpc.ID_ITEM_VENDIDO AS 'ID Item Zig',
      tvivpc.ID_ZIG_ITEM_VENDIDO AS 'Product ID',
      tivd.PRODUCT_NAME AS 'Item Vendido Zig',
      DATE(tivd.EVENT_DATE) AS 'Data Venda',
      SUM(QUANTIDADE * VALOR_UNITARIO) / SUM(QUANTIDADE) AS 'Valor Unitário',
      SUM(tivd.QUANTIDADE) AS 'Quantidade',
      SUM(tivd.DESCONTO) AS 'Desconto',
      COALESCE((tivd.VALOR_UNITARIO * tivd.QUANTIDADE), 0) AS 'Faturamento Bruto',
      COALESCE(((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO), 0) AS 'Faturamento Líquido'
    FROM T_ITENS_VENDIDOS_DIA tivd
    LEFT JOIN T_EMPRESAS te ON te.ID = tivd.FK_CASA 
    LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA tvivpc 
      ON tvivpc.ID_ZIG_ITEM_VENDIDO = tivd.PRODUCT_ID
      AND tvivpc.ID_CASA = tivd.FK_CASA
    GROUP BY tivd.FK_CASA, tvivpc.ID_ZIG_ITEM_VENDIDO, DATE(tivd.EVENT_DATE)
  ''')


############################### CMV ###################################

@st.cache_data
def GET_FATURAM_ZIG_ALIM_BEB_MENSAL(data_inicio, data_fim):
  return dataframe_query(f'''
  SELECT
    te.ID AS ID_Loja,
    te.NOME_FANTASIA AS Loja,
    tivc2.DESCRICAO AS Categoria,
    CASE 
      WHEN te.ID IN (103, 112, 118, 139) THEN 1
      ELSE 0 
    END AS Delivery,
    cast(date_format(cast(tivd.EVENT_DATE AS date), '%Y-%m-01') AS date) AS Primeiro_Dia_Mes,
    concat(year(cast(tivd.EVENT_DATE AS date)), '-', month(cast(tivd.EVENT_DATE AS date))) AS Ano_Mes,
    cast(tivd.EVENT_DATE AS date) AS Data_Evento,
    SUM((tivd.VALOR_UNITARIO  * tivd.QUANTIDADE)) AS Valor_Bruto,
    SUM(tivd.DESCONTO) AS Desconto,
    SUM((tivd.VALOR_UNITARIO * tivd.QUANTIDADE) - tivd.DESCONTO) AS Valor_Liquido
  FROM T_ITENS_VENDIDOS_DIA tivd
  LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tivd.PRODUCT_ID = tivc.ID_ZIGPAY
  LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
  LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
  LEFT JOIN T_EMPRESAS te ON tivd.LOJA_ID = te.ID_ZIGPAY
  WHERE cast(tivd.EVENT_DATE AS date) >= '{data_inicio}'
    AND cast(tivd.EVENT_DATE AS date) <= '{data_fim}'
    AND tivc2.DESCRICAO IN ('Alimentos', 'Bebidas')
  GROUP BY 
    ID_Loja,
    Categoria,
    Primeiro_Dia_Mes;
''')

def GET_VALORACAO_ESTOQUE(loja, data_contagem):
  return dataframe_query(f'''
  SELECT 
  	te.ID AS 'ID_Loja',
  	te.NOME_FANTASIA AS 'Loja',
  	tin5.ID AS 'ID_Insumo',
  	REPLACE(tin5.DESCRICAO, ',', '.') AS 'Insumo',
  	tci.QUANTIDADE_INSUMO AS 'Quantidade',
  	tin5.FK_INSUMOS_NIVEL_4 AS 'ID_Nivel_4',
  	tudm.UNIDADE_MEDIDA_NAME AS 'Unidade_Medida',
    tin.DESCRICAO AS 'Categoria',
  	tve.VALOR_EM_ESTOQUE AS 'Valor_em_Estoque',
  	tci.DATA_CONTAGEM
  FROM T_VALORACAO_ESTOQUE tve 
  LEFT JOIN T_CONTAGEM_INSUMOS tci ON tve.FK_CONTAGEM = tci.ID 
  LEFT JOIN T_EMPRESAS te ON tci.FK_EMPRESA = te.ID 
  LEFT JOIN T_INSUMOS_NIVEL_5 tin5 ON tci.FK_INSUMO = tin5.ID
  LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON tin5.FK_INSUMOS_NIVEL_4 = tin4.ID 
  LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON tin4.FK_INSUMOS_NIVEL_3 = tin3.ID 
  LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON tin3.FK_INSUMOS_NIVEL_2 = tin2.ID
  LEFT JOIN T_INSUMOS_NIVEL_1 tin ON tin2.FK_INSUMOS_NIVEL_1 = tin.ID
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON tin5.FK_UNIDADE_MEDIDA = tudm.ID
  WHERE tci.QUANTIDADE_INSUMO != 0
    AND tci.DATA_CONTAGEM = '{data_contagem}'
    AND te.NOME_FANTASIA = '{loja}'
  ORDER BY DATA_CONTAGEM DESC
  ''')



@st.cache_data
def GET_EVENTOS_CMV(data_inicio, data_fim):
  return dataframe_query(f'''
  SELECT 
    te.ID AS 'ID_Loja',
   	te.NOME_FANTASIA AS 'Loja',
   	SUM(tec.VALOR_EVENTOS_A_B) AS 'Valor',
   	tec.DATA AS 'Data',
    cast(date_format(cast(tec.DATA AS date), '%Y-%m-01') AS date) AS 'Primeiro_Dia_Mes'
  FROM T_EVENTOS_CMV tec 
  LEFT JOIN T_EMPRESAS te ON tec.FK_EMPRESA = te.ID 
  WHERE tec.DATA BETWEEN '{data_inicio}' AND '{data_fim}'
  GROUP BY te.ID
  ''')


@st.cache_data
def GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_SEM_PEDIDO():
  return dataframe_query(f'''
    WITH subquery AS (
    SELECT
      tdr.ID AS tdr_ID,
      te.ID AS ID_Loja,
      te.NOME_FANTASIA AS Loja,
      CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE), '%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes,
      tdr.VALOR_PAGAMENTO AS Valor,
      tccg2.DESCRICAO AS Class_Cont_Grupo_2
    FROM
      T_DESPESA_RAPIDA tdr
    JOIN T_EMPRESAS te ON tdr.FK_LOJA = te.ID
    LEFT JOIN T_FORNECEDOR tf ON tdr.FK_FORNECEDOR = tf.ID
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID
    LEFT JOIN T_ASSOCIATIVA_PLANO_DE_CONTAS tapdc ON tccg2.ID = tapdc.FK_CLASSIFICACAO_GRUPO_2
    LEFT JOIN T_DESPESA_STATUS tds ON tdr.ID = tds.FK_DESPESA_RAPIDA
    LEFT JOIN T_STATUS ts ON tds.FK_STATUS_NAME = ts.ID
    LEFT JOIN T_STATUS_PAGAMENTO tsp2 ON ts.FK_STATUS_PAGAMENTO = tsp2.ID
    WHERE
      tdr.FK_DESPESA_TEKNISA IS NULL
      AND tccg.ID IN (162, 205, 236)
      AND NOT EXISTS (
        SELECT 1
        FROM T_DESPESA_RAPIDA_ITEM tdri
        WHERE tdri.FK_DESPESA_RAPIDA = tdr.ID
      )
    GROUP BY
      tdr.ID,
      te.ID,
      tccg2.DESCRICAO,
      CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE), '%Y-%m-01') AS DATE)
  )
  SELECT
    ID_Loja,
    Loja,
    Primeiro_Dia_Mes,
    SUM(Valor) AS BlueMe_Sem_Pedido_Valor,
    SUM(CASE
      WHEN Class_Cont_Grupo_2 IN ('ALIMENTOS', 'Insumos - Alimentos') THEN Valor
      ELSE 0
    END) AS BlueMe_Sem_Pedido_Alimentos,
    SUM(CASE
      WHEN Class_Cont_Grupo_2 IN ('BEBIDAS', 'Insumos - Bebidas') THEN Valor
      ELSE 0
    END) AS BlueMe_Sem_Pedido_Bebidas,
    SUM(CASE
      WHEN Class_Cont_Grupo_2 IN ('EMBALAGENS', 'Insumos - Embalagens') THEN Valor
      ELSE 0
      END) AS BlueMe_Sem_Pedido_Descart_Hig_Limp,
    SUM(CASE
      WHEN Class_Cont_Grupo_2 NOT IN ('ALIMENTOS', 'Insumos - Alimentos', 'BEBIDAS', 'Insumos - Bebidas', 'EMBALAGENS', 'Insumos - Embalagens') THEN Valor
      ELSE 0
      END) AS BlueMe_Sem_Pedido_Outros
  FROM subquery
  GROUP BY
    ID_Loja,
    Primeiro_Dia_Mes
  ORDER BY
    ID_Loja,
    Primeiro_Dia_Mes;
''')


@st.cache_data
def GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_COM_PEDIDO():
  return dataframe_query(f'''
  select
    vibmcp.ID_Loja AS ID_Loja,
    vibmcp.Loja AS Loja,
    vibmcp.Primeiro_Dia_Mes AS Primeiro_Dia_Mes,
    sum(vibmcp.Valor_Liquido) AS BlueMe_Com_Pedido_Valor_Liquido,
    sum(vibmcp.Valor_Insumos) AS BlueMe_Com_Pedido_Valor_Insumos,
    sum(vibmcp.Valor_Liq_Alimentos) AS BlueMe_Com_Pedido_Valor_Liq_Alimentos,
    sum(vibmcp.Valor_Liq_Bebidas) AS BlueMe_Com_Pedido_Valor_Liq_Bebidas,
    sum(vibmcp.Valor_Liq_Descart_Hig_Limp) AS BlueMe_Com_Pedido_Valor_Liq_Descart_Hig_Limp,
    sum(vibmcp.Valor_Liq_Outros) AS BlueMe_Com_Pedido_Valor_Liq_Outros
  from
    View_Insumos_BlueMe_Com_Pedido vibmcp
  group by
    vibmcp.ID_Loja,
    vibmcp.Primeiro_Dia_Mes
  order by
    vibmcp.ID_Loja,
    vibmcp.Primeiro_Dia_Mes;
''')



@st.cache_data
def GET_TRANSF_ESTOQUE():
  return dataframe_query(f'''
  SELECT
    tti.ID as 'ID_Transferencia',
    te.ID as 'ID_Loja_Saida',
    te.NOME_FANTASIA as 'Casa_Saida',
    te2.ID as 'ID_Loja_Entrada',
    te2.NOME_FANTASIA as 'Casa_Entrada',
    tti.DATA_TRANSFERENCIA as 'Data_Transferencia',
    tin5.ID as 'ID_Insumo_Nivel_5',
    tin5.DESCRICAO as 'Insumo_Nivel_5',
    tin.DESCRICAO as 'Categoria',
    tti.QUANTIDADE as 'Quantidade',
    tudm.UNIDADE_MEDIDA_NAME as 'Unidade_Medida',
    tti.VALOR_TRANSFERENCIA as 'Valor_Transferencia',
    tti.OBSERVACAO as 'Observacao'
  FROM T_TRANSFERENCIAS_INSUMOS tti 
    LEFT JOIN T_EMPRESAS te ON (tti.FK_EMRPESA_SAIDA = te.ID)
    LEFT JOIN T_EMPRESAS te2 ON tti.FK_EMPRESA_ENTRADA = te2.ID
    LEFT JOIN T_INSUMOS_NIVEL_5 tin5 ON tti.FK_INSUMO_NIVEL_5 = tin5.ID
    LEFT JOIN T_INSUMOS_NIVEL_4 tin4 ON tin5.FK_INSUMOS_NIVEL_4 = tin4.ID 
    LEFT JOIN T_INSUMOS_NIVEL_3 tin3 ON tin4.FK_INSUMOS_NIVEL_3 = tin3.ID 
    LEFT JOIN T_INSUMOS_NIVEL_2 tin2 ON tin3.FK_INSUMOS_NIVEL_2 = tin2.ID 
    LEFT JOIN T_INSUMOS_NIVEL_1 tin ON tin2.FK_INSUMOS_NIVEL_1 = tin.id
    LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tin5.FK_UNIDADE_MEDIDA = tudm.ID)
  ORDER BY tti.ID DESC
''')


@st.cache_data
def GET_PERDAS_E_CONSUMO_AGRUPADOS():
  return dataframe_query(f'''
  WITH vpec AS (
    SELECT
      tpecc.ID AS Perdas_ID,
      tl.ID AS ID_Loja,
      tl.NOME_FANTASIA AS Loja,
      tpecc.DATA_BAIXA AS Data_Baixa,        
      CASE
        WHEN tpecc.FK_MOTIVO = 106 THEN tpecc.VALOR
        ELSE 0
      END AS Consumo_Interno,
      CASE
        WHEN tpecc.FK_MOTIVO <> 106 THEN tpecc.VALOR
        ELSE 0
      END AS Quebras_e_Perdas,
      CAST(DATE_FORMAT(CAST(tpecc.DATA_BAIXA AS DATE), '%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes
    FROM
      T_PERDAS_E_CONSUMO_CONSOLIDADOS tpecc
    JOIN T_EMPRESAS tl ON tpecc.FK_EMPRESA = tl.ID
  )
  SELECT
    vpec.ID_Loja,
    vpec.Loja,
    vpec.Primeiro_Dia_Mes,
    SUM(vpec.Consumo_Interno) AS Consumo_Interno,
    SUM(vpec.Quebras_e_Perdas) AS Quebras_e_Perdas
  FROM vpec
  GROUP BY
    vpec.ID_Loja,
    vpec.Primeiro_Dia_Mes
  ORDER BY
    vpec.ID_Loja,
    vpec.Primeiro_Dia_Mes;
''')

  

@st.cache_data
def GET_INSUMOS_BLUE_ME_COM_PEDIDO():
  return dataframe_query(f'''
  SELECT
    vbmcp.tdr_ID AS tdr_ID,
    vbmcp.ID_Loja AS ID_Loja,
    vbmcp.Loja AS Loja,
    vbmcp.Fornecedor AS Fornecedor,
    vbmcp.Doc_Serie AS Doc_Serie,
    vbmcp.Data_Emissao AS Data_Emissao,
    vbmcp.Valor_Liquido AS Valor_Liquido,
    vbmcp.Valor_Insumos AS Valor_Cotacao,
    CAST(DATE_FORMAT(CAST(vbmcp.Data_Emissao AS DATE), '%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes,
    ROUND((vbmcp.Valor_Liquido * (virapc.Valor_Alimentos / virapc.Valor_Total_Insumos)), 2) AS Valor_Liq_Alimentos,
    ROUND((vbmcp.Valor_Liquido * (virapc.Valor_Bebidas / virapc.Valor_Total_Insumos)), 2) AS Valor_Liq_Bebidas,
    ROUND((vbmcp.Valor_Liquido * (virapc.Valor_Descartaveis_Higiene_Limpeza / virapc.Valor_Total_Insumos)), 2) AS Valor_Liq_Descart_Hig_Limp,
    ROUND((vbmcp.Valor_Liquido * (virapc.Valor_Gelo_Gas_Carvao_Velas / virapc.Valor_Total_Insumos)), 2) AS Valor_Gelo_Gas_Carvao_Velas,
    ROUND((vbmcp.Valor_Liquido * (virapc.Valor_Utensilios / virapc.Valor_Total_Insumos)), 2) AS Valor_Utensilios,
    ROUND((vbmcp.Valor_Liquido * (virapc.Valor_Outros / virapc.Valor_Total_Insumos)), 2) AS Valor_Liq_Outros
  FROM
    View_BlueMe_Com_Pedido vbmcp
  LEFT JOIN View_Insumos_Receb_Agrup_Por_Categ virapc ON
    vbmcp.tdr_ID = virapc.tdr_ID
''')


 

@st.cache_data
def GET_INSUMOS_BLUE_ME_SEM_PEDIDO():
  return dataframe_query(f'''
  SELECT
    subquery.tdr_ID AS tdr_ID,
    subquery.ID_Loja AS ID_Loja,
    subquery.Loja AS Loja,
    subquery.Fornecedor AS Fornecedor,
    subquery.Doc_Serie AS Doc_Serie,
    subquery.Data_Emissao AS Data_Emissao,
    subquery.Valor AS Valor,
    subquery.Plano_de_Contas AS Plano_de_Contas,
    subquery.Primeiro_Dia_Mes AS Primeiro_Dia_Mes
  FROM
    (
    SELECT
      tdr.ID AS tdr_ID,
      te.ID AS ID_Loja,
      te.NOME_FANTASIA AS Loja,
      tf.CORPORATE_NAME AS Fornecedor,
      tdr.NF AS Doc_Serie,
      tdr.COMPETENCIA AS Data_Emissao,
      tdr.VENCIMENTO AS Data_Vencimento,
      tccg2.DESCRICAO AS Class_Cont_Grupo_2,
      tccg.DESCRICAO AS Class_Cont_Grupo_1,
      tdr.OBSERVACAO AS Observacao,
      tdr.VALOR_PAGAMENTO AS Valor,
      tccg2.DESCRICAO AS Plano_de_Contas,
      tsp2.DESCRICAO AS Status,
      CAST(DATE_FORMAT(CAST(tdr.COMPETENCIA AS DATE), '%Y-%m-01') AS DATE) AS Primeiro_Dia_Mes,
      ROW_NUMBER() OVER (PARTITION BY tdr.ID
      ORDER BY
        tds.ID DESC) AS row_num
    FROM
      T_DESPESA_RAPIDA tdr
    JOIN T_EMPRESAS te ON tdr.FK_LOJA = te.ID
    LEFT JOIN T_FORMAS_DE_PAGAMENTO tfdp ON tdr.FK_FORMA_PAGAMENTO = tfdp.ID
    LEFT JOIN T_FORNECEDOR tf ON tdr.FK_FORNECEDOR = tf.ID
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID
    LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2.ID
    LEFT JOIN T_STATUS_CONFERENCIA_DOCUMENTACAO tscd ON tdr.FK_CONFERENCIA_DOCUMENTACAO = tscd.ID
    LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON tdr.FK_APROVACAO_DIRETORIA = tsad.ID
    LEFT JOIN T_STATUS_APROVACAO_CAIXA tsac ON tdr.FK_APROVACAO_CAIXA = tsac.ID
    LEFT JOIN T_STATUS_PAGAMENTO tsp ON tdr.FK_STATUS_PGTO = tsp.ID
    LEFT JOIN T_CALENDARIO tc ON tdr.PREVISAO_PAGAMENTO = tc.ID
    LEFT JOIN T_CALENDARIO tc2 ON tdr.FK_DATA_REALIZACAO_PGTO = tc2.ID
    LEFT JOIN T_TEKNISA_CONTAS_A_PAGAR ttcap ON tdr.FK_DESPESA_TEKNISA = ttcap.ID
    LEFT JOIN T_DESPESA_RAPIDA_ITEM tdri ON tdr.ID = tdri.FK_DESPESA_RAPIDA
    LEFT JOIN T_DESPESA_STATUS tds ON tdr.ID = tds.FK_DESPESA_RAPIDA
    LEFT JOIN T_STATUS ts ON tds.FK_STATUS_NAME = ts.ID
    LEFT JOIN T_STATUS_PAGAMENTO tsp2 ON ts.FK_STATUS_PAGAMENTO = tsp2.ID
    WHERE
      tdri.ID IS NULL
      AND tdr.FK_DESPESA_TEKNISA IS NULL
      AND tccg.ID IN (162, 205, 236)
    ) subquery
  WHERE
    subquery.row_num = 1;
''')



def GET_VALORACAO_PRODUCAO(data):
  return dataframe_query(f'''
  SELECT
    te.ID as 'ID_Loja',
    te.NOME_FANTASIA as 'Loja',
    tipc.DATA_CONTAGEM as 'Data_Contagem',
    DATE_FORMAT(DATE_SUB(tipc.DATA_CONTAGEM, INTERVAL 1 MONTH), '%m/%Y') AS 'Mes_Texto',
    tip.NOME_ITEM_PRODUZIDO as 'Item_Produzido',
    tudm.UNIDADE_MEDIDA_NAME as 'Unidade_Medida',
    tipc.QUANTIDADE_INSUMO as 'Quantidade',
    tin.DESCRICAO as 'Categoria',
    tipv.VALOR as 'Valor_Unidade_Medida',
    ROUND(tipc.QUANTIDADE_INSUMO * tipv.VALOR, 2) as 'Valor_Total'
  FROM T_ITENS_PRODUCAO_CONTAGEM tipc
  LEFT JOIN T_ITENS_PRODUCAO_VALORACAO tipv ON (tipc.FK_ITEM_PRODUZIDO = tipv.FK_ITEM_PRODUZIDO) AND (DATE_FORMAT(tipc.DATA_CONTAGEM, '%m/%Y') = DATE_FORMAT(tipv.DATA_VALORACAO, '%m/%Y'))
  LEFT JOIN T_ITENS_PRODUCAO tip ON (tipv.FK_ITEM_PRODUZIDO = tip.ID)
  LEFT JOIN T_EMPRESAS te ON (tip.FK_EMPRESA = te.ID)
  LEFT JOIN T_INSUMOS_NIVEL_1 tin ON (tip.FK_INSUMO_NIVEL_1 = tin.ID)
  LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (tip.FK_UNIDADE_MEDIDA = tudm.ID)
  WHERE tipc.DATA_CONTAGEM = '{data}'
  ''')