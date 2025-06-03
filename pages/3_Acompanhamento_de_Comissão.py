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

    # # Recupera dados dos eventos
    df_recebimentos = GET_RECEBIMENTOS_EVENTOS()
    df_orcamentos = GET_ORCAMENTOS_EVENTOS()

    # Vendedores
    df_vendedores = df_recebimentos[['ID - Responsavel']].drop_duplicates().dropna()

    # Header
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

    # Seletores
    col0, col1, col2, col3= st.columns([1,1,1,1])
    with col0:
        lista_retirar_casas = ['Arcos', 'Bar Léo - Centro', 'Bar Léo - Vila Madalena', 'Blue Note - São Paulo', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Girondino - CCBB', 'Love Cabaret', 'Ultra Evil Premium Ltda ']
        id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, key='acompanhamento_comissao_casas')
        # Filtra por casa
        df_recebimentos = df_recebimentos[df_recebimentos['ID Casa'] == id_casa]
        df_orcamentos = df_orcamentos[df_orcamentos['ID Casa'] == id_casa]
        
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

    
    # Filtra por ano e mês
    df_recebimentos = df_recebimentos[(df_recebimentos['Ano Recebimento'] == ano) & (df_recebimentos['Mês Recebimento'] == mes)]
    df_orcamentos = df_orcamentos[(df_orcamentos['Ano'] == ano) & (df_orcamentos['Mês'] == mes)]
    
    # st.dataframe(df_recebimentos, use_container_width=True)
    # st.dataframe(df_orcamentos, use_container_width=True)

    # Calcula o atingimento
    total_recebido_mes = df_recebimentos['Valor Total Parcelas'].sum()
    orcamento_mes = df_orcamentos['Valor'].values[0]
    print(f"Total Recebido no Mês: {total_recebido_mes}")
    print(f"Orçamento do Mês: {orcamento_mes}")
    meta_atingida = False
    if total_recebido_mes >= orcamento_mes:
        meta_atingida = True

    st.write(f"**Total Recebido no Mês: R$ {total_recebido_mes:,.2f}**")
    st.write(f"**Orçamento do Mês: R$ {orcamento_mes:,.2f}**")
    if meta_atingida:
        st.success("Meta Atingida!")
    else:
        st.error("Meta Não Atingida!")



if __name__ == "__main__":
    main()
