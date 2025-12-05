import streamlit as st
from utils.functions.general_functions import config_sidebar
from utils.queries_conciliacao import GET_CASAS
from utils.queries_forecast import GET_ITENS_VENDIDOS_DIA
from utils.functions.faturamento_dia_semana import *
from utils.functions.forecast import *
from utils.user import logout


st.set_page_config(
    page_title="Faturamento ZigPay - Média por dia da semana",
    page_icon=":moneybag:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

col1, col2, col3 = st.columns([6, 1, 1], vertical_alignment='center')
with col1:
    st.title(":moneybag: Faturamento ZigPay - Dias da semana")
with col2:
    st.button(label="Atualizar dados", on_click=st.cache_data.clear)
with col3:
    if st.button("Logout"):
        logout()
st.divider()

# Seletor de casa
df_casas = GET_CASAS()
casas = df_casas['Casa'].tolist()
casas = [c for c in casas if c not in ['All bar']]
casa = st.selectbox("Selecione uma casa:", casas)

# Obtendo o ID da casa selecionada
mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))
id_casa = mapeamento_casas[casa] 
st.divider()

# Query com todos os faturamentos da Zig
df_faturamento_diario = GET_ITENS_VENDIDOS_DIA()

# Filtrando por casa e gerando coluna com dia da semana
df_faturamento_diario_casa = prepara_dados_faturamento_casa(df_faturamento_diario, casa)

# Gera projeção para prox dias do mês corrente/seguinte por dia da semana
df_dias_futuros_com_categorias = lista_dias_mes_anterior_atual(
    datas['ano_atual'], 
    datas['mes_atual'], 
    datas['ultimo_dia_mes_atual'], 
    datas['ano_anterior'], 
    datas['mes_anterior'],
    datas['dois_meses_antes'],
    df_faturamento_diario_casa
)

df_dias_futuros_mes = cria_projecao_mes_corrente(df_faturamento_diario_casa, df_dias_futuros_com_categorias)

# Une meses já concluídos com mês corrente
df_faturamento_todos_meses = concatena_meses_reais_projetados(df_dias_futuros_mes, df_faturamento_diario_casa, id_casa, casa)

# Calcula faturamento geral por dia da semana para cada mês
pivot_faturamento_geral = calcula_faturamento_medio(df_faturamento_todos_meses)

# Formata e estiliza exibição
pivot_faturamento_geral = formata_df(pivot_faturamento_geral)
pivot_faturamento_geral = pivot_faturamento_geral.rename(columns={'Mes_Ano':'Mês-Ano'})
df_estilizado = pivot_faturamento_geral.style.apply(destaca_mes_atual_seguintes, axis=1)

st.subheader(f"Média de faturamento geral por dia da semana - {casa} - {datas['ano_atual']}")
st.dataframe(df_estilizado, hide_index=True, height=458)

# Exibe legenda
st.markdown(
    f"""
    <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
        <div style="width: 15px; height: 15px; background-color: #fff3b0; border: 1px solid #ccc; margin-right: 10px;"></div>
        <span style="font-size: 14px">Média de faturamento projetado (não real). Mês ainda não está concluído.</span>
    </div>
    """,
    unsafe_allow_html=True
)
st.divider()

# Detalhamento
st.subheader('Faturamento por categoria')
df_faturamento_categorias_todos_meses = df_faturamento_todos_meses[~df_faturamento_todos_meses['Categoria'].isna()].copy()

# Cria seletor
categorias_faturamento = df_faturamento_categorias_todos_meses['Categoria'].unique().tolist()
categoria_selecionada = st.selectbox("Selecione uma categoria:", categorias_faturamento)

# Calcula a média de faturamento de cada categoria por dia da semana
pivot_faturamento_categoria_dia_semana = calcula_faturamento_medio(df_faturamento_todos_meses, detalhamento_categoria=True, categoria_selecionada=categoria_selecionada)

# Formata e estiliza exibição
pivot_faturamento_categoria_dia_semana = formata_df(pivot_faturamento_categoria_dia_semana)
pivot_faturamento_categoria_dia_semana = pivot_faturamento_categoria_dia_semana.rename(columns={'Mes_Ano':'Mês-Ano'})
df_estilizado = pivot_faturamento_categoria_dia_semana.style.apply(destaca_mes_atual_seguintes, axis=1)
st.dataframe(df_estilizado, hide_index=True, height=458)

# Exibe legenda
st.markdown(
    f"""
    <div style="display: flex; align-items: center; padding:10px; border:1px solid #ccc; border-radius:8px";>
        <div style="width: 15px; height: 15px; background-color: #fff3b0; border: 1px solid #ccc; margin-right: 10px;"></div>
        <span style="font-size: 14px">Média de faturamento projetado (não real). Mês ainda não está concluído.</span>
    </div>
    """,
    unsafe_allow_html=True
)