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
    page_title="KPI's de Vendas Priceless - Comissões",
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
    df_orcamentos = GET_ORCAMENTOS_EVENTOS

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

    st.markdown("## Acompanhamento de Comissão")
    st.divider()

    # Adiciona selecao de mes e ano
    col0, col1, col2, col3= st.columns([1,1,1,1])
    with col0:
        lista_retirar_casas = ['Arcos', 'Bar Léo - Centro', 'Bar Léo - Vila Madalena', 'Blue Note - São Paulo', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Girondino - CCBB', 'Love Cabaret', 'Ultra Evil Premium Ltda ']
        id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='acompanhamento_comissao_casas')
    with col1:
        ano = seletor_ano(2025, 2025, key="seletor_ano_kpi_comissao")
    with col2:
        mes = seletor_mes(
            "Selecionar mês:", key="seletor_mes_kpi_comissao"
        )
        mes = int(mes)
    with col3:
        id_vendedor, nome_vendedor = seletor_vendedor("Comercial Responsável:", df_vendedores, "seletor_vendedor_kpi_comissao")

    st.divider()

    

    # Filtra por data de envio de proposta
    df_eventos_ano = df_filtrar_ano(df_eventos, 'Data Envio Proposta', ano)
    df_eventos = df_filtrar_mes(df_eventos_ano, 'Data Envio Proposta', mes)

    if id_vendedor != -1:
        df_eventos = df_eventos[df_eventos['ID Responsavel Comercial'] == id_vendedor]
        df_eventos_ano = df_eventos_ano[df_eventos_ano['ID Responsavel Comercial'] == id_vendedor]



if __name__ == "__main__":
    main()
