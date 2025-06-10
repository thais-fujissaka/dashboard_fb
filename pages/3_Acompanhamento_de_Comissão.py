import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries import *
from utils.functions.parcelas import *
from utils.user import *
from utils.functions.kpis_conversao_eventos_priceless import *
from utils.functions.acompanhamento_comissao import *
from streamlit_card import card


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
    df_recebimentos = GET_RECEBIMENTOS_EVENTOS()
    df_orcamentos = GET_ORCAMENTOS_EVENTOS()

    # Vendedores
    df_vendedores = df_recebimentos[['ID - Responsavel', 'ID Responsavel', 'Cargo']].drop_duplicates()

    # Formata valores monetários
    df_recebimentos['Valor Total Parcelas'] = df_recebimentos['Valor Total Parcelas'].astype(float)
    df_orcamentos['Valor'] = df_orcamentos['Valor'].astype(float)

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
        # Filtra por casa se não for "Todas as Casas"
        if id_casa != -1:
            df_recebimentos = df_recebimentos[df_recebimentos['ID Casa'] == id_casa]
            df_orcamentos = df_orcamentos[df_orcamentos['ID Casa'] == id_casa]
    with col1:
        ano = seletor_ano(2025, 2025, key="seletor_ano_kpi_comissao")
    with col2:
        mes = seletor_mes(
            "Selecionar mês:", key="seletor_mes_kpi_comissao"
        )
    with col3:
        id_vendedor, nome_vendedor = seletor_vendedor("Comercial Responsável:", df_vendedores, "seletor_vendedor_kpi_comissao")
    st.divider()

    # Verifica se há dados disponíveis para o mês e casa selecionados
    if df_recebimentos.empty and df_orcamentos.empty:
        st.error("Não há dados disponíveis de recebimentos e orçamentos para o mês e casa selecionados.")
        st.stop()
    elif df_recebimentos.empty:
        st.error("Não há dados disponíveis de recebimentos para o mês e casa selecionados.")
        st.stop()
    elif df_orcamentos.empty:
        st.error("Não há dados disponíveis de orçamentos para o mês e casa selecionados.")
        st.stop()
    
    # Filtra por ano e mês
    df_recebimentos = df_recebimentos[(df_recebimentos['Ano Recebimento'] == ano) & (df_recebimentos['Mês Recebimento'] == int(mes))]
    df_orcamentos = df_orcamentos[(df_orcamentos['Ano'] == ano) & (df_orcamentos['Mês'] == int(mes))]

    # Calcula o recebimento total do mês
    total_recebido_mes = df_recebimentos['Valor Total Parcelas'].sum()

    # Calcula o orcamento do mês
    orcamento_mes = df_orcamentos['Valor'].sum()

    # Filtra por vendedor
    if id_vendedor != -1:
        cargo_vendedor = df_vendedores[df_vendedores['ID Responsavel'] == id_vendedor]['Cargo'].values[0]
        df_recebimentos = df_recebimentos[df_recebimentos['ID Responsavel'] == id_vendedor]
        if not df_recebimentos.empty:
            valor_total_vendido = df_recebimentos['Valor Total Parcelas'].values[0]
        else:
            valor_total_vendido = 0
    else:
        cargo_vendedor = "Todos os vendedores"
        valor_total_vendido = total_recebido_mes

    # Calcula o percentual de atingimento da meta
    if orcamento_mes > 0:
        porcentagem_atingimento = (total_recebido_mes / orcamento_mes) * 100
    else:
        porcentagem_atingimento = 0
    
    # Verifica se o vendedor atingiu a meta
    meta_atingida = False
    if total_recebido_mes >= orcamento_mes:
        meta_atingida = True
    #st.dataframe(df_recebimentos, use_container_width=True, hide_index=True)

    
    comissao = calcular_comissao(df_recebimentos, orcamento_mes, meta_atingida)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Orçamento do Mês", f"R$ {format_brazilian(orcamento_mes)}", "white", "#31333F", "#31333F")
    with col2:
        kpi_card("Total Vendido/Recebido", f"R$ {format_brazilian(valor_total_vendido)}", "white", "#31333F", "#31333F")
    with col3:
        if meta_atingida:
            kpi_card("Atingimento da Meta", f"{format_brazilian(round(porcentagem_atingimento, 2))} %", "white", "#31333F", "#2ecc71")
        else:
            kpi_card("Atingimento da Meta", f"{format_brazilian(round(porcentagem_atingimento, 2))} %", "white", "#31333F", "#e74c3c")
    with col4:
        kpi_card("Comissão", f"R$ {format_brazilian(comissao)}", "white", "#31333F", "#31333F")


if __name__ == "__main__":
    main()
