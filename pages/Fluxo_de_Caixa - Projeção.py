import streamlit as st
import pandas as pd
from utils.queries_fluxo_de_caixa import *
from utils.functions.general_functions import *
from utils.functions.fluxo_de_caixa_projecao import *
from utils.constants.general_constants import lojasAgrupadas
from datetime import datetime
from utils.user import logout
from utils.components import button_download
from utils.queries_conciliacao import GET_CASAS


st.set_page_config(
    page_title="Projeção", 
    page_icon=":material/chart_data:", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

config_sidebar()

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

col, col2, col3 = st.columns([6, 1, 1])
with col:
    st.title(":material/chart_data: Projeção - Despesas Aprovadas")
with col2:
    st.button(label="Atualizar dados", on_click=st.cache_data.clear)
with col3:
    if st.button("Logout"):
        logout()
st.divider()


# Bares exibidos nos seletores
lojasComDados = preparar_dados_lojas_user_projecao_fluxo() 
lojas_retirar = ['Bar Brahma Aeroclube', 'Brahma Aricanduva', 'Bar Brasilia -  Aeroporto', 'Bardassê', 'Bar Léo - Vila Madalena', 'Colorado Aeroporto BSB', 'Duroc ', 
                 'FDB DIGITAL PARTICIPACOES LTDA', 'FDB HOLDING INFERIOR LTDA', 'FDB HOLDING SUPERIOR LTDA', 'Filial', 'Hbar participacoes e empreendimentos ', 'Ilha das Flores ', 
                 'Lojinha - Brahma', 'Navarro', 'Patizal ', 'Tundra', 'Hotel Maraba', 'Brahma - Ribeirão']
lojasComDados = [loja for loja in lojasComDados if loja not in lojas_retirar]
lojasComDados = ["Todas as casas" if c == "All bar" else c for c in lojasComDados]

# Recuperando dados
df_saldos_bancarios = GET_SALDOS_BANCARIOS()                    # saldo inicio do dia atual de cada casa
df_valor_liquido = GET_VALOR_LIQUIDO_RECEBIDO()                 # valor liquido de receitas do dia atual de cada casa
df_projecao_zig = GET_PROJECAO_ZIG()                            # projecao faturamento da zig de cada casa para a semana
df_receitas_extraord_proj = GET_RECEITAS_EXTRAORD_FLUXO_CAIXA() # receit. extr. lançadas de cada casa para duas semanas
df_receitas_eventos_proj = GET_EVENTOS_FLUXO_CAIXA()            # eventos lançados de cada casa para duas semanas
df_despesas_aprovadas = GET_DESPESAS_APROVADAS()                # despesas aprovadas e pendentes de pagamento
df_despesas_pagas = GET_DESPESAS_PAGAS()                        # despesas pagas no período

df_projecao_bares_geral = config_projecao_bares(
    df_saldos_bancarios, 
    df_valor_liquido, 
    df_projecao_zig, 
    df_receitas_extraord_proj,
    df_receitas_eventos_proj,  
    df_despesas_aprovadas, 
    df_despesas_pagas,
)


# Projeção Agrupada
with st.container(border=True):
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.subheader("Projeção de bares agrupados")
    with col2:
        data_fim2 = seletor_data_fim_padrao(key='date_input2') # Data de fim padrão dos seletores: uma semana à frente do dia atual
    with col3:
        multiplicador2 = st.number_input("Selecione um multiplicador", value=1.0, key="multiplicador_input2")
    
    st.markdown(
        """*Bar Brahma - Centro, Bar Brahma - Granja, Bar Brahma Paulista, Brahma Ribeirão, Bar Léo - Centro, Bar Brasília - Aeroporto, 
            Delivery Bar Léo Centro, Delivery Fábrica de Bares, Delivery Orfeu, Edifício Rolim, Escritório Fábrica de Bares, 
            Girondino, Girondino - CCBB, Hotel Marabá, Jacaré, Orfeu, Priceless, Riviera, Tempus*
    """
    )

    df_projecao_bares = df_projecao_bares_geral

    # Aplica data e multiplicador selecionados
    df_projecao_bares = filtra_soma_saldo_final(df_projecao_bares, data_fim2, multiplicador2)
    
    # Aplica as casas agrupadas
    df_projecao_grouped = config_grouped_projecao(df_projecao_bares, lojasAgrupadas)
    df_projecao_grouped_com_soma = somar_total(df_projecao_grouped)

    df_projecao_grouped_com_soma = df_projecao_grouped_com_soma[[
        "Data",
        "Saldo_Inicio_Dia",
        "Valor_Liquido_Recebido",
        "Valor_Projetado_Zig",
        "Receita_Projetada_Extraord",
        "Receita_Projetada_Eventos",
        "Despesas_Aprovadas_Pendentes",
        "Despesas_Pagas",
        "Saldo_Final"
    ]]

    df_projecao_grouped_com_soma = format_columns_brazilian(
        df_projecao_grouped_com_soma,
        [
            "Saldo_Inicio_Dia",
            "Valor_Liquido_Recebido",
            "Valor_Projetado_Zig",
            "Receita_Projetada_Extraord",
            "Receita_Projetada_Eventos",
            "Despesas_Aprovadas_Pendentes",
            "Despesas_Pagas",
            "Saldo_Final",
        ],
    )

    df_projecao_grouped_com_soma = df_projecao_grouped_com_soma.rename(columns={
        "Saldo_Inicio_Dia": "Saldo Início Dia",
        "Valor_Liquido_Recebido": "Valor Líquido Recebido",
        "Valor_Projetado_Zig": "Valor Zig Projetado",
        "Receita_Projetada_Extraord": "Receitas Extr Projetadas",
        "Receita_Projetada_Eventos": "Receitas Eventos Projetadas",
        "Despesas_Aprovadas_Pendentes": "Despesas Aprovadas Pendentes",
        "Despesas_Pagas": "Despesas Pagas",
        "Saldo_Final": "Saldo Final"
    })

    st.dataframe(df_projecao_grouped_com_soma, use_container_width=True, hide_index=True)
    button_download(df_projecao_grouped_com_soma, f"Projeção de bares agrupados", f"Projeção de bares agrupados")

st.divider()

# Projeção casa a casa (selecionadas)
with st.container(border=True):
    st.subheader("Projeção casa a casa")
    col1, col2, col3 = st.columns([3, 1, 1])

    # Adiciona seletores
    with col1:
        bares_selecionados = st.multiselect("Selecione casas", lojasComDados, default=lojasComDados[0])
    with col2:
        # Data de fim padrão dos seletores: uma semana à frente do dia atual
        data_fim = seletor_data_fim_padrao(key='date_input')
    with col3:
        multiplicador = st.number_input(
            "Selecione um multiplicador", value=1.0, key="multiplicador_input"
        )

    df_projecao_bares = df_projecao_bares_geral

    # Aplica data e multiplicador selecionados
    df_projecao_bares = filtra_soma_saldo_final(df_projecao_bares, data_fim, multiplicador)
    
    # Filtra para as casas selecionadas
    if 'Todas as casas' in bares_selecionados:
        df_projecao_bar = filtrar_por_classe_selecionada(df_projecao_bares, "Empresa", lojasComDados)
    else: 
        df_projecao_bar = filtrar_por_classe_selecionada(df_projecao_bares, "Empresa", bares_selecionados)

    # Formata exibição
    df_projecao_bar = df_format_date_brazilian(df_projecao_bar, "Data")
    df_projecao_bar = df_projecao_bar.sort_values(by=["Empresa", "Data"])
    df_projecao_bar_com_soma = somar_total(df_projecao_bar)
    
    # Organiza colunas
    df_projecao_bar_com_soma = df_projecao_bar_com_soma[[
        "Empresa",
        "Data",
        "Saldo_Inicio_Dia",
        "Valor_Liquido_Recebido",
        "Valor_Projetado_Zig",
        "Receita_Projetada_Extraord",
        "Receita_Projetada_Eventos",
        "Despesas_Aprovadas_Pendentes",
        "Despesas_Pagas",
        "Saldo_Final",
    ]]
    
    df_projecao_bar_com_soma = format_columns_brazilian(
        df_projecao_bar_com_soma,
        [
            "Saldo_Inicio_Dia",
            "Valor_Liquido_Recebido",
            "Valor_Projetado_Zig",
            "Receita_Projetada_Extraord",
            "Receita_Projetada_Eventos",
            "Despesas_Aprovadas_Pendentes",
            "Despesas_Pagas",
            "Saldo_Final"
        ],
    )

    df_projecao_bar_com_soma = df_projecao_bar_com_soma.rename(columns={
        "Empresa": "Casa",
        "Saldo_Inicio_Dia": "Saldo Início Dia",
        "Valor_Liquido_Recebido": "Valor Líquido Recebido",
        "Valor_Projetado_Zig": "Valor Zig Projetado",
        "Receita_Projetada_Extraord": "Receitas Extr Projetadas",
        "Receita_Projetada_Eventos": "Receitas Eventos Projetadas",
        "Despesas_Aprovadas_Pendentes": "Despesas Aprovadas Pendentes",
        "Despesas_Pagas": "Despesas Pagas",
        "Saldo_Final": "Saldo Final"
    })

    st.dataframe(df_projecao_bar_com_soma, use_container_width=True, hide_index=True)
    button_download(df_projecao_bar_com_soma, f"Projeção casa a casa", f"Projeção casa a casa")

st.divider()

with st.container(border=True):
    st.subheader("Despesas do dia")
    col1, col2, col3, col4 = st.columns([5, 3, 4, 4], vertical_alignment='center')

    # Adiciona seletores
    with col1:
        lojasSelecionadas = st.multiselect(label="Selecione casas", options=lojasComDados, key="lojas_multiselect", default=lojasComDados[0])
    with col2:
        checkbox = st.checkbox(label="Adicionar lojas agrupadas", key="checkbox_lojas_despesas")
        if checkbox: # Lojas agrupadas
            lojasAgrupadas = lojasAgrupadas
            lojasSelecionadas.extend(lojasAgrupadas)
        
        checkbox2 = st.checkbox(label="Apenas Pendentes", key="checkbox_despesas_pendentes") # Apenas despesas pendentes
        checkbox3 = st.checkbox(label="Apenas Pagas", key="checkbox_despesas_pagas") # Apenas despesas pagas
    
    with col3:
        dataSelecionada = st.date_input(
            "Data de Início (da previsão de pagamento)",
            value=datetime.today(),
            key="data_inicio_input",
            format="DD/MM/YYYY",
        )
    with col4:
        dataSelecionada2 = st.date_input(
            "Data de Fim (da previsão de pagamento)",
            value=datetime.today(),
            key="data_fim_input3",
            format="DD/MM/YYYY",
        )

    data_inicio = pd.to_datetime(dataSelecionada)
    data_fim = pd.to_datetime(dataSelecionada2)

    despesas_pendentes_pagas = GET_DESPESAS_PENDENTES(dataInicio=data_inicio, dataFim=data_fim)
    
    # Filtra para as casas selecionadas
    if 'Todas as casas' in lojasSelecionadas:  
        despesas_pendentes_pagas = filtrar_por_classe_selecionada(despesas_pendentes_pagas, 'Loja', lojasComDados)
    else:
        despesas_pendentes_pagas = filtrar_por_classe_selecionada(despesas_pendentes_pagas, 'Loja', lojasSelecionadas)

    if checkbox2:
        despesas_pendentes_pagas = filtrar_por_classe_selecionada(despesas_pendentes_pagas, "Status_Pgto", ["Pendente"])
    if checkbox3:
        despesas_pendentes_pagas = filtrar_por_classe_selecionada(despesas_pendentes_pagas, "Status_Pgto", ["Pago"])

    # Formata exibição
    valorTotal = despesas_pendentes_pagas["Valor"].sum()
    valorTotal = format_brazilian(valorTotal)
    df = format_columns_brazilian(despesas_pendentes_pagas, ["Valor"])
    df = df_format_date_brazilian(df, 'Previsao_Pgto')
    df = df_format_date_brazilian(df, 'Data_Vencimento')
    df = df.sort_values(by=["Loja"])

    # Organiza colunas
    df = df[['Loja', 'Previsao_Pgto', 'Data_Vencimento', 'Parcelamento', 'ID_Despesa', 'ID_Parcela', 'Valor', 'Status_Pgto', 'Fornecedor']]
    df = df.rename(columns={
        "Loja": "Casa",
        "Previsao_Pgto": "Previsão Pgto",
        "Data_Vencimento": "Data Vencimento",
        "ID_Despesa": "ID Despesa",
        "ID_Parcela": "ID Parcela",        
        "Status_Pgto": "Status Pgto",
    })

    st.dataframe(df, use_container_width=True, hide_index=True)
    col1, col2 = st.columns([5, 2], vertical_alignment='center')
    with col1:
        st.write(f"Valor total das despesas selecionadas = **R$ {valorTotal}**")
    with col2:
        button_download(df, f"Despesas do dia", f"Despesas do dia")


with st.container(border=True):
    st.subheader("Receitas Extraordinárias do Dia")
    col1, col2, col3 = st.columns([5, 2, 3], vertical_alignment='center')

    # Adiciona seletores
    with col1:
        lojasSelecionadas2 = st.multiselect(label="Selecione casas", options=lojasComDados, key="lojas_multiselect2", default=lojasComDados[0])

    with col2:
        checkboxLojas = st.checkbox(label="Adicionar lojas agrupadas", key="checkbox_lojas_extraord")
        if checkboxLojas: # Lojas agrupadas
            lojasAgrupadas = lojasAgrupadas
            lojasSelecionadas2.extend(lojasAgrupadas)
    
    with col3:
        dataSelecionada2 = st.date_input(
            "Selecione uma Data",
            value=datetime.today(),
            key="data_inicio_input2",
            format="DD/MM/YYYY",
        )

    df = GET_RECEITAS_EXTRAORD_DO_DIA()

    # Filtra para as casas e data selecionadas
    if 'Todas as casas' in lojasSelecionadas2:
        df = filtrar_por_classe_selecionada(df, "Empresa", lojasComDados)
    else:
        df = filtrar_por_classe_selecionada(df, "Empresa", lojasSelecionadas2)
    
    dataSelecionada2 = pd.to_datetime(dataSelecionada2)
    df = filtrar_por_datas(df, dataSelecionada2, dataSelecionada2, "Data_Vencimento_Parcela")

    # Formata para exibição
    valorTotal = df["Valor_Parcela"].sum()
    valorTotal = format_brazilian(valorTotal)
    df = format_columns_brazilian(df, ["Valor_Parcela"])
    df = df_format_date_columns_brazilian(df, ['Data_Vencimento_Parcela'])
    df = df.sort_values(by=["Empresa"])
    
    # Organiza colunas
    df = df[['Empresa', 'ID_Receita_Extraordinária', 'Data_Vencimento_Parcela', 'Valor_Parcela', 'Classificação', 'Nome_Cliente', 'Observações']]
    df = df.rename(columns={
        "Empresa": "Casa",
        "ID_Receita_Extraodinária": "ID Receita Extraodinária",
        "Data_Vencimento_Parcela": "Data Vencimento Parcela",
        "Valor_Parcela": "Valor Parcela",        
    })

    st.dataframe(df, use_container_width=True, hide_index=True)
    col1, col2 = st.columns([5, 2], vertical_alignment='center')
    with col1:
        st.write(f"Valor total das receitas extraordinárias selecionadas = **R$ {valorTotal}**")
    with col2:
        button_download(df, f"Receitas Extraord do dia", f"Receitas Extraord do dia")
    
    

with st.container(border=True):
    st.subheader("Receitas de Eventos do Dia")
    col1, col2, col3 = st.columns([5, 2, 3], vertical_alignment='center')

    # Adiciona seletores
    with col1:
        lojasSelecionadas2 = st.multiselect(label="Selecione Lojas", options=lojasComDados, key="lojas_multiselect3", default=lojasComDados[0])

    with col2: # Lojas agrupadas
        checkboxLojas = st.checkbox(label="Adicionar lojas agrupadas", key="checkbox_lojas_eventos")
        if checkboxLojas:
            lojasAgrupadas = lojasAgrupadas
            lojasSelecionadas2.extend(lojasAgrupadas)
    
    with col3:
        dataSelecionada2 = st.date_input(
            "Selecione uma Data",
            value=datetime.today(),
            key="data_inicio_input3",
            format="DD/MM/YYYY",
        )

    df = GET_RECEITAS_EVENTOS_DO_DIA()

    # Filtra por casas e data selecionadas
    if 'Todas as casas' in lojasSelecionadas2:
        df = filtrar_por_classe_selecionada(df, "Empresa", lojasComDados)
    else:
        df = filtrar_por_classe_selecionada(df, "Empresa", lojasSelecionadas2)
    
    dataSelecionada2 = pd.to_datetime(dataSelecionada2)
    df = filtrar_por_datas(df, dataSelecionada2, dataSelecionada2, "Data_Vencimento_Parcela")
    
    # Formata para exibição
    valorTotal = df["Valor_Parcela"].sum()
    valorTotal = format_brazilian(valorTotal)
    df = format_columns_brazilian(df, ["Valor_Parcela"])
    df = df_format_date_columns_brazilian(df, ['Data_Vencimento_Parcela'])
    df = df.sort_values(by=["Empresa"])
   
    # Organiza colunas
    df = df[['Empresa', 'ID_Evento', 'Data_Vencimento_Parcela', 'Valor_Parcela', 'Classificação', 'Nome_Cliente', 'Observações']]
    df = df.rename(columns={
        "Empresa": "Casa",
        "ID_Evento": "ID Evento",
        "Data_Vencimento_Parcela": "Data Vencimento Parcela",
        "Valor_Parcela": "Valor Parcela",        
    })

    st.dataframe(df, use_container_width=True, hide_index=True)
    col1, col2 = st.columns([5, 2], vertical_alignment='center')
    with col1:
        st.write(f"Valor total das receitas de eventos selecionadas = **R$ {valorTotal}**")
    with col2:
        button_download(df, f"Receitas Eventos do dia", f"Receitas Eventos do dia")
