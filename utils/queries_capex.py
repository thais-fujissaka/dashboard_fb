from utils.functions.general_functions import dataframe_query
from utils.constants.general_constants import casas_validas


# Teste
def GET_DESPESAS_CAPEX():
    df_despesas_capex = dataframe_query(f''' 
        SELECT
        tdr.ID as 'ID Despesa',
        te.ID as 'ID Casa',
        te.NOME_FANTASIA as 'Casa',
        tf.ID as 'ID Fornecedor',
        tf.FANTASY_NAME as 'Fornecedor',
        DATE_ADD(STR_TO_DATE(tdr.LANCAMENTO, '%Y-%m-%d'), INTERVAL 30 SECOND) as 'Data Lançamento',  
        DATE_ADD(STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d'), INTERVAL 30 SECOND) as 'Data Competência',
        DATE_ADD(STR_TO_DATE(tdr.VENCIMENTO, '%Y-%m-%d'), INTERVAL 30 SECOND) as 'Data Vencimento',
        tdr.VALOR_PAGAMENTO as 'Valor Original',
        tdr.VALOR_LIQUIDO as 'Valor Liquido',
        tsad.DESCRICAO as 'Status Aprov Diretoria',
        tscd.DESCRICAO as 'Status Aprov Document',
        tsp.DESCRICAO as 'Status Pgto',
        tc.`DATA` as 'Data Pgto',
        tccg2_despesa.DESCRICAO as 'Class. Cont. Despesa',
        tccg2_orcamento.DESCRICAO as 'Class. Cont. Orçamento',                                
        tpc.ID as 'ID Projeto',
        tpc.NOME_PROJETO as 'Nome Projeto',
        toc.ID as 'ID Orçamento',
        toc.ITEM_DESCRICAO_RESUMIDA as 'Descrição Orçamento'
        FROM T_DESPESA_RAPIDA tdr 
        LEFT JOIN T_EMPRESAS te ON (tdr.FK_LOJA = te.ID)
        LEFT JOIN T_FORNECEDOR tf ON (tdr.FK_FORNECEDOR = tf.ID)
        LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_1 tccg ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_1 = tccg.ID)
        LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2_despesa ON (tdr.FK_CLASSIFICACAO_CONTABIL_GRUPO_2 = tccg2_despesa.ID)
        LEFT JOIN T_PROJETOS_CAPEX tpc ON (tdr.FK_PROJETO_CAPEX = tpc.ID)
        LEFT JOIN T_ORCAMENTO_CAPEX toc ON (tdr.FK_ORCAMENTO_CAPEX = toc.ID)
        LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2_orcamento ON (toc.FK_CLASSIFICACAO_GRUPO_2 = tccg2_orcamento.ID)
        LEFT JOIN T_STATUS_APROVACAO_DIRETORIA tsad ON (tdr.FK_APROVACAO_DIRETORIA = tsad.ID)
        LEFT JOIN T_STATUS_CONFERENCIA_DOCUMENTACAO tscd ON (tdr.FK_CONFERENCIA_DOCUMENTACAO = tscd.ID)
        LEFT JOIN T_STATUS_PAGAMENTO tsp ON (tdr.FK_STATUS_PGTO = tsp.ID)
        LEFT JOIN T_CALENDARIO tc ON (tdr.FK_DATA_REALIZACAO_PGTO = tc.ID)
        WHERE tdr.BIT_CANCELADA = 0
        AND tccg.ID = 250
        AND tpc.ID IS NOT NULL                                
       -- AND DATE_ADD(STR_TO_DATE(tdr.COMPETENCIA, '%Y-%m-%d'), INTERVAL 30 SECOND) >= '2025-09-01 00:00:00'
       -- ORDER BY tdr.ID DESC  
    ''')
    return df_despesas_capex


# Projetos CAPEX das casas
def GET_PROJETOS_CAPEX():
    df_projetos_capex = dataframe_query('''
        SELECT 
        tpc.ID as 'ID Projeto',
        te.ID as 'ID Casa',
        te.NOME_FANTASIA as 'Casa',
        tpc.NOME_PROJETO as 'Nome Projeto'
        FROM T_PROJETOS_CAPEX tpc 
        LEFT JOIN T_EMPRESAS te ON (tpc.FK_EMPRESA = te.ID)
    ''')
    return df_projetos_capex


# Orçamentos CAPEX dos projetos
def GET_ORCAMENTOS_CAPEX():
    df_orcamentos_capex = dataframe_query('''
        SELECT 
        toc.ID as 'ID Orçamento',
        te.ID as 'ID Casa',
        te.NOME_FANTASIA as 'Casa',
        tpc.ID as 'ID Projeto',                                  
        toc.DATA_PREVISTA as 'Data Prevista',
        tccg2.DESCRICAO as 'Classificação Contabil 2',                                  
        toc.VALOR_ESTIMADO as 'Valor Estimado', 
        toc.ITEM_DESCRICAO_RESUMIDA as 'Descrição Resumida',
        toc.ITEM_DESCRICAO_DETALHADA as 'Descrição Detalhada'                           
        FROM T_ORCAMENTO_CAPEX toc 
        LEFT JOIN T_EMPRESAS te ON (toc.FK_EMPRESA = te.ID)
        LEFT JOIN T_PROJETOS_CAPEX tpc ON (toc.FK_PROJETO_CAPEX = tpc.ID) 
        LEFT JOIN T_CLASSIFICACAO_CONTABIL_GRUPO_2 tccg2 ON (toc.FK_CLASSIFICACAO_GRUPO_2 = tccg2.ID)                                                                 
    ''')
    return df_orcamentos_capex