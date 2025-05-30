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

    # Busca vendedores

    st.title("📈 KPI's de Vendas Priceless")
    st.divider()

    # Adiciona selecao de mes e ano
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        ano = seletor_ano(2025, 2025, key="seletor_ano_kpi_conversao_eventos_priceless")
    with col2:
        mes = seletor_mes(
            "Selecionar mês:", key="seletor_mes_kpi_conversao_eventos_priceless"
        )
        mes = int(mes)
    st.divider()

    st.markdown("## Conversão de Eventos")
    st.divider()

    # Filtra por data de envio de proposta
    df_eventos = df_filtrar_ano(df_eventos, 'Data Envio Proposta', ano)
    df_eventos = df_filtrar_mes(df_eventos, 'Data Envio Proposta', mes)

    col1, col2, col3 = st.columns([1.1, 1.15, 3], gap="small", vertical_alignment="bottom")
    with col1:
        num_lancadas, num_confirmadas, num_declinadas, num_em_negociacao = calculo_numero_propostas(df_eventos, ano, mes)
        cards_numero_propostas(
            num_lancadas, num_confirmadas, num_declinadas, num_em_negociacao
        )
    with col2:
        valor_lancadas,valor_confirmadas, valor_declinadas, valor_em_negociacao = calculo_valores_propostas(df_eventos, ano, mes)
        cards_valor_propostas(
            valor_lancadas, valor_confirmadas, valor_declinadas, valor_em_negociacao
        )
    with col3:
        grafico_pizza_num_propostas(
            num_confirmadas, num_declinadas, num_em_negociacao
        )

if __name__ == "__main__":
    main()
