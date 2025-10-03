import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import calendar
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.functions.general_functions_conciliacao import *
from utils.functions.fluxo_realizado import *
from utils.functions.general_functions import config_sidebar
from utils.components import dataframe_aggrid
from utils.queries_conciliacao import *


st.set_page_config(
    page_title="Fluxo Futuro",
    page_icon=":material/event_upcoming:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/event_upcoming: Fluxo Futuro")
st.divider()

# Recuperando dados
df_casas = GET_CASAS()
df_orcamentos = GET_ORCAMENTOS()
df_faturamento_agregado = GET_FATURAMENTO_AGREGADO()
df_parc_receit_extr = GET_PARCELAS_RECEIT_EXTR()
df_despesas_sem_parcelamento = GET_CUSTOS_BLUEME_SEM_PARC()
df_despesas_com_parcelamento = GET_CUSTOS_BLUEME_COM_PARC()
df_tipo_class_cont_2 = GET_TIPO_CLASS_CONT_2()


# Filtrando Data
today = datetime.datetime.now()
last_year = today.year - 1
jan_last_year = datetime.datetime(last_year, 1, 1)
jan_this_year = datetime.datetime(today.year, 1, 1)
last_day_of_month = calendar.monthrange(today.year, today.month)[1]
this_month_this_year = datetime.datetime(today.year, today.month, last_day_of_month)
dec_this_year = datetime.datetime(today.year, 12, 31)

# Calculando datas para o próximo mês até fim do ano
next_month = today.replace(day=1) + timedelta(days=32)
next_month = next_month.replace(day=1)
end_of_year = datetime.datetime(today.year, 12, 31)

## 5 meses atras
month_sub_3 = today.month - 3
year = today.year

if month_sub_3 <= 0:
    # Se o mês resultante for menor ou igual a 0, ajustamos o ano e corrigimos o mês
    month_sub_3 += 12
    year -= 1

start_of_three_months_ago = datetime.datetime(year, month_sub_3, 1)


# Filtrando por casa(s) e data
casas = df_casas['Casa'].tolist()

# Troca o valor na lista
casas = ["Todas as casas" if c == "All bar" else c for c in casas]


# Criando colunas para o seletor de casas e o botão
col_casas, col_botao = st.columns([4, 2])

with col_casas:
    # Usando session_state se disponível, senão usa o valor padrão
    default_casas = st.session_state.get('casas_selecionadas', [casas[1]] if casas else [])
    casas_selecionadas = st.multiselect("Casas", casas, default=default_casas, placeholder='Selecione casas', key="casas_multiselect")

with col_botao:
    st.markdown("<br>", unsafe_allow_html=True)  # para alinhar o botão com os widgets
    if st.button("🏢 Sem Sócios Externos", 
                 help="Seleciona automaticamente todas as casas que não possuem sócios externos (Bit_Socios_Externos = 0)", 
                 use_container_width=True):
        
        # Filtrando casas sem sócios externos
        casas_sem_socios_externos = df_casas[df_casas['Bit_Socios_Externos'] == 0]['Casa'].tolist()
        casas_sem_socios_externos = [c for c in casas_sem_socios_externos if c != 'All bar']

        # Atualizando o multiselect através do session_state
        st.session_state['casas_selecionadas'] = casas_sem_socios_externos

        # Limpando a chave do multiselect para forçar a atualização
        if 'casas_multiselect' in st.session_state:
            del st.session_state['casas_multiselect']
        st.rerun()
    
    # Mostrando informação sobre casas sem sócios externos
    total_casas_sem_socios = len(df_casas[df_casas['Bit_Socios_Externos'] == 0]) - 1
    st.caption(f"📊 {total_casas_sem_socios} casas sem sócios externos")

# Definindo um dicionário para mapear nomes de casas a IDs de casas
mapeamento_lojas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))

# Obtendo os IDs das casas selecionadas
ids_casas_selecionadas = []
for casa in casas_selecionadas:
    if casa == "Todas as casas":
        # pega todos os IDs exceto o "All bar"
        todas_ids = df_casas.loc[df_casas["Casa"] != "All bar", "ID_Casa"].tolist()
        ids_casas_selecionadas.extend(todas_ids)
    else:
        ids_casas_selecionadas.append(mapeamento_lojas[casa])
st.divider()

col_datas, col_botao_futuro = st.columns([4, 2])

with col_datas: 
    # Campos de seleção de data
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Data de início", 
            value=next_month, 
            min_value=jan_last_year, 
            max_value=dec_this_year, 
            format="DD/MM/YYYY",
            key='start_date')
    with col2:
        end_date = st.date_input(
            "Data de fim", 
            value=end_of_year, 
            min_value=jan_last_year, 
            max_value=dec_this_year, 
            format="DD/MM/YYYY",
            key='end_date')

    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

# with col_botao_futuro:
#     st.markdown("<br>", unsafe_allow_html=True)  # para alinhar o botão com os widgets
#     if st.button("📅 Próximo mês → Fim do ano", help="Define o período do primeiro dia do próximo mês até o último dia do ano atual", use_container_width=True):
#         # Limpa os widgets para recriar com novos valores
#         if "start_date" in st.session_state:
#             del st.session_state["start_date"]
#         if "end_date" in st.session_state:
#             del st.session_state["end_date"]

#         # Atualizando o date_input através do session_state
#         st.session_state['start_date'] = next_month
#         st.session_state['end_date'] = end_of_year
#         st.rerun()

if not casas_selecionadas:
    st.warning("Por favor, selecione pelo menos uma casa.")
    st.stop()

st.divider()

## Orçamentos
col1, col2 = st.columns([6, 1])
with col1:
    st.subheader("Orçamentos")

# Informando o período filtrado
# st.info(f"📅 **Período filtrado**: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")

# Convertendo Ano_Orcamento e Mes_Orcamento para formato de data
df_orcamentos['Data_Orcamento'] = pd.to_datetime(
    df_orcamentos['Ano_Orcamento'].astype(str) + '-' + 
    df_orcamentos['Mes_Orcamento'].astype(str).str.zfill(2) + '-01',
    format='%Y-%m-%d',
    errors='coerce'
)

# Selecionando colunas incluindo a nova Data_Orcamento
df_orcamentos = df_orcamentos[['ID_Orcamento','ID_Casa','Casa','Class_Cont_1','Class_Cont_2','Ano_Orcamento','Mes_Orcamento','Data_Orcamento','Valor_Orcamento','Tipo_Fluxo_Futuro']]

# Filtrando por casas selecionadas e período de data
df_orcamentos_filtrada = df_orcamentos[
    (df_orcamentos['ID_Casa'].isin(ids_casas_selecionadas)) &
    (df_orcamentos['Data_Orcamento'] >= start_date) &
    (df_orcamentos['Data_Orcamento'] <= end_date)
]

# Exibindo tabela de orçamentos
df_orcamentos_filtrada_aggrid, tam_df_orcamentos_filtrada_aggrid = dataframe_aggrid(
    df=df_orcamentos_filtrada,
    name="Orçamentos",
    num_columns=["Valor_Orcamento"],
    date_columns=['Data_Orcamento']
)

with col2:
    function_copy_dataframe_as_tsv(df_orcamentos_filtrada_aggrid)

st.divider()

## Faturamento Agregado
col1, col2 = st.columns([6, 1])
with col1:
    st.subheader("Faturamento Agregado")

df_faturamento_agregado['Ano_Mes'] = df_faturamento_agregado['Ano'].astype(str) + '-' + df_faturamento_agregado['Mes'].astype(str).str.zfill(2)

df_faturamento_agregado = df_faturamento_agregado[['ID_Faturam_Agregado', 'ID_Casa', 'Casa', 'Categoria', 'Ano_Mes', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]

df_faturamento_agregado_filtrada = df_faturamento_agregado[df_faturamento_agregado['ID_Casa'].isin(ids_casas_selecionadas)]

# Exibindo tabela de faturamento agregado
df_faturamento_agregado_aggrid, tam_df_faturamento_agregado_aggrid = dataframe_aggrid(
    df=df_faturamento_agregado_filtrada,
    name="Faturamento Agregado",
    num_columns=["Valor_Bruto", "Desconto", "Valor_Liquido"],
    
)

with col2:
    function_copy_dataframe_as_tsv(df_faturamento_agregado_aggrid)

st.divider()

# ===== CONFIGURAÇÃO DO FATOR DE AJUSTE =====
st.subheader("📅 Configuração do Fator de Ajuste")
# st.markdown("**Defina o período histórico para cálculo do fator de ajuste:**")

# Calculando datas padrão para o filtro
hoje = datetime.datetime.now()
data_limite_padrao = hoje.replace(day=1) - timedelta(days=1)  # Último dia do mês anterior
data_inicio_padrao = datetime.datetime(hoje.year, 1, 1)  # Primeiro dia do ano corrente

# Usando session_state se disponível, senão usa o valor padrão
default_fator_data = st.session_state.get('fator_ajuste_date_input', (data_inicio_padrao, data_limite_padrao))
fator_ajuste_date_input = st.date_input(
    "Período para cálculo do fator de ajuste:",
    value=default_fator_data,
    min_value=jan_last_year,
    max_value=data_limite_padrao,
    format="DD/MM/YYYY",
    key="fator_ajuste_date_input_widget",
    help="Selecione o período histórico que será usado para calcular o fator de ajuste baseado no desempenho orçado vs realizado."
)

# Atualizando session_state
st.session_state['fator_ajuste_date_input'] = fator_ajuste_date_input

# Convertendo para datetime se necessário
if isinstance(fator_ajuste_date_input, tuple):
    data_inicio_fator = fator_ajuste_date_input[0]
    data_fim_fator = fator_ajuste_date_input[1]
else:
    data_inicio_fator = fator_ajuste_date_input
    data_fim_fator = fator_ajuste_date_input

# st.info(f"📊 **Período selecionado para cálculo do fator**: {data_inicio_fator.strftime('%d/%m/%Y')} a {data_fim_fator.strftime('%d/%m/%Y')}")

# ===== ANÁLISE COMPARATIVA: ORÇADO vs REALIZADO =====
st.subheader("Análise Comparativa: Orçado vs Realizado")

# Mostrando o período usado para análise
if 'fator_ajuste_date_input' in st.session_state:
    fator_data = st.session_state['fator_ajuste_date_input']
    if isinstance(fator_data, tuple):
        if len(fator_data) >= 2:
            periodo_analise = f"{fator_data[0].strftime('%d/%m/%Y')} a {fator_data[1].strftime('%d/%m/%Y')}"
        elif len(fator_data) == 1:
            periodo_analise = fator_data[0].strftime('%d/%m/%Y')
        else:
            periodo_analise = "Período não definido"
    else:
        periodo_analise = fator_data.strftime('%d/%m/%Y')
    # st.info(f"📅 **Período de análise**: {periodo_analise}")

# Filtrando dados para análise comparativa usando o filtro de data personalizado
# Se o filtro de fator de ajuste não foi definido ainda, usar valores padrão
if 'fator_ajuste_date_input' not in st.session_state:
    hoje = datetime.datetime.now()
    data_limite_analise = hoje.replace(day=1) - timedelta(days=1)  # Último dia do mês anterior
    data_inicio_analise = data_limite_analise.replace(day=1) - timedelta(days=180)  # 6 meses atrás
else:
    fator_data = st.session_state['fator_ajuste_date_input']
    if isinstance(fator_data, tuple):
        data_inicio_analise = pd.to_datetime(fator_data[0])
        if len(fator_data) >= 2:
            data_limite_analise = pd.to_datetime(fator_data[1])
        else:
            data_limite_analise = data_inicio_analise  # Se só tem uma data, usar a mesma
    else:
        data_inicio_analise = pd.to_datetime(fator_data)
        data_limite_analise = pd.to_datetime(fator_data)

# Filtrando orçamentos para análise
df_orcamentos_analise = df_orcamentos[
    (df_orcamentos['ID_Casa'].isin(ids_casas_selecionadas)) &
    (df_orcamentos['Data_Orcamento'] >= data_inicio_analise) &
    (df_orcamentos['Data_Orcamento'] <= data_limite_analise) &
    (df_orcamentos['Class_Cont_1'] == 'Faturamento Bruto')
]

# Filtrando faturamento realizado para análise
df_faturamento_analise = df_faturamento_agregado[
    (df_faturamento_agregado['ID_Casa'].isin(ids_casas_selecionadas))
]

# Aplicando filtro de data ao faturamento realizado
# Convertendo Ano_Mes para datetime para comparação
df_faturamento_analise = df_faturamento_analise.copy()
df_faturamento_analise.loc[:, 'Data_Faturamento'] = pd.to_datetime(
    df_faturamento_analise['Ano_Mes'] + '-01'
)

# Filtrando por período selecionado
df_faturamento_analise = df_faturamento_analise[
    (df_faturamento_analise['Data_Faturamento'] >= data_inicio_analise) &
    (df_faturamento_analise['Data_Faturamento'] <= data_limite_analise)
]

if not df_orcamentos_analise.empty and not df_faturamento_analise.empty:
    # Agrupando orçamentos por mês
    orcamentos_mensais = df_orcamentos_analise.groupby(['Ano_Orcamento', 'Mes_Orcamento'])['Valor_Orcamento'].sum().reset_index()
    orcamentos_mensais['Data_Comparacao'] = pd.to_datetime(
        orcamentos_mensais['Ano_Orcamento'].astype(str) + '-' + 
        orcamentos_mensais['Mes_Orcamento'].astype(str).str.zfill(2) + '-01'
    )
    
    # Agrupando faturamento realizado por mês
    faturamento_mensais = df_faturamento_analise.groupby('Ano_Mes')['Valor_Bruto'].sum().reset_index()
    faturamento_mensais['Data_Comparacao'] = pd.to_datetime(
        faturamento_mensais['Ano_Mes'] + '-01'
    )
    
    # Merge dos dados para comparação
    df_comparacao = pd.merge(
        orcamentos_mensais[['Data_Comparacao', 'Valor_Orcamento']],
        faturamento_mensais[['Data_Comparacao', 'Valor_Bruto']],
        on='Data_Comparacao',
        how='outer'
    ).fillna(0)
    
    # Calculando diferenças e percentuais
    df_comparacao['Diferenca'] = df_comparacao['Valor_Bruto'] - df_comparacao['Valor_Orcamento']
    # Calculando percentual realizado evitando divisão por zero
    df_comparacao['Percentual_Realizado'] = df_comparacao.apply(
        lambda row: (row['Valor_Bruto'] / row['Valor_Orcamento'] * 100) if row['Valor_Orcamento'] != 0 else 0, 
        axis=1
    ).fillna(0)
    df_comparacao['Mes_Ano'] = df_comparacao['Data_Comparacao'].dt.strftime('%m/%Y')
    
    # Criando gráfico comparativo
    fig_comparacao = go.Figure()
    
    # Orçado (linha azul)
    fig_comparacao.add_trace(go.Scatter(
        x=df_comparacao['Mes_Ano'],
        y=df_comparacao['Valor_Orcamento'],
        mode='lines+markers',
        name='Orçado',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8)
    ))
    
    # Realizado (linha verde)
    fig_comparacao.add_trace(go.Scatter(
        x=df_comparacao['Mes_Ano'],
        y=df_comparacao['Valor_Bruto'],
        mode='lines+markers',
        name='Realizado',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8)
    ))
    
    # Configurando layout
    fig_comparacao.update_layout(
        title=f'Comparação Orçado vs Realizado - {", ".join(casas_selecionadas)}',
        xaxis_title="Mês/Ano",
        yaxis_title="Valor (R$)",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    fig_comparacao.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
    
    st.plotly_chart(fig_comparacao, use_container_width=True)

    st.divider()

    # Métricas de análise
    st.subheader(":material/heap_snapshot_large: Métricas de projeção")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_orcado = df_comparacao['Valor_Orcamento'].sum() if not df_comparacao.empty else 0
        st.metric("Total Orçado", f"R$ {total_orcado:,.2f}")
    
    with col2:
        total_realizado = df_comparacao['Valor_Bruto'].sum() if not df_comparacao.empty else 0
        st.metric("Total Realizado", f"R$ {total_realizado:,.2f}")
    
    with col3:
        diferenca_total = total_realizado - total_orcado
        st.metric("Diferença Total", f"R$ {diferenca_total:,.2f}", 
                    delta=f"{diferenca_total/total_orcado*100:.1f}%" if total_orcado > 0 else "N/A")
    
    with col4:
        percentual_medio = df_comparacao['Percentual_Realizado'].mean()
        percentual_medio_display = f"{percentual_medio:.1f}%" if not pd.isna(percentual_medio) else "N/A"
        st.metric("Realizado vs Orçado (%)", percentual_medio_display)
    
    st.divider()

    # Tabela detalhada de comparação
    col1, col2 = st.columns([6, 1])
    with col1:
        st.subheader("Detalhamento Mensal - Orçado vs Realizado")
    
    df_comparacao_display = df_comparacao[['Mes_Ano', 'Valor_Orcamento', 'Valor_Bruto', 'Diferenca', 'Percentual_Realizado']].copy()
    df_comparacao_display.columns = ['Mês/Ano', 'Orçado (R$)', 'Realizado (R$)', 'Diferença (R$)', 'Realizado/Orçado (%)']
    
    df_comparacao_aggrid, tam_df_comparacao_aggrid = dataframe_aggrid(
        df=df_comparacao_display,
        name="Comparação Orçado vs Realizado",
        num_columns=["Orçado (R$)", "Realizado (R$)", "Diferença (R$)"],
        percent_columns=["Realizado/Orçado (%)"]
    )
    
    with col2:
        function_copy_dataframe_as_tsv(df_comparacao_aggrid)

    st.divider()
    
    # ===== PROJEÇÃO DE RECEITAS DE PATROCÍNIOS =====
    st.subheader("🎯 Projeção de Receitas de Patrocínios")
    
    try:        
        # Debug: Verificando se o DataFrame existe e tem dados
        if df_parc_receit_extr is None or df_parc_receit_extr.empty:
            st.warning("⚠️ DataFrame de parcelas de receitas extraordinárias está vazio ou não disponível.")
            total_patrocinios = 0
            patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
        else:
            # Debug: Verificando colunas disponíveis
            colunas_necessarias = ['ID_Casa', 'Classif_Receita', 'Recebimento_Parcela', 'Vencimento_Parcela']
            colunas_faltantes = [col for col in colunas_necessarias if col not in df_parc_receit_extr.columns]
            if colunas_faltantes:
                st.error(f"❌ Colunas necessárias não encontradas: {colunas_faltantes}")
                st.write("Colunas disponíveis:", list(df_parc_receit_extr.columns))
                total_patrocinios = 0
                patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
            else:
                # Filtrando apenas patrocínios pendentes (Recebimento_Parcela nulo) 
                # e vencimento dentro do período futuro
                df_patrocinios_futuros = df_parc_receit_extr[
                    (df_parc_receit_extr['ID_Casa'].isin(ids_casas_selecionadas)) &
                    (df_parc_receit_extr['Classif_Receita'] == 'Patrocínio') &
                    (df_parc_receit_extr['Recebimento_Parcela'].isna()) &  # Parcelas não recebidas
                    (df_parc_receit_extr['Vencimento_Parcela'] >= start_date) &
                    (df_parc_receit_extr['Vencimento_Parcela'] <= end_date)
                ].copy()
                
                # Debug: Mostrando informações sobre o filtro
                st.caption(f"🔍 Filtros aplicados: Casas={len(ids_casas_selecionadas)}, Período={start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
                st.caption(f"📊 Total de registros encontrados: {len(df_patrocinios_futuros)}")
                
                # Debug adicional: Verificando se há patrocínios para as casas selecionadas
                total_patrocinios_casas = df_parc_receit_extr[
                    (df_parc_receit_extr['ID_Casa'].isin(ids_casas_selecionadas)) &
                    (df_parc_receit_extr['Classif_Receita'] == 'Patrocínio')
                ]
                st.caption(f"🔍 Total de patrocínios para as casas selecionadas: {len(total_patrocinios_casas)}")
                
                # Debug: Verificando patrocínios pendentes (sem filtro de data)
                patrocinios_pendentes = df_parc_receit_extr[
                    (df_parc_receit_extr['ID_Casa'].isin(ids_casas_selecionadas)) &
                    (df_parc_receit_extr['Classif_Receita'] == 'Patrocínio') &
                    (df_parc_receit_extr['Recebimento_Parcela'].isna())
                ]
                st.caption(f"🔍 Patrocínios pendentes (sem filtro de data): {len(patrocinios_pendentes)}")
                
                # Debug: Verificando patrocínios no período (sem filtro de recebimento)
                patrocinios_periodo = df_parc_receit_extr[
                    (df_parc_receit_extr['ID_Casa'].isin(ids_casas_selecionadas)) &
                    (df_parc_receit_extr['Classif_Receita'] == 'Patrocínio') &
                    (df_parc_receit_extr['Vencimento_Parcela'] >= start_date) &
                    (df_parc_receit_extr['Vencimento_Parcela'] <= end_date)
                ]
                st.caption(f"🔍 Patrocínios no período (sem filtro de recebimento): {len(patrocinios_periodo)}")
                
                if not df_patrocinios_futuros.empty:
                    # Verificando se há valores únicos na coluna Classif_Receita para debug
                    classificacoes_unicas = df_parc_receit_extr['Classif_Receita'].unique()
                    st.caption(f"🏷️ Classificações disponíveis: {list(classificacoes_unicas)}")
                    
                    # Preparando dados para exibição
                    df_patrocinios_exibicao = df_patrocinios_futuros[[
                        'ID_Receita', 'Casa', 'Cliente', 'Data_Ocorrencia', 
                        'Vencimento_Parcela', 'Valor_Parcela', 'Classif_Receita', 
                        'Status_Pgto', 'Observacoes'
                    ]].copy()
                    
                    # Formatando datas
                    df_patrocinios_exibicao['Data_Ocorrencia'] = df_patrocinios_exibicao['Data_Ocorrencia'].dt.strftime('%d/%m/%Y')
                    df_patrocinios_exibicao['Vencimento_Parcela'] = df_patrocinios_exibicao['Vencimento_Parcela'].dt.strftime('%d/%m/%Y')
                    
                    # Renomeando colunas para melhor visualização
                    df_patrocinios_exibicao = df_patrocinios_exibicao.rename(columns={
                        'ID_Receita': 'ID Receita',
                        'Cliente': 'Cliente',
                        'Data_Ocorrencia': 'Data Ocorrência',
                        'Vencimento_Parcela': 'Vencimento Parcela',
                        'Valor_Parcela': 'Valor Parcela (R$)',
                        'Classif_Receita': 'Classificação',
                        'Status_Pgto': 'Status Pagamento',
                        'Observacoes': 'Observações'
                    })
                    
                    # Ordenando por vencimento
                    df_patrocinios_exibicao = df_patrocinios_exibicao.sort_values('Vencimento Parcela')
                    
                    # Exibindo tabela de patrocínios futuros
                    df_patrocinios_aggrid, tam_df_patrocinios_aggrid = dataframe_aggrid(
                        df=df_patrocinios_exibicao,
                        name="Projeção de Receitas de Patrocínios",
                        num_columns=["Valor Parcela (R$)"],
                        date_columns=[]
                    )
                    
                    col1, col2 = st.columns([6, 1])
                    with col1: # Calculando total dos valores filtrados
                        total_valores_filtrados(df_patrocinios_aggrid, tam_df_patrocinios_aggrid, "Valor Parcela (R$)", despesa_com_parc=False)
                    with col2:
                        function_copy_dataframe_as_tsv(df_patrocinios_aggrid)
                    

                    # Agrupando patrocínios por mês para uso nas projeções
                    df_patrocinios_futuros['Mes_Ano'] = df_patrocinios_futuros['Vencimento_Parcela'].dt.strftime('%m/%Y')
                    # Convertendo Valor_Parcela para float para evitar problemas com Decimal
                    df_patrocinios_futuros['Valor_Parcela_Float'] = df_patrocinios_futuros['Valor_Parcela'].astype(float)
                    patrocinios_mensais = df_patrocinios_futuros.groupby('Mes_Ano')['Valor_Parcela_Float'].sum().reset_index()
                    patrocinios_mensais = patrocinios_mensais.rename(columns={'Valor_Parcela_Float': 'Valor_Parcela'})
                    patrocinios_mensais['Mes_Ano_Display'] = patrocinios_mensais['Mes_Ano']
                    
                    # Debug: Mostrando informações sobre o agrupamento
                    st.caption(f"🔍 Patrocínios agrupados por mês: {len(patrocinios_mensais)} meses")
                    if not patrocinios_mensais.empty:
                        st.caption(f"🔍 Meses com patrocínios: {list(patrocinios_mensais['Mes_Ano_Display'])}")
                        st.caption(f"🔍 Total de patrocínios agrupados: R$ {patrocinios_mensais['Valor_Parcela'].astype(float).sum():,.2f}")
                    
                else:
                    st.info("Não há receitas de patrocínios pendentes para o período selecionado.")
                    total_patrocinios = 0
                    patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
                    
    except Exception as e:
        st.error(f"❌ Erro ao processar projeção de patrocínios: {str(e)}")
        st.exception(e)
        total_patrocinios = 0
        patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
    
    # ===== PROJEÇÃO AJUSTADA =====
    st.subheader("🔮 Projeção Ajustada - Próximos Meses")
    
    # Calculando fator de ajuste baseado no histórico (abordagem conservadora)
    # Aplica ajuste apenas quando percentual_medio < 100% (corrige para baixo)
    # Quando percentual_medio > 100%, mantém fator = 1.0 (não projeta otimisticamente)
    if percentual_medio > 0:
        fator_ajuste = min(percentual_medio / 100, 1.0)
    else:
        fator_ajuste = 1.0
    
    # Obtendo orçamentos futuros para ajustar - usando o filtro de datas do usuário
    data_futura_inicio = start_date  # Usando a data inicial do filtro
    data_futura_fim = end_date       # Usando a data final do filtro  # Até o final do período selecionado
    
    df_orcamentos_futuros = df_orcamentos[
        (df_orcamentos['ID_Casa'].isin(ids_casas_selecionadas)) &
        (df_orcamentos['Data_Orcamento'] >= data_futura_inicio) &
        (df_orcamentos['Data_Orcamento'] <= data_futura_fim) &
        (df_orcamentos['Class_Cont_1'] == 'Faturamento Bruto')
    ]
    
    if not df_orcamentos_futuros.empty:
        df_orcamentos_futuros = df_orcamentos_futuros.copy()
        # Convertendo Valor_Orcamento para float para evitar problemas com decimal.Decimal
        df_orcamentos_futuros.loc[:, 'Valor_Orcamento_Float'] = df_orcamentos_futuros['Valor_Orcamento'].astype(float)
        
        # Aplicando fator de ajuste
        df_orcamentos_futuros.loc[:, 'Valor_Projetado'] = df_orcamentos_futuros['Valor_Orcamento_Float'] * fator_ajuste
        df_orcamentos_futuros.loc[:, 'Ajuste'] = df_orcamentos_futuros['Valor_Projetado'] - df_orcamentos_futuros['Valor_Orcamento_Float']
        
        # Agrupando projeções por mês
        projecoes_mensais = df_orcamentos_futuros.groupby(['Ano_Orcamento', 'Mes_Orcamento']).agg({
            'Valor_Orcamento_Float': 'sum',
            'Valor_Projetado': 'sum',
            'Ajuste': 'sum'
        }).reset_index()
        
        # Renomeando coluna para manter compatibilidade
        projecoes_mensais = projecoes_mensais.rename(columns={'Valor_Orcamento_Float': 'Valor_Orcamento'})
        
        projecoes_mensais['Data_Projecao'] = pd.to_datetime(
            projecoes_mensais['Ano_Orcamento'].astype(str) + '-' + 
            projecoes_mensais['Mes_Orcamento'].astype(str).str.zfill(2) + '-01'
        )
        projecoes_mensais['Mes_Ano'] = projecoes_mensais['Data_Projecao'].dt.strftime('%m/%Y')
        
        # Criando gráfico de projeção
        fig_projecao = go.Figure()
        
        # Orçado original (linha azul)
        fig_projecao.add_trace(go.Scatter(
            x=projecoes_mensais['Mes_Ano'],
            y=projecoes_mensais['Valor_Orcamento'],
            mode='lines+markers',
            name='Orçado Original',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        # Projeção ajustada (linha laranja)
        fig_projecao.add_trace(go.Scatter(
            x=projecoes_mensais['Mes_Ano'],
            y=projecoes_mensais['Valor_Projetado'],
            mode='lines+markers',
            name='Projeção Ajustada (Orçamento)',
            line=dict(color='#ff7f0e', width=3),
            marker=dict(size=8)
        ))
        
        # Adicionando patrocínios se existirem
        if not patrocinios_mensais.empty:
            # Debug: Verificando dados dos patrocínios antes de adicionar ao gráfico
            st.caption(f"🔍 Adicionando patrocínios ao gráfico: {len(patrocinios_mensais)} pontos")
            st.caption(f"🔍 Dados dos patrocínios: {patrocinios_mensais[['Mes_Ano_Display', 'Valor_Parcela']].to_dict('records')}")
            
            fig_projecao.add_trace(go.Scatter(
                x=patrocinios_mensais['Mes_Ano_Display'],
                y=patrocinios_mensais['Valor_Parcela'],
                mode='lines+markers',
                name='Patrocínios',
                line=dict(color='#32CD32', width=3),
                marker=dict(size=8)
            ))
            
            # Calculando receita total (orçamento + patrocínios)
            # Criando DataFrame com projeções de orçamento
            receita_total_mensal = projecoes_mensais[['Mes_Ano', 'Valor_Projetado']].copy()
            receita_total_mensal = receita_total_mensal.rename(columns={'Valor_Projetado': 'Orcamento_Projetado'})
            
            # Adicionando patrocínios através de merge
            patrocinios_para_total = patrocinios_mensais[['Mes_Ano', 'Valor_Parcela']].copy()
            patrocinios_para_total = patrocinios_para_total.rename(columns={'Valor_Parcela': 'Patrocinios'})
            
            # Merge para combinar orçamento e patrocínios
            receita_total_mensal = pd.merge(
                receita_total_mensal,
                patrocinios_para_total,
                on='Mes_Ano',
                how='left'
            ).fillna(0)
            
            # Calculando receita total - convertendo ambos para float para evitar problemas com Decimal
            receita_total_mensal['Receita_Total'] = receita_total_mensal['Orcamento_Projetado'].astype(float) + receita_total_mensal['Patrocinios'].astype(float)
            
            # Formatando data para exibição
            receita_total_mensal['Mes_Ano_Display'] = receita_total_mensal['Mes_Ano']
            
            # Debug: Verificando cálculo da receita total
            st.caption(f"🔍 Receita total calculada: {len(receita_total_mensal)} meses")
            st.caption(f"🔍 Dados da receita total: {receita_total_mensal[['Mes_Ano_Display', 'Orcamento_Projetado', 'Patrocinios', 'Receita_Total']].to_dict('records')}")
            
            # Adicionando linha de receita total
            st.caption(f"🔍 Adicionando receita total ao gráfico: {len(receita_total_mensal)} pontos")

            
            fig_projecao.add_trace(go.Scatter(
                x=receita_total_mensal['Mes_Ano_Display'],
                y=receita_total_mensal['Receita_Total'],
                mode='lines+markers',
                name='Receita Total (Orçamento + Patrocínios)',
                line=dict(color='#2E8B57', width=4, dash='dash'),
                marker=dict(size=10)
            ))
        
        # Configurando layout
        titulo_grafico = f'Projeção Ajustada - Fator: {fator_ajuste:.2f} ({percentual_medio:.1f}% do orçado)'
        if not patrocinios_mensais.empty:
            titulo_grafico += ' + Patrocínios'
        
        fig_projecao.update_layout(
            title=titulo_grafico,
            xaxis_title="Mês/Ano",
            yaxis_title="Valor (R$)",
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig_projecao.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
        
        st.plotly_chart(fig_projecao, use_container_width=True)

        st.divider()
        
        # Métricas de projeção
        st.subheader(":material/heap_snapshot_large: Métricas de projeção")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_orcado_futuro = projecoes_mensais['Valor_Orcamento'].sum()
            st.metric("Total Orçado Futuro", f"R$ {total_orcado_futuro:,.2f}")
        
        with col2:
            total_projetado = projecoes_mensais['Valor_Projetado'].sum()
            st.metric("Total Projetado (Orçamento)", f"R$ {total_projetado:,.2f}")
        
        with col3:
            total_patrocinios_projecao = patrocinios_mensais['Valor_Parcela'].astype(float).sum() if not patrocinios_mensais.empty else 0
            st.metric("Total Patrocínios", f"R$ {total_patrocinios_projecao:,.2f}")
        
        with col4:
            receita_total_projetada = total_projetado + total_patrocinios_projecao
            st.metric("Receita Total Projetada", f"R$ {receita_total_projetada:,.2f}")
        
        # Métricas adicionais
        col1, col2 = st.columns(2)
        
        with col1:
            diferenca_projecao = total_projetado - total_orcado_futuro
            st.metric("Ajuste Orçamento", f"R$ {diferenca_projecao:,.2f}", 
                        delta=f"{diferenca_projecao/total_orcado_futuro*100:.1f}%" if total_orcado_futuro > 0 else "N/A")
        
        with col2:
            diferenca_percentual = (diferenca_projecao / total_orcado_futuro * 100) if total_orcado_futuro > 0 else 0
            st.metric("Ajuste Orçamento (%)", f"↓{diferenca_percentual:.1f}%")
        
        st.divider()

        # Tabela de projeções
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader("Detalhamento das Projeções")
        
        # Preparando dados para a tabela consolidada
        # Sempre incluir patrocínios, mesmo que vazios
        projecoes_consolidadas = projecoes_mensais[['Mes_Ano', 'Valor_Orcamento', 'Valor_Projetado', 'Ajuste']].copy()
        projecoes_consolidadas = projecoes_consolidadas.rename(columns={
            'Valor_Orcamento': 'Orcamento_Original',
            'Valor_Projetado': 'Orcamento_Projetado',
            'Ajuste': 'Ajuste_Orcamento'
        })
        
        # Adicionando patrocínios (se existirem)
        if not patrocinios_mensais.empty:
            # Convertendo Mes_Ano_Display para Mes_Ano para fazer o merge correto
            patrocinios_para_merge = patrocinios_mensais[['Mes_Ano', 'Valor_Parcela']].copy()
            patrocinios_para_merge = patrocinios_para_merge.rename(columns={
                'Valor_Parcela': 'Patrocinios'
            })
            
            # Merge das projeções
            projecoes_consolidadas = pd.merge(
                projecoes_consolidadas, 
                patrocinios_para_merge, 
                on='Mes_Ano', 
                how='left'
            ).fillna(0)
        else:
            # Adicionando coluna vazia para patrocínios
            projecoes_consolidadas['Patrocinios'] = 0
        
        # Calculando receita total - convertendo ambos para float para evitar problemas com Decimal
        projecoes_consolidadas['Receita_Total'] = projecoes_consolidadas['Orcamento_Projetado'].astype(float) + projecoes_consolidadas['Patrocinios'].astype(float)
        
        # Debug: Verificando dados da tabela consolidada
        # st.caption(f"🔍 Tabela consolidada: {len(projecoes_consolidadas)} linhas")
        # st.caption(f"🔍 Colunas da tabela: {list(projecoes_consolidadas.columns)}")
        # st.caption(f"🔍 Dados da tabela: {projecoes_consolidadas[['Mes_Ano', 'Orcamento_Projetado', 'Patrocinios', 'Receita_Total']].to_dict('records')}")

        # Preparando para exibição
        projecoes_display = projecoes_consolidadas[[
            'Mes_Ano', 'Orcamento_Original', 'Orcamento_Projetado', 'Ajuste_Orcamento', 
            'Patrocinios', 'Receita_Total'
        ]].copy()
        projecoes_display.columns = [
            'Mês/Ano', 'Orçado Original (R$)', 'Projeção Ajustada (R$)', 'Ajuste (R$)', 
            'Patrocínios (R$)', 'Receita Total (R$)'
        ]
        
        projecoes_aggrid, tam_projecoes_aggrid = dataframe_aggrid(
            df=projecoes_display,
            name="Projeções Ajustadas",
            num_columns=["Orçado Original (R$)", "Projeção Ajustada (R$)", "Ajuste (R$)", "Patrocínios (R$)", "Receita Total (R$)"]
        )
        
        with col2:
            function_copy_dataframe_as_tsv(projecoes_aggrid)
        
    else:
        st.warning("Não há orçamentos futuros disponíveis para projeção.")

    st.divider()

    # ===== PROJEÇÃO DE FLUXO DE CAIXA FUTURO BASEADA NO TIPO DE FLUXO =====
    st.subheader("🔮 Projeção de Fluxo de Caixa Futuro - Por Tipo de Fluxo")
    
    # Informando o período de projeção
    st.info(f"📅 **Período de projeção**: {data_futura_inicio.strftime('%d/%m/%Y')} a {data_futura_fim.strftime('%d/%m/%Y')}")    
    
    # Filtrando despesas por casas selecionadas
    df_despesas_sem_parcelamento = df_despesas_sem_parcelamento[df_despesas_sem_parcelamento['ID_Casa'].isin(ids_casas_selecionadas)]
    df_despesas_com_parcelamento = df_despesas_com_parcelamento[df_despesas_com_parcelamento['ID_Casa'].isin(ids_casas_selecionadas)]
    
    # Obtendo orçamentos futuros por tipo de fluxo
    df_orcamentos_futuros_tipos = df_orcamentos[
        (df_orcamentos['ID_Casa'].isin(ids_casas_selecionadas)) &
        (df_orcamentos['Data_Orcamento'] >= data_futura_inicio) &
        (df_orcamentos['Data_Orcamento'] <= data_futura_fim) &
        (df_orcamentos['Class_Cont_1'] != 'Faturamento Bruto')  # Excluindo faturamento
    ]
    
    if not df_orcamentos_futuros_tipos.empty:
        # Processando por tipo de fluxo futuro
        projecoes_por_tipo = []
        
        # Criando seção expansível com os parâmetros configurados no sistema
        with st.expander("Parâmetros Configurados no Sistema", expanded=False):            
            # Criando dataframe para exibição
            df_configuracao_exibicao = df_tipo_class_cont_2[['Tipo_Fluxo_Futuro', 'Class_Cont_1', 'Class_Cont_2']].copy()
            df_configuracao_exibicao = df_configuracao_exibicao.rename(columns={
                'Tipo_Fluxo_Futuro': 'Tipo de Fluxo Futuro',
                'Class_Cont_1': 'Classificação Contábil 1',
                'Class_Cont_2': 'Classificação Contábil 2'
            })
            
            # Ordenando por tipo de fluxo e classificações
            ordem_tipos = {'Fixo': 1, 'Variavel do Faturamento': 2, 'Considerar Lançamentos': 3}
            df_configuracao_exibicao['Ordem'] = df_configuracao_exibicao['Tipo de Fluxo Futuro'].map(ordem_tipos)
            df_configuracao_exibicao = df_configuracao_exibicao.sort_values(['Ordem', 'Classificação Contábil 1', 'Classificação Contábil 2'])
            df_configuracao_exibicao = df_configuracao_exibicao.drop('Ordem', axis=1)
            
            # Exibindo tabela de configuração
            config_aggrid, tam_config_aggrid = dataframe_aggrid(
                df=df_configuracao_exibicao,
                name="Configuração do Sistema"
            )
            
            function_copy_dataframe_as_tsv(config_aggrid)
        
        # Processando por tipo de fluxo futuro
        projecoes_por_tipo = []
        
        for tipo_fluxo in ['Fixo', 'Variavel do Faturamento', 'Considerar Lançamentos']:
            st.write(f"**Tipo de Fluxo: {tipo_fluxo}**")
            
            if tipo_fluxo == 'Fixo':
                # Despesas fixas - usar valores dos orçamentos diretamente
                # Obtendo as classificações que são do tipo "Fixo" da configuração do sistema
                classificacoes_fixo_configuradas = df_tipo_class_cont_2[
                    df_tipo_class_cont_2['Tipo_Fluxo_Futuro'] == 'Fixo'
                ]['Class_Cont_1'].unique()
                
                # Filtrando orçamentos apenas para classificações configuradas como "Fixo"
                orcamentos_fixo = df_orcamentos_futuros_tipos[
                    df_orcamentos_futuros_tipos['Class_Cont_1'].isin(classificacoes_fixo_configuradas)
                ].copy()
                
                if not orcamentos_fixo.empty:
                    orcamentos_fixo['Valor_Projetado'] = orcamentos_fixo['Valor_Orcamento'].astype(float)
                    orcamentos_fixo['Tipo_Projecao'] = 'Fixo'
                    projecoes_por_tipo.append(orcamentos_fixo)
                    
                    total_fixo = orcamentos_fixo['Valor_Projetado'].sum()
                    st.write(f"Total projetado (Fixo): R$ {total_fixo:,.2f}")
                else:
                    st.write("Nenhum orçamento encontrado para este tipo.")
            
            elif tipo_fluxo == 'Variavel do Faturamento':
                # Despesas variáveis - aplicar fator de ajuste
                # Obtendo as classificações que são do tipo "Variável do Faturamento" da configuração do sistema
                classificacoes_variavel_configuradas = df_tipo_class_cont_2[
                    df_tipo_class_cont_2['Tipo_Fluxo_Futuro'] == 'Variavel do Faturamento'
                ]['Class_Cont_1'].unique()
                
                # Filtrando orçamentos apenas para classificações configuradas como "Variável do Faturamento"
                orcamentos_variavel = df_orcamentos_futuros_tipos[
                    df_orcamentos_futuros_tipos['Class_Cont_1'].isin(classificacoes_variavel_configuradas)
                ].copy()
                
                if not orcamentos_variavel.empty:
                    orcamentos_variavel['Valor_Projetado'] = orcamentos_variavel['Valor_Orcamento'].astype(float) * fator_ajuste
                    orcamentos_variavel['Tipo_Projecao'] = 'Variável'
                    projecoes_por_tipo.append(orcamentos_variavel)
                    
                    total_variavel = orcamentos_variavel['Valor_Projetado'].sum()
                    st.write(f"Total projetado (Variável - fator {fator_ajuste:.2f}): R$ {total_variavel:,.2f}")
                else:
                    st.write("Nenhum orçamento encontrado para este tipo.")
            
            elif tipo_fluxo == 'Considerar Lançamentos':
                # Usar despesas realmente lançadas (pendentes) apenas para classificações que são "Considerar Lançamentos"
                
                # Obtendo as classificações que são do tipo "Considerar Lançamentos" da configuração do sistema
                classificacoes_lancamentos_configuradas = df_tipo_class_cont_2[
                    df_tipo_class_cont_2['Tipo_Fluxo_Futuro'] == 'Considerar Lançamentos'
                ]['Class_Cont_1'].unique()
                
                # Usando apenas as classificações configuradas como "Considerar Lançamentos"
                classificacoes_lancamentos = list(classificacoes_lancamentos_configuradas)
                
                # Despesas sem parcelamento pendentes - filtrando apenas pelas classificações corretas
                despesas_sem_parc_pendentes = df_despesas_sem_parcelamento[
                    (df_despesas_sem_parcelamento['Status_Pgto'] == 'Pendente') &
                    (df_despesas_sem_parcelamento['Class_Cont_1'].isin(classificacoes_lancamentos))
                ].copy()
                
                # Despesas com parcelamento pendentes - filtrando apenas pelas classificações corretas
                despesas_com_parc_pendentes = df_despesas_com_parcelamento[
                    (df_despesas_com_parcelamento['Status_Pgto'] == 'Parcela_Pendente') &
                    (df_despesas_com_parcelamento['Class_Cont_1'].isin(classificacoes_lancamentos))
                ].copy()
                
                # Processando despesas sem parcelamento
                if not despesas_sem_parc_pendentes.empty:
                    # Usar Previsao_Pgto se disponível, senão Data_Vencimento (mantendo o dia exato)
                    despesas_sem_parc_pendentes['Data_Projecao'] = despesas_sem_parc_pendentes['Previsao_Pgto'].fillna(
                        despesas_sem_parc_pendentes['Data_Vencimento']
                    )
                    # Adicionando colunas de data de competência e vencimento original
                    if 'Data_Competencia' in despesas_sem_parc_pendentes.columns:
                        despesas_sem_parc_pendentes['Data_Competencia'] = despesas_sem_parc_pendentes['Data_Competencia']
                    else:
                        despesas_sem_parc_pendentes['Data_Competencia'] = pd.NaT
                    despesas_sem_parc_pendentes['Data_Vencimento_Original'] = despesas_sem_parc_pendentes['Data_Vencimento']
                    # Consolidando despesas sem parcelamento
                    despesas_sem_parc_pendentes['Valor_Projetado'] = despesas_sem_parc_pendentes['Valor'].astype(float)
                    despesas_sem_parc_pendentes['Tipo_Projecao'] = 'Lançamentos'
                    
                    # Filtrar apenas despesas dentro do período selecionado
                    despesas_sem_parc_futuras = despesas_sem_parc_pendentes[
                        (despesas_sem_parc_pendentes['Data_Projecao'] >= data_futura_inicio) &
                        (despesas_sem_parc_pendentes['Data_Projecao'] <= data_futura_fim)
                    ]
                    
                    # Processando despesas com parcelamento
                    if not despesas_com_parc_pendentes.empty:
                        # Usar Previsao_Parcela se disponível, senão Vencimento_Parcela (mantendo o dia exato)
                        despesas_com_parc_pendentes['Data_Projecao'] = despesas_com_parc_pendentes['Previsao_Parcela'].fillna(
                            despesas_com_parc_pendentes['Vencimento_Parcela']
                        )
                        # Adicionando colunas de data de competência e vencimento original
                        if 'Data_Competencia' in despesas_com_parc_pendentes.columns:
                            despesas_com_parc_pendentes['Data_Competencia'] = despesas_com_parc_pendentes['Data_Competencia']
                        else:
                            despesas_com_parc_pendentes['Data_Competencia'] = despesas_com_parc_pendentes['Vencimento_Parcela']
                        despesas_com_parc_pendentes['Data_Vencimento_Original'] = despesas_com_parc_pendentes['Vencimento_Parcela']
                        despesas_com_parc_pendentes['Valor_Projetado'] = despesas_com_parc_pendentes['Valor_Parcela'].astype(float)
                        despesas_com_parc_pendentes['Tipo_Projecao'] = 'Lançamentos'
                        
                        # Filtrar apenas despesas dentro do período selecionado
                        despesas_com_parc_futuras = despesas_com_parc_pendentes[
                            (despesas_com_parc_pendentes['Data_Projecao'] >= data_futura_inicio) &
                            (despesas_com_parc_pendentes['Data_Projecao'] <= data_futura_fim)
                        ]
                        
                        # Consolidando todas as despesas de lançamentos
                        if not despesas_sem_parc_futuras.empty or not despesas_com_parc_futuras.empty:
                            todas_despesas_lancamentos = pd.concat([
                                despesas_sem_parc_futuras, 
                                despesas_com_parc_futuras
                            ], ignore_index=True)
                            
                            projecoes_por_tipo.append(todas_despesas_lancamentos)
                            total_lancamentos = todas_despesas_lancamentos['Valor_Projetado'].sum()
                            st.write(f"Total de despesas pendentes (consolidadas): R$ {total_lancamentos:,.2f}")
                    else:
                        # Apenas despesas sem parcelamento
                        if not despesas_sem_parc_futuras.empty:
                            projecoes_por_tipo.append(despesas_sem_parc_futuras)
                            total_sem_parc = despesas_sem_parc_futuras['Valor_Projetado'].sum()
                            st.write(f"Total de despesas pendentes: R$ {total_sem_parc:,.2f}")
                else:
                    st.write("Nenhuma despesa pendente encontrada para as classificações 'Considerar Lançamentos'.")
            
            # Removendo seção de Faturamento - já tratado em outra seção
            
            st.write("---")
        
        # Consolidando todas as projeções
        if projecoes_por_tipo:
            df_projecoes_consolidadas = pd.concat(projecoes_por_tipo, ignore_index=True)
            
            # Padronizando a coluna de data para agrupamento por mês
            # Para orçamentos, usar Data_Orcamento; para lançamentos, usar Data_Projecao
            df_projecoes_consolidadas['Data_Agrupamento'] = df_projecoes_consolidadas['Data_Orcamento'].fillna(
                df_projecoes_consolidadas['Data_Projecao']
            )
            
            # Agrupando por mês
            df_projecoes_consolidadas['Mes_Ano'] = df_projecoes_consolidadas['Data_Agrupamento'].dt.strftime('%m/%Y')
            
            # Adicionando coluna Ano_Mes_Projecao baseada na Data_Projecao para facilitar filtros
            df_projecoes_consolidadas['Ano_Mes_Projecao'] = df_projecoes_consolidadas['Data_Projecao'].dt.strftime('%Y-%m')
            
            projecoes_mensais_consolidadas = df_projecoes_consolidadas.groupby(['Mes_Ano', 'Tipo_Projecao'])['Valor_Projetado'].sum().reset_index()
            
            # Criando gráfico consolidado
            fig_projecao_consolidada = go.Figure()
            
            # Calculando totais por mês para os rótulos
            totais_por_mes = projecoes_mensais_consolidadas.groupby('Mes_Ano')['Valor_Projetado'].sum()
            
            # Formatando as datas para exibição no eixo X (mês/ano)
            projecoes_mensais_consolidadas['Mes_Ano_Display'] = projecoes_mensais_consolidadas['Mes_Ano']
            totais_por_mes_display = totais_por_mes.copy()
            totais_por_mes_display.index = totais_por_mes_display.index
            
            for tipo in projecoes_mensais_consolidadas['Tipo_Projecao'].unique():
                dados_tipo = projecoes_mensais_consolidadas[projecoes_mensais_consolidadas['Tipo_Projecao'] == tipo]
                fig_projecao_consolidada.add_trace(go.Bar(
                    x=dados_tipo['Mes_Ano_Display'],
                    y=dados_tipo['Valor_Projetado'],
                    name=tipo,
                    text=[f'R$ {valor:,.0f}' for valor in dados_tipo['Valor_Projetado']],
                    textposition='auto'
                ))
            
            # Adicionando rótulos com totais no topo das barras
            fig_projecao_consolidada.add_trace(go.Scatter(
                x=totais_por_mes_display.index,
                y=totais_por_mes_display.values,
                mode='text',
                text=[f'Total: R$ {valor:,.0f}' for valor in totais_por_mes_display.values],
                textposition='top center',
                textfont=dict(size=12, color='white'),
                showlegend=False,
                hoverinfo='skip'
            ))
            
            fig_projecao_consolidada.update_layout(
                title='Projeção de Despesas Futuras por Tipo de Fluxo',
                xaxis_title="Mês/Ano",
                yaxis_title="Valor (R$)",
                height=500,
                barmode='stack'
            )
            
            fig_projecao_consolidada.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
            
            st.plotly_chart(fig_projecao_consolidada, use_container_width=True)

            st.divider()
            
            # ===== TABELA DETALHADA POR CLASS_CONT_1 E MÊS =====
            col1, col2 = st.columns([6, 1])
            with col1:
                st.subheader("Detalhamento por Classificação Contábil e Mês")
            
            # Preparando dados para a tabela detalhada
            if not df_projecoes_consolidadas.empty:
                # Agrupando por Class_Cont_1, mês e tipo de projeção
                df_detalhado = df_projecoes_consolidadas.groupby([
                    'Class_Cont_1', 
                    'Mes_Ano', 
                    'Tipo_Projecao'
                ])['Valor_Projetado'].sum().reset_index()
                
                # Criando tabela pivot
                pivot_detalhado = df_detalhado.pivot_table(
                    index=['Class_Cont_1', 'Tipo_Projecao'],
                    columns='Mes_Ano',
                    values='Valor_Projetado',
                    aggfunc='sum'
                ).fillna(0)
                
                # Adicionando coluna de total
                pivot_detalhado['Total'] = pivot_detalhado.sum(axis=1)
                
                # Resetando índice para incluir Class_Cont_1 e Tipo_Projecao como colunas
                pivot_detalhado = pivot_detalhado.reset_index()
                
                # Renomeando colunas para melhor visualização (antes da ordenação)
                pivot_detalhado = pivot_detalhado.rename(columns={
                    'Class_Cont_1': 'Classificação Contábil',
                    'Tipo_Projecao': 'Tipo de Fluxo Futuro'
                })
                
                # Ordenando por tipo de fluxo e ordem personalizada
                # Definindo ordem de prioridade: Variável > Fixo > Lançamentos
                ordem_tipos = {'Variável': 1, 'Fixo': 2, 'Lançamentos': 3}
                
                # Definindo ordem personalizada para classificações variáveis
                ordem_classificacoes_variavel = {
                    'Deduções sobre Venda': 1,
                    'Gorjeta': 2,
                    'Custo Mercadoria Vendida': 3,
                    'Mão de Obra - Extra': 4
                }
                
                # Criando colunas de ordenação
                pivot_detalhado['Ordem_Tipo'] = pivot_detalhado['Tipo de Fluxo Futuro'].map(ordem_tipos)
                pivot_detalhado['Ordem_Classificacao'] = pivot_detalhado['Classificação Contábil'].map(ordem_classificacoes_variavel).fillna(999)
                
                # Ordenando primeiro por tipo de fluxo, depois por ordem personalizada, depois por total
                pivot_detalhado = pivot_detalhado.sort_values(['Ordem_Tipo', 'Ordem_Classificacao', 'Total'], ascending=[True, True, False])
                
                # Removendo colunas auxiliares de ordenação
                pivot_detalhado = pivot_detalhado.drop(['Ordem_Tipo', 'Ordem_Classificacao'], axis=1)
                
                # Separando colunas numéricas das de texto
                colunas_texto = ['Classificação Contábil', 'Tipo de Fluxo Futuro']
                colunas_numericas = [col for col in pivot_detalhado.columns if col not in colunas_texto]
                
                # Exibindo tabela detalhada
                df_detalhado_aggrid, tam_df_detalhado_aggrid = dataframe_aggrid(
                    df=pivot_detalhado,
                    name="Detalhamento por Classificação e Mês",
                    num_columns=colunas_numericas
                )
                
                with col2:
                    function_copy_dataframe_as_tsv(df_detalhado_aggrid)

                st.divider()
                
                # ===== TABELA DETALHADA DE LANÇAMENTOS =====
                st.subheader("Detalhamento das Despesas - Tipo 'Lançamentos'")
                
                # Filtrando apenas despesas do tipo "Lançamentos" das projeções consolidadas
                if not df_projecoes_consolidadas.empty:
                    lancamentos_detalhados = df_projecoes_consolidadas[
                        df_projecoes_consolidadas['Tipo_Projecao'] == 'Lançamentos'
                    ].copy()
                    
                    if not lancamentos_detalhados.empty:
                        # Selecionando colunas relevantes para exibição na ordem desejada
                        colunas_exibicao = []
                        
                        # Verificando quais colunas existem no dataframe e adicionando na ordem específica
                        if 'ID_Despesa' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('ID_Despesa')
                        if 'ID_Parcela' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('ID_Parcela')
                        if 'Casa' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Casa')
                        if 'Descricao' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Descricao')
                        if 'Fornecedor' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Fornecedor')
                        if 'Class_Cont_1' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Class_Cont_1')
                        if 'Class_Cont_2' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Class_Cont_2')
                        if 'Valor_Projetado' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Valor_Projetado')
                        if 'Data_Competencia' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Data_Competencia')
                        if 'Data_Vencimento_Original' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Data_Vencimento_Original')
                        if 'Data_Projecao' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Data_Projecao')
                        if 'Ano_Mes_Projecao' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Ano_Mes_Projecao')
                        if 'Status_Pgto' in lancamentos_detalhados.columns:
                            colunas_exibicao.append('Status_Pgto')
                        
                        # Garantindo que temos pelo menos as colunas essenciais
                        if not colunas_exibicao:
                            colunas_exibicao = ['Valor_Projetado', 'Data_Projecao']
                        
                        # Preparando dataframe para exibição
                        df_lancamentos_exibicao = lancamentos_detalhados[colunas_exibicao].copy()
                        
                        # Ordenando por data de projeção e valor
                        if 'Data_Projecao' in df_lancamentos_exibicao.columns:
                            df_lancamentos_exibicao = df_lancamentos_exibicao.sort_values(['Data_Projecao', 'Valor_Projetado'], ascending=[True, False])
                        
                        # Formatando datas para exibição
                        if 'Data_Competencia' in df_lancamentos_exibicao.columns:
                            df_lancamentos_exibicao['Data_Competencia'] = df_lancamentos_exibicao['Data_Competencia'].dt.strftime('%d/%m/%Y').fillna('N/A')
                        if 'Data_Vencimento_Original' in df_lancamentos_exibicao.columns:
                            df_lancamentos_exibicao['Data_Vencimento_Original'] = df_lancamentos_exibicao['Data_Vencimento_Original'].dt.strftime('%d/%m/%Y').fillna('N/A')
                        if 'Data_Projecao' in df_lancamentos_exibicao.columns:
                            df_lancamentos_exibicao['Data_Projecao'] = df_lancamentos_exibicao['Data_Projecao'].dt.strftime('%d/%m/%Y').fillna('N/A')
                        
                        # Renomeando colunas para melhor visualização
                        mapeamento_colunas = {
                            'ID_Despesa': 'ID Despesa',
                            'ID_Parcela': 'ID Parcela', 
                            'Descricao': 'Descrição',
                            'Fornecedor': 'Fornecedor',
                            'Class_Cont_1': 'Classificação 1',
                            'Class_Cont_2': 'Classificação 2',
                            'Data_Competencia': 'Data Competência',
                            'Data_Vencimento_Original': 'Data Vencimento Original',
                            'Data_Projecao': 'Data Projeção',
                            'Ano_Mes_Projecao': 'Ano/Mês Projeção',
                            'Status_Pgto': 'Status Pagamento',
                            'Valor_Projetado': 'Valor (R$)',
                            'Casa': 'Casa'
                        }
                        
                        df_lancamentos_exibicao = df_lancamentos_exibicao.rename(columns=mapeamento_colunas)
                        
                        # Exibindo tabela detalhada
                        df_lancamentos_aggrid, tam_df_lancamentos_aggrid = dataframe_aggrid(
                            df=df_lancamentos_exibicao,
                            name="Detalhamento de Lançamentos",
                            num_columns=["Valor (R$)"]
                        )
                        
                        col1, col2 = st.columns([6, 1])
                        with col1: # Calculando total dos valores filtrados
                            total_valores_filtrados(df_lancamentos_aggrid, tam_df_lancamentos_aggrid, 'Valor (R$)')
                        with col2:
                            function_copy_dataframe_as_tsv(df_lancamentos_aggrid)
                        
                    else:
                        st.info("Não há despesas do tipo 'Lançamentos' para exibir.")
                else:
                    st.warning("Não há dados de projeções consolidadas disponíveis.")

                st.divider()
                
                # Informações adicionais da tabela detalhada
                st.subheader(":material/heap_snapshot_large: Informações adicionais")
                col1, col2 = st.columns(2)
                
                with col1:
                    total_classificacoes = len(pivot_detalhado['Classificação Contábil'].unique())
                    st.metric("Total de Classificações", total_classificacoes)
                
                with col2:
                    total_meses = len(colunas_numericas) - 1  # Excluindo a coluna 'Total'
                    st.metric("Período de Projeção", f"{total_meses} meses")
                
            else:
                st.warning("Não há dados disponíveis para gerar a tabela detalhada.")
        else:
            st.warning("Nenhuma projeção encontrada para os tipos de fluxo configurados.")
    else:
        st.warning("Não há orçamentos futuros disponíveis para projeção por tipo de fluxo.")

else:
    st.warning("Dados insuficientes para análise comparativa. Verifique se há dados de orçamento e faturamento realizado nos últimos 6 meses.")

st.divider()

# Gráfico de Projeção Avançada por Mês - Receitas vs Despesas
st.subheader("Projeção Avançada por Mês - Receitas vs Despesas")

# Verificando se temos dados de projeção disponíveis
if 'df_projecoes_consolidadas' in locals() and not df_projecoes_consolidadas.empty:
    # Usando os dados de projeção consolidados
    # st.info("📈 Utilizando projeções baseadas nos tipos de fluxo futuro configurados")
    
    # Verificando se patrocinios_mensais está definida
    if 'patrocinios_mensais' not in locals():
        patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
    
    # Separando receitas e despesas das projeções
    receitas_projetadas = df_orcamentos_futuros.copy() if 'df_orcamentos_futuros' in locals() and not df_orcamentos_futuros.empty else pd.DataFrame()
    despesas_projetadas = df_projecoes_consolidadas.copy()
    
    # Verificando se df_orcamentos_futuros está definida
    if 'df_orcamentos_futuros' not in locals():
        df_orcamentos_futuros = pd.DataFrame()
    
    # Preparando dados de receitas projetadas (orçamento + patrocínios)
    receitas_consolidadas = []
    
    # Receitas do orçamento
    if not receitas_projetadas.empty:
        receitas_projetadas['Mes_Ano'] = receitas_projetadas['Data_Orcamento'].dt.strftime('%m/%Y')
        receitas_orcamento = receitas_projetadas.groupby('Mes_Ano')['Valor_Projetado'].sum().reset_index()
        receitas_orcamento['Tipo'] = 'Receitas Orçamento'
        receitas_orcamento = receitas_orcamento.rename(columns={'Valor_Projetado': 'Valor'})
        receitas_consolidadas.append(receitas_orcamento)
    
    # Receitas de patrocínios
    if not patrocinios_mensais.empty:
        patrocinios_para_receitas = patrocinios_mensais[['Mes_Ano', 'Valor_Parcela']].copy()
        patrocinios_para_receitas['Tipo'] = 'Receitas Patrocínios'
        patrocinios_para_receitas = patrocinios_para_receitas.rename(columns={'Valor_Parcela': 'Valor'})
        receitas_consolidadas.append(patrocinios_para_receitas)
    
    # Combinando todas as receitas
    if receitas_consolidadas:
        receitas_mensais = pd.concat(receitas_consolidadas, ignore_index=True)
    else:
        receitas_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor', 'Tipo'])
    
    # Preparando dados de despesas projetadas
    if not despesas_projetadas.empty:
        despesas_mensais = despesas_projetadas.groupby('Mes_Ano')['Valor_Projetado'].sum().reset_index()
        despesas_mensais['Tipo'] = 'Despesas Projetadas'
        despesas_mensais = despesas_mensais.rename(columns={'Valor_Projetado': 'Valor'})
    else:
        despesas_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor', 'Tipo'])
    
    # Combinando dados
    projecao_mensal = pd.concat([receitas_mensais, despesas_mensais], ignore_index=True)
    
    if not projecao_mensal.empty:
        # Ordenando por data
        projecao_mensal = projecao_mensal.sort_values('Mes_Ano')
        
        # Formatando data para exibição
        projecao_mensal['Mes_Ano_Display'] = projecao_mensal['Mes_Ano']
        
        # Criando gráfico
        fig_projecao_mensal = go.Figure()
        
        # Combinando receitas em uma única barra
        receitas_orcamento_data = projecao_mensal[projecao_mensal['Tipo'] == 'Receitas Orçamento']
        receitas_patrocinios_data = projecao_mensal[projecao_mensal['Tipo'] == 'Receitas Patrocínios']
        
        # Criando DataFrame com receitas consolidadas
        receitas_consolidadas_grafico = []
        
        # Obtendo todos os meses únicos
        todos_meses = sorted(projecao_mensal['Mes_Ano_Display'].unique())
        
        for mes in todos_meses:
            # Receitas do orçamento para este mês
            valor_orcamento = receitas_orcamento_data[receitas_orcamento_data['Mes_Ano_Display'] == mes]['Valor'].sum() if not receitas_orcamento_data.empty else 0
            
            # Receitas de patrocínios para este mês
            valor_patrocinios = receitas_patrocinios_data[receitas_patrocinios_data['Mes_Ano_Display'] == mes]['Valor'].sum() if not receitas_patrocinios_data.empty else 0
            
            # Total de receitas para este mês
            valor_total_receitas = valor_orcamento + valor_patrocinios
            
            if valor_total_receitas > 0:
                receitas_consolidadas_grafico.append({
                    'Mes_Ano_Display': mes,
                    'Valor': valor_total_receitas,
                    'Valor_Orcamento': valor_orcamento,
                    'Valor_Patrocinios': valor_patrocinios
                })
        
        # Criando DataFrame de receitas consolidadas
        df_receitas_consolidadas = pd.DataFrame(receitas_consolidadas_grafico)
        
        # Adicionando barra de receitas consolidadas (verde)
        if not df_receitas_consolidadas.empty:
            fig_projecao_mensal.add_trace(go.Bar(
                x=df_receitas_consolidadas['Mes_Ano_Display'],
                y=df_receitas_consolidadas['Valor'],
                name='Receitas Totais (Orçamento + Patrocínios)',
                marker_color='#2E8B57',
                text=[f'R$ {valor:,.0f}' for valor in df_receitas_consolidadas['Valor']],
                textposition='auto',
                hovertemplate='<b>%{x}</b><br>' +
                                'Receitas Totais: R$ %{y:,.2f}<br>' +
                                'Orçamento: R$ %{customdata[0]:,.2f}<br>' +
                                'Patrocínios: R$ %{customdata[1]:,.2f}<br>' +
                                '<extra></extra>',
                customdata=df_receitas_consolidadas[['Valor_Orcamento', 'Valor_Patrocinios']].values
            ))
        
        # Despesas projetadas (vermelho)
        despesas_data = projecao_mensal[projecao_mensal['Tipo'] == 'Despesas Projetadas']
        if not despesas_data.empty:
            fig_projecao_mensal.add_trace(go.Bar(
                x=despesas_data['Mes_Ano_Display'],
                y=despesas_data['Valor'],
                name='Despesas Projetadas',
                marker_color='#DC143C',
                text=[f'R$ {valor:,.0f}' for valor in despesas_data['Valor']],
                textposition='auto'
            ))
        
        # Configurando layout
        fig_projecao_mensal.update_layout(
            title=f'Projeção Avançada por Mês - {", ".join(casas_selecionadas)} (Baseada em Tipos de Fluxo)',
            xaxis_title="Mês/Ano",
            yaxis_title="Valor Projetado (R$)",
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            barmode='group'
        )
        
        fig_projecao_mensal.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
        
        st.plotly_chart(fig_projecao_mensal, use_container_width=True)
        
        st.divider()

        # Métricas resumidas da projeção
        st.subheader(":material/heap_snapshot_large: Métricas de projeção")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_receitas_proj = df_receitas_consolidadas['Valor'].sum() if not df_receitas_consolidadas.empty else 0
            st.metric("Total Receitas Projetadas", f"R$ {total_receitas_proj:,.2f}")
        
        with col2:
            total_despesas_proj = despesas_data['Valor'].sum() if not despesas_data.empty else 0
            st.metric("Total Despesas Projetadas", f"R$ {total_despesas_proj:,.2f}")
        
        with col3:
            saldo_projetado = total_receitas_proj - total_despesas_proj
            st.metric("Saldo Projetado", f"R$ {saldo_projetado:,.2f}")
        
        with col4:
            if total_receitas_proj > 0:
                margem_projetada = (saldo_projetado / total_receitas_proj) * 100
                st.metric("Margem Projetada (%)", f"{margem_projetada:.1f}%")
            else:
                st.metric("Margem Projetada (%)", "N/A")
        
        # Métricas detalhadas das receitas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_receitas_orcamento = df_receitas_consolidadas['Valor_Orcamento'].sum() if not df_receitas_consolidadas.empty else 0
            st.metric("Receitas Orçamento", f"R$ {total_receitas_orcamento:,.2f}")
        
        with col2:
            total_receitas_patrocinios = df_receitas_consolidadas['Valor_Patrocinios'].sum() if not df_receitas_consolidadas.empty else 0
            st.metric("Receitas Patrocínios", f"R$ {total_receitas_patrocinios:,.2f}")
        
        with col3:
            if total_receitas_proj > 0:
                percentual_patrocinios = (total_receitas_patrocinios / total_receitas_proj) * 100
                st.metric("Patrocínios/Total (%)", f"{percentual_patrocinios:.1f}%")
            else:
                st.metric("Patrocínios/Total (%)", "N/A")
        
        st.divider()

        # Tabela resumida da projeção
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader("Resumo da Projeção Avançada por Mês")
        
        # Criando tabela pivot usando os dados consolidadas
        if not df_receitas_consolidadas.empty:
            # Criando DataFrame para a tabela
            tabela_projecao = df_receitas_consolidadas[['Mes_Ano_Display', 'Valor_Orcamento', 'Valor_Patrocinios', 'Valor']].copy()
            tabela_projecao = tabela_projecao.rename(columns={
                'Valor_Orcamento': 'Receitas Orçamento',
                'Valor_Patrocinios': 'Receitas Patrocínios',
                'Valor': 'Receitas Total'
            })
            
            # Adicionando despesas projetadas
            if not despesas_data.empty:
                despesas_tabela = despesas_data[['Mes_Ano_Display', 'Valor']].copy()
                despesas_tabela = despesas_tabela.rename(columns={'Valor': 'Despesas Projetadas'})
                
                # Merge das receitas com despesas
                tabela_projecao = pd.merge(tabela_projecao, despesas_tabela, on='Mes_Ano_Display', how='left').fillna(0)
            else:
                tabela_projecao['Despesas Projetadas'] = 0
            
            # Calculando saldo
            tabela_projecao['Saldo'] = tabela_projecao['Receitas Total'] - tabela_projecao['Despesas Projetadas']
            
            # Reordenando colunas
            colunas_ordenadas = ['Mes_Ano_Display', 'Receitas Orçamento', 'Receitas Patrocínios', 'Receitas Total', 'Despesas Projetadas', 'Saldo']
            tabela_projecao = tabela_projecao[colunas_ordenadas]
            
            pivot_projecao = tabela_projecao
        else:
            # Fallback se não houver receitas consolidadas
            pivot_projecao = pd.DataFrame(columns=['Mes_Ano_Display', 'Receitas Orçamento', 'Receitas Patrocínios', 'Receitas Total', 'Despesas Projetadas', 'Saldo'])
        
        # Exibindo tabela
        colunas_numericas = [col for col in pivot_projecao.columns if col != 'Mes_Ano_Display']
        pivot_projecao_aggrid, tam_pivot_projecao_aggrid = dataframe_aggrid(
            df=pivot_projecao,
            name="Resumo da Projeção Avançada Mensal",
            num_columns=colunas_numericas
        )
        
        with col2:
            function_copy_dataframe_as_tsv(pivot_projecao_aggrid)
        
    else:
        st.warning("Não há dados de projeção para exibir no gráfico.")

else:
    # Fallback para o gráfico original se não houver projeções
    st.info("📊 Exibindo dados básicos do orçamento (sem projeções avançadas)")
    
    if not df_orcamentos_filtrada.empty:
        # Separando receitas e despesas
        receitas_orcamento = df_orcamentos_filtrada[df_orcamentos_filtrada['Class_Cont_1'] == 'Faturamento Bruto'].copy()
        despesas_orcamento = df_orcamentos_filtrada[df_orcamentos_filtrada['Class_Cont_1'] != 'Faturamento Bruto'].copy()
        
        # Agrupando receitas por mês
        if not receitas_orcamento.empty:
            receitas_mensais = receitas_orcamento.groupby('Data_Orcamento')['Valor_Orcamento'].sum().reset_index()
            receitas_mensais['Tipo'] = 'Receitas'
        else:
            receitas_mensais = pd.DataFrame(columns=['Data_Orcamento', 'Valor_Orcamento', 'Tipo'])
        
        # Agrupando despesas por mês
        if not despesas_orcamento.empty:
            despesas_mensais = despesas_orcamento.groupby('Data_Orcamento')['Valor_Orcamento'].sum().reset_index()
            despesas_mensais['Tipo'] = 'Despesas'
        else:
            despesas_mensais = pd.DataFrame(columns=['Data_Orcamento', 'Valor_Orcamento', 'Tipo'])
        
        # Combinando dados
        orcamento_mensal = pd.concat([receitas_mensais, despesas_mensais], ignore_index=True)
        
        if not orcamento_mensal.empty:
            # Ordenando por data
            orcamento_mensal = orcamento_mensal.sort_values('Data_Orcamento')
            
            # Formatando data para exibição
            orcamento_mensal['Mes_Ano'] = orcamento_mensal['Data_Orcamento'].dt.strftime('%m/%Y')
            
            # Criando gráfico
            fig_orcamento_mensal = go.Figure()
            
            # Receitas (verde)
            receitas_data = orcamento_mensal[orcamento_mensal['Tipo'] == 'Receitas']
            if not receitas_data.empty:
                fig_orcamento_mensal.add_trace(go.Bar(
                    x=receitas_data['Mes_Ano'],
                    y=receitas_data['Valor_Orcamento'],
                    name='Receitas',
                    marker_color='#2E8B57',
                    text=[f'R$ {valor:,.0f}' for valor in receitas_data['Valor_Orcamento']],
                    textposition='auto'
                ))
            
            # Despesas (vermelho)
            despesas_data = orcamento_mensal[orcamento_mensal['Tipo'] == 'Despesas']
            if not despesas_data.empty:
                fig_orcamento_mensal.add_trace(go.Bar(
                    x=despesas_data['Mes_Ano'],
                    y=despesas_data['Valor_Orcamento'],
                    name='Despesas',
                    marker_color='#DC143C',
                    text=[f'R$ {valor:,.0f}' for valor in despesas_data['Valor_Orcamento']],
                    textposition='auto'
                ))
            
            # Configurando layout
            fig_orcamento_mensal.update_layout(
                title=f'Orçamento por Mês - {", ".join(casas_selecionadas)}',
                xaxis_title="Mês/Ano",
                yaxis_title="Valor Orçado (R$)",
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                barmode='group'
            )
            
            fig_orcamento_mensal.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
            
            st.plotly_chart(fig_orcamento_mensal, use_container_width=True)
            
            # Métricas resumidas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_receitas = receitas_orcamento['Valor_Orcamento'].sum() if not receitas_orcamento.empty else 0
                st.metric("Total Receitas Orçadas", f"R$ {total_receitas:,.2f}")
            
            with col2:
                total_despesas = despesas_orcamento['Valor_Orcamento'].sum() if not despesas_orcamento.empty else 0
                st.metric("Total Despesas Orçadas", f"R$ {total_despesas:,.2f}")
            
            with col3:
                saldo_orcado = total_receitas - total_despesas
                st.metric("Saldo Orçado", f"R$ {saldo_orcado:,.2f}")
            
            with col4:
                if total_receitas > 0:
                    margem_orcada = (saldo_orcado / total_receitas) * 100
                    st.metric("Margem Orçada (%)", f"{margem_orcada:.1f}%")
                else:
                    st.metric("Margem Orçada (%)", "N/A")
            
            # Tabela resumida
            st.subheader("📋 Resumo Orçamentário por Mês")
            
            # Criando tabela pivot
            pivot_orcamento = orcamento_mensal.pivot(
                index='Mes_Ano',
                columns='Tipo',
                values='Valor_Orcamento'
            ).fillna(0)
            
            # Adicionando coluna de saldo - convertendo para float para evitar problemas com Decimal
            pivot_orcamento['Saldo'] = float(pivot_orcamento.get('Receitas', 0)) - float(pivot_orcamento.get('Despesas', 0))
            
            # Resetando índice
            pivot_orcamento = pivot_orcamento.reset_index()
            
            # Reordenando colunas: Receitas, Despesas, Saldo
            colunas_ordenadas = ['Mes_Ano', 'Receitas', 'Despesas', 'Saldo']
            pivot_orcamento = pivot_orcamento[colunas_ordenadas]
            
            # Exibindo tabela
            pivot_orcamento_aggrid = component_plotDataframe_aggrid(
                df=pivot_orcamento,
                name="Resumo Orçamentário Mensal",
                num_columns=["Receitas", "Despesas", "Saldo"],
                percent_columns=[],
                df_details=None,
                coluns_merge_details=None,
                coluns_name_details=None
            )
            
            function_copy_dataframe_as_tsv(pivot_orcamento_aggrid)
            
        else:
            st.warning("Não há dados de orçamento para exibir no gráfico.")
    else:
        st.warning("Não há dados de orçamento disponíveis para as casas selecionadas.")

st.divider()

# ===== TABELA DE FATORES DE AJUSTE POR CASA =====
col1, col2 = st.columns([6, 1])
with col1:
    st.subheader("Fatores de Ajuste por Casa")
    st.markdown("**Análise de Performance: Orçado vs Realizado**")

# Mostrando o período usado para análise
if 'fator_ajuste_date_input' in st.session_state:
    fator_data = st.session_state['fator_ajuste_date_input']
    if isinstance(fator_data, tuple):
        if len(fator_data) >= 2:
            periodo_analise_fatores = f"{fator_data[0].strftime('%d/%m/%Y')} a {fator_data[1].strftime('%d/%m/%Y')}"
        elif len(fator_data) == 1:
            periodo_analise_fatores = fator_data[0].strftime('%d/%m/%Y')
        else:
            periodo_analise_fatores = "Período não definido"
    else:
        periodo_analise_fatores = fator_data.strftime('%d/%m/%Y')
    # st.info(f"📅 **Período de análise**: {periodo_analise_fatores}")

# Calculando fatores de ajuste por casa individual
fatores_por_casa = []

for casa in casas_selecionadas:
    if casa == 'Todas as casas':
        casas_para_processar = list(mapeamento_lojas.keys())  # todas as casas do mapeamento
        casas_para_processar = [c for c in casas_para_processar if c != 'All bar']
    else:
        casas_para_processar = [casa]

    for c in casas_para_processar:
        casa_id = mapeamento_lojas[c]
        casas_ids = [casa_id]  # lista com o(s) ID(s) para filtro
        casa_label = c  # label da casa para exibir na tabela
    
        # Filtrando dados de orçamento para esta casa usando o filtro de data personalizado
        if 'fator_ajuste_date_input' not in st.session_state:
            hoje = datetime.datetime.now()
            data_limite_analise_casa = hoje.replace(day=1) - timedelta(days=1)  # Último dia do mês anterior
            data_inicio_analise_casa = data_limite_analise_casa.replace(day=1) - timedelta(days=180)  # 6 meses atrás
        else:
            fator_data = st.session_state['fator_ajuste_date_input']
            if isinstance(fator_data, tuple):
                data_inicio_analise_casa = pd.to_datetime(fator_data[0])
                if len(fator_data) >= 2:
                    data_limite_analise_casa = pd.to_datetime(fator_data[1])
                else:
                    data_limite_analise_casa = data_inicio_analise_casa  # Se só tem uma data, usar a mesma
            else:
                data_inicio_analise_casa = pd.to_datetime(fator_data)
                data_limite_analise_casa = pd.to_datetime(fator_data)
        
        df_orcamentos_casa = df_orcamentos[
            (df_orcamentos['ID_Casa'].isin(casas_ids)) &
            (df_orcamentos['Data_Orcamento'] >= data_inicio_analise_casa) &
            (df_orcamentos['Data_Orcamento'] <= data_limite_analise_casa) &
            (df_orcamentos['Class_Cont_1'] == 'Faturamento Bruto')
        ]
        
        # Filtrando dados de faturamento para esta casa
        df_faturamento_casa = df_faturamento_agregado[
            (df_faturamento_agregado['ID_Casa'].isin(casas_ids))
        ]
        
        if not df_orcamentos_casa.empty and not df_faturamento_casa.empty:
            # Agrupando orçamentos por mês para esta casa
            orcamentos_casa_mensais = df_orcamentos_casa.groupby(['Ano_Orcamento', 'Mes_Orcamento'])['Valor_Orcamento'].sum().reset_index()
            orcamentos_casa_mensais['Data_Comparacao'] = pd.to_datetime(
                orcamentos_casa_mensais['Ano_Orcamento'].astype(str) + '-' + 
                orcamentos_casa_mensais['Mes_Orcamento'].astype(str).str.zfill(2) + '-01'
            )
            
            # Agrupando faturamento por mês para esta casa
            faturamento_casa_mensais = df_faturamento_casa.groupby('Ano_Mes')['Valor_Bruto'].sum().reset_index()
            faturamento_casa_mensais['Data_Comparacao'] = pd.to_datetime(
                faturamento_casa_mensais['Ano_Mes'] + '-01'
            )
            
            # Merge dos dados para comparação desta casa
            df_comparacao_casa = pd.merge(
                orcamentos_casa_mensais[['Data_Comparacao', 'Valor_Orcamento']],
                faturamento_casa_mensais[['Data_Comparacao', 'Valor_Bruto']],
                on='Data_Comparacao',
                how='left'
            ).fillna(0)
            
            # Calculando percentual realizado para esta casa
            df_comparacao_casa['Percentual_Realizado'] = df_comparacao_casa.apply(
                lambda row: (row['Valor_Bruto'] / row['Valor_Orcamento'] * 100) if row['Valor_Orcamento'] != 0 else 0, 
                axis=1
            ).fillna(0)
            
            # Calculando métricas para esta casa
            total_orcado_casa = df_comparacao_casa['Valor_Orcamento'].sum()
            total_realizado_casa = df_comparacao_casa['Valor_Bruto'].sum()
            percentual_medio_casa = df_comparacao_casa['Percentual_Realizado'].mean()
            
            # Calculando fator de ajuste para esta casa
            if percentual_medio_casa > 0:
                fator_ajuste_casa = min(percentual_medio_casa / 100, 1.0)
            else:
                fator_ajuste_casa = 1.0
            
            # Classificando performance
            if percentual_medio_casa >= 110:
                classificacao = "🟢 Excelente"
                cor_classificacao = "green"
            elif percentual_medio_casa >= 100:
                classificacao = "🟡 Boa"
                cor_classificacao = "orange"
            elif percentual_medio_casa >= 90:
                classificacao = "🟠 Atenção"
                cor_classificacao = "red"
            else:
                classificacao = "🔴 Crítica"
                cor_classificacao = "darkred"
            
            # Adicionando à lista de fatores
            fatores_por_casa.append({
                'Casa': casa_label,
                'Total_Orcado': total_orcado_casa,
                'Total_Realizado': total_realizado_casa,
                'Percentual_Realizado': percentual_medio_casa,
                'Fator_Ajuste': fator_ajuste_casa,
                'Classificacao': classificacao,
                'Meses_Analisados': len(df_comparacao_casa)
            })
        else:
            # Caso não haja dados suficientes
            fatores_por_casa.append({
                'Casa': casa_label,
                'Total_Orcado': 0,
                'Total_Realizado': 0,
                'Percentual_Realizado': 0,
                'Fator_Ajuste': 1.0,
                'Classificacao': "⚪ Sem dados",
                'Meses_Analisados': 0
            })

# Criando DataFrame com os fatores
df_fatores_ajuste = pd.DataFrame(fatores_por_casa)

if not df_fatores_ajuste.empty:
    # Formatando colunas para exibição
    df_fatores_display = df_fatores_ajuste.copy()
    df_fatores_display['Total_Orcado'] = df_fatores_display['Total_Orcado'].apply(lambda x: f"R$ {x:,.2f}")
    df_fatores_display['Total_Realizado'] = df_fatores_display['Total_Realizado'].apply(lambda x: f"R$ {x:,.2f}")
    df_fatores_display['Percentual_Realizado'] = df_fatores_display['Percentual_Realizado'].apply(lambda x: f"{x:.1f}%")
    df_fatores_display['Fator_Ajuste'] = df_fatores_display['Fator_Ajuste'].apply(lambda x: f"{x:.3f}")
    
    # Renomeando colunas
    df_fatores_display.columns = [
        'Casa', 
        'Total Orçado', 
        'Total Realizado', 
        'Realizado/Orçado (%)', 
        'Fator de Ajuste', 
        'Classificação', 
        'Meses Analisados'
    ]
    
    # Exibindo tabela
    st.markdown("**📋 Resumo dos Fatores de Ajuste por Casa**")
    st.caption(f"Período de análise: {data_inicio_analise.strftime('%d/%m/%Y')} a {data_limite_analise.strftime('%d/%m/%Y')}")
    
    fatores_aggrid, tam_fatores_aggrid = dataframe_aggrid(
        df=df_fatores_display,
        name="Fatores de Ajuste por Casa",
        num_columns=["Total Orçado", "Total Realizado"],
        percent_columns=["Realizado/Orçado (%)"]
    )
    
    with col2:
        function_copy_dataframe_as_tsv(fatores_aggrid)

    st.divider()
    
    # Métricas resumidas
    st.subheader(":material/heap_snapshot_large: Métricas gerais")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        media_percentual = df_fatores_ajuste['Percentual_Realizado'].mean()
        st.metric("Média Realizado/Orçado", f"{media_percentual:.1f}%")
    
    with col2:
        media_fator = df_fatores_ajuste['Fator_Ajuste'].mean()
        st.metric("Fator de Ajuste Médio", f"{media_fator:.3f}")
    
    with col3:
        casas_excelentes = len(df_fatores_ajuste[df_fatores_ajuste['Percentual_Realizado'] >= 110])
        total_casas = len(df_fatores_ajuste)
        st.metric("Casas Excelentes", f"{casas_excelentes}/{total_casas}")
    
    with col4:
        casas_criticas = len(df_fatores_ajuste[df_fatores_ajuste['Percentual_Realizado'] < 90])
        st.metric("Casas Críticas", f"{casas_criticas}/{total_casas}")
    
    st.divider()

    # Legenda das classificações
    st.markdown("**📝 Legenda das Classificações:**")
    st.markdown("""
    - 🟢 **Excelente**: Realizado ≥ 110% do orçado
    - 🟡 **Boa**: Realizado entre 100% e 109% do orçado  
    - 🟠 **Atenção**: Realizado entre 90% e 99% do orçado
    - 🔴 **Crítica**: Realizado < 90% do orçado
    - ⚪ **Sem dados**: Dados insuficientes para análise
    """)
    
    # Explicação do fator de ajuste
    st.markdown("**💡 Sobre o Fator de Ajuste:**")
    st.markdown("""
    O fator de ajuste é calculado com base no histórico de realização vs orçamento de cada casa no período selecionado. 
    - **Fator = 1.000**: Casa atingiu 100% ou mais do orçado (projeção otimista mantida)
    - **Fator < 1.000**: Casa realizou menos que 100% do orçado (projeção ajustada para baixo)
    
    Este fator é aplicado nas projeções futuras para tornar as estimativas mais realistas.
    O período histórico usado para o cálculo pode ser configurado na seção "Configuração do Fator de Ajuste".
    """)

else:
    st.warning("Não foi possível calcular os fatores de ajuste para as casas selecionadas.")



