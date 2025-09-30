import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import calendar
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.functions.general_functions_conciliacao import *
from utils.constants.general_constants import mapeamento_class_cont
from utils.functions.general_functions import config_sidebar
from utils.functions.fluxo_realizado import *
from utils.queries_conciliacao import *
from utils.components import dataframe_aggrid


st.set_page_config(
    page_title="Fluxo Realizado",
    page_icon=":material/currency_exchange:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/currency_exchange: Fluxo Realizado")
st.divider()

# Recuperando dados
df_casas = GET_CASAS()
df_extrato_zig = GET_EXTRATO_ZIG()
df_parc_receit_extr = GET_PARCELAS_RECEIT_EXTR()
df_eventos = GET_EVENTOS()
df_mutuos = GET_MUTUOS()
df_bloqueios = GET_BLOQUEIOS_JUDICIAIS()
df_custos_blueme_sem_parcelam = GET_CUSTOS_BLUEME_SEM_PARC()
df_custos_blueme_com_parcelam = GET_CUSTOS_BLUEME_COM_PARC()


# Filtrando Data
today = datetime.datetime.now()
last_year = today.year - 1
jan_last_year = datetime.datetime(last_year, 1, 1)
jan_this_year = datetime.datetime(today.year, 1, 1)
last_day_of_month = calendar.monthrange(today.year, today.month)[1]
this_month_this_year = datetime.datetime(today.year, today.month, last_day_of_month)
dec_this_year = datetime.datetime(today.year, 12, 31)

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
col_casas, col_botao = st.columns([4, 1])

with col_casas:
    # Usando session_state se disponível, senão usa o valor padrão
    default_casas = st.session_state.get('casas_selecionadas', [casas[0]] if casas else [])
    casas_selecionadas = st.multiselect("Casas", casas, default=default_casas, placeholder='Selecione casas', key="casas_multiselect")

with col_botao:
    st.markdown("<br>", unsafe_allow_html=True)  # para alinhar o botão com os widgets
    if st.button(
        "🏢 Sem Sócios Externos", 
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

# Usando session_state se disponível, senão usa o valor padrão
default_value = st.session_state.get('date_input', (jan_this_year, this_month_this_year))

# Campos de seleção de data
col1, col2 = st.columns(2)

with col1:
    start_date = st.date_input(
        "Data de início", 
        value=jan_this_year, 
        min_value=jan_last_year, 
        max_value=dec_this_year, 
        format="DD/MM/YYYY")
with col2:
    end_date = st.date_input(
        "Data de fim", 
        value=this_month_this_year, 
        min_value=jan_last_year, 
        max_value=dec_this_year, 
        format="DD/MM/YYYY")

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

if not casas_selecionadas:
    st.warning("Por favor, selecione pelo menos uma casa.")
    st.stop()

st.divider()

## Receitas ##
st.markdown("""
    <h2 style="color: green; font-weight: bold;">Receitas</h1>
    """, unsafe_allow_html=True)

## Zig_Extrato
st.subheader("Extrato Zig")
df_extrato_zig_filtrada = filtra_df(df_extrato_zig, 'Data_Liquidacao', ids_casas_selecionadas, start_date, end_date)
df_extrato_zig_filtrada = df_extrato_zig_filtrada[['ID_Extrato','ID_Casa','Casa','Descricao','Data_Liquidacao','Data_Transacao','Valor']]

# Exibe df com aggrid
df_extrato_zig_filtrada_aggrid, tam_df_extrato_zig_filtrada_aggrid = dataframe_aggrid(
    df=df_extrato_zig_filtrada, 
    name='Extrato Zig', 
    num_columns=["Valor"],
    date_columns=['Data_Liquidacao', 'Data_Transacao'],
    key='teste_extrato_zig'
)

# Calcula total dos valores filtrados
total_valores_filtrados(df_extrato_zig_filtrada_aggrid, tam_df_extrato_zig_filtrada_aggrid, 'Valor')

# Botão para excel
function_copy_dataframe_as_tsv(df_extrato_zig_filtrada_aggrid)

st.divider()

## Parcelas Receitas Extraordinárias
st.subheader("Parcelas Receitas Extraordinárias")
df_parc_receit_extr_filtrada = filtra_df(df_parc_receit_extr, 'Recebimento_Parcela', ids_casas_selecionadas, start_date, end_date)
df_parc_receit_extr_filtrada = df_parc_receit_extr_filtrada[['ID_Receita','ID_Casa','Casa','Cliente','Data_Ocorrencia','Vencimento_Parcela','Recebimento_Parcela','Valor_Parcela','Classif_Receita','Status_Pgto','Observacoes']]

# Exibe df com aggrid
df_parc_receit_extr_filtrada_aggrid, tam_df_parc_receit_extr_filtrada_aggrid = dataframe_aggrid(
    df=df_parc_receit_extr_filtrada,
    name="Parcelas Receitas Extraordinárias",
    num_columns=["Valor_Parcela"],     
    date_columns=['Data_Ocorrencia', 'Vencimento_Parcela', 'Recebimento_Parcela']              
)

# Calcula total dos valores filtrados
total_valores_filtrados(df_parc_receit_extr_filtrada_aggrid, tam_df_parc_receit_extr_filtrada_aggrid, 'Valor_Parcela')

# Botão para excel
function_copy_dataframe_as_tsv(df_parc_receit_extr_filtrada_aggrid)

st.divider()

## Eventos
st.subheader("Eventos")
df_eventos_filtrada = filtra_df(df_eventos, 'Recebimento_Parcela', ids_casas_selecionadas, start_date, end_date)
df_eventos_filtrada = df_eventos_filtrada[['ID_Evento', 'Nome_Evento', 'ID_Casa', 'Casa', 'ID_Parcela', 'Valor_Parcela', 'Vencimento_Parcela', 'Recebimento_Parcela', 'Status_Pgto', 'Forma_Pgto', 'Observacoes']]

# Exibe df com aggrid
df_eventos_filtrada_aggrid, tam_df_eventos_filtrada_aggrid = dataframe_aggrid(
    df=df_eventos_filtrada,
    name="Eventos",
    num_columns=["Valor_Parcela"],      
    date_columns=['Vencimento_Parcela', 'Recebimento_Parcela']              
)

# Calcula total dos valores filtrados
total_valores_filtrados(df_eventos_filtrada_aggrid, tam_df_eventos_filtrada_aggrid, 'Valor_Parcela')

# Botão para excel
function_copy_dataframe_as_tsv(df_eventos_filtrada_aggrid)

st.divider()

## Desbloqueios Judiciais
st.subheader("Desbloqueios Judiciais")
df_desbloqueios_filtrada = filtra_df(df_bloqueios, 'Data_Transacao', ids_casas_selecionadas, start_date, end_date)
df_desbloqueios_filtrada = df_desbloqueios_filtrada[df_desbloqueios_filtrada['Valor'] > 0]
df_desbloqueios_filtrada = df_desbloqueios_filtrada[['ID_Bloqueio', 'ID_Casa', 'Casa', 'Data_Transacao', 'Valor', 'Observacao']]

# Exibe df com aggrid
df_desbloqueios_filtrada_aggrid, tam_df_desbloqueios_filtrada_aggrid = dataframe_aggrid(
    df=df_desbloqueios_filtrada,
    name="Desbloqueios Judiciais",
    num_columns=["Valor"],      
    date_columns=['Data_Transacao']              
)

# Calcula total dos valores filtrados
total_valores_filtrados(df_desbloqueios_filtrada_aggrid, tam_df_desbloqueios_filtrada_aggrid, 'Valor')

# Botão para excel
function_copy_dataframe_as_tsv(df_desbloqueios_filtrada_aggrid)

st.divider()

## Despesas ## 
st.markdown("""
    <h2 style="color: #DC143C; font-weight: bold;">Despesas</h1>
    """, unsafe_allow_html=True)

## Custos BlueMe Sem Parcelamento
st.subheader("Despesas BlueMe Sem Parcelamento")
df_custos_blueme_sem_parcelam_filtrada = filtra_df(df_custos_blueme_sem_parcelam, 'Realizacao_Pgto', ids_casas_selecionadas, start_date, end_date)
df_custos_blueme_sem_parcelam_filtrada = df_custos_blueme_sem_parcelam_filtrada[['ID_Despesa','ID_Casa','Casa','Fornecedor','Valor','Data_Vencimento','Previsao_Pgto','Realizacao_Pgto','Data_Competencia','Class_Cont_1','Class_Cont_2','Status_Pgto']]

# Exibe df com aggrid
df_custos_blueme_sem_parcelam_filtrada_aggrid, tam_df_custos_blueme_sem_parcelam_filtrada_aggrid = dataframe_aggrid(
    df=df_custos_blueme_sem_parcelam_filtrada,
    name="Despesas BlueMe Sem Parcelamento",
    num_columns=["Valor"],      
    date_columns=['Data_Vencimento', 'Previsao_Pgto', 'Realizacao_Pgto', 'Data_Competencia']
)

# Calcula total dos valores filtrados
total_valores_filtrados(df_custos_blueme_sem_parcelam_filtrada_aggrid, tam_df_custos_blueme_sem_parcelam_filtrada_aggrid, 'Valor')

# Botão para excel
function_copy_dataframe_as_tsv(df_custos_blueme_sem_parcelam_filtrada_aggrid)

st.divider()

## Custos BlueMe Com Parcelamento
st.subheader("Despesas BlueMe Com Parcelamento")
df_custos_blueme_com_parcelam_filtrada = filtra_df(df_custos_blueme_com_parcelam, 'Realiz_Parcela', ids_casas_selecionadas, start_date, end_date)
df_custos_blueme_com_parcelam_filtrada = df_custos_blueme_com_parcelam_filtrada[['ID_Parcela','ID_Despesa','Casa','ID_Casa','Fornecedor','Qtd_Parcelas','Num_Parcela','Valor_Parcela','Vencimento_Parcela','Realiz_Parcela','Valor_Original','Class_Cont_1','Class_Cont_2','Status_Pgto']]

# Exibe df com aggrid
df_custos_blueme_com_parcelam_filtrada_aggrid, tam_df_custos_blueme_com_parcelam_filtrada_aggrid = dataframe_aggrid(
    df=df_custos_blueme_com_parcelam_filtrada,
    name="Despesas Com Parcelamento",
    num_columns=["Valor_Parcela", "Valor_Original"],      
    date_columns=['Vencimento_Parcela', 'Realiz_Parcela']
)

# Calculando total dos valores filtrados
total_valores_filtrados(df_custos_blueme_com_parcelam_filtrada_aggrid, tam_df_custos_blueme_com_parcelam_filtrada_aggrid, 'Valor_Parcela', despesa_com_parc=True)

# Botão para excel
function_copy_dataframe_as_tsv(df_custos_blueme_com_parcelam_filtrada_aggrid)

st.divider()

## Bloqueios Judiciais
st.subheader("Bloqueios Judiciais")
df_bloqueios_filtrada = filtra_df(df_bloqueios, 'Data_Transacao', ids_casas_selecionadas, start_date, end_date)
df_bloqueios_filtrada = df_bloqueios_filtrada[df_bloqueios_filtrada['Valor'] < 0]
df_bloqueios_filtrada = df_bloqueios_filtrada[['ID_Bloqueio', 'ID_Casa', 'Casa', 'Data_Transacao', 'Valor', 'Observacao']]

df_bloqueios_filtrada_aggrid, tam_df_bloqueios_filtrada_aggrid = dataframe_aggrid(
    df=df_bloqueios_filtrada,
    name="Bloqueios Judiciais",
    num_columns=["Valor"],      
    date_columns=['Data_Transacao']              
)

# Calcula total dos valores filtrados
total_valores_filtrados(df_bloqueios_filtrada_aggrid, tam_df_bloqueios_filtrada_aggrid, 'Valor')

# Botão para excel
function_copy_dataframe_as_tsv(df_bloqueios_filtrada_aggrid)

st.divider()

## Mutuos ##
st.markdown("""
    <h2 style="color: orange; font-weight: bold;">Mútuos</h1>
    """, unsafe_allow_html=True)

## Entradas Mútuos
st.subheader("Entradas Mútuos")
df_entradas_mutuos_filtrada = filtra_df(df_mutuos, 'Data_Mutuo', ids_casas_selecionadas, start_date, end_date, entradas_mutuos=True)
df_entradas_mutuos_filtrada = df_entradas_mutuos_filtrada[['Mutuo_ID', 'ID_Casa_Entrada', 'Casa_Entrada', 'ID_Casa_Saida', 'Casa_Saida', 'Data_Mutuo', 'Valor', 'Observacoes']]

# Exibe df com aggrid
df_entradas_mutuos_filtrada_aggrid, tam_df_entradas_mutuos_filtrada_aggrid = dataframe_aggrid(
    df=df_entradas_mutuos_filtrada,
    name="Entradas Mútuos",
    num_columns=["Valor"],      
    date_columns=['Data_Mutuo']              
)

# Calcula total dos valores filtrados
total_valores_filtrados(df_entradas_mutuos_filtrada_aggrid, tam_df_entradas_mutuos_filtrada_aggrid, 'Valor')

# Botão para excel
function_copy_dataframe_as_tsv(df_entradas_mutuos_filtrada_aggrid)

st.divider()

## Saidas Mútuos
st.subheader("Saídas Mútuos")
df_saidas_mutuos_filtrada = filtra_df(df_mutuos, 'Data_Mutuo', ids_casas_selecionadas, start_date, end_date, saidas_mutuos=True)
df_saidas_mutuos_filtrada = df_saidas_mutuos_filtrada[['Mutuo_ID', 'ID_Casa_Entrada', 'Casa_Entrada', 'ID_Casa_Saida', 'Casa_Saida', 'Data_Mutuo', 'Valor', 'Observacoes']]

# Exibe df com aggrid
df_saidas_mutuos_filtrada_aggrid, tam_df_saidas_mutuos_filtrada_aggrid = dataframe_aggrid(
    df=df_saidas_mutuos_filtrada,
    name="Saídas Mútuos",
    num_columns=["Valor"],      
    date_columns=['Data_Mutuo']              
)

# Calcula total dos valores filtrados
total_valores_filtrados(df_saidas_mutuos_filtrada_aggrid, tam_df_saidas_mutuos_filtrada_aggrid, 'Valor')

# Botão para excel
function_copy_dataframe_as_tsv(df_saidas_mutuos_filtrada_aggrid)

st.divider()


# Preparando dados para os gráficos - Fluxo de Caixa por Mês e Fluxo Líquido por Mês
df_consolidado = prepare_monthly_data(
    df_extrato_zig_filtrada, 
    df_parc_receit_extr_filtrada, 
    df_eventos_filtrada, 
    df_desbloqueios_filtrada,
    df_custos_blueme_sem_parcelam_filtrada,
    df_custos_blueme_com_parcelam_filtrada,
    df_bloqueios_filtrada
)

## Gráfico Consolidado - Fluxo de Caixa por Mês
st.subheader("📊 Fluxo de Caixa Consolidado por Mês")

# Criando o gráfico
try:
    if not df_consolidado.empty:
        # Criando gráfico de barras personalizado
        fig = go.Figure()
        
        # Obtendo todos os meses únicos
        meses_unicos = sorted(df_consolidado['Mes_Ano_Str'].unique())

        # Adicionando barras de receitas
        receitas_data = df_consolidado[df_consolidado['Categoria'] == 'Receitas']
        for tipo in receitas_data['Tipo'].unique():
            dados_tipo = receitas_data[receitas_data['Tipo'] == tipo]
            valores = []
            for mes in meses_unicos:
                valor = dados_tipo[dados_tipo['Mes_Ano_Str'] == mes]['Valor'].sum()
                valores.append(valor)
                
            if tipo == 'Extrato Zig': 
                cor = "#0F3F24" 
                name = 'Receitas - Extrato Zig'
            if tipo == 'Extraordinária': 
                cor = "#1F7544"
                name = 'Receitas Extraordinárias'
            if tipo == 'Eventos': 
                cor = "#36A867"
                name = 'Receitas - Eventos'
            if tipo == 'Desbloqueios': 
                cor = '#32CD32'
                name = 'Receitas - Desbloqueios Judiciais'

            fig.add_trace(go.Bar(
                x=meses_unicos,
                y=valores,
                name=name,
                marker_color=cor,
                offsetgroup='Receitas'
            ))
        
        # Adicionando barras de despesas
        despesas_data = df_consolidado[df_consolidado['Categoria'] == 'Despesas']
        for tipo in despesas_data['Tipo'].unique():
            dados_tipo = despesas_data[despesas_data['Tipo'] == tipo]
            valores = []
            for mes in meses_unicos:
                valor = dados_tipo[dados_tipo['Mes_Ano_Str'] == mes]['Valor'].sum()
                valores.append(valor)
            
            if tipo == 'Sem Parcelamento': 
                cor = "#82001A" 
                name = 'Despesas Sem Parcelamento'
            if tipo == 'Com Parcelamento': 
                cor = '#DC143C'
                name = 'Despesas Com Parcelamento'
            if tipo == 'Bloqueios': 
                cor = "#F98F7D"
                name = 'Despesas - Bloqueios Judiciais'

            fig.add_trace(go.Bar(
                x=meses_unicos,
                y=valores,
                name=name,
                marker_color=cor,
                offsetgroup='Despesas'
            ))

        # Personalizando o layout
        casas_titulo = ', '.join(casas_selecionadas) if len(casas_selecionadas) <= 3 else f"{len(casas_selecionadas)} casas selecionadas"
        fig.update_layout(
            title=f'Fluxo de Caixa Consolidado - {casas_titulo} ({start_date.strftime("%d/%m/%Y")} a {end_date.strftime("%d/%m/%Y")})',
            xaxis_title="Mês/Ano",
            yaxis_title="Valor (R$)",
            barmode='stack',
            height=600,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            bargap=0.3,  # Espaço entre grupos de barras (meses)
            bargroupgap=0.0  # Sem espaço entre barras do mesmo grupo (receitas e despesas do mesmo mês)
        )
        
        # Formatando eixo Y para moeda brasileira
        fig.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
        
        # Exibindo o gráfico
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.warning("Não há dados disponíveis para o período e casas selecionadas.")

except Exception as e:
    st.error(f"Erro ao gerar gráfico: {str(e)}")

st.divider()        

## Gráfico Consolidado - Fluxo Líquido por Mês
st.subheader("📈 Fluxo Líquido por Mês")

# Calculando fluxo líquido
receitas_mensais = df_consolidado[df_consolidado['Categoria'] == 'Receitas'].groupby('Mes_Ano_Str')['Valor'].sum()
despesas_mensais = df_consolidado[df_consolidado['Categoria'] == 'Despesas'].groupby('Mes_Ano_Str')['Valor'].sum()

fluxo_liquido = pd.DataFrame({
    'Mes_Ano_Str': receitas_mensais.index,
    'Receitas': receitas_mensais.values,
    'Despesas': despesas_mensais.values
})

fluxo_liquido['Fluxo_Liquido'] = fluxo_liquido['Receitas'] - fluxo_liquido['Despesas']
fluxo_liquido['Receitas'] = fluxo_liquido['Receitas'].fillna(0)
fluxo_liquido['Despesas'] = fluxo_liquido['Despesas'].fillna(0)

# Gráfico de linha para fluxo líquido
fig_liquido = go.Figure()

fig_liquido.add_trace(go.Scatter(
    x=fluxo_liquido['Mes_Ano_Str'],
    y=fluxo_liquido['Fluxo_Liquido'],
    mode='lines+markers',
    name='Fluxo Líquido',
    line=dict(color='#1f77b4', width=3),
    marker=dict(size=8)
))

fig_liquido.add_trace(go.Scatter(
    x=fluxo_liquido['Mes_Ano_Str'],
    y=fluxo_liquido['Receitas'],
    mode='lines+markers',
    name='Receitas Totais',
    line=dict(color='#2E8B57', width=2, dash='dash'),
    marker=dict(size=6)
))

fig_liquido.add_trace(go.Scatter(
    x=fluxo_liquido['Mes_Ano_Str'],
    y=fluxo_liquido['Despesas'],
    mode='lines+markers',
    name='Despesas Totais',
    line=dict(color='#DC143C', width=2, dash='dash'),
    marker=dict(size=6)
))

# Adicionando linha horizontal em y=0
fig_liquido.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

fig_liquido.update_layout(
    title=f'Fluxo Líquido Mensal - {casas_titulo} ({start_date.strftime("%d/%m/%Y")} a {end_date.strftime("%d/%m/%Y")})',
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

fig_liquido.update_yaxes(tickformat=",.0f", tickprefix="R$ ")

st.plotly_chart(fig_liquido, use_container_width=True)

st.divider()

# Tabela Dinâmica - Class_Cont_0 (Agrupamento)
st.subheader("📊 Despesas por Classificação Contábil (Class_Cont_0)")

# Preparando dados para Class_Cont_0
def prepare_pivot_data_class0():
    # Despesas - BlueMe Sem Parcelamento (aplicando filtro de data)
    despesas_sem_parc = df_custos_blueme_sem_parcelam_filtrada.copy()
    despesas_sem_parc["Realizacao_Pgto"] = pd.to_datetime(despesas_sem_parc["Realizacao_Pgto"], errors="coerce")
    despesas_sem_parc = despesas_sem_parc[(despesas_sem_parc["Realizacao_Pgto"] >= start_date) & (despesas_sem_parc["Realizacao_Pgto"] <= end_date)]
    despesas_sem_parc['Mes_Ano'] = despesas_sem_parc['Realizacao_Pgto'].dt.to_period('M')
    despesas_sem_parc['Valor'] = (
        despesas_sem_parc['Valor']
        .astype(str)                 # garante que tudo é string
        .str.replace('.', '', regex=False)  # remove pontos de milhar
        .str.replace(',', '.', regex=False) # troca vírgula por ponto
    )
    despesas_sem_parc['Valor'] = pd.to_numeric(despesas_sem_parc['Valor'], errors='coerce')

    
    # Despesas - BlueMe Com Parcelamento (aplicando filtro de data)
    despesas_com_parc = df_custos_blueme_com_parcelam_filtrada.copy()
    despesas_com_parc["Realiz_Parcela"] = pd.to_datetime(despesas_com_parc["Realiz_Parcela"], errors="coerce")
    despesas_com_parc = despesas_com_parc[(despesas_com_parc["Realiz_Parcela"] >= start_date) & (despesas_com_parc["Realiz_Parcela"] <= end_date)]
    despesas_com_parc['Mes_Ano'] = despesas_com_parc['Realiz_Parcela'].dt.to_period('M')
    despesas_com_parc['Valor_Parcela'] = (
    despesas_com_parc['Valor_Parcela']
        .astype(str)                 # garante que tudo é string
        .str.replace('.', '', regex=False)  # remove pontos de milhar
        .str.replace(',', '.', regex=False) # troca vírgula por ponto
    )
    despesas_com_parc['Valor_Parcela'] = pd.to_numeric(despesas_com_parc['Valor_Parcela'], errors='coerce')


    # Combinando dados
    if not despesas_sem_parc.empty:
        despesas_sem_parc_grouped = despesas_sem_parc.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor'].sum().reset_index()
    else:
        despesas_sem_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Mes_Ano', 'Valor'])
        
    if not despesas_com_parc.empty:
        despesas_com_parc_grouped = despesas_com_parc.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor_Parcela'].sum().reset_index()
        despesas_com_parc_grouped = despesas_com_parc_grouped.rename(columns={'Valor_Parcela': 'Valor'})
    else:
        despesas_com_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Mes_Ano', 'Valor'])
    
    # Combinando os resultados
    all_despesas = pd.concat([despesas_sem_parc_grouped, despesas_com_parc_grouped], ignore_index=True)
    
    # Agrupando novamente para consolidar
    if not all_despesas.empty:
        despesas_consolidadas = all_despesas.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor'].sum().reset_index()
        
        # Adicionando Class_Cont_0 baseado no mapeamento
        despesas_consolidadas['Class_Cont_0'] = despesas_consolidadas['Class_Cont_1'].map(mapeamento_class_cont)
        
        # Para Class_Cont_1 não mapeadas, usar a própria Class_Cont_1
        despesas_consolidadas['Class_Cont_0'] = despesas_consolidadas['Class_Cont_0'].fillna(despesas_consolidadas['Class_Cont_1'])
        
        # Agrupando por Class_Cont_0
        despesas_class0 = despesas_consolidadas.groupby(['Class_Cont_0', 'Mes_Ano'])['Valor'].sum().reset_index()
        return despesas_class0
    else:
        return pd.DataFrame()

# Obtendo dados para Class_Cont_0
df_class0_data = prepare_pivot_data_class0()

if not df_class0_data.empty:
    # Criando tabela dinâmica para Class_Cont_0
    pivot_table_class0 = df_class0_data.pivot(
        index='Class_Cont_0',
        columns='Mes_Ano',
        values='Valor'
    ).fillna(0)
    
    # Convertendo índices de coluna para string
    pivot_table_class0.columns = pivot_table_class0.columns.astype(str)
    
    # Adicionando coluna de total
    pivot_table_class0['Total'] = pivot_table_class0.sum(axis=1)
    
    # Ordenando por total (maior para menor)
    pivot_table_class0 = pivot_table_class0.sort_values('Total', ascending=False)
    
    # Resetando o índice para incluir Class_Cont_0 como coluna
    pivot_table_class0 = pivot_table_class0.reset_index()
    
    # Separando colunas numéricas das de texto
    colunas_numericas_class0 = [col for col in pivot_table_class0.columns if col != 'Class_Cont_0']
    
    # Exibindo tabela dinâmica de Class_Cont_0
    df_pivot_class0_aggrid, tam_df_pivot_class0_aggrid = dataframe_aggrid(
        df=pivot_table_class0,
        name="Despesas por Classificação Contábil (Class_Cont_0)",
        num_columns=colunas_numericas_class0
    )
    
    # Botão para copiar dados de Class_Cont_0
    function_copy_dataframe_as_tsv(df_pivot_class0_aggrid)
    
    st.markdown("---")

# Tabela Dinâmica - Class_Cont_1 (Detalhamento)
st.subheader("📊 Despesas por Classificação Contábil (Class_Cont_1)")

# Preparando dados para a tabela dinâmica
def prepare_pivot_data():
    # Despesas - BlueMe Sem Parcelamento (aplicando filtro de data)
    despesas_sem_parc = df_custos_blueme_sem_parcelam_filtrada.copy()
    despesas_sem_parc['Realizacao_Pgto'] = pd.to_datetime(despesas_sem_parc['Realizacao_Pgto'], errors='coerce')
    despesas_sem_parc = despesas_sem_parc[(despesas_sem_parc["Realizacao_Pgto"] >= start_date) & (despesas_sem_parc["Realizacao_Pgto"] <= end_date)]
    despesas_sem_parc['Mes_Ano'] = despesas_sem_parc['Realizacao_Pgto'].dt.to_period('M')
    despesas_sem_parc['Valor'] = (
    despesas_sem_parc['Valor']
        .astype(str)                 # garante que tudo é string
        .str.replace('.', '', regex=False)  # remove pontos de milhar
        .str.replace(',', '.', regex=False) # troca vírgula por ponto
    )
    despesas_sem_parc['Valor'] = pd.to_numeric(despesas_sem_parc['Valor'], errors='coerce')

    
    # Despesas - BlueMe Com Parcelamento (aplicando filtro de data)
    despesas_com_parc = df_custos_blueme_com_parcelam_filtrada.copy()
    despesas_com_parc["Realiz_Parcela"] = pd.to_datetime(despesas_com_parc["Realiz_Parcela"], errors="coerce")
    despesas_com_parc = despesas_com_parc[(despesas_com_parc["Realiz_Parcela"] >= start_date) & (despesas_com_parc["Realiz_Parcela"] <= end_date)]
    despesas_com_parc['Mes_Ano'] = despesas_com_parc['Realiz_Parcela'].dt.to_period('M')
    despesas_com_parc['Valor_Parcela'] = (
    despesas_com_parc['Valor_Parcela']
        .astype(str)                 # garante que tudo é string
        .str.replace('.', '', regex=False)  # remove pontos de milhar
        .str.replace(',', '.', regex=False) # troca vírgula por ponto
    )
    despesas_com_parc['Valor_Parcela'] = pd.to_numeric(despesas_com_parc['Valor_Parcela'], errors='coerce')

    
    # Combinando dados
    if not despesas_sem_parc.empty:
        despesas_sem_parc_grouped = despesas_sem_parc.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor'].sum().reset_index()
    else:
        despesas_sem_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Mes_Ano', 'Valor'])
        
    if not despesas_com_parc.empty:
        despesas_com_parc_grouped = despesas_com_parc.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor_Parcela'].sum().reset_index()
        despesas_com_parc_grouped = despesas_com_parc_grouped.rename(columns={'Valor_Parcela': 'Valor'})
    else:
        despesas_com_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Mes_Ano', 'Valor'])
    

    # Combinando os resultados
    all_despesas = pd.concat([despesas_sem_parc_grouped, despesas_com_parc_grouped], ignore_index=True)
    
    # Agrupando novamente para consolidar
    if not all_despesas.empty:
        despesas_consolidadas = all_despesas.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor'].sum().reset_index()
        
        # Criando tabela dinâmica usando pivot
        pivot_table = despesas_consolidadas.pivot(
            index='Class_Cont_1',
            columns='Mes_Ano',
            values='Valor'
        ).fillna(0)
        
        # Convertendo índices de coluna para string
        pivot_table.columns = pivot_table.columns.astype(str)
        
        # Adicionando coluna de total
        pivot_table['Total'] = pivot_table.sum(axis=1)
        
        # Ordenando por total (maior para menor)
        pivot_table = pivot_table.sort_values('Total', ascending=False)
        
        # Resetando o índice para incluir Class_Cont_1 como coluna
        pivot_table = pivot_table.reset_index()
        
        return pivot_table
    else:
        return pd.DataFrame()

# Criando a tabela dinâmica
try:
    pivot_table = prepare_pivot_data()
    
    if not pivot_table.empty:
        # Separando colunas numéricas das de texto
        colunas_numericas = [col for col in pivot_table.columns if col != 'Class_Cont_1']
        
        # Exibindo tabela dinâmica
        df_pivot_aggrid, tam_df_pivot_aggrid = dataframe_aggrid(
            df=pivot_table,
            name="Tabela Dinâmica - Despesas por Classificação e Mês",
            num_columns=colunas_numericas,  # Apenas colunas numéricas
        )
        
        # Botão para copiar dados
        function_copy_dataframe_as_tsv(df_pivot_aggrid)
        
        # Tabela Dinâmica - Detalhamento por Class_Cont_2
        st.subheader("📋 Detalhamento por Subclassificação Contábil")
        
        # Preparando dados para Class_Cont_2
        def prepare_pivot_data_class2():
            # Despesas - BlueMe Sem Parcelamento (aplicando filtro de data)
            despesas_sem_parc = df_custos_blueme_sem_parcelam_filtrada.copy()
            despesas_sem_parc["Realizacao_Pgto"] = pd.to_datetime(despesas_sem_parc["Realizacao_Pgto"], errors="coerce")
            despesas_sem_parc = despesas_sem_parc[(despesas_sem_parc["Realizacao_Pgto"] >= start_date) & (despesas_sem_parc["Realizacao_Pgto"] <= end_date)]
            despesas_sem_parc['Mes_Ano'] = despesas_sem_parc['Realizacao_Pgto'].dt.to_period('M')
            despesas_sem_parc['Valor'] = (
            despesas_sem_parc['Valor']
                .astype(str)                 # garante que tudo é string
                .str.replace('.', '', regex=False)  # remove pontos de milhar
                .str.replace(',', '.', regex=False) # troca vírgula por ponto
            )
            despesas_sem_parc['Valor'] = pd.to_numeric(despesas_sem_parc['Valor'], errors='coerce')

            
            # Despesas - BlueMe Com Parcelamento (aplicando filtro de data)
            despesas_com_parc = df_custos_blueme_com_parcelam_filtrada.copy()
            despesas_com_parc["Realiz_Parcela"] = pd.to_datetime(despesas_com_parc["Realiz_Parcela"], errors="coerce")
            despesas_com_parc = despesas_com_parc[(despesas_com_parc["Realiz_Parcela"] >= start_date) & (despesas_com_parc["Realiz_Parcela"] <= end_date)]
            despesas_com_parc['Mes_Ano'] = despesas_com_parc['Realiz_Parcela'].dt.to_period('M')
            despesas_com_parc['Valor_Parcela'] = (
            despesas_com_parc['Valor_Parcela']
                .astype(str)                 # garante que tudo é string
                .str.replace('.', '', regex=False)  # remove pontos de milhar
                .str.replace(',', '.', regex=False) # troca vírgula por ponto
            )
            despesas_com_parc['Valor_Parcela'] = pd.to_numeric(despesas_com_parc['Valor_Parcela'], errors='coerce')

            
            # Combinando dados
            if not despesas_sem_parc.empty:
                despesas_sem_parc_grouped = despesas_sem_parc.groupby(['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano'])['Valor'].sum().reset_index()
            else:
                despesas_sem_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano', 'Valor'])
                
            if not despesas_com_parc.empty:
                despesas_com_parc_grouped = despesas_com_parc.groupby(['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano'])['Valor_Parcela'].sum().reset_index()
                despesas_com_parc_grouped = despesas_com_parc_grouped.rename(columns={'Valor_Parcela': 'Valor'})
            else:
                despesas_com_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano', 'Valor'])

    
            # Combinando os resultados
            all_despesas = pd.concat([despesas_sem_parc_grouped, despesas_com_parc_grouped], ignore_index=True)
            
            # Agrupando novamente para consolidar
            if not all_despesas.empty:
                despesas_consolidadas = all_despesas.groupby(['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano'])['Valor'].sum().reset_index()
                return despesas_consolidadas
            else:
                return pd.DataFrame()
        
        # Obtendo dados para Class_Cont_2
        df_class2_data = prepare_pivot_data_class2()
        
        if not df_class2_data.empty:
            # Obtendo lista de Class_Cont_1 disponíveis
            classificacoes_disponiveis = sorted(df_class2_data['Class_Cont_1'].unique())
            
            # Selectbox para escolher a classificação
            classificacao_selecionada = st.selectbox(
                "Selecione a Classificação Contábil para ver os detalhes:",
                classificacoes_disponiveis,
                index=0
            )
            
            # Filtrando dados para a classificação selecionada
            df_class2_filtrado = df_class2_data[df_class2_data['Class_Cont_1'] == classificacao_selecionada]
            
            if not df_class2_filtrado.empty:
                # Criando tabela dinâmica para Class_Cont_2
                pivot_table_class2 = df_class2_filtrado.pivot(
                    index='Class_Cont_2',
                    columns='Mes_Ano',
                    values='Valor'
                ).fillna(0)
                
                # Convertendo índices de coluna para string
                pivot_table_class2.columns = pivot_table_class2.columns.astype(str)
                
                # Adicionando coluna de total
                pivot_table_class2['Total'] = pivot_table_class2.sum(axis=1)
                
                # Ordenando por total (maior para menor)
                pivot_table_class2 = pivot_table_class2.sort_values('Total', ascending=False)
                
                # Resetando o índice para incluir Class_Cont_2 como coluna
                pivot_table_class2 = pivot_table_class2.reset_index()
                
                # Separando colunas numéricas das de texto
                colunas_numericas_class2 = [col for col in pivot_table_class2.columns if col != 'Class_Cont_2']
            
                # Exibindo tabela dinâmica de Class_Cont_2
                df_pivot_class2_aggrid, tam_df_pivot_class2_aggrid = dataframe_aggrid(
                    df=pivot_table_class2,
                    name=f"Detalhamento - {classificacao_selecionada}",
                    num_columns=colunas_numericas_class2
                )
                
                # Botão para copiar dados de Class_Cont_2
                function_copy_dataframe_as_tsv(df_pivot_class2_aggrid)
                
            else:
                st.warning(f"Não há dados de subclassificação disponíveis para {classificacao_selecionada}")
        else:
            st.warning("Não há dados de subclassificação disponíveis para o período e casas selecionadas.")
        
    else:
        st.warning("Não há dados de despesas disponíveis para o período e casas selecionadas.")
        
except Exception as e:
    st.error(f"Erro ao gerar tabela dinâmica: {str(e)}")

st.divider()

# Resumo estatístico
st.subheader("📋 Resumo Estatístico")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_receitas = df_consolidado[df_consolidado['Categoria'] == 'Receitas']['Valor'].sum()
    st.metric("Total Receitas", f"R$ {total_receitas:,.2f}")

with col2:
    total_despesas = df_consolidado[df_consolidado['Categoria'] == 'Despesas']['Valor'].sum()
    st.metric("Total Despesas", f"R$ {total_despesas:,.2f}")

with col3:
    fluxo_liquido_total = total_receitas - total_despesas
    st.metric("Fluxo Líquido", f"R$ {fluxo_liquido_total:,.2f}")

with col4:
    if total_receitas > 0:
        margem = (fluxo_liquido_total / total_receitas) * 100
        st.metric("Margem (%)", f"{margem:.1f}%")
    else:
        st.metric("Margem (%)", "N/A")

# Tabela de Referência - Mapeamento Class_Cont_0 ↔ Class_Cont_1
st.markdown("---")
st.subheader("📋 Tabela de Referência - Mapeamento de Classificações")
st.write("Mapeamento Class_Cont_0 ↔ Class_Cont_1")

# Criando DataFrame de referência
def create_mapping_reference():
    # Criando lista de mapeamentos
    mapping_list = []
    for class_cont_1, class_cont_0 in mapeamento_class_cont.items():
        mapping_list.append({
            'Class_Cont_0': class_cont_0,
            'Class_Cont_1': class_cont_1,
            'Status': 'Mapeado'
        })
    
    # Verificando Class_Cont_1 que aparecem nos dados mas não estão mapeadas
    all_class_cont_1 = set()
    
    # Despesas sem parcelamento
    if not df_custos_blueme_sem_parcelam_filtrada.empty:
        # Filtrando valores não nulos
        class_cont_1_sem_parc = df_custos_blueme_sem_parcelam_filtrada['Class_Cont_1'].dropna().unique()
        all_class_cont_1.update(class_cont_1_sem_parc)
    
    # Despesas com parcelamento
    if not df_custos_blueme_com_parcelam_filtrada.empty:
        # Filtrando valores não nulos
        class_cont_1_com_parc = df_custos_blueme_com_parcelam_filtrada['Class_Cont_1'].dropna().unique()
        all_class_cont_1.update(class_cont_1_com_parc)
    
    # Verificando quais não estão mapeadas
    unmapped = all_class_cont_1 - set(mapeamento_class_cont.keys())
    
    for class_cont_1 in sorted(unmapped):
        mapping_list.append({
            'Class_Cont_0': class_cont_1,  # Usa a própria Class_Cont_1
            'Class_Cont_1': class_cont_1,
            'Status': 'Não Mapeado'
        })
    
    return pd.DataFrame(mapping_list)

# Criando e exibindo tabela de referência
try:
    df_mapping_ref = create_mapping_reference()
    
    if not df_mapping_ref.empty:
        # Ordenando por Class_Cont_0 e depois por Class_Cont_1
        # Tratando valores None na ordenação
        df_mapping_ref = df_mapping_ref.sort_values(['Class_Cont_0', 'Class_Cont_1'], na_position='last')
        
        # Exibindo tabela de referência
        df_mapping_ref_aggrid, tam_df_mapping_ref_aggrid = dataframe_aggrid(
            df=df_mapping_ref,
            name="Mapeamento Class_Cont_0 ↔ Class_Cont_1"
        )
        
        # Botão para copiar dados de referência
        function_copy_dataframe_as_tsv(df_mapping_ref_aggrid)

        st.divider()
        
        # Resumo estatístico
        st.subheader("📋 Resumo Estatístico")
        total_mapped = len(df_mapping_ref[df_mapping_ref['Status'] == 'Mapeado'])
        total_unmapped = len(df_mapping_ref[df_mapping_ref['Status'] == 'Não Mapeado'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Classificações", len(df_mapping_ref))
        with col2:
            percentual_mapeadas = f"{total_mapped/len(df_mapping_ref)*100:.1f}%" if len(df_mapping_ref) > 0 else "N/A"
            st.metric("Mapeadas", total_mapped, delta=percentual_mapeadas)
        with col3:
            percentual_nao_mapeadas = f"{total_unmapped/len(df_mapping_ref)*100:.1f}%" if len(df_mapping_ref) > 0 else "N/A"
            st.metric("Não Mapeadas", total_unmapped, delta=percentual_nao_mapeadas)
        
        # Aviso sobre classificações não mapeadas
        if total_unmapped > 0:
            st.warning(f"⚠️ **Atenção**: {total_unmapped} classificação(ões) não possuem mapeamento definido e serão tratadas como Class_Cont_0 próprias.")
    else:
        st.info("Nenhuma classificação encontrada nos dados.")
        
except Exception as e:
    st.error(f"Erro ao gerar tabela de referência: {str(e)}")

