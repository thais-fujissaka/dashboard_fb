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
			tee.NOME_COMPLETO as 'Comercial_Responsavel',
			tep.NOME_EVENTO as 'Nome_do_Evento',
			trec.NOME as 'Cliente',
			tep.DATA_CONTRATACAO as 'Data_Contratacao',
			tep.DATA_EVENTO as 'Data_Evento',
			tte.DESCRICAO as 'Tipo_Evento',
			tme.DESCRICAO as 'Modelo_Evento',
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
			tpep.ID as 'ID_Parcela',
			tpep.FK_EVENTO_PRICELESS as 'ID_Evento',
			te.NOME_FANTASIA AS 'Casa',
			tep.NOME_EVENTO as 'Nome_do_Evento',
			tcep.DESCRICAO as 'Categoria_Parcela',
			tpep.VALOR_PARCELA as 'Valor_Parcela',
			tpep.DATA_VENCIMENTO_PARCELA as 'Data_Vencimento',
			tsp.DESCRICAO as 'Status_Pagamento',
			tpep.DATA_RECEBIMENTO_PARCELA as 'Data_Recebimento' 
		FROM T_PARCELAS_EVENTOS_PRICELESS tpep 
			LEFT JOIN T_EVENTOS_PRICELESS tep ON (tpep.FK_EVENTO_PRICELESS = tep.ID)
			LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tpep.FK_STATUS_PAGAMENTO = tsp.ID)
			LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (tpep.FK_CATEGORIA_PARCELA = tcep.ID)
			LEFT JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
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
			tep.DATA_EVENTO AS 'Data do Evento',
			tte.DESCRICAO AS 'Tipo do Evento',
			tme.DESCRICAO AS 'Modelo do Evento',
			tep.VALOR_TOTAL_EVENTO AS 'Valor Total',
			tep.NUM_CLIENTES AS 'Número de Pessoas',
			tep.VALOR_AB AS 'Valor AB',
			COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) as 'Valor_Locacao_Total',
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
			to2.MES AS 'Mês',
			to2.ANO AS 'Ano',
			SUM(to2.VALOR) AS 'Valor'
		FROM T_ORCAMENTOS to2
			INNER JOIN T_EMPRESAS te ON to2.FK_EMPRESA = te.ID
			INNER JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON to2.FK_CLASSIFICACAO_1 = tccg.ID
			INNER JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON to2.FK_CLASSIFICACAO_2 = tccg2.ID
		WHERE tccg.DESCRICAO = 'Faturamento Bruto' AND tccg2.ID IN (939, 940, 942, 943)
		GROUP BY te.NOME_FANTASIA, to2.ANO, to2.MES
	''')


@st.cache_data
def GET_RECEBIMENTOS_EVENTOS():
	return dataframe_query(f'''
		SELECT 
			CONCAT(tee.ID, ' - ', tee.NOME_COMPLETO) AS 'ID - Responsavel',
			te.ID AS 'ID Casa',
			YEAR(tpep.DATA_RECEBIMENTO_PARCELA) AS 'Ano Recebimento',
			MONTH(tpep.DATA_RECEBIMENTO_PARCELA) AS 'Mês Recebimento',
			SUM(tpep.VALOR_PARCELA) AS 'Valor Total Parcelas'
		FROM T_EVENTOS_PRICELESS tep 
			INNER JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			INNER JOIN T_EXECUTIVAS_EVENTOS tee ON tee.ID = tep.FK_EXECUTIVA_EVENTOS
			INNER JOIN T_PARCELAS_EVENTOS_PRICELESS tpep ON tpep.FK_EVENTO_PRICELESS = tep.ID
		GROUP BY CONCAT(tee.ID, ' - ', tee.NOME_COMPLETO), te.ID, DATE_FORMAT(tpep.DATA_RECEBIMENTO_PARCELA, '%Y'), DATE_FORMAT(tpep.DATA_RECEBIMENTO_PARCELA, '%m')
	''')