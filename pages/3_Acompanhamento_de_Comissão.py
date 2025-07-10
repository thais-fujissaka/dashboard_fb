import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries import *
from utils.functions.parcelas import *
from utils.user import *
from utils.functions.kpis_conversao_eventos_priceless import *
from utils.functions.acompanhamento_comissao import *
from utils.functions.faturamento import *


st.set_page_config(
    page_icon="📊",
    page_title="KPI's de Vendas - Cálculo da Comissão de Eventos",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "loggedIn" not in st.session_state or not st.session_state["loggedIn"]:
    st.switch_page("Login.py")

def main():
    st.markdown(" <style>iframe{ height: 320px !important } ", unsafe_allow_html=True)
    config_sidebar()

    # Header
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("📊 KPI's de Vendas - Cálculo da Comissão de Eventos")
    with col2:
        st.button(label='Atualizar', key='atualizar_kpis_vendas', on_click=st.cache_data.clear)
    with col3:
        if st.button('Logout', key='logout_kpis_vendas'):
            logout()
    st.divider()

    # Recupera dados dos eventos
    df_recebimentos = GET_RECEBIMENTOS_EVENTOS()
    df_orcamentos = GET_ORCAMENTOS_EVENTOS()
    df_eventos = GET_EVENTOS_COMISSOES()

    # Recupera dados dos eventos e parcelas para seção de faturamento
    df_orcamentos_faturamento = df_orcamentos.copy()
    df_eventos_faturamento = GET_EVENTOS_PRICELESS()
    df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()

    # Formata tipos de dados do dataframe de eventos
    tipos_de_dados_eventos = {
        'Valor_Locacao_Aroo_1': float,
        'Valor_Locacao_Aroo_2': float,
        'Valor_Locacao_Aroo_3': float,
        'Valor_Locacao_Anexo': float,
        'Valor_Locacao_Notie': float,
        'Valor_Locacao_Mirante': float,
        'Valor_Imposto': float,
        'Valor_AB': float,
        'Valor_Total': float,
        'Valor_Locacao_Total': float
    }
    df_eventos_faturamento = df_eventos_faturamento.astype(tipos_de_dados_eventos, errors='ignore')
    df_eventos_faturamento['Data_Contratacao'] = pd.to_datetime(df_eventos_faturamento['Data_Contratacao'], errors='coerce')
    df_eventos_faturamento['Data_Evento'] = pd.to_datetime(df_eventos_faturamento['Data_Evento'], errors='coerce')
    # Formata tipos de dados do dataframe de parcelas
    tipos_de_dados_parcelas = {
        'Valor_Parcela': float,
        'Categoria_Parcela': str
    }
    df_parcelas = df_parcelas.astype(tipos_de_dados_parcelas, errors='ignore')
    df_parcelas['Data_Vencimento'] = pd.to_datetime(df_parcelas['Data_Vencimento'], errors='coerce')
    df_parcelas['Data_Recebimento'] = pd.to_datetime(df_parcelas['Data_Recebimento'], errors='coerce')
    # Formata tipos de dados do dataframe de orcamentos
    tipos_de_dados_orcamentos = {
        'Valor': float
    }
    df_orcamentos_faturamento = df_orcamentos_faturamento.astype(tipos_de_dados_orcamentos, errors='ignore')
    # Adiciona coluna de concatenação de ID e Nome do Evento
    df_eventos_faturamento['ID_Nome_Evento'] = df_eventos_faturamento['ID_Evento'].astype(str) + " - " + df_eventos_faturamento['Nome_do_Evento']
    # Calcula o valor de repasse para Gazit
    df_eventos_faturamento = calcular_repasses_gazit(df_eventos_faturamento)


    # Faturamento por Categoria
    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            st.write("")
            st.markdown("## Faturamento de Eventos", help='Comparar Orçamento e Faturamento para verificar o atingimento da meta')
            st.divider()
            col1, col2 = st.columns([1, 1], gap="large")
            with col1:
                lista_retirar_casas = ['Arcos', 'Bar Léo - Centro', 'Bar Léo - Vila Madalena', 'Blue Note - São Paulo', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Girondino - CCBB', 'Love Cabaret']
                id_casa_faturamento, casa_faturamento, id_zigpay_faturamento = input_selecao_casas(lista_retirar_casas, key='faturamento_bruto_comissao')
            with col2:
                ano = seletor_ano(2024, 2025, key='ano_faturamento')
        filtro_data_categoria = "Recebimento (Caixa)"

        # Filtros parcelas
        df_parcelas_filtradas_por_status = filtrar_por_classe_selecionada(df_parcelas, 'Status Evento', ['Confirmado'])
        df_parcelas_filtradas_por_data = get_parcelas_por_tipo_data(df_parcelas_filtradas_por_status, df_eventos_faturamento, filtro_data_categoria, ano)

        # Filtros orcamentos
        df_orcamentos_faturamento = filtrar_por_classe_selecionada(df_orcamentos_faturamento, 'Ano', [ano])
        if casa_faturamento != "Todas as Casas":
            df_orcamentos_faturamento = filtrar_por_classe_selecionada(df_orcamentos_faturamento, 'ID Casa', [id_casa_faturamento])
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            if filtro_data_categoria is None:
                st.warning("Por favor, selecione um filtro de data.")
            if casa_faturamento == "Todas as Casas":
                montar_tabs_geral(df_parcelas_filtradas_por_data, casa_faturamento, id_casa_faturamento, filtro_data_categoria, df_orcamentos_faturamento)
            else:
                df_parcelas_casa = df_filtrar_casa(df_parcelas_filtradas_por_data, casa_faturamento)
                if casa_faturamento == "Priceless":
                    montar_tabs_priceless(df_parcelas_casa, id_casa_faturamento, df_eventos_faturamento, filtro_data_categoria, df_orcamentos_faturamento)
                else:
                    montar_tabs_geral(df_parcelas_casa, casa_faturamento, id_casa_faturamento, filtro_data_categoria, df_orcamentos_faturamento)
    st.write("")

    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            st.write("")
            st.markdown("## Cálculo da Comissão de Eventos")
            st.divider()
            # Vendedores
            df_vendedores = df_recebimentos[['ID - Responsavel', 'ID Responsavel', 'Comissão Com Meta Atingida', 'Comissão Sem Meta Atingida']].copy().drop_duplicates()

            # Formata valores monetários
            df_recebimentos['Valor da Parcela'] = df_recebimentos['Valor da Parcela'].astype(float)
            df_recebimentos['Comissão Com Meta Atingida'] = df_recebimentos['Comissão Com Meta Atingida'].astype(float)
            df_recebimentos['Comissão Sem Meta Atingida'] = df_recebimentos['Comissão Sem Meta Atingida'].astype(float)
            df_orcamentos['Valor'] = df_orcamentos['Valor'].astype(float)
            
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

            df_recebimentos = df_recebimentos[(df_recebimentos['Ano Recebimento'] == ano) & (df_recebimentos['Mês Recebimento'] == int(mes))]
            df_orcamentos = df_orcamentos[(df_orcamentos['Ano'] == ano) & (df_orcamentos['Mês'] == int(mes))]

            # Calcula o recebimento total do mês
            total_recebido_mes = df_recebimentos['Valor da Parcela'].sum()

            # Calcula o orcamento do mês
            orcamento_mes = df_orcamentos['Valor'].sum()

            # Filtra por vendedor
            if id_vendedor != -1:
                df_recebimentos = df_recebimentos[df_recebimentos['ID Responsavel'] == id_vendedor]
                if not df_recebimentos.empty:
                    valor_total_vendido = df_recebimentos['Valor da Parcela'].sum()
                else:
                    valor_total_vendido = 0
            else:
                cargo_vendedor = "Todos os vendedores"
                valor_total_vendido = df_recebimentos['Valor da Parcela'].sum()

            # Calcula o percentual de atingimento da meta
            if orcamento_mes > 0:
                porcentagem_atingimento = (total_recebido_mes / orcamento_mes) * 100
            else:
                porcentagem_atingimento = 0
            
            # Verifica se o vendedor atingiu a meta
            meta_atingida = False
            if total_recebido_mes >= orcamento_mes:
                meta_atingida = True

            # Calcula a comissão total para o mês, casa e vendedor(es) selecionados
            comissao = calcular_comissao(df_recebimentos, orcamento_mes, meta_atingida)

            # Visualização das parcelas
            if df_recebimentos.empty:
                st.warning("Não há recebimentos e comissões para os filtros selecionados.")
                st.stop()
            else:
                vendedores = df_recebimentos['ID - Responsavel'].unique().tolist()
                total_vendido = df_recebimentos['Valor da Parcela'].sum()
                for vendedor in vendedores:
                    df_vendedor = df_recebimentos[df_recebimentos['ID - Responsavel'] == vendedor].copy()
                    
                    # Define os tipos das colunas
                    df_vendedor['Ano Recebimento'] = df_vendedor['Ano Recebimento'].astype(int).astype(str)
                    df_vendedor['Mês Recebimento'] = df_vendedor['Mês Recebimento'].astype(int).astype(str)
                    if not df_vendedor.empty:
                        st.markdown(f"#### {vendedor}")
                        df_vendedor = df_vendedor[['Casa', 'ID Evento', 'Nome Evento', 'Ano Recebimento', 'Mês Recebimento', 'Categoria Parcela', 'Valor da Parcela', '% Comissão',  'Comissão']]
                        total_vendido_vendedor = df_vendedor['Valor da Parcela'].sum()
                        total_comissao = df_vendedor['Comissão'].sum()
                        lista_ids_eventos = df_vendedor['ID Evento'].unique().tolist()
                        df_vendedor = df_vendedor.astype({
                            'ID Evento': str,
                            'Valor da Parcela': str,
                            '% Comissão': str,
                            'Comissão': str,
                            'Ano Recebimento': str,
                            'Mês Recebimento': str,
                            'Categoria Parcela': str
                        })
                        linha_total = pd.DataFrame({
                            'Casa': ['Total'],
                            'ID Evento': [''],
                            'Nome Evento': [''],
                            'Valor da Parcela': [total_vendido_vendedor],
                            'Ano Recebimento': [''],
                            'Mês Recebimento': [''],
                            'Categoria Parcela': [''],
                            '% Comissão': [''],
                            'Comissão': [total_comissao]
                        })
                        df_vendedor = pd.concat([df_vendedor, linha_total], ignore_index=True)
                        df_vendedor = format_columns_brazilian(df_vendedor, ['Valor da Parcela', '% Comissão', 'Comissão'])
                        df_vendedor = df_vendedor.rename(columns={
                            'Ano Recebimento': 'Ano',
                            'Mês Recebimento': 'Mês'
                        })
                        df_vendedor = df_vendedor[['Casa', 'ID Evento', 'Nome Evento', 'Categoria Parcela', 'Ano', 'Mês', 'Valor da Parcela', '% Comissão', 'Comissão']]
                        df_vendedor_styled = df_vendedor.style.apply(highlight_total_row, axis=1)
                        # Verifique se há duplicação
                        
                        st.dataframe(df_vendedor_styled, use_container_width=True, hide_index=True)
                        with st.expander(f"Ver eventos correspondentes"):
                            
                            df_eventos_vendedor = df_eventos[df_eventos['ID Evento'].isin(lista_ids_eventos)]
                            df_eventos_vendedor = format_columns_brazilian(df_eventos_vendedor, ['Valor Total', 'Valor AB', 'Valor Imposto'])
                            st.dataframe(df_eventos_vendedor[['ID Evento', 'Casa', 'Nome Evento', 'Cliente', 'Data Contratacao', 'Data Evento', 'Valor Total', 'Valor AB', 'Valor Imposto', 'Status Evento']], use_container_width=True, hide_index=True)
                st.divider()

    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            # Exibe os KPIs
            st.markdown(f"## Resumo Final da Comissão - {casa} - {nome_vendedor} - {mes}/{ano}")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                kpi_card("Orçamento do Mês", f"R$ {format_brazilian(orcamento_mes)}", "rgb(30, 58, 138)", "white", "white")
            with col2:
                kpi_card("Faturamento do Mês", f"R$ {format_brazilian(total_recebido_mes)}", "rgb(30, 58, 138)", "white", "white")
            with col3:
                if meta_atingida:
                    kpi_card("Atingimento da Meta", f"{format_brazilian(porcentagem_atingimento)} %", "rgb(30, 58, 138)", "white", "rgb(0, 255, 100)")
                else:
                    kpi_card("Atingimento da Meta", f"{format_brazilian(porcentagem_atingimento)} %", "rgb(30, 58, 138)", "white", "rgb(255, 30, 30)")
            with col4:
                kpi_card("Total Vendido/Recebido no Mês", f"R$ {format_brazilian(total_vendido)}", "rgb(30, 58, 138)", "white", "white")
            with col5:
                kpi_card("Comissão", f"R$ {format_brazilian(comissao)}", "rgb(30, 58, 138)", "white", "white")
            st.html("<br>")

    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 2.6, 0.1], gap="large", vertical_alignment="center")
        with col2:
            st.write("")
            st.markdown("## Farol - Eventos sem Comercial Responsável")
            st.divider()

            df_eventos_sem_comercial = df_eventos_faturamento[df_eventos_faturamento['Comercial_Responsavel'].isnull()]
            df_eventos_sem_comercial = df_eventos_sem_comercial.rename(columns={
                'ID_Evento': 'ID Evento',
                'Nome_do_Evento': 'Nome Evento',
                'Comercial_Responsavel': 'Comercial Responsável',
                'Cliente': 'Cliente',
                'Data_Contratacao': 'Data Contratação',
                'Data_Evento': 'Data Evento',
                'Valor_Total': 'Valor Total',
                'Valor_AB': 'Valor AB',
                'Valor_Imposto': 'Valor Imposto',
                'Status_Evento': 'Status Evento',
                'Motivo_Declinio': 'Motivo Declínio',
                'Observacoes': 'Observações'
            })
            df_eventos_sem_comercial = df_formata_datas_sem_horario(df_eventos_sem_comercial, ['Data Evento', 'Data Contratação'])
            df_eventos_sem_comercial = format_columns_brazilian(df_eventos_sem_comercial, ['Valor Total', 'Valor AB', 'Valor Imposto'])
            st.dataframe(df_eventos_sem_comercial[['Casa','ID Evento', 'Nome Evento', 'Comercial Responsável', 'Cliente', 'Data Contratação', 'Data Evento', 'Valor Total', 'Valor AB', 'Valor Imposto', 'Status Evento', 'Motivo Declínio', 'Observações']], use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
