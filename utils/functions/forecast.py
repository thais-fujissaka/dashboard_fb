import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import timedelta
from utils.functions.general_functions_conciliacao import formata_df, traduz_semana_mes
from utils.queries_cmv import GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_SEM_PEDIDO, GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_COM_PEDIDO, GET_TRANSF_ESTOQUE, GET_PERDAS_E_CONSUMO_AGRUPADOS
from utils.queries_forecast import GET_VALORACAO_ESTOQUE, GET_VALORACAO_PRODUCAO, GET_EVENTOS_CMV
from utils.components import dataframe_aggrid
from st_aggrid import ColumnsAutoSizeMode

pd.set_option('future.no_silent_downcasting', True)

############################################ PROJEÇÕES MÊS CORRENTE ############################################

# Prepara df de faturamento agregado diário para a casa selecionada
def prepara_dados_faturam_agregado_diario(id_casa, df_faturamento_agregado_dia, inicio_do_mes_anterior, fim_do_mes_atual):
    df_faturamento_agregado_casa = df_faturamento_agregado_dia[df_faturamento_agregado_dia['ID_Casa'] == id_casa]
    df_faturamento_agregado_casa['Data_Evento'] = pd.to_datetime(df_faturamento_agregado_casa['Data_Evento'], errors='coerce')
    
    # Traduz dia da semana para português
    df_faturamento_agregado_casa['Dia Semana'] = df_faturamento_agregado_casa['Data_Evento'].dt.strftime('%A')
    df_faturamento_agregado_casa['Dia Semana'] = df_faturamento_agregado_casa['Dia Semana'].apply(
        lambda x: traduz_semana_mes(x, 'dia semana')
    )
    
    df_faturamento_agregado_casa['Dia_Mes'] = pd.to_datetime(df_faturamento_agregado_casa['Data_Evento'], errors='coerce').dt.day

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

    # Traduz dia da semana para português
    df_dias_mes_anterior['Dia Semana'] = df_dias_mes_anterior['Data_Evento'].dt.strftime('%A') 
    df_dias_mes_anterior['Dia Semana'] = df_dias_mes_anterior['Dia Semana'].apply(
        lambda x: traduz_semana_mes(x, 'dia semana')
    )

    # Cria DataFrame para o mês atual
    df_dias_mes_corrente = pd.DataFrame({'Dia_Mes': lista_dias_mes_corrente})
    df_dias_mes_corrente['Data_Evento'] = pd.to_datetime({
        'year': ano_atual,
        'month': mes_atual,
        'day': df_dias_mes_corrente['Dia_Mes']
    })

    # Traduz dia da semana para português usando sua função
    df_dias_mes_corrente['Dia Semana'] = df_dias_mes_corrente['Data_Evento'].dt.strftime('%A')
    df_dias_mes_corrente['Dia Semana'] = df_dias_mes_corrente['Dia Semana'].apply(
        lambda x: traduz_semana_mes(x, 'dia semana')
    )

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


# Exibe projeção por categoria (A&B, delivery, gifts e couvert) - mês corrente
def exibe_faturamento_categoria(categoria, df_dias_futuros_mes, today):
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
        'Projecao': 'Valor Projetado (R$)',
        'Valor_Bruto': 'Valor Real'
    })

    # Exibe titulo
    st.markdown(f'''
            <h4 style="color: #1f77b4;">{titulo}</h4>
        ''', unsafe_allow_html=True)
    
    if df_projecao_faturamento_categoria.empty:
        st.info('Não há dados de faturamento para essa categoria.')

    else: # Exibe df com aggrid
        dataframe_aggrid(
            df=df_projecao_faturamento_categoria,
            name=f"Projeção - {titulo}",
            num_columns=["Valor Projetado (R$)", 'Valor Real', 'Desconto', 'Valor_Liquido'],     
            date_columns=['Data'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True,
        )
    
    st.divider()


# Exibe projeção de Eventos - mês corrente
def exibe_faturamento_eventos(df_faturamento_eventos, id_casa, datas):
    st.markdown(f'''
            <h4 style="color: #1f77b4;">Eventos</h4>
            <p><strong>Premissa:</strong> considerar o que está lançado para a competência nesse mês</p>        
        ''', unsafe_allow_html=True)

    df_faturamento_eventos_futuros = df_faturamento_eventos[
        (df_faturamento_eventos['ID_Casa'] == id_casa) &
        (df_faturamento_eventos['Data_Evento'] >= datas['amanha']) &
        (df_faturamento_eventos['Data_Evento'] <= datas['fim_mes_atual']) 
    ]

    df_faturamento_eventos_futuros = df_faturamento_eventos_futuros[['Categoria', 'Data_Evento', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]
    df_faturamento_eventos_futuros = df_faturamento_eventos_futuros.rename(columns={
        'Data_Evento':'Data Evento',
        'Valor_Bruto':'Valor Bruto (R$)',
        'Desconto':'Desconto (R$)',
        'Valor_Liquido':'Valor Liquido (R$)'
    })
    
    if not df_faturamento_eventos_futuros.empty:
        dataframe_aggrid(
            df=df_faturamento_eventos_futuros,
            name=f"Projeção - Faturamento Eventos",
            num_columns=['Valor Bruto (R$)', 'Desconto (R$)', 'Valor Liquido (R$)'],     
            date_columns=['Data Evento'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True,
        )
    else:
        st.info(f"Não há informações de eventos para os próximos dias de {datas['nome_mes_atual_pt']}.")
    st.divider()


# Exibe projeção de Outras Receitas - mês corrente
def exibe_faturamento_outras_receitas(df_parc_receit_extr_dia, df_parc_receitas_extr, id_casa, datas):
    st.markdown(f'''
            <h4 style="color: #1f77b4;">Outras Receitas</h4>
            <p><strong>Premissa:</strong> considerar o que está lançado para a competência nesse mês</p>
        ''', unsafe_allow_html=True)

    # Filtra por casa e dias futuros
    df_parc_receitas_extr_futuras = df_parc_receit_extr_dia[
        (df_parc_receit_extr_dia['ID_Casa'] == id_casa) &
        (df_parc_receit_extr_dia['Data_Evento'] >= datas['amanha']) &
        (df_parc_receit_extr_dia['Data_Evento'] <= datas['fim_mes_atual']) 
    ]

    if not df_parc_receitas_extr_futuras.empty:
        # Merge para exibir categorias específicas no expander
        df_detalha_outras_receitas = df_parc_receitas_extr_futuras.merge(
            df_parc_receitas_extr,
            how='left',
            left_on=['Casa', 'Data_Evento'],
            right_on=['Casa', 'Data_Ocorrencia']
        )
        df_detalha_outras_receitas = df_detalha_outras_receitas[['Categoria_x', 'Data_Ocorrencia', 'Categoria_y', 'Valor_Parcela']]
        df_detalha_outras_receitas = df_detalha_outras_receitas.rename(columns={'Categoria_y':'Classificacao_Receita', 'Categoria_x':'Categoria'})

        # Exibe df de 'Outras Receitas'
        df_parc_receitas_extr_futuras = df_parc_receitas_extr_futuras[['Categoria', 'Data_Evento', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]
        df_parc_receitas_extr_futuras = df_parc_receitas_extr_futuras.rename(columns={
            'Data_Evento':'Data Evento',
            'Valor_Bruto':'Valor Bruto (R$)',
            'Desconto':'Desconto (R$)',
            'Valor_Liquido':'Valor Liquido (R$)'
        })
        
        dataframe_aggrid(
            df=df_parc_receitas_extr_futuras,
            name=f"Projeção - Faturamento Outras Receitas",
            num_columns=['Valor Bruto (R$)', 'Desconto (R$)', 'Valor Liquido (R$)'],     
            date_columns=['Data_Evento'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True,   
        )

        with st.expander('Detalhamento', icon=":material/chevron_right:"):
            df_detalha_outras_receitas_fmt = formata_df(df_detalha_outras_receitas)
            st.dataframe(df_detalha_outras_receitas_fmt, hide_index=True)
        
    else:
        st.info(f"Não há informações de receitas extraordinárias para os próximos dias de {datas['nome_mes_atual_pt']}.")


# Exibe dias anteriores do mês corrente - para comparação projeção/real
def exibe_faturamento_dias_anteriores(df_dias_futuros_mes, datas):
 
    # Filtra para exibir dias anteriores do mês corrente - para comparação projeção/real
    df_faturamento_dias_anteriores = df_dias_futuros_mes[
        (df_dias_futuros_mes['Data_Evento'] >= datas['inicio_mes_atual']) &
        (df_dias_futuros_mes['Data_Evento'] <= datas['today']) &
        (df_dias_futuros_mes['Categoria'] != 'Serviço')
    ]
    
    # Organiza colunas
    df_faturamento_dias_anteriores = df_faturamento_dias_anteriores[['Categoria', 'Data_Evento', 'Dia Semana', 'Projecao', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]
    df_faturamento_dias_anteriores = df_faturamento_dias_anteriores.sort_values(by=['Categoria', 'Data_Evento'])
    df_faturamento_dias_anteriores = df_faturamento_dias_anteriores.rename(
        columns={'Data_Evento':'Data Evento',
                'Projecao':'Faturamento Projetado (R$)', 
                'Valor_Bruto':'Faturamento Real (R$)',
                'Desconto':'Desconto (R$)',
                'Valor_Liquido':'Faturamento Liquido (R$)'})

    st.markdown(f'''
        <h4>Dias anteriores - {datas['inicio_mes_atual'].strftime('%d/%m/%y')} a {datas['today'].strftime('%d/%m/%y')}</h4>
        <h5>Comparação: Faturamento Projetado e Faturamento Real</h5>
    ''', unsafe_allow_html=True)

    dataframe_aggrid(
        df=df_faturamento_dias_anteriores,
        name=f"Projeção - Faturamento Dias Anteriores",
        num_columns=['Faturamento Projetado (R$)', 'Faturamento Real (R$)', 'Desconto (R$)', 'Faturamento Liquido (R$)'],     
        date_columns=['Data Evento'],
        fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        fit_columns_on_grid_load=True,
    )

############################################ PROJEÇÕES PRÓXIMOS MESES ############################################

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

    df_faturamento_mes_casa = df_faturamento_mes_casa.groupby(['ID_Casa', 'Casa', 'Categoria', 'Ano', 'Mes'], as_index=False)[['Valor_Bruto', 'Desconto', 'Valor_Liquido']].sum()

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
        'Mes':'Mês',
        'Orcamento_Faturamento': 'Orçamento (R$)',
        'Projecao_Atingimento (%)':'Projeção Atingimento (%)',
        'Valor Projetado':'Valor Projetado (R$)'
    })

    # Exibe titulo
    st.markdown(f'''
            <h4 style="color: #1f77b4;">{titulo}</h4>
        ''', unsafe_allow_html=True)
    
    if df_projecao_faturamento_categoria_prox_meses.empty:
        st.info('Não há dados de faturamento para essa categoria.')

    else: # Exibe df com aggrid
        dataframe_aggrid(
            df=df_projecao_faturamento_categoria_prox_meses,
            name=f"Projeção próximos meses - {titulo}",
            num_columns=['Orçamento (R$)', 'Valor Projetado (R$)'],     
            percent_columns=['Projeção Atingimento (%)'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True,
        )
    
    if titulo != 'Outras Receitas':
        st.divider()


# Exibe meses anteriores - para comparação projeção/real
def exibe_faturamento_meses_anteriores(df_faturamento_meses_futuros, datas):
    st.markdown(f'''
            <h4>Meses anteriores</h4>
            <h5>Comparação Faturamento: Atingimento Projetado e Atingimento Real</h5>
        ''', unsafe_allow_html=True)
    
    df_faturamento_meses_anteriores = df_faturamento_meses_futuros.copy()
    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores[
        (df_faturamento_meses_anteriores['Ano'] == datas['ano_atual']) &
        (df_faturamento_meses_anteriores['Mes'] <= datas['mes_atual']) &
        (df_faturamento_meses_anteriores['Categoria'] != 'Serviço')
    ]

    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores[['Categoria', 'Mes', 'Orcamento_Faturamento', 'Valor_Bruto', 'Atingimento Real (%)', 'Projecao_Atingimento (%)', 'Valor Projetado']]
    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores.rename(columns={
        'Mes':'Mês',
        'Orcamento_Faturamento':'Orçamento (R$)',
        'Valor_Bruto':'Faturamento Real (R$)',
        'Projecao_Atingimento (%)':'Atingimento Projetado (%)',
        'Valor Projetado':'Faturamento Projetado (R$)'
    })
    df_faturamento_meses_anteriores = df_faturamento_meses_anteriores.sort_values(by=['Categoria', 'Mês'])

    dataframe_aggrid(
        df=df_faturamento_meses_anteriores,
        name=f"Projeção - Faturamento Meses Anteriores",
        num_columns=['Orçamento (R$)', 'Faturamento Real (R$)', 'Faturamento Projetado (R$)'],     
        percent_columns=['Atingimento Real (%)', 'Atingimento Projetado (%)'],
        fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        fit_columns_on_grid_load=True,
    )
    st.divider()
    
############################################ PROJEÇÃO CMV - PRÓXIMOS MESES ############################################

def config_faturamento_bruto_zig(df, data_inicio, data_fim, casa):
    df['Valor_Bruto'] = df['Valor_Bruto'].astype(float)
    df['Data_Evento'] = pd.to_datetime(df['Data_Evento'], errors='coerce')
    df['Mes_Ano'] = df['Data_Evento'].dt.strftime('%Y-%m')
    df = df[
        df['Categoria'].isin(['Alimentos', 'Bebidas', 'Delivery']) &
        (df['Casa'] == casa) &
        (df['Data_Evento'] >= data_inicio) &
        (df['Data_Evento'] <= data_fim)
    ]

    df = df.groupby(['ID_Casa', 'Casa', 'Mes_Ano', 'Categoria']).agg({
        'Valor_Bruto': 'sum',
        'Desconto': 'sum',
        'Valor_Liquido': 'sum',
        'Data_Evento': 'first'
    }).reset_index()

    faturamento_bruto_alimentos = df[(df['Categoria'] == 'Alimentos')]['Valor_Bruto'].sum()
    faturamento_bruto_bebidas = df[(df['Categoria'] == 'Bebidas')]['Valor_Bruto'].sum()
    faturamento_delivery = df[(df['Categoria'] == 'Delivery')]['Valor_Bruto'].sum()

    return df, faturamento_bruto_alimentos, faturamento_bruto_bebidas, faturamento_delivery


def config_compras(data_inicio, data_fim, loja):
    df1 = GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_SEM_PEDIDO()  
    df2 = GET_INSUMOS_AGRUPADOS_BLUE_ME_POR_CATEG_COM_PEDIDO()

    df_compras = pd.merge(df2, df1, on=['ID_Loja', 'Loja', 'Primeiro_Dia_Mes'], how='outer')

    df_compras['Primeiro_Dia_Mes'] = pd.to_datetime(df_compras['Primeiro_Dia_Mes'], errors='coerce')
    df_compras['Mes_Ano'] = df_compras['Primeiro_Dia_Mes'].dt.strftime('%Y-%m')
    df_compras = df_compras[
        (df_compras['Loja'] == loja) &
        (df_compras['Primeiro_Dia_Mes'] >= data_inicio) &
        (df_compras['Primeiro_Dia_Mes'] <= data_fim)
        ]

    
    df_compras = df_compras.groupby(['ID_Loja', 'Loja', 'Mes_Ano']).agg(
        {'BlueMe_Sem_Pedido_Alimentos': 'sum', 
        'BlueMe_Sem_Pedido_Bebidas': 'sum', 
        'BlueMe_Com_Pedido_Valor_Liq_Alimentos': 'sum', 
        'BlueMe_Com_Pedido_Valor_Liq_Bebidas': 'sum'}).reset_index()

    Compras_Alimentos = df_compras['BlueMe_Sem_Pedido_Alimentos'].sum() + df_compras['BlueMe_Com_Pedido_Valor_Liq_Alimentos'].sum()
    Compras_Bebidas = df_compras['BlueMe_Sem_Pedido_Bebidas'].sum() + df_compras['BlueMe_Com_Pedido_Valor_Liq_Bebidas'].sum()

    Compras_Alimentos = float(Compras_Alimentos)
    Compras_Bebidas = float(Compras_Bebidas)

    df_compras['Compras Alimentos'] = df_compras['BlueMe_Com_Pedido_Valor_Liq_Alimentos'] + df_compras['BlueMe_Sem_Pedido_Alimentos']
    df_compras['Compras Bebidas'] = df_compras['BlueMe_Com_Pedido_Valor_Liq_Bebidas'] + df_compras['BlueMe_Sem_Pedido_Bebidas']
    df_compras = df_compras.rename(columns={'ID_Loja': 'ID_Casa', 'Loja': 'Casa', 'BlueMe_Com_Pedido_Valor_Liq_Alimentos': 'BlueMe c/ Pedido Alim.', 'BlueMe_Com_Pedido_Valor_Liq_Bebidas': 'BlueMe c/ Pedido Bebidas', 'BlueMe_Sem_Pedido_Alimentos': 'BlueMe s/ Pedido Alim.', 'BlueMe_Sem_Pedido_Bebidas': 'BlueMe s/ Pedido Bebidas'})

    df_compras = df_compras[['ID_Casa', 'Casa', 'Mes_Ano', 'BlueMe c/ Pedido Alim.', 'BlueMe s/ Pedido Alim.', 'Compras Alimentos', 'BlueMe c/ Pedido Bebidas', 'BlueMe s/ Pedido Bebidas', 'Compras Bebidas']]
    
    return df_compras, Compras_Alimentos, Compras_Bebidas


def processar_transferencias(df, casa_col, loja, data_inicio, data_fim):
    # Filtrar pelo nome da loja e pelo intervalo de datas
    df['Data_Transferencia'] = pd.to_datetime(df['Data_Transferencia'], errors='coerce')
    df['Mes_Ano'] = df['Data_Transferencia'].dt.strftime('%Y-%m')
    df = df[
        (df[casa_col] == loja) &
        (df['Data_Transferencia'] >= data_inicio) &
        (df['Data_Transferencia'] <= data_fim)
    ]
    
    # Agrupar por casa e categoria, somando os valores
    df_grouped = df.groupby([casa_col, 'Categoria', 'Mes_Ano']).agg({
        'Valor_Transferencia': 'sum'
    }).reset_index()
    
    # Ajustar categoria para formato capitalizado
    df_grouped['Categoria'] = df_grouped['Categoria'].str.capitalize()
    
    # Pivotar para transformar categorias em colunas
    df_pivot = df_grouped.pivot_table(
        index=[casa_col, 'Mes_Ano'],
        columns='Categoria',
        values='Valor_Transferencia',
        fill_value=0
    ).reset_index()
    
    # Renomear colunas para refletir o tipo de operação
    operacao = 'Entrada' if casa_col == 'Casa_Entrada' else 'Saída'
    df_pivot.columns = [
        'Loja' if col == casa_col else col if col == 'Mes_Ano' else f'{operacao} {col}'
        for col in df_pivot.columns
    ]    
    return df_pivot

def config_transferencias_gastos(data_inicio, data_fim, loja):
    df_transf_estoque = GET_TRANSF_ESTOQUE()
    df_entradas_pivot = processar_transferencias(df_transf_estoque, 'Casa_Entrada', loja, data_inicio, data_fim)
    df_saidas_pivot = processar_transferencias(df_transf_estoque, 'Casa_Saida', loja, data_inicio, data_fim)
    
    df_perdas_e_consumo = GET_PERDAS_E_CONSUMO_AGRUPADOS()
    df_perdas_e_consumo['Primeiro_Dia_Mes'] = pd.to_datetime(df_perdas_e_consumo['Primeiro_Dia_Mes'], errors='coerce')
    df_perdas_e_consumo['Mes_Ano'] = df_perdas_e_consumo['Primeiro_Dia_Mes'].dt.strftime('%Y-%m')
    df_perdas_e_consumo = df_perdas_e_consumo[
        (df_perdas_e_consumo['Loja'] == loja) &
        (df_perdas_e_consumo['Primeiro_Dia_Mes'] >= data_inicio) &
        (df_perdas_e_consumo['Primeiro_Dia_Mes'] <= data_fim)
    ]
    df_perdas_e_consumo.fillna(0, inplace=True)

    df_transf_e_gastos = pd.merge(df_entradas_pivot, df_saidas_pivot, on=['Loja', 'Mes_Ano'], how='outer')
    df_transf_e_gastos = pd.merge(df_transf_e_gastos, df_perdas_e_consumo, on=['Loja', 'Mes_Ano'], how='outer')
    df_transf_e_gastos = df_transf_e_gastos.rename(columns={
        'ID_Loja': 'ID_Casa',
        'Loja': 'Casa',
        'Consumo_Interno': 'Consumo Interno',
        'Quebras_e_Perdas': 'Quebras e Perdas'
    })
    cols = ['ID_Casa', 'Casa', 'Mes_Ano', 'Entrada Alimentos', 'Entrada Bebidas', 'Saída Alimentos', 'Saída Bebidas', 'Consumo Interno', 'Quebras e Perdas']
    for col in cols:
        if col not in df_transf_e_gastos.columns:
            df_transf_e_gastos[col] = 0

    df_transf_e_gastos = df_transf_e_gastos[cols]

    # Conversão para float para evitar erros de tipo
    saida_alimentos = float(df_saidas_pivot['Saída Alimentos'].iloc[0]) if not df_saidas_pivot.empty and 'Saída Alimentos' in df_saidas_pivot.columns else 0.0
    saida_bebidas = float(df_saidas_pivot['Saída Bebidas'].iloc[0]) if not df_saidas_pivot.empty and 'Saída Bebidas' in df_saidas_pivot.columns else 0.0
    entrada_alimentos = float(df_entradas_pivot['Entrada Alimentos'].iloc[0]) if not df_entradas_pivot.empty and 'Entrada Alimentos' in df_entradas_pivot.columns else 0.0
    entrada_bebidas = float(df_entradas_pivot['Entrada Bebidas'].iloc[0]) if not df_entradas_pivot.empty and 'Entrada Bebidas' in df_entradas_pivot.columns else 0.0
    consumo_interno = float(df_transf_e_gastos['Consumo Interno'].iloc[0]) if not df_perdas_e_consumo.empty and 'Consumo Interno' in df_transf_e_gastos.columns else 0.0
    quebras_e_perdas = float(df_transf_e_gastos['Quebras e Perdas'].iloc[0]) if not df_perdas_e_consumo.empty and 'Quebras e Perdas' in df_transf_e_gastos.columns else 0.0

    return df_transf_e_gastos, saida_alimentos, saida_bebidas, entrada_alimentos, entrada_bebidas, consumo_interno, quebras_e_perdas


def config_valoracao_estoque_ou_producao(tipo, data_inicio, data_fim, loja):
    # Pega os dados
    if tipo == 'estoque':
        df_valoracao = GET_VALORACAO_ESTOQUE(data_inicio, data_fim)
        col_data = 'DATA_CONTAGEM'
        col_valor = 'Valor_em_Estoque'
    if tipo == 'producao':
        df_valoracao = GET_VALORACAO_PRODUCAO(data_inicio, data_fim)
        col_data = 'Data_Contagem'
        col_valor = 'Valor_Total'
    
    df_valoracao = df_valoracao[
       (df_valoracao['Loja'] == loja) &
       (df_valoracao['Categoria'].isin(['ALIMENTOS', 'BEBIDAS']))
    ]
    
    # Agrupar por mês, loja e categoria
    df_valoracao = (
        df_valoracao
        .groupby(['Loja', 'Categoria', col_data], as_index=False)
        .agg({col_valor: 'sum'})
    )
    
    # Criar todas as datas do período
    todas_datas = pd.date_range(start=data_inicio, end=data_fim, freq='MS')
    
    # Todas combinações de Loja, Categoria e DATA_CONTAGEM
    lojas_categorias = df_valoracao[['Loja', 'Categoria']].drop_duplicates()
    todas_combinacoes = (
        lojas_categorias
        .merge(pd.DataFrame({col_data: todas_datas}), how='cross')
    )
    
    # Merge com o dataframe real
    df_valoracao = todas_combinacoes.merge(
        df_valoracao,
        on=['Loja', 'Categoria', col_data],
        how='left'
    )
    
    # Preencher valores ausentes com 0
    df_valoracao[col_valor] = df_valoracao[col_valor].fillna(0)
    
    # Calcular variação mensal
    df_valoracao['Variação_Mensal'] = (
        df_valoracao
        .groupby(['Loja', 'Categoria'])[col_valor]
        .diff()
        .fillna(0)
    )
    
    # Coluna DATA_MES_ANTERIOR
    df_valoracao['DATA_MES_ANTERIOR'] = df_valoracao[col_data] - pd.DateOffset(months=1)
    df_valoracao['Mes_Ano'] = df_valoracao['DATA_MES_ANTERIOR'].dt.strftime("%Y-%m")
    df_valoracao = df_valoracao.rename(columns={'Loja': 'Casa'})

    return df_valoracao


def config_faturamento_eventos(data_inicio, data_fim, loja, faturamento_bruto_alimentos, faturamento_bruto_bebidas):
    df_eventos = GET_EVENTOS_CMV(data_inicio=data_inicio, data_fim=data_fim)
    
    df_eventos = df_eventos[df_eventos['Loja'] == loja]
    df_eventos['Valor_AB'] = df_eventos['Valor_AB'].astype(float)
    df_eventos['Mes_Ano'] = df_eventos['Data'].dt.strftime('%Y-%m')
    df_eventos = df_eventos.rename(columns={'ID_Loja': 'ID_Casa', 'Loja': 'Casa'})

    # faturmento_total_zig = faturamento_bruto_alimentos + faturamento_bruto_bebidas
    # faturamento_total_eventos = df['Valor_AB'].sum()

    # faturamento_alimentos_eventos = (faturamento_bruto_alimentos * faturamento_total_eventos) / faturmento_total_zig
    # faturamento_bebidas_eventos = (faturamento_bruto_bebidas * faturamento_total_eventos) / faturmento_total_zig

    return df_eventos


def merge_e_calculo_para_cmv(df_faturamento_zig, df_compras, df_valoracao_estoque, df_transf_e_gastos, df_valoracao_producao, df_faturamento_eventos):
    # Faturamento Bruto (alimentos + bebidas + delivery) mensal
    df_faturamento_zig_geral = df_faturamento_zig.copy()
    df_faturamento_zig_geral = df_faturamento_zig_geral.groupby(['ID_Casa', 'Casa', 'Mes_Ano'], as_index=False)['Valor_Bruto'].sum()
    df_faturamento_zig_geral = df_faturamento_zig_geral.rename(columns={'Valor_Bruto':'Faturamento Bruto'})

    # Compras (alimentos + bebidas) mensais
    df_compras_geral = df_compras.copy()
    df_compras_geral['Compras Geral'] = df_compras_geral['Compras Alimentos'] + df_compras_geral['Compras Bebidas']
    df_compras_geral = df_compras_geral[['ID_Casa', 'Casa', 'Mes_Ano', 'Compras Geral']]

    # Valoração estoque (alimentos + bebidas) mensal
    df_valoracao_estoque_geral = df_valoracao_estoque.copy()
    df_valoracao_estoque_geral = df_valoracao_estoque_geral.groupby(['Casa', 'Mes_Ano'], as_index=False)['Variação_Mensal'].sum()

    # Transferências e gastos (entrada alimentos + bebidas, saidas alimentos + bebidas, consumo interno, quebras e perdas)
    df_transf_e_gastos_geral = df_transf_e_gastos.copy()
    df_transf_e_gastos_geral['Entradas Geral'] = df_transf_e_gastos_geral['Entrada Alimentos'] + df_transf_e_gastos_geral['Entrada Bebidas']
    df_transf_e_gastos_geral['Saídas Geral'] = df_transf_e_gastos_geral['Saída Alimentos'] + df_transf_e_gastos_geral['Saída Bebidas']
    df_transf_e_gastos_geral = df_transf_e_gastos_geral[['ID_Casa', 'Casa', 'Mes_Ano', 'Entradas Geral', 'Saídas Geral', 'Consumo Interno', 'Quebras e Perdas']]

    # Valoração produção (alimentos + bebidas) mensal
    df_valoracao_producao_geral = df_valoracao_producao.copy()
    df_valoracao_producao_geral = df_valoracao_producao_geral.groupby(['Casa', 'Mes_Ano'], as_index=False)['Variação_Mensal'].sum()

    # Faturamento eventos (A&B) mensal
    df_faturamento_eventos_geral = df_faturamento_eventos.copy()
    df_faturamento_eventos_geral = df_faturamento_eventos_geral.groupby(['ID_Casa', 'Casa', 'Mes_Ano'], as_index=False)['Valor_AB'].sum()

    # Merge passo a passo para cálculo do cmv
    df_cmv = (
        df_compras_geral
            .merge(df_valoracao_estoque_geral, on=['Casa', 'Mes_Ano'], how='left')
            .merge(df_transf_e_gastos_geral, on=['Casa', 'Mes_Ano'], how='left')
            .merge(df_valoracao_producao_geral, on=['Casa', 'Mes_Ano'], how='left')
    ).fillna(0)
    df_cmv = df_cmv.rename(columns={'Variação_Mensal_x':'Variacao_Estoque', 'Variação_Mensal_y':'Variacao_Producao'})
    
    # Fauramento geral (bruto + eventos)
    df_merge_faturamento = df_faturamento_zig_geral.merge(
        df_faturamento_eventos_geral,
        on=['Casa', 'Mes_Ano'],
        how='left'
    ).fillna(0)
    df_merge_faturamento['Faturamento_Geral'] = df_merge_faturamento['Faturamento Bruto'] + df_merge_faturamento['Valor_AB']
    
    df_merge_cmv = pd.merge(
        df_cmv[['Casa', 'Mes_Ano', 'Compras Geral', 'Variacao_Estoque', 'Entradas Geral', 'Saídas Geral', 'Consumo Interno', 'Quebras e Perdas', 'Variacao_Producao']],
        df_merge_faturamento[['Casa', 'Mes_Ano', 'Faturamento_Geral']],
        on=['Casa', 'Mes_Ano'],
        how='left'
    )

    # Cálculo do cmv e porcentagem cmv
    df_calculo_cmv = df_merge_cmv.copy()
    df_calculo_cmv['Compras Geral'] = df_calculo_cmv['Compras Geral'].astype(float)
    df_calculo_cmv['Variacao_Estoque'] = df_calculo_cmv['Variacao_Estoque'].astype(float)
    df_calculo_cmv['Entradas Geral'] = df_calculo_cmv['Entradas Geral'].astype(float)
    df_calculo_cmv['Saídas Geral'] = df_calculo_cmv['Saídas Geral'].astype(float)
    df_calculo_cmv['Consumo Interno'] = df_calculo_cmv['Consumo Interno'].astype(float)
    df_calculo_cmv['Variacao_Producao'] = df_calculo_cmv['Variacao_Producao'].astype(float)

    df_calculo_cmv['CMV (R$)'] = df_calculo_cmv['Compras Geral'] - df_calculo_cmv['Variacao_Estoque'] + df_calculo_cmv['Entradas Geral'] - df_calculo_cmv['Saídas Geral'] - df_calculo_cmv['Consumo Interno'] - df_calculo_cmv['Variacao_Producao']
    df_calculo_cmv['CMV Percentual (%)'] = (df_calculo_cmv['CMV (R$)'] / df_calculo_cmv['Faturamento_Geral']) * 100
    df_calculo_cmv = df_calculo_cmv[['Casa', 'Mes_Ano', 'Faturamento_Geral', 'CMV (R$)', 'CMV Percentual (%)']]

    return df_calculo_cmv


# Utiliza o df de faturamento projetado criado anteriormente (para projetar o cmv para os prox meses)
def calcula_cmv_proximos_meses(df_faturamento_meses_futuros, datas, df_calculo_cmv):
    df_resgata_faturamento_meses_futuros = df_faturamento_meses_futuros[
        (df_faturamento_meses_futuros['Ano'] == datas['ano_atual']) &
        (df_faturamento_meses_futuros['Categoria'].isin(['Alimentos', 'Bebidas', 'Delivery', 'Eventos A&B']))
    ]

    df_resgata_faturamento_meses_futuros = df_resgata_faturamento_meses_futuros.groupby(['Ano', 'Mes'], as_index=False)[['Valor_Bruto', 'Valor Projetado']].sum()
    df_resgata_faturamento_meses_futuros['Mes'] = df_resgata_faturamento_meses_futuros['Mes'].astype(int)
    df_resgata_faturamento_meses_futuros['Mes_Ano'] = df_resgata_faturamento_meses_futuros['Ano'].astype(str) + '-' + df_resgata_faturamento_meses_futuros['Mes'].astype(str).str.zfill(2)
    
    df_merge_meses_anteriores_seguintes = pd.merge(
        df_calculo_cmv,
        df_resgata_faturamento_meses_futuros[['Ano', 'Mes', 'Mes_Ano', 'Valor Projetado']],
        on='Mes_Ano',
        how='right'
    )

    # Cria coluna para CMV projetado de cada mês
    df_merge_meses_anteriores_seguintes['Data'] = pd.to_datetime(df_merge_meses_anteriores_seguintes['Mes_Ano'], format='%Y-%m')
    df_merge_meses_anteriores_seguintes['CMV Percentual Projetado (%)'] = None
    df_merge_meses_anteriores_seguintes['CMV Projetado (R$)'] = None

    # 
    for mes_ano in df_merge_meses_anteriores_seguintes['Mes_Ano'].unique():
        df_mes_ano = df_merge_meses_anteriores_seguintes[df_merge_meses_anteriores_seguintes['Mes_Ano'] == mes_ano]
        data = df_mes_ano['Data'].iloc[0]

        # pega histórico dos dois meses atrás
        dois_meses_atras = data - pd.DateOffset(months=2)

        historico = df_merge_meses_anteriores_seguintes[
            (df_merge_meses_anteriores_seguintes['Data'] >= dois_meses_atras) &
            (df_merge_meses_anteriores_seguintes['Data'] < data)
        ]

        # Faz Projecao = (CMV1 + CMV2) / (Faturamento_Geral1 + Faturamento_Geral2)
        # Define colunas auxiliares conforme o mês
        historico["CMV_Usado"] = np.where(
            historico["Mes"] >= datas["mes_atual"],
            historico["CMV Projetado (R$)"],       # usa o projetado se mês >= atual
            historico["CMV (R$)"]                  # senão usa o real
        )

        historico["Faturamento_Usado"] = np.where(
            historico["Mes"] >= datas["mes_atual"],
            historico["Valor Projetado"],          # usa o projetado se mês >= atual
            historico["Faturamento_Geral"]         # senão usa o real
        )

        valores_para_soma_cmvs = historico['CMV_Usado'].fillna(historico['CMV Projetado (R$)']).astype(float)
        valores_para_soma_faturamento = historico['Faturamento_Usado'].fillna(historico['Valor Projetado']).astype(float)

        soma_cmvs = valores_para_soma_cmvs.sum()
        soma_faturamentos = valores_para_soma_faturamento.sum()
        
        if soma_faturamentos and not pd.isna(soma_faturamentos) and soma_faturamentos != 0:
            cmv_projetado = (soma_cmvs / soma_faturamentos) * 100
        else:
            cmv_projetado = 0 

        # Atribui o valor à coluna correta
        df_merge_meses_anteriores_seguintes.loc[
            df_merge_meses_anteriores_seguintes['Mes_Ano'] == mes_ano, 
            'CMV Percentual Projetado (%)'
        ] = cmv_projetado

        # Define valor de CMV Projetado em Reais
        df_merge_meses_anteriores_seguintes['CMV Projetado (R$)'] = (df_merge_meses_anteriores_seguintes['CMV Percentual Projetado (%)'] / 100) * df_merge_meses_anteriores_seguintes['Valor Projetado']

    return df_merge_meses_anteriores_seguintes