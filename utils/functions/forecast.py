import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import timedelta
from utils.components import dataframe_aggrid
from st_aggrid import ColumnsAutoSizeMode


# Prepara df de faturamento agregado diário para a casa selecionada
def prepara_dados_faturam_agregado_diario(id_casa, df_faturamento_agregado_dia, inicio_do_mes_anterior, fim_do_mes_atual):
    df_faturamento_agregado_casa = df_faturamento_agregado_dia[df_faturamento_agregado_dia['ID_Casa'] == id_casa]
    df_faturamento_agregado_casa['Data_Evento'] = pd.to_datetime(df_faturamento_agregado_casa['Data_Evento'], errors='coerce')
    df_faturamento_agregado_casa['Dia Semana'] = pd.to_datetime(df_faturamento_agregado_casa['Data_Evento'], errors='coerce').dt.strftime('%A')
    df_faturamento_agregado_casa['Dia_Mes'] = pd.to_datetime(df_faturamento_agregado_casa['Data_Evento'], errors='coerce').dt.day
    # st.write(df_faturamento_agregado_dia)

    # Filtra por casa e mês (anterior e corrente) - para utilizar no cálculo de projeção
    df_faturamento_agregado_mes_corrente = df_faturamento_agregado_casa[
        (df_faturamento_agregado_casa['Data_Evento'] >= inicio_do_mes_anterior) &
        (df_faturamento_agregado_casa['Data_Evento'] <= fim_do_mes_atual)]
    
    return df_faturamento_agregado_mes_corrente


# --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x DIAS (mês anterior e corrente) ---
def lista_dias_mes_anterior_atual(ano_atual, mes_atual, ultimo_dia_mes_atual, 
                                  ano_anterior, mes_anterior,
                                  df_faturamento_agregado_mes_corrente):

    # Último dia do mês anterior
    ultimo_dia_mes_anterior = calendar.monthrange(ano_anterior, mes_anterior)[1]

    # Cria lista de dias dos dois meses
    lista_dias_mes_anterior = list(range(1, ultimo_dia_mes_anterior + 1))
    lista_dias_mes_corrente = list(range(1, ultimo_dia_mes_atual + 1))

    # Cria DataFrame para o mês anterior
    df_dias_mes_anterior = pd.DataFrame({'Dia_Mes': lista_dias_mes_anterior})
    df_dias_mes_anterior['Data_Evento'] = pd.to_datetime({
        'year': ano_anterior,
        'month': mes_anterior,
        'day': df_dias_mes_anterior['Dia_Mes']
    })
    df_dias_mes_anterior['Dia Semana'] = df_dias_mes_anterior['Data_Evento'].dt.strftime('%A')

    # Cria DataFrame para o mês atual
    df_dias_mes_corrente = pd.DataFrame({'Dia_Mes': lista_dias_mes_corrente})
    df_dias_mes_corrente['Data_Evento'] = pd.to_datetime({
        'year': ano_atual,
        'month': mes_atual,
        'day': df_dias_mes_corrente['Dia_Mes']
    })
    df_dias_mes_corrente['Dia Semana'] = df_dias_mes_corrente['Data_Evento'].dt.strftime('%A')

    # Junta os dois meses
    df_dias_mes = pd.concat([df_dias_mes_anterior, df_dias_mes_corrente], ignore_index=True)

    # Agora faz o cross com categorias 
    categorias = df_faturamento_agregado_mes_corrente['Categoria'].dropna().unique()
    df_categorias = pd.DataFrame({'Categoria': categorias})
    df_dias_futuros_com_categorias = df_dias_mes.merge(df_categorias, how='cross')
    return df_dias_futuros_com_categorias


# Função para cálculo da projeção - mês corrente
def cria_projecao_mes_corrente(df_faturamento_agregado_mes_corrente, df_dias_futuros_com_categorias, today):
    # Merge com df do mês completo para gerar projeção dos prox dias
    df_dias_futuros_mes = df_faturamento_agregado_mes_corrente.merge(
        df_dias_futuros_com_categorias, 
        how='right', 
        on=['Data_Evento', 'Dia Semana', 'Categoria'])

    df_dias_futuros_mes['Projecao'] = None

    # Loop por categoria
    for categoria in df_dias_futuros_mes['Categoria'].unique():
        df_cat = None
        if categoria not in ('Eventos A&B', 'Eventos Locações', 'Eventos Couvert', 'Outras Receitas'): 
            df_cat = df_dias_futuros_mes[df_dias_futuros_mes['Categoria'] == categoria]
        
        if df_cat is not None and not df_cat.empty:
            for i, row in df_cat.iterrows():
                data = row['Data_Evento']

                # if data > today:  # apenas dias futuros 
                # -> estou fazendo para todos os dias (desde o mês anterior) para comparar projetado/real
                dia_semana = row['Dia Semana']

                # pega histórico das duas semanas anteriores MESMO DIA DA SEMANA e MESMA CATEGORIA
                duas_semanas_atras = data - timedelta(days=14)

                historico = df_dias_futuros_mes[
                    (df_dias_futuros_mes['Categoria'] == categoria) &
                    (df_dias_futuros_mes['Dia Semana'] == dia_semana) &
                    (df_dias_futuros_mes['Data_Evento'] >= duas_semanas_atras) &
                    (df_dias_futuros_mes['Data_Evento'] < data)
                ]

                # usa o Valor_Bruto (real) quando existir, senão a Projecao (que pode vir de dias anteriores)
                valores_para_media = historico['Valor_Bruto'].fillna(historico['Projecao']).astype(float)

                if not valores_para_media.empty:
                    media = valores_para_media.mean()
                    df_dias_futuros_mes.at[i, 'Projecao'] = media

    # Define valor final
    df_dias_futuros_mes['Valor_Final'] = df_dias_futuros_mes['Valor_Bruto'].fillna(df_dias_futuros_mes['Projecao'])
    return df_dias_futuros_mes


# Função para exibição da projeção por categoria - mês corrente
def exibe_categoria_faturamento(categoria, df_dias_futuros_mes, today):
    df_dias_futuros_mes['Projecao'] = df_dias_futuros_mes['Projecao'].fillna(0)
    df_dias_futuros_mes['Valor_Bruto'] = df_dias_futuros_mes['Valor_Bruto'].fillna(0)
    df_dias_futuros_mes['Desconto'] = df_dias_futuros_mes['Desconto'].fillna(0)
    df_dias_futuros_mes['Valor_Liquido'] = df_dias_futuros_mes['Valor_Liquido'].fillna(0)
    titulo = categoria

    if categoria == 'A&B':
        df_projecao_faturamento_categoria = df_dias_futuros_mes[
            ((df_dias_futuros_mes['Categoria'] == 'Alimentos') |
            (df_dias_futuros_mes['Categoria'] == 'Bebidas')) & 
            (df_dias_futuros_mes['Data_Evento'] > today)]
        
    else:
        df_projecao_faturamento_categoria = df_dias_futuros_mes[
            (df_dias_futuros_mes['Categoria'] == categoria) &
            (df_dias_futuros_mes['Data_Evento'] > today)]

        if categoria == 'Couvert':
            titulo = 'Artístico (Couvert)'


    df_projecao_faturamento_categoria = df_projecao_faturamento_categoria[['Categoria', 'Data_Evento', 'Dia Semana', 'Projecao']]
    df_projecao_faturamento_categoria = df_projecao_faturamento_categoria.rename(columns={
        'Data_Evento': 'Data',
        'Projecao': 'Valor Projetado',
        'Valor_Bruto': 'Valor Real'
    })

    # Exibe titulo
    st.markdown(f'''
            <h4 style="color: #1f77b4;">Faturamento {titulo}</h4>
        ''', unsafe_allow_html=True)
    
    if df_projecao_faturamento_categoria.empty:
        st.info('Não há dados de faturamento para essa categoria.')

    else: # Exibe df com aggrid
        dataframe_aggrid(
            df=df_projecao_faturamento_categoria,
            name=f"Projeção - {titulo}",
            num_columns=["Valor Projetado", 'Valor Real', 'Desconto', 'Valor_Liquido'],     
            date_columns=['Data'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True   
        )
    
    st.divider()


# Une faturamentos e orçamentos mensais para calcular histórico de atingimento (%)
def prepara_dados_faturamento_orcamentos_mensais(id_casa, df_orcamentos, df_faturamento_agregado_mes, ano_passado, ano_atual):
    # Filtra por casa e período (ano passado e atual)
    df_orcamentos_casa = df_orcamentos[
        (df_orcamentos['ID_Casa'] == id_casa) &
        (df_orcamentos['Ano'] >= ano_passado) &
        (df_orcamentos['Ano'] <= ano_atual) &
        (df_orcamentos['Categoria'] != 'Eventos Rebate Fornecedores')
    ]
    
    df_faturamento_mes_casa = df_faturamento_agregado_mes[
        (df_faturamento_agregado_mes['ID_Casa'] == id_casa) &
        (df_faturamento_agregado_mes['Ano'] >= ano_passado) &
        (df_faturamento_agregado_mes['Ano'] <= ano_atual)
    ]

    # Merge para calcular faturamento/orçamento
    df_faturamento_orcamento = pd.merge(
        df_faturamento_mes_casa[['Categoria', 'Ano', 'Mes', 'Valor_Bruto']],
        df_orcamentos_casa[['Categoria', 'Ano', 'Mes', 'Orcamento_Faturamento']],
        how='right',
        on=['Mes', 'Ano', 'Categoria']
    )
    
    # Calcula Faturamento / Orçamento
    df_faturamento_orcamento['Atingimento Real (%)'] = (
        (df_faturamento_orcamento['Valor_Bruto'].astype(float) /
        df_faturamento_orcamento['Orcamento_Faturamento'].replace(0, np.nan).astype(float)) * 100
    )

    return df_faturamento_mes_casa, df_faturamento_orcamento


# --- CRIA COMBINAÇÃO DE TODAS AS CATEGORIAS x MESES (ano corrente) ---
def lista_meses_ano(df_faturamento_agregado, ano_atual, ano_passado):
    lista_meses_ano_anterior = list(range(1, 13))
    df_meses_ano_anterior = pd.DataFrame({'Meses_Ano':lista_meses_ano_anterior, 'Ano': ano_passado})

    lista_meses_ano_atual = list(range(1, 13))
    df_meses_ano_atual = pd.DataFrame({'Meses_Ano':lista_meses_ano_atual, 'Ano': ano_atual})

    # Concatena ano anterior e atual
    df_meses_anos = pd.concat([df_meses_ano_anterior, df_meses_ano_atual])

    # Agora faz o cross com categorias 
    categorias = df_faturamento_agregado['Categoria'].dropna().unique()
    df_categorias = pd.DataFrame({'Categoria': categorias})
    df_meses_futuros_com_categorias = df_meses_anos.merge(df_categorias, how='cross')

    df_meses_futuros_com_categorias['Data'] = pd.to_datetime({
        'year': df_meses_futuros_com_categorias['Ano'],
        'month': df_meses_futuros_com_categorias['Meses_Ano'],
        'day': 1
    })

    return df_meses_futuros_com_categorias


# Função para cálculo da projeção - meses seguintes
def cria_projecao_meses_seguintes(df_faturamento_orcamento, df_meses_futuros_com_categorias, ano_atual):
    # Merge com df que contém todos os meses (ano anterior e corrente)
    df_meses_seguintes = df_faturamento_orcamento.merge(
        df_meses_futuros_com_categorias, 
        how='right', 
        left_on=['Ano', 'Mes', 'Categoria'],
        right_on=['Ano', 'Meses_Ano', 'Categoria']
    )
    
    df_meses_seguintes['Projecao_Atingimento (%)'] = None

    # Loop por categoria
    for categoria in df_meses_seguintes['Categoria'].unique():
        df_cat = None
        df_cat = df_meses_seguintes[df_meses_seguintes['Categoria'] == categoria]
        
        if df_cat is not None and not df_cat.empty:
            for i, row in df_cat.iterrows():
                data = row['Data']
                ano = row['Ano']

                if ano >= ano_atual:  # apenas meses do ano atual
                    mes = row['Data']

                    # pega histórico dos dois meses atrás
                    dois_meses_atras = mes - pd.DateOffset(months=2)

                    historico = df_meses_seguintes[
                        (df_meses_seguintes['Categoria'] == categoria) &
                        (df_meses_seguintes['Data'] >= dois_meses_atras) &
                        (df_meses_seguintes['Data'] < mes)
                    ]

                    # usa o Atingimento (real) quando existir, senão a Projecao (que pode vir de meses anteriores)
                    valores_para_media = historico['Atingimento Real (%)'].fillna(historico['Projecao_Atingimento (%)']).astype(float)

                    if not valores_para_media.empty:
                        media = valores_para_media.mean()
                        df_meses_seguintes.at[i, 'Projecao_Atingimento (%)'] = media

    # Define valor de faturamento projetado baseado na projeção (%) de atingimento do orçamento
    df_meses_seguintes['Valor Projetado'] = (
        df_meses_seguintes['Orcamento_Faturamento'].astype(float) * (df_meses_seguintes['Projecao_Atingimento (%)'].astype(float) / 100)
    )
    return df_meses_seguintes


# Função para exibição da projeção por categoria - mês corrente
def exibe_categoria_faturamento_prox_meses(categoria, df_meses_futuros, ano_atual, mes_atual):
    df_meses_futuros['Valor_Bruto'] = df_meses_futuros['Valor_Bruto'].fillna(0)
    df_meses_futuros['Atingimento Real (%)'] = df_meses_futuros['Atingimento Real (%)'].fillna(0)
    df_meses_futuros['Projecao_Atingimento (%)'] = df_meses_futuros['Projecao_Atingimento (%)'].fillna(0)
    df_meses_futuros['Valor Projetado'] = df_meses_futuros['Valor Projetado'].fillna(0)
    
    titulo = categoria

    if categoria == 'A&B':
        df_projecao_faturamento_categoria_prox_meses = df_meses_futuros[
            ((df_meses_futuros['Categoria'] == 'Alimentos') | (df_meses_futuros['Categoria'] == 'Bebidas')) & 
            (df_meses_futuros['Ano'] == ano_atual) &
            (df_meses_futuros['Mes'] > mes_atual)
        ]

    elif categoria == 'Eventos':
        df_projecao_faturamento_categoria_prox_meses = df_meses_futuros[
            (df_meses_futuros['Categoria'].isin(['Eventos A&B', 'Eventos Locações', 'Eventos Couvert'])) & 
            (df_meses_futuros['Ano'] == ano_atual) &
            (df_meses_futuros['Mes'] > mes_atual)
        ]
        
    else:
        df_projecao_faturamento_categoria_prox_meses = df_meses_futuros[
            (df_meses_futuros['Categoria'] == categoria) &
            (df_meses_futuros['Ano'] == ano_atual) &
            (df_meses_futuros['Mes'] > mes_atual)
        ]

        if categoria == 'Couvert':
            titulo = 'Artístico (Couvert)'


    df_projecao_faturamento_categoria_prox_meses = df_projecao_faturamento_categoria_prox_meses[['Categoria', 'Ano', 'Mes', 'Orcamento_Faturamento', 'Projecao_Atingimento (%)', 'Valor Projetado']]
    df_projecao_faturamento_categoria_prox_meses = df_projecao_faturamento_categoria_prox_meses.rename(columns={
        'Orcamento_Faturamento': 'Orçamento',
        'Valor_Bruto': 'Valor Real',
        'Projecao_Atingimento (%)':'Projeção Atingimento (%)'
    })

    # Exibe titulo
    st.markdown(f'''
            <h4 style="color: #1f77b4;">Faturamento {titulo}</h4>
        ''', unsafe_allow_html=True)
    
    if df_projecao_faturamento_categoria_prox_meses.empty:
        st.info('Não há dados de faturamento para essa categoria.')

    else: # Exibe df com aggrid
        dataframe_aggrid(
            df=df_projecao_faturamento_categoria_prox_meses,
            name=f"Projeção próximos meses - {titulo}",
            num_columns=['Orçamento', 'Valor Projetado'],     
            percent_columns=['Projecao_Atingimento (%)'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True   
        )
    
    st.divider()
    
    