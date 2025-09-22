import streamlit as st
import pandas as pd
from utils.functions.general_functions import *
from utils.functions.conciliacoes import *
from utils.constants.general_constants import *


# Exibe correspondência de blueme sem parcelamento, blueme com parcelamento, saidas mutuos e bloqueios com extrato: chamada em 'cria_tabs_contas'
def itens_por_conta(id_casa, ids_outras, df_custos_blueme_sem_parc, df_custos_blueme_com_parc, df_bloqueios, df_saidas_mutuos, df_extratos_bancarios, conta, item):
    if conta == "Outras contas":
        # filtra os extratos
        df_extratos_outras = df_extratos_bancarios[df_extratos_bancarios['ID_Conta_Bancaria'].isin(ids_outras)]

        if id_casa == 116: # Bar Léo - Centro (tem valores de DEBITO positivos)
            df_extratos_outras["Valor"] = df_extratos_outras["Valor"].apply(lambda x: -x if x < 0 else x)
        else:
            df_extratos_outras['Valor'] = df_extratos_outras['Valor'] * (-1)
            
        df_extratos_outras.loc[:, 'Data_Transacao'] = df_extratos_outras['Data_Transacao'].dt.date

        if item == "blueme sem parcelamento outras":
            # filtra as despesas dessas contas
            df_blueme_outras = df_custos_blueme_sem_parc[
                df_custos_blueme_sem_parc['ID_Conta_Bancaria'].isin(ids_outras) 
                | df_custos_blueme_sem_parc['ID_Conta_Bancaria'].isna()]                
            df_blueme_outras.loc[:, 'Realizacao_Pgto'] = df_blueme_outras['Realizacao_Pgto'].dt.date

            # faz o merge para tentar conciliar
            df_blueme_outras = merge_com_fuzzy(
            df_blueme_outras,
            df_extratos_outras,
            left_on=['ID_Conta_Bancaria', 'Realizacao_Pgto', 'Valor'],
            right_on=['ID_Conta_Bancaria', 'Data_Transacao', 'Valor'],
            principal='despesa',
            text_left='Fornecedor',
            text_right='Descricao_Transacao',
            exceptions=exceptions,  
            limiar=40      
            )

            if 'ID_Conta_Bancaria_despesa' in df_blueme_outras.columns:
                df_blueme_outras = df_blueme_outras.rename(columns={"ID_Conta_Bancaria_despesa": "ID_Conta_Bancaria"})
            
            # Seleciona só colunas mais importantes e reordena
            df_blueme_outras = df_blueme_outras[["ID_Despesa", "ID_Extrato_Bancario", "ID_Conta_Bancaria", "Conta_Bancaria", "Fornecedor", "Valor", "Realizacao_Pgto", "Forma_Pagamento", "Class_Cont_1", "Class_Cont_2", "Doc_NF", "Status_Conf_Document", "Status_Aprov_Diret", "Status_Aprov_Caixa", "Data_Transacao", "Descricao_Transacao"]]
            df_blueme_outras["ID_Conta_Bancaria"] = df_blueme_outras["ID_Conta_Bancaria"].astype("Int64")
            df_blueme_outras["ID_Extrato_Bancario"] = df_blueme_outras["ID_Extrato_Bancario"].astype("Int64")
            df_blueme_outras = df_blueme_outras.rename(
                columns={"Data_Transacao": "Data_Transacao_Extrato",
                        "Descricao_Transacao": "Descricao_Transacao_Extrato"
                })

            # Estiliza e exibe 
            df_blueme_outras = df_blueme_outras.sort_values(by="Realizacao_Pgto", ascending=False)
            df_blueme_outras_styled = df_blueme_outras.style.apply(colorir_linhas(df_blueme_outras, 'ID_Despesa', 'Status_Conf_Document', 'Status_Aprov_Diret', 'despesa'), axis=1)
            st.dataframe(df_blueme_outras_styled, use_container_width=True, hide_index=True)
            exibir_legenda("contas")
            st.write("")

            col1, col2 = st.columns([6, 1], vertical_alignment="center")
            with col2:
                button_download(df_blueme_outras, 'ID_Extrato_Bancario', f"Blueme Sem Parc - Extrato", key=f'download_{item}_{conta}')
            st.divider()
        
        elif item == "blueme com parcelamento outras":
            # filtra as despesas dessas contas
            df_blueme_com_parc_outras = df_custos_blueme_com_parc[
                df_custos_blueme_com_parc['ID_Conta_Bancaria'].isin(ids_outras) 
                | df_custos_blueme_com_parc['ID_Conta_Bancaria'].isna()]                
            df_blueme_com_parc_outras.loc[:, 'Realiz_Parcela'] = df_blueme_com_parc_outras['Realiz_Parcela'].dt.date
            
            # faz o merge para tentar conciliar
            df_blueme_com_parc_outras = merge_com_fuzzy(
            df_blueme_com_parc_outras,
            df_extratos_outras,
            left_on=['Realiz_Parcela', 'Valor_Parcela'],
            right_on=['Data_Transacao', 'Valor'],
            principal='despesa',
            text_left='Fornecedor',
            text_right='Descricao_Transacao',
            exceptions=exceptions,  
            limiar=40
            )

            if 'ID_Conta_Bancaria_despesa' in df_blueme_com_parc_outras.columns:
                df_blueme_com_parc_outras = df_blueme_com_parc_outras.rename(columns={"ID_Conta_Bancaria_despesa": "ID_Conta_Bancaria"})
            
            # Seleciona só colunas mais importantes e reordena
            df_blueme_com_parc_outras = df_blueme_com_parc_outras[["ID_Parcela", "ID_Despesa", "ID_Extrato_Bancario", "ID_Conta_Bancaria", "Conta_Bancaria", "Fornecedor", "Qtd_Parcelas", "Num_Parcela", "Valor_Parcela", "Realiz_Parcela", "Forma_Pagamento", "Doc_NF", "Class_Cont_1", "Class_Cont_2", "Status_Conf_Document", "Status_Aprov_Diret", "Status_Aprov_Caixa", "Data_Transacao", "Descricao_Transacao"]]
            df_blueme_com_parc_outras["ID_Conta_Bancaria"] = df_blueme_com_parc_outras["ID_Conta_Bancaria"].astype("Int64")
            df_blueme_com_parc_outras["ID_Extrato_Bancario"] = df_blueme_com_parc_outras["ID_Extrato_Bancario"].astype("Int64")
            df_blueme_com_parc_outras = df_blueme_com_parc_outras.rename(
                columns={"Data_Transacao": "Data_Transacao_Extrato",
                        "Descricao_Transacao": "Descricao_Transacao_Extrato"
                })

            # Estiliza e exibe 
            df_blueme_com_parc_outras = df_blueme_com_parc_outras.sort_values(by="Realiz_Parcela", ascending=False)
            df_blueme_com_parc_outras_styled = df_blueme_com_parc_outras.style.apply(colorir_linhas(df_blueme_com_parc_outras, 'ID_Parcela', 'Status_Conf_Document', 'Status_Aprov_Diret', 'despesa'), axis=1)
            st.dataframe(df_blueme_com_parc_outras_styled, use_container_width=True, hide_index=True)
            exibir_legenda("contas")
            st.write("")

            col1, col2 = st.columns([6, 1], vertical_alignment="center")
            with col2:
                button_download(df_blueme_com_parc_outras, 'ID_Extrato_Bancario', f"Blueme Com Parc - Extrato", key=f'download_{item}_{conta}')
            st.divider()
        
        elif item == "saidas mutuos outras":
            # filtra pela conta de saida
            df_extratos_contas = df_extratos_bancarios[~df_extratos_bancarios['ID_Conta_Bancaria'].isin(ids_outras)]
            df_extratos_contas['Valor'] = df_extratos_contas['Valor'] * (-1)
            df_extratos_contas['Data_Transacao'] = pd.to_datetime(df_extratos_contas['Data_Transacao']).dt.normalize()

            df_saidas_mutuos_outras = df_saidas_mutuos[
                df_saidas_mutuos['ID_Conta_Saida'].isin(ids_outras) 
                | df_saidas_mutuos['ID_Conta_Saida'].isna()]  

            df_saidas_mutuos_outras.loc[:, 'Data_Mutuo'] = pd.to_datetime(df_saidas_mutuos_outras['Data_Mutuo']).dt.normalize()

            # Não vou usar o campo 'Observacoes' - muitos None
            df_saidas_mutuos_outras = df_saidas_mutuos_outras.merge(
            df_extratos_contas,
            left_on=['Data_Mutuo', 'Valor'], 
            right_on=['Data_Transacao', 'Valor'],
            how='left'
            )

            # Seleciona só colunas mais importantes e reordena
            df_saidas_mutuos_outras = df_saidas_mutuos_outras[["Mutuo_ID", "ID_Extrato_Bancario", "Data_Mutuo", "Valor", "ID_Conta_Saida", "Conta_Saida", "Casa_Entrada", "ID_Conta_Entrada", "Conta_Entrada", "Observacoes", "Data_Transacao", "Descricao_Transacao"]]
            df_saidas_mutuos_outras["Mutuo_ID"] = df_saidas_mutuos_outras["Mutuo_ID"].astype("Int64")
            df_saidas_mutuos_outras["ID_Extrato_Bancario"] = df_saidas_mutuos_outras["ID_Extrato_Bancario"].astype("Int64")
            df_saidas_mutuos_outras = df_saidas_mutuos_outras.rename(
                columns={"Data_Transacao": "Data_Transacao_Extrato",
                        "Descricao_Transacao": "Descricao_Transacao_Extrato"
                })

            # Estiliza e exibe
            df_saidas_mutuos_outras = df_saidas_mutuos_outras.sort_values(by="Data_Mutuo", ascending=False)
            df_saidas_mutuos_outras_styled = df_saidas_mutuos_outras.style.apply(colorir_linhas(df_saidas_mutuos_outras, 'Mutuo_ID', 'Status_Conf_Document', 'Status_Aprov_Diret', 'despesa'), axis=1)
            st.dataframe(df_saidas_mutuos_outras_styled, use_container_width=True, hide_index=True)
            exibir_legenda("contas")
            st.write("")

            col1, col2 = st.columns([6, 1], vertical_alignment="center")
            with col2:
                button_download(df_saidas_mutuos_outras, 'ID_Extrato_Bancario', f"Saidas Mutuos - Extrato", key=f'download_{item}_{conta}')
            st.divider()

    else:
        nome_conta = conta
        if nome_conta == "Bar Léo -  Aurora Térreo - Banco do Brasil": 
            st.warning('Problemas no Valor do Extrato Bancário')

        # filtra os extratos
        df_extratos_conta = df_extratos_bancarios[df_extratos_bancarios['Nome_Conta_Bancaria'] == nome_conta]
        
        if id_casa == 116: # Bar Léo - Centro
            df_extratos_conta["Valor"] = df_extratos_conta["Valor"].apply(lambda x: -x if x < 0 else x)
        else:
            df_extratos_conta.loc[:, 'Valor'] = df_extratos_conta['Valor'] * -1
        
        df_extratos_conta.loc[:, 'Data_Transacao'] = df_extratos_conta['Data_Transacao'].dt.date

        if item == "blueme sem parcelamento":
            if nome_conta == "Arcos - Arcos Bar - Banco do Brasil": 
                st.warning('Observação: Folha de Pagamento')
            elif nome_conta == "Bar Brahma - Ypiranga Matriz - Bradesco": 
                st.warning('Observações do extrato completamente diferentes do fornecedor da despesa')
            elif nome_conta == "Bar Brahma - Tutum Matriz - Kamino":
                st.warning('Observação: Valores de Gorjeta')

            # filtra as despesas dessas contas
            df_blueme_sem_parc_conta = df_custos_blueme_sem_parc[df_custos_blueme_sem_parc['Conta_Bancaria'] == nome_conta]
            df_blueme_sem_parc_conta.loc[:, 'Realizacao_Pgto'] = df_blueme_sem_parc_conta['Realizacao_Pgto'].dt.date

            if id_casa == 145: # Ultra Evil tem duas contas (184, 185) com o mesmo nome
                # faz o merge para tentar conciliar
                df_blueme_sem_parc = merge_com_fuzzy(
                df_blueme_sem_parc_conta,
                df_extratos_conta,
                left_on=['Realizacao_Pgto', 'Valor'],
                right_on=['Data_Transacao', 'Valor'],
                principal='despesa',
                text_left='Fornecedor',
                text_right='Descricao_Transacao',
                exceptions=exceptions,  
                limiar=60   
                )
                df_blueme_sem_parc = df_blueme_sem_parc.rename(columns={"ID_Conta_Bancaria_despesa": "ID_Conta_Bancaria"})

            else:
                # faz o merge para tentar conciliar
                df_blueme_sem_parc = merge_com_fuzzy(
                df_blueme_sem_parc_conta,
                df_extratos_conta,
                left_on=['Realizacao_Pgto', 'Valor'],
                right_on=['Data_Transacao', 'Valor'],
                principal='despesa',
                text_left='Fornecedor',
                text_right='Descricao_Transacao',
                exceptions=exceptions,  
                limiar=30   
                )

            # Seleciona só colunas mais importantes e reordena
            if "ID_Conta_Bancaria_despesa" in df_blueme_sem_parc.columns:
                df_blueme_sem_parc = df_blueme_sem_parc.rename(columns={"ID_Conta_Bancaria_despesa": "ID_Conta_Bancaria"})
            
            df_blueme_sem_parc = df_blueme_sem_parc[["ID_Despesa", "ID_Extrato_Bancario", "ID_Conta_Bancaria", "Conta_Bancaria", "Fornecedor", "Valor", "Realizacao_Pgto", "Forma_Pagamento", "Class_Cont_1", "Class_Cont_2", "Doc_NF", "Status_Conf_Document", "Status_Aprov_Diret", "Status_Aprov_Caixa", "Data_Transacao", "Descricao_Transacao"]]
            df_blueme_sem_parc["ID_Conta_Bancaria"] = df_blueme_sem_parc["ID_Conta_Bancaria"].astype("Int64")
            df_blueme_sem_parc["ID_Extrato_Bancario"] = df_blueme_sem_parc["ID_Extrato_Bancario"].astype("Int64")
            df_blueme_sem_parc = df_blueme_sem_parc.rename(
                columns={"Data_Transacao": "Data_Transacao_Extrato",
                        "Descricao_Transacao": "Descricao_Transacao_Extrato"
                })

            # Estiliza a exibe
            df_blueme_sem_parc = df_blueme_sem_parc.sort_values(by="Realizacao_Pgto", ascending=False)
            df_blueme_sem_parc_styled = df_blueme_sem_parc.style.apply(colorir_linhas(df_blueme_sem_parc, 'ID_Despesa', 'Status_Conf_Document', 'Status_Aprov_Diret', 'despesa'), axis=1)
            st.dataframe(df_blueme_sem_parc_styled, use_container_width=True, hide_index=True)
            exibir_legenda("contas")
            st.write("")

            col1, col2 = st.columns([6, 1], vertical_alignment="center")
            with col2:
                button_download(df_blueme_sem_parc, 'ID_Extrato_Bancario', f"Blueme Sem Parc - Extrato", key=f'download_{item}_{conta}')
            st.divider()

        elif item == "blueme com parcelamento":
            if nome_conta == "Bar Brahma - Tutum Matriz - Kamino":
                st.warning('Observação: Valores de Mão de Obra')

            # filtra as despesas dessas contas
            df_blueme_com_parc_conta = df_custos_blueme_com_parc[df_custos_blueme_com_parc['Conta_Bancaria'] == nome_conta]
            df_blueme_com_parc_conta.loc[:, 'Realiz_Parcela'] = df_blueme_com_parc_conta['Realiz_Parcela'].dt.date

            if id_casa == 145:
                df_blueme_com_parc = merge_com_fuzzy(
                df_blueme_com_parc_conta,
                df_extratos_conta,
                left_on=['Realiz_Parcela', 'Valor_Parcela'],
                right_on=['Data_Transacao', 'Valor'],
                principal='despesa',
                text_left='Fornecedor',
                text_right='Descricao_Transacao',
                exceptions=exceptions, 
                limiar=60      
                )
                df_blueme_com_parc = df_blueme_com_parc.rename(columns={"ID_Conta_Bancaria_despesa": "ID_Conta_Bancaria"})

            else:
                df_blueme_com_parc = merge_com_fuzzy(
                df_blueme_com_parc_conta,
                df_extratos_conta,
                left_on=['Realiz_Parcela', 'Valor_Parcela'],
                right_on=['Data_Transacao', 'Valor'],
                principal='despesa',
                text_left='Fornecedor',
                text_right='Descricao_Transacao',
                exceptions=exceptions, 
                limiar=40      
                )

            # Seleciona só colunas mais importantes e reordena
            if "ID_Conta_Bancaria_despesa" in df_blueme_com_parc.columns:
                df_blueme_com_parc = df_blueme_com_parc.rename(columns={"ID_Conta_Bancaria_despesa": "ID_Conta_Bancaria"})
            df_blueme_com_parc = df_blueme_com_parc[["ID_Parcela", "ID_Despesa", "ID_Extrato_Bancario", "ID_Conta_Bancaria", "Conta_Bancaria", "Fornecedor", "Qtd_Parcelas", "Num_Parcela", "Valor_Parcela", "Realiz_Parcela", "Forma_Pagamento", "Doc_NF", "Class_Cont_1", "Class_Cont_2", "Status_Conf_Document", "Status_Aprov_Diret", "Status_Aprov_Caixa", "Data_Transacao", "Descricao_Transacao"]]
            df_blueme_com_parc["ID_Conta_Bancaria"] = df_blueme_com_parc["ID_Conta_Bancaria"].astype("Int64")
            df_blueme_com_parc["ID_Extrato_Bancario"] = df_blueme_com_parc["ID_Extrato_Bancario"].astype("Int64")
            df_blueme_com_parc = df_blueme_com_parc.rename(
                columns={"Data_Transacao": "Data_Transacao_Extrato",
                        "Descricao_Transacao": "Descricao_Transacao_Extrato"
                })

            # Estiliza a exibe
            df_blueme_com_parc = df_blueme_com_parc.sort_values(by="Realiz_Parcela", ascending=False)
            df_blueme_com_parc_styled = df_blueme_com_parc.style.apply(colorir_linhas(df_blueme_com_parc, 'ID_Parcela', 'Status_Conf_Document', 'Status_Aprov_Diret', 'despesa'), axis=1)
            st.dataframe(df_blueme_com_parc_styled, use_container_width=True, hide_index=True)
            exibir_legenda("contas")
            st.write("")

            col1, col2 = st.columns([6, 1], vertical_alignment="center")
            with col2:
                button_download(df_blueme_com_parc, 'ID_Extrato_Bancario', f"Blueme Com Parc - Extrato", key=f'download_{item}_{conta}')
            st.divider()

        elif item == "bloqueios":
            # filtra as despesas dessas contas
            df_bloqueios_conta = df_bloqueios[(df_bloqueios['Nome da Conta'] == nome_conta)]  
            df_bloqueios_conta = df_bloqueios_conta.rename(columns={"Data_Transacao": "Data_Bloqueio"})
            df_bloqueios_conta.loc[:, 'Data_Bloqueio'] = df_bloqueios_conta['Data_Bloqueio'].dt.date
            df_bloqueios_conta.loc[:, 'Valor'] = df_bloqueios_conta['Valor'] * (-1)

            # faz o merge para tentar conciliar
            df_bloqueios_conta = merge_com_fuzzy(
            df_bloqueios_conta,
            df_extratos_conta,
            left_on=['Data_Bloqueio', 'Valor'], 
            right_on=['Data_Transacao', 'Valor'],
            principal='despesa',
            text_left='Observacao',
            text_right='Descricao_Transacao',
            exceptions=exceptions, 
            limiar=20   
            )
            
            # Seleciona só colunas mais importantes e reordena
            if "ID_Conta_Bancaria_despesa" in df_bloqueios_conta.columns:
                df_bloqueios_conta = df_bloqueios_conta.rename(columns={"ID_Conta_Bancaria_despesa": "ID_Conta_Bancaria"})
            df_bloqueios_conta = df_bloqueios_conta[["ID_Bloqueio", "ID_Extrato_Bancario", "ID_Conta_Bancaria", "Nome da Conta", "Valor", "Data_Bloqueio", "Observacao", "Data_Transacao", "Descricao_Transacao"]]
            df_bloqueios_conta["ID_Conta_Bancaria"] = df_bloqueios_conta["ID_Conta_Bancaria"].astype("Int64")
            df_bloqueios_conta["ID_Extrato_Bancario"] = df_bloqueios_conta["ID_Extrato_Bancario"].astype("Int64")
            df_bloqueios_conta = df_bloqueios_conta.rename(
                columns={"Data_Transacao": "Data_Transacao_Extrato",
                        "Descricao_Transacao": "Descricao_Transacao_Extrato"
                })

            # Estiliza e exibe
            df_bloqueios_conta = df_bloqueios_conta.sort_values(by="Data_Bloqueio", ascending=False)
            df_bloqueios_conta_styled = df_bloqueios_conta.style.apply(colorir_linhas(df_bloqueios_conta, 'ID_Bloqueio', 'Status_Conf_Document', 'Status_Aprov_Diret', 'despesa'), axis=1)
            st.dataframe(df_bloqueios_conta_styled, use_container_width=True, hide_index=True)
            exibir_legenda("contas")
            st.write("")

            col1, col2 = st.columns([6, 1], vertical_alignment="center")
            with col2:
                button_download(df_bloqueios_conta, 'ID_Extrato_Bancario', f"Bloqueios Judicias - Extrato", key=f'download_{item}_{conta}')
            st.divider()

        elif item == "saidas mutuos":
            # filtra pela conta de saida
            df_saidas_mutuos_conta = df_saidas_mutuos[(df_saidas_mutuos['Conta_Saida'] == nome_conta)]                
            df_saidas_mutuos_conta.loc[:, 'Data_Mutuo'] = pd.to_datetime(df_saidas_mutuos_conta['Data_Mutuo'])

            # faz o merge para tentar conciliar
            df_saidas_mutuos_conta = merge_com_fuzzy(
            df_saidas_mutuos_conta,
            df_extratos_conta,
            left_on=['Data_Mutuo', 'Valor'], 
            right_on=['Data_Transacao', 'Valor'],
            principal='despesa',
            text_left='Observacoes',
            text_right='Descricao_Transacao',
            exceptions=exceptions,  
            limiar=16  
            )
            
            # Seleciona só colunas mais importantes e reordena
            df_saidas_mutuos_conta = df_saidas_mutuos_conta[["Mutuo_ID", "ID_Extrato_Bancario", "Data_Mutuo", "Valor", "ID_Conta_Saida", "Conta_Saida", "Casa_Entrada", "ID_Conta_Entrada", "Conta_Entrada", "Observacoes", "Data_Transacao", "Descricao_Transacao"]]
            df_saidas_mutuos_conta["Mutuo_ID"] = df_saidas_mutuos_conta["Mutuo_ID"].astype("Int64")
            df_saidas_mutuos_conta["ID_Conta_Saida"] = df_saidas_mutuos_conta["ID_Conta_Saida"].astype("Int64")
            df_saidas_mutuos_conta["ID_Conta_Entrada"] = df_saidas_mutuos_conta["ID_Conta_Entrada"].astype("Int64")
            df_saidas_mutuos_conta["ID_Extrato_Bancario"] = df_saidas_mutuos_conta["ID_Extrato_Bancario"].astype("Int64")
            df_saidas_mutuos_conta = df_saidas_mutuos_conta.rename(
                columns={"Data_Transacao": "Data_Transacao_Extrato",
                        "Descricao_Transacao": "Descricao_Transacao_Extrato"
                })

            # Estiliza e exibe
            df_saidas_mutuos_conta = df_saidas_mutuos_conta.sort_values(by="Data_Mutuo", ascending=False)
            df_saidas_mutuos_conta_styled = df_saidas_mutuos_conta.style.apply(colorir_linhas(df_saidas_mutuos_conta, 'Mutuo_ID', 'Status_Conf_Document', 'Status_Aprov_Diret', 'despesa'), axis=1)
            st.dataframe(df_saidas_mutuos_conta_styled, use_container_width=True, hide_index=True)
            exibir_legenda("contas")

            st.write("")
            col1, col2 = st.columns([6, 1], vertical_alignment="center")
            with col2:
                button_download(df_saidas_mutuos_conta, 'ID_Extrato_Bancario', f"Saidas Mutuos - Extrato", key=f'download_{item}_{conta}')
            st.divider()

        elif item == "extrato bancario":
            # df_extratos_conta = df_extratos_conta.reset_index(drop=True)
            # st.write(df_extratos_conta)
            
            # Blueme sem parc: filtra e organiza colunas
            df_custos_blueme_sem_parc_filtrado = df_custos_blueme_sem_parc[df_custos_blueme_sem_parc['Conta_Bancaria'] == nome_conta]
            df_custos_blueme_sem_parc_filtrado = df_custos_blueme_sem_parc_filtrado[["ID_Conta_Bancaria", "ID_Despesa", "Valor", "Realizacao_Pgto", "Fornecedor"]]
            df_custos_blueme_sem_parc_filtrado['Categoria_Despesa'] = "Despesa Blueme Sem Parcelamento"
            df_custos_blueme_sem_parc_filtrado = df_custos_blueme_sem_parc_filtrado.rename(columns={
                "ID_Conta_Bancaria": "ID_Conta_Despesa",
                "Fornecedor": "Descricao_Despesa"
            })

            # Blueme com parc: filtra e organiza colunas
            df_custos_blueme_com_parc_filtrado = df_custos_blueme_com_parc[df_custos_blueme_com_parc['Conta_Bancaria'] == nome_conta]
            df_custos_blueme_com_parc_filtrado = df_custos_blueme_com_parc_filtrado[["ID_Conta_Bancaria", "ID_Parcela", "Valor_Parcela", "Realiz_Parcela", "Fornecedor"]]
            df_custos_blueme_com_parc_filtrado['Categoria_Despesa'] = "Despesa Blueme Com Parcelamento"
            df_custos_blueme_com_parc_filtrado = df_custos_blueme_com_parc_filtrado.rename(columns={
                "ID_Conta_Bancaria": "ID_Conta_Despesa",
                "ID_Parcela": "ID_Despesa",
                "Valor_Parcela": "Valor",
                "Realiz_Parcela": "Realizacao_Pgto",
                "Fornecedor": "Descricao_Despesa"
            })

            # Bloqueios: filtra e organiza colunas
            df_bloqueios_filtrado = df_bloqueios[df_bloqueios['Nome da Conta'] == nome_conta]
            df_bloqueios_filtrado.loc[:, 'Valor'] = df_bloqueios_filtrado['Valor'] * (-1)
            df_bloqueios_filtrado = df_bloqueios_filtrado[["ID_Conta_Bancaria", "ID_Bloqueio", "Valor", "Data_Transacao", "Observacao"]]
            df_bloqueios_filtrado['Categoria_Despesa'] = "Bloqueio Judicial"
            df_bloqueios_filtrado = df_bloqueios_filtrado.rename(columns={
                "ID_Conta_Bancaria": "ID_Conta_Despesa",
                "ID_Bloqueio": "ID_Despesa",
                "Data_Transacao": "Realizacao_Pgto",
                "Observacao": "Descricao_Despesa"
            })

            # Saídas Mutuos: filtra e organiza colunas
            df_saidas_mutuos_filtrado = df_saidas_mutuos[(df_saidas_mutuos['ID_Casa_Saida'] == id_casa) | (df_saidas_mutuos['Conta_Saida'] == nome_conta)]
            df_saidas_mutuos_filtrado = df_saidas_mutuos_filtrado[["ID_Conta_Saida", "Mutuo_ID", "Valor", "Data_Mutuo", "Observacoes"]]
            df_saidas_mutuos_filtrado['Categoria_Despesa'] = "Saída Mútuo"
            df_saidas_mutuos_filtrado = df_saidas_mutuos_filtrado.rename(columns={
                "ID_Conta_Saida": "ID_Conta_Despesa",
                "Mutuo_ID": "ID_Despesa",
                "Data_Mutuo": "Realizacao_Pgto",
                "Observacoes": "Descricao_Despesa"
            })

            df_concat = pd.concat(
                [df_custos_blueme_sem_parc_filtrado, df_custos_blueme_com_parc_filtrado, df_bloqueios_filtrado, df_saidas_mutuos_filtrado], 
                axis=0, 
                ignore_index=True)
            
            # df_concat = df_concat.reset_index(drop=True)
            # st.write(df_concat)

            # Garante que ambos estão no mesmo formato (datetime)
            df_extratos_conta.loc[:, 'Data_Transacao'] = pd.to_datetime(df_extratos_conta['Data_Transacao'], errors='coerce')
            df_concat['Realizacao_Pgto'] = pd.to_datetime(df_concat['Realizacao_Pgto'], errors='coerce')
        
            # Df com o merge de cada item do extrato com despesa correspondente
            df_concat_merge = merge_com_fuzzy(
            df_extratos_conta,
            df_concat,
            left_on=['Data_Transacao', 'Valor'],
            right_on=['Realizacao_Pgto', 'Valor'], 
            principal='extrato',
            text_left='Descricao_Transacao',
            text_right='Descricao_Despesa',
            exceptions=exceptions,  
            limiar=7
            )

            # Estiliza e exibe
            df_concat_merge = df_concat_merge.reset_index(drop=True)
            df_concat_merge = df_concat_merge[["ID_Extrato_Bancario", "ID_Despesa",  "Categoria_Despesa", "ID_Conta_Bancaria", "Nome_Conta_Bancaria", "Data_Transacao", "Descricao_Transacao", "Valor", "Realizacao_Pgto", "Descricao_Despesa"]]
            df_concat_merge["ID_Despesa"] = df_concat_merge["ID_Despesa"].astype("Int64")
            df_concat_merge = df_concat_merge.rename(
                columns={"Data_Transacao": "Data_Transacao_Extrato",
                        "Descricao_Transacao": "Descricao_Transacao_Extrato"
                })
            
            df_concat_merge = df_concat_merge.sort_values(by="Data_Transacao_Extrato", ascending=False)
            df_concat_merge_styled = df_concat_merge.style.apply(colorir_linhas(df_concat_merge, 'ID_Despesa', 'Status_Conf_Document', 'Status_Aprov_Diret', 'extrato'), axis=1)
            st.dataframe(df_concat_merge_styled, use_container_width=True, hide_index=True)
            exibir_legenda("extrato")
            
            st.write("")
            col1, col2 = st.columns([6, 1], vertical_alignment="center")
            with col2:
                button_download(df_concat_merge, 'ID_Despesa', f"Extrato - Despesas", key=f'download_{item}_{conta}')


# Cria uma tab para cada conta bancária da casa: chamada em 'conciliacao_inicial' para Contas a Pagar e Contas a Receber
def cria_tabs_contas(df_contas, id_casa, df_custos_blueme_sem_parc, df_custos_blueme_sem_parc_formatada, df_custos_blueme_com_parc, df_custos_blueme_com_parc_formatada, df_mutuos, df_mutuos_formatada, df_bloqueios, df_extratos_bancarios, df_extratos_bancarios_formatada):
    # Mapeamento nome → ID
    mapeamento_contas = dict(zip(df_contas["Nome da Conta"], df_contas["ID_Conta"]))

    # Lista de IDs que terão tabs individuais em cada casa
    ids_exclusivos_por_casa = {                      
        122: [113, 183],       
        114: [103, 130, 137],                        
        148: [148, 153, 164, 187],  
        173: [188, 190],                                             
        116: [140, 151],                           
        110: [117, 181],
        131: [116],                          
        129: [109],                            
        127: [104, 176],             
        156: [145, 155, 168],    
        160: [154],    
        105: [105, 150, 160, 165],                         
        128: [115, 182],   
        104: [127, 138, 107, 110, 169],                         
        149: [132, 133, 134, 149],   
        115: [126, 139, 170, 186],
        142: [146],
        143: [111, 129],
        145: [124, 184, 185]                                              
    }

    # pega os exclusivos da casa atual (se existir)
    ids_exclusivos = ids_exclusivos_por_casa.get(id_casa, [])

    lista_tabs = []
    lista_ids = []

    # Junta listas de várias bases
    lista_contas = (
        df_extratos_bancarios['Nome_Conta_Bancaria'].tolist()
        + df_custos_blueme_sem_parc['Conta_Bancaria'].tolist()
        + df_custos_blueme_com_parc['Conta_Bancaria'].tolist()
        + df_bloqueios['Nome da Conta'].tolist()
    )
    lista_contas = list(set(lista_contas))

    # cria tabs individuais só para os exclusivos
    for conta in lista_contas:
        # trata nulos como "Outras contas"
        if pd.isna(conta) or conta is None:
            if "Outras contas" not in lista_tabs:
                lista_tabs.append("Outras contas")
                lista_ids.append("OUTRAS")
            continue 

        # pega o ID da conta de forma segura
        id_conta = mapeamento_contas.get(conta)

        if id_conta is None:
            # se não encontrar, joga pra "Outras contas"
            if "Outras contas" not in lista_tabs:
                lista_tabs.append("Outras contas")
                lista_ids.append("OUTRAS")
            continue

        if id_conta in ids_exclusivos:
            lista_tabs.append(conta)
            lista_ids.append(id_conta)
        else:
            if "Outras contas" not in lista_tabs:
                lista_tabs.append("Outras contas")
                lista_ids.append("OUTRAS")
        
    if lista_tabs:
        # garante que "Todas as contas" venha primeiro
        lista_tabs = ["Todas as contas"] + lista_tabs
        lista_ids = ["TODAS"] + lista_ids

        # garante que "Outras contas" fique por último
        if "Outras contas" in lista_tabs:
            idx = lista_tabs.index("Outras contas")
            lista_tabs.append(lista_tabs.pop(idx))
            lista_ids.append(lista_ids.pop(idx))
        
        # cria as tabs para cada conta
        tabs = st.tabs(lista_tabs)

        for tab, conta_fmt in enumerate(lista_tabs):
            with tabs[tab]:
                if conta_fmt == "Todas as contas":
                    exibe_tabelas_contas_a_pagar(
                        id_casa, 
                        df_custos_blueme_sem_parc_formatada, 
                        df_custos_blueme_com_parc_formatada, 
                        df_mutuos_formatada, 
                        df_bloqueios, 
                        df_extratos_bancarios_formatada)

                # Contas que não estão entre as principais da casa (tesouraria, petty cash, sem conta)
                elif conta_fmt == "Outras contas":
                    st.write("Despesas petty cash, tesouraria, sem conta registrada, etc")

                    # pega os IDs que não são exclusivos
                    ids_outras = [
                            id_conta
                            for nome, id_conta in mapeamento_contas.items()
                            if id_conta not in ids_exclusivos
                        ]

                    # Despesas blueme sem parcelamento #
                    st.subheader('Correspondência: Despesas BlueMe Sem Parcelamento -> Extrato')
                    itens_por_conta(
                        id_casa,
                        ids_outras, 
                        df_custos_blueme_sem_parc, 
                        df_custos_blueme_com_parc, 
                        df_bloqueios,
                        df_mutuos,
                        df_extratos_bancarios, 
                        conta_fmt, 
                        "blueme sem parcelamento outras")

                    # Despesas blueme com parcelamento #
                    st.subheader('Correspondência: Despesas BlueMe Com Parcelamento -> Extrato')
                    itens_por_conta(
                        id_casa,
                        ids_outras, 
                        df_custos_blueme_sem_parc, 
                        df_custos_blueme_com_parc, 
                        df_bloqueios,
                        df_mutuos,
                        df_extratos_bancarios, 
                        conta_fmt, 
                        "blueme com parcelamento outras")
                    
                    # Saídas Mútuos #
                    st.subheader('Correspondência: Saídas Mútuos -> Extrato')
                    itens_por_conta(
                        id_casa,
                        ids_outras,
                        df_custos_blueme_sem_parc, 
                        df_custos_blueme_com_parc,
                        df_bloqueios, 
                        df_mutuos,
                        df_extratos_bancarios, 
                        conta_fmt, 
                        "saidas mutuos outras")

                else:
                    # Despesas blueme sem parcelamento #
                    st.subheader('Correspondência: Despesas BlueMe Sem Parcelamento -> Extrato')
                    itens_por_conta(
                        id_casa,
                        None,  
                        df_custos_blueme_sem_parc, 
                        df_custos_blueme_com_parc,
                        df_bloqueios,
                        df_mutuos,
                        df_extratos_bancarios, 
                        conta_fmt, 
                        "blueme sem parcelamento"
                    )

                    # Despesas blueme com parcelamento #
                    st.subheader('Correspondência: Despesas BlueMe Com Parcelamento -> Extrato')
                    itens_por_conta(
                        id_casa,
                        None, 
                        df_custos_blueme_sem_parc,
                        df_custos_blueme_com_parc, 
                        df_bloqueios,
                        df_mutuos,
                        df_extratos_bancarios, 
                        conta_fmt, 
                        "blueme com parcelamento"
                    )

                    # Bloqueos Judiciais #
                    st.subheader('Correspondência: Bloqueios Judiciais -> Extrato')
                    itens_por_conta(
                        id_casa,
                        None,
                        df_custos_blueme_sem_parc, 
                        df_custos_blueme_com_parc,
                        df_bloqueios, 
                        df_mutuos,
                        df_extratos_bancarios, 
                        conta_fmt, 
                        "bloqueios")
                    
                    # Saídas Mútuos #
                    st.subheader('Correspondência: Saídas Mútuos -> Extrato')
                    itens_por_conta(
                        id_casa,
                        None,
                        df_custos_blueme_sem_parc, 
                        df_custos_blueme_com_parc,
                        df_bloqueios, 
                        df_mutuos,
                        df_extratos_bancarios, 
                        conta_fmt, 
                        "saidas mutuos")
                    
                    # Extrato Bancário #
                    st.subheader("Correspondência: Extrato -> Despesa")
                    itens_por_conta(
                        id_casa,
                        None,
                        df_custos_blueme_sem_parc, 
                        df_custos_blueme_com_parc,
                        df_bloqueios, 
                        df_mutuos,
                        df_extratos_bancarios, 
                        conta_fmt, 
                        "extrato bancario")

    else: 
        st.warning('Nada para exibir')


# Exibe itens do CONTAS A PAGAR em TODAS AS CONTAS
def exibe_tabelas_contas_a_pagar(id_casa, df_custos_blueme_sem_parcelam_formatada, df_custos_blueme_com_parcelam_formatada, df_mutuos_formatada, df_bloqueios_judiciais_filtrada, df_extratos_bancarios_formatada):
    st.subheader("Despesas BlueMe Sem Parcelamento - Todas as contas")
    st.dataframe(df_custos_blueme_sem_parcelam_formatada, use_container_width=True, hide_index=True)
    st.divider()

    st.subheader("Despesas BlueMe Com Parcelamento - Todas as contas")
    st.dataframe(df_custos_blueme_com_parcelam_formatada, use_container_width=True, hide_index=True)
    st.divider()

    st.subheader("Saídas Mútuos - Todas as contas")
    df_mutuos_formatada = df_mutuos_formatada[df_mutuos_formatada['ID_Casa_Saida'] == id_casa]
    st.dataframe(df_mutuos_formatada, use_container_width=True, hide_index=True)
    st.divider()

    st.subheader("Bloqueios Judiciais - Todas as contas")
    df_bloqueios_judiciais_filtrada = df_bloqueios_judiciais_filtrada[df_bloqueios_judiciais_filtrada['Valor'] < 0]
    df_bloqueios_judiciais_formatada = formata_df(df_bloqueios_judiciais_filtrada)
    st.dataframe(df_bloqueios_judiciais_formatada, use_container_width=True, hide_index=True)
    st.divider()

    st.subheader("Extratos Bancários (Débito) - Todas as contas")
    df_extratos_bancarios_formatada = df_extratos_bancarios_formatada[df_extratos_bancarios_formatada['Tipo_Credito_Debito'] == 'DEBITO']
    st.dataframe(df_extratos_bancarios_formatada, use_container_width=True, hide_index=True)
    st.divider()


