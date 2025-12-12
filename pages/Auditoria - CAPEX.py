import streamlit as st
import pandas as pd
from utils.functions.general_functions import config_sidebar
from utils.functions.general_functions_conciliacao import calcular_datas, format_brazilian, formata_df
from utils.queries_conciliacao import GET_CASAS
from utils.queries_capex import *


st.set_page_config(
    page_title="CAPEX",
    page_icon=":material/receipt_long:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/receipt_long: CAPEX")
st.divider()

# Recupera dados
datas = calcular_datas()
df_casas = GET_CASAS()
df_projetos = GET_PROJETOS_CAPEX()
df_orcamentos = GET_ORCAMENTOS_CAPEX()
df_despesas_capex = GET_DESPESAS_CAPEX()

# Seletor de casa
casas = df_casas['Casa'].tolist()

# Troca o valor na lista
casas = [c for c in casas if c not in ['All bar', 'Sanduiche comunicação LTDA ', 'Tempus Fugit  Ltda ', 'Blue Note SP (Novo)']]
casa = st.selectbox("Selecione uma casa:", casas)
st.divider()

# Recupera id da casa
mapeamento_casas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))
id_casa = mapeamento_casas[casa]

# Seleciona projeto da casa
df_projetos_casa = df_projetos[df_projetos['ID Casa'] == id_casa]
lista_projetos_casa = df_projetos_casa['Nome Projeto'].tolist()

if lista_projetos_casa:
    st.write(f'Selecione um projeto do {casa} para mais informações:')
    projeto_selecionado = st.selectbox(
        f"Selecione um projeto do {casa}:",
        lista_projetos_casa,
        label_visibility='collapsed'
    )

    # Recupera id do projeto
    mapeamento_projetos = dict(zip(df_projetos_casa["Nome Projeto"], df_projetos_casa["ID Projeto"]))
    id_projeto = mapeamento_projetos[projeto_selecionado]
    df_orcamentos_projeto = df_orcamentos[df_orcamentos['ID Projeto'] == id_projeto]
    
    # Exibe orçamentos do projeto selecionado
    if not df_orcamentos_projeto.empty:
        st.subheader('Orçamentos do projeto')
        df_orcamentos_projeto_exibe = df_orcamentos_projeto[['ID Orçamento', 'Classificação Contabil 2', 'Data Prevista', 'Valor Estimado', 'Descrição Resumida', 'Descrição Detalhada']]
        df_orcamentos_projeto_exibe = df_orcamentos_projeto_exibe.sort_values(by=['Data Prevista'])
        df_orcamentos_projeto_exibe = formata_df(df_orcamentos_projeto_exibe)
        st.dataframe(df_orcamentos_projeto_exibe, hide_index=True, width='stretch')
        
        total_orcamento = df_orcamentos_projeto['Valor Estimado'].sum()
        st.write(f'**Total:** {format_brazilian(total_orcamento)}')
        st.divider()

        # Exibe despesas do projeto selecionado
        st.subheader('Despesas gerais do projeto')
        df_despesas_projeto = df_despesas_capex[df_despesas_capex['ID Projeto'] == id_projeto]
        df_despesas_projeto_exibe = df_despesas_projeto[
                ['ID Despesa', 'ID Fornecedor', 'Fornecedor', 'Class. Cont. Despesa', 'ID Orçamento', 'Class. Cont. Orçamento', 'Descrição Orçamento', 
                 'Valor Original', 'Valor Liquido', 'Data Lançamento', 'Data Competência', 'Data Vencimento', 
                 'Status Aprov Diretoria', 'Status Aprov Document', 'Status Pgto', 'Data Pgto'
                ]]
        
        df_despesas_projeto_exibe = df_despesas_projeto_exibe.sort_values(by=['Class. Cont. Orçamento', 'Descrição Orçamento'])
        df_despesas_projeto_exibe = formata_df(df_despesas_projeto_exibe)
        st.dataframe(df_despesas_projeto_exibe, hide_index=True, width='stretch')
        
        total_despesas = df_despesas_projeto['Valor Original'].sum()
        st.write(f'**Total:** {format_brazilian(total_despesas)}')

        if total_despesas > total_orcamento:
            diferenca = total_despesas - total_orcamento
            st.markdown(f'''
                  <p style="color: red;">O total de despesas lançadas está R$ {format_brazilian(diferenca)} acima do orçado</p>  
            ''', unsafe_allow_html=True)
        st.divider()

        # Cria lista com as class. cont. 
        st.subheader(':material/arrow_downward: Visualizar despesas por Classificação Contábil 2')
        lista_class_cont_despesas = df_despesas_projeto['Class. Cont. Orçamento'].unique().tolist()
        class_cont_selecionada = st.selectbox(
            f"Selecione uma class. cont. 2:",
            lista_class_cont_despesas,
            index=None,
            placeholder='Selecione uma Class. Cont. Orçamento',
            label_visibility='collapsed'
        )
        
        # Exibe as despesas da class. cont. selecionada do projeto
        if class_cont_selecionada is not None:
            df_despesas_projeto_class_cont = df_despesas_projeto[df_despesas_capex['Class. Cont. Orçamento'] == class_cont_selecionada]
        
            if not df_despesas_projeto_class_cont.empty:
                df_despesas_projeto_class_cont_exibe = df_despesas_projeto_class_cont[
                    ['ID Despesa', 'ID Fornecedor', 'Fornecedor', 'ID Orçamento', 'Descrição Orçamento', 'Valor Original', 'Valor Liquido', 
                    'Data Lançamento', 'Data Competência', 'Data Vencimento', 'Status Aprov Diretoria', 'Status Aprov Document', 
                    'Status Pgto', 'Data Pgto']]
                
                # st.subheader('Despesas')
                df_despesas_capex_class_cont_exibe = formata_df(df_despesas_projeto_class_cont_exibe)
                st.dataframe(df_despesas_capex_class_cont_exibe, hide_index=True, width='stretch')

                # Cria df com resumo das informações de cada descrição da class. cont escolhida
                lista_descricao_despesas = df_despesas_projeto_class_cont['Descrição Orçamento'].unique().tolist()
                df_infos_descricoes = pd.DataFrame({'Descrição': lista_descricao_despesas})

                # Une com o de orçamentos para comparar orçamento vc despesas
                df_orcamentos_class_cont = df_orcamentos_projeto[df_orcamentos_projeto['Classificação Contabil 2'] ==  class_cont_selecionada]
                df_merge = pd.merge(
                    df_orcamentos_class_cont[['Valor Estimado', 'Descrição Resumida']],
                    df_infos_descricoes,
                    left_on=['Descrição Resumida'],
                    right_on=['Descrição'],
                    how='left'
                )
                
                st.divider()
                st.subheader('Resumo por descrição')

                for descricao in lista_descricao_despesas:
                    orcamento_descricao = df_merge[df_merge['Descrição Resumida'] ==  descricao]
                    valor_orcado = orcamento_descricao['Valor Estimado'].iloc[0] # Orçamento estimado para a descrição

                    df_despesas_descricao = df_despesas_projeto_class_cont[df_despesas_projeto_class_cont['Descrição Orçamento'] == descricao]
                    contagem_descricao = df_despesas_descricao['Descrição Orçamento'].count() # Contagem de despesas lançadas por descrição
                    total_despesas = df_despesas_descricao['Valor Original'].sum() # Soma valor total de despesas lançadas por descrição

                    df_despesas_pagas_descricao = df_despesas_descricao[df_despesas_descricao['Status Pgto'] == 'Pago']
                    contagem_pagas = df_despesas_pagas_descricao['Status Pgto'].count() # Contagem de despesas pagas por descrição
                    total_pagas = df_despesas_pagas_descricao['Valor Original'].sum() # Soma valor total de despesas pagas por descrição

                    cond = df_merge['Descrição'] == descricao
                    df_merge.loc[cond, 'Contagem Despesas'] = contagem_descricao
                    df_merge.loc[cond, 'Valor Total Despesas'] = total_despesas
                    df_merge.loc[cond, 'Contagem Pagas'] = contagem_pagas
                    df_merge.loc[cond, 'Valor Total Pagas'] = total_pagas

                    # Cria os alertas apenas se necessário
                    alerta_diferenca_lancado = '<p></p>'
                    if total_despesas > valor_orcado:
                        diferenca_lancado = total_despesas - valor_orcado
                        alerta_diferenca_lancado = f'<p style="margin:0; color:red;">O total lançado está R$ {format_brazilian(diferenca_lancado)} acima do orçado</p>'
                    
                    alerta_diferenca_pago = '<p></p>'
                    if total_pagas > valor_orcado:
                        diferenca_pago = total_pagas - valor_orcado
                        alerta_diferenca_pago = f'<p style="margin:0; color:red;">O total pago está R$ {format_brazilian(diferenca_pago)} acima do orçado</p>'

                    st.markdown(f"""
                        <h5 style="margin-top:20px;"><b>• {descricao}</b></h5>
                        <p style="margin-bottom:8px;"><b>Valor Orçado:</b> {format_brazilian(valor_orcado)}</p>
                        <div style="display: flex; flex-direction: row; background-color:#f7f7f7; gap: 6em; padding: 15px; border-radius:10px;">
                            <div>
                                <h5 style="margin-bottom:8px;">Despesas Lançadas</h5>
                                <p style="margin:0;"><b>Quantidade:</b> {contagem_descricao}</p>
                                <p style="margin:0;"><b>Total lançado:</b> R$ {format_brazilian(total_despesas)}</p>
                                {alerta_diferenca_lancado}
                            </div>
                            <div>
                                <h5 style="margin-bottom:8px;">Despesas Pagas</h5>
                                <p style="margin:0;"><b>Quantidade:</b> {contagem_pagas}</p>
                                <p style="margin:0;"><b>Total pago:</b> R$ {format_brazilian(total_pagas)}</p>
                                {alerta_diferenca_pago}
                            </div>
                        </div>
                        <hr style="margin-top:30px; margin-bottom:10px;">
                    """, unsafe_allow_html=True)

            else: # Class. cont. sem despesas lançadas
                st.info('Não há despesas lançadas!')

    else: # Projeto não tem orçamentos lançados
        st.info('Não há orçamentos lançados para este projeto!')
         
else: # Casa não tem projetos lançados
    st.info(f'{casa} não tem projetos lançados!')

