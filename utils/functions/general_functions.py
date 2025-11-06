import streamlit as st
import pandas as pd
import numpy as np
from workalendar.america import Brazil
import openpyxl
import os
from utils.functions.date_functions import *
from utils.user import *
import mysql.connector
from streamlit.logger import get_logger


LOGGER = get_logger(__name__)

def mysql_connection_fb():
	mysql_config = st.secrets["mysql_fb"]

	conn_fb = mysql.connector.connect(
			host=mysql_config['host'],
			port=mysql_config['port'],
			database=mysql_config['database'],
			user=mysql_config['username'],
			password=mysql_config['password']
		)    
	return conn_fb


def execute_query(query):
    try:
        conn = mysql_connection_fb()
        cursor = conn.cursor()
        cursor.execute(query)

        # Obter nomes das colunas
        column_names = [col[0] for col in cursor.description]
  
        # Obter resultados
        result = cursor.fetchall()
  
        cursor.close()
        conn.close()  # Fechar a conexão
        return result, column_names
    except mysql.connector.Error as err:
        LOGGER.error(f"Erro ao executar query: {err}")
        return None, None


def dataframe_query(query):
	resultado, nomeColunas = execute_query(query)
	dataframe = pd.DataFrame(resultado, columns=nomeColunas)
	return dataframe


# Permissões de usuário
@st.cache_data
def GET_PERMISSIONS(email):
	emailStr = f"'{email}'"
	return dataframe_query(f''' 
		SELECT 
			tg.POSICAO AS 'Permissao'
		FROM
			ADMIN_USERS au 
			LEFT JOIN T_GRUPO_USUARIO tgu ON au.ID = tgu.FK_USUARIO 
			LEFT JOIN T_GRUPO tg ON tgu.FK_GRUPO = tg.id
		WHERE au.LOGIN = {emailStr}
  	''')


@st.cache_data
def GET_USERNAME(email):
	emailStr = f"'{email}'"
	return dataframe_query(f'''
		SELECT 
			au.FULL_NAME AS 'Nome'
		FROM
			ADMIN_USERS au 
		WHERE au.LOGIN = {emailStr}
  ''')


def config_permissoes_user():
    email = st.session_state.get("user_email", "Usuário desconhecido")
    dfpermissao = GET_PERMISSIONS(email)
    if dfpermissao.empty: # Não está no EPM
        permissao = ["Gazit"]
        nomeUser = ""
    else: # Está no EPM
        permissao = dfpermissao["Permissao"].tolist()
        nomeUser = GET_USERNAME(email)
        nomeUser = " ".join(nomeUser["Nome"].tolist())
    return permissao, nomeUser, email


def GET_LOJAS():
  return dataframe_query(f'''
    SELECT
    te.ID as 'ID_Loja',
    te.NOME_FANTASIA as 'Loja'
    FROM T_EMPRESAS te
''')


@st.cache_data
def GET_LOJAS_USER(email):
	emailStr = f"'{email}'"
	return dataframe_query(f'''
		SELECT 
			te.NOME_FANTASIA AS 'Loja'
		FROM
			ADMIN_USERS au 
			LEFT JOIN T_USUARIOS_EMPRESAS tue ON au.ID = tue.FK_USUARIO 
			LEFT JOIN T_EMPRESAS te ON tue.FK_EMPRESA = te.ID
			LEFT JOIN T_LOJAS tl ON te.ID = tl.ID
		WHERE au.LOGIN = {emailStr}
  	''')


def mostrar_menu_permissoes_eventos(permissoes):
    if "Dev Dash FB" in permissoes:
        st.sidebar.markdown("## Eventos")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos.py", label=":calendar: Calendário de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Conversao_Eventos_Priceless.py", label="📈 KPI's de Vendas - Conversão de Eventos")
        st.sidebar.page_link("pages/Eventos - Acompanhamento_de_Comissão.py", label="📊 KPI's de Vendas - Cálculo da Comissão de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Historico_Clientes_Eventos.py", label=":busts_in_silhouette: KPI's de Vendas - Histórico e Recorrência de Clientes")
        st.sidebar.page_link("pages/Eventos - Faturamento_Bruto_de_Eventos.py", label=":moneybag: Faturamento Bruto de Eventos")
        st.sidebar.page_link("pages/Eventos - Conciliação_de_Parcelas_Eventos.py", label=":left_right_arrow: Conciliação de Parcelas de Eventos")
        st.sidebar.page_link("pages/Eventos - Auditoria_de_Eventos_Preenchimento_Lancamentos.py", label=":receipt: Auditoria de Eventos - Preenchimento dos Lançamentos")
        st.sidebar.page_link("pages/Eventos - Informações_de_Eventos.py", label="🔎 Informações de Eventos")
        # st.sidebar.page_link("pages/10_Regras_de_Eventos.py", label=":clipboard: Regras de Eventos")
        st.sidebar.page_link("pages/Eventos - Eventos_Auditoria_de_Eventos_Confirmados.py", label=":no_entry_sign: Auditoria de Eventos - Confirmados")
        st.sidebar.page_link("pages/Eventos - Gazit.py", label=":shopping_bags: Gazit")
        st.sidebar.page_link("pages/Eventos - Calendário_Gazit.py", label=":calendar: Calendário de Eventos - Gazit")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos_Confirmados.py", label=":calendar: Calendário de Eventos Confirmados")
    elif "Acesso Liderança Eventos" in permissoes:
        st.sidebar.markdown("## Eventos")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos.py", label=":calendar: Calendário de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Conversao_Eventos_Priceless.py", label="📈 KPI's de Vendas - Conversão de Eventos")
        st.sidebar.page_link("pages/Eventos - Acompanhamento_de_Comissão.py", label="📊 KPI's de Vendas - Cálculo da Comissão de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Historico_Clientes_Eventos.py", label=":busts_in_silhouette: KPI's de Vendas - Histórico e Recorrência de Clientes")
        st.sidebar.page_link("pages/Eventos - Faturamento_Bruto_de_Eventos.py", label=":moneybag: Faturamento Bruto de Eventos")
        st.sidebar.page_link("pages/Eventos - Conciliação_de_Parcelas_Eventos.py", label=":left_right_arrow: Conciliação de Parcelas de Eventos")
        st.sidebar.page_link("pages/Eventos - Auditoria_de_Eventos_Preenchimento_Lancamentos.py", label=":receipt: Auditoria de Eventos - Preenchimento dos Lançamentos")
        st.sidebar.page_link("pages/Eventos - Informações_de_Eventos.py", label="🔎 Informações de Eventos")
        # st.sidebar.page_link("pages/10_Regras_de_Eventos.py", label=":clipboard: Regras de Eventos")
        st.sidebar.page_link("pages/Eventos - Gazit.py", label=":shopping_bags: Gazit")
        st.sidebar.page_link("pages/Eventos - Calendário_Gazit.py", label=":calendar: Calendário de Eventos - Gazit")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos_Confirmados.py", label=":calendar: Calendário de Eventos Confirmados")
    elif "Acesso Admin Eventos" in permissoes:
        st.sidebar.markdown("## Eventos")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos.py", label=":calendar: Calendário de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Conversao_Eventos_Priceless.py", label="📈 KPI's de Vendas - Conversão de Eventos")
        st.sidebar.page_link("pages/Eventos - Acompanhamento_de_Comissão.py", label="📊 KPI's de Vendas - Cálculo da Comissão de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Historico_Clientes_Eventos.py", label=":busts_in_silhouette: KPI's de Vendas - Histórico e Recorrência de Clientes")
        st.sidebar.page_link("pages/Eventos - Faturamento_Bruto_de_Eventos.py", label=":moneybag: Faturamento Bruto de Eventos")
        st.sidebar.page_link("pages/Eventos - Conciliação_de_Parcelas_Eventos.py", label=":left_right_arrow: Conciliação de Parcelas de Eventos")
        st.sidebar.page_link("pages/Eventos - Auditoria_de_Eventos_Preenchimento_Lancamentos.py", label=":receipt: Auditoria de Eventos - Preenchimento dos Lançamentos")
        st.sidebar.page_link("pages/Eventos - Informações_de_Eventos.py", label="🔎 Informações de Eventos")
        # st.sidebar.page_link("pages/10_Regras_de_Eventos.py", label=":clipboard: Regras de Eventos")
        st.sidebar.page_link("pages/Eventos - Gazit.py", label=":shopping_bags: Gazit")
        st.sidebar.page_link("pages/Eventos - Calendário_Gazit.py", label=":calendar: Calendário de Eventos - Gazit")
    elif "Acesso Eventos 1" in permissoes:
        st.sidebar.markdown("## Eventos")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos.py", label=":calendar: Calendário de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Conversao_Eventos_Priceless.py", label="📈 KPI's de Vendas - Conversão de Eventos")
        st.sidebar.page_link("pages/Eventos - Acompanhamento_de_Comissão.py", label="📊 KPI's de Vendas - Cálculo da Comissão de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Historico_Clientes_Eventos.py", label=":busts_in_silhouette: KPI's de Vendas - Histórico e Recorrência de Clientes")
        st.sidebar.page_link("pages/Eventos - Faturamento_Bruto_de_Eventos.py", label=":moneybag: Faturamento Bruto de Eventos")
        st.sidebar.page_link("pages/Eventos - Conciliação_de_Parcelas_Eventos.py", label=":left_right_arrow: Conciliação de Parcelas de Eventos")
        st.sidebar.page_link("pages/Eventos - Auditoria_de_Eventos_Preenchimento_Lancamentos.py", label=":receipt: Auditoria de Eventos - Preenchimento dos Lançamentos")
        st.sidebar.page_link("pages/Eventos - Informações_de_Eventos.py", label="🔎 Informações de Eventos")
    elif "Acesso Eventos 2" in permissoes:
        st.sidebar.markdown("## Eventos")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos.py", label=":calendar: Calendário de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Conversao_Eventos_Priceless.py", label="📈 KPI's de Vendas - Conversão de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Historico_Clientes_Eventos.py", label=":busts_in_silhouette: KPI's de Vendas - Histórico e Recorrência de Clientes")
        st.sidebar.page_link("pages/Eventos - Faturamento_Bruto_de_Eventos.py", label=":moneybag: Faturamento Bruto de Eventos")
        st.sidebar.page_link("pages/Eventos - Conciliação_de_Parcelas_Eventos.py", label=":left_right_arrow: Conciliação de Parcelas de Eventos")
        st.sidebar.page_link("pages/Eventos - Auditoria_de_Eventos_Preenchimento_Lancamentos.py", label=":receipt: Auditoria de Eventos - Preenchimento dos Lançamentos")
        st.sidebar.page_link("pages/Eventos - Informações_de_Eventos.py", label="🔎 Informações de Eventos")
        st.sidebar.page_link("pages/Eventos - Gazit.py", label=":shopping_bags: Gazit")
        st.sidebar.page_link("pages/Eventos - Calendário_Gazit.py", label=":calendar: Calendário de Eventos - Gazit")
    elif "Acesso Eventos 3" in permissoes:
        st.sidebar.markdown("## Eventos")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos.py", label=":calendar: Calendário de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Conversao_Eventos_Priceless.py", label="📈 KPI's de Vendas - Conversão de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Historico_Clientes_Eventos.py", label=":busts_in_silhouette: KPI's de Vendas - Histórico e Recorrência de Clientes")
        st.sidebar.page_link("pages/Eventos - Faturamento_Bruto_de_Eventos.py", label=":moneybag: Faturamento Bruto de Eventos")
        st.sidebar.page_link("pages/Eventos - Conciliação_de_Parcelas_Eventos.py", label=":left_right_arrow: Conciliação de Parcelas de Eventos")
        st.sidebar.page_link("pages/Eventos - Auditoria_de_Eventos_Preenchimento_Lancamentos.py", label=":receipt: Auditoria de Eventos - Preenchimento dos Lançamentos")
        st.sidebar.page_link("pages/Eventos - Informações_de_Eventos.py", label="🔎 Informações de Eventos")
    elif "Acesso Eventos 4" in permissoes:
        st.sidebar.markdown("## Eventos")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos.py", label=":calendar: Calendário de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Conversao_Eventos_Priceless.py", label="📈 KPI's de Vendas - Conversão de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Historico_Clientes_Eventos.py", label=":busts_in_silhouette: KPI's de Vendas - Histórico e Recorrência de Clientes")
        st.sidebar.page_link("pages/Eventos - Faturamento_Bruto_de_Eventos.py", label=":moneybag: Faturamento Bruto de Eventos")
        st.sidebar.page_link("pages/Eventos - Informações_de_Eventos.py", label="🔎 Informações de Eventos")
        st.sidebar.page_link("pages/Produto - Análise de Consumo.py", label=":material/solo_dining: Análise de Consumo")
    elif "Acesso Eventos 5" in permissoes:
        st.sidebar.markdown("## Eventos")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos.py", label=":calendar: Calendário de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Historico_Clientes_Eventos.py", label=":busts_in_silhouette: KPI's de Vendas - Histórico e Recorrência de Clientes")
        st.sidebar.page_link("pages/Eventos - Faturamento_Bruto_de_Eventos.py", label=":moneybag: Faturamento Bruto de Eventos")
        st.sidebar.page_link("pages/Eventos - Informações_de_Eventos.py", label="🔎 Informações de Eventos")
    elif "Gazit" in permissoes:
        st.sidebar.markdown("## Eventos")
        st.sidebar.page_link("pages/Eventos - Calendário_de_Eventos.py", label=":calendar: Calendário de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Conversao_Eventos_Priceless.py", label="📈 KPI's de Vendas - Conversão de Eventos")
        st.sidebar.page_link("pages/Eventos - KPIs_Historico_Clientes_Eventos.py", label=":busts_in_silhouette: KPI's de Vendas - Histórico e Recorrência de Clientes")
        st.sidebar.page_link("pages/Eventos - Faturamento_Bruto_de_Eventos.py", label=":moneybag: Faturamento Bruto de Eventos")
        st.sidebar.page_link("pages/Eventos - Conciliação_de_Parcelas_Eventos.py", label=":left_right_arrow: Conciliação de Parcelas de Eventos")
        st.sidebar.page_link("pages/Eventos - Informações_de_Eventos.py", label="🔎 Informações de Eventos")
        st.sidebar.page_link("pages/Eventos - Gazit.py", label=":shopping_bags: Gazit")
        st.sidebar.page_link("pages/Eventos - Calendário_Gazit.py", label=":calendar: Calendário de Eventos - Gazit")
    else:
        pass


def mostrar_menu_permissoes_cmv(permissoes):
    if "Dev Dash FB" in permissoes:
        st.sidebar.markdown("## CMV")
        st.sidebar.page_link('pages/CMV - Painel_CMV.py', label=":bar_chart: Painel de CMV")
        st.sidebar.page_link("pages/CMV - CMV_Real.py", label="⚖ CMV Real")
        st.sidebar.page_link("pages/CMV - CMV_Teórico_-_Análise_de_Fichas_Técnicas.py", label=":material/rubric: CMV Teórico - Análise de Fichas Técnicas")
    if "Acesso CMV 1" in permissoes:
        st.sidebar.markdown("## CMV")
        st.sidebar.page_link("pages/CMV - CMV_Teórico_-_Análise_de_Fichas_Técnicas.py", label=":material/rubric: CMV Teórico - Análise de Fichas Técnicas")        


def mostrar_menu_permissoes_compras(permissoes):
    if "Dev Dash FB" in permissoes:
        st.sidebar.markdown("## Compras")
        st.sidebar.page_link("pages/Compras - Análises.py", label=":material/shelves: Análises")
        st.sidebar.page_link("pages/Compras - Processos.py", label=":material/cycle: Processos")
        st.sidebar.page_link("pages/Compras - Curva_ABC.py", label=":material/abc: Curva ABC")
    if "Acesso Compras 1" in permissoes:
        st.sidebar.markdown("## Compras")
        st.sidebar.page_link("pages/Compras - Análises.py", label=":material/shelves: Análises")
        st.sidebar.page_link("pages/Compras - Processos.py", label=":material/cycle: Processos")
        st.sidebar.page_link("pages/Compras - Curva_ABC.py", label=":material/abc: Curva ABC")


def mostrar_menu_permissoes_produto(permissoes):
    if "Dev Dash FB" in permissoes:
        st.sidebar.markdown("## Produtos")
        st.sidebar.page_link("pages/Produto - Análise de Consumo.py", label=":material/restaurant: Análise de Consumo")
        st.sidebar.page_link("pages/Produto - Relatório de Vendas.py", label="🛍️ Relatório de Vendas")
    if "Acesso Produtos 1" in permissoes:
        st.sidebar.markdown("## Produtos")
        st.sidebar.page_link("pages/Produto - Análise de Consumo.py", label=":material/restaurant: Análise de Consumo")


def mostrar_menu_permissoes_conciliacao(permissoes):
    if "Acesso Conciliação" in permissoes:
        st.sidebar.markdown("## Conciliação Financeira")
        st.sidebar.page_link("pages/Conciliação - Conciliações.py", label=":material/money_bag: Conciliação por casa")
        st.sidebar.page_link("pages/Conciliação - Farol_de_Conciliação.py", label=":material/finance: Farol de Conciliação")
        st.sidebar.page_link("pages/Conciliação - Ajustes.py", label=":material/instant_mix: Ajustes")
    elif "Acesso Conciliação Casa" in permissoes:
        st.sidebar.markdown("## Conciliação Financeira")
        st.sidebar.page_link("pages/Conciliação - Conciliações.py", label=":material/money_bag: Conciliação por casa")
    
def mostrar_menu_permissoes_financeiro(permissoes):
    if 'Dev Dash FB' in permissoes:
        st.sidebar.markdown("## Financeiro")
        st.sidebar.page_link("pages/Financeiro - Faturamento_Zigpay.py", label=":moneybag: Faturamento Zigpay")
        st.sidebar.page_link("pages/Financeiro - Faturamento_Extraordinário.py", label=":dollar: Faturamento Extraordinário")
        st.sidebar.page_link("pages/Financeiro - Despesas.py", label=":money_with_wings: Despesas")
        st.sidebar.page_link("pages/Financeiro - Forecast.py", label=":material/event_upcoming: Forecast")
    if 'Acesso Financeiro 2' in permissoes:
        st.sidebar.markdown("## Financeiro")
        st.sidebar.page_link("pages/Financeiro - Despesas.py", label=":money_with_wings: Despesas")


def mostrar_menu_permissoes_fluxo_de_caixa(permissoes):
    if 'Dev Dash FB' in permissoes:
        st.sidebar.markdown("## Fluxo de Caixa")
        st.sidebar.page_link("pages/Fluxo_de_Caixa - Projeção.py", label="📈 Projeção")
        st.sidebar.page_link("pages/Fluxo_de_Caixa - Previsão_de_Faturamento.py", label="🪙 Previsão de Faturamento")
        st.sidebar.page_link("pages/Conciliação - Fluxo_Realizado.py", label=":material/currency_exchange: Fluxo Realizado")
        st.sidebar.page_link("pages/Conciliação - Fluxo_Futuro.py", label=":material/event_upcoming: Fluxo Futuro")
    elif 'Acesso Conciliação' in permissoes:
        st.sidebar.markdown("## Fluxo de Caixa")
        st.sidebar.page_link("pages/Conciliação - Fluxo_Realizado.py", label=":material/currency_exchange: Fluxo Realizado")
        st.sidebar.page_link("pages/Conciliação - Fluxo_Futuro.py", label=":material/event_upcoming: Fluxo Futuro")


def mostrar_menu_permissoes_auditoria(permissoes):
    if 'Dev Dash FB' in permissoes:
        st.sidebar.markdown("## Auditoria")
        st.sidebar.page_link("pages/Auditoria - Descontos.py", label=":material/list: Categorização - Descontos")
        

def config_sidebar():

    permissoes, user_name, email = config_permissoes_user()
    st.sidebar.header(f"Bem-vindo(a) {user_name}!")
    if st.session_state["loggedIn"]:
        mostrar_menu_permissoes_financeiro(permissoes)
        mostrar_menu_permissoes_fluxo_de_caixa(permissoes)
        mostrar_menu_permissoes_eventos(permissoes)
        mostrar_menu_permissoes_cmv(permissoes)
        mostrar_menu_permissoes_compras(permissoes)
        mostrar_menu_permissoes_produto(permissoes)
        mostrar_menu_permissoes_conciliacao(permissoes)
        mostrar_menu_permissoes_auditoria(permissoes)
    else:
        st.sidebar.write("Por favor, faça login para acessar o menu.")


def filtrar_por_classe_selecionada(dataframe, classe, valores_selecionados):
    if valores_selecionados:
        dataframe = dataframe[dataframe[classe].isin(valores_selecionados)]
    return dataframe


def safe_sheet_name(name):
    # Remove caracteres inválidos e limita a 31 chars
    invalid_chars = ['\\', '/', '*', '[', ']', ':', '?']
    for char in invalid_chars:
        name = name.replace(char, '')
    return name[:31]


def export_to_excel(df, sheet_name, excel_filename):
    if os.path.exists(excel_filename):
        wb = openpyxl.load_workbook(excel_filename)
    else:
        wb = openpyxl.Workbook()

    if sheet_name in wb.sheetnames:
        wb.remove(wb[sheet_name])
    ws = wb.create_sheet(title=sheet_name)

    # Escrever os cabeçalhos
    for col_idx, column_title in enumerate(df.columns, start=1):
        ws.cell(row=1, column=col_idx, value=column_title)

    # Escrever os dados
    for row_idx, row in enumerate(df.itertuples(index=False, name=None), start=2):
        for col_idx, value in enumerate(row, start=1):
            ws.cell(row=row_idx, column=col_idx, value=value)

    wb.save(excel_filename)


def format_brazilian(num):
    try:
        num = float(num)
        return f"{num:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return num
    

def format_brazilian_without_decimal(num):
    try:
        num = float(num)
        return f"{num:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return num


def format_columns_brazilian(df, numeric_columns):
    if df is not None and not df.empty:
        df = df.copy()
        for col in numeric_columns:
            if col in df.columns:
                df[col] = df[col].apply(format_brazilian)
        return df
    else:
        return df


def format_percentage(num):
    try:
        num = float(num)
        formatted_num = f"{num * 100:,.2f}"  # Multiplica por 100 e formata
        return f"{formatted_num.replace(',', 'X').replace('.', ',').replace('X', '.')}%"  # Formata como percentual
    except (ValueError, TypeError):
        return num  # Retorna o valor original em caso de erro


def format_columns_percentage(df, numeric_columns):
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].apply(format_percentage)
    return df


# Dataframe filtrado pela casa:
def df_filtrar_casa(df, id_casa):
    df_filtrado = df[df["Casa"] == id_casa]
    return df_filtrado


def df_filtrar_periodo_data(df, coluna_data, data_inicio, data_fim):

    data_inicio = pd.to_datetime(data_inicio)
    data_fim = pd.to_datetime(data_fim) + pd.DateOffset(days=1)

    df = df.copy()

    df[coluna_data] = pd.to_datetime(df[coluna_data])
    df_filtrado = df.loc[
        (df[coluna_data] >= data_inicio) & (df[coluna_data] < data_fim)
    ]

    return df_filtrado


def df_filtrar_mes(df, coluna_data, mes):

    df = df.copy()

    df[coluna_data] = pd.to_datetime(df[coluna_data])

    df_filtrado = df.loc[(df[coluna_data].dt.month == int(mes))]

    return df_filtrado


def df_filtrar_ano(df, coluna_data, ano):

    df = df.copy()

    df[coluna_data] = pd.to_datetime(df[coluna_data])

    df_filtrado = df.loc[(df[coluna_data].dt.year == int(ano))]

    return df_filtrado


def escape_dolar(texto):
    return texto.replace('$', r'\$')


def highlight_values(val):
    color = 'red' if '-' in val else 'green'
    return f'color: {color}'


def preparar_dados_lojas_user_financeiro():
    permissao, nomeuser, username = config_permissoes_user()
    if 'Administrador' in permissao:
        dflojas = GET_LOJAS()
        lojasARemover = ['Casa Teste', 'Casa Teste 2', 'Casa Teste 3']
        dflojas = dflojas[~dflojas['Loja'].isin(lojasARemover)]
    else:
        dflojas = GET_LOJAS_USER(username)

    lojasReais = [
        'Abaru - Priceless', 'Arcos', 'Bar Brahma - Centro', 'Bar Brahma Paulista', 'Bar Léo - Centro',
        'Blue Note - São Paulo', 'Blue Note SP (Novo)', 'Delivery Bar Leo Centro', 'Delivery Fabrica de Bares',
        'Delivery Jacaré', 'Delivery Orfeu', 'Edificio Rolim', 'Escritório Fabrica de Bares',
        'Girondino ', 'Girondino - CCBB', 'Hotel Maraba', 'Jacaré', 'Love Cabaret', 'Notiê - Priceless',
        'Orfeu', 'Priceless', 'Riviera Bar', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ',
        'Ultra Evil Premium Ltda ', 'Bar Brahma - Granja', 'Brahma - Ribeirão'
    ]

    lojas = dflojas[dflojas['Loja'].isin(set(lojasReais))]['Loja'].tolist()
    lojas.sort(key=str.lower)

    # Verificar se ambas as lojas estão na lista
    if 'Abaru - Priceless' in lojas and 'Notiê - Priceless' in lojas:
        # Remover a 'loja 1' da lista
        lojas.remove('Abaru - Priceless')

        # Encontrar o índice da 'loja 3' para inserir a 'loja 1' logo após
        indice_loja_alvo = lojas.index('Notiê - Priceless')

        # Inserir a 'loja 1' após a 'loja 3'
        lojas.insert(indice_loja_alvo + 1, 'Abaru - Priceless')

    return lojas


def preparar_dados_lojas_user_projecao_fluxo():
  permissao, nomeuser, username = config_permissoes_user()
  if 'Administrador' in permissao:
    dflojas = GET_LOJAS()
    lojasARemover = ['Casa Teste', 'Casa Teste 2', 'Casa Teste 3']
    dflojas = dflojas[~dflojas['Loja'].isin(lojasARemover)]
  else:
    dflojas = GET_LOJAS_USER(username)

  lojasReais = ['Abaru - Priceless', 'Arcos', 'All bar', 'Bar Brahma Aeroclube', 'Brahma Aricanduva',
                'Bar Brahma - Centro', 'Bar Brahma Paulista', 'Bar Brasilia -  Aeroporto', 'Bardassê', 'Bar Léo - Centro', 'Bar Léo - Vila Madalena', 'Blue Note - São Paulo', 'Blue Note SP (Novo)',
                'Colorado Aeroporto BSB', 'Delivery Bar Leo Centro', 'Delivery Fabrica de Bares', 'Delivery Jacaré', 'Delivery Orfeu', 'Duroc ', 'Edificio Rolim', 'Escritório Fabrica de Bares', 'FDB DIGITAL PARTICIPACOES LTDA', 'FDB HOLDING INFERIOR LTDA', 'FDB HOLDING SUPERIOR LTDA', 'Filial', 'Hbar participacoes e empreendimentos ', 'Ilha das Flores ', 'Lojinha - Brahma', 'Navarro', 'Patizal ',  'Piratininga', 'Tundra',
                'Girondino ', 'Girondino - CCBB', 'Hotel Maraba', 'Jacaré', 'Love Cabaret', 'Notiê - Priceless', 'Orfeu', 'Priceless', 'Riviera Bar', 
                'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'Ultra Evil Premium Ltda ', 'Bar Brahma - Granja', 'Brahma - Ribeirão']
  
  lojas = dflojas[dflojas['Loja'].isin(set(lojasReais))]['Loja'].tolist()
  lojas.sort(key=str.lower)

  # Verificar se ambas as lojas estão na lista
  if 'Abaru - Priceless' in lojas and 'Notiê - Priceless' in lojas:
    # Remover a 'loja 1' da lista
    lojas.remove('Abaru - Priceless')
    
    # Encontrar o índice da 'loja 3' para inserir a 'loja 1' logo após
    indice_loja_alvo = lojas.index('Notiê - Priceless')
    
    # Inserir a 'loja 1' após a 'loja 3'
    lojas.insert(indice_loja_alvo + 1, 'Abaru - Priceless')

    return lojas


def obter_valores_unicos_ordenados(df, coluna):
    dados = df[coluna].dropna().unique().tolist()
    dados.sort(key=str.lower)
    return dados


def highlight_values_inverse(val):
  if '-' in val:
    color = 'green' 
  elif val == '0,00' or val == 'nan':
    color = 'black'
  else:
    color = 'red'
  return f'color: {color}'



