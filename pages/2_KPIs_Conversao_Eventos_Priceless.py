import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries import *
from utils.functions.parcelas import *
from utils.user import *
from utils.functions.kpis_conversao_eventos_priceless import *

st.set_page_config(
    page_icon="📈",
    page_title="KPI's de Vendas Priceless - Conversão de Eventos",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "loggedIn" not in st.session_state or not st.session_state["loggedIn"]:
    st.switch_page("Login.py")


def main():

    config_sidebar()

    # Recupera dados dos eventos
    df_eventos = GET_EVENTOS_PRICELESS_KPIS()
    df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()

    # Vendedores
    df_vendedores = df_eventos[['ID Responsavel Comercial', 'Comercial Responsável']].drop_duplicates().dropna()
    df_vendedores["ID Responsavel Comercial"] = df_vendedores["ID Responsavel Comercial"].astype(int)
    df_vendedores["ID - Responsavel"] = df_vendedores["ID Responsavel Comercial"].astype(str) + " - " + df_vendedores["Comercial Responsável"].astype(str)

    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("📈 KPI's de Vendas")
    with col2:
        st.button(label='Atualizar', key='atualizar_kpis_vendas', on_click=st.cache_data.clear)
    with col3:
        if st.button('Logout', key='logout_kpis_vendas'):
            logout()
    st.divider()

    # Adiciona selecao de mes e ano
    col1, col2, col3, col4= st.columns([1,1,1,1])
    with col1:
        ano = seletor_ano(2025, 2025, key="seletor_ano_kpi_conversao_eventos_priceless")
    with col2:
        mes = seletor_mes(
            "Selecionar mês:", key="seletor_mes_kpi_conversao_eventos_priceless"
        )
        mes = int(mes)
    with col3:
        id_vendedor, nome_vendedor = seletor_vendedor("Comercial Responsável:", df_vendedores, "seletor_vendedor_kpi_conversao_eventos")

    st.divider()

    col1, col2 = st.columns([6, 3])
    with col1:
        st.markdown("## Conversão de Eventos *")
    with col2:
        st.markdown("")
        st.markdown("")
        st.markdown("*Com base nos eventos lançados no mês selecionado.")
    st.divider()

    # Filtra por data de envio de proposta
    df_eventos_ano = df_filtrar_ano(df_eventos, 'Data Envio Proposta', ano)
    df_eventos = df_filtrar_mes(df_eventos_ano, 'Data Envio Proposta', mes)

    if id_vendedor != -1:
        df_eventos = df_eventos[df_eventos['ID Responsavel Comercial'] == id_vendedor]
        df_eventos_ano = df_eventos_ano[df_eventos_ano['ID Responsavel Comercial'] == id_vendedor]

    col1, col2, col3 = st.columns([1.1, 1.15, 3], gap="small", vertical_alignment="bottom")
    with col1:
        num_lancadas, num_confirmadas, num_declinadas, num_em_negociacao = calculo_numero_propostas(df_eventos, ano, mes)
        cards_numero_propostas(
            num_lancadas, num_confirmadas, num_declinadas, num_em_negociacao
        )
    with col2:
        valor_lancadas, valor_confirmadas, valor_declinadas, valor_em_negociacao = calculo_valores_propostas(df_eventos, ano, mes)
        valor_lancadas = format_brazilian(valor_lancadas)
        valor_confirmadas = format_brazilian(valor_confirmadas)
        valor_declinadas = format_brazilian(valor_declinadas)
        valor_em_negociacao = format_brazilian(valor_em_negociacao)
        cards_valor_propostas(
            valor_lancadas, valor_confirmadas, valor_declinadas, valor_em_negociacao
        )
    with col3:
        grafico_pizza_num_propostas(
            num_confirmadas, num_declinadas, num_em_negociacao
        )
        grafico_barras_num_propostas(df_eventos_ano)

if __name__ == "__main__":
    main()
