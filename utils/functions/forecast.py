import streamlit as st
import pandas as pd
import numpy as np
import calendar
from datetime import timedelta
from utils.queries_cmv import *
from utils.queries_forecast import GET_VALORACAO_ESTOQUE, GET_VALORACAO_PRODUCAO
from utils.components import dataframe_aggrid
from st_aggrid import ColumnsAutoSizeMode


# Traduz dia da semana ou mês
def traduz_semana_mes(item, tipo):
    meses = {
        'January': 'Janeiro',
        'February': 'Fevereiro',
        'March': 'Março',
        'April': 'Abril',
        'May': 'Maio',
        'June': 'Junho',
        'July': 'Julho',
        'August': 'Agosto',
        'September': 'Setembro',
        'October': 'Outubro',
        'November': 'Novembro',
        'December': 'Dezembro'
    }

    dias_semana = {
        'Sunday': 'Domingo',
        'Monday': 'Segunda-feira',
        'Tuesday': 'Terça-feira',
        'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira',
        'Friday': 'Sexta-feira',
        'Saturday': 'Sábado'
    }

    if tipo == 'mes':
        return meses.get(item, item)  # Retorna o nome traduzido ou o original se não achar
    if tipo == 'dia semana':
        return dias_semana.get(item, item) 


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
            percent_columns=['Projeção Atingimento (%)'],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True   
        )
    
    st.divider()
    

########################### Funções - CMV ###########################
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

    #   df_compras = substituicao_ids(df_compras, 'Loja', 'ID_Loja')
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

    #   df_compras = filtrar_por_datas(df_compras, data_inicio, data_fim, 'Primeiro_Dia_Mes')

    Compras_Alimentos = df_compras['BlueMe_Sem_Pedido_Alimentos'].sum() + df_compras['BlueMe_Com_Pedido_Valor_Liq_Alimentos'].sum()
    Compras_Bebidas = df_compras['BlueMe_Sem_Pedido_Bebidas'].sum() + df_compras['BlueMe_Com_Pedido_Valor_Liq_Bebidas'].sum()

    Compras_Alimentos = float(Compras_Alimentos)
    Compras_Bebidas = float(Compras_Bebidas)

    #   df_compras = primeiro_dia_mes_para_mes_ano(df_compras)

    df_compras['Compras Alimentos'] = df_compras['BlueMe_Com_Pedido_Valor_Liq_Alimentos'] + df_compras['BlueMe_Sem_Pedido_Alimentos']
    df_compras['Compras Bebidas'] = df_compras['BlueMe_Com_Pedido_Valor_Liq_Bebidas'] + df_compras['BlueMe_Sem_Pedido_Bebidas']
    df_compras = df_compras.rename(columns={'ID_Loja': 'ID_Casa', 'Loja': 'Casa', 'BlueMe_Com_Pedido_Valor_Liq_Alimentos': 'BlueMe c/ Pedido Alim.', 'BlueMe_Com_Pedido_Valor_Liq_Bebidas': 'BlueMe c/ Pedido Bebidas', 'BlueMe_Sem_Pedido_Alimentos': 'BlueMe s/ Pedido Alim.', 'BlueMe_Sem_Pedido_Bebidas': 'BlueMe s/ Pedido Bebidas'})

    df_compras = df_compras[['ID_Casa', 'Casa', 'Mes_Ano', 'BlueMe c/ Pedido Alim.', 'BlueMe s/ Pedido Alim.', 'Compras Alimentos', 'BlueMe c/ Pedido Bebidas', 'BlueMe s/ Pedido Bebidas', 'Compras Bebidas']]
    
    # columns = ['BlueMe c/ Pedido Alim.', 'BlueMe s/ Pedido Alim.', 'Compras Alimentos', 'BlueMe c/ Pedido Bebidas', 'BlueMe s/ Pedido Bebidas', 'Compras Bebidas']
    #   df_compras = format_columns_brazilian(df_compras, columns)

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
    # df = filtrar_por_datas(df, data_inicio, data_fim, 'Data_Transferencia')
    
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

    # df_transf_e_gastos = format_columns_brazilian(df_transf_e_gastos, ['Entrada Alimentos', 'Entrada Bebidas', 'Saída Alimentos', 'Saída Bebidas', 'Consumo Interno', 'Quebras e Perdas'])

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
    
    df_valoracao = df_valoracao[df_valoracao['Loja'] == loja]
    
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
    
    return df_valoracao


# def config_valoracao_producao(data_inicio, data_fim, loja):
#     df_valoracao_producao = GET_VALORACAO_PRODUCAO(data_inicio, data_fim)

#     df_valoracao_producao = df_valoracao_producao[df_valoracao_producao['Loja'] == loja]
   
#     # Agrupar por mês, loja e categoria
#     df_valoracao_producao = (
#         df_valoracao_producao
#         .groupby(['Loja', 'Categoria', 'Data_Contagem'], as_index=False)
#         .agg({'Valor_Total': 'sum'})
#     )
    
#     # Criar todas as datas do período
#     todas_datas = pd.date_range(start=data_inicio, end=data_fim, freq='MS')
    
#     # Todas combinações de Loja, Categoria e DATA_CONTAGEM
#     lojas_categorias = df_valoracao_producao[['Loja', 'Categoria']].drop_duplicates()
#     todas_combinacoes = (
#         lojas_categorias
#         .merge(pd.DataFrame({'Data_Contagem': todas_datas}), how='cross')
#     )
    
#     # Merge com o dataframe real
#     df_valoracao_producao = todas_combinacoes.merge(
#         df_valoracao_producao,
#         on=['Loja', 'Categoria', 'Data_Contagem'],
#         how='left'
#     )
    
#     # Preencher valores ausentes com 0
#     df_valoracao_producao['Valor_Total'] = df_valoracao_producao['Valor_Total'].fillna(0)
    
#     # Calcular variação mensal
#     df_valoracao_producao['Variação_Mensal'] = (
#         df_valoracao_producao
#         .groupby(['Loja', 'Categoria'])['Valor_Total']
#         .diff()
#         .fillna(0)
#     )
    
#     # Coluna DATA_MES_ANTERIOR
#     df_valoracao_producao['DATA_MES_ANTERIOR'] = df_valoracao_producao['Data_Contagem'] - pd.DateOffset(months=1)
    
#     return df_valoracao_producao

