import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import calendar
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from utils.functions.general_functions_conciliacao import *
from utils.functions.general_functions import config_sidebar
from utils.queries_conciliacao import *
from workalendar.america import Brazil


st.set_page_config(
    page_title="Fluxo de Caixa FB",
    page_icon=":material/currency_exchange:",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Se der refresh, volta para página de login
if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Main.py')

# Personaliza menu lateral
config_sidebar()

st.title(":material/currency_exchange: Fluxo de Caixa Futuro FB")
st.divider()

# Filtrando Data
today = datetime.datetime.now()
last_year = today.year - 1
jan_last_year = datetime.datetime(last_year, 1, 1)
jan_this_year = datetime.datetime(today.year, 1, 1)
last_day_of_month = calendar.monthrange(today.year, today.month)[1]
this_month_this_year = datetime.datetime(today.year, today.month, last_day_of_month)
dec_this_year = datetime.datetime(today.year, 12, 31)

## 5 meses atras
month_sub_3 = today.month - 3
year = today.year

if month_sub_3 <= 0:
    # Se o mês resultante for menor ou igual a 0, ajustamos o ano e corrigimos o mês
    month_sub_3 += 12
    year -= 1

start_of_three_months_ago = datetime.datetime(year, month_sub_3, 1)


# Filtrando casas
df_casas = GET_CASAS()
casas = df_casas['Casa'].tolist()

# Criando colunas para o seletor de casas e o botão
col_casas, col_botao = st.columns([4, 1])

with col_casas:
    # Usando session_state se disponível, senão usa o valor padrão
    default_casas = st.session_state.get('casas_selecionadas', [casas[0]] if casas else [])
    casas_selecionadas = st.multiselect("Casas", casas, default=default_casas, key="casas_multiselect")

with col_botao:
    st.write("")  # Espaçamento para alinhar com o multiselect
    if st.button("🏢 Sem Sócios Externos ---", 
                 help="Seleciona automaticamente todas as casas que não possuem sócios externos (Bit_Socios_Externos = 0)", 
                 use_container_width=True):
        # Filtrando casas sem sócios externos
        casas_sem_socios_externos = df_casas[df_casas['Bit_Socios_Externos'] == 0]['Casa'].tolist()
        # Atualizando o multiselect através do session_state
        st.session_state['casas_selecionadas'] = casas_sem_socios_externos
        # Limpando a chave do multiselect para forçar a atualização
        if 'casas_multiselect' in st.session_state:
            del st.session_state['casas_multiselect']
        st.rerun()
    
    # Mostrando informação sobre casas sem sócios externos
    total_casas_sem_socios = len(df_casas[df_casas['Bit_Socios_Externos'] == 0])
    st.caption(f"📊 {total_casas_sem_socios} casas sem sócios externos")

# Definindo um dicionário para mapear nomes de casas a IDs de casas
mapeamento_lojas = dict(zip(df_casas["Casa"], df_casas["ID_Casa"]))

# Obtendo os IDs das casas selecionadas
ids_casas_selecionadas = [mapeamento_lojas[casa] for casa in casas_selecionadas]

if casas_selecionadas:
    st.write('Casas selecionadas:', ', '.join(casas_selecionadas))
    st.write('IDs das casas selecionadas:', ids_casas_selecionadas)
else:
    st.warning("Por favor, selecione pelo menos uma casa.")
    st.stop()

st.divider()

# Filtro de período simples
col1, col2 = st.columns([4, 1])

with col1:
    # Usando session_state se disponível, senão usa o valor padrão
    default_value = st.session_state.get('date_input', (jan_this_year, this_month_this_year))
    date_input = st.date_input("Período",
                               value=default_value,
                               min_value=jan_last_year,
                               max_value=dec_this_year,
                               format="DD/MM/YYYY",
                               key="date_input_widget"
                               )

with col2:
    # Calculando datas para o próximo mês até fim do ano
    next_month = today.replace(day=1) + timedelta(days=32)
    next_month = next_month.replace(day=1)
    end_of_year = datetime.datetime(today.year, 12, 31)
    
    st.write("")  # Espaçamento para alinhar com o date_input
    if st.button("📅 Próximo mês → Fim do ano", help="Define o período do primeiro dia do próximo mês até o último dia do ano atual", use_container_width=True):
        # Atualizando o date_input através do session_state
        st.session_state['date_input'] = (next_month.date(), end_of_year.date())
        st.rerun()

# Convertendo as datas do "date_input" para datetime
start_date = pd.to_datetime(date_input[0])
end_date = pd.to_datetime(date_input[1])

# Criando abas para separar fluxo realizado e futuro
tab1, tab2 = st.tabs(["💰 Fluxo Realizado", "🔮 Fluxo Futuro"])

with tab1:
    st.header("💰 Fluxo de Caixa Realizado")
    
    ### Definindo Bases ###

    ## Zig_Extrato
    st.subheader("Extrato Zig")
    df_extrato_zig = GET_EXTRATO_ZIG()
    df_extrato_zig_filtrada = df_extrato_zig[df_extrato_zig['ID_Casa'].isin(ids_casas_selecionadas)]
    df_extrato_zig_filtrada = df_extrato_zig_filtrada[(df_extrato_zig_filtrada["Data_Liquidacao"] >= start_date) & (df_extrato_zig_filtrada["Data_Liquidacao"] <= end_date)]
    df_extrato_zig_filtrada = df_extrato_zig_filtrada[['ID_Extrato','ID_Casa','Casa','Descricao','Data_Liquidacao','Data_Transacao','Valor']]
    #st.dataframe(df_extrato_zig_filtrada, use_container_width=True, hide_index=True)
    df_extrato_zig_filtrada_aggrid = component_plotDataframe_aggrid(
        df=df_extrato_zig_filtrada,
        name="Extrato Zig",
        num_columns=["Valor"],      # ex.: coluna de valores
        percent_columns=[],                # se tiver %
        df_details=None,
        coluns_merge_details=None,
        coluns_name_details=None
    )
    
    # Calculando total dos valores filtrados
    if not df_extrato_zig_filtrada_aggrid.empty and "Valor" in df_extrato_zig_filtrada_aggrid.columns:
        valores_filtrados = pd.to_numeric(df_extrato_zig_filtrada_aggrid["Valor"], errors='coerce')
        total_filtrado = valores_filtrados.sum()
        
        st.markdown(f"""
        <div style="
            background-color: #1e1e1e; 
            border: 1px solid #ffb131; 
            border-radius: 4px; 
            padding: 8px 12px; 
            margin: 5px 0; 
            text-align: center;
            display: inline-block;
        ">
            <span style="color: #ffb131; font-weight: bold;">💰 Total: R$ {total_filtrado:,.2f}</span>
            <span style="color: #cccccc; margin-left: 10px;">({len(df_extrato_zig_filtrada_aggrid)} registros)</span>
        </div>
        """, unsafe_allow_html=True)
    
    function_copy_dataframe_as_tsv(df_extrato_zig_filtrada_aggrid)

    st.divider()

    # ## Zig_Faturamento
    # st.subheader("Zig Faturamento")
    # df_zig_faturam = st.session_state["df_zig_faturam"]
    # df_zig_faturam_filtrada = df_zig_faturam[df_zig_faturam['ID_Casa'].isin(ids_casas_selecionadas)]
    # df_zig_faturam_filtrada = df_zig_faturam_filtrada[(df_zig_faturam_filtrada["Data_Venda"] >= start_date) & (df_zig_faturam_filtrada["Data_Venda"] <= end_date)]
    # df_zig_faturam_filtrada = df_zig_faturam_filtrada[df_zig_faturam_filtrada['Valor'] != 0]

    # st.dataframe(df_zig_faturam_filtrada, use_container_width=True, hide_index=True)

    # st.divider()

    ## Parcelas Receitas Extraordinárias
    st.subheader("Parcelas Receitas Extraordinarias")
    df_parc_receit_extr = GET_PARCELAS_RECEIT_EXTR()
    df_parc_receit_extr_filtrada = df_parc_receit_extr[df_parc_receit_extr['ID_Casa'].isin(ids_casas_selecionadas)]
    #df_parc_receit_extr_filtrada = df_parc_receit_extr_filtrada[(df_parc_receit_extr_filtrada["Recebimento_Parcela"] >= start_date) & (df_parc_receit_extr_filtrada["Recebimento_Parcela"] <= end_date)]
    df_parc_receit_extr_filtrada = df_parc_receit_extr_filtrada[['ID_Receita','ID_Casa','Casa','Cliente','Data_Ocorrencia','Vencimento_Parcela','Recebimento_Parcela','Valor_Parcela','Classif_Receita','Status_Pgto','Observacoes']]
    #st.dataframe(df_parc_receit_extr_filtrada, use_container_width=True, hide_index=True)
    df_parc_receit_extr_filtrada_aggrid = component_plotDataframe_aggrid(
        df=df_parc_receit_extr_filtrada,
        name="Parcelas Receitas Extraordinárias",
        num_columns=["Valor_Parcela"],      # ex.: coluna de valores
        percent_columns=[],                # se tiver %
        df_details=None,
        coluns_merge_details=None,
        coluns_name_details=None
    )
    
    # Calculando total dos valores filtrados
    if not df_parc_receit_extr_filtrada_aggrid.empty and "Valor_Parcela" in df_parc_receit_extr_filtrada_aggrid.columns:
        valores_filtrados = pd.to_numeric(df_parc_receit_extr_filtrada_aggrid["Valor_Parcela"], errors='coerce')
        total_filtrado = valores_filtrados.sum()
        
        st.markdown(f"""
        <div style="
            background-color: #1e1e1e; 
            border: 1px solid #ffb131; 
            border-radius: 4px; 
            padding: 8px 12px; 
            margin: 5px 0; 
            text-align: center;
            display: inline-block;
        ">
            <span style="color: #ffb131; font-weight: bold;">💰 Total: R$ {total_filtrado:,.2f}</span>
            <span style="color: #cccccc; margin-left: 10px;">({len(df_parc_receit_extr_filtrada_aggrid)} registros)</span>
        </div>
        """, unsafe_allow_html=True)
    
    function_copy_dataframe_as_tsv(df_parc_receit_extr_filtrada_aggrid)

    st.divider()

    ## Custos BlueMe Sem Parcelamento
    st.subheader("Despesas BlueMe Sem Parcelamento")
    df_custos_blueme_sem_parcelam = GET_CUSTOS_BLUEME_SEM_PARC()
    df_custos_blueme_sem_parcelam_filtrada = df_custos_blueme_sem_parcelam[df_custos_blueme_sem_parcelam['ID_Casa'].isin(ids_casas_selecionadas)]
    #df_custos_blueme_sem_parcelam_filtrada = df_custos_blueme_sem_parcelam_filtrada[(df_custos_blueme_sem_parcelam_filtrada["Realizacao_Pgto"] >= start_date) & (df_custos_blueme_sem_parcelam_filtrada["Realizacao_Pgto"] <= end_date)]
    df_custos_blueme_sem_parcelam_filtrada = df_custos_blueme_sem_parcelam_filtrada[['ID_Despesa','ID_Casa','Casa','Fornecedor','Valor','Data_Vencimento','Previsao_Pgto','Realizacao_Pgto','Data_Competencia','Class_Cont_1','Class_Cont_2','Status_Pgto']]
    #st.dataframe(df_custos_blueme_sem_parcelam_filtrada, use_container_width=True, hide_index=True)
    df_custos_blueme_sem_parcelam_filtrada_aggrid = component_plotDataframe_aggrid(
        df=df_custos_blueme_sem_parcelam_filtrada,
        name="Despesas BlueMe Sem Parcelamento",
        num_columns=["Valor"],      # ex.: coluna de valores
        percent_columns=[],                # se tiver %
        df_details=None,
        coluns_merge_details=None,
        coluns_name_details=None,
    )
    
    # Calculando total dos valores filtrados
    if not df_custos_blueme_sem_parcelam_filtrada_aggrid.empty and "Valor" in df_custos_blueme_sem_parcelam_filtrada_aggrid.columns:
        valores_filtrados = pd.to_numeric(df_custos_blueme_sem_parcelam_filtrada_aggrid["Valor"], errors='coerce')
        total_filtrado = valores_filtrados.sum()
        
        st.markdown(f"""
        <div style="
            background-color: #1e1e1e; 
            border: 1px solid #ffb131; 
            border-radius: 4px; 
            padding: 8px 12px; 
            margin: 5px 0; 
            text-align: center;
            display: inline-block;
        ">
            <span style="color: #ffb131; font-weight: bold;">💰 Total: R$ {total_filtrado:,.2f}</span>
            <span style="color: #cccccc; margin-left: 10px;">({len(df_custos_blueme_sem_parcelam_filtrada_aggrid)} registros)</span>
        </div>
        """, unsafe_allow_html=True)
    
    function_copy_dataframe_as_tsv(df_custos_blueme_sem_parcelam_filtrada_aggrid)

    st.divider()

    ## Custos BlueMe Com Parcelamento
    st.subheader("Despesas BlueMe Com Parcelamento")
    df_custos_blueme_com_parcelam = GET_CUSTOS_BLUEME_COM_PARC()
    df_custos_blueme_com_parcelam = df_custos_blueme_com_parcelam[['ID_Parcela','ID_Despesa','Casa','ID_Casa','Fornecedor','Qtd_Parcelas','Num_Parcela','Valor_Parcela','Vencimento_Parcela','Realiz_Parcela','Valor_Original','Class_Cont_1','Class_Cont_2','Status_Pgto']]
    df_custos_blueme_com_parcelam_filtrada = df_custos_blueme_com_parcelam[df_custos_blueme_com_parcelam['ID_Casa'].isin(ids_casas_selecionadas)]
    #df_custos_blueme_com_parcelam_filtrada = df_custos_blueme_com_parcelam_filtrada[(df_custos_blueme_com_parcelam_filtrada["Realiz_Parcela"] >= start_date) & (df_custos_blueme_com_parcelam_filtrada["Realiz_Parcela"] <= end_date)] 
    #st.dataframe(df_custos_blueme_com_parcelam_filtrada, use_container_width=True, hide_index=True)
    df_custos_blueme_com_parcelam_filtrada_aggrid = component_plotDataframe_aggrid(
        df=df_custos_blueme_com_parcelam_filtrada,
        name="Despesas Com Parcelamento",
        num_columns=["Valor_Parcela","Valor_Original"],      # ex.: coluna de valores
        percent_columns=[],                # se tiver %
        df_details=None,
        coluns_merge_details=None,
        coluns_name_details=None
    )
    
    # Calculando total dos valores filtrados
    if not df_custos_blueme_com_parcelam_filtrada_aggrid.empty:
        total_parcelas = 0
        total_original = 0
        
        if "Valor_Parcela" in df_custos_blueme_com_parcelam_filtrada_aggrid.columns:
            valores_parcelas = pd.to_numeric(df_custos_blueme_com_parcelam_filtrada_aggrid["Valor_Parcela"], errors='coerce')
            total_parcelas = valores_parcelas.sum()
        
        if "Valor_Original" in df_custos_blueme_com_parcelam_filtrada_aggrid.columns:
            valores_originais = pd.to_numeric(df_custos_blueme_com_parcelam_filtrada_aggrid["Valor_Original"], errors='coerce')
            total_original = valores_originais.sum()
        
        st.markdown(f"""
        <div style="
            background-color: #1e1e1e; 
            border: 1px solid #ffb131; 
            border-radius: 4px; 
            padding: 8px 12px; 
            margin: 5px 0; 
            text-align: center;
            display: inline-block;
        ">
            <span style="color: #ffb131; font-weight: bold;">💰 Parcelas: R$ {total_parcelas:,.2f}</span>
            <span style="color: #cccccc; margin-left: 10px;">| Original: R$ {total_original:,.2f}</span>
            <span style="color: #cccccc; margin-left: 10px;">({len(df_custos_blueme_com_parcelam_filtrada_aggrid)} registros)</span>
        </div>
        """, unsafe_allow_html=True)
    
    function_copy_dataframe_as_tsv(df_custos_blueme_com_parcelam_filtrada_aggrid)

    st.divider()

    # Aqui você pode adicionar mais conteúdo para o fluxo realizado
    st.info("💰 Conteúdo do Fluxo de Caixa Realizado - Todas as funcionalidades estão funcionando!")

    ## Gráfico Consolidado - Fluxo de Caixa por Mês
    st.subheader("📊 Fluxo de Caixa Consolidado por Mês")

    # Preparando dados para o gráfico
    def prepare_monthly_data():
        # Receitas - Extrato Zig
        receitas_zig = df_extrato_zig_filtrada.copy()
        mask_extrato_zig = (
        receitas_zig['Descricao'].str.contains('Cartão de Débito integrado Zig', na=False) |
        receitas_zig['Descricao'].str.contains('Cartão de Crédito integrado Zig', na=False) |
        receitas_zig['Descricao'].str.contains('Transações via Pix', na=False) |
        receitas_zig['Descricao'].str.contains('Transações via App', na=False) |
        receitas_zig['Descricao'].str.contains('Venda Avulsa Crédito', na=False) |
        receitas_zig['Descricao'].str.contains('Venda Avulsa Débito', na=False) |
        receitas_zig['Descricao'].str.contains('Venda Avulsa PIX', na=False)
        )
        receitas_zig = receitas_zig[mask_extrato_zig]
        receitas_zig['Mes_Ano'] = receitas_zig['Data_Liquidacao'].dt.to_period('M')
        receitas_zig['Tipo'] = 'Extrato Zig'
        receitas_zig_monthly = receitas_zig.groupby(['Mes_Ano', 'Tipo'])['Valor'].sum().reset_index()
        
        # Receitas - Parcelas Extraordinárias (aplicando filtro de data)
        receitas_extr = df_parc_receit_extr_filtrada.copy()
        receitas_extr = receitas_extr[(receitas_extr["Recebimento_Parcela"] >= start_date) & (receitas_extr["Recebimento_Parcela"] <= end_date)]
        receitas_extr['Mes_Ano'] = receitas_extr['Recebimento_Parcela'].dt.to_period('M')
        receitas_extr['Tipo'] = 'Extraordinária'
        receitas_extr_monthly = receitas_extr.groupby(['Mes_Ano', 'Tipo'])['Valor_Parcela'].sum().reset_index()
        receitas_extr_monthly.rename(columns={'Valor_Parcela': 'Valor'}, inplace=True)
        
        # Despesas - BlueMe Sem Parcelamento (aplicando filtro de data)
        despesas_sem_parc = df_custos_blueme_sem_parcelam_filtrada.copy()
        despesas_sem_parc = despesas_sem_parc[(despesas_sem_parc["Realizacao_Pgto"] >= start_date) & (despesas_sem_parc["Realizacao_Pgto"] <= end_date)]
        despesas_sem_parc['Mes_Ano'] = despesas_sem_parc['Realizacao_Pgto'].dt.to_period('M')
        despesas_sem_parc['Tipo'] = 'Sem Parcelamento'
        despesas_sem_parc_monthly = despesas_sem_parc.groupby(['Mes_Ano', 'Tipo'])['Valor'].sum().reset_index()
        
        # Despesas - BlueMe Com Parcelamento (aplicando filtro de data)
        despesas_com_parc = df_custos_blueme_com_parcelam_filtrada.copy()
        despesas_com_parc = despesas_com_parc[(despesas_com_parc["Realiz_Parcela"] >= start_date) & (despesas_com_parc["Realiz_Parcela"] <= end_date)]
        despesas_com_parc['Mes_Ano'] = despesas_com_parc['Realiz_Parcela'].dt.to_period('M')
        despesas_com_parc['Tipo'] = 'Com Parcelamento'
        despesas_com_parc_monthly = despesas_com_parc.groupby(['Mes_Ano', 'Tipo'])['Valor_Parcela'].sum().reset_index()
        despesas_com_parc_monthly.rename(columns={'Valor_Parcela': 'Valor'}, inplace=True)
        
        # Combinando dados de receitas
        receitas_data = pd.concat([receitas_zig_monthly, receitas_extr_monthly], ignore_index=True)
        receitas_data['Categoria'] = 'Receitas'
        
        # Combinando dados de despesas
        despesas_data = pd.concat([despesas_sem_parc_monthly, despesas_com_parc_monthly], ignore_index=True)
        despesas_data['Categoria'] = 'Despesas'
        
        # Combinando todos os dados
        all_data = pd.concat([receitas_data, despesas_data], ignore_index=True)
        
        # Convertendo Mes_Ano para string para melhor visualização (formato MM/YYYY)
        all_data['Mes_Ano_Str'] = all_data['Mes_Ano'].dt.strftime('%m/%Y')
        
        return all_data

    # Criando o gráfico
    try:
        df_consolidado = prepare_monthly_data()
        
        if not df_consolidado.empty:
            # Criando gráfico de barras personalizado
            fig = go.Figure()
            
            # Obtendo todos os meses únicos
            meses_unicos = sorted(df_consolidado['Mes_Ano_Str'].unique())
            
            # Adicionando barras de receitas
            receitas_data = df_consolidado[df_consolidado['Categoria'] == 'Receitas']
            for tipo in receitas_data['Tipo'].unique():
                dados_tipo = receitas_data[receitas_data['Tipo'] == tipo]
                valores = []
                for mes in meses_unicos:
                    valor = dados_tipo[dados_tipo['Mes_Ano_Str'] == mes]['Valor'].sum()
                    valores.append(valor)
                
                cor = '#2E8B57' if tipo == 'Extrato Zig' else '#32CD32'
                fig.add_trace(go.Bar(
                    x=meses_unicos,
                    y=valores,
                    name=tipo,
                    marker_color=cor,
                    offsetgroup='Receitas'
                ))
            
            # Adicionando barras de despesas
            despesas_data = df_consolidado[df_consolidado['Categoria'] == 'Despesas']
            for tipo in despesas_data['Tipo'].unique():
                dados_tipo = despesas_data[despesas_data['Tipo'] == tipo]
                valores = []
                for mes in meses_unicos:
                    valor = dados_tipo[dados_tipo['Mes_Ano_Str'] == mes]['Valor'].sum()
                    valores.append(valor)
                
                cor = '#DC143C' if tipo == 'Sem Parcelamento' else '#FF6347'
                fig.add_trace(go.Bar(
                    x=meses_unicos,
                    y=valores,
                    name=tipo,
                    marker_color=cor,
                    offsetgroup='Despesas'
                ))
            
            # Personalizando o layout
            casas_titulo = ', '.join(casas_selecionadas) if len(casas_selecionadas) <= 3 else f"{len(casas_selecionadas)} casas selecionadas"
            fig.update_layout(
                title=f'Fluxo de Caixa Consolidado - {casas_titulo} ({start_date.strftime("%d/%m/%Y")} a {end_date.strftime("%d/%m/%Y")})',
                xaxis_title="Mês/Ano",
                yaxis_title="Valor (R$)",
                barmode='group',
                height=600,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                bargap=0.3,  # Espaço entre grupos de barras (meses)
                bargroupgap=0.0  # Sem espaço entre barras do mesmo grupo (receitas e despesas do mesmo mês)
            )
            
            # Formatando eixo Y para moeda brasileira
            fig.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
            
            # Exibindo o gráfico
            st.plotly_chart(fig, use_container_width=True)
            
            # Criando gráfico de linha para fluxo líquido
            st.subheader("📈 Fluxo Líquido por Mês")
            
            # Calculando fluxo líquido
            receitas_mensais = df_consolidado[df_consolidado['Categoria'] == 'Receitas'].groupby('Mes_Ano_Str')['Valor'].sum()
            despesas_mensais = df_consolidado[df_consolidado['Categoria'] == 'Despesas'].groupby('Mes_Ano_Str')['Valor'].sum()
            
            fluxo_liquido = pd.DataFrame({
                'Mes_Ano_Str': receitas_mensais.index,
                'Receitas': receitas_mensais.values,
                'Despesas': despesas_mensais.values
            })
            fluxo_liquido['Fluxo_Liquido'] = fluxo_liquido['Receitas'] - fluxo_liquido['Despesas']
            fluxo_liquido['Receitas'] = fluxo_liquido['Receitas'].fillna(0)
            fluxo_liquido['Despesas'] = fluxo_liquido['Despesas'].fillna(0)
            
            # Gráfico de linha para fluxo líquido
            fig_liquido = go.Figure()
            
            fig_liquido.add_trace(go.Scatter(
                x=fluxo_liquido['Mes_Ano_Str'],
                y=fluxo_liquido['Fluxo_Liquido'],
                mode='lines+markers',
                name='Fluxo Líquido',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            fig_liquido.add_trace(go.Scatter(
                x=fluxo_liquido['Mes_Ano_Str'],
                y=fluxo_liquido['Receitas'],
                mode='lines+markers',
                name='Receitas Totais',
                line=dict(color='#2E8B57', width=2, dash='dash'),
                marker=dict(size=6)
            ))
            
            fig_liquido.add_trace(go.Scatter(
                x=fluxo_liquido['Mes_Ano_Str'],
                y=fluxo_liquido['Despesas'],
                mode='lines+markers',
                name='Despesas Totais',
                line=dict(color='#DC143C', width=2, dash='dash'),
                marker=dict(size=6)
            ))
            
            # Adicionando linha horizontal em y=0
            fig_liquido.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            fig_liquido.update_layout(
                title=f'Fluxo Líquido Mensal - {casas_titulo} ({start_date.strftime("%d/%m/%Y")} a {end_date.strftime("%d/%m/%Y")})',
                xaxis_title="Mês/Ano",
                yaxis_title="Valor (R$)",
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            fig_liquido.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
            
            st.plotly_chart(fig_liquido, use_container_width=True)
            
            # Mapeamento Class_Cont_1 para Class_Cont_0
            mapeamento_class_cont = {
                'Custo Mercadoria Vendida': 'Custo Mercadoria Vendida',
                'Custos Artístico Geral': 'Custos Artístico Geral',
                'Gorjeta': 'Mão de Obra',
                'Utilidades': 'Utilidades',
                'Mão de Obra - Salários': 'Mão de Obra',
                'Impostos sobre Venda': 'Impostos',
                'Custo de Ocupação': 'Ocupação',
                'Mão de Obra - PJ': 'Mão de Obra',
                'Mão de Obra - Extra': 'Mão de Obra',
                'Mão de Obra - Benefícios': 'Mão de Obra',
                'MAO DE OBRA FIXA/ TEMPORARIOS': 'Mão de Obra',
                'Endividamento': 'Endividamento',
                'CUSTO ARTISTICO': 'Custos Artístico Geral',
                'Serviços de Terceiros': 'Serviços de Terceiros',
                'Investimento - CAPEX': 'Investimento - Capex',
                'Marketing': 'Marketing',
                'INSUMOS': 'Custo Mercadoria Vendida',
                'UTILIDADES': 'Utilidades',
                'IMPOSTOS SOBRE VENDA': 'Impostos',
                'Manutenção': 'Manutenção',
                'Mão de Obra - Encargos e Provisões': 'Mão de Obra',
                'ENDIVIDAMENTO': 'Endividamento',
                'Dividendos e Remunerações Variáveis': 'Dividendos e Remunerações Variáveis',
                'Locação de Equipamentos': 'Locação de Equipamentos',
                'SERVICOS DE TERCEIROS': 'Serviços de Terceiros',
                'CUSTOS COM MARKETING': 'Marketing',
                'Informática e TI': 'Informática e TI',
                'CUSTOS DE EVENTOS': 'Custos de Eventos',
                'INVESTIMENTOS': 'Investimento - Capex',
                'Despesas Financeiras': 'Despesas Financeiras',
                'DESPESAS GERAIS': 'Utilidades',
                'Custos de Eventos': 'Custos de Eventos',
                'ADIANTAMENTO A FORNECEDORES': 'Custo Mercadoria Vendida',
                'Deduções sobre Venda': 'Deduções sobre Venda',
                'IMPOSTOS/ TRIBUTOS': 'Impostos',
                'LOCACOES': 'Locação de Equipamentos',
                'SISTEMAS/ T.I': 'Informática e TI',
                'Despesas com Transporte / Hospedagem': 'Despesas com Transporte / Hospedagem',
                'DESPESAS BANCARIAS': 'Despesas Financeiras',
                'CUSTO DA MERCADORIA VENDIDA': 'Custo Mercadoria Vendida',
                'CUSTO DE OCUPACAO': 'Ocupação',
                'CUSTOS DE MANUTENCAO': 'Manutenção',
                'DEDUCOES SOBRE VENDA': 'Deduções sobre Venda',
                'Imposto de Renda': 'Impostos'
            }
            
            # Tabela Dinâmica - Class_Cont_0 (Agrupamento)
            st.subheader("📊 Despesas por Classificação Contábil (Class_Cont_0)")
            
            # Preparando dados para Class_Cont_0
            def prepare_pivot_data_class0():
                # Despesas - BlueMe Sem Parcelamento (aplicando filtro de data)
                despesas_sem_parc = df_custos_blueme_sem_parcelam_filtrada.copy()
                despesas_sem_parc = despesas_sem_parc[(despesas_sem_parc["Realizacao_Pgto"] >= start_date) & (despesas_sem_parc["Realizacao_Pgto"] <= end_date)]
                despesas_sem_parc['Mes_Ano'] = despesas_sem_parc['Realizacao_Pgto'].dt.to_period('M')
                
                # Despesas - BlueMe Com Parcelamento (aplicando filtro de data)
                despesas_com_parc = df_custos_blueme_com_parcelam_filtrada.copy()
                despesas_com_parc = despesas_com_parc[(despesas_com_parc["Realiz_Parcela"] >= start_date) & (despesas_com_parc["Realiz_Parcela"] <= end_date)]
                despesas_com_parc['Mes_Ano'] = despesas_com_parc['Realiz_Parcela'].dt.to_period('M')
                
                # Combinando dados
                if not despesas_sem_parc.empty:
                    despesas_sem_parc_grouped = despesas_sem_parc.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor'].sum().reset_index()
                else:
                    despesas_sem_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Mes_Ano', 'Valor'])
                    
                if not despesas_com_parc.empty:
                    despesas_com_parc_grouped = despesas_com_parc.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor_Parcela'].sum().reset_index()
                    despesas_com_parc_grouped = despesas_com_parc_grouped.rename(columns={'Valor_Parcela': 'Valor'})
                else:
                    despesas_com_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Mes_Ano', 'Valor'])
                
                # Combinando os resultados
                all_despesas = pd.concat([despesas_sem_parc_grouped, despesas_com_parc_grouped], ignore_index=True)
                
                # Agrupando novamente para consolidar
                if not all_despesas.empty:
                    despesas_consolidadas = all_despesas.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor'].sum().reset_index()
                    
                    # Adicionando Class_Cont_0 baseado no mapeamento
                    despesas_consolidadas['Class_Cont_0'] = despesas_consolidadas['Class_Cont_1'].map(mapeamento_class_cont)
                    
                    # Para Class_Cont_1 não mapeadas, usar a própria Class_Cont_1
                    despesas_consolidadas['Class_Cont_0'] = despesas_consolidadas['Class_Cont_0'].fillna(despesas_consolidadas['Class_Cont_1'])
                    
                    # Agrupando por Class_Cont_0
                    despesas_class0 = despesas_consolidadas.groupby(['Class_Cont_0', 'Mes_Ano'])['Valor'].sum().reset_index()
                    return despesas_class0
                else:
                    return pd.DataFrame()
            
            # Obtendo dados para Class_Cont_0
            df_class0_data = prepare_pivot_data_class0()
            
            if not df_class0_data.empty:
                # Criando tabela dinâmica para Class_Cont_0
                pivot_table_class0 = df_class0_data.pivot(
                    index='Class_Cont_0',
                    columns='Mes_Ano',
                    values='Valor'
                ).fillna(0)
                
                # Convertendo índices de coluna para string
                pivot_table_class0.columns = pivot_table_class0.columns.astype(str)
                
                # Adicionando coluna de total
                pivot_table_class0['Total'] = pivot_table_class0.sum(axis=1)
                
                # Ordenando por total (maior para menor)
                pivot_table_class0 = pivot_table_class0.sort_values('Total', ascending=False)
                
                # Resetando o índice para incluir Class_Cont_0 como coluna
                pivot_table_class0 = pivot_table_class0.reset_index()
                
                # Separando colunas numéricas das de texto
                colunas_numericas_class0 = [col for col in pivot_table_class0.columns if col != 'Class_Cont_0']
                
                # Exibindo tabela dinâmica de Class_Cont_0
                df_pivot_class0_aggrid = component_plotDataframe_aggrid(
                    df=pivot_table_class0,
                    name="Despesas por Classificação Contábil (Class_Cont_0)",
                    num_columns=colunas_numericas_class0,
                    percent_columns=[],
                    df_details=None,
                    coluns_merge_details=None,
                    coluns_name_details=None
                )
                
                # Botão para copiar dados de Class_Cont_0
                function_copy_dataframe_as_tsv(df_pivot_class0_aggrid)
                
                st.markdown("---")
            
            # Tabela Dinâmica - Class_Cont_1 (Detalhamento)
            st.subheader("📊 Despesas por Classificação Contábil (Class_Cont_1)")
            
            # Preparando dados para a tabela dinâmica
            def prepare_pivot_data():
                # Despesas - BlueMe Sem Parcelamento (aplicando filtro de data)
                despesas_sem_parc = df_custos_blueme_sem_parcelam_filtrada.copy()
                despesas_sem_parc = despesas_sem_parc[(despesas_sem_parc["Realizacao_Pgto"] >= start_date) & (despesas_sem_parc["Realizacao_Pgto"] <= end_date)]
                despesas_sem_parc['Mes_Ano'] = despesas_sem_parc['Realizacao_Pgto'].dt.to_period('M')
                
                # Despesas - BlueMe Com Parcelamento (aplicando filtro de data)
                despesas_com_parc = df_custos_blueme_com_parcelam_filtrada.copy()
                despesas_com_parc = despesas_com_parc[(despesas_com_parc["Realiz_Parcela"] >= start_date) & (despesas_com_parc["Realiz_Parcela"] <= end_date)]
                despesas_com_parc['Mes_Ano'] = despesas_com_parc['Realiz_Parcela'].dt.to_period('M')
                
                # Combinando dados
                if not despesas_sem_parc.empty:
                    despesas_sem_parc_grouped = despesas_sem_parc.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor'].sum().reset_index()
                else:
                    despesas_sem_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Mes_Ano', 'Valor'])
                    
                if not despesas_com_parc.empty:
                    despesas_com_parc_grouped = despesas_com_parc.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor_Parcela'].sum().reset_index()
                    despesas_com_parc_grouped = despesas_com_parc_grouped.rename(columns={'Valor_Parcela': 'Valor'})
                else:
                    despesas_com_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Mes_Ano', 'Valor'])
                
                # Combinando os resultados
                all_despesas = pd.concat([despesas_sem_parc_grouped, despesas_com_parc_grouped], ignore_index=True)
                
                # Agrupando novamente para consolidar
                if not all_despesas.empty:
                    despesas_consolidadas = all_despesas.groupby(['Class_Cont_1', 'Mes_Ano'])['Valor'].sum().reset_index()
                    
                    # Criando tabela dinâmica usando pivot
                    pivot_table = despesas_consolidadas.pivot(
                        index='Class_Cont_1',
                        columns='Mes_Ano',
                        values='Valor'
                    ).fillna(0)
                    
                    # Convertendo índices de coluna para string
                    pivot_table.columns = pivot_table.columns.astype(str)
                    
                    # Adicionando coluna de total
                    pivot_table['Total'] = pivot_table.sum(axis=1)
                    
                    # Ordenando por total (maior para menor)
                    pivot_table = pivot_table.sort_values('Total', ascending=False)
                    
                    # Resetando o índice para incluir Class_Cont_1 como coluna
                    pivot_table = pivot_table.reset_index()
                    
                    return pivot_table
                else:
                    return pd.DataFrame()
            
            # Criando a tabela dinâmica
            try:
                pivot_table = prepare_pivot_data()
                
                if not pivot_table.empty:
                    # Separando colunas numéricas das de texto
                    colunas_numericas = [col for col in pivot_table.columns if col != 'Class_Cont_1']
                    
                    # Exibindo tabela dinâmica
                    df_pivot_aggrid = component_plotDataframe_aggrid(
                        df=pivot_table,
                        name="Tabela Dinâmica - Despesas por Classificação e Mês",
                        num_columns=colunas_numericas,  # Apenas colunas numéricas
                        percent_columns=[],
                        df_details=None,
                        coluns_merge_details=None,
                        coluns_name_details=None
                    )
                    
                    # Botão para copiar dados
                    function_copy_dataframe_as_tsv(df_pivot_aggrid)
                    
                    # Tabela Dinâmica - Detalhamento por Class_Cont_2
                    st.subheader("📋 Detalhamento por Subclassificação Contábil")
                    
                    # Preparando dados para Class_Cont_2
                    def prepare_pivot_data_class2():
                        # Despesas - BlueMe Sem Parcelamento (aplicando filtro de data)
                        despesas_sem_parc = df_custos_blueme_sem_parcelam_filtrada.copy()
                        despesas_sem_parc = despesas_sem_parc[(despesas_sem_parc["Realizacao_Pgto"] >= start_date) & (despesas_sem_parc["Realizacao_Pgto"] <= end_date)]
                        despesas_sem_parc['Mes_Ano'] = despesas_sem_parc['Realizacao_Pgto'].dt.to_period('M')
                        
                        # Despesas - BlueMe Com Parcelamento (aplicando filtro de data)
                        despesas_com_parc = df_custos_blueme_com_parcelam_filtrada.copy()
                        despesas_com_parc = despesas_com_parc[(despesas_com_parc["Realiz_Parcela"] >= start_date) & (despesas_com_parc["Realiz_Parcela"] <= end_date)]
                        despesas_com_parc['Mes_Ano'] = despesas_com_parc['Realiz_Parcela'].dt.to_period('M')
                        
                        # Combinando dados
                        if not despesas_sem_parc.empty:
                            despesas_sem_parc_grouped = despesas_sem_parc.groupby(['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano'])['Valor'].sum().reset_index()
                        else:
                            despesas_sem_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano', 'Valor'])
                            
                        if not despesas_com_parc.empty:
                            despesas_com_parc_grouped = despesas_com_parc.groupby(['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano'])['Valor_Parcela'].sum().reset_index()
                            despesas_com_parc_grouped = despesas_com_parc_grouped.rename(columns={'Valor_Parcela': 'Valor'})
                        else:
                            despesas_com_parc_grouped = pd.DataFrame(columns=['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano', 'Valor'])
                        
                        # Combinando os resultados
                        all_despesas = pd.concat([despesas_sem_parc_grouped, despesas_com_parc_grouped], ignore_index=True)
                        
                        # Agrupando novamente para consolidar
                        if not all_despesas.empty:
                            despesas_consolidadas = all_despesas.groupby(['Class_Cont_1', 'Class_Cont_2', 'Mes_Ano'])['Valor'].sum().reset_index()
                            return despesas_consolidadas
                        else:
                            return pd.DataFrame()
                    
                    # Obtendo dados para Class_Cont_2
                    df_class2_data = prepare_pivot_data_class2()
                    
                    if not df_class2_data.empty:
                        # Obtendo lista de Class_Cont_1 disponíveis
                        classificacoes_disponiveis = sorted(df_class2_data['Class_Cont_1'].unique())
                        
                        # Selectbox para escolher a classificação
                        classificacao_selecionada = st.selectbox(
                            "Selecione a Classificação Contábil para ver os detalhes:",
                            classificacoes_disponiveis,
                            index=0
                        )
                        
                        # Filtrando dados para a classificação selecionada
                        df_class2_filtrado = df_class2_data[df_class2_data['Class_Cont_1'] == classificacao_selecionada]
                        
                        if not df_class2_filtrado.empty:
                            # Criando tabela dinâmica para Class_Cont_2
                            pivot_table_class2 = df_class2_filtrado.pivot(
                                index='Class_Cont_2',
                                columns='Mes_Ano',
                                values='Valor'
                            ).fillna(0)
                            
                            # Convertendo índices de coluna para string
                            pivot_table_class2.columns = pivot_table_class2.columns.astype(str)
                            
                            # Adicionando coluna de total
                            pivot_table_class2['Total'] = pivot_table_class2.sum(axis=1)
                            
                            # Ordenando por total (maior para menor)
                            pivot_table_class2 = pivot_table_class2.sort_values('Total', ascending=False)
                            
                            # Resetando o índice para incluir Class_Cont_2 como coluna
                            pivot_table_class2 = pivot_table_class2.reset_index()
                            
                            # Separando colunas numéricas das de texto
                            colunas_numericas_class2 = [col for col in pivot_table_class2.columns if col != 'Class_Cont_2']
                            
                            # Exibindo tabela dinâmica de Class_Cont_2
                            df_pivot_class2_aggrid = component_plotDataframe_aggrid(
                                df=pivot_table_class2,
                                name=f"Detalhamento - {classificacao_selecionada}",
                                num_columns=colunas_numericas_class2,
                                percent_columns=[],
                                df_details=None,
                                coluns_merge_details=None,
                                coluns_name_details=None
                            )
                            
                            # Botão para copiar dados de Class_Cont_2
                            function_copy_dataframe_as_tsv(df_pivot_class2_aggrid)
                            
                        else:
                            st.warning(f"Não há dados de subclassificação disponíveis para {classificacao_selecionada}")
                    else:
                        st.warning("Não há dados de subclassificação disponíveis para o período e casas selecionadas.")
                    
                else:
                    st.warning("Não há dados de despesas disponíveis para o período e casas selecionadas.")
                    
            except Exception as e:
                st.error(f"Erro ao gerar tabela dinâmica: {str(e)}")
            
            # Resumo estatístico
            st.subheader("📋 Resumo Estatístico")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_receitas = df_consolidado[df_consolidado['Categoria'] == 'Receitas']['Valor'].sum()
                st.metric("Total Receitas", f"R$ {total_receitas:,.2f}")
            
            with col2:
                total_despesas = df_consolidado[df_consolidado['Categoria'] == 'Despesas']['Valor'].sum()
                st.metric("Total Despesas", f"R$ {total_despesas:,.2f}")
            
            with col3:
                fluxo_liquido_total = total_receitas - total_despesas
                st.metric("Fluxo Líquido", f"R$ {fluxo_liquido_total:,.2f}")
            
            with col4:
                if total_receitas > 0:
                    margem = (fluxo_liquido_total / total_receitas) * 100
                    st.metric("Margem (%)", f"{margem:.1f}%")
                else:
                    st.metric("Margem (%)", "N/A")
            
            # Tabela de Referência - Mapeamento Class_Cont_0 ↔ Class_Cont_1
            st.markdown("---")
            st.subheader("📋 Tabela de Referência - Mapeamento de Classificações")
            
            # Criando DataFrame de referência
            def create_mapping_reference():
                # Criando lista de mapeamentos
                mapping_list = []
                for class_cont_1, class_cont_0 in mapeamento_class_cont.items():
                    mapping_list.append({
                        'Class_Cont_0': class_cont_0,
                        'Class_Cont_1': class_cont_1,
                        'Status': 'Mapeado'
                    })
                
                # Verificando Class_Cont_1 que aparecem nos dados mas não estão mapeadas
                all_class_cont_1 = set()
                
                # Despesas sem parcelamento
                if not df_custos_blueme_sem_parcelam_filtrada.empty:
                    # Filtrando valores não nulos
                    class_cont_1_sem_parc = df_custos_blueme_sem_parcelam_filtrada['Class_Cont_1'].dropna().unique()
                    all_class_cont_1.update(class_cont_1_sem_parc)
                
                # Despesas com parcelamento
                if not df_custos_blueme_com_parcelam_filtrada.empty:
                    # Filtrando valores não nulos
                    class_cont_1_com_parc = df_custos_blueme_com_parcelam_filtrada['Class_Cont_1'].dropna().unique()
                    all_class_cont_1.update(class_cont_1_com_parc)
                
                # Verificando quais não estão mapeadas
                unmapped = all_class_cont_1 - set(mapeamento_class_cont.keys())
                
                for class_cont_1 in sorted(unmapped):
                    mapping_list.append({
                        'Class_Cont_0': class_cont_1,  # Usa a própria Class_Cont_1
                        'Class_Cont_1': class_cont_1,
                        'Status': 'Não Mapeado'
                    })
                
                return pd.DataFrame(mapping_list)
            
            # Criando e exibindo tabela de referência
            try:
                df_mapping_ref = create_mapping_reference()
                
                if not df_mapping_ref.empty:
                    # Ordenando por Class_Cont_0 e depois por Class_Cont_1
                    # Tratando valores None na ordenação
                    df_mapping_ref = df_mapping_ref.sort_values(['Class_Cont_0', 'Class_Cont_1'], na_position='last')
                    
                    # Exibindo tabela de referência
                    df_mapping_ref_aggrid = component_plotDataframe_aggrid(
                        df=df_mapping_ref,
                        name="Mapeamento Class_Cont_0 ↔ Class_Cont_1",
                        num_columns=[],
                        percent_columns=[],
                        df_details=None,
                        coluns_merge_details=None,
                        coluns_name_details=None
                    )
                    
                    # Botão para copiar dados de referência
                    function_copy_dataframe_as_tsv(df_mapping_ref_aggrid)
                    
                    # Resumo estatístico
                    total_mapped = len(df_mapping_ref[df_mapping_ref['Status'] == 'Mapeado'])
                    total_unmapped = len(df_mapping_ref[df_mapping_ref['Status'] == 'Não Mapeado'])
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total de Classificações", len(df_mapping_ref))
                    with col2:
                        percentual_mapeadas = f"{total_mapped/len(df_mapping_ref)*100:.1f}%" if len(df_mapping_ref) > 0 else "N/A"
                        st.metric("Mapeadas", total_mapped, delta=percentual_mapeadas)
                    with col3:
                        percentual_nao_mapeadas = f"{total_unmapped/len(df_mapping_ref)*100:.1f}%" if len(df_mapping_ref) > 0 else "N/A"
                        st.metric("Não Mapeadas", total_unmapped, delta=percentual_nao_mapeadas)
                    
                    # Aviso sobre classificações não mapeadas
                    if total_unmapped > 0:
                        st.warning(f"⚠️ **Atenção**: {total_unmapped} classificação(ões) não possuem mapeamento definido e serão tratadas como Class_Cont_0 próprias.")
                else:
                    st.info("Nenhuma classificação encontrada nos dados.")
                    
            except Exception as e:
                st.error(f"Erro ao gerar tabela de referência: {str(e)}")
            
        else:
            st.warning("Não há dados disponíveis para o período e casas selecionadas.")
            
    except Exception as e:
        st.error(f"Erro ao gerar gráfico: {str(e)}")



with tab2:
    st.header("🔮 Fluxo Futuro")

    # Definindo bases
    st.subheader("📋 Orçamento")
    
    # Informando o período filtrado
    st.info(f"📅 **Período filtrado**: {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")

    df_orcamentos = GET_ORCAMENTOS()
    
    # Convertendo Ano_Orcamento e Mes_Orcamento para formato de data
    df_orcamentos['Data_Orcamento'] = pd.to_datetime(
        df_orcamentos['Ano_Orcamento'].astype(str) + '-' + 
        df_orcamentos['Mes_Orcamento'].astype(str).str.zfill(2) + '-01',
        format='%Y-%m-%d',
        errors='coerce'
    )
    
    # Selecionando colunas incluindo a nova Data_Orcamento
    df_orcamentos = df_orcamentos[['ID_Orcamento','ID_Casa','Casa','Class_Cont_1','Class_Cont_2','Ano_Orcamento','Mes_Orcamento','Data_Orcamento','Valor_Orcamento','Tipo_Fluxo_Futuro']]
    
    # Filtrando por casas selecionadas e período de data
    df_orcamentos_filtrada = df_orcamentos[
        (df_orcamentos['ID_Casa'].isin(ids_casas_selecionadas)) &
        (df_orcamentos['Data_Orcamento'] >= start_date) &
        (df_orcamentos['Data_Orcamento'] <= end_date)
    ]
    
    # Exibindo tabela de orçamentos
    df_orcamentos_filtrada_aggrid = component_plotDataframe_aggrid(
        df=df_orcamentos_filtrada,
        name="Orcamentos",
        num_columns=["Valor_Orcamento"],
        percent_columns=[],
        df_details=None,
        coluns_merge_details=None,
        coluns_name_details=None
    )
    function_copy_dataframe_as_tsv(df_orcamentos_filtrada_aggrid)

    # Exibindo tabela de faturamento agregado
    st.subheader("📋 Faturamento Agregado")
    df_faturamento_agregado = GET_FATURAMENTO_AGREGADO()
    
    df_faturamento_agregado['Ano_Mes'] = df_faturamento_agregado['Ano'].astype(str) + '-' + df_faturamento_agregado['Mes'].astype(str).str.zfill(2)
    
    df_faturamento_agregado = df_faturamento_agregado[['ID_Faturam_Agregado', 'ID_Casa', 'Casa', 'Categoria', 'Ano_Mes', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]

    df_faturamento_agregado_filtrada = df_faturamento_agregado[df_faturamento_agregado['ID_Casa'].isin(ids_casas_selecionadas)]

    # Exibindo tabela de faturamento agregado
    df_faturamento_agregado_aggrid = component_plotDataframe_aggrid(
        df=df_faturamento_agregado_filtrada,
        name="Faturamento Agregado",
        num_columns=["Valor_Bruto", "Desconto", "Valor_Liquido"],
        percent_columns=[],
        df_details=None,
        coluns_merge_details=None,
        coluns_name_details=None
    )
    function_copy_dataframe_as_tsv(df_faturamento_agregado_aggrid)

    # ===== CONFIGURAÇÃO DO FATOR DE AJUSTE =====
    st.subheader("📅 Configuração do Fator de Ajuste")
    st.markdown("**Defina o período histórico para cálculo do fator de ajuste:**")
    
    # Calculando datas padrão para o filtro (últimos 6 meses realizados)
    hoje = datetime.datetime.now()
    data_limite_padrao = hoje.replace(day=1) - timedelta(days=1)  # Último dia do mês anterior
    data_inicio_padrao = data_limite_padrao.replace(day=1) - timedelta(days=180)  # 6 meses atrás
    
    # Usando session_state se disponível, senão usa o valor padrão
    default_fator_data = st.session_state.get('fator_ajuste_date_input', (data_inicio_padrao, data_limite_padrao))
    fator_ajuste_date_input = st.date_input(
        "Período para cálculo do fator de ajuste",
        value=default_fator_data,
        min_value=jan_last_year,
        max_value=data_limite_padrao,
        format="DD/MM/YYYY",
        key="fator_ajuste_date_input_widget",
        help="Selecione o período histórico que será usado para calcular o fator de ajuste baseado no desempenho orçado vs realizado."
    )
    
    # Atualizando session_state
    st.session_state['fator_ajuste_date_input'] = fator_ajuste_date_input
    
    # Convertendo para datetime se necessário
    if isinstance(fator_ajuste_date_input, tuple):
        data_inicio_fator = fator_ajuste_date_input[0]
        data_fim_fator = fator_ajuste_date_input[1]
    else:
        data_inicio_fator = fator_ajuste_date_input
        data_fim_fator = fator_ajuste_date_input
    
    st.info(f"📊 **Período selecionado para cálculo do fator**: {data_inicio_fator.strftime('%d/%m/%Y')} a {data_fim_fator.strftime('%d/%m/%Y')}")

    # ===== ANÁLISE COMPARATIVA: ORÇADO vs REALIZADO =====
    st.subheader("📊 Análise Comparativa: Orçado vs Realizado")
    
    # Mostrando o período usado para análise
    if 'fator_ajuste_date_input' in st.session_state:
        fator_data = st.session_state['fator_ajuste_date_input']
        if isinstance(fator_data, tuple):
            if len(fator_data) >= 2:
                periodo_analise = f"{fator_data[0].strftime('%d/%m/%Y')} a {fator_data[1].strftime('%d/%m/%Y')}"
            elif len(fator_data) == 1:
                periodo_analise = fator_data[0].strftime('%d/%m/%Y')
            else:
                periodo_analise = "Período não definido"
        else:
            periodo_analise = fator_data.strftime('%d/%m/%Y')
        st.info(f"📅 **Período de análise**: {periodo_analise}")
    
    # Filtrando dados para análise comparativa usando o filtro de data personalizado
    # Se o filtro de fator de ajuste não foi definido ainda, usar valores padrão
    if 'fator_ajuste_date_input' not in st.session_state:
        hoje = datetime.datetime.now()
        data_limite_analise = hoje.replace(day=1) - timedelta(days=1)  # Último dia do mês anterior
        data_inicio_analise = data_limite_analise.replace(day=1) - timedelta(days=180)  # 6 meses atrás
    else:
        fator_data = st.session_state['fator_ajuste_date_input']
        if isinstance(fator_data, tuple):
            data_inicio_analise = pd.to_datetime(fator_data[0])
            if len(fator_data) >= 2:
                data_limite_analise = pd.to_datetime(fator_data[1])
            else:
                data_limite_analise = data_inicio_analise  # Se só tem uma data, usar a mesma
        else:
            data_inicio_analise = pd.to_datetime(fator_data)
            data_limite_analise = pd.to_datetime(fator_data)
    
    # Filtrando orçamentos para análise
    df_orcamentos_analise = df_orcamentos[
        (df_orcamentos['ID_Casa'].isin(ids_casas_selecionadas)) &
        (df_orcamentos['Data_Orcamento'] >= data_inicio_analise) &
        (df_orcamentos['Data_Orcamento'] <= data_limite_analise) &
        (df_orcamentos['Class_Cont_1'] == 'Faturamento Bruto')
    ]
    
    # Filtrando faturamento realizado para análise
    df_faturamento_analise = df_faturamento_agregado[
        (df_faturamento_agregado['ID_Casa'].isin(ids_casas_selecionadas))
    ]
    
    # Aplicando filtro de data ao faturamento realizado
    # Convertendo Ano_Mes para datetime para comparação
    df_faturamento_analise['Data_Faturamento'] = pd.to_datetime(
        df_faturamento_analise['Ano_Mes'] + '-01'
    )
    
    # Filtrando por período selecionado
    df_faturamento_analise = df_faturamento_analise[
        (df_faturamento_analise['Data_Faturamento'] >= data_inicio_analise) &
        (df_faturamento_analise['Data_Faturamento'] <= data_limite_analise)
    ]
    
    if not df_orcamentos_analise.empty and not df_faturamento_analise.empty:
        # Agrupando orçamentos por mês
        orcamentos_mensais = df_orcamentos_analise.groupby(['Ano_Orcamento', 'Mes_Orcamento'])['Valor_Orcamento'].sum().reset_index()
        orcamentos_mensais['Data_Comparacao'] = pd.to_datetime(
            orcamentos_mensais['Ano_Orcamento'].astype(str) + '-' + 
            orcamentos_mensais['Mes_Orcamento'].astype(str).str.zfill(2) + '-01'
        )
        
        # Agrupando faturamento realizado por mês
        faturamento_mensais = df_faturamento_analise.groupby('Ano_Mes')['Valor_Bruto'].sum().reset_index()
        faturamento_mensais['Data_Comparacao'] = pd.to_datetime(
            faturamento_mensais['Ano_Mes'] + '-01'
        )
        
        # Merge dos dados para comparação
        df_comparacao = pd.merge(
            orcamentos_mensais[['Data_Comparacao', 'Valor_Orcamento']],
            faturamento_mensais[['Data_Comparacao', 'Valor_Bruto']],
            on='Data_Comparacao',
            how='outer'
        ).fillna(0)
        
        # Calculando diferenças e percentuais
        df_comparacao['Diferenca'] = df_comparacao['Valor_Bruto'] - df_comparacao['Valor_Orcamento']
        # Calculando percentual realizado evitando divisão por zero
        df_comparacao['Percentual_Realizado'] = df_comparacao.apply(
            lambda row: (row['Valor_Bruto'] / row['Valor_Orcamento'] * 100) if row['Valor_Orcamento'] != 0 else 0, 
            axis=1
        ).fillna(0)
        df_comparacao['Mes_Ano'] = df_comparacao['Data_Comparacao'].dt.strftime('%m/%Y')
        
        # Criando gráfico comparativo
        fig_comparacao = go.Figure()
        
        # Orçado (linha azul)
        fig_comparacao.add_trace(go.Scatter(
            x=df_comparacao['Mes_Ano'],
            y=df_comparacao['Valor_Orcamento'],
            mode='lines+markers',
            name='Orçado',
            line=dict(color='#1f77b4', width=3),
            marker=dict(size=8)
        ))
        
        # Realizado (linha verde)
        fig_comparacao.add_trace(go.Scatter(
            x=df_comparacao['Mes_Ano'],
            y=df_comparacao['Valor_Bruto'],
            mode='lines+markers',
            name='Realizado',
            line=dict(color='#2ca02c', width=3),
            marker=dict(size=8)
        ))
        
        # Configurando layout
        fig_comparacao.update_layout(
            title=f'Comparação Orçado vs Realizado - {", ".join(casas_selecionadas)}',
            xaxis_title="Mês/Ano",
            yaxis_title="Valor (R$)",
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig_comparacao.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
        
        st.plotly_chart(fig_comparacao, use_container_width=True)
        
        # Métricas de análise
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_orcado = df_comparacao['Valor_Orcamento'].sum() if not df_comparacao.empty else 0
            st.metric("Total Orçado", f"R$ {total_orcado:,.2f}")
        
        with col2:
            total_realizado = df_comparacao['Valor_Bruto'].sum() if not df_comparacao.empty else 0
            st.metric("Total Realizado", f"R$ {total_realizado:,.2f}")
        
        with col3:
            diferenca_total = total_realizado - total_orcado
            st.metric("Diferença Total", f"R$ {diferenca_total:,.2f}", 
                     delta=f"{diferenca_total/total_orcado*100:.1f}%" if total_orcado > 0 else "N/A")
        
        with col4:
            percentual_medio = df_comparacao['Percentual_Realizado'].mean()
            percentual_medio_display = f"{percentual_medio:.1f}%" if not pd.isna(percentual_medio) else "N/A"
            st.metric("Realizado vs Orçado (%)", percentual_medio_display)
        
        # Tabela detalhada de comparação
        st.subheader("📋 Detalhamento Mensal - Orçado vs Realizado")
        
        df_comparacao_display = df_comparacao[['Mes_Ano', 'Valor_Orcamento', 'Valor_Bruto', 'Diferenca', 'Percentual_Realizado']].copy()
        df_comparacao_display.columns = ['Mês/Ano', 'Orçado (R$)', 'Realizado (R$)', 'Diferença (R$)', 'Realizado/Orçado (%)']
        
        df_comparacao_aggrid = component_plotDataframe_aggrid(
            df=df_comparacao_display,
            name="Comparação Orçado vs Realizado",
            num_columns=["Orçado (R$)", "Realizado (R$)", "Diferença (R$)"],
            percent_columns=["Realizado/Orçado (%)"],
            df_details=None,
            coluns_merge_details=None,
            coluns_name_details=None
        )
        
        function_copy_dataframe_as_tsv(df_comparacao_aggrid)
        
        # ===== PROJEÇÃO DE RECEITAS DE PATROCÍNIOS =====
        st.subheader("🎯 Projeção de Receitas de Patrocínios")
        
        try:
            # Obtendo dados de parcelas de receitas extraordinárias
            df_parc_receit_extr = GET_PARCELAS_RECEIT_EXTR()
            
            # Debug: Verificando se o DataFrame existe e tem dados
            if df_parc_receit_extr is None or df_parc_receit_extr.empty:
                st.warning("⚠️ DataFrame de parcelas de receitas extraordinárias está vazio ou não disponível.")
                total_patrocinios = 0
                patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
            else:
                # Debug: Verificando colunas disponíveis
                colunas_necessarias = ['ID_Casa', 'Classif_Receita', 'Recebimento_Parcela', 'Vencimento_Parcela']
                colunas_faltantes = [col for col in colunas_necessarias if col not in df_parc_receit_extr.columns]
                if colunas_faltantes:
                    st.error(f"❌ Colunas necessárias não encontradas: {colunas_faltantes}")
                    st.write("Colunas disponíveis:", list(df_parc_receit_extr.columns))
                    total_patrocinios = 0
                    patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
                else:
                    # Filtrando apenas patrocínios pendentes (Recebimento_Parcela nulo) 
                    # e vencimento dentro do período futuro
                    df_patrocinios_futuros = df_parc_receit_extr[
                        (df_parc_receit_extr['ID_Casa'].isin(ids_casas_selecionadas)) &
                        (df_parc_receit_extr['Classif_Receita'] == 'Patrocínio') &
                        (df_parc_receit_extr['Recebimento_Parcela'].isna()) &  # Parcelas não recebidas
                        (df_parc_receit_extr['Vencimento_Parcela'] >= start_date) &
                        (df_parc_receit_extr['Vencimento_Parcela'] <= end_date)
                    ].copy()
                    
                    # Debug: Mostrando informações sobre o filtro
                    st.caption(f"🔍 Filtros aplicados: Casas={len(ids_casas_selecionadas)}, Período={start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}")
                    st.caption(f"📊 Total de registros encontrados: {len(df_patrocinios_futuros)}")
                    
                    # Debug adicional: Verificando se há patrocínios para as casas selecionadas
                    total_patrocinios_casas = df_parc_receit_extr[
                        (df_parc_receit_extr['ID_Casa'].isin(ids_casas_selecionadas)) &
                        (df_parc_receit_extr['Classif_Receita'] == 'Patrocínio')
                    ]
                    st.caption(f"🔍 Total de patrocínios para as casas selecionadas: {len(total_patrocinios_casas)}")
                    
                    # Debug: Verificando patrocínios pendentes (sem filtro de data)
                    patrocinios_pendentes = df_parc_receit_extr[
                        (df_parc_receit_extr['ID_Casa'].isin(ids_casas_selecionadas)) &
                        (df_parc_receit_extr['Classif_Receita'] == 'Patrocínio') &
                        (df_parc_receit_extr['Recebimento_Parcela'].isna())
                    ]
                    st.caption(f"🔍 Patrocínios pendentes (sem filtro de data): {len(patrocinios_pendentes)}")
                    
                    # Debug: Verificando patrocínios no período (sem filtro de recebimento)
                    patrocinios_periodo = df_parc_receit_extr[
                        (df_parc_receit_extr['ID_Casa'].isin(ids_casas_selecionadas)) &
                        (df_parc_receit_extr['Classif_Receita'] == 'Patrocínio') &
                        (df_parc_receit_extr['Vencimento_Parcela'] >= start_date) &
                        (df_parc_receit_extr['Vencimento_Parcela'] <= end_date)
                    ]
                    st.caption(f"🔍 Patrocínios no período (sem filtro de recebimento): {len(patrocinios_periodo)}")
                    
                    if not df_patrocinios_futuros.empty:
                        # Verificando se há valores únicos na coluna Classif_Receita para debug
                        classificacoes_unicas = df_parc_receit_extr['Classif_Receita'].unique()
                        st.caption(f"🏷️ Classificações disponíveis: {list(classificacoes_unicas)}")
                        
                        # Preparando dados para exibição
                        df_patrocinios_exibicao = df_patrocinios_futuros[[
                            'ID_Receita', 'Casa', 'Cliente', 'Data_Ocorrencia', 
                            'Vencimento_Parcela', 'Valor_Parcela', 'Classif_Receita', 
                            'Status_Pgto', 'Observacoes'
                        ]].copy()
                        
                        # Formatando datas
                        df_patrocinios_exibicao['Data_Ocorrencia'] = df_patrocinios_exibicao['Data_Ocorrencia'].dt.strftime('%d/%m/%Y')
                        df_patrocinios_exibicao['Vencimento_Parcela'] = df_patrocinios_exibicao['Vencimento_Parcela'].dt.strftime('%d/%m/%Y')
                        
                        # Renomeando colunas para melhor visualização
                        df_patrocinios_exibicao = df_patrocinios_exibicao.rename(columns={
                            'ID_Receita': 'ID Receita',
                            'Cliente': 'Cliente',
                            'Data_Ocorrencia': 'Data Ocorrência',
                            'Vencimento_Parcela': 'Vencimento Parcela',
                            'Valor_Parcela': 'Valor Parcela (R$)',
                            'Classif_Receita': 'Classificação',
                            'Status_Pgto': 'Status Pagamento',
                            'Observacoes': 'Observações'
                        })
                        
                        # Ordenando por vencimento
                        df_patrocinios_exibicao = df_patrocinios_exibicao.sort_values('Vencimento Parcela')
                        
                        # Exibindo tabela de patrocínios futuros
                        df_patrocinios_aggrid = component_plotDataframe_aggrid(
                            df=df_patrocinios_exibicao,
                            name="Projeção de Receitas de Patrocínios",
                            num_columns=["Valor Parcela (R$)"],
                            percent_columns=[],
                            df_details=None,
                            coluns_merge_details=None,
                            coluns_name_details=None
                        )
                        
                        # Calculando total dos valores filtrados
                        if not df_patrocinios_aggrid.empty and "Valor Parcela (R$)" in df_patrocinios_aggrid.columns:
                            valores_filtrados = pd.to_numeric(df_patrocinios_aggrid["Valor Parcela (R$)"], errors='coerce')
                            total_patrocinios = valores_filtrados.sum()
                            
                            st.markdown(f"""
                            <div style="
                                background-color: #1e1e1e; 
                                border: 1px solid #ffb131; 
                                border-radius: 4px; 
                                padding: 8px 12px; 
                                margin: 5px 0; 
                                text-align: center;
                                display: inline-block;
                            ">
                                <span style="color: #ffb131; font-weight: bold;">💰 Total Patrocínios: R$ {total_patrocinios:,.2f}</span>
                                <span style="color: #cccccc; margin-left: 10px;">({len(df_patrocinios_aggrid)} parcelas pendentes)</span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        function_copy_dataframe_as_tsv(df_patrocinios_aggrid)
                        
                        # Agrupando patrocínios por mês para uso nas projeções
                        df_patrocinios_futuros['Mes_Ano'] = df_patrocinios_futuros['Vencimento_Parcela'].dt.strftime('%m/%Y')
                        # Convertendo Valor_Parcela para float para evitar problemas com Decimal
                        df_patrocinios_futuros['Valor_Parcela_Float'] = df_patrocinios_futuros['Valor_Parcela'].astype(float)
                        patrocinios_mensais = df_patrocinios_futuros.groupby('Mes_Ano')['Valor_Parcela_Float'].sum().reset_index()
                        patrocinios_mensais = patrocinios_mensais.rename(columns={'Valor_Parcela_Float': 'Valor_Parcela'})
                        patrocinios_mensais['Mes_Ano_Display'] = patrocinios_mensais['Mes_Ano']
                        
                        # Debug: Mostrando informações sobre o agrupamento
                        st.caption(f"🔍 Patrocínios agrupados por mês: {len(patrocinios_mensais)} meses")
                        if not patrocinios_mensais.empty:
                            st.caption(f"🔍 Meses com patrocínios: {list(patrocinios_mensais['Mes_Ano_Display'])}")
                            st.caption(f"🔍 Total de patrocínios agrupados: R$ {patrocinios_mensais['Valor_Parcela'].astype(float).sum():,.2f}")
                        
                    else:
                        st.info("Não há receitas de patrocínios pendentes para o período selecionado.")
                        total_patrocinios = 0
                        patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
                        
        except Exception as e:
            st.error(f"❌ Erro ao processar projeção de patrocínios: {str(e)}")
            st.exception(e)
            total_patrocinios = 0
            patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
        
        # ===== PROJEÇÃO AJUSTADA =====
        st.subheader("🔮 Projeção Ajustada - Próximos Meses")
        
        # Calculando fator de ajuste baseado no histórico (abordagem conservadora)
        # Aplica ajuste apenas quando percentual_medio < 100% (corrige para baixo)
        # Quando percentual_medio > 100%, mantém fator = 1.0 (não projeta otimisticamente)
        if percentual_medio > 0:
            fator_ajuste = min(percentual_medio / 100, 1.0)
        else:
            fator_ajuste = 1.0
        
        # Obtendo orçamentos futuros para ajustar - usando o filtro de datas do usuário
        data_futura_inicio = start_date  # Usando a data inicial do filtro
        data_futura_fim = end_date       # Usando a data final do filtro  # Até o final do período selecionado
        
        df_orcamentos_futuros = df_orcamentos[
            (df_orcamentos['ID_Casa'].isin(ids_casas_selecionadas)) &
            (df_orcamentos['Data_Orcamento'] >= data_futura_inicio) &
            (df_orcamentos['Data_Orcamento'] <= data_futura_fim) &
            (df_orcamentos['Class_Cont_1'] == 'Faturamento Bruto')
        ]
        
        if not df_orcamentos_futuros.empty:
            # Convertendo Valor_Orcamento para float para evitar problemas com decimal.Decimal
            df_orcamentos_futuros['Valor_Orcamento_Float'] = df_orcamentos_futuros['Valor_Orcamento'].astype(float)
            
            # Aplicando fator de ajuste
            df_orcamentos_futuros['Valor_Projetado'] = df_orcamentos_futuros['Valor_Orcamento_Float'] * fator_ajuste
            df_orcamentos_futuros['Ajuste'] = df_orcamentos_futuros['Valor_Projetado'] - df_orcamentos_futuros['Valor_Orcamento_Float']
            
            # Agrupando projeções por mês
            projecoes_mensais = df_orcamentos_futuros.groupby(['Ano_Orcamento', 'Mes_Orcamento']).agg({
                'Valor_Orcamento_Float': 'sum',
                'Valor_Projetado': 'sum',
                'Ajuste': 'sum'
            }).reset_index()
            
            # Renomeando coluna para manter compatibilidade
            projecoes_mensais = projecoes_mensais.rename(columns={'Valor_Orcamento_Float': 'Valor_Orcamento'})
            
            projecoes_mensais['Data_Projecao'] = pd.to_datetime(
                projecoes_mensais['Ano_Orcamento'].astype(str) + '-' + 
                projecoes_mensais['Mes_Orcamento'].astype(str).str.zfill(2) + '-01'
            )
            projecoes_mensais['Mes_Ano'] = projecoes_mensais['Data_Projecao'].dt.strftime('%m/%Y')
            
            # Criando gráfico de projeção
            fig_projecao = go.Figure()
            
            # Orçado original (linha azul)
            fig_projecao.add_trace(go.Scatter(
                x=projecoes_mensais['Mes_Ano'],
                y=projecoes_mensais['Valor_Orcamento'],
                mode='lines+markers',
                name='Orçado Original',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ))
            
            # Projeção ajustada (linha laranja)
            fig_projecao.add_trace(go.Scatter(
                x=projecoes_mensais['Mes_Ano'],
                y=projecoes_mensais['Valor_Projetado'],
                mode='lines+markers',
                name='Projeção Ajustada (Orçamento)',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=8)
            ))
            
            # Adicionando patrocínios se existirem
            if not patrocinios_mensais.empty:
                # Debug: Verificando dados dos patrocínios antes de adicionar ao gráfico
                st.caption(f"🔍 Adicionando patrocínios ao gráfico: {len(patrocinios_mensais)} pontos")
                st.caption(f"🔍 Dados dos patrocínios: {patrocinios_mensais[['Mes_Ano_Display', 'Valor_Parcela']].to_dict('records')}")
                
                fig_projecao.add_trace(go.Scatter(
                    x=patrocinios_mensais['Mes_Ano_Display'],
                    y=patrocinios_mensais['Valor_Parcela'],
                    mode='lines+markers',
                    name='Patrocínios',
                    line=dict(color='#32CD32', width=3),
                    marker=dict(size=8)
                ))
                
                # Calculando receita total (orçamento + patrocínios)
                # Criando DataFrame com projeções de orçamento
                receita_total_mensal = projecoes_mensais[['Mes_Ano', 'Valor_Projetado']].copy()
                receita_total_mensal = receita_total_mensal.rename(columns={'Valor_Projetado': 'Orcamento_Projetado'})
                
                # Adicionando patrocínios através de merge
                patrocinios_para_total = patrocinios_mensais[['Mes_Ano', 'Valor_Parcela']].copy()
                patrocinios_para_total = patrocinios_para_total.rename(columns={'Valor_Parcela': 'Patrocinios'})
                
                # Merge para combinar orçamento e patrocínios
                receita_total_mensal = pd.merge(
                    receita_total_mensal,
                    patrocinios_para_total,
                    on='Mes_Ano',
                    how='left'
                ).fillna(0)
                
                # Calculando receita total - convertendo ambos para float para evitar problemas com Decimal
                receita_total_mensal['Receita_Total'] = receita_total_mensal['Orcamento_Projetado'].astype(float) + receita_total_mensal['Patrocinios'].astype(float)
                
                # Formatando data para exibição
                receita_total_mensal['Mes_Ano_Display'] = receita_total_mensal['Mes_Ano']
                
                # Debug: Verificando cálculo da receita total
                st.caption(f"🔍 Receita total calculada: {len(receita_total_mensal)} meses")
                st.caption(f"🔍 Dados da receita total: {receita_total_mensal[['Mes_Ano_Display', 'Orcamento_Projetado', 'Patrocinios', 'Receita_Total']].to_dict('records')}")
                
                # Adicionando linha de receita total
                st.caption(f"🔍 Adicionando receita total ao gráfico: {len(receita_total_mensal)} pontos")
                
                fig_projecao.add_trace(go.Scatter(
                    x=receita_total_mensal['Mes_Ano_Display'],
                    y=receita_total_mensal['Receita_Total'],
                    mode='lines+markers',
                    name='Receita Total (Orçamento + Patrocínios)',
                    line=dict(color='#2E8B57', width=4, dash='dash'),
                    marker=dict(size=10)
                ))
            
            # Configurando layout
            titulo_grafico = f'Projeção Ajustada - Fator: {fator_ajuste:.2f} ({percentual_medio:.1f}% do orçado)'
            if not patrocinios_mensais.empty:
                titulo_grafico += ' + Patrocínios'
            
            fig_projecao.update_layout(
                title=titulo_grafico,
                xaxis_title="Mês/Ano",
                yaxis_title="Valor (R$)",
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            fig_projecao.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
            
            st.plotly_chart(fig_projecao, use_container_width=True)
            
            # Métricas de projeção
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_orcado_futuro = projecoes_mensais['Valor_Orcamento'].sum()
                st.metric("Total Orçado Futuro", f"R$ {total_orcado_futuro:,.2f}")
            
            with col2:
                total_projetado = projecoes_mensais['Valor_Projetado'].sum()
                st.metric("Total Projetado (Orçamento)", f"R$ {total_projetado:,.2f}")
            
            with col3:
                total_patrocinios_projecao = patrocinios_mensais['Valor_Parcela'].astype(float).sum() if not patrocinios_mensais.empty else 0
                st.metric("Total Patrocínios", f"R$ {total_patrocinios_projecao:,.2f}")
            
            with col4:
                receita_total_projetada = total_projetado + total_patrocinios_projecao
                st.metric("Receita Total Projetada", f"R$ {receita_total_projetada:,.2f}")
            
            # Métricas adicionais
            col1, col2 = st.columns(2)
            
            with col1:
                diferenca_projecao = total_projetado - total_orcado_futuro
                st.metric("Ajuste Orçamento", f"R$ {diferenca_projecao:,.2f}", 
                         delta=f"{diferenca_projecao/total_orcado_futuro*100:.1f}%" if total_orcado_futuro > 0 else "N/A")
            
            with col2:
                diferenca_percentual = (diferenca_projecao / total_orcado_futuro * 100) if total_orcado_futuro > 0 else 0
                st.metric("Ajuste Orçamento (%)", f"↓{diferenca_percentual:.1f}%")
            
            # Tabela de projeções
            st.subheader("📋 Detalhamento das Projeções")
            
            # Preparando dados para a tabela consolidada
            # Sempre incluir patrocínios, mesmo que vazios
            projecoes_consolidadas = projecoes_mensais[['Mes_Ano', 'Valor_Orcamento', 'Valor_Projetado', 'Ajuste']].copy()
            projecoes_consolidadas = projecoes_consolidadas.rename(columns={
                'Valor_Orcamento': 'Orcamento_Original',
                'Valor_Projetado': 'Orcamento_Projetado',
                'Ajuste': 'Ajuste_Orcamento'
            })
            
            # Adicionando patrocínios (se existirem)
            if not patrocinios_mensais.empty:
                # Convertendo Mes_Ano_Display para Mes_Ano para fazer o merge correto
                patrocinios_para_merge = patrocinios_mensais[['Mes_Ano', 'Valor_Parcela']].copy()
                patrocinios_para_merge = patrocinios_para_merge.rename(columns={
                    'Valor_Parcela': 'Patrocinios'
                })
                
                # Merge das projeções
                projecoes_consolidadas = pd.merge(
                    projecoes_consolidadas, 
                    patrocinios_para_merge, 
                    on='Mes_Ano', 
                    how='left'
                ).fillna(0)
            else:
                # Adicionando coluna vazia para patrocínios
                projecoes_consolidadas['Patrocinios'] = 0
            
            # Calculando receita total - convertendo ambos para float para evitar problemas com Decimal
            projecoes_consolidadas['Receita_Total'] = projecoes_consolidadas['Orcamento_Projetado'].astype(float) + projecoes_consolidadas['Patrocinios'].astype(float)
            
            # Debug: Verificando dados da tabela consolidada
            st.caption(f"🔍 Tabela consolidada: {len(projecoes_consolidadas)} linhas")
            st.caption(f"🔍 Colunas da tabela: {list(projecoes_consolidadas.columns)}")
            st.caption(f"🔍 Dados da tabela: {projecoes_consolidadas[['Mes_Ano', 'Orcamento_Projetado', 'Patrocinios', 'Receita_Total']].to_dict('records')}")
            
            # Preparando para exibição
            projecoes_display = projecoes_consolidadas[[
                'Mes_Ano', 'Orcamento_Original', 'Orcamento_Projetado', 'Ajuste_Orcamento', 
                'Patrocinios', 'Receita_Total'
            ]].copy()
            projecoes_display.columns = [
                'Mês/Ano', 'Orçado Original (R$)', 'Projeção Ajustada (R$)', 'Ajuste (R$)', 
                'Patrocínios (R$)', 'Receita Total (R$)'
            ]
            
            projecoes_aggrid = component_plotDataframe_aggrid(
                df=projecoes_display,
                name="Projeções Ajustadas",
                num_columns=["Orçado Original (R$)", "Projeção Ajustada (R$)", "Ajuste (R$)", "Patrocínios (R$)", "Receita Total (R$)"],
                percent_columns=[],
                df_details=None,
                coluns_merge_details=None,
                coluns_name_details=None
            )
            
            function_copy_dataframe_as_tsv(projecoes_aggrid)
            
        else:
            st.warning("Não há orçamentos futuros disponíveis para projeção.")

        # ===== PROJEÇÃO DE FLUXO DE CAIXA FUTURO BASEADA NO TIPO DE FLUXO =====
        st.subheader("🔮 Projeção de Fluxo de Caixa Futuro - Por Tipo de Fluxo")
        
        # Informando o período de projeção
        st.info(f"📅 **Período de projeção**: {data_futura_inicio.strftime('%d/%m/%Y')} a {data_futura_fim.strftime('%d/%m/%Y')}")
        
        # Obtendo dados das despesas BlueMe
        df_despesas_sem_parcelamento = GET_CUSTOS_BLUEME_SEM_PARC()
        df_despesas_com_parcelamento = GET_CUSTOS_BLUEME_COM_PARC()
        
        # Filtrando despesas por casas selecionadas
        df_despesas_sem_parcelamento = df_despesas_sem_parcelamento[df_despesas_sem_parcelamento['ID_Casa'].isin(ids_casas_selecionadas)]
        df_despesas_com_parcelamento = df_despesas_com_parcelamento[df_despesas_com_parcelamento['ID_Casa'].isin(ids_casas_selecionadas)]
        
        # Obtendo orçamentos futuros por tipo de fluxo
        df_orcamentos_futuros_tipos = df_orcamentos[
            (df_orcamentos['ID_Casa'].isin(ids_casas_selecionadas)) &
            (df_orcamentos['Data_Orcamento'] >= data_futura_inicio) &
            (df_orcamentos['Data_Orcamento'] <= data_futura_fim) &
            (df_orcamentos['Class_Cont_1'] != 'Faturamento Bruto')  # Excluindo faturamento
        ]
        
        if not df_orcamentos_futuros_tipos.empty:
            # Processando por tipo de fluxo futuro
            projecoes_por_tipo = []
            
            # Criando seção expansível com os parâmetros configurados no sistema
            with st.expander("📋 Parâmetros Configurados no Sistema", expanded=False):
                # Obtendo dados da configuração do sistema
                df_tipo_class_cont_2 = GET_TIPO_CLASS_CONT_2()
                
                # Criando dataframe para exibição
                df_configuracao_exibicao = df_tipo_class_cont_2[['Tipo_Fluxo_Futuro', 'Class_Cont_1', 'Class_Cont_2']].copy()
                df_configuracao_exibicao = df_configuracao_exibicao.rename(columns={
                    'Tipo_Fluxo_Futuro': 'Tipo de Fluxo Futuro',
                    'Class_Cont_1': 'Classificação Contábil 1',
                    'Class_Cont_2': 'Classificação Contábil 2'
                })
                
                # Ordenando por tipo de fluxo e classificações
                ordem_tipos = {'Fixo': 1, 'Variavel do Faturamento': 2, 'Considerar Lançamentos': 3}
                df_configuracao_exibicao['Ordem'] = df_configuracao_exibicao['Tipo de Fluxo Futuro'].map(ordem_tipos)
                df_configuracao_exibicao = df_configuracao_exibicao.sort_values(['Ordem', 'Classificação Contábil 1', 'Classificação Contábil 2'])
                df_configuracao_exibicao = df_configuracao_exibicao.drop('Ordem', axis=1)
                
                # Exibindo tabela de configuração
                config_aggrid = component_plotDataframe_aggrid(
                    df=df_configuracao_exibicao,
                    name="Configuração do Sistema",
                    num_columns=[],
                    percent_columns=[],
                    df_details=None,
                    coluns_merge_details=None,
                    coluns_name_details=None
                )
                
                function_copy_dataframe_as_tsv(config_aggrid)
            
            # Processando por tipo de fluxo futuro
            projecoes_por_tipo = []
            
            for tipo_fluxo in ['Fixo', 'Variavel do Faturamento', 'Considerar Lançamentos']:
                st.write(f"**Tipo de Fluxo: {tipo_fluxo}**")
                
                if tipo_fluxo == 'Fixo':
                    # Despesas fixas - usar valores dos orçamentos diretamente
                    # Obtendo as classificações que são do tipo "Fixo" da configuração do sistema
                    df_tipo_class_cont_2 = GET_TIPO_CLASS_CONT_2()
                    classificacoes_fixo_configuradas = df_tipo_class_cont_2[
                        df_tipo_class_cont_2['Tipo_Fluxo_Futuro'] == 'Fixo'
                    ]['Class_Cont_1'].unique()
                    
                    # Filtrando orçamentos apenas para classificações configuradas como "Fixo"
                    orcamentos_fixo = df_orcamentos_futuros_tipos[
                        df_orcamentos_futuros_tipos['Class_Cont_1'].isin(classificacoes_fixo_configuradas)
                    ].copy()
                    
                    if not orcamentos_fixo.empty:
                        orcamentos_fixo['Valor_Projetado'] = orcamentos_fixo['Valor_Orcamento'].astype(float)
                        orcamentos_fixo['Tipo_Projecao'] = 'Fixo'
                        projecoes_por_tipo.append(orcamentos_fixo)
                        
                        total_fixo = orcamentos_fixo['Valor_Projetado'].sum()
                        st.write(f"Total projetado (Fixo): R$ {total_fixo:,.2f}")
                    else:
                        st.write("Nenhum orçamento encontrado para este tipo.")
                
                elif tipo_fluxo == 'Variavel do Faturamento':
                    # Despesas variáveis - aplicar fator de ajuste
                    # Obtendo as classificações que são do tipo "Variável do Faturamento" da configuração do sistema
                    df_tipo_class_cont_2 = GET_TIPO_CLASS_CONT_2()
                    classificacoes_variavel_configuradas = df_tipo_class_cont_2[
                        df_tipo_class_cont_2['Tipo_Fluxo_Futuro'] == 'Variavel do Faturamento'
                    ]['Class_Cont_1'].unique()
                    
                    # Filtrando orçamentos apenas para classificações configuradas como "Variável do Faturamento"
                    orcamentos_variavel = df_orcamentos_futuros_tipos[
                        df_orcamentos_futuros_tipos['Class_Cont_1'].isin(classificacoes_variavel_configuradas)
                    ].copy()
                    
                    if not orcamentos_variavel.empty:
                        orcamentos_variavel['Valor_Projetado'] = orcamentos_variavel['Valor_Orcamento'].astype(float) * fator_ajuste
                        orcamentos_variavel['Tipo_Projecao'] = 'Variável'
                        projecoes_por_tipo.append(orcamentos_variavel)
                        
                        total_variavel = orcamentos_variavel['Valor_Projetado'].sum()
                        st.write(f"Total projetado (Variável - fator {fator_ajuste:.2f}): R$ {total_variavel:,.2f}")
                    else:
                        st.write("Nenhum orçamento encontrado para este tipo.")
                
                elif tipo_fluxo == 'Considerar Lançamentos':
                    # Usar despesas realmente lançadas (pendentes) apenas para classificações que são "Considerar Lançamentos"
                    
                    # Obtendo as classificações que são do tipo "Considerar Lançamentos" da configuração do sistema
                    df_tipo_class_cont_2 = GET_TIPO_CLASS_CONT_2()
                    classificacoes_lancamentos_configuradas = df_tipo_class_cont_2[
                        df_tipo_class_cont_2['Tipo_Fluxo_Futuro'] == 'Considerar Lançamentos'
                    ]['Class_Cont_1'].unique()
                    
                    # Usando apenas as classificações configuradas como "Considerar Lançamentos"
                    classificacoes_lancamentos = list(classificacoes_lancamentos_configuradas)
                    
                    # Despesas sem parcelamento pendentes - filtrando apenas pelas classificações corretas
                    despesas_sem_parc_pendentes = df_despesas_sem_parcelamento[
                        (df_despesas_sem_parcelamento['Status_Pgto'] == 'Pendente') &
                        (df_despesas_sem_parcelamento['Class_Cont_1'].isin(classificacoes_lancamentos))
                    ].copy()
                    
                    # Despesas com parcelamento pendentes - filtrando apenas pelas classificações corretas
                    despesas_com_parc_pendentes = df_despesas_com_parcelamento[
                        (df_despesas_com_parcelamento['Status_Pgto'] == 'Parcela_Pendente') &
                        (df_despesas_com_parcelamento['Class_Cont_1'].isin(classificacoes_lancamentos))
                    ].copy()
                    
                    # Processando despesas sem parcelamento
                    if not despesas_sem_parc_pendentes.empty:
                        # Usar Previsao_Pgto se disponível, senão Data_Vencimento (mantendo o dia exato)
                        despesas_sem_parc_pendentes['Data_Projecao'] = despesas_sem_parc_pendentes['Previsao_Pgto'].fillna(
                            despesas_sem_parc_pendentes['Data_Vencimento']
                        )
                        # Adicionando colunas de data de competência e vencimento original
                        if 'Data_Competencia' in despesas_sem_parc_pendentes.columns:
                            despesas_sem_parc_pendentes['Data_Competencia'] = despesas_sem_parc_pendentes['Data_Competencia']
                        else:
                            despesas_sem_parc_pendentes['Data_Competencia'] = pd.NaT
                        despesas_sem_parc_pendentes['Data_Vencimento_Original'] = despesas_sem_parc_pendentes['Data_Vencimento']
                        # Consolidando despesas sem parcelamento
                        despesas_sem_parc_pendentes['Valor_Projetado'] = despesas_sem_parc_pendentes['Valor'].astype(float)
                        despesas_sem_parc_pendentes['Tipo_Projecao'] = 'Lançamentos'
                        
                        # Filtrar apenas despesas dentro do período selecionado
                        despesas_sem_parc_futuras = despesas_sem_parc_pendentes[
                            (despesas_sem_parc_pendentes['Data_Projecao'] >= data_futura_inicio) &
                            (despesas_sem_parc_pendentes['Data_Projecao'] <= data_futura_fim)
                        ]
                        
                        # Processando despesas com parcelamento
                        if not despesas_com_parc_pendentes.empty:
                            # Usar Previsao_Parcela se disponível, senão Vencimento_Parcela (mantendo o dia exato)
                            despesas_com_parc_pendentes['Data_Projecao'] = despesas_com_parc_pendentes['Previsao_Parcela'].fillna(
                                despesas_com_parc_pendentes['Vencimento_Parcela']
                            )
                            # Adicionando colunas de data de competência e vencimento original
                            if 'Data_Competencia' in despesas_com_parc_pendentes.columns:
                                despesas_com_parc_pendentes['Data_Competencia'] = despesas_com_parc_pendentes['Data_Competencia']
                            else:
                                despesas_com_parc_pendentes['Data_Competencia'] = despesas_com_parc_pendentes['Vencimento_Parcela']
                            despesas_com_parc_pendentes['Data_Vencimento_Original'] = despesas_com_parc_pendentes['Vencimento_Parcela']
                            despesas_com_parc_pendentes['Valor_Projetado'] = despesas_com_parc_pendentes['Valor_Parcela'].astype(float)
                            despesas_com_parc_pendentes['Tipo_Projecao'] = 'Lançamentos'
                            
                            # Filtrar apenas despesas dentro do período selecionado
                            despesas_com_parc_futuras = despesas_com_parc_pendentes[
                                (despesas_com_parc_pendentes['Data_Projecao'] >= data_futura_inicio) &
                                (despesas_com_parc_pendentes['Data_Projecao'] <= data_futura_fim)
                            ]
                            
                            # Consolidando todas as despesas de lançamentos
                            if not despesas_sem_parc_futuras.empty or not despesas_com_parc_futuras.empty:
                                todas_despesas_lancamentos = pd.concat([
                                    despesas_sem_parc_futuras, 
                                    despesas_com_parc_futuras
                                ], ignore_index=True)
                                
                                projecoes_por_tipo.append(todas_despesas_lancamentos)
                                total_lancamentos = todas_despesas_lancamentos['Valor_Projetado'].sum()
                                st.write(f"Total de despesas pendentes (consolidadas): R$ {total_lancamentos:,.2f}")
                        else:
                            # Apenas despesas sem parcelamento
                            if not despesas_sem_parc_futuras.empty:
                                projecoes_por_tipo.append(despesas_sem_parc_futuras)
                                total_sem_parc = despesas_sem_parc_futuras['Valor_Projetado'].sum()
                                st.write(f"Total de despesas pendentes: R$ {total_sem_parc:,.2f}")
                    else:
                        st.write("Nenhuma despesa pendente encontrada para as classificações 'Considerar Lançamentos'.")
                
                # Removendo seção de Faturamento - já tratado em outra seção
                
                st.write("---")
            
            # Consolidando todas as projeções
            if projecoes_por_tipo:
                df_projecoes_consolidadas = pd.concat(projecoes_por_tipo, ignore_index=True)
                
                # Padronizando a coluna de data para agrupamento por mês
                # Para orçamentos, usar Data_Orcamento; para lançamentos, usar Data_Projecao
                df_projecoes_consolidadas['Data_Agrupamento'] = df_projecoes_consolidadas['Data_Orcamento'].fillna(
                    df_projecoes_consolidadas['Data_Projecao']
                )
                
                # Agrupando por mês
                df_projecoes_consolidadas['Mes_Ano'] = df_projecoes_consolidadas['Data_Agrupamento'].dt.strftime('%m/%Y')
                
                # Adicionando coluna Ano_Mes_Projecao baseada na Data_Projecao para facilitar filtros
                df_projecoes_consolidadas['Ano_Mes_Projecao'] = df_projecoes_consolidadas['Data_Projecao'].dt.strftime('%Y-%m')
                
                projecoes_mensais_consolidadas = df_projecoes_consolidadas.groupby(['Mes_Ano', 'Tipo_Projecao'])['Valor_Projetado'].sum().reset_index()
                
                # Criando gráfico consolidado
                fig_projecao_consolidada = go.Figure()
                
                # Calculando totais por mês para os rótulos
                totais_por_mes = projecoes_mensais_consolidadas.groupby('Mes_Ano')['Valor_Projetado'].sum()
                
                # Formatando as datas para exibição no eixo X (mês/ano)
                projecoes_mensais_consolidadas['Mes_Ano_Display'] = projecoes_mensais_consolidadas['Mes_Ano']
                totais_por_mes_display = totais_por_mes.copy()
                totais_por_mes_display.index = totais_por_mes_display.index
                
                for tipo in projecoes_mensais_consolidadas['Tipo_Projecao'].unique():
                    dados_tipo = projecoes_mensais_consolidadas[projecoes_mensais_consolidadas['Tipo_Projecao'] == tipo]
                    fig_projecao_consolidada.add_trace(go.Bar(
                        x=dados_tipo['Mes_Ano_Display'],
                        y=dados_tipo['Valor_Projetado'],
                        name=tipo,
                        text=[f'R$ {valor:,.0f}' for valor in dados_tipo['Valor_Projetado']],
                        textposition='auto'
                    ))
                
                # Adicionando rótulos com totais no topo das barras
                fig_projecao_consolidada.add_trace(go.Scatter(
                    x=totais_por_mes_display.index,
                    y=totais_por_mes_display.values,
                    mode='text',
                    text=[f'Total: R$ {valor:,.0f}' for valor in totais_por_mes_display.values],
                    textposition='top center',
                    textfont=dict(size=12, color='white'),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig_projecao_consolidada.update_layout(
                    title='Projeção de Despesas Futuras por Tipo de Fluxo',
                    xaxis_title="Mês/Ano",
                    yaxis_title="Valor (R$)",
                    height=500,
                    barmode='stack'
                )
                
                fig_projecao_consolidada.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
                
                st.plotly_chart(fig_projecao_consolidada, use_container_width=True)
                
                # ===== TABELA DETALHADA POR CLASS_CONT_1 E MÊS =====
                st.subheader("📋 Detalhamento por Classificação Contábil e Mês")
                
                # Preparando dados para a tabela detalhada
                if not df_projecoes_consolidadas.empty:
                    # Agrupando por Class_Cont_1, mês e tipo de projeção
                    df_detalhado = df_projecoes_consolidadas.groupby([
                        'Class_Cont_1', 
                        'Mes_Ano', 
                        'Tipo_Projecao'
                    ])['Valor_Projetado'].sum().reset_index()
                    
                    # Criando tabela pivot
                    pivot_detalhado = df_detalhado.pivot_table(
                        index=['Class_Cont_1', 'Tipo_Projecao'],
                        columns='Mes_Ano',
                        values='Valor_Projetado',
                        aggfunc='sum'
                    ).fillna(0)
                    
                    # Adicionando coluna de total
                    pivot_detalhado['Total'] = pivot_detalhado.sum(axis=1)
                    
                    # Resetando índice para incluir Class_Cont_1 e Tipo_Projecao como colunas
                    pivot_detalhado = pivot_detalhado.reset_index()
                    
                    # Renomeando colunas para melhor visualização (antes da ordenação)
                    pivot_detalhado = pivot_detalhado.rename(columns={
                        'Class_Cont_1': 'Classificação Contábil',
                        'Tipo_Projecao': 'Tipo de Fluxo Futuro'
                    })
                    
                    # Ordenando por tipo de fluxo e ordem personalizada
                    # Definindo ordem de prioridade: Variável > Fixo > Lançamentos
                    ordem_tipos = {'Variável': 1, 'Fixo': 2, 'Lançamentos': 3}
                    
                    # Definindo ordem personalizada para classificações variáveis
                    ordem_classificacoes_variavel = {
                        'Deduções sobre Venda': 1,
                        'Gorjeta': 2,
                        'Custo Mercadoria Vendida': 3,
                        'Mão de Obra - Extra': 4
                    }
                    
                    # Criando colunas de ordenação
                    pivot_detalhado['Ordem_Tipo'] = pivot_detalhado['Tipo de Fluxo Futuro'].map(ordem_tipos)
                    pivot_detalhado['Ordem_Classificacao'] = pivot_detalhado['Classificação Contábil'].map(ordem_classificacoes_variavel).fillna(999)
                    
                    # Ordenando primeiro por tipo de fluxo, depois por ordem personalizada, depois por total
                    pivot_detalhado = pivot_detalhado.sort_values(['Ordem_Tipo', 'Ordem_Classificacao', 'Total'], ascending=[True, True, False])
                    
                    # Removendo colunas auxiliares de ordenação
                    pivot_detalhado = pivot_detalhado.drop(['Ordem_Tipo', 'Ordem_Classificacao'], axis=1)
                    
                    # Separando colunas numéricas das de texto
                    colunas_texto = ['Classificação Contábil', 'Tipo de Fluxo Futuro']
                    colunas_numericas = [col for col in pivot_detalhado.columns if col not in colunas_texto]
                    
                    # Exibindo tabela detalhada
                    df_detalhado_aggrid = component_plotDataframe_aggrid(
                        df=pivot_detalhado,
                        name="Detalhamento por Classificação e Mês",
                        num_columns=colunas_numericas,
                        percent_columns=[],
                        df_details=None,
                        coluns_merge_details=None,
                        coluns_name_details=None
                    )
                    
                    function_copy_dataframe_as_tsv(df_detalhado_aggrid)
                    
                    # ===== TABELA DETALHADA DE LANÇAMENTOS =====
                    st.subheader("📋 Detalhamento das Despesas - Tipo 'Lançamentos'")
                    
                    # Filtrando apenas despesas do tipo "Lançamentos" das projeções consolidadas
                    if not df_projecoes_consolidadas.empty:
                        lancamentos_detalhados = df_projecoes_consolidadas[
                            df_projecoes_consolidadas['Tipo_Projecao'] == 'Lançamentos'
                        ].copy()
                        
                        if not lancamentos_detalhados.empty:
                            # Selecionando colunas relevantes para exibição na ordem desejada
                            colunas_exibicao = []
                            
                            # Verificando quais colunas existem no dataframe e adicionando na ordem específica
                            if 'ID_Despesa' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('ID_Despesa')
                            if 'ID_Parcela' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('ID_Parcela')
                            if 'Casa' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Casa')
                            if 'Descricao' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Descricao')
                            if 'Fornecedor' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Fornecedor')
                            if 'Class_Cont_1' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Class_Cont_1')
                            if 'Class_Cont_2' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Class_Cont_2')
                            if 'Valor_Projetado' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Valor_Projetado')
                            if 'Data_Competencia' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Data_Competencia')
                            if 'Data_Vencimento_Original' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Data_Vencimento_Original')
                            if 'Data_Projecao' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Data_Projecao')
                            if 'Ano_Mes_Projecao' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Ano_Mes_Projecao')
                            if 'Status_Pgto' in lancamentos_detalhados.columns:
                                colunas_exibicao.append('Status_Pgto')
                            
                            # Garantindo que temos pelo menos as colunas essenciais
                            if not colunas_exibicao:
                                colunas_exibicao = ['Valor_Projetado', 'Data_Projecao']
                            
                            # Preparando dataframe para exibição
                            df_lancamentos_exibicao = lancamentos_detalhados[colunas_exibicao].copy()
                            
                            # Ordenando por data de projeção e valor
                            if 'Data_Projecao' in df_lancamentos_exibicao.columns:
                                df_lancamentos_exibicao = df_lancamentos_exibicao.sort_values(['Data_Projecao', 'Valor_Projetado'], ascending=[True, False])
                            
                            # Formatando datas para exibição
                            if 'Data_Competencia' in df_lancamentos_exibicao.columns:
                                df_lancamentos_exibicao['Data_Competencia'] = df_lancamentos_exibicao['Data_Competencia'].dt.strftime('%d/%m/%Y').fillna('N/A')
                            if 'Data_Vencimento_Original' in df_lancamentos_exibicao.columns:
                                df_lancamentos_exibicao['Data_Vencimento_Original'] = df_lancamentos_exibicao['Data_Vencimento_Original'].dt.strftime('%d/%m/%Y').fillna('N/A')
                            if 'Data_Projecao' in df_lancamentos_exibicao.columns:
                                df_lancamentos_exibicao['Data_Projecao'] = df_lancamentos_exibicao['Data_Projecao'].dt.strftime('%d/%m/%Y').fillna('N/A')
                            
                            # Renomeando colunas para melhor visualização
                            mapeamento_colunas = {
                                'ID_Despesa': 'ID Despesa',
                                'ID_Parcela': 'ID Parcela', 
                                'Descricao': 'Descrição',
                                'Fornecedor': 'Fornecedor',
                                'Class_Cont_1': 'Classificação 1',
                                'Class_Cont_2': 'Classificação 2',
                                'Data_Competencia': 'Data Competência',
                                'Data_Vencimento_Original': 'Data Vencimento Original',
                                'Data_Projecao': 'Data Projeção',
                                'Ano_Mes_Projecao': 'Ano/Mês Projeção',
                                'Status_Pgto': 'Status Pagamento',
                                'Valor_Projetado': 'Valor (R$)',
                                'Casa': 'Casa'
                            }
                            
                            df_lancamentos_exibicao = df_lancamentos_exibicao.rename(columns=mapeamento_colunas)
                            
                            # Exibindo tabela detalhada
                            df_lancamentos_aggrid = component_plotDataframe_aggrid(
                                df=df_lancamentos_exibicao,
                                name="Detalhamento de Lançamentos",
                                num_columns=["Valor (R$)"],
                                percent_columns=[],
                                df_details=None,
                                coluns_merge_details=None,
                                coluns_name_details=None
                            )
                            
                            # Calculando total dos valores filtrados
                            if not df_lancamentos_aggrid.empty and "Valor (R$)" in df_lancamentos_aggrid.columns:
                                # Convertendo valores para numérico se necessário
                                valores_filtrados = pd.to_numeric(df_lancamentos_aggrid["Valor (R$)"], errors='coerce')
                                total_filtrado = valores_filtrados.sum()
                                
                                # Exibindo total formatado
                                st.markdown(f"""
                                <div style="
                                    background-color: #1e1e1e; 
                                    border: 1px solid #ffb131; 
                                    border-radius: 4px; 
                                    padding: 8px 12px; 
                                    margin: 5px 0; 
                                    text-align: center;
                                    display: inline-block;
                                ">
                                    <span style="color: #ffb131; font-weight: bold;">💰 Total: R$ {total_filtrado:,.2f}</span>
                                    <span style="color: #cccccc; margin-left: 10px;">({len(df_lancamentos_aggrid)} registros)</span>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            function_copy_dataframe_as_tsv(df_lancamentos_aggrid)
                            
                        else:
                            st.info("Não há despesas do tipo 'Lançamentos' para exibir.")
                    else:
                        st.warning("Não há dados de projeções consolidadas disponíveis.")
                    
                    # Informações adicionais da tabela detalhada
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        total_classificacoes = len(pivot_detalhado['Classificação Contábil'].unique())
                        st.metric("Total de Classificações", total_classificacoes)
                    
                    with col2:
                        total_meses = len(colunas_numericas) - 1  # Excluindo a coluna 'Total'
                        st.metric("Período de Projeção", f"{total_meses} meses")
                    
                else:
                    st.warning("Não há dados disponíveis para gerar a tabela detalhada.")
            else:
                st.warning("Nenhuma projeção encontrada para os tipos de fluxo configurados.")
        else:
            st.warning("Não há orçamentos futuros disponíveis para projeção por tipo de fluxo.")
    
    else:
        st.warning("Dados insuficientes para análise comparativa. Verifique se há dados de orçamento e faturamento realizado nos últimos 6 meses.")

    # Gráfico de Projeção Avançada por Mês - Receitas vs Despesas
    st.subheader("📊 Projeção Avançada por Mês - Receitas vs Despesas")
    
    # Verificando se temos dados de projeção disponíveis
    if 'df_projecoes_consolidadas' in locals() and not df_projecoes_consolidadas.empty:
        # Usando os dados de projeção consolidados
        st.info("📈 Utilizando projeções baseadas nos tipos de fluxo futuro configurados")
        
        # Verificando se patrocinios_mensais está definida
        if 'patrocinios_mensais' not in locals():
            patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
        
        # Separando receitas e despesas das projeções
        receitas_projetadas = df_orcamentos_futuros.copy() if 'df_orcamentos_futuros' in locals() and not df_orcamentos_futuros.empty else pd.DataFrame()
        despesas_projetadas = df_projecoes_consolidadas.copy()
        
        # Verificando se df_orcamentos_futuros está definida
        if 'df_orcamentos_futuros' not in locals():
            df_orcamentos_futuros = pd.DataFrame()
        
        # Preparando dados de receitas projetadas (orçamento + patrocínios)
        receitas_consolidadas = []
        
        # Receitas do orçamento
        if not receitas_projetadas.empty:
            receitas_projetadas['Mes_Ano'] = receitas_projetadas['Data_Orcamento'].dt.strftime('%m/%Y')
            receitas_orcamento = receitas_projetadas.groupby('Mes_Ano')['Valor_Projetado'].sum().reset_index()
            receitas_orcamento['Tipo'] = 'Receitas Orçamento'
            receitas_orcamento = receitas_orcamento.rename(columns={'Valor_Projetado': 'Valor'})
            receitas_consolidadas.append(receitas_orcamento)
        
        # Receitas de patrocínios
        if not patrocinios_mensais.empty:
            patrocinios_para_receitas = patrocinios_mensais[['Mes_Ano', 'Valor_Parcela']].copy()
            patrocinios_para_receitas['Tipo'] = 'Receitas Patrocínios'
            patrocinios_para_receitas = patrocinios_para_receitas.rename(columns={'Valor_Parcela': 'Valor'})
            receitas_consolidadas.append(patrocinios_para_receitas)
        
        # Combinando todas as receitas
        if receitas_consolidadas:
            receitas_mensais = pd.concat(receitas_consolidadas, ignore_index=True)
        else:
            receitas_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor', 'Tipo'])
        
        # Preparando dados de despesas projetadas
        if not despesas_projetadas.empty:
            despesas_mensais = despesas_projetadas.groupby('Mes_Ano')['Valor_Projetado'].sum().reset_index()
            despesas_mensais['Tipo'] = 'Despesas Projetadas'
            despesas_mensais = despesas_mensais.rename(columns={'Valor_Projetado': 'Valor'})
        else:
            despesas_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor', 'Tipo'])
        
        # Combinando dados
        projecao_mensal = pd.concat([receitas_mensais, despesas_mensais], ignore_index=True)
        
        if not projecao_mensal.empty:
            # Ordenando por data
            projecao_mensal = projecao_mensal.sort_values('Mes_Ano')
            
            # Formatando data para exibição
            projecao_mensal['Mes_Ano_Display'] = projecao_mensal['Mes_Ano']
            
            # Criando gráfico
            fig_projecao_mensal = go.Figure()
            
            # Combinando receitas em uma única barra
            receitas_orcamento_data = projecao_mensal[projecao_mensal['Tipo'] == 'Receitas Orçamento']
            receitas_patrocinios_data = projecao_mensal[projecao_mensal['Tipo'] == 'Receitas Patrocínios']
            
            # Criando DataFrame com receitas consolidadas
            receitas_consolidadas_grafico = []
            
            # Obtendo todos os meses únicos
            todos_meses = sorted(projecao_mensal['Mes_Ano_Display'].unique())
            
            for mes in todos_meses:
                # Receitas do orçamento para este mês
                valor_orcamento = receitas_orcamento_data[receitas_orcamento_data['Mes_Ano_Display'] == mes]['Valor'].sum() if not receitas_orcamento_data.empty else 0
                
                # Receitas de patrocínios para este mês
                valor_patrocinios = receitas_patrocinios_data[receitas_patrocinios_data['Mes_Ano_Display'] == mes]['Valor'].sum() if not receitas_patrocinios_data.empty else 0
                
                # Total de receitas para este mês
                valor_total_receitas = valor_orcamento + valor_patrocinios
                
                if valor_total_receitas > 0:
                    receitas_consolidadas_grafico.append({
                        'Mes_Ano_Display': mes,
                        'Valor': valor_total_receitas,
                        'Valor_Orcamento': valor_orcamento,
                        'Valor_Patrocinios': valor_patrocinios
                    })
            
            # Criando DataFrame de receitas consolidadas
            df_receitas_consolidadas = pd.DataFrame(receitas_consolidadas_grafico)
            
            # Adicionando barra de receitas consolidadas (verde)
            if not df_receitas_consolidadas.empty:
                fig_projecao_mensal.add_trace(go.Bar(
                    x=df_receitas_consolidadas['Mes_Ano_Display'],
                    y=df_receitas_consolidadas['Valor'],
                    name='Receitas Totais (Orçamento + Patrocínios)',
                    marker_color='#2E8B57',
                    text=[f'R$ {valor:,.0f}' for valor in df_receitas_consolidadas['Valor']],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>' +
                                  'Receitas Totais: R$ %{y:,.2f}<br>' +
                                  'Orçamento: R$ %{customdata[0]:,.2f}<br>' +
                                  'Patrocínios: R$ %{customdata[1]:,.2f}<br>' +
                                  '<extra></extra>',
                    customdata=df_receitas_consolidadas[['Valor_Orcamento', 'Valor_Patrocinios']].values
                ))
            
            # Despesas projetadas (vermelho)
            despesas_data = projecao_mensal[projecao_mensal['Tipo'] == 'Despesas Projetadas']
            if not despesas_data.empty:
                fig_projecao_mensal.add_trace(go.Bar(
                    x=despesas_data['Mes_Ano_Display'],
                    y=despesas_data['Valor'],
                    name='Despesas Projetadas',
                    marker_color='#DC143C',
                    text=[f'R$ {valor:,.0f}' for valor in despesas_data['Valor']],
                    textposition='auto'
                ))
            
            # Configurando layout
            fig_projecao_mensal.update_layout(
                title=f'Projeção Avançada por Mês - {", ".join(casas_selecionadas)} (Baseada em Tipos de Fluxo)',
                xaxis_title="Mês/Ano",
                yaxis_title="Valor Projetado (R$)",
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                ),
                barmode='group'
            )
            
            fig_projecao_mensal.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
            
            st.plotly_chart(fig_projecao_mensal, use_container_width=True)
            
            # Métricas resumidas da projeção
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_receitas_proj = df_receitas_consolidadas['Valor'].sum() if not df_receitas_consolidadas.empty else 0
                st.metric("Total Receitas Projetadas", f"R$ {total_receitas_proj:,.2f}")
            
            with col2:
                total_despesas_proj = despesas_data['Valor'].sum() if not despesas_data.empty else 0
                st.metric("Total Despesas Projetadas", f"R$ {total_despesas_proj:,.2f}")
            
            with col3:
                saldo_projetado = total_receitas_proj - total_despesas_proj
                st.metric("Saldo Projetado", f"R$ {saldo_projetado:,.2f}")
            
            with col4:
                if total_receitas_proj > 0:
                    margem_projetada = (saldo_projetado / total_receitas_proj) * 100
                    st.metric("Margem Projetada (%)", f"{margem_projetada:.1f}%")
                else:
                    st.metric("Margem Projetada (%)", "N/A")
            
            # Métricas detalhadas das receitas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_receitas_orcamento = df_receitas_consolidadas['Valor_Orcamento'].sum() if not df_receitas_consolidadas.empty else 0
                st.metric("Receitas Orçamento", f"R$ {total_receitas_orcamento:,.2f}")
            
            with col2:
                total_receitas_patrocinios = df_receitas_consolidadas['Valor_Patrocinios'].sum() if not df_receitas_consolidadas.empty else 0
                st.metric("Receitas Patrocínios", f"R$ {total_receitas_patrocinios:,.2f}")
            
            with col3:
                if total_receitas_proj > 0:
                    percentual_patrocinios = (total_receitas_patrocinios / total_receitas_proj) * 100
                    st.metric("Patrocínios/Total (%)", f"{percentual_patrocinios:.1f}%")
                else:
                    st.metric("Patrocínios/Total (%)", "N/A")
            
            # Tabela resumida da projeção
            st.subheader("📋 Resumo da Projeção Avançada por Mês")
            
            # Criando tabela pivot usando os dados consolidadas
            if not df_receitas_consolidadas.empty:
                # Criando DataFrame para a tabela
                tabela_projecao = df_receitas_consolidadas[['Mes_Ano_Display', 'Valor_Orcamento', 'Valor_Patrocinios', 'Valor']].copy()
                tabela_projecao = tabela_projecao.rename(columns={
                    'Valor_Orcamento': 'Receitas Orçamento',
                    'Valor_Patrocinios': 'Receitas Patrocínios',
                    'Valor': 'Receitas Total'
                })
                
                # Adicionando despesas projetadas
                if not despesas_data.empty:
                    despesas_tabela = despesas_data[['Mes_Ano_Display', 'Valor']].copy()
                    despesas_tabela = despesas_tabela.rename(columns={'Valor': 'Despesas Projetadas'})
                    
                    # Merge das receitas com despesas
                    tabela_projecao = pd.merge(tabela_projecao, despesas_tabela, on='Mes_Ano_Display', how='left').fillna(0)
                else:
                    tabela_projecao['Despesas Projetadas'] = 0
                
                # Calculando saldo
                tabela_projecao['Saldo'] = tabela_projecao['Receitas Total'] - tabela_projecao['Despesas Projetadas']
                
                # Reordenando colunas
                colunas_ordenadas = ['Mes_Ano_Display', 'Receitas Orçamento', 'Receitas Patrocínios', 'Receitas Total', 'Despesas Projetadas', 'Saldo']
                tabela_projecao = tabela_projecao[colunas_ordenadas]
                
                pivot_projecao = tabela_projecao
            else:
                # Fallback se não houver receitas consolidadas
                pivot_projecao = pd.DataFrame(columns=['Mes_Ano_Display', 'Receitas Orçamento', 'Receitas Patrocínios', 'Receitas Total', 'Despesas Projetadas', 'Saldo'])
            
            # Exibindo tabela
            colunas_numericas = [col for col in pivot_projecao.columns if col != 'Mes_Ano_Display']
            pivot_projecao_aggrid = component_plotDataframe_aggrid(
                df=pivot_projecao,
                name="Resumo da Projeção Avançada Mensal",
                num_columns=colunas_numericas,
                percent_columns=[],
                df_details=None,
                coluns_merge_details=None,
                coluns_name_details=None
            )
            
            function_copy_dataframe_as_tsv(pivot_projecao_aggrid)
            
        else:
            st.warning("Não há dados de projeção para exibir no gráfico.")
    
    else:
        # Fallback para o gráfico original se não houver projeções
        st.info("📊 Exibindo dados básicos do orçamento (sem projeções avançadas)")
        
        if not df_orcamentos_filtrada.empty:
            # Separando receitas e despesas
            receitas_orcamento = df_orcamentos_filtrada[df_orcamentos_filtrada['Class_Cont_1'] == 'Faturamento Bruto'].copy()
            despesas_orcamento = df_orcamentos_filtrada[df_orcamentos_filtrada['Class_Cont_1'] != 'Faturamento Bruto'].copy()
            
            # Agrupando receitas por mês
            if not receitas_orcamento.empty:
                receitas_mensais = receitas_orcamento.groupby('Data_Orcamento')['Valor_Orcamento'].sum().reset_index()
                receitas_mensais['Tipo'] = 'Receitas'
            else:
                receitas_mensais = pd.DataFrame(columns=['Data_Orcamento', 'Valor_Orcamento', 'Tipo'])
            
            # Agrupando despesas por mês
            if not despesas_orcamento.empty:
                despesas_mensais = despesas_orcamento.groupby('Data_Orcamento')['Valor_Orcamento'].sum().reset_index()
                despesas_mensais['Tipo'] = 'Despesas'
            else:
                despesas_mensais = pd.DataFrame(columns=['Data_Orcamento', 'Valor_Orcamento', 'Tipo'])
            
            # Combinando dados
            orcamento_mensal = pd.concat([receitas_mensais, despesas_mensais], ignore_index=True)
            
            if not orcamento_mensal.empty:
                # Ordenando por data
                orcamento_mensal = orcamento_mensal.sort_values('Data_Orcamento')
                
                # Formatando data para exibição
                orcamento_mensal['Mes_Ano'] = orcamento_mensal['Data_Orcamento'].dt.strftime('%m/%Y')
                
                # Criando gráfico
                fig_orcamento_mensal = go.Figure()
                
                # Receitas (verde)
                receitas_data = orcamento_mensal[orcamento_mensal['Tipo'] == 'Receitas']
                if not receitas_data.empty:
                    fig_orcamento_mensal.add_trace(go.Bar(
                        x=receitas_data['Mes_Ano'],
                        y=receitas_data['Valor_Orcamento'],
                        name='Receitas',
                        marker_color='#2E8B57',
                        text=[f'R$ {valor:,.0f}' for valor in receitas_data['Valor_Orcamento']],
                        textposition='auto'
                    ))
                
                # Despesas (vermelho)
                despesas_data = orcamento_mensal[orcamento_mensal['Tipo'] == 'Despesas']
                if not despesas_data.empty:
                    fig_orcamento_mensal.add_trace(go.Bar(
                        x=despesas_data['Mes_Ano'],
                        y=despesas_data['Valor_Orcamento'],
                        name='Despesas',
                        marker_color='#DC143C',
                        text=[f'R$ {valor:,.0f}' for valor in despesas_data['Valor_Orcamento']],
                        textposition='auto'
                    ))
                
                # Configurando layout
                fig_orcamento_mensal.update_layout(
                    title=f'Orçamento por Mês - {", ".join(casas_selecionadas)}',
                    xaxis_title="Mês/Ano",
                    yaxis_title="Valor Orçado (R$)",
                    height=500,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    ),
                    barmode='group'
                )
                
                fig_orcamento_mensal.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
                
                st.plotly_chart(fig_orcamento_mensal, use_container_width=True)
                
                # Métricas resumidas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_receitas = receitas_orcamento['Valor_Orcamento'].sum() if not receitas_orcamento.empty else 0
                    st.metric("Total Receitas Orçadas", f"R$ {total_receitas:,.2f}")
                
                with col2:
                    total_despesas = despesas_orcamento['Valor_Orcamento'].sum() if not despesas_orcamento.empty else 0
                    st.metric("Total Despesas Orçadas", f"R$ {total_despesas:,.2f}")
                
                with col3:
                    saldo_orcado = total_receitas - total_despesas
                    st.metric("Saldo Orçado", f"R$ {saldo_orcado:,.2f}")
                
                with col4:
                    if total_receitas > 0:
                        margem_orcada = (saldo_orcado / total_receitas) * 100
                        st.metric("Margem Orçada (%)", f"{margem_orcada:.1f}%")
                    else:
                        st.metric("Margem Orçada (%)", "N/A")
                
                # Tabela resumida
                st.subheader("📋 Resumo Orçamentário por Mês")
                
                # Criando tabela pivot
                pivot_orcamento = orcamento_mensal.pivot(
                    index='Mes_Ano',
                    columns='Tipo',
                    values='Valor_Orcamento'
                ).fillna(0)
                
                # Adicionando coluna de saldo - convertendo para float para evitar problemas com Decimal
                pivot_orcamento['Saldo'] = float(pivot_orcamento.get('Receitas', 0)) - float(pivot_orcamento.get('Despesas', 0))
                
                # Resetando índice
                pivot_orcamento = pivot_orcamento.reset_index()
                
                # Reordenando colunas: Receitas, Despesas, Saldo
                colunas_ordenadas = ['Mes_Ano', 'Receitas', 'Despesas', 'Saldo']
                pivot_orcamento = pivot_orcamento[colunas_ordenadas]
                
                # Exibindo tabela
                pivot_orcamento_aggrid = component_plotDataframe_aggrid(
                    df=pivot_orcamento,
                    name="Resumo Orçamentário Mensal",
                    num_columns=["Receitas", "Despesas", "Saldo"],
                    percent_columns=[],
                    df_details=None,
                    coluns_merge_details=None,
                    coluns_name_details=None
                )
                
                function_copy_dataframe_as_tsv(pivot_orcamento_aggrid)
                
            else:
                st.warning("Não há dados de orçamento para exibir no gráfico.")
        else:
            st.warning("Não há dados de orçamento disponíveis para as casas selecionadas.")

    # ===== TABELA DE FATORES DE AJUSTE POR CASA =====
    st.subheader("📊 Fatores de Ajuste por Casa")
    st.markdown("**Análise de Performance: Orçado vs Realizado**")
    
    # Mostrando o período usado para análise
    if 'fator_ajuste_date_input' in st.session_state:
        fator_data = st.session_state['fator_ajuste_date_input']
        if isinstance(fator_data, tuple):
            if len(fator_data) >= 2:
                periodo_analise_fatores = f"{fator_data[0].strftime('%d/%m/%Y')} a {fator_data[1].strftime('%d/%m/%Y')}"
            elif len(fator_data) == 1:
                periodo_analise_fatores = fator_data[0].strftime('%d/%m/%Y')
            else:
                periodo_analise_fatores = "Período não definido"
        else:
            periodo_analise_fatores = fator_data.strftime('%d/%m/%Y')
        st.info(f"📅 **Período de análise**: {periodo_analise_fatores}")
    
    # Calculando fatores de ajuste por casa individual
    fatores_por_casa = []
    
    for casa in casas_selecionadas:
        casa_id = mapeamento_lojas[casa]
        
        # Filtrando dados de orçamento para esta casa usando o filtro de data personalizado
        if 'fator_ajuste_date_input' not in st.session_state:
            hoje = datetime.datetime.now()
            data_limite_analise_casa = hoje.replace(day=1) - timedelta(days=1)  # Último dia do mês anterior
            data_inicio_analise_casa = data_limite_analise_casa.replace(day=1) - timedelta(days=180)  # 6 meses atrás
        else:
            fator_data = st.session_state['fator_ajuste_date_input']
            if isinstance(fator_data, tuple):
                data_inicio_analise_casa = pd.to_datetime(fator_data[0])
                if len(fator_data) >= 2:
                    data_limite_analise_casa = pd.to_datetime(fator_data[1])
                else:
                    data_limite_analise_casa = data_inicio_analise_casa  # Se só tem uma data, usar a mesma
            else:
                data_inicio_analise_casa = pd.to_datetime(fator_data)
                data_limite_analise_casa = pd.to_datetime(fator_data)
        
        df_orcamentos_casa = df_orcamentos[
            (df_orcamentos['ID_Casa'] == casa_id) &
            (df_orcamentos['Data_Orcamento'] >= data_inicio_analise_casa) &
            (df_orcamentos['Data_Orcamento'] <= data_limite_analise_casa) &
            (df_orcamentos['Class_Cont_1'] == 'Faturamento Bruto')
        ]
        
        # Filtrando dados de faturamento para esta casa
        df_faturamento_casa = df_faturamento_agregado[
            (df_faturamento_agregado['ID_Casa'] == casa_id)
        ]
        
        if not df_orcamentos_casa.empty and not df_faturamento_casa.empty:
            # Agrupando orçamentos por mês para esta casa
            orcamentos_casa_mensais = df_orcamentos_casa.groupby(['Ano_Orcamento', 'Mes_Orcamento'])['Valor_Orcamento'].sum().reset_index()
            orcamentos_casa_mensais['Data_Comparacao'] = pd.to_datetime(
                orcamentos_casa_mensais['Ano_Orcamento'].astype(str) + '-' + 
                orcamentos_casa_mensais['Mes_Orcamento'].astype(str).str.zfill(2) + '-01'
            )
            
            # Agrupando faturamento por mês para esta casa
            faturamento_casa_mensais = df_faturamento_casa.groupby('Ano_Mes')['Valor_Bruto'].sum().reset_index()
            faturamento_casa_mensais['Data_Comparacao'] = pd.to_datetime(
                faturamento_casa_mensais['Ano_Mes'] + '-01'
            )
            
            # Merge dos dados para comparação desta casa
            df_comparacao_casa = pd.merge(
                orcamentos_casa_mensais[['Data_Comparacao', 'Valor_Orcamento']],
                faturamento_casa_mensais[['Data_Comparacao', 'Valor_Bruto']],
                on='Data_Comparacao',
                how='outer'
            ).fillna(0)
            
            # Calculando percentual realizado para esta casa
            df_comparacao_casa['Percentual_Realizado'] = df_comparacao_casa.apply(
                lambda row: (row['Valor_Bruto'] / row['Valor_Orcamento'] * 100) if row['Valor_Orcamento'] != 0 else 0, 
                axis=1
            ).fillna(0)
            
            # Calculando métricas para esta casa
            total_orcado_casa = df_comparacao_casa['Valor_Orcamento'].sum()
            total_realizado_casa = df_comparacao_casa['Valor_Bruto'].sum()
            percentual_medio_casa = df_comparacao_casa['Percentual_Realizado'].mean()
            
            # Calculando fator de ajuste para esta casa
            if percentual_medio_casa > 0:
                fator_ajuste_casa = min(percentual_medio_casa / 100, 1.0)
            else:
                fator_ajuste_casa = 1.0
            
            # Classificando performance
            if percentual_medio_casa >= 110:
                classificacao = "🟢 Excelente"
                cor_classificacao = "green"
            elif percentual_medio_casa >= 100:
                classificacao = "🟡 Boa"
                cor_classificacao = "orange"
            elif percentual_medio_casa >= 90:
                classificacao = "🟠 Atenção"
                cor_classificacao = "red"
            else:
                classificacao = "🔴 Crítica"
                cor_classificacao = "darkred"
            
            # Adicionando à lista de fatores
            fatores_por_casa.append({
                'Casa': casa,
                'Total_Orcado': total_orcado_casa,
                'Total_Realizado': total_realizado_casa,
                'Percentual_Realizado': percentual_medio_casa,
                'Fator_Ajuste': fator_ajuste_casa,
                'Classificacao': classificacao,
                'Meses_Analisados': len(df_comparacao_casa)
            })
        else:
            # Caso não haja dados suficientes
            fatores_por_casa.append({
                'Casa': casa,
                'Total_Orcado': 0,
                'Total_Realizado': 0,
                'Percentual_Realizado': 0,
                'Fator_Ajuste': 1.0,
                'Classificacao': "⚪ Sem dados",
                'Meses_Analisados': 0
            })
    
    # Criando DataFrame com os fatores
    df_fatores_ajuste = pd.DataFrame(fatores_por_casa)
    
    if not df_fatores_ajuste.empty:
        # Formatando colunas para exibição
        df_fatores_display = df_fatores_ajuste.copy()
        df_fatores_display['Total_Orcado'] = df_fatores_display['Total_Orcado'].apply(lambda x: f"R$ {x:,.2f}")
        df_fatores_display['Total_Realizado'] = df_fatores_display['Total_Realizado'].apply(lambda x: f"R$ {x:,.2f}")
        df_fatores_display['Percentual_Realizado'] = df_fatores_display['Percentual_Realizado'].apply(lambda x: f"{x:.1f}%")
        df_fatores_display['Fator_Ajuste'] = df_fatores_display['Fator_Ajuste'].apply(lambda x: f"{x:.3f}")
        
        # Renomeando colunas
        df_fatores_display.columns = [
            'Casa', 
            'Total Orçado', 
            'Total Realizado', 
            'Realizado/Orçado (%)', 
            'Fator de Ajuste', 
            'Classificação', 
            'Meses Analisados'
        ]
        
        # Exibindo tabela
        st.markdown("**📋 Resumo dos Fatores de Ajuste por Casa**")
        st.caption(f"Período de análise: {data_inicio_analise.strftime('%d/%m/%Y')} a {data_limite_analise.strftime('%d/%m/%Y')}")
        
        fatores_aggrid = component_plotDataframe_aggrid(
            df=df_fatores_display,
            name="Fatores de Ajuste por Casa",
            num_columns=["Total Orçado", "Total Realizado"],
            percent_columns=["Realizado/Orçado (%)"],
            df_details=None,
            coluns_merge_details=None,
            coluns_name_details=None
        )
        
        function_copy_dataframe_as_tsv(fatores_aggrid)
        
        # Métricas resumidas
        st.markdown("**📊 Métricas Gerais**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            media_percentual = df_fatores_ajuste['Percentual_Realizado'].mean()
            st.metric("Média Realizado/Orçado", f"{media_percentual:.1f}%")
        
        with col2:
            media_fator = df_fatores_ajuste['Fator_Ajuste'].mean()
            st.metric("Fator de Ajuste Médio", f"{media_fator:.3f}")
        
        with col3:
            casas_excelentes = len(df_fatores_ajuste[df_fatores_ajuste['Percentual_Realizado'] >= 110])
            total_casas = len(df_fatores_ajuste)
            st.metric("Casas Excelentes", f"{casas_excelentes}/{total_casas}")
        
        with col4:
            casas_criticas = len(df_fatores_ajuste[df_fatores_ajuste['Percentual_Realizado'] < 90])
            st.metric("Casas Críticas", f"{casas_criticas}/{total_casas}")
        
        # Legenda das classificações
        st.markdown("**📝 Legenda das Classificações:**")
        st.markdown("""
        - 🟢 **Excelente**: Realizado ≥ 110% do orçado
        - 🟡 **Boa**: Realizado entre 100% e 109% do orçado  
        - 🟠 **Atenção**: Realizado entre 90% e 99% do orçado
        - 🔴 **Crítica**: Realizado < 90% do orçado
        - ⚪ **Sem dados**: Dados insuficientes para análise
        """)
        
        # Explicação do fator de ajuste
        st.markdown("**💡 Sobre o Fator de Ajuste:**")
        st.markdown("""
        O fator de ajuste é calculado com base no histórico de realização vs orçamento de cada casa no período selecionado. 
        - **Fator = 1.000**: Casa atingiu 100% ou mais do orçado (projeção otimista mantida)
        - **Fator < 1.000**: Casa realizou menos que 100% do orçado (projeção ajustada para baixo)
        
        Este fator é aplicado nas projeções futuras para tornar as estimativas mais realistas.
        O período histórico usado para o cálculo pode ser configurado na seção "Configuração do Fator de Ajuste".
        """)
    
    else:
        st.warning("Não foi possível calcular os fatores de ajuste para as casas selecionadas.")



