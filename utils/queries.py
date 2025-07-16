import streamlit as st
from streamlit.logger import get_logger
import pandas as pd
import mysql.connector

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


### Permissões de usuário ###

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


@st.cache_data
def get_casas_validas():
    result, column_names = execute_query("""
		SELECT te.ID AS ID_Casa,
		te.NOME_FANTASIA AS Casa,
		te.ID_ZIGPAY AS ID_Zigpay
		FROM T_EMPRESAS te
		"""
	)
    df_casas = pd.DataFrame(result, columns=column_names)
    lista_casas_validas = ['Priceless', 'Arcos', 'Bar Brahma - Centro', 'Bar Brahma - Granja', 'Bar Léo - Centro', 'Bar Léo - Vila Madalena', 'Blue Note - São Paulo', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Girondino ', 'Girondino - CCBB', 'Jacaré', 'Love Cabaret', 'Orfeu', 'Riviera Bar', 'Ultra Evil Premium Ltda ']
    df_validas = pd.DataFrame(lista_casas_validas, columns=["Casa"])
    df = df_casas.merge(df_validas, on="Casa", how="inner")
    return df


# Dados de Eventos

@st.cache_data
def GET_EVENTOS_PRICELESS():
   	return dataframe_query(f'''
		SELECT 
			tep.ID as 'ID_Evento',
			te.NOME_FANTASIA as 'Casa',
			te.ID as 'ID Casa',
			tee.NOME_COMPLETO as 'Comercial_Responsavel',
			tep.NOME_EVENTO as 'Nome_do_Evento',
			trec.NOME as 'Cliente',
			tep.DATA_CONTRATACAO as 'Data_Contratacao',
			tep.DATA_EVENTO as 'Data_Evento',
			tte.DESCRICAO as 'Tipo Evento',
			tme.DESCRICAO as 'Modelo Evento',
			tep.VALOR_TOTAL_EVENTO as 'Valor_Total',
			tep.NUM_CLIENTES as 'Num_Pessoas',
			tep.VALOR_AB as 'Valor_AB',
			COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) as 'Valor_Locacao_Total',
			tep.VALOR_LOCACAO_AROO_1 as 'Valor_Locacao_Aroo_1',
			tep.VALOR_LOCACAO_AROO_2 as 'Valor_Locacao_Aroo_2',
			tep.VALOR_LOCACAO_AROO_3 as 'Valor_Locacao_Aroo_3',
			tep.VALOR_LOCACAO_ANEXO as 'Valor_Locacao_Anexo',
			tep.VALOR_LOCACAO_NOTIE as 'Valor_Locacao_Notie',
			tep.VALOR_LOCACAO_MIRANTE as 'Valor_Locacao_Mirante',
			tep.VALOR_IMPOSTO as 'Valor_Imposto',
			tsep.DESCRICAO as 'Status_Evento',
			temd.DESCRICAO as 'Motivo_Declinio',
			tep.OBSERVACOES as 'Observacoes'
		FROM T_EVENTOS_PRICELESS tep
			LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
			LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
			LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
			LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
			LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
	''')


@st.cache_data
def GET_PARCELAS_EVENTOS_PRICELESS():
   	return dataframe_query(f'''
		SELECT
			tpep.ID AS 'ID_Parcela',
			tpep.FK_EVENTO_PRICELESS AS 'ID_Evento',
			te.NOME_FANTASIA AS 'Casa',
			te.ID AS 'ID Casa',
			tep.NOME_EVENTO AS 'Nome_do_Evento',
			tsep.DESCRICAO AS 'Status Evento',
			tcep.DESCRICAO AS 'Categoria_Parcela',
			tpep.VALOR_PARCELA as 'Valor_Parcela',
			tpep.DATA_VENCIMENTO_PARCELA AS 'Data_Vencimento',
			tsp.DESCRICAO AS 'Status_Pagamento',
			tpep.DATA_RECEBIMENTO_PARCELA AS 'Data_Recebimento' 
		FROM T_PARCELAS_EVENTOS_PRICELESS tpep 
			LEFT JOIN T_EVENTOS_PRICELESS tep ON (tpep.FK_EVENTO_PRICELESS = tep.ID)
			LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tpep.FK_STATUS_PAGAMENTO = tsp.ID)
			LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (tpep.FK_CATEGORIA_PARCELA = tcep.ID)
			LEFT JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON tsep.ID = tep.FK_STATUS_EVENTO
		ORDER BY tep.ID DESC, tpep.ID DESC
	''')

@st.cache_data
def GET_EVENTOS_PRICELESS_KPIS():
   	return dataframe_query(f'''
	SELECT 
		tep.ID AS 'ID Evento',
		te.NOME_FANTASIA AS 'Casa',
		tee.NOME_COMPLETO AS 'Comercial Responsável',
		tee.ID AS 'ID Responsavel Comercial',
		tep.NOME_EVENTO AS 'Nome do Evento',
		trec.NOME AS 'Cliente',
		tep.DATA_ENVIO_PROPOSTA AS 'Data Envio Proposta',
		tep.DATA_CONTRATACAO AS 'Data de Contratação',
		tep.DATA_RECEBIMENTO_LEAD AS 'Data Recebimento Lead',
		tep.DATA_EVENTO AS 'Data do Evento',
		tte.DESCRICAO AS 'Tipo do Evento',
		tme.DESCRICAO AS 'Modelo do Evento',
		tep.VALOR_TOTAL_EVENTO AS 'Valor Total',
		tep.NUM_CLIENTES AS 'Número de Pessoas',
		tep.VALOR_AB AS 'Valor AB',
		COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) as 'Valor Locação Total',
		tep.VALOR_IMPOSTO AS 'Valor Imposto',
		tsep.DESCRICAO AS 'Status do Evento',
		temd.DESCRICAO AS 'Motivo do Declínio',
		tep.OBSERVACOES AS 'Observações'
	FROM T_EVENTOS_PRICELESS tep
		LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
		LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
		LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
		LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
		LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
		LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
		LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
	''')

@st.cache_data
def GET_ORCAMENTOS_EVENTOS():
	return dataframe_query(f'''
		SELECT 
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			to2.ANO AS 'Ano',
			to2.MES AS 'Mês',
			CASE
				WHEN tccg2.DESCRICAO = 'Eventos A&B' THEN 'A&B'
				WHEN tccg2.DESCRICAO = 'Eventos Couvert' THEN 'Couvert'
				WHEN tccg2.DESCRICAO = 'Eventos Locações' THEN 'Locação'
				WHEN tccg2.DESCRICAO = 'Eventos Rebate Fornecedores' THEN 'Repasse Fornecedores'
			END AS 'Categoria Orcamento',
			to2.VALOR AS 'Valor'
		FROM T_ORCAMENTOS to2
			INNER JOIN T_EMPRESAS te ON to2.FK_EMPRESA = te.ID
			INNER JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON to2.FK_CLASSIFICACAO_1 = tccg.ID
			INNER JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON to2.FK_CLASSIFICACAO_2 = tccg2.ID
		WHERE tccg.DESCRICAO = 'Faturamento Bruto' AND tccg2.ID IN (939, 940, 942, 943)
		GROUP BY te.NOME_FANTASIA, to2.ANO, to2.MES, to2.FK_CLASSIFICACAO_2
	''')


@st.cache_data
def GET_RECEBIMENTOS_EVENTOS():
	return dataframe_query(f'''
		SELECT 
			CONCAT(tee.ID, ' - ', tee.NOME_COMPLETO) AS 'ID - Responsavel',
			tee.ID AS 'ID Responsavel',
			tee.COMISSAO_COM_META_ATINGIDA AS 'Comissão Com Meta Atingida',
			tee.COMISSAO_SEM_META_ATINGIDA AS 'Comissão Sem Meta Atingida',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			tep.ID AS 'ID Evento',
			tep.NOME_EVENTO AS 'Nome Evento',
			DATE(tpep.DATA_VENCIMENTO_PARCELA) AS 'Data Vencimento',
			DATE(tpep.DATA_RECEBIMENTO_PARCELA) AS 'Data Recebimento',
			YEAR(tpep.DATA_RECEBIMENTO_PARCELA) AS 'Ano Recebimento',
			MONTH(tpep.DATA_RECEBIMENTO_PARCELA) AS 'Mês Recebimento',
			tpep.VALOR_PARCELA AS 'Valor da Parcela',
			tcep.DESCRICAO AS 'Categoria Parcela'
		FROM T_EVENTOS_PRICELESS tep 
			INNER JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			INNER JOIN T_EXECUTIVAS_EVENTOS tee ON tee.ID = tep.FK_EXECUTIVA_EVENTOS
			INNER JOIN T_PARCELAS_EVENTOS_PRICELESS tpep ON tpep.FK_EVENTO_PRICELESS = tep.ID
			INNER JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (tpep.FK_CATEGORIA_PARCELA = tcep.ID)
		GROUP BY tpep.ID, CONCAT(tee.ID, ' - ', tee.NOME_COMPLETO), te.ID, DATE_FORMAT(tpep.DATA_RECEBIMENTO_PARCELA, '%Y'), DATE_FORMAT(tpep.DATA_RECEBIMENTO_PARCELA, '%m'), tcep.DESCRICAO
		ORDER BY YEAR(tpep.DATA_RECEBIMENTO_PARCELA), MONTH(tpep.DATA_RECEBIMENTO_PARCELA)
''')


@st.cache_data
def GET_EVENTOS_COMISSOES():
	return dataframe_query(f'''
		SELECT 
			tep.ID as 'ID Evento',
			te.NOME_FANTASIA as 'Casa',
			te.ID as 'ID Casa',	
			tee.NOME_COMPLETO as 'Comercial Responsável',
			tep.NOME_EVENTO as 'Nome Evento',
			trec.NOME as 'Cliente',
			DATE(tep.DATA_CONTRATACAO) AS 'Data Contratacao',
			DATE(tep.DATA_EVENTO) AS 'Data Evento',
			tep.VALOR_TOTAL_EVENTO as 'Valor Total',
			tep.VALOR_AB as 'Valor AB',
			tep.VALOR_IMPOSTO as 'Valor Imposto',
			tsep.DESCRICAO as 'Status Evento',
			temd.DESCRICAO as 'Motivo Declínio'
		FROM T_EVENTOS_PRICELESS tep
			LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
			LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
			LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
			LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
			LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
''')


def GET_EVENTOS_AUDITORIA():
	return dataframe_query(f'''
		SELECT DISTINCT 
			tep.ID AS 'ID Evento',
			tep.NOME_EVENTO AS 'Nome Evento',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			tsep.DESCRICAO AS 'Status',
			temd.DESCRICAO AS 'Motivo Declínio',
			tep.VALOR_TOTAL_EVENTO AS 'Valor Total Evento',
			tep.VALOR_AB AS 'Valor AB',
			tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
			tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
			tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
			tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
			tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
			tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
			tep.VALOR_IMPOSTO AS 'Valor Imposto',
			tep.OBSERVACOES AS 'Observações',
			trec.NOME AS 'Cliente',
			DATE(tep.DATA_EVENTO) AS 'Data Evento',
			DATE(tep.DATA_RECEBIMENTO_LEAD) AS 'Data Recebimento Lead',
			DATE(tep.DATA_ENVIO_PROPOSTA) AS 'Data Envio Proposta',
			DATE(tep.DATA_CONTRATACAO) AS 'Data Contratação'
		FROM T_EVENTOS_PRICELESS tep 
			LEFT JOIN T_PARCELAS_EVENTOS_PRICELESS tpep ON tpep.FK_EVENTO_PRICELESS = tep.ID
			INNER JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			INNER JOIN T_EXECUTIVAS_EVENTOS tee ON tee.ID = tep.FK_EXECUTIVA_EVENTOS
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON tsep.ID = tep.FK_STATUS_EVENTO
			LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON temd.ID = tep.FK_MOTIVO_DECLINIO
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
	''')


def GET_PARCELAS_EVENTOS_AUDITORIA():
	return dataframe_query(f'''
		SELECT
			tpep.ID AS 'ID Parcela',
			tpep.FK_EVENTO_PRICELESS AS 'ID Evento',
			te.NOME_FANTASIA AS 'Casa',
			te.ID AS 'ID Casa',
			tep.NOME_EVENTO AS 'Nome do Evento',
			tsep.DESCRICAO AS 'Status Evento',
			tcep.DESCRICAO AS 'Categoria Parcela',
			tpep.VALOR_PARCELA as 'Valor Parcela',
			tpep.DATA_VENCIMENTO_PARCELA AS 'Data Vencimento',
			tsp.DESCRICAO AS 'Status Pagamento',
			tpep.DATA_RECEBIMENTO_PARCELA AS 'Data Recebimento' 
		FROM T_PARCELAS_EVENTOS_PRICELESS tpep 
			LEFT JOIN T_EVENTOS_PRICELESS tep ON (tpep.FK_EVENTO_PRICELESS = tep.ID)
			LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tpep.FK_STATUS_PAGAMENTO = tsp.ID)
			LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (tpep.FK_CATEGORIA_PARCELA = tcep.ID)
			LEFT JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON tsep.ID = tep.FK_STATUS_EVENTO
	''')


def GET_CLIENTES_EVENTOS():
	return dataframe_query(f'''
		SELECT
			trec.ID AS 'ID Cliente',
			trec.NOME AS 'Cliente',
			trec.RAZAO_SOCIAL AS 'Razão Social',
			tsece.DESCRICAO_SETOR AS 'Setor Empresa',
			trec.DOCUMENTO AS 'Documento',
			trec.EMAIL AS 'Email',
			trec.TELEFONE AS 'Telefone',
			trec.PESSOA_DE_CONTATO AS 'Pessoa de Contato',
			trec.ENDERECO_COMPLETO AS 'Endereço',
			trec.CEP AS 'CEP',	
			tep.ID AS 'ID Evento',
			tep.NOME_EVENTO AS 'Nome Evento',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			tsep.DESCRICAO AS 'Status',
			tep.VALOR_TOTAL_EVENTO AS 'Valor Total Evento',
			tep.VALOR_AB AS 'Valor AB',
			tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
			tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
			tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
			tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
			tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
			tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
			tep.VALOR_IMPOSTO AS 'Valor Imposto',
			tep.OBSERVACOES AS 'Observações',
			DATE(tep.DATA_EVENTO) AS 'Data Evento',
			DATE(tep.DATA_RECEBIMENTO_LEAD) AS 'Data Recebimento Lead',
			DATE(tep.DATA_ENVIO_PROPOSTA) AS 'Data Envio Proposta',
			DATE(tep.DATA_CONTRATACAO) AS 'Data Contratação'
		FROM T_EVENTOS_PRICELESS tep
			INNER JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			INNER JOIN T_EXECUTIVAS_EVENTOS tee ON tee.ID = tep.FK_EXECUTIVA_EVENTOS
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
			LEFT JOIN T_SETOR_EMPRESA_CLIENTES_EVENTOS tsece ON tsece.ID = trec.FK_SETOR_CLIENTE 
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON tsep.ID = tep.FK_STATUS_EVENTO
		WHERE tsep.DESCRICAO = 'Confirmado' AND trec.ID IS NOT NULL
	''')