import streamlit as st
import pandas as pd
import calendar
from datetime import timedelta
from utils.components import dataframe_aggrid
from st_aggrid import ColumnsAutoSizeMode


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
    df_dias_mes_anterior['Dia_Semana'] = df_dias_mes_anterior['Data_Evento'].dt.strftime('%A')

    # Cria DataFrame para o mês atual
    df_dias_mes_corrente = pd.DataFrame({'Dia_Mes': lista_dias_mes_corrente})
    df_dias_mes_corrente['Data_Evento'] = pd.to_datetime({
        'year': ano_atual,
        'month': mes_atual,
        'day': df_dias_mes_corrente['Dia_Mes']
    })
    df_dias_mes_corrente['Dia_Semana'] = df_dias_mes_corrente['Data_Evento'].dt.strftime('%A')

    # Junta os dois meses
    df_dias_mes = pd.concat([df_dias_mes_anterior, df_dias_mes_corrente], ignore_index=True)

    # Agora faz o cross com categorias (mantendo seu código original)
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
        on=['Data_Evento', 'Dia_Semana', 'Categoria'])

    df_dias_futuros_mes['Projecao'] = None

    # Loop por categoria
    for categoria in df_dias_futuros_mes['Categoria'].unique():
        df_cat = None
        if categoria not in ('Eventos A&B', 'Eventos Locações', 'Eventos Couvert', 'Outras Receitas'): 
            df_cat = df_dias_futuros_mes[df_dias_futuros_mes['Categoria'] == categoria]
        
        if df_cat is not None and not df_cat.empty:
            for i, row in df_cat.iterrows():
                data = row['Data_Evento']

                if data > today:  # apenas dias futuros
                    dia_semana = row['Dia_Semana']

                    # pega histórico das duas semanas anteriores MESMO DIA DA SEMANA e MESMA CATEGORIA
                    duas_semanas_atras = data - timedelta(days=14)

                    historico = df_dias_futuros_mes[
                        (df_dias_futuros_mes['Categoria'] == categoria) &
                        (df_dias_futuros_mes['Dia_Semana'] == dia_semana) &
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
        
    elif categoria == 'Eventos':
        df_projecao_faturamento_categoria = df_dias_futuros_mes[
            ((df_dias_futuros_mes['Categoria'] == 'Eventos A&B') |
            (df_dias_futuros_mes['Categoria'] == 'Eventos Couvert') |
            (df_dias_futuros_mes['Categoria'] == 'Eventos Locações')) & 
            (df_dias_futuros_mes['Data_Evento'] > today)]
    
    else:
        df_projecao_faturamento_categoria = df_dias_futuros_mes[
            (df_dias_futuros_mes['Categoria'] == categoria) &
            (df_dias_futuros_mes['Data_Evento'] > today)]

        if categoria == 'Couvert':
            titulo = 'Artístico (Couvert)'


    df_projecao_faturamento_categoria = df_projecao_faturamento_categoria[['Categoria', 'Data_Evento', 'Dia_Semana', 'Projecao']]
    df_projecao_faturamento_categoria = df_projecao_faturamento_categoria.rename(columns={
        'Data_Evento': 'Data',
        'Projecao': 'Valor_Projetado',
        'Valor_Bruto': 'Valor_Real'
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
            num_columns=["Valor_Projetado", 'Valor_Real', 'Desconto', 'Valor_Liquido'],     
            date_columns=['Data'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True   
        )
    
    st.divider()
    