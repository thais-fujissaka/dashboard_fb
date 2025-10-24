import pandas as pd
import numpy as np
from utils.queries_cmv import *

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
        prioridade = ((df_precos_insumos_estoque_filtrado['ID Casa'] == id_casa) & 
                      (df_precos_insumos_estoque_filtrado['Mês Compra'] == mes) &
                      (df_precos_insumos_estoque_filtrado['Ano Compra'] == ano)).astype(int)
    )
    df_precos_insumos_estoque_filtrado = (
        df_precos_insumos_estoque_filtrado
        .sort_values(by=['prioridade'], ascending=False)
        .drop_duplicates(subset=['ID Insumo Estoque'], keep='first')
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
            df_precos_insumos_estoque['Ano Compra'].astype(int).astype(str) + '-' +
            df_precos_insumos_estoque['Mês Compra'].astype(int).astype(str).str.zfill(2) + '-01'
        )
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


def cor_porcentagem_cmv(cmv_teorico_porcentagem):
    if cmv_teorico_porcentagem < 29:
        return 'verde'
    elif cmv_teorico_porcentagem >= 29 and cmv_teorico_porcentagem < 32:
        return 'amarelo'
    else:
        return 'vermelho'