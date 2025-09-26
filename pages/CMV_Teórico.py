import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.user import *
from utils.functions.cmv_teorico import *
from utils.queries_cmv import *

st.set_page_config(
    page_icon=":material/rubric:",
    page_title="CMV Teórico",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
    st.switch_page('Login.py')
    

def main():
    # Sidebar
    config_sidebar()
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title(":material/rubric: CMV Teórico")
    with col2:
        st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
    with col3:
        if st.button('Logout', key='logout'):
            logout()
    st.divider()

    # Seletores
    col_casa, col_mes, col_ano = st.columns([1, 1, 1])
    with col_casa:
        lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Todas as Casas']
        id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, 'selecao_casa')
    with col_mes:
        #periodo = input_periodo_datas(key='data_inicio')
        nome_mes, mes = seletor_mes_produtos('mes', 'Mês de Referência de Compra de Insumos', 'Base de cálculo dos custos médios de insumos')
    with col_ano:
        ano = seletor_ano(2024, 2025, 'ano', 'Ano de Referência de Compra de Insumos', 'Base de cálculo dos custos médios de insumos')

    st.divider()

    # PREÇO DOS ITENS VENDIDOS
    # 1. Dados dos itens vendidos (A&B), sem considerar o desconto

    # FICHAS TÉCNICAS - Custo do item vendido
    # 2. Dados dos insumos de estoque das fichas técnicas (por casa)
        # Para cada insumo de estoque, calcular uma média de preços de compra e de estoque

    # 3. Dados dos insumos de produção das fichas técnicas (por casa)
        # Para cada insumo de produção, visualizar os insumos de estoque necessários para produzir o insumo de produção

    # 4. Chegar no Custo Unit. do Produto pelo custo dos insumos (estoque + produção)
    
    ### FICHAS TÉCNICAS - ITENS VENDIDOS PARA INSUMOS DE ESTOQUE E PRODUÇÃO
    # dataframe com as quantidades de insumos de estoque para cada ITEM VENDIDO
    df_fichas_itens_vendidos_insumos_estoque = GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_INSUMOS_ESTOQUE()
    # dataframe com as quantidades de insumos de produção para cada ITEM VENDIDO
    df_fichas_itens_vendidos_itens_producao = GET_FICHAS_TECNICAS_DE_ITENS_VENDIDOS_PARA_ITENS_PRODUCAO()
    
    # dataframe com as quantidades de insumos de produção e de estoque para cada VENDIDO
    df_fichas_itens_vendidos = pd.merge(df_fichas_itens_vendidos_insumos_estoque, df_fichas_itens_vendidos_itens_producao, how='outer')

    ### FICHAS TÉCNICAS - INSUMOS DE ESTOQUE
    df_precos_insumos = GET_PRECOS_INSUMOS_N5_COM_PROPORCAO_ESTOQUE()

    df_precos_insumos_de_estoque = df_precos_insumos.groupby(['ID Casa', 'ID Insumo Estoque', 'Mês Compra', 'Ano Compra']).agg({
        'Valor N5': 'sum',
        'Quantidade Insumo Estoque': 'sum',
        'Casa': 'first',
        'Insumo Estoque': 'first',
        'U.M. Insumo Estoque': 'first'
    }).reset_index()
    col_ordem = [
        'ID Casa', 'Casa', 'Mês Compra', 'Ano Compra',
        'ID Insumo Estoque', 'Insumo Estoque', 'U.M. Insumo Estoque',
        'Valor N5', 'Quantidade Insumo Estoque'
    ]
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[col_ordem]
    # Calcula o preço da unidade (preço de 1 unidade de medida) do insumo de estoque
    df_precos_insumos_de_estoque['Preço Médio Insumo Estoque'] = df_precos_insumos_de_estoque['Valor N5'] / df_precos_insumos_de_estoque['Quantidade Insumo Estoque']

    #### PAREI AQUI, FALTA SELECIONAR UM ÚNICO PREÇO PARA CADA INSUMO DE ESTOQUE

    # Remover NaN
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque.dropna(subset=['Preço Médio Insumo Estoque'])
    # Remover inf e -inf
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[
        ~np.isinf(df_precos_insumos_de_estoque['Preço Médio Insumo Estoque'])
    ]
    # Remover valores negativos
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[
        df_precos_insumos_de_estoque['Preço Médio Insumo Estoque'] > 0
    ]

    # Filtra por casa   
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[df_precos_insumos_de_estoque['ID Casa'] == id_casa]

    ### FICHAS TÉCNICAS - INSUMOS DE PRODUÇÃO
    # dataframe com as quantidades de insumos de estoque e de produção para cada ITEM DE PRODUÇÃO
    df_fichas_itens_producao = GET_FICHAS_TECNICAS_DE_INSUMOS_PRODUCAO()

    # Obtem os insumos de estoque para cada casa para calcular o preço posteriormente
    insumos_necessarios_estoque_casa = df_fichas_itens_vendidos_insumos_estoque.loc[
        df_fichas_itens_vendidos_insumos_estoque['ID Casa'] == id_casa,
        ['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque']
    ].drop_duplicates()

    insumos_necessarios_estoque_casa = pd.concat(
        [
            insumos_necessarios_estoque_casa,
            df_fichas_itens_producao.loc[
                df_fichas_itens_producao['ID Casa'] == id_casa,
                ['ID Casa', 'Casa', 'ID Insumo Estoque', 'Insumo Estoque']
            ].drop_duplicates()
        ],
        ignore_index=True
    ).drop_duplicates()

    df_precos_insumos_producao, df_precos_itens_producao_completo, df_precos_selecionados_estoque_mes_casa = calcular_precos_itens_producao_mes_casa(df_fichas_itens_producao, df_precos_insumos_de_estoque, insumos_necessarios_estoque_casa, id_casa, mes, ano)


    ### CUSTO ITENS VENDIDOS
    df_fichas_itens_vendidos = df_fichas_itens_vendidos[df_fichas_itens_vendidos['ID Casa'] == id_casa]
    df_precos_itens_vendidos, df_fichas_itens_vendidos, df_fichas_itens_vendidos_auditoria = calcular_custos_itens_vendidos(df_fichas_itens_vendidos, df_precos_selecionados_estoque_mes_casa, df_precos_itens_producao_completo, )

    # Ordena colunas
    df_precos_itens_vendidos = df_precos_itens_vendidos.sort_values(by=['Custo Item'], ascending=False)
    df_fichas_itens_vendidos = df_fichas_itens_vendidos.sort_values(by=['Item Vendido Zig', 'Custo Item'], ascending=False)
    df_precos_insumos_de_estoque = df_precos_insumos_de_estoque.sort_values(by=['Preço Médio Insumo Estoque'], ascending=False)
    df_precos_itens_producao_completo = df_precos_itens_producao_completo.sort_values(by=['Custo Item Produzido'], ascending=False)
    df_precos_insumos_producao = df_precos_insumos_producao.sort_values(by=['Custo Ficha'], ascending=False)

    df_precos_itens_vendidos_download = df_precos_itens_vendidos.copy()

    df_precos_insumos_producao = df_precos_insumos_producao.drop(columns={'Produção?'})
    df_precos_itens_vendidos = format_columns_brazilian(df_precos_itens_vendidos, ['Custo Item'])

    
    col1, col2 = st.columns([3, 1], vertical_alignment='center', gap='large')
    with col1:
        st.markdown(f'## CMV - Custo Itens Vendidos ({casa})')
    with col2:
        button_download(df_precos_itens_vendidos_download, f'custo_itens_{casa}', f'custo_itens_{casa}')
    st.dataframe(df_precos_itens_vendidos, use_container_width=True, hide_index=True)

    with st.container(border=True):
        col1, col2, col3 = st.columns([0.1, 3, 0.1], vertical_alignment='center', gap='large')
        with col2:
            # Filtro por prato
            df_lista_produtos = pd.DataFrame(df_precos_itens_vendidos['ID Item Zig'].unique())
            df_lista_produtos['ID - Produto'] = df_precos_itens_vendidos['ID Item Zig'].astype(str) + ' - ' + df_precos_itens_vendidos['Item Vendido Zig']
            lista_produtos = df_lista_produtos['ID - Produto'].unique().tolist()
            produto_selecionado = st.selectbox('Selecionar Produto', lista_produtos, key='selecionar_produto')
            id_produto_selecionado = int(float(produto_selecionado.split(' - ')[0]))


            #
            ordem_col = ['ID Casa', 'Casa', 'ID Item Zig', 'Item Vendido Zig', 'ID Ficha Técnica', 'ID Insumo', 'Insumo', 'Quantidade na Ficha', 'Unidade Medida', 'Custo Item']
            df_fichas_itens_vendidos = df_fichas_itens_vendidos[df_fichas_itens_vendidos['ID Item Zig'] == id_produto_selecionado]
            lista_ids_e_insumos_utilizados = df_fichas_itens_vendidos[['ID Insumo', 'Insumo']].to_dict('records')
            dict_ids_e_insumos_utilizados = {item["ID Insumo"]: item["Insumo"] for item in lista_ids_e_insumos_utilizados}

            df_precos_insumos_de_estoque = df_precos_insumos_de_estoque[df_precos_insumos_de_estoque.apply(lambda row: dict_ids_e_insumos_utilizados.get(row['ID Insumo Estoque']) == row['Insumo Estoque'], axis=1)]
            df_precos_itens_producao_completo = df_precos_itens_producao_completo[df_precos_itens_producao_completo.apply(lambda row: dict_ids_e_insumos_utilizados.get(row['ID Item Produzido']) == row['Item Produzido'], axis=1)]

            lista_fichas_itens_producao = df_precos_itens_producao_completo['ID Ficha Técnica Produção'].unique().tolist()
            df_precos_insumos_producao = df_precos_insumos_producao[df_precos_insumos_producao['ID Ficha Técnica Produção'].isin(lista_fichas_itens_producao)].sort_values(by=['ID Ficha Técnica Produção', 'Custo Ficha'], ascending=[True,False])

            # Guarda valores numéricos para download (antes da formatação)
            df_fichas_itens_vendidos_download = df_fichas_itens_vendidos.copy()
            df_fichas_insumos_de_estoque_download = df_precos_insumos_de_estoque.copy()
            df_precos_itens_producao_completo_download = df_precos_itens_producao_completo.copy()
            df_precos_insumos_producao_download = df_precos_insumos_producao.copy()
            
            # Formatação de colunas
            df_fichas_itens_vendidos = format_columns_brazilian(df_fichas_itens_vendidos, ['Custo Item'])
            df_precos_insumos_de_estoque = format_columns_brazilian(df_precos_insumos_de_estoque, ['Valor N5', 'Preço Médio Insumo Estoque'])
            df_precos_itens_producao_completo = format_columns_brazilian(df_precos_itens_producao_completo, ['Custo Ficha', 'Custo Item Produzido'])
            df_precos_insumos_producao = format_columns_brazilian(df_precos_insumos_producao, ['Preço Médio Insumo Estoque', 'Custo Ficha'])

        
            col1, col2 = st.columns([6, 1], vertical_alignment='center', gap='large')
            with col1:
                st.markdown(f'## Ficha Técnica - {produto_selecionado}')
            with col2:
                button_download(df_fichas_itens_vendidos_download[ordem_col], f'fichas_{casa}', f'fichas_{casa}')
            st.dataframe(df_fichas_itens_vendidos[ordem_col], use_container_width=True, hide_index=True)
            
            col1, col2 = st.columns([6, 1], vertical_alignment='center', gap='large')
            with col1:
                st.markdown('### Custos Itens de Estoque')
            with col2:
                button_download(df_fichas_insumos_de_estoque_download, f'estoq_{casa}', f'estoq_{casa}')
            st.dataframe(df_precos_insumos_de_estoque, use_container_width=True, hide_index=True)

            col1, col2 = st.columns([6, 1], vertical_alignment='center', gap='large')
            with col1:
                st.markdown('### Custos Itens de Produção')
            with col2:
                button_download(df_precos_itens_producao_completo_download, f'prod_{casa}', f'prod_{casa}')
            st.dataframe(df_precos_itens_producao_completo, use_container_width=True, hide_index=True)

            col1, col2 = st.columns([6, 1], vertical_alignment='center', gap='large')
            with col1:
                st.markdown(f'## Fichas Técnicas - Itens de Produção - {produto_selecionado}')
            with col2:
                button_download(df_precos_insumos_producao_download, f'fichas_prod{casa}', f'fichas_prod_{casa}')
            st.dataframe(df_precos_insumos_producao, use_container_width=True, hide_index=True)
    
if __name__ == '__main__':
    main()
