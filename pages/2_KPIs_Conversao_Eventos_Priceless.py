import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries import *
from utils.functions.parcelas import *
from utils.user import *
from utils.functions.kpis_conversao_eventos_priceless import *
from utils.functions.faturamento import *

st.set_page_config(
    page_icon="📈",
    page_title="KPI's de Vendas Priceless",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "loggedIn" not in st.session_state or not st.session_state["loggedIn"]:
    st.switch_page("Login.py")

def main():

    config_sidebar()

    # Recupera dados dos eventos
    df_eventos = GET_EVENTOS_PRICELESS_KPIS()

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
    col1, col2, col3, col4= st.columns([0.5,0.5,0.5,1])
    with col1:
        ano = seletor_ano(2025, 2025, key="seletor_ano_kpi_conversao_eventos_priceless")
    with col2:
        mes = seletor_mes(
            "Selecionar mês:", key="seletor_mes_kpi_conversao_eventos_priceless"
        )
        mes = int(mes)
    with col3:
        id_vendedor, nome_vendedor = seletor_vendedor("Comercial Responsável:", df_vendedores, "seletor_vendedor_kpi_conversao_eventos")
    with col4:
        filtro_data_categoria = "Competência do Evento"
        filtro_data_categoria = st.segmented_control(
            label="Por Data de:",
            options=["Competência do Evento", "Recebimento do Lead", "Envio da Proposta"],
            selection_mode="single",
            default="Competência do Evento",
        )

    

    # Filtra por data
    if filtro_data_categoria:
        dict_filtro_data = {
            "Competência do Evento": "Data do Evento",
            "Recebimento do Lead": "Data Recebimento Lead",
            "Envio da Proposta": "Data Envio Proposta",
        }
        filtro_tipo_data = dict_filtro_data[filtro_data_categoria]
        st.divider()
        df_eventos_ano = df_filtrar_ano(df_eventos, filtro_tipo_data, ano)
        df_eventos = df_filtrar_mes(df_eventos_ano, filtro_tipo_data, mes)
    else:
        st.warning("Selecione um filtro de data.")
        st.stop()   

    if id_vendedor != -1:
        df_eventos = df_eventos[df_eventos['ID Responsavel Comercial'] == id_vendedor]
        df_eventos_ano = df_eventos_ano[df_eventos_ano['ID Responsavel Comercial'] == id_vendedor]

    col1, col2, col3 = st.columns([1.3, 1.5, 3], gap="small", vertical_alignment="top")
    with col1:
        num_leads_recebidos, num_lancadas, num_confirmadas, num_declinadas, num_em_negociacao = calculo_numero_propostas(df_eventos, ano, mes)
        cards_numero_propostas(
            num_leads_recebidos, num_lancadas, num_confirmadas, num_declinadas, num_em_negociacao
        )
    with col2:
        valor_leads_recebidos, valor_lancadas, valor_confirmadas, valor_declinadas, valor_em_negociacao = calculo_valores_propostas(df_eventos, ano, mes)
        valor_leads_recebidos = format_brazilian(valor_leads_recebidos)
        valor_lancadas = format_brazilian(valor_lancadas)
        valor_confirmadas = format_brazilian(valor_confirmadas)
        valor_declinadas = format_brazilian(valor_declinadas)
        valor_em_negociacao = format_brazilian(valor_em_negociacao)
        cards_valor_propostas(
            valor_leads_recebidos, valor_lancadas, valor_confirmadas, valor_declinadas, valor_em_negociacao
        )
    with col3:
        grafico_pizza_num_propostas(
            num_confirmadas, num_declinadas, num_em_negociacao
        )
        grafico_barras_num_propostas(df_eventos_ano)

    st.divider()
    col1, col2 = st.columns([1, 1], vertical_alignment = "bottom")
    with col1:
        st.markdown("### Eventos por status")
    with col2:
        options_eventos = ["Leads Recebidos", "Com Propostas Enviadas", "Confirmados", "Declinados", "Em Negociação"]
        selection = st.segmented_control(
            "Selecione o status do evento", options_eventos, selection_mode="single", key="segmented_control_kpi_conversao", label_visibility="collapsed"
        )

    # Formata datas
    df_eventos = format_columns_brazilian(df_eventos, ['Valor Total', 'Número de Pessoas', 'Valor AB', 'Valor Locação Total', 'Valor Imposto', 'Valor Locação Gerador', 'Valor Locação Mobiliário', 'Valor Locação Utensílios', 'Valor Mão de Obra Extra', 'Valor Taxa Administrativa', 'Valor Comissão BV', 'Valor Extras Gerais', 'Valor Taxa Serviço', 'Valor Acréscimo Forma Pagamento', 'Valor_Imposto'])
    df_eventos = df_formata_datas_sem_horario(df_eventos, ['Data Envio Proposta', 'Data de Contratação', 'Data do Evento', 'Data Recebimento Lead', 'Data Confirmação', 'Data Declínio', 'Data Em Negociação'])
    df_eventos = df_eventos.drop(columns=['ID Responsavel Comercial'])
    df_eventos_com_proposta_enviada = df_eventos[df_eventos['Data Envio Proposta'].notnull()]
    if selection == "Leads Recebidos":
        st.dataframe(df_eventos, use_container_width=True, hide_index=True)
        st.markdown(f"Número de Leads Recebidos: {len(df_eventos)}")
    elif selection == "Com Propostas Enviadas":
        st.dataframe(df_eventos_com_proposta_enviada[df_eventos_com_proposta_enviada['Data Envio Proposta'].notnull()], use_container_width=True, hide_index=True)
        st.markdown(f"Número de Propostas Enviadas: {len(df_eventos_com_proposta_enviada)}")
    elif selection == "Confirmados":
        st.dataframe(df_eventos[df_eventos['Status do Evento'] == 'Confirmado'], use_container_width=True, hide_index=True)
        st.markdown(f"Número de Eventos Confirmados: {len(df_eventos[df_eventos['Status do Evento'] == 'Confirmado'])}")
    elif selection == "Declinados":
        st.dataframe(df_eventos[df_eventos['Status do Evento'] == 'Declinado'], use_container_width=True, hide_index=True)
        st.markdown(f"Número de Eventos Declinados: {len(df_eventos[df_eventos['Status do Evento'] == 'Declinado'])}")
    elif selection == "Em Negociação":
        st.dataframe(df_eventos[df_eventos['Status do Evento'] == 'Em negociação'], use_container_width=True, hide_index=True)
        st.markdown(f"Número de Eventos em Negociação: {len(df_eventos[df_eventos['Status do Evento'] == 'Em negociação'])}")
    

if __name__ == "__main__":
        main()
