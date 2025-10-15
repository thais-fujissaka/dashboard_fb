import streamlit as st
import pandas as pd
from utils.functions.general_functions import dataframe_query


@st.cache_data
def GET_FATURAMENTO_AGREGADO(casas_validas):
    # Garante que as casas estão corretamente formatadas no SQL
    casas_validas = [c for c in casas_validas if c != 'All bar']
    casas_str = "', '".join(casas_validas)  # vira: "Bar Brahma - Centro', 'Orfeu"
    casas_str = f"'{casas_str}'"  # adiciona aspas ao redor da lista toda

    df_faturamento_agregado = dataframe_query(f''' 
    SELECT
        te.ID AS ID_Casa,
        te.NOME_FANTASIA AS Casa,
        CASE 
            WHEN te.ID IN (103, 112, 118, 139, 169) THEN 'Delivery'
            ELSE tivc2.DESCRICAO 
        END AS Categoria,
        -- cast(date_format(cast(tiv.EVENT_DATE as date), '%Y-%m-01') as date) AS Primeiro_Dia_Mes,
        -- concat(year(cast(tiv.EVENT_DATE as date)), '-', month(cast(tiv.EVENT_DATE as date))) AS Ano_Mes,
        cast(tiv.EVENT_DATE as date) AS Data_Evento,
        SUM((tiv.UNIT_VALUE * tiv.COUNT)) AS Valor_Bruto,
        SUM(tiv.DISCOUNT_VALUE) AS Desconto,
        SUM((tiv.UNIT_VALUE * tiv.COUNT) - tiv.DISCOUNT_VALUE) AS Valor_Liquido
    FROM T_ITENS_VENDIDOS tiv
    LEFT JOIN T_ITENS_VENDIDOS_CADASTROS tivc ON tiv.PRODUCT_ID = tivc.ID_ZIGPAY
    LEFT JOIN T_ITENS_VENDIDOS_CATEGORIAS tivc2 ON tivc.FK_CATEGORIA = tivc2.ID
    LEFT JOIN T_ITENS_VENDIDOS_TIPOS tivt ON tivc.FK_TIPO = tivt.ID
    LEFT JOIN T_EMPRESAS te ON tiv.LOJA_ID = te.ID_ZIGPAY
    WHERE YEAR(tiv.EVENT_DATE) > 2024 AND te.NOME_FANTASIA IN ({casas_str}) OR te.NOME_FANTASIA LIKE '%Delivery%'
    GROUP BY 
        ID_Casa,
        Categoria,
        Data_Evento
    ''')

    mapeamento = {
    'Delivery Bar Leo Centro': ('Bar Léo - Centro', 116),
    'Delivery Orfeu': ('Orfeu', 104),
    'Delivery Fabrica de Bares': ('Bar Brahma - Centro', 114),
    'Delivery Brahma Granja Viana': ('Bar Brahma - Granja', 148),
    }

    for nome_antigo, (novo_nome, novo_id) in mapeamento.items():
        mask = df_faturamento_agregado['Casa'] == nome_antigo
        df_faturamento_agregado.loc[mask, ['Casa', 'ID_Casa']] = [novo_nome, novo_id]
    
    # df_faturamento_agregado_casa = df_faturamento_agregado[df_faturamento_agregado['ID_Casa'] == id_casa]

    return df_faturamento_agregado


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


@st.cache_data
def GET_PARCELAS_RECEIT_EXTR(casas_validas):
    # Garante que as casas estão corretamente formatadas no SQL
    casas_validas = [c for c in casas_validas if c != 'All bar']
    casas_str = "', '".join(casas_validas)  # vira: "Bar Brahma - Centro', 'Orfeu"
    casas_str = f"'{casas_str}'"  # adiciona aspas ao redor da lista toda

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


@st.cache_data
def GET_TODOS_FATURAMENTOS(casas_validas):
    faturamento_agregado = GET_FATURAMENTO_AGREGADO(casas_validas)
    faturamento_eventos = GET_FATURAMENTO_EVENTOS()
    parc_receitas_extr, parc_receitas_extr_dia = GET_PARCELAS_RECEIT_EXTR(casas_validas) # parcelas com categorias específicas e parcelas agrupadas como 'Outras Receitas'
    todos_faturamentos = pd.concat([faturamento_agregado, faturamento_eventos, parc_receitas_extr_dia])
    return todos_faturamentos, faturamento_eventos, parc_receitas_extr, parc_receitas_extr_dia


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