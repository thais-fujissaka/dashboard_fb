import pymysql
import pandas as pd
import streamlit as st
import time

def atualizar_faturam_agregado_dia(data_inicio, data_fim):
    """
    Função para processar faturamento agregado por período específico usando INSERT ... ON DUPLICATE KEY UPDATE
    """
    print(f"=== PROCESSANDO FATURAMENTO AGREGADO ZIG ===")
    print(f"Período: {data_inicio} a {data_fim}")
    print("=" * 50)
    
    conn = pymysql.connect(
        host=st.secrets["mysql_fb"]["host"],
        user=st.secrets["mysql_fb"]["username"],
        password=st.secrets["mysql_fb"]["password"],
        port=st.secrets["mysql_fb"]["port"],
        database=st.secrets["mysql_fb"]["database"]
    )
    
    try:
        with conn.cursor() as c:
            # Query de faturamento agregado
            sql_faturam_itens_agrup = '''
            SELECT
                te.ID AS ID_Casa,
                tiv.PRODUCT_ID,
                tiv.PRODUCT_SKU,
                tiv.PRODUCT_NAME,
                DATE(tiv.EVENT_DATE) AS Data_Evento,
                tiv.UNIT_VALUE AS VALOR_UNITARIO,
                COALESCE(SUM(tiv.COUNT), 0) AS QUANTIDADE,
                COALESCE(SUM(tiv.DISCOUNT_VALUE), 0) AS DESCONTO,
                tiv.REDE_ID,
                tiv.LOJA_ID,
                tiv.EVENT_ID
            FROM T_CALENDARIO tc
            LEFT JOIN T_ITENS_VENDIDOS tiv ON DATE(tc.DATA) = DATE(tiv.EVENT_DATE)
            LEFT JOIN T_EMPRESAS te ON tiv.LOJA_ID = te.ID_ZIGPAY
            WHERE tc.DATA >= %s
              AND tc.DATA <= %s
            GROUP BY te.ID, tiv.PRODUCT_ID, DATE(tiv.EVENT_DATE), tiv.UNIT_VALUE
            ORDER BY te.ID, tiv.PRODUCT_ID, DATE(tiv.EVENT_DATE)z, tiv.UNIT_VALUE
            '''
            
            print("Executando query de faturamento agregado...")
            c.execute(sql_faturam_itens_agrup, (data_inicio, data_fim))
            resultado = c.fetchall()
            colunas = [desc[0] for desc in c.description]
            df = pd.DataFrame(resultado, columns=colunas)
            
            print(f"Dados obtidos: {len(df)} registros")
            if df.empty:
                print("Nenhum dado encontrado para processar.")
                return
            else:
                st.toast('Dataframe criado com sucesso!', icon="✅")
            
            # Preparar dados para INSERT
            valores = []
            for _, row in df.iterrows():
                valores.append((
                    row['ID_Casa'], row['PRODUCT_ID'], row['PRODUCT_SKU'], row['PRODUCT_NAME'],
                    row['VALOR_UNITARIO'], row['QUANTIDADE'], row['DESCONTO'],
                    row['REDE_ID'], row['LOJA_ID'], row['EVENT_ID'], row['Data_Evento']
                ))
            
            # Inserção em batch com ON DUPLICATE KEY UPDATE
            sql_insert = '''
            INSERT INTO T_ITENS_VENDIDOS_DIA
            (FK_CASA, PRODUCT_ID, PRODUCT_SKU, PRODUCT_NAME, VALOR_UNITARIO,
             QUANTIDADE, DESCONTO, REDE_ID, LOJA_ID, EVENT_ID, EVENT_DATE)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                QUANTIDADE = VALUES(QUANTIDADE),
                DESCONTO = VALUES(DESCONTO)
            '''
            
            # Executar em batch
            batch_size = 500  # ajustável conforme volume
            total = len(valores)
            for i in range(0, total, batch_size):
                batch = valores[i:i+batch_size]
                c.executemany(sql_insert, batch)
                print(f"Processados {min(i+batch_size, total)} / {total} registros...")
            
        conn.commit()
        st.toast(f"Processamento de {total} registros concluído!")
    
    finally:
        conn.close()
