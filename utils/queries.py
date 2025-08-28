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
		SELECT
			te.ID AS ID_Casa,
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
def GET_EVENTOS_E_ADITIVOS_PRICELESS():
   	return dataframe_query(f'''
	SELECT 
		tep.ID AS 'ID Evento',
		te.NOME_FANTASIA AS 'Casa',
		te.ID AS 'ID Casa',
		tee.NOME_COMPLETO AS 'Comercial Responsável',
		tep.NOME_EVENTO AS 'Nome Evento',
		trec.NOME AS 'Cliente',
		tep.DATA_CONTRATACAO AS 'Data Contratação',
		tep.DATA_EVENTO AS 'Data Evento',
		tte.DESCRICAO AS 'Tipo Evento',
		tme.DESCRICAO AS 'Modelo Evento',
		tse.DESCRICAO AS 'Segmento Evento',
		tep.VALOR_TOTAL_EVENTO AS 'Valor Total Evento',
		tep.NUM_CLIENTES AS 'Num Pessoas',
		tep.VALOR_AB AS 'Valor AB',
		tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
		COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) + COALESCE(tep.VALOR_LOCACAO_BAR, 0) AS 'Valor Total Locação',
		tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
		tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
		tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
		tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
		tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
		tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
		tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
		tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
		tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
		tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
		tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
		tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
		tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
		tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
		tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
		tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
		tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
		tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO AS 'Valor Contratação Bilheteria/Couvert Artístico',
		tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
		tep.VALOR_IMPOSTO AS 'Valor Imposto',
		tsep.DESCRICAO AS 'Status Evento',
		tep.OBSERVACOES AS 'Observações',
		temd.DESCRICAO AS 'Motivo Declínio',
		tep.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio'
	FROM T_EVENTOS_PRICELESS tep
		LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
		LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
		LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
		LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
		LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
		LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
		LEFT JOIN T_SEGMENTOS_EVENTOS tse ON (tep.FK_SEGMENTO = tse.ID)
		LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
	''')


def GET_EVENTOS():
   	return dataframe_query(f'''
	SELECT 
		tep.ID AS 'ID Evento',
		te.NOME_FANTASIA AS 'Casa',
		te.ID AS 'ID Casa',
		tee.NOME_COMPLETO AS 'Comercial Responsável',
		tep.NOME_EVENTO AS 'Nome Evento',
		trec.NOME AS 'Cliente',
		tep.DATA_CONTRATACAO AS 'Data Contratação',
		tep.DATA_EVENTO AS 'Data Evento',
		tte.DESCRICAO AS 'Tipo Evento',
		tme.DESCRICAO AS 'Modelo Evento',
		tse.DESCRICAO AS 'Segmento Evento',
		tep.VALOR_TOTAL_EVENTO AS 'Valor Total Evento',
		tep.NUM_CLIENTES AS 'Num Pessoas',
		tep.VALOR_AB AS 'Valor AB',
		tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
		COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) AS 'Valor Total Locação',
		tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
		tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
		tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
		tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
		tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
		tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
		tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
		tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
		tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
		tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
		tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO AS 'Valor Contratação Bilheteria/Couvert Artístico',
		tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
		tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
		tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
		tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
		tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
		tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
		tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
		tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
		tep.VALOR_IMPOSTO AS 'Valor Imposto',
		tsep.DESCRICAO AS 'Status Evento',
		tep.OBSERVACOES AS 'Observações',
		temd.DESCRICAO AS 'Motivo Declínio',
		tep.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio'
	FROM T_EVENTOS_PRICELESS tep
		LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
		LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
		LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
		LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
		LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
		LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
		LEFT JOIN T_SEGMENTOS_EVENTOS tse ON (tep.FK_SEGMENTO = tse.ID)
		LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
	WHERE tep.IS_ADITIVO = 0
	''')

@st.cache_data
def GET_ADITIVOS():
   	return dataframe_query(f'''
	SELECT 
		tep.ID AS 'ID Aditivo',
		tep.FK_EVENTO_DO_ADITIVO AS 'ID Evento do Aditivo',
		te.NOME_FANTASIA AS 'Casa',
		te.ID AS 'ID Casa',
		tee.NOME_COMPLETO AS 'Comercial Responsável',
		tep.NOME_EVENTO AS 'Nome Evento',
		trec.NOME AS 'Cliente',
		tep.DATA_CONTRATACAO AS 'Data Contratação',
		tep.DATA_EVENTO AS 'Data Evento',
		tte.DESCRICAO AS 'Tipo Evento',
		tme.DESCRICAO AS 'Modelo Evento',
		tse.DESCRICAO AS 'Segmento Evento',
		tep.VALOR_TOTAL_EVENTO AS 'Valor Total Aditivo',
		tep.NUM_CLIENTES AS 'Num Pessoas',
		tep.VALOR_AB AS 'Valor AB',
		tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
		COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) + COALESCE(tep.VALOR_LOCACAO_BAR, 0) AS 'Valor Total Locação',
		tep.VALOR_LOCACAO_AROO_1 AS 'Valor Locação Aroo 1',
		tep.VALOR_LOCACAO_AROO_2 AS 'Valor Locação Aroo 2',
		tep.VALOR_LOCACAO_AROO_3 AS 'Valor Locação Aroo 3',
		tep.VALOR_LOCACAO_ANEXO AS 'Valor Locação Anexo',
		tep.VALOR_LOCACAO_NOTIE AS 'Valor Locação Notie',
		tep.VALOR_LOCACAO_BAR AS 'Valor Locação Bar',
		tep.VALOR_LOCACAO_MIRANTE AS 'Valor Locação Mirante',
		tep.VALOR_LOCACAO_ESPACO AS 'Valor Locação Espaço',
		tep.VALOR_CONTRATACAO_ARTISTICO AS 'Valor Contratação Artístico',
		tep.VALOR_CONTRATACAO_TECNICO_SOM AS 'Valor Contratação Técnico de Som',
		tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO AS 'Valor Contratação Bilheteria/Couvert Artístico',
		tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
		tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
		tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
		tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
		tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
		tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
		tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
		tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
		tep.VALOR_IMPOSTO AS 'Valor Imposto',
		tsep.DESCRICAO AS 'Status Evento',
		tep.OBSERVACOES AS 'Observações',
		temd.DESCRICAO AS 'Motivo Declínio',
		tep.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio'
	FROM T_EVENTOS_PRICELESS tep
		LEFT JOIN T_EMPRESAS te ON (tep.FK_EMPRESA = te.ID)
		LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep.FK_CLIENTE = trec.ID)
		LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep.FK_STATUS_EVENTO = tsep.ID)
		LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep.FK_MOTIVO_DECLINIO = temd.ID)
		LEFT JOIN T_TIPO_EVENTO tte ON (tep.FK_TIPO_EVENTO = tte.ID)
		LEFT JOIN T_MODELO_EVENTO tme ON (tep.FK_MODELO_EVENTO = tme.ID)
		LEFT JOIN T_SEGMENTOS_EVENTOS tse ON (tep.FK_SEGMENTO = tse.ID)
		LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep.FK_EXECUTIVA_EVENTOS = tee.ID)
	WHERE tep.IS_ADITIVO = 1
	''')	


@st.cache_data
def GET_PARCELAS_EVENTOS_PRICELESS():
   	return dataframe_query(f'''
		SELECT
			tpep.ID AS 'ID Parcela',
			tpep.FK_EVENTO_PRICELESS AS 'ID Evento',
			te.NOME_FANTASIA AS 'Casa',
			te.ID AS 'ID Casa',
			tep.NOME_EVENTO AS 'Nome Evento',
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
		ORDER BY tep.ID DESC, tpep.ID DESC
	''')

@st.cache_data
def GET_EVENTOS_ADITIVOS_AGRUPADOS():
   	return dataframe_query(f'''
		SELECT
			COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID) AS 'ID Evento',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			tee.NOME_COMPLETO AS 'Comercial Responsável',
			tee.ID AS 'ID Responsavel Comercial',
			tep2.NOME_EVENTO AS 'Nome Evento',
			trec.NOME AS 'Cliente',
			tep2.DATA_ENVIO_PROPOSTA AS 'Data Envio Proposta',
			tep2.DATA_CONTRATACAO AS 'Data de Contratação',
			tep2.DATA_RECEBIMENTO_LEAD AS 'Data Recebimento Lead',
			tep2.DATA_EVENTO AS 'Data do Evento',
			tte.DESCRICAO AS 'Tipo do Evento',
			tme.DESCRICAO AS 'Modelo do Evento',
			SUM(tep.VALOR_TOTAL_EVENTO) AS 'Valor Total',
			SUM(tep.NUM_CLIENTES) AS 'Número de Pessoas',
			SUM(tep.VALOR_AB) AS 'Valor AB',
			SUM(COALESCE(tep.VALOR_LOCACAO_AROO_1, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_2, 0) + COALESCE(tep.VALOR_LOCACAO_AROO_3, 0) + COALESCE(tep.VALOR_LOCACAO_ANEXO, 0) + COALESCE(tep.VALOR_LOCACAO_NOTIE, 0) + COALESCE(tep.VALOR_LOCACAO_BAR, 0) + COALESCE(tep.VALOR_LOCACAO_MIRANTE, 0) + COALESCE(tep.VALOR_LOCACAO_ESPACO)) AS 'Valor Locação Total',
			SUM(tep.VALOR_CONTRATACAO_ARTISTICO) AS 'Valor Contratação Artístico',
			SUM(tep.VALOR_CONTRATACAO_TECNICO_SOM) AS 'Valor Contratação Técnico de Som',
			SUM(tep.VALOR_CONTRATACAO_COUVERT_ARTISTICO) AS 'Valor Contratação Bilheteria/Couvert Artístico',
			SUM(tep.VALOR_IMPOSTO) AS 'Valor Imposto',
			SUM(tep.VALOR_LOCACAO_GERADOR) AS 'Valor Locação Gerador',
			SUM(tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO) AS 'Valor Locação Mobiliário',
			SUM(tep.VALOR_LOCACAO_UTENSILIOS) AS 'Valor Locação Utensílios',
			SUM(tep.VALOR_MAO_DE_OBRA_EXTRA) AS 'Valor Mão de Obra Extra',
			SUM(tep.VALOR_TAXA_ADMINISTRATIVA) AS 'Valor Taxa Administrativa',
			SUM(tep.VALOR_COMISSAO_BV) AS 'Valor Comissão BV',
			SUM(tep.VALOR_EXTRAS_GERAIS) AS 'Valor Extras Gerais',
			SUM(tep.VALOR_TAXA_SERVICO) AS 'Valor Taxa Serviço',
			SUM(tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO) AS 'Valor Acréscimo Forma de Pagamento',
			tsep.DESCRICAO AS 'Status do Evento',
			tep2.OBSERVACOES AS 'Observações',
			temd.DESCRICAO AS 'Motivo do Declínio',
			tep2.OBSERVACAO_MOTIVO_DECLINIO AS 'Observações Motivo Declínio',
			tep2.IS_ADITIVO AS 'Is Aditivo'
		FROM T_EVENTOS_PRICELESS tep
			LEFT JOIN T_EVENTOS_PRICELESS tep2 ON COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID) = tep2.ID # tep2 = evento pai
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep2.FK_CLIENTE = trec.ID)
			LEFT JOIN T_TIPO_EVENTO tte ON (tep2.FK_TIPO_EVENTO = tte.ID)
			LEFT JOIN T_MODELO_EVENTO tme ON (tep2.FK_MODELO_EVENTO = tme.ID)
			LEFT JOIN T_EMPRESAS te ON (tep2.FK_EMPRESA = te.ID)
			LEFT JOIN T_EVENTOS_MOTIVOS_DECLINIO temd ON (tep2.FK_MOTIVO_DECLINIO = temd.ID)
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON (tep2.FK_STATUS_EVENTO = tsep.ID)
			LEFT JOIN T_EXECUTIVAS_EVENTOS tee ON (tep2.FK_EXECUTIVA_EVENTOS = tee.ID)
		GROUP BY COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID)
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
			tee.CARGO AS 'Cargo',
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
			tpep.ID AS 'ID Parcela',
			tpep.VALOR_PARCELA AS 'Valor da Parcela',
			tcep.DESCRICAO AS 'Categoria Parcela'
		FROM T_EVENTOS_PRICELESS tep 
			INNER JOIN T_EMPRESAS te ON te.ID = tep.FK_EMPRESA
			INNER JOIN T_EXECUTIVAS_EVENTOS tee ON tee.ID = tep.FK_EXECUTIVA_EVENTOS
			INNER JOIN T_PARCELAS_EVENTOS_PRICELESS tpep ON tpep.FK_EVENTO_PRICELESS = tep.ID
			LEFT JOIN T_CATEGORIA_EVENTO_PRICELESS tcep ON (tpep.FK_CATEGORIA_PARCELA = tcep.ID)
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


def GET_ACESSOS_COMISSOES():
	return dataframe_query(f'''
		SELECT
			CONCAT(tee.ID, ' - ', tee.NOME_COMPLETO) AS 'ID - Responsavel',
			au.EMAIL AS 'E-mail',
			tee.CARGO AS 'Cargo',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa'
		FROM T_ASSOCIATIVA_CASAS_EXECUTIVAS_EVENTOS tacee
			JOIN T_EXECUTIVAS_EVENTOS tee ON (tee.ID = tacee.FK_EXECUTIVAS_EVENTOS)
			JOIN T_EMPRESAS te ON (te.ID = tacee.CASA)
			JOIN ADMIN_USERS au ON (au.ID= tacee.EMAIL)				
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
			tep.VALOR_LOCACAO_GERADOR AS 'Valor Locação Gerador',
			tep.VALOR_LOCACAO_DECORACAO_MOBILIARIO AS 'Valor Locação Mobiliário',
			tep.VALOR_LOCACAO_UTENSILIOS AS 'Valor Locação Utensílios',
			tep.VALOR_MAO_DE_OBRA_EXTRA AS 'Valor Mão de Obra Extra',
			tep.VALOR_TAXA_ADMINISTRATIVA AS 'Valor Taxa Administrativa',
			tep.VALOR_COMISSAO_BV AS 'Valor Comissão BV',
			tep.VALOR_EXTRAS_GERAIS AS 'Valor Extras Gerais',
			tep.VALOR_TAXA_SERVICO AS 'Valor Taxa Serviço',
			tep.VALOR_ACRESCIMO_FORMA_PAGAMENTO AS 'Valor Acréscimo Forma de Pagamento',
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
			tep.NOME_EVENTO AS 'Nome Evento',
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
			COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID) AS 'ID Evento',
			tep2.NOME_EVENTO AS 'Nome Evento',
			te.ID AS 'ID Casa',
			te.NOME_FANTASIA AS 'Casa',
			tsep.DESCRICAO AS 'Status',
			SUM(tep.VALOR_TOTAL_EVENTO) AS 'Valor Total Evento',
			SUM(tep.VALOR_AB) AS 'Valor AB',
			SUM(tep.VALOR_LOCACAO_AROO_1) AS 'Valor Locação Aroo 1',
			SUM(tep.VALOR_LOCACAO_AROO_2) AS 'Valor Locação Aroo 2',
			SUM(tep.VALOR_LOCACAO_AROO_3) AS 'Valor Locação Aroo 3',
			SUM(tep.VALOR_LOCACAO_ANEXO) AS 'Valor Locação Anexo',
			SUM(tep.VALOR_LOCACAO_NOTIE) AS 'Valor Locação Notie',
			SUM(tep.VALOR_LOCACAO_MIRANTE) AS 'Valor Locação Mirante',
			SUM(tep.VALOR_LOCACAO_ESPACO) AS 'Valor Locação Espaço',
			SUM(tep.VALOR_IMPOSTO) AS 'Valor Imposto',
			tep2.OBSERVACOES AS 'Observações',
			DATE(tep.DATA_EVENTO) AS 'Data Evento',
			DATE(tep.DATA_RECEBIMENTO_LEAD) AS 'Data Recebimento Lead',
			DATE(tep.DATA_ENVIO_PROPOSTA) AS 'Data Envio Proposta',
			DATE(tep.DATA_CONTRATACAO) AS 'Data Contratação',
			tep.IS_ADITIVO AS 'Is Aditivo'
		FROM T_EVENTOS_PRICELESS tep
			LEFT JOIN T_EVENTOS_PRICELESS tep2 ON COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID) = tep2.ID
			INNER JOIN T_EMPRESAS te ON te.ID = tep2.FK_EMPRESA
			INNER JOIN T_EXECUTIVAS_EVENTOS tee ON tee.ID = tep2.FK_EXECUTIVA_EVENTOS
			LEFT JOIN T_RECEITAS_EXTRAORDINARIAS_CLIENTE trec ON (tep2.FK_CLIENTE = trec.ID)
			LEFT JOIN T_SETOR_EMPRESA_CLIENTES_EVENTOS tsece ON tsece.ID = trec.FK_SETOR_CLIENTE 
			LEFT JOIN T_STATUS_EVENTO_PRE tsep ON tsep.ID = tep2.FK_STATUS_EVENTO
		WHERE tsep.DESCRICAO = 'Confirmado' AND trec.ID IS NOT NULL
		GROUP BY COALESCE(tep.FK_EVENTO_DO_ADITIVO, tep.ID)
	''')

@st.cache_data
def inputs_expenses(day,day2):
  return dataframe_query(f'''
    SELECT 
    DRI.ID AS 'ID_zAssociac Despesa Item',
    E.ID AS 'ID Casa',
    E.NOME_FANTASIA AS 'Casa',
    DR.ID AS 'ID Despesa',
    F.ID AS 'ID Fornecedor',
    LEFT(F.FANTASY_NAME, 23) AS 'Fornecedor',
    STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d') AS 'Data Competencia',
    I5.ID AS 'ID Insumo',
    I5.DESCRICAO AS 'Insumo',
    I4.ID AS 'ID Nivel 4',
    I4.DESCRICAO AS 'Nivel 4',
    I3.ID AS 'ID Nivel 3',
    I3.DESCRICAO AS 'Nivel 3',
    I2.ID AS 'ID Nivel 2',
    I2.DESCRICAO AS 'Nivel 2',
    I1.ID AS 'ID Nivel 1',
    I1.DESCRICAO AS 'Nivel 1',
    ROUND(CAST(DRI.QUANTIDADE AS FLOAT), 3) AS 'Quantidade Insumo',
    tudm.UNIDADE_MEDIDA_NAME AS 'Unidade Medida',
    ROUND(CAST(DRI.VALOR AS FLOAT), 2) AS 'Valor Insumo'
    FROM T_DESPESA_RAPIDA_ITEM DRI 
    INNER JOIN T_INSUMOS_NIVEL_5 I5 ON (DRI.FK_INSUMO = I5.ID)
    INNER JOIN T_INSUMOS_NIVEL_4 I4 ON (I5.FK_INSUMOS_NIVEL_4 = I4.ID)
    INNER JOIN T_INSUMOS_NIVEL_3 I3 ON (I4.FK_INSUMOS_NIVEL_3 = I3.ID)
    INNER JOIN T_INSUMOS_NIVEL_2 I2 ON (I3.FK_INSUMOS_NIVEL_2 = I2.ID)
    INNER JOIN T_INSUMOS_NIVEL_1 I1 ON (I2.FK_INSUMOS_NIVEL_1 = I1.ID)
    INNER JOIN ADMIN_USERS au ON (DRI.LAST_USER = au.ID)
    INNER JOIN T_DESPESA_RAPIDA DR ON (DRI.FK_DESPESA_RAPIDA = DR.ID)
    INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
    INNER JOIN T_FORNECEDOR F ON (DR.FK_FORNECEDOR = F.ID)
    LEFT JOIN T_UNIDADES_DE_MEDIDAS tudm ON (I5.FK_UNIDADE_MEDIDA = tudm.ID)
    WHERE STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d') >= '{day}'
    AND STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d') <= '{day2}'
    AND I1.ID IN (100,101)
    AND E.FK_GRUPO_EMPRESA = 100
    ORDER BY DR.ID
  ''')


@st.cache_data
def supplier_expense_n5(day,day2):
  return dataframe_query(f"""
SELECT 
		F.ID AS 'ID Fornecedor',
		F.FANTASY_NAME AS 'Fornecedor',
    E.NOME_FANTASIA AS 'Casa',
    N5.ID AS 'ID Nivel 5',
    N5.DESCRICAO AS 'INSUMO N5',
    SUM(DRI.QUANTIDADE) AS 'Quantidade Insumo',
    SUM(DRI.VALOR) AS 'Valor Insumo',
    SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE) AS 'Valor Med Por Insumo'                                
    FROM T_DESPESA_RAPIDA_ITEM DRI 
    INNER JOIN T_INSUMOS_NIVEL_5 N5 ON (DRI.FK_INSUMO = N5.ID)
    INNER JOIN T_DESPESA_RAPIDA DR ON (DRI.FK_DESPESA_RAPIDA = DR.ID)
    INNER JOIN T_FORNECEDOR F ON (DR.FK_FORNECEDOR = F.ID)
    INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
    WHERE DR.COMPETENCIA >= '{day}'
    AND DR.COMPETENCIA <= '{day2}'

		GROUP BY F.ID, N5.ID
    ORDER BY F.FANTASY_NAME, N5.DESCRICAO
""")

@st.cache_data
def item_sold():
  return dataframe_query(f"""
    WITH ULTIMO_VALOR AS (
      SELECT 
        IV.PRODUCT_ID,
        MAX(IV.TRANSACTION_DATE) AS MAX_DATE,
        IV.UNIT_VALUE
      FROM T_ITENS_VENDIDOS IV
      WHERE IV.UNIT_VALUE > 1
      GROUP BY IV.PRODUCT_ID
    )

    SELECT
        IVC.CASA AS 'EMPRESA',
        AIFT.ID AS 'ID_Assoc',
        IVC.ITEM_VENDIDO AS 'Item Vendido',
        IVC.CATEGORIA AS 'CATEGORIA',
        IE.ID AS 'ID Insumo de Estoque',
        IE.DESCRICAO AS 'Insumo de Estoque',
        UM.UNIDADE_MEDIDA AS 'Unidade Medida',
        AIFT.QUANTIDADE_POR_FICHA AS 'Quantidade na Ficha',
        UV.UNIT_VALUE AS 'VALOR DO ITEM'
    FROM T_ASSOCIATIVA_INSUMOS_FICHA_TECNICA AIFT
    LEFT JOIN T_FICHAS_TECNICAS FT ON AIFT.FK_FICHA_TECNICA = FT.ID
    LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA IVC ON FT.FK_ITEM_VENDIDO_POR_CASA = IVC.ID
    LEFT JOIN T_INSUMOS_ESTOQUE IE ON AIFT.FK_ITEM_ESTOQUE = IE.ID
    LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON IE.FK_UNIDADE_MEDIDA = UM.ID
    LEFT JOIN ULTIMO_VALOR UV ON UV.PRODUCT_ID = IVC.ID_ZIG_ITEM_VENDIDO

    UNION ALL

    SELECT 
        IVC.CASA AS 'EMPRESA',
        AIPFT.ID AS 'ID_Assoc',
        IVC.ITEM_VENDIDO AS 'Item Vendido',
        IVC.CATEGORIA AS 'CATEGORIA',
        'IP' AS 'ID Insumo de Estoque',
        IP.NOME_ITEM_PRODUZIDO AS 'Insumo de Estoque',
        UM.UNIDADE_MEDIDA AS 'Unidade Medida',
        AIPFT.QUANTIDADE AS 'Quantidade na Ficha',
        UV.UNIT_VALUE AS 'VALOR DO ITEM'
    FROM T_ASSOCIATIVA_ITENS_PRODUCAO_FICHA_TECNICA AIPFT
    LEFT JOIN T_FICHAS_TECNICAS FT ON AIPFT.FK_FICHA_TECNICA = FT.ID
    LEFT JOIN T_VISUALIZACAO_ITENS_VENDIDOS_POR_CASA IVC ON FT.FK_ITEM_VENDIDO_POR_CASA = IVC.ID
    LEFT JOIN T_ITENS_PRODUCAO IP ON AIPFT.FK_ITEM_PRODUCAO = IP.ID
    LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON IP.FK_UNIDADE_MEDIDA = UM.ID
    LEFT JOIN ULTIMO_VALOR UV ON UV.PRODUCT_ID = IVC.ID_ZIG_ITEM_VENDIDO
    ORDER BY `Item Vendido`;
    """)


@st.cache_data
def input_produced(day, day2):
    return dataframe_query(f"""
        SELECT
            E.NOME_FANTASIA AS 'EMPRESA',
            IP.NOME_ITEM_PRODUZIDO AS 'ITEM PRODUZIDO',
        FTP.QUANTIDADE_FICHA AS 'RENDIMENTO',
        COALESCE(IE.DESCRICAO, IP2.NOME_ITEM_PRODUZIDO) AS 'Insumo de Estoque',
        AFTIP.QUANTIDADE AS 'QUANTIDADE INSUMO',
        #(DRI.VALOR / DRI.QUANTIDADE) AS 'Média Preço (Insumo de Compra)',
        ((DRI.VALOR / DRI.QUANTIDADE) / ACE.PROPORCAO) AS 'MÉDIA PREÇO NO ITEM KG',
        (AFTIP.QUANTIDADE / 1000) * ((DRI.VALOR / DRI.QUANTIDADE) / ACE.PROPORCAO) AS 'VALOR PRODUÇÃO'
        FROM T_ITENS_PRODUCAO IP
        LEFT JOIN T_EMPRESAS E ON E.ID = IP.FK_EMPRESA
        LEFT JOIN T_FICHA_TECNICA_PRODUCAO FTP ON FTP.FK_ITEM_PRODUZIDO = IP.ID
        LEFT JOIN T_ASSOCIATIVA_FICHAS_TECNICAS_ITENS_PRODUCAO AFTIP ON AFTIP.FK_FICHA_PRODUCAO = FTP.ID
        LEFT JOIN T_ITENS_PRODUCAO IP2 ON IP2.ID = AFTIP.FK_ITEM_PRODUZIDO 
        LEFT JOIN T_INSUMOS_ESTOQUE IE ON IE.ID = AFTIP.FK_INSUMO_ESTOQUE
        LEFT JOIN T_ASSOCIATIVA_COMPRA_ESTOQUE ACE ON IE.ID = ACE.FK_INSUMO_ESTOQUE
        LEFT JOIN T_INSUMOS_NIVEL_5 N5 ON ACE.FK_INSUMO = N5.ID
        LEFT JOIN T_INSUMOS_NIVEL_4 N4 ON N4.ID = N5.FK_INSUMOS_NIVEL_4
        LEFT JOIN T_INSUMOS_NIVEL_3 N3 ON N3.ID = N4.FK_INSUMOS_NIVEL_3
        LEFT JOIN T_INSUMOS_NIVEL_2 N2 ON N2.ID = N3.FK_INSUMOS_NIVEL_2
        LEFT JOIN T_INSUMOS_NIVEL_1 N1 ON N1.ID = N2.FK_INSUMOS_NIVEL_1
        LEFT JOIN (
        SELECT
            DRI.ID,
            DR.COMPETENCIA,
            E2.NOME_FANTASIA,
            E2.ID AS ID_CASA,
            DRI.FK_INSUMO,
            DRI.QUANTIDADE,
            DRI.VALOR,
            ACE.FK_INSUMO_ESTOQUE,
            ACE.PROPORCAO
        FROM T_DESPESA_RAPIDA_ITEM DRI
        INNER JOIN T_DESPESA_RAPIDA DR ON DR.ID = DRI.FK_DESPESA_RAPIDA
        LEFT JOIN T_ASSOCIATIVA_COMPRA_ESTOQUE ACE ON ACE.FK_INSUMO = DRI.FK_INSUMO
        LEFT JOIN T_EMPRESAS E2 ON E2.ID = DR.FK_LOJA
        WHERE DATE(DR.COMPETENCIA) >= '{day}' AND DATE(DR.COMPETENCIA) <= '{day2}'
        AND DRI.VALOR > 0
        GROUP BY DRI.ID
        ) AS DRI ON DRI.FK_INSUMO = N5.ID
        LEFT JOIN T_CONTAGEM_INSUMOS CI ON CI.FK_INSUMO = N5.ID
        WHERE (DATE(CI.DATA_CONTAGEM) >= '{day}' 
        AND DATE(CI.DATA_CONTAGEM) <= '{day2}' OR CI.DATA_CONTAGEM IS NULL)
        AND FTP.ID IS NOT NULL
        AND N1.DESCRICAO IN ('BEBIDAS','ALIMENTOS')
        GROUP BY E.ID, IP.ID, IE.ID
        ORDER BY IP.NOME_ITEM_PRODUZIDO
""")


@st.cache_data
def average_inputN5_price(day, day2):
  return dataframe_query(f"""
SELECT 
    E.ID AS 'CASA ID',
    E.NOME_FANTASIA AS 'EMPRESA',
    N5.ID AS 'ID N5',
    N5.DESCRICAO AS 'INSUMO N5',
    UM.UNIDADE_MEDIDA_NAME AS 'Unidade de  Medida N5',
    SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE) AS 'Média Preço (Insumo de Compra)',
    IE.ID AS 'ID Insumo de Estoque',
    IE.DESCRICAO AS 'Insumo de Estoque',
    UM2.UNIDADE_MEDIDA_NAME AS 'Unidade de Medida Estoque',
    ACE.PROPORCAO AS 'Proporção Compra',
    ROUND(CAST(SUM(DRI.VALOR) AS FLOAT), 2) AS 'VALOR DRI',
    ROUND(CAST(SUM(DRI.QUANTIDADE) AS FLOAT), 3) AS 'QUANTIDADE DRI',
    ACE.PROPORCAO AS 'PROPORÇÃO ACE',
    (SUM(DRI.VALOR) / SUM(DRI.QUANTIDADE)) / ACE.PROPORCAO AS 'Média Preço (Insumo Estoque)'
  
    FROM T_DESPESA_RAPIDA_ITEM DRI 
    INNER JOIN T_INSUMOS_NIVEL_5 N5 ON (DRI.FK_INSUMO = N5.ID)
    LEFT JOIN T_INSUMOS_NIVEL_4 N4 ON N4.ID = N5.FK_INSUMOS_NIVEL_4
    LEFT JOIN T_INSUMOS_NIVEL_3 N3 ON N3.ID = N4.FK_INSUMOS_NIVEL_3
    LEFT JOIN T_INSUMOS_NIVEL_2 N2 ON N2.ID = N3.FK_INSUMOS_NIVEL_2
    LEFT JOIN T_INSUMOS_NIVEL_1 N1 ON N1.ID = N2.FK_INSUMOS_NIVEL_1
    INNER JOIN T_DESPESA_RAPIDA DR ON (DRI.FK_DESPESA_RAPIDA = DR.ID)
    INNER JOIN T_EMPRESAS E ON (DR.FK_LOJA = E.ID)
    LEFT JOIN T_UNIDADES_DE_MEDIDAS UM ON (N5.FK_UNIDADE_MEDIDA = UM.ID)
    LEFT JOIN T_ASSOCIATIVA_COMPRA_ESTOQUE ACE ON (ACE.FK_INSUMO = N5.ID)
    LEFT JOIN T_INSUMOS_ESTOQUE IE ON (IE.ID = ACE.FK_INSUMO_ESTOQUE)
    LEFT JOIN T_UNIDADES_DE_MEDIDAS UM2 ON IE.FK_UNIDADE_MEDIDA = UM2.ID
    WHERE STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d') >= '{day}'
    AND STR_TO_DATE(DR.COMPETENCIA, '%Y-%m-%d') <= '{day2}'
    AND N1.DESCRICAO IN ('BEBIDAS','ALIMENTOS')
    GROUP BY E.ID, N5.ID
    ORDER BY N5.DESCRICAO
""")
