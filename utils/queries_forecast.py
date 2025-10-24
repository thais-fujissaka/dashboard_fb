import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query
from utils.constants.general_constants import casas_validas


# Garante que as casas estão corretamente formatadas no SQL
casas_validas = [c for c in casas_validas if c != 'All bar']
casas_str = "', '".join(casas_validas)  # vira: "Bar Brahma - Centro', 'Orfeu"
casas_str = f"'{casas_str}'"  # adiciona aspas ao redor da lista toda


# Faturamento da Zig por dia: alimentos, bebidas, delivery, couvert, etc
@st.cache_data
def GET_FATURAMENTO_AGREGADO_DIA():
    df_faturamento_agregado_diario = dataframe_query(f''' 
    SELECT
        CASE
            WHEN te.ID IN (161, 162) THEN 149
            ELSE te.ID    
        END AS ID_Casa,                                                                                                                      
        CASE
            WHEN te.NOME_FANTASIA IN ('Abaru - Priceless', 'Notiê - Priceless') THEN 'Priceless'
            ELSE te.NOME_FANTASIA    
        END AS Casa,  
        CASE 
            WHEN te.ID IN (103, 112, 118, 139, 169) THEN 'Delivery'
            ELSE tivc2.DESCRICAO 
        END AS Categoria,
        cast(tiv.EVENT_DATE as date) AS Data_Evento,
        SUM((tiv.UNIT_VALUE * tiv.COUNT)) AS Valor_Bruto,
        SUM(tiv.DISCOUNT_VALUE) AS Desconto,
        SUM((tiv.UNIT_VALUE * tiv.COUNT) - tiv.DISCOUNT_VALUE) AS Valor_Liquido
    FROM T_ITENS_VENDIDOS tiv
    LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tiv.PRODUCT_ID = tivc.ID_ZIGPAY
    LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
    LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
    LEFT JOIN T_EMPRESAS te ON tiv.LOJA_ID = te.ID_ZIGPAY
    WHERE 
        YEAR(tiv.EVENT_DATE) > 2024 AND 
        (te.NOME_FANTASIA IN ({casas_str}) OR 
        te.NOME_FANTASIA LIKE '%Delivery%' OR
        te.NOME_FANTASIA LIKE '%Priceless%')
    GROUP BY 
        ID_Casa,
        Casa,
        Categoria,
        Data_Evento
    ''')

    # Mapeamento do Delivery
    mapeamento = {
    'Delivery Bar Leo Centro': ('Bar Léo - Centro', 116),
    'Delivery Orfeu': ('Orfeu', 104),
    'Delivery Fabrica de Bares': ('Bar Brahma - Centro', 114),
    'Delivery Brahma Granja Viana': ('Bar Brahma - Granja', 148),
    'Delivery Jacaré': ('Jacaré', 105)
    }

    for nome_antigo, (novo_nome, novo_id) in mapeamento.items():
        mask = df_faturamento_agregado_diario['Casa'] == nome_antigo
        df_faturamento_agregado_diario.loc[mask, ['Casa', 'ID_Casa']] = [novo_nome, novo_id]
    
    return df_faturamento_agregado_diario


# Faturamento de Eventos: Eventos A&B, Locações, Couvert
@st.cache_data
def GET_FATURAMENTO_EVENTOS():
    df_faturamento_eventos = dataframe_query(f'''
    SELECT 
        te.ID AS ID_Casa,
        te.NOME_FANTASIA AS Casa,
        tep.DATA_EVENTO AS Data_Evento,
        tep.VALOR_AB AS Valor_AB,
        tep.VALOR_LOCACAO_AROO_1 AS VALOR_LOCACAO_AROO_1,
        tep.VALOR_LOCACAO_AROO_2 AS VALOR_LOCACAO_AROO_2,
        tep.VALOR_LOCACAO_AROO_3 AS VALOR_LOCACAO_AROO_3,          
        tep.VALOR_LOCACAO_ANEXO AS VALOR_LOCACAO_ANEXO,
        tep.VALOR_LOCACAO_NOTIE AS VALOR_LOCACAO_NOTIE, 
        tep.VALOR_LOCACAO_MIRANTE AS VALOR_LOCACAO_MIRANTE, 
        tep.VALOR_LOCACAO_GERADOR AS VALOR_LOCACAO_GERADOR,          
        tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS VALOR_LOCACAO_DECORACAO_MOBILIARIO,          
        tep.VALOR_LOCACAO_UTENSILIOS AS VALOR_LOCACAO_UTENSILIOS,   
        tep.VALOR_LOCACAO_ESPACO AS VALOR_LOCACAO_ESPACO,
        tep.VALOR_CONTRATACAO_ARTISTICO AS Couvert                                                                                                                                                                                                                            
    FROM T_EVENTOS_PRICELESS AS tep
    LEFT JOIN T_EMPRESAS AS te ON (tep.FK_EMPRESA = te.ID)  
    ORDER BY tep.DATA_EVENTO                                                                           
    '''
    )

    # Define quais colunas serão "mantidas"
    id_vars = ['ID_Casa', 'Casa', 'Data_Evento']

    # Define quais colunas serão transformadas em categorias
    value_vars = ['Valor_AB', 'VALOR_LOCACAO_AROO_1', 'VALOR_LOCACAO_AROO_2',
                'VALOR_LOCACAO_AROO_3', 'VALOR_LOCACAO_ANEXO',
                'VALOR_LOCACAO_NOTIE', 'VALOR_LOCACAO_MIRANTE',
                'VALOR_LOCACAO_GERADOR', 'VALOR_LOCACAO_DECORACAO_MOBILIARIO',
                'VALOR_LOCACAO_UTENSILIOS', 'VALOR_LOCACAO_ESPACO', 'Couvert']

    # Faz o melt
    df_eventos_melt = df_faturamento_eventos.melt(
        id_vars=id_vars,
        value_vars=value_vars,
        var_name='Categoria',
        value_name='Valor_Bruto'
    )

    # Remove linhas sem valor
    df_eventos_melt = df_eventos_melt.dropna(subset=['Valor_Bruto'])

    # Simplifica nomes de categoria
    df_eventos_melt['Categoria'] = df_eventos_melt['Categoria'].replace({
        'Valor_AB': 'Eventos A&B',
        'VALOR_LOCACAO_AROO_1': 'Eventos Locações',
        'VALOR_LOCACAO_AROO_2': 'Eventos Locações',
        'VALOR_LOCACAO_AROO_3': 'Eventos Locações',
        'VALOR_LOCACAO_ANEXO': 'Eventos Locações',
        'VALOR_LOCACAO_NOTIE': 'Eventos Locações',
        'VALOR_LOCACAO_MIRANTE': 'Eventos Locações',
        'VALOR_LOCACAO_GERADOR': 'Eventos Locações',
        'VALOR_LOCACAO_DECORACAO_MOBILIARIO': 'Eventos Locações',
        'VALOR_LOCACAO_UTENSILIOS': 'Eventos Locações',
        'VALOR_LOCACAO_ESPACO': 'Eventos Locações',
        'Couvert': 'Eventos Couvert'
    })

    # Agrupa somando o valor total por categoria por data
    df_eventos_final = (
        df_eventos_melt
        .groupby(['ID_Casa', 'Casa', 'Data_Evento', 'Categoria'], as_index=False)
        .agg({'Valor_Bruto': 'sum'})
    )

    df_eventos_final['Desconto'] = 0
    df_eventos_final['Valor_Liquido'] = df_eventos_final['Valor_Bruto']
    df_eventos_final = df_eventos_final[['ID_Casa', 'Casa', 'Categoria', 'Data_Evento', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]
    return df_eventos_final


# Receitas Extraordinárias: 'Outras receitas'
@st.cache_data
def GET_PARCELAS_RECEIT_EXTR():
    df_parc_receit_extr = dataframe_query(f'''
        SELECT 
        te.ID as 'ID_Casa',
        te.NOME_FANTASIA as 'Casa',
        tre.DATA_OCORRENCIA as 'Data_Ocorrencia',
        vpa.VALOR_PARCELA as 'Valor_Parcela',
        trec2.CLASSIFICACAO as 'Categoria'
        FROM View_Parcelas_Agrupadas vpa
        INNER JOIN T_EMPRESAS te ON (vpa.FK_EMPRESA = te.ID)
        LEFT JOIN T_RECEITAS_EXTRAORDINARIAS tre ON (vpa.ID = tre.ID)
        LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLASSIFICACAO trec2 ON (tre.FK_CLASSIFICACAO = trec2.ID)
        WHERE YEAR(tre.DATA_OCORRENCIA) > 2024 AND trec2.CLASSIFICACAO != 'Eventos' AND te.NOME_FANTASIA IN ({casas_str})
        ORDER BY te.NOME_FANTASIA ASC, tre.DATA_OCORRENCIA
        ''')
    
    df_parc_receit_extr = df_parc_receit_extr.groupby(['ID_Casa', 'Casa', 'Data_Ocorrencia', 'Categoria'], as_index=False)['Valor_Parcela'].sum()

    # Agrupa por casa e dia (soma todas as categorias)
    df_parc_receit_extr_dia = df_parc_receit_extr.groupby(['ID_Casa', 'Casa', 'Data_Ocorrencia'], as_index=False)['Valor_Parcela'].sum()
    df_parc_receit_extr_dia['Categoria'] = 'Outras Receitas'

    # Adequa para poder concatenar ao faturamento agregado
    df_parc_receit_extr_dia = df_parc_receit_extr_dia.rename(columns={
        'Data_Ocorrencia':'Data_Evento',
        'Valor_Parcela':'Valor_Bruto'
    })

    df_parc_receit_extr_dia['Desconto'] = 0
    df_parc_receit_extr_dia['Valor_Liquido'] = df_parc_receit_extr_dia['Valor_Bruto']

    df_parc_receit_extr_dia = df_parc_receit_extr_dia[['ID_Casa', 'Casa', 'Categoria', 'Data_Evento', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]

    return df_parc_receit_extr, df_parc_receit_extr_dia


# Concatena todos os tipos de faturamento
@st.cache_data
def GET_TODOS_FATURAMENTOS_DIA():
    faturamento_agregado_diario = GET_FATURAMENTO_AGREGADO_DIA()
    faturamento_eventos = GET_FATURAMENTO_EVENTOS()
    parc_receitas_extr, parc_receitas_extr_dia = GET_PARCELAS_RECEIT_EXTR() # parcelas com categorias específicas e parcelas agrupadas como 'Outras Receitas'
    todos_faturamentos = pd.concat([faturamento_agregado_diario, faturamento_eventos, parc_receitas_extr_dia])
    return todos_faturamentos, faturamento_eventos, parc_receitas_extr, parc_receitas_extr_dia


# Orçamentos mensais
@st.cache_data
def GET_ORCAMENTOS():
    df_orcamentos =  dataframe_query(f'''
    SELECT
        te.ID AS ID_Casa,
        te.NOME_FANTASIA AS Casa,
        to2.ANO AS 'Ano',
        to2.MES AS 'Mes',
        to2.VALOR AS Orcamento_Faturamento,
        CASE
        WHEN tccg.DESCRICAO IN ('VENDA DE ALIMENTO', 'Alimentação') THEN 'Alimentos'
        WHEN tccg.DESCRICAO IN ('VENDA DE BEBIDAS', 'Bebida') THEN 'Bebidas'
        WHEN tccg.DESCRICAO IN ('VENDA DE COUVERT/ SHOWS', 'Artístico (couvert/shows)') THEN 'Couvert'
        WHEN tccg.DESCRICAO IN ('DELIVERY', 'Delivery') THEN 'Delivery'
        WHEN tccg.DESCRICAO IN ('GIFTS', 'Gifts') THEN 'Gifts'
        ELSE tccg.DESCRICAO
        END AS Categoria
    FROM
        T_ORCAMENTOS to2
    JOIN
        T_EMPRESAS te ON to2.FK_EMPRESA = te.ID
    JOIN
        T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg ON to2.FK_CLASSIFICACAO_2 = tccg.ID
    WHERE
        to2.FK_CLASSIFICACAO_1 IN (178, 245)
        -- tccg.DESCRICAO NOT IN ('SERVICO', 'Serviço', 'Eventos Rebate Fornecedores')                             
    ORDER BY
        ID_Casa,
        MES,
        ANO;
    ''')
    return df_orcamentos


# @st.cache_data
# def GET_FATURAMENTO_AGREGADO_MES():
#     df_faturamento_agregado_mensal = dataframe_query(f'''
#         WITH empresas_normalizadas AS (
#             SELECT
#             ID             AS original_id,
#             CASE 
#                 WHEN ID IN (161, 162) THEN 149 
#                 ELSE ID 
#             END            AS id_casa_normalizada
#             FROM T_EMPRESAS
#         )
#         SELECT
#             en.id_casa_normalizada     AS ID_Casa,
#             te2.NOME_FANTASIA          AS Casa,
#             CASE 
#                 WHEN en.id_casa_normalizada IN (103, 112, 118, 139, 169) THEN 'Delivery'
#                 ELSE tivc.DESCRICAO 
#             END AS Categoria,                                  
#             -- tivc.DESCRICAO             AS Categoria,
#             tfa.ANO                    AS Ano,
#             tfa.MES                    AS Mes,
#             tfa.VALOR_BRUTO            AS Valor_Bruto,
#             tfa.DESCONTO               AS Desconto,
#             tfa.VALOR_LIQUIDO          AS Valor_Liquido
#         FROM T_FATURAMENTO_AGREGADO tfa
#         -- primeiro, linka ao CTE para saber a casa “normalizada”
#         LEFT JOIN empresas_normalizadas en
#             ON tfa.FK_EMPRESA = en.original_id
#         -- depois, puxa o nome da casa já normalizada
#         LEFT JOIN T_EMPRESAS te2
#             ON en.id_casa_normalizada = te2.ID
#         LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc
#             ON tfa.FK_CATEGORIA = tivc.ID  
#         WHERE 
#             te2.NOME_FANTASIA IN ({casas_str}) OR 
#             te2.NOME_FANTASIA LIKE '%Delivery%'
#     ''')

#     # Mapeamento do Delivery
#     mapeamento = {
#     'Delivery Bar Leo Centro': ('Bar Léo - Centro', 116),
#     'Delivery Orfeu': ('Orfeu', 104),
#     'Delivery Fabrica de Bares': ('Bar Brahma - Centro', 114),
#     'Delivery Brahma Granja Viana': ('Bar Brahma - Granja', 148),
#     'Delivery Jacaré': ('Jacaré', 105)
#     }

#     for nome_antigo, (novo_nome, novo_id) in mapeamento.items():
#         mask = df_faturamento_agregado_mensal['Casa'] == nome_antigo
#         df_faturamento_agregado_mensal.loc[mask, ['Casa', 'ID_Casa']] = [novo_nome, novo_id]

#     return df_faturamento_agregado_mensal


# Para eventos e receitas extraordinárias mensais
@st.cache_data
def GET_FATURAMENTO_CATEGORIA_MENSAL(df_faturamento_categoria):
    df_faturamento_categoria_mensal = df_faturamento_categoria.copy() # Utiliza o mesmo df que já foi carregado na outra tab

    # Zera a hora
    df_faturamento_categoria_mensal['Data_Evento'] = pd.to_datetime(df_faturamento_categoria_mensal['Data_Evento'], errors='coerce').dt.normalize()
    df_faturamento_categoria_mensal['Ano'] = df_faturamento_categoria_mensal['Data_Evento'].dt.year
    df_faturamento_categoria_mensal['Mes'] = df_faturamento_categoria_mensal['Data_Evento'].dt.month
    df_faturamento_categoria_mensal = df_faturamento_categoria_mensal[df_faturamento_categoria_mensal['Ano'] > 2024]
    
    # Agrupa para ter os valores por mês
    df_faturamento_categoria_mensal = df_faturamento_categoria_mensal.groupby(['ID_Casa', 'Casa', 'Categoria', 'Ano', 'Mes'], as_index=False)[['Valor_Bruto', 'Desconto', 'Valor_Liquido']].sum()

    return df_faturamento_categoria_mensal


@st.cache_data
def GET_TODOS_FATURAMENTOS_MENSAL(df_faturamento_agregado_dia, df_faturamento_eventos, df_parc_receit_extr_dia):
    df_faturamento_agregado_mensal = GET_FATURAMENTO_CATEGORIA_MENSAL(df_faturamento_agregado_dia)
    df_faturamento_eventos_mensal = GET_FATURAMENTO_CATEGORIA_MENSAL(df_faturamento_eventos)
    df_faturamento_receit_extr_mensal = GET_FATURAMENTO_CATEGORIA_MENSAL(df_parc_receit_extr_dia)
    df_todos_faturamentos_mensal = pd.concat([df_faturamento_agregado_mensal, df_faturamento_eventos_mensal, df_faturamento_receit_extr_mensal])
    return df_faturamento_agregado_mensal, df_todos_faturamentos_mensal


######################################## CMV ########################################
@st.cache_data
def GET_VALORACAO_ESTOQUE(data_inicio, data_fim):
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
    AND tci.DATA_CONTAGEM >= '{data_inicio}'
    AND tci.DATA_CONTAGEM <= '{data_fim}'
  ORDER BY DATA_CONTAGEM DESC
  ''')


@st.cache_data
def GET_VALORACAO_PRODUCAO(data_inicio, data_fim):
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
        WHERE tipc.DATA_CONTAGEM >= '{data_inicio}'
        AND tipc.DATA_CONTAGEM <= '{data_fim}'
    ''')


@st.cache_data
def GET_EVENTOS_CMV(data_inicio, data_fim):
    return dataframe_query(f'''
        SELECT 
            te.ID AS 'ID_Loja',
            te.NOME_FANTASIA AS 'Loja',
            tec.VALOR_EVENTOS_A_B AS 'Valor_AB',
            tec.DATA AS 'Data',
            cast(date_format(cast(tec.DATA AS date), '%Y-%m-01') AS date) AS 'Primeiro_Dia_Mes'
        FROM T_EVENTOS_CMV tec 
        LEFT JOIN T_EMPRESAS te ON tec.FK_EMPRESA = te.ID 
        WHERE tec.DATA BETWEEN '{data_inicio}' AND '{data_fim}'
    ''')