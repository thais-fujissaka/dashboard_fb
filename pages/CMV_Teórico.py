import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.user import *
from utils.functions.cmv_teorico_fichas_tecnicas import *
from utils.queries_cmv import *

st.set_page_config(
    page_icon=":material/rubric:",
    page_title="CMV Teórico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
    st.switch_page('Login.py')


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


def calcular_custo_insumos_estoque(row):
    # ('ml', 'LITRO') onde 'ml' é U.M. do insumo na ficha (Unidade Medida) e 'LITRO' é U.M. do insumo no estoque (U.M. Insumo Estoque)
    conversoes = {
        ('ml', 'ml'): 1,
        ('ml', 'LT'): 0.001,
        ('gr', 'gr'): 1,
        ('gr', 'KG'): 0.001,
        ('UN', 'UN'): 1
    }
    if row['Produção?'] == 0: # Item de estoque
        conversao = (row['Unidade Medida'], row['U.M. Insumo Estoque'])
        if conversao in conversoes:
            proporcao = conversoes[conversao]
            return row['Quantidade na Ficha'] * row['Preço Médio Insumo Estoque'] * proporcao
    return


def selecionar_precos_mes_casa(df_precos_insumos_estoque, df_insumos_estoque_necessarios_casa, id_casa, mes, ano):

    if mes == 1:
        mes_anterior = 12
        ano_anterior = ano - 1
    else:
        mes_anterior = mes - 1
        ano_anterior = ano

    # Insumos de estoque necessários da casa
    df_insumos_necessarios_casa = df_insumos_estoque_necessarios_casa[df_insumos_estoque_necessarios_casa['ID Casa'] == id_casa].dropna(subset=['ID Insumo Estoque'])
    
    # Filtra os precos do mes ou mes anterior e da casa
    df_precos_insumos_estoque_filtrado = df_precos_insumos_estoque[
        (df_precos_insumos_estoque['Mês Compra'].isin([mes, mes_anterior])) &
        (df_precos_insumos_estoque['Ano Compra'].isin([ano, ano_anterior])) &
        (df_precos_insumos_estoque['ID Casa'] == id_casa)].copy()

    # Prioridade para o mês atual no preço (merge)
    df_precos_insumos_estoque_filtrado = df_precos_insumos_estoque_filtrado.assign(
        prioridade = ((df_precos_insumos_estoque_filtrado['Mês Compra'] == mes) &
                    (df_precos_insumos_estoque_filtrado['Ano Compra'] == ano)).astype(int)
    )
    df_precos_insumos_estoque_filtrado = (
        df_precos_insumos_estoque_filtrado
        .sort_values(by=['prioridade'], ascending=False)
        .drop_duplicates(subset=['ID Casa', 'ID Insumo Estoque'], keep='first')
        .drop(columns=['prioridade'])
    )

    # Adiciona os preços dos insumos de estoque comprados no mês ou no mês anterior com prioridade para o mês atual
    df_insumos_necessarios_casa = pd.merge(df_insumos_necessarios_casa, df_precos_insumos_estoque_filtrado, how='left', on=['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque'])
    df_insumos_comprados_mes_ou_anterior = df_insumos_necessarios_casa[df_insumos_necessarios_casa['ID Insumo Estoque'].isin(df_precos_insumos_estoque_filtrado['ID Insumo Estoque'])]

    # Insumos de estoque não comprados no mês nem no mês anterior
    df_insumos_nao_comprados_mes_ou_anterior = df_insumos_necessarios_casa[~df_insumos_necessarios_casa['ID Insumo Estoque'].isin(df_precos_insumos_estoque_filtrado['ID Insumo Estoque'])]
    df_insumos_nao_comprados_mes_ou_anterior = df_insumos_nao_comprados_mes_ou_anterior[['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque']]

    # Adiciona os preços dos insumos de estoque comprado mais recente de outra casa:
    # Cria coluna de data usando ano e mês
    df_precos_insumos_estoque = df_precos_insumos_estoque.assign(
        data_compra = pd.to_datetime(
            df_precos_insumos_estoque['Ano Compra'].astype(str) + '-' +
            df_precos_insumos_estoque['Mês Compra'].astype(str) + '-01')
    )
    # Ordena por ID Insumo e data mais recente
    df_precos_insumos_estoque = df_precos_insumos_estoque.sort_values(by=['ID Insumo Estoque', 'data_compra'], ascending=[True, False])
    # Mantém apenas o preço mais recente por ID Insumo
    df_precos_insumos_estoque = df_precos_insumos_estoque.drop_duplicates(subset=['ID Insumo Estoque', 'Insumo Estoque'], keep='first')
    # Adiciona os preços dos insumos de estoque comprado mais recente de outra casa
    df_precos_insumos_nao_comprados = pd.merge(df_insumos_nao_comprados_mes_ou_anterior, df_precos_insumos_estoque, how='left', on=['ID Insumo Estoque', 'Insumo Estoque'])
    # Remove coluna data_compra e colunas das casas substitutivas
    df_precos_insumos_nao_comprados = df_precos_insumos_nao_comprados.drop(columns=['data_compra', 'ID Casa_y', 'Casa_y'])
    df_precos_insumos_nao_comprados = df_precos_insumos_nao_comprados.rename(columns={'ID Casa_x': 'ID Casa', 'Casa_x': 'Casa'})

    # Junta preços comprados no mês anterior e atual para a casa + preço mais recente de outras casas
    df_insumos_estoque_necessarios_casa = pd.concat([df_insumos_comprados_mes_ou_anterior, df_precos_insumos_nao_comprados])

    return df_insumos_estoque_necessarios_casa


def somar_precos_itens_estoque_na_ficha(df_merged_fichas_producao_precos):
    proporcao_unidades_medida = {
        ('gr', 'gr'): 1,
        ('gr', 'KG'): 0.001,
        ('ml', 'ml'): 1,
        ('ml', 'LT'): 0.001,
        ('UN', 'UN'): 1
    }

    df_precos_estoque_na_ficha = df_merged_fichas_producao_precos.copy()

    # Calcula preço dos itens de estoque nas fichas de produção
    for index, row in df_precos_estoque_na_ficha.iterrows():
        conversao = (row['U.M. Ficha Itens'], row['U.M. Insumo Estoque'])
        if conversao in proporcao_unidades_medida:
            proporcao = proporcao_unidades_medida[conversao]
            df_precos_estoque_na_ficha.at[index, 'Custo Ficha'] = row['Preço Médio Insumo Estoque'] * row['Quantidade'] * proporcao
 
    return df_precos_estoque_na_ficha


def substituir_precos_producao_na_ficha(df_precos_na_ficha, df_itens_precos_completos):
    
    proporcao_unidades_medida = {
        ('gr', 'gr'): 1,
        ('gr', 'KG'): 0.001,
        ('KG', 'gr'): 1000,
        ('ml', 'ml'): 1,
        ('ml', 'LT'): 0.001,
        ('UN', 'UN'): 1,
        ('LT', 'ml'): 1000
    }
    df_itens_precos_completos = df_itens_precos_completos[['ID Casa', 'Casa', 'ID Ficha Técnica Produção', 'ID Item Produzido', 'Item Produzido', 'U.M. Rendimento', 'Custo Ficha', 'Custo Item Produzido']]
    for index, row in df_precos_na_ficha.iterrows():
        if pd.isna(row['Custo Ficha']) and row['ID Insumo Produção'] in df_itens_precos_completos['ID Item Produzido'].tolist():
            unidade_ficha = row['U.M. Ficha Itens']
            unidade_insumo_producao = df_itens_precos_completos.loc[
                df_itens_precos_completos['ID Item Produzido'] == row['ID Insumo Produção'],
                'U.M. Rendimento'
            ].values[0]
            
            proporcao = proporcao_unidades_medida.get((unidade_ficha, unidade_insumo_producao), 1) # Se não existir a proporção no dicionário usa proporção 1
            
            df_precos_na_ficha.at[index, 'Custo Ficha'] = (df_itens_precos_completos.loc[df_itens_precos_completos['ID Item Produzido'] == row['ID Insumo Produção'], 'Custo Item Produzido'].values[0] 
                                                           * row['Quantidade'] 
                                                           * proporcao)
    
    condicao = (
        df_precos_na_ficha['Custo Ficha'].isna() &
        ~df_precos_na_ficha[['U.M. Ficha Itens', 'U.M. Insumo Estoque']].apply(tuple, axis=1).isin(proporcao_unidades_medida.keys()) &
        df_precos_na_ficha['ID Insumo Produção'].isna()
    )
    df_precos_na_ficha['Custo Ficha'] = np.where(condicao, 0, df_precos_na_ficha['Custo Ficha'])
    
    return df_precos_na_ficha

def adicionar_novos_precos_producao_completos(df_precos_na_ficha):
    itens_precos_completos = (
        df_precos_na_ficha.groupby('ID Item Produzido')['Custo Ficha']
        .apply(lambda x: x.notna().all())
    )
    df_itens_precos_completos = df_precos_na_ficha[df_precos_na_ficha['ID Item Produzido'].isin(itens_precos_completos[itens_precos_completos].index)]
    df_itens_precos_completos = df_itens_precos_completos.groupby(['ID Casa', 'Casa', 'ID Ficha Técnica Produção', 'ID Item Produzido', 'Item Produzido', 'Quantidade Rendimento', 'U.M. Rendimento'],
    as_index=False)['Custo Ficha'].sum().reset_index()

    # Calcula o preço médio da unidade de rendimento do item produzido
    df_itens_precos_completos['Custo Item Produzido'] = df_itens_precos_completos['Custo Ficha'] / df_itens_precos_completos['Quantidade Rendimento']

    return df_itens_precos_completos


def adicionar_precos_sem_ficha_producao(df_precos_na_ficha):
    # Quando não há ficha técnica do item de produção, não há como calcular o preço do item. Então, assume preço igual a zero
    s1 = set(df_precos_na_ficha['ID Insumo Produção'].dropna().unique().tolist())
    s2 = set(df_precos_na_ficha['ID Item Produzido'].dropna().unique().tolist())

    set_itens_sem_ficha_producao = s1 - s2
    
    df_precos_na_ficha['Custo Ficha'] = np.where(df_precos_na_ficha['ID Insumo Produção'].isin(set_itens_sem_ficha_producao), 0, df_precos_na_ficha['Custo Ficha'])
    
    return df_precos_na_ficha

def somar_precos_itens_producao_na_ficha(df_precos_na_ficha):

    # Dataframe auxiliar dos itens de produção que possuem todos os valores necessários para a soma dos preços
    df_itens_precos_completos = adicionar_novos_precos_producao_completos(df_precos_na_ficha)

    # Verifica se os itens de produção necessários são da casa selecionada
    df_casas_itens_producao = GET_CASAS_ITENS_PRODUCAO()
    df_precos_na_ficha = df_precos_na_ficha.merge(
        df_casas_itens_producao, how='left', on='ID Insumo Produção'
    )

    # Se o item de produção não pertence à casa, remove-o do dataframe
    df_precos_na_ficha = df_precos_na_ficha[
        (df_precos_na_ficha['ID Casa'] == df_precos_na_ficha['ID Casa Produção'])
        | (df_precos_na_ficha['ID Insumo Estoque'].notna())
    ]

    # Preenche os preços dos insumos de estoque que estão com os custos completos
    df_precos_na_ficha = substituir_precos_producao_na_ficha(
        df_precos_na_ficha, df_itens_precos_completos
    )

    # Recalcula novos preços completos
    df_novos_precos_completos = adicionar_novos_precos_producao_completos(df_precos_na_ficha)

    # Exclui coluna auxiliar
    df_precos_na_ficha = df_precos_na_ficha.drop(columns=['ID Casa Produção'])

    # Se surgiram novos preços completos, chama recursivamente
    if not df_novos_precos_completos.equals(df_itens_precos_completos):
        return somar_precos_itens_producao_na_ficha(df_precos_na_ficha)

    return df_precos_na_ficha, df_novos_precos_completos


def calcular_precos_itens_producao(df_fichas_itens_producao, df_precos_selecionados_mes_casa, id_casa):
    df_precos_selecionados_mes_casa = df_precos_selecionados_mes_casa[['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque', 'U.M. Insumo Estoque', 'Preço Médio Insumo Estoque']]
    # Filtra fichas da casa
    df_fichas_itens_producao = df_fichas_itens_producao[df_fichas_itens_producao['ID Casa'] == id_casa]
    
    df_merged_fichas_producao_precos = pd.merge(df_fichas_itens_producao, df_precos_selecionados_mes_casa, how='left', on=['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque'])

    df_precos_na_ficha = somar_precos_itens_estoque_na_ficha(df_merged_fichas_producao_precos)
    df_precos_na_ficha, df_itens_producao_precos_completos = somar_precos_itens_producao_na_ficha(df_precos_na_ficha)


    # Se existe ainda insumos de produção cujos preços não constam nos preços completos, calcula os preços completos e adiciona no dataframe de preços de produção completos
    df_precos_na_ficha = adicionar_precos_sem_ficha_producao(df_precos_na_ficha)
    df_itens_producao_precos_completos = adicionar_novos_precos_producao_completos(df_precos_na_ficha)

    return df_precos_na_ficha, df_itens_producao_precos_completos


def calcular_precos_itens_producao_mes_casa(df_fichas_itens_producao, df_precos_insumos_de_estoque, df_insumos_estoque_necessarios_casa, id_casa, mes, ano):
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[['ID Casa', 'Casa', 'Mês Compra', 'Ano Compra', 'ID Insumo Estoque', 'Insumo Estoque', 'U.M. Insumo Estoque', 'Preço Médio Insumo Estoque']].copy()

    # IMPORTANTE: Preços dos insumos de estoque necessários
    df_precos_selecionados_mes_casa = selecionar_precos_mes_casa(df_precos_insumos_de_estoque, df_insumos_estoque_necessarios_casa, id_casa, mes, ano)
    # Zera preços None
    df_precos_selecionados_mes_casa['Preço Médio Insumo Estoque'] = df_precos_selecionados_mes_casa['Preço Médio Insumo Estoque'].fillna(0)

    # IMPORTANTE: Preços dos insumos de produção
    df_precos_fichas_producao, df_precos_itens_producao = calcular_precos_itens_producao(df_fichas_itens_producao, df_precos_selecionados_mes_casa, id_casa)

    return df_precos_fichas_producao, df_precos_itens_producao, df_precos_selecionados_mes_casa
    

def calcular_custos_itens_vendidos(df_fichas_itens_vendidos, df_precos_insumos_de_estoque, df_precos_itens_producao_completo):
    df_fichas_itens_vendidos = df_fichas_itens_vendidos[['ID Casa', 'Casa', 'ID Item Zig', 'Item Vendido Zig', 'ID Ficha Técnica', 'ID Insumo Estoque', 'Insumo Estoque', 'Quantidade na Ficha', 'Unidade Medida', 'ID Insumo Produção', 'Insumo Produção']].copy()
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque', 'U.M. Insumo Estoque', 'Preço Médio Insumo Estoque']].copy()
    df_precos_itens_producao_completo = df_precos_itens_producao_completo[['ID Casa', 'Casa', 'ID Item Produzido', 'Item Produzido', 'U.M. Rendimento', 'Custo Item Produzido']].copy()
    df_precos_itens_producao_completo = df_precos_itens_producao_completo.rename(columns={
        'ID Item Produzido': 'ID Insumo Produção',
        'Item Produzido': 'Insumo Produção'
    })

    df_fichas_itens_vendidos = pd.merge(df_fichas_itens_vendidos, df_precos_insumos_de_estoque, how='left', on=['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque'])
    df_fichas_itens_vendidos = pd.merge(df_fichas_itens_vendidos, df_precos_itens_producao_completo, how='left', on=['ID Casa', 'Casa', 'ID Insumo Produção', 'Insumo Produção'])

    proporcao = {
        ('gr', 'gr'): 1,
        ('gr', 'KG'): 1000,
        ('KG', 'gr'): 0.001,
        ('ml', 'ml'): 1,
        ('ml', 'LT'): 1000,
        ('UN', 'UN'): 1,
        ('LT', 'ml'): 0.001
    }
    # Calcula custos
    df_fichas_itens_vendidos['Preço Médio Insumo Estoque'] = df_fichas_itens_vendidos['Preço Médio Insumo Estoque'].fillna(0)
    df_fichas_itens_vendidos['Custo Item Produzido'] = df_fichas_itens_vendidos['Custo Item Produzido'].fillna(0)
    # Cria coluna de chave de proporções
    df_fichas_itens_vendidos['chave_proporcao_producao'] = df_fichas_itens_vendidos[['U.M. Rendimento', 'Unidade Medida']].apply(tuple, axis=1)
    df_fichas_itens_vendidos['chave_proporcao_estoque'] = df_fichas_itens_vendidos[['U.M. Insumo Estoque', 'Unidade Medida']].apply(tuple, axis=1)
    # Colunas de valores finais
    df_fichas_itens_vendidos['Custo Item Estoque'] = df_fichas_itens_vendidos['Quantidade na Ficha'] * df_fichas_itens_vendidos['Preço Médio Insumo Estoque'] * df_fichas_itens_vendidos['chave_proporcao_estoque'].map(proporcao)
    df_fichas_itens_vendidos['Custo Item Produção'] = df_fichas_itens_vendidos['Quantidade na Ficha'] * df_fichas_itens_vendidos['Custo Item Produzido'] * df_fichas_itens_vendidos['chave_proporcao_producao'].map(proporcao)

    df_fichas_itens_vendidos['Custo Item Estoque'] = df_fichas_itens_vendidos['Custo Item Estoque'].fillna(0)
    df_fichas_itens_vendidos['Custo Item Produção'] = df_fichas_itens_vendidos['Custo Item Produção'].fillna(0)

    # Soma custo de itens de estoque e de produção
    df_fichas_itens_vendidos['Custo Item'] = df_fichas_itens_vendidos['Custo Item Estoque'] + df_fichas_itens_vendidos['Custo Item Produção']

    df_fichas_itens_vendidos_auditoria = df_fichas_itens_vendidos.copy()

    # Dataframe de ficha técnica do item vendido 
    df_fichas_itens_vendidos['ID Insumo'] = df_fichas_itens_vendidos['ID Insumo Estoque'].fillna(df_fichas_itens_vendidos['ID Insumo Produção'])
    df_fichas_itens_vendidos['Insumo'] = df_fichas_itens_vendidos['Insumo Estoque'].fillna(df_fichas_itens_vendidos['Insumo Produção'])
    df_fichas_itens_vendidos = df_fichas_itens_vendidos.drop(columns={
        'ID Insumo Estoque', 'Insumo Estoque', 'ID Insumo Produção', 'Insumo Produção', 'U.M. Insumo Estoque', 'U.M. Rendimento', 'Custo Item Produzido', 'chave_proporcao_estoque', 'chave_proporcao_producao', 'Preço Médio Insumo Estoque', 'Custo Item Estoque', 'Custo Item Produção'
    })
    df_fichas_itens_vendidos.sort_values(by=['Item Vendido Zig'], inplace=True)
    
    # Dataframe com custo final dos itens vendidos
    df_precos_itens_vendidos = df_fichas_itens_vendidos[['ID Casa', 'Casa', 'ID Item Zig', 'Item Vendido Zig', 'ID Ficha Técnica', 'Custo Item']].copy().groupby(['ID Casa', 'Casa', 'ID Item Zig', 'Item Vendido Zig', 'ID Ficha Técnica']).agg({'Custo Item': 'sum'}).reset_index()
    
    return df_precos_itens_vendidos, df_fichas_itens_vendidos, df_fichas_itens_vendidos_auditoria
    

def main():
    # Sidebar
    config_sidebar()
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title(":material/rubric: CMV Teórico")
    with col2:
        st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
    with col3:
        if st.button('Logout', key='logout'):
            logout()
    st.divider()

    # Seletores
    col_casa, col_mes, col_ano = st.columns([1, 1, 1])
    with col_casa:
        lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Todas as Casas']
        id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, 'selecao_casa')
    with col_mes:
        #periodo = input_periodo_datas(key='data_inicio')
        nome_mes, mes = seletor_mes_produtos('mes')
    with col_ano:
        ano = seletor_ano(2024, 2025, 'ano')

    st.divider()

    # PREÇO DOS ITENS VENDIDOS
    # 1. Dados dos itens vendidos (A&B), sem considerar o desconto

    # FICHAS TÉCNICAS - Custo do item vendido
    # 2. Dados dos insumos de estoque das fichas técnicas (por casa)
        # Para cada insumo de estoque, calcular uma média de preços de compra e de estoque

    # 3. Dados dos insumos de produção das fichas técnicas (por casa)
        # Para cada insumo de produção, visualizar os insumos de estoque necessários para produzir o insumo de produção

    # 4. Chegar no Custo Unit. do Produto pelo custo dos insumos (estoque + produção)
    
    ### FICHAS TÉCNICAS - ITENS VENDIDOS PARA INSUMOS DE ESTOQUE E PRODUÇÃO
    # dataframe com as quantidades de insumos de estoque para cada ITEM VENDIDO
    df_fichas_itens_vendidos_insumos_estoque = GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_INSUMOS_ESTOQUE()
    # dataframe com as quantidades de insumos de produção para cada ITEM VENDIDO
    df_fichas_itens_vendidos_itens_producao = GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_ITENS_PRODUCAO()
    
    # dataframe com as quantidades de insumos de produção e de estoque para cada VENDIDO
    df_fichas_itens_vendidos = pd.merge(df_fichas_itens_vendidos_insumos_estoque, df_fichas_itens_vendidos_itens_producao, how='outer')

    ### FICHAS TÉCNICAS - INSUMOS DE ESTOQUE
    df_precos_insumos = GET_PRECOS_INSUMOS_N5_COM_PROPORCAO_ESTOQUE()

    df_precos_insumos_de_estoque = df_precos_insumos.groupby(['ID Casa', 'ID Insumo Estoque', 'Mês Compra', 'Ano Compra']).agg({
        'Valor N5': 'sum',
        'Quantidade Insumo Estoque': 'sum',
        'Casa': 'first',
        'Insumo Estoque': 'first',
        'U.M. Insumo Estoque': 'first'
    }).reset_index()
    col_ordem = [
        'ID Casa', 'Casa', 'Mês Compra', 'Ano Compra',
        'ID Insumo Estoque', 'Insumo Estoque', 'U.M. Insumo Estoque',
        'Valor N5', 'Quantidade Insumo Estoque'
    ]
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[col_ordem]
    # Calcula o preço da unidade (preço de 1 unidade de medida) do insumo de estoque
    df_precos_insumos_de_estoque['Preço Médio Insumo Estoque'] = df_precos_insumos_de_estoque['Valor N5'] / df_precos_insumos_de_estoque['Quantidade Insumo Estoque']

    #### PAREI AQUI, FALTA SELECIONAR UM ÚNICO PREÇO PARA CADA INSUMO DE ESTOQUE

    # Remover NaN
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque.dropna(subset=['Preço Médio Insumo Estoque'])
    # Remover inf e -inf
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[
        ~np.isinf(df_precos_insumos_de_estoque['Preço Médio Insumo Estoque'])
    ]
    # Remover valores negativos
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[
        df_precos_insumos_de_estoque['Preço Médio Insumo Estoque'] > 0
    ]

    # Filtra por casa   
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[df_precos_insumos_de_estoque['ID Casa'] == id_casa]

    ### FICHAS TÉCNICAS - INSUMOS DE PRODUÇÃO
    # dataframe com as quantidades de insumos de estoque e de produção para cada ITEM DE PRODUÇÃO
    df_fichas_itens_producao = GET_FICHAS_TECNICAS_DE_INSUMOS_PRODUCAO()

    # Obtem os insumos de estoque para cada casa para calcular o preço posteriormente
    insumos_necessarios_estoque_casa = df_fichas_itens_vendidos_insumos_estoque.loc[
        df_fichas_itens_vendidos_insumos_estoque['ID Casa'] == id_casa,
        ['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque']
    ].drop_duplicates()

    insumos_necessarios_estoque_casa = pd.concat(
        [
            insumos_necessarios_estoque_casa,
            df_fichas_itens_producao.loc[
                df_fichas_itens_producao['ID Casa'] == id_casa,
                ['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque']
            ].drop_duplicates()
        ],
        ignore_index=True
    ).drop_duplicates()

    df_precos_insumos_producao, df_precos_itens_producao_completo, df_precos_selecionados_estoque_mes_casa = calcular_precos_itens_producao_mes_casa(df_fichas_itens_producao, df_precos_insumos_de_estoque, insumos_necessarios_estoque_casa, id_casa, mes, ano)


    ### CUSTO ITENS VENDIDOS
    df_fichas_itens_vendidos = df_fichas_itens_vendidos[df_fichas_itens_vendidos['ID Casa'] == id_casa]
    df_precos_itens_vendidos, df_fichas_itens_vendidos, df_fichas_itens_vendidos_auditoria = calcular_custos_itens_vendidos(df_fichas_itens_vendidos, df_precos_selecionados_estoque_mes_casa, df_precos_itens_producao_completo, )

    # Ordena colunas
    df_precos_itens_vendidos = df_precos_itens_vendidos.sort_values(by=['Custo Item'], ascending=False)
    df_fichas_itens_vendidos = df_fichas_itens_vendidos.sort_values(by=['Item Vendido Zig', 'Custo Item'], ascending=False)
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque.sort_values(by=['Preço Médio Insumo Estoque'], ascending=False)
    df_precos_itens_producao_completo = df_precos_itens_producao_completo.sort_values(by=['Custo Item Produzido'], ascending=False)
    df_precos_insumos_producao = df_precos_insumos_producao.sort_values(by=['Custo Ficha'], ascending=False)

    df_precos_itens_vendidos_download = df_precos_itens_vendidos.copy()

    # Formatação de colunas
    df_precos_itens_vendidos = format_columns_brazilian(df_precos_itens_vendidos, ['Custo Item'])
    df_fichas_itens_vendidos = format_columns_brazilian(df_fichas_itens_vendidos, ['Custo Item'])
    df_precos_insumos_de_estoque = format_columns_brazilian(df_precos_insumos_de_estoque, ['Valor N5', 'Preço Médio Insumo Estoque'])
    df_precos_itens_producao_completo = format_columns_brazilian(df_precos_itens_producao_completo, ['Custo Ficha', 'Custo Item Produzido'])
    df_precos_insumos_producao = df_precos_insumos_producao.drop(columns={'Produção?'})
    df_precos_insumos_producao = format_columns_brazilian(df_precos_insumos_producao, ['Preço Médio Insumo Estoque', 'Custo Ficha'])

    col1, col2 = st.columns([3, 1], vertical_alignment='center', gap='large')
    with col1:
        st.markdown(f'## CMV - Custo Itens Vendidos ({casa})')
    with col2:
        button_download(df_precos_itens_vendidos_download, f'custo_itens_{casa}', f'custo_itens_{casa}')
    st.dataframe(df_precos_itens_vendidos, use_container_width=True, hide_index=True)
    st.divider()

    # Filtro por prato
    df_lista_produtos = pd.DataFrame(df_precos_itens_vendidos['ID Item Zig'].unique())
    df_lista_produtos['ID - Produto'] = df_precos_itens_vendidos['ID Item Zig'].astype(str) + ' - ' + df_precos_itens_vendidos['Item Vendido Zig']
    lista_produtos = df_lista_produtos['ID - Produto'].tolist()
    produto_selecionado = st.selectbox('Selecionar Produto', lista_produtos, key='selecionar_produto')
    id_produto_selecionado = int(produto_selecionado.split(' - ')[0])

    st.markdown('## Fichas Técnicas - Itens Vendidos')
    ordem_col = ['ID Casa', 'Casa', 'ID Item Zig', 'Item Vendido Zig', 'ID Ficha Técnica', 'ID Insumo', 'Insumo', 'Quantidade na Ficha', 'Unidade Medida', 'Custo Item']
    df_fichas_itens_vendidos = df_fichas_itens_vendidos[df_fichas_itens_vendidos['ID Item Zig'] == id_produto_selecionado]
    st.dataframe(df_fichas_itens_vendidos, use_container_width=True, hide_index=True)
     
    st.markdown('## Custos Itens de Estoque')
    st.dataframe(df_precos_insumos_de_estoque, use_container_width=True, hide_index=True)

    st.markdown('## Custos Itens de Produção')
    st.dataframe(df_precos_itens_producao_completo, use_container_width=True, hide_index=True)

    st.markdown('## Fichas Técnicas - Itens de Produção')
    st.dataframe(df_precos_insumos_producao, use_container_width=True, hide_index=True)
    
if __name__ == '__main__':
    main()
