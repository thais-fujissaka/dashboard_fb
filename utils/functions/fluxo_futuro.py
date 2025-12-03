import streamlit as st
import pandas as pd
import datetime
from datetime import timedelta
import plotly.graph_objects as go
from st_aggrid import ColumnsAutoSizeMode
from utils.functions.general_functions_conciliacao import *
from utils.functions.fluxo_realizado import total_valores_filtrados
from utils.components import dataframe_aggrid


def exibe_orcamentos_e_faturamento(
        df_orcamentos, 
        df_faturamento_agregado, df_eventos_faturam_agregado, 
        ids_casas_selecionadas, start_date, end_date):
    
    col1, col2 = st.columns([6, 1])
    with col1:
        st.subheader("Orçamentos")

    # Convertendo Ano_Orcamento e Mes_Orcamento para formato de data
    df_orcamentos['Data_Orcamento'] = pd.to_datetime(
        df_orcamentos['Ano_Orcamento'].astype(str) + '-' + 
        df_orcamentos['Mes_Orcamento'].astype(str).str.zfill(2) + '-01',
        format='%Y-%m-%d',
        errors='coerce'
    )

    # Filtrando por casas selecionadas e período de data
    df_orcamentos = df_orcamentos[df_orcamentos['ID_Casa'].isin(ids_casas_selecionadas)]
    df_orcamentos_filtrada = df_orcamentos[(df_orcamentos['Data_Orcamento'] >= start_date) & (df_orcamentos['Data_Orcamento'] <= end_date)]

    # Selecionando colunas incluindo a nova Data_Orcamento
    df_orcamentos_filtrada = df_orcamentos_filtrada[['ID_Orcamento','ID_Casa','Casa','Class_Cont_1','Class_Cont_2','Ano_Orcamento','Mes_Orcamento','Data_Orcamento','Valor_Orcamento','Tipo_Fluxo_Futuro']]

    # Exibindo tabela de orçamentos
    df_orcamentos_filtrada_aggrid, tam_df_orcamentos_filtrada_aggrid = dataframe_aggrid(
        df=df_orcamentos_filtrada,
        name="Orçamentos",
        num_columns=["Valor_Orcamento"],
        date_columns=['Data_Orcamento']
    )

    with col2:
        function_copy_dataframe_as_tsv(df_orcamentos_filtrada_aggrid)

    st.divider()

    ## Faturamento Agregado
    col1, col2 = st.columns([6, 1])
    with col1:
        st.subheader("Faturamento Agregado")
        
    # Não considerar eventos das receitas extraordinárias a partir de setembro
    df_faturamento_agregado_copia = df_faturamento_agregado.copy()
    df_faturamento_agregado_copia = df_faturamento_agregado_copia[ 
            ~(
                (df_faturamento_agregado_copia["Categoria"].str.lower() == "eventos") &
                (df_faturamento_agregado_copia["Ano"] == 2025) &
                (df_faturamento_agregado_copia["Mes"] >= 9)
            )
    ]

    # Inclui eventos no faturamento agregado
    df_faturamento_com_eventos = pd.concat(
        [df_faturamento_agregado_copia,
        df_eventos_faturam_agregado])

    # Convertendo Ano_Orcamento e Mes_Orcamento para formato de data
    df_faturamento_com_eventos['Data_Faturamento'] = pd.to_datetime(
        df_faturamento_com_eventos['Ano'].astype(str) + '-' + 
        df_faturamento_com_eventos['Mes'].astype(str).str.zfill(2) + '-01',
        format='%Y-%m-%d',
        errors='coerce'
    )

    df_faturamento_com_eventos['Ano_Mes'] = df_faturamento_com_eventos['Ano'].astype(str) + '-' + df_faturamento_com_eventos['Mes'].astype(str).str.zfill(2)
    df_faturamento_com_eventos = df_faturamento_com_eventos[df_faturamento_com_eventos['ID_Casa'].isin(ids_casas_selecionadas)]

    df_faturamento_com_eventos_filtrada = df_faturamento_com_eventos[['ID_Faturam_Agregado', 'ID_Casa', 'Casa', 'Categoria', 'Ano_Mes', 'Valor_Bruto', 'Desconto', 'Valor_Liquido']]

    # Exibindo tabela de faturamento agregado
    df_faturamento_agregado_aggrid, tam_df_faturamento_agregado_aggrid = dataframe_aggrid(
        df=df_faturamento_com_eventos_filtrada,
        name="Faturamento Agregado",
        num_columns=["Valor_Bruto", "Desconto", "Valor_Liquido"],
        fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
        fit_columns_on_grid_load=True
    )

    with col2:
        function_copy_dataframe_as_tsv(df_faturamento_agregado_aggrid)

    return df_orcamentos, df_orcamentos_filtrada, df_faturamento_com_eventos


def analise_orcado_realizado(
        df_orcamentos, df_faturamento_com_eventos, 
        data_inicio_analise, data_limite_analise, 
        casas_selecionadas):
    
    # 1. Aplicando filtros de data no orçamento (de faturamento bruto) e faturamento realizado
    df_orcamentos_analise = df_orcamentos[
        (df_orcamentos['Data_Orcamento'] >= data_inicio_analise) &
        (df_orcamentos['Data_Orcamento'] <= data_limite_analise) &
        (df_orcamentos['Class_Cont_1'] == 'Faturamento Bruto')
    ]

    df_faturamento_analise = df_faturamento_com_eventos[
        (df_faturamento_com_eventos['Data_Faturamento'] >= data_inicio_analise) &
        (df_faturamento_com_eventos['Data_Faturamento'] <= data_limite_analise)
    ]

    percentual_medio = 0
    # 2. Agrupando orçamentos e faturamentos por mês e merge
    if not df_orcamentos_analise.empty and not df_faturamento_analise.empty:
        orcamentos_mensais = df_orcamentos_analise.groupby('Data_Orcamento')['Valor_Orcamento'].sum().reset_index()
        orcamentos_mensais = orcamentos_mensais.rename(columns={"Data_Orcamento": "Data_Comparacao"})

        faturamento_mensais = df_faturamento_analise.groupby('Data_Faturamento')['Valor_Bruto'].sum().reset_index()
        faturamento_mensais = faturamento_mensais.rename(columns={"Data_Faturamento": "Data_Comparacao"})

        df_comparacao = pd.merge(
            orcamentos_mensais[['Data_Comparacao', 'Valor_Orcamento']],
            faturamento_mensais[['Data_Comparacao', 'Valor_Bruto']],
            on='Data_Comparacao',
            how='outer'
        ).fillna(0)
        

        # 3. Cálculo de métricas: diferença e percentual realizado
        df_comparacao['Diferenca'] = df_comparacao['Valor_Bruto'] - df_comparacao['Valor_Orcamento']

        df_comparacao['Percentual_Realizado'] = df_comparacao.apply(
            lambda row: (row['Valor_Bruto'] / row['Valor_Orcamento'] * 100) if row['Valor_Orcamento'] != 0 else 0, 
            axis=1
        ).fillna(0)
        
        df_comparacao['Mes_Ano'] = df_comparacao['Data_Comparacao'].dt.strftime('%m/%Y')
        

        # 4. Criando gráfico comparativo
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
        st.plotly_chart(fig_comparacao, width='stretch')

        st.divider()

        # 5. Exibição do df: Orçado vs Realizado
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader("Detalhamento Mensal - Orçado vs Realizado")
        
        df_comparacao_display = df_comparacao[['Mes_Ano', 'Valor_Orcamento', 'Valor_Bruto', 'Diferenca', 'Percentual_Realizado']].copy()
        df_comparacao_display.columns = ['Mês/Ano', 'Orçado (R$)', 'Realizado (R$)', 'Diferença (R$)', 'Realizado/Orçado (%)']
        
        df_comparacao_aggrid, tam_df_comparacao_aggrid = dataframe_aggrid(
            df=df_comparacao_display,
            name="Comparação Orçado vs Realizado",
            num_columns=["Orçado (R$)", "Realizado (R$)", "Diferença (R$)"],
            percent_columns=["Realizado/Orçado (%)"],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True
        )
        
        with col2:
            function_copy_dataframe_as_tsv(df_comparacao_aggrid)

        st.divider()

        # 6. Exibição das métricas de análise
        st.subheader(":material/heap_snapshot_large: Resumo das métricas")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_orcado = df_comparacao['Valor_Orcamento'].sum() if not df_comparacao.empty else 0
            total_orcado_fmt = format_brazilian(total_orcado)
            st.metric("Total Orçado", f"R$ {total_orcado_fmt}")
        
        with col2:
            total_realizado = df_comparacao['Valor_Bruto'].sum() if not df_comparacao.empty else 0
            total_realizado_fmt = format_brazilian(total_realizado)
            st.metric("Total Realizado", f"R$ {total_realizado_fmt}")
        
        with col3:
            diferenca_total = total_realizado - total_orcado
            diferenca_total_fmt = format_brazilian(diferenca_total)
            porc_diferenca_total = diferenca_total/total_orcado*100
            porc_diferenca_total_fmt = format_brazilian(porc_diferenca_total)
            st.metric("Diferença Total", f"R$ {diferenca_total_fmt}", 
                        delta=f"{porc_diferenca_total_fmt}%" if total_orcado > 0 else "N/A")
        
        with col4:
            percentual_medio = df_comparacao['Percentual_Realizado'].mean()
            # percentual_medio_display = f"{percentual_medio:.1f}%" if not pd.isna(percentual_medio) else "N/A"
            percentual_medio_display_fmt = format_brazilian(percentual_medio)
            st.metric("Média: Realizado vs Orçado (%)", f"{percentual_medio_display_fmt}%")

    else: 
        st.warning('Não há dados disponíveis para exibição.')

    # Calculando fator de ajuste baseado no histórico (abordagem conservadora)
    # Aplica ajuste apenas quando percentual_medio < 100% (corrige para baixo)
    # Quando percentual_medio > 100%, mantém fator = 1.0 (não projeta otimisticamente)
    if percentual_medio > 0:
        fator_ajuste = min(percentual_medio / 100, 1.0)
    else:
        fator_ajuste = 1.0

    return percentual_medio, fator_ajuste


def projecao_receitas_patrocinios(
        df_parc_receit_extr, df_orcamentos, 
        percentual_medio, fator_ajuste, 
        ids_casas_selecionadas, start_date, end_date):
    
    try:        
        # Debug: Verificando se o DataFrame existe e tem dados
        if df_parc_receit_extr is None or df_parc_receit_extr.empty:
            st.warning("⚠️ DataFrame de parcelas de receitas extraordinárias está vazio ou não disponível.")
            patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
        else:
            # 1. Filtrando apenas patrocínios pendentes (Recebimento_Parcela nulo) 
            # e vencimento dentro do período futuro
            df_patrocinios_futuros = df_parc_receit_extr[
                (df_parc_receit_extr['ID_Casa'].isin(ids_casas_selecionadas)) &
                (df_parc_receit_extr['Classif_Receita'] == 'Patrocínio') &
                (df_parc_receit_extr['Recebimento_Parcela'].isna()) &  # Parcelas não recebidas
                (df_parc_receit_extr['Vencimento_Parcela'] >= start_date) &
                (df_parc_receit_extr['Vencimento_Parcela'] <= end_date)
            ].copy()
            
            if not df_patrocinios_futuros.empty:
                # Preparando dados para exibição
                df_patrocinios_exibicao = df_patrocinios_futuros[[
                    'ID_Receita', 'Casa', 'Cliente', 'Data_Ocorrencia', 
                    'Vencimento_Parcela', 'Valor_Parcela', 'Classif_Receita', 
                    'Status_Pgto', 'Observacoes'
                ]].copy()
                
                # Formatando datas
                df_patrocinios_exibicao['Data_Ocorrencia'] = df_patrocinios_exibicao['Data_Ocorrencia'].dt.strftime('%d/%m/%Y')
                df_patrocinios_exibicao['Vencimento_Parcela'] = df_patrocinios_exibicao['Vencimento_Parcela'].dt.strftime('%d/%m/%Y')
                
                # Ordenando por vencimento
                df_patrocinios_exibicao = df_patrocinios_exibicao.sort_values('Vencimento_Parcela')
                
                # Exibindo tabela de patrocínios futuros
                df_patrocinios_aggrid, tam_df_patrocinios_aggrid = dataframe_aggrid(
                    df=df_patrocinios_exibicao,
                    name="Projeção de Receitas de Patrocínios",
                    num_columns=["Valor_Parcela"],
                    date_columns=[]
                )
                
                col1, col2 = st.columns([6, 1])
                with col1: 
                    total_valores_filtrados(df_patrocinios_aggrid, tam_df_patrocinios_aggrid, "Valor_Parcela", despesa_com_parc=False)
                with col2:
                    function_copy_dataframe_as_tsv(df_patrocinios_aggrid)
                

                # Agrupando patrocínios por mês para uso nas projeções
                df_patrocinios_futuros['Mes_Ano'] = df_patrocinios_futuros['Vencimento_Parcela'].dt.strftime('%m/%Y')
                
                # Convertendo Valor_Parcela para float para evitar problemas com Decimal
                df_patrocinios_futuros['Valor_Parcela_Float'] = df_patrocinios_futuros['Valor_Parcela'].astype(float)
                patrocinios_mensais = df_patrocinios_futuros.groupby('Mes_Ano')['Valor_Parcela_Float'].sum().reset_index()
                patrocinios_mensais = patrocinios_mensais.rename(columns={'Valor_Parcela_Float': 'Valor_Parcela'})
                patrocinios_mensais['Mes_Ano_Display'] = patrocinios_mensais['Mes_Ano']
        
            else:
                st.info("Não há receitas de patrocínios pendentes para o período selecionado.")
                patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])
                    
    except Exception as e:
        st.error(f"❌ Erro ao processar projeção de patrocínios: {str(e)}")
        st.exception(e)
        patrocinios_mensais = pd.DataFrame(columns=['Mes_Ano', 'Valor_Parcela', 'Mes_Ano_Display'])

    st.divider()

    ## 2. Projeção Ajustada - Próximos Meses
    st.subheader("Orçamento Ajustado - Próximos Meses")

    # Obtendo orçamentos (de faturamento) futuros para ajustar - usando o filtro de datas do usuário
    df_orcamentos_futuros = df_orcamentos[
        (df_orcamentos['Data_Orcamento'] >= start_date) &
        (df_orcamentos['Data_Orcamento'] <= end_date) &
        (df_orcamentos['Class_Cont_1'] == 'Faturamento Bruto')
    ]

    if not df_orcamentos_futuros.empty:
        df_orcamentos_futuros = df_orcamentos_futuros.copy()
        # Convertendo Valor_Orcamento para float para evitar problemas com decimal.Decimal
        df_orcamentos_futuros.loc[:, 'Valor_Orcamento_Float'] = df_orcamentos_futuros['Valor_Orcamento'].astype(float)
        
        # Aplicando fator de ajuste
        df_orcamentos_futuros.loc[:, 'Valor_Projetado'] = df_orcamentos_futuros['Valor_Orcamento_Float'] * fator_ajuste
        df_orcamentos_futuros.loc[:, 'Ajuste'] = df_orcamentos_futuros['Valor_Projetado'] - df_orcamentos_futuros['Valor_Orcamento_Float']

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
        
        # 3. Criando gráfico de projeção
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
            
            fig_projecao.add_trace(go.Scatter(
                x=receita_total_mensal['Mes_Ano_Display'],
                y=receita_total_mensal['Receita_Total'],
                mode='lines+markers',
                name='Receita Total (Orçamento Projetado + Patrocínios)',
                line=dict(color='#2E8B57', width=4, dash='dash'),
                marker=dict(size=10)
            ))
        
        # Configurando layout
        titulo_grafico = f'Orçamento Ajustado<br>Fator: {fator_ajuste:.2f} ({percentual_medio:.1f}% do orçado)'
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
        st.plotly_chart(fig_projecao, width='stretch')

        st.divider()
        
        # 4. Métricas de projeção
        st.subheader(":material/heap_snapshot_large: Métricas de projeção")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_orcado_futuro = projecoes_mensais['Valor_Orcamento'].sum()
            total_orcado_futuro_fmt = format_brazilian(total_orcado_futuro)
            st.metric("Total Orçado Futuro", f"R$ {total_orcado_futuro_fmt}")
        
        with col2:
            total_projetado = projecoes_mensais['Valor_Projetado'].sum()
            total_projetado_fmt = format_brazilian(total_projetado)
            st.metric("Total Orçado Ajustado", f"R$ {total_projetado_fmt}")
        
        with col3:
            total_patrocinios_projecao = patrocinios_mensais['Valor_Parcela'].astype(float).sum() if not patrocinios_mensais.empty else 0
            total_patrocinios_projecao_fmt = format_brazilian(total_patrocinios_projecao)
            st.metric("Total Patrocínios", f"R$ {total_patrocinios_projecao_fmt}")
        
        with col4:
            receita_total_projetada = total_projetado + total_patrocinios_projecao
            receita_total_projetada_fmt = format_brazilian(receita_total_projetada)
            st.metric("Receita Total Projetada", f"R$ {receita_total_projetada_fmt}")
        
        # Métricas adicionais
        col1, col2 = st.columns(2)
        
        with col1:
            diferenca_projecao = total_projetado - total_orcado_futuro
            diferenca_projecao_fmt = format_brazilian(diferenca_projecao)
            porc_diferenca_projecao = diferenca_projecao/total_orcado_futuro*100
            porc_diferenca_projecao_fmt = format_brazilian(porc_diferenca_projecao)
            st.metric("Ajuste Orçamento", f"R$ {diferenca_projecao_fmt}", 
                        delta=f"{porc_diferenca_projecao_fmt}%" if total_orcado_futuro > 0 else "N/A")
        
        with col2:
            diferenca_percentual = (diferenca_projecao / total_orcado_futuro * 100) if total_orcado_futuro > 0 else 0
            diferenca_percentual_fmt = format_brazilian(diferenca_percentual)
            st.metric("Ajuste Orçamento (%)", f"↓{diferenca_percentual_fmt}%")
        
        st.divider()

        # 5. Tabela de projeções
        col1, col2 = st.columns([6, 1])
        with col1:
            st.subheader("Detalhamento das Projeções")
        
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
        
        # Preparando para exibição
        projecoes_display = projecoes_consolidadas[[
            'Mes_Ano', 'Orcamento_Original', 'Orcamento_Projetado', 'Ajuste_Orcamento', 
            'Patrocinios', 'Receita_Total'
        ]].copy()
        projecoes_display.columns = [
            'Mês/Ano', 'Orçado Original (R$)', 'Projeção Ajustada (R$)', 'Ajuste (R$)', 
            'Patrocínios (R$)', 'Receita Total (R$)'
        ]
        
        projecoes_aggrid, tam_projecoes_aggrid = dataframe_aggrid(
            df=projecoes_display,
            name="Projeções Ajustadas",
            num_columns=["Orçado Original (R$)", "Projeção Ajustada (R$)", "Ajuste (R$)", "Patrocínios (R$)", "Receita Total (R$)"],
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True
        )
        
        with col2:
            function_copy_dataframe_as_tsv(projecoes_aggrid)
        
    else:
        st.warning("Não há orçamentos futuros disponíveis para projeção.")

    return df_orcamentos_futuros, patrocinios_mensais


def projecao_despesas_futuras(
        df_despesas_sem_parcelamento, df_despesas_com_parcelamento, df_orcamentos,
        df_tipo_class_cont_2, fator_ajuste,
        ids_casas_selecionadas, start_date, end_date):
    
    # Filtrando despesas por casas selecionadas
    df_despesas_sem_parcelamento = df_despesas_sem_parcelamento[df_despesas_sem_parcelamento['ID_Casa'].isin(ids_casas_selecionadas)]
    df_despesas_com_parcelamento = df_despesas_com_parcelamento[df_despesas_com_parcelamento['ID_Casa'].isin(ids_casas_selecionadas)]

    # Obtendo orçamentos futuros por tipo de fluxo
    df_orcamentos_futuros_tipos = df_orcamentos[
        (df_orcamentos['Data_Orcamento'] >= start_date) &
        (df_orcamentos['Data_Orcamento'] <= end_date) &
        (df_orcamentos['Class_Cont_1'] != 'Faturamento Bruto')  # Excluindo faturamento
    ]

    if not df_orcamentos_futuros_tipos.empty:
        # 1. Criando seção expansível com os parâmetros configurados no sistema
        with st.expander("Parâmetros Configurados no Sistema", expanded=False):            
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

            st.dataframe(df_configuracao_exibicao, hide_index=True)
            function_copy_dataframe_as_tsv(df_configuracao_exibicao)
        
        # 2. Processando por tipo de fluxo futuro
        projecoes_por_tipo = []
        
        for tipo_fluxo in ['Fixo', 'Variavel do Faturamento', 'Considerar Lançamentos']:
            ## Despesas fixas - usar valores dos orçamentos diretamente
            if tipo_fluxo == 'Fixo':
                # Obtendo as classificações que são do tipo "Fixo" da configuração do sistema
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

                    # Cria df com valor projetado para as despesas fixas - próximos meses
                    df_orcamentos_fixo_mensais = orcamentos_fixo.copy()     
                    df_orcamentos_fixo_mensais['Mes_Ano'] = df_orcamentos_fixo_mensais['Data_Orcamento'].dt.strftime('%m/%Y')
                    
                    # df_orcamentos_fixo_mensais['Mes_Ano'] = df_orcamentos_fixo_mensais['Ano_Orcamento'].astype(str) + '-' + df_orcamentos_fixo_mensais['Mes_Orcamento'].astype(str).str.zfill(2)
                    df_orcamentos_fixo_mensais = df_orcamentos_fixo_mensais.groupby('Mes_Ano', as_index=False)['Valor_Orcamento'].sum()
                    df_orcamentos_fixo_mensais['Valor_Projetado'] = df_orcamentos_fixo_mensais['Valor_Orcamento'].astype(float)
                    df_orcamentos_fixo_mensais['Tipo de Fluxo'] = 'Fixo'
                    # st.write(df_orcamentos_fixo_mensais)
                else:
                    st.write("Nenhum orçamento encontrado para este tipo.")
            

            ## Despesas variáveis - aplicar fator de ajuste
            elif tipo_fluxo == 'Variavel do Faturamento':
                # Obtendo as classificações que são do tipo "Variável do Faturamento" da configuração do sistema
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

                    # Cria df com valor projetado para as despesas 'variável do faturamento' - próximos meses
                    df_orcamentos_variavel_mensais = orcamentos_variavel.copy()
                    df_orcamentos_variavel_mensais['Mes_Ano'] = df_orcamentos_variavel_mensais['Data_Orcamento'].dt.strftime('%m/%Y')
                    df_orcamentos_variavel_mensais = df_orcamentos_variavel_mensais.groupby('Mes_Ano', as_index=False)['Valor_Orcamento'].sum()
                    df_orcamentos_variavel_mensais['Valor_Projetado'] = df_orcamentos_variavel_mensais['Valor_Orcamento'].astype(float) * fator_ajuste
                    df_orcamentos_variavel_mensais['Tipo de Fluxo'] = 'Variável do Faturamento'
                    # st.write(df_orcamentos_variavel_mensais)
                else:
                    st.write("Nenhum orçamento encontrado para este tipo.")
            

            ## Usar despesas realmente lançadas (pendentes) apenas para classificações que são "Considerar Lançamentos"
            elif tipo_fluxo == 'Considerar Lançamentos':
                # Obtendo as classificações que são do tipo "Considerar Lançamentos" da configuração do sistema
                classificacoes_lancamentos_configuradas = df_tipo_class_cont_2[
                    df_tipo_class_cont_2['Tipo_Fluxo_Futuro'] == 'Considerar Lançamentos'
                ]['Class_Cont_1'].unique()
                
                # Usando apenas as classificações configuradas como "Considerar Lançamentos"
                classificacoes_lancamentos = list(classificacoes_lancamentos_configuradas)
                

                # Processando despesas sem parcelamento
                # Despesas sem parcelamento pendentes - filtrando apenas pelas classificações corretas
                despesas_sem_parc_pendentes = df_despesas_sem_parcelamento[
                    (df_despesas_sem_parcelamento['Status_Pgto'] == 'Pendente') &
                    (df_despesas_sem_parcelamento['Class_Cont_1'].isin(classificacoes_lancamentos))
                ].copy()

                # Usar Previsao_Pgto se disponível, senão Data_Vencimento (mantendo o dia exato)
                despesas_sem_parc_pendentes['Data_Projecao'] = despesas_sem_parc_pendentes['Previsao_Pgto'].fillna(
                    despesas_sem_parc_pendentes['Data_Vencimento']
                )

                despesas_sem_parc_pendentes = despesas_sem_parc_pendentes.rename(columns={'Data_Vencimento': 'Data_Vencimento_Original'})

                # Consolidando despesas sem parcelamento
                despesas_sem_parc_pendentes['Valor_Projetado'] = despesas_sem_parc_pendentes['Valor'].astype(float)
                despesas_sem_parc_pendentes['Tipo_Projecao'] = 'Lançamentos'
                
                # Filtrar apenas despesas dentro do período selecionado
                despesas_sem_parc_futuras = despesas_sem_parc_pendentes[
                    (despesas_sem_parc_pendentes['Data_Projecao'] >= start_date) &
                    (despesas_sem_parc_pendentes['Data_Projecao'] <= end_date)
                ]

                
                # Processando despesas com parcelamento
                # Despesas com parcelamento pendentes - filtrando apenas pelas classificações corretas
                despesas_com_parc_pendentes = df_despesas_com_parcelamento[
                    (df_despesas_com_parcelamento['Status_Pgto'] == 'Parcela_Pendente') &
                    (df_despesas_com_parcelamento['Class_Cont_1'].isin(classificacoes_lancamentos))
                ].copy()
                
                # Usar Previsao_Parcela se disponível, senão Vencimento_Parcela (mantendo o dia exato)
                despesas_com_parc_pendentes['Data_Projecao'] = despesas_com_parc_pendentes['Previsao_Parcela'].fillna(
                    despesas_com_parc_pendentes['Vencimento_Parcela']
                )
                
                despesas_com_parc_pendentes = despesas_com_parc_pendentes.rename(columns={'Vencimento_Parcela': 'Data_Vencimento_Original'})
                despesas_com_parc_pendentes['Valor_Projetado'] = despesas_com_parc_pendentes['Valor_Parcela'].astype(float)
                despesas_com_parc_pendentes['Tipo_Projecao'] = 'Lançamentos'
                
                # Filtrar apenas despesas dentro do período selecionado
                despesas_com_parc_futuras = despesas_com_parc_pendentes[
                    (despesas_com_parc_pendentes['Data_Projecao'] >= start_date) &
                    (despesas_com_parc_pendentes['Data_Projecao'] <= end_date)
                ]

                # Consolidando todas as despesas de lançamentos
                # if not despesas_sem_parc_futuras.empty or not despesas_com_parc_futuras.empty:
                todas_despesas_lancamentos = pd.concat([
                    despesas_sem_parc_futuras, 
                    despesas_com_parc_futuras
                ], ignore_index=True)

                projecoes_por_tipo.append(todas_despesas_lancamentos)
                
                # Cria df com valor projetado para as despesas 'considerar lançamentos' - próximos meses
                df_todas_despesas_lancamentos_mensais = todas_despesas_lancamentos.copy()
                df_todas_despesas_lancamentos_mensais['Mes_Ano'] = df_todas_despesas_lancamentos_mensais['Data_Projecao'].dt.strftime('%m/%Y')
                df_todas_despesas_lancamentos_mensais = df_todas_despesas_lancamentos_mensais.groupby('Mes_Ano', as_index=False)['Valor_Projetado'].sum()
                df_todas_despesas_lancamentos_mensais['Tipo de Fluxo'] = 'Considerar Lançamentos'
                # st.write(df_todas_despesas_lancamentos_mensais)

            else:
                st.write("Nenhuma despesa pendente encontrada para as classificações 'Considerar Lançamentos'.")

        todos_tipo_despesas = pd.concat([df_orcamentos_fixo_mensais, df_orcamentos_variavel_mensais, df_todas_despesas_lancamentos_mensais])          
        todos_tipo_despesas = todos_tipo_despesas.drop('Valor_Orcamento', axis=1)

        todos_tipo_despesas_pivot = todos_tipo_despesas.pivot(
            index='Tipo de Fluxo',
            columns='Mes_Ano',
            values='Valor_Projetado'
        ).fillna(0)
        
        todos_tipo_despesas_pivot['Total Projetado'] = todos_tipo_despesas_pivot.sum(axis=1)

        # Corrige nomes de colunas (se forem Period, converte para string)
        todos_tipo_despesas_pivot.columns = todos_tipo_despesas_pivot.columns.astype(str)
        
        # Resetando o índice para incluir Tipo como coluna
        todos_tipo_despesas_pivot = todos_tipo_despesas_pivot.reset_index()
        colunas_numericas_despesas = [col for col in todos_tipo_despesas_pivot if col != 'Tipo de Fluxo']

        # Exibindo df
        df_todos_tipo_despesas_aggrid, tam_df_todos_tipo_despesas_aggrid = dataframe_aggrid(
            df=todos_tipo_despesas_pivot,
            name="Despesas futuras por tipo de fluxo",
            num_columns=colunas_numericas_despesas,
            fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
            fit_columns_on_grid_load=True
        )

        # 3. Criando gráfico consolidado
        fig_projecao_despesas_consolidadas = go.Figure()

        # Obtendo todos os meses únicos
        meses_unicos = sorted(todos_tipo_despesas['Mes_Ano'].unique())

        for tipo in todos_tipo_despesas['Tipo de Fluxo'].unique():
            dados_tipo = todos_tipo_despesas[todos_tipo_despesas['Tipo de Fluxo'] == tipo]
            valores = []
            for mes in meses_unicos:
                valor = dados_tipo[dados_tipo['Mes_Ano'] == mes]['Valor_Projetado'].sum()
                valores.append(valor)

            if tipo == 'Fixo': 
                cor = "#24206c" 
                name = 'Fixo'
            if tipo == 'Variável do Faturamento': 
                cor = "#70639c"
                name = 'Variável do Faturamento'
            if tipo == 'Considerar Lançamentos': 
                cor = "#b6aecd"
                name = 'Considerar Lançamentos'

            fig_projecao_despesas_consolidadas.add_trace(go.Bar(
                x=meses_unicos,
                y=valores,
                name=name,
                marker_color=cor,
                offsetgroup='Despesas prjetadas',
                text=[f"R$ {v:,.0f}" for v in valores],
                textposition='auto',
                textfont=dict(size=12, color='white'),
                hoverinfo='skip'
            ))
        
        fig_projecao_despesas_consolidadas.update_layout(
            title='',
            xaxis_title="Mês/Ano",
            yaxis_title="Valor (R$)",
            height=500,
            barmode='stack'
        )
        
        fig_projecao_despesas_consolidadas.update_yaxes(tickformat=",.0f", tickprefix="R$ ")
        st.plotly_chart(fig_projecao_despesas_consolidadas, width='stretch')

        st.divider()
        
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
            
            
            ## 4. TABELA DETALHADA POR CLASS_CONT_1 E MÊS
            col1, col2 = st.columns([6, 1])
            with col1:
                st.subheader("Detalhamento por Classificação Contábil e Mês")
            
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
                df_detalhado_aggrid, tam_df_detalhado_aggrid = dataframe_aggrid(
                    df=pivot_detalhado,
                    name="Detalhamento por Classificação e Mês",
                    num_columns=colunas_numericas,
                    fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
                    fit_columns_on_grid_load=True
                )
                
                with col2:
                    function_copy_dataframe_as_tsv(df_detalhado_aggrid)

                st.divider()

                # 5. Informações adicionais da tabela detalhada
                st.subheader(":material/heap_snapshot_large: Informações adicionais")
                col1, col2 = st.columns(2)
                
                with col1:
                    total_classificacoes = len(pivot_detalhado['Classificação Contábil'].unique())
                    st.metric("Total de Classificações", total_classificacoes)
                
                with col2:
                    total_meses = len(colunas_numericas) - 1  # Excluindo a coluna 'Total'
                    st.metric("Período de Projeção", f"{total_meses} meses")
                
                st.divider()
                
                ## 6. TABELA DETALHADA DE LANÇAMENTOS
                st.subheader("Detalhamento das Despesas - Tipo 'Lançamentos'")
                
                # Filtrando apenas despesas do tipo "Lançamentos" das projeções consolidadas
                if not df_projecoes_consolidadas.empty:
                    lancamentos_detalhados = df_projecoes_consolidadas[
                        df_projecoes_consolidadas['Tipo_Projecao'] == 'Lançamentos'
                    ].copy()
                    
                    if not lancamentos_detalhados.empty:
                        # Preparando dataframe para exibição
                        df_lancamentos_exibicao = lancamentos_detalhados[[
                            'ID_Despesa', 'ID_Parcela', 'Casa', 
                            'Fornecedor', 'Class_Cont_1', 'Class_Cont_2', 'Valor_Projetado',
                            'Data_Competencia', 'Data_Vencimento_Original', 'Data_Projecao', 
                            'Ano_Mes_Projecao', 'Status_Pgto'   
                        ]].copy()
                        
                        # Ordenando por data de projeção e valor
                        df_lancamentos_exibicao = df_lancamentos_exibicao.sort_values(['Data_Projecao', 'Valor_Projetado'], ascending=[True, False])
                        
                        # Formatando datas para exibição
                        df_lancamentos_exibicao['Data_Competencia'] = df_lancamentos_exibicao['Data_Competencia'].dt.strftime('%d/%m/%Y').fillna('N/A')
                        df_lancamentos_exibicao['Data_Vencimento_Original'] = df_lancamentos_exibicao['Data_Vencimento_Original'].dt.strftime('%d/%m/%Y').fillna('N/A')
                        df_lancamentos_exibicao['Data_Projecao'] = df_lancamentos_exibicao['Data_Projecao'].dt.strftime('%d/%m/%Y').fillna('N/A')
                        
                        # Exibindo tabela detalhada
                        df_lancamentos_aggrid, tam_df_lancamentos_aggrid = dataframe_aggrid(
                            df=df_lancamentos_exibicao,
                            name="Detalhamento de Lançamentos",
                            num_columns=["Valor_Projetado"]
                        )
                        
                        col1, col2 = st.columns([6, 1])
                        with col1: # Calculando total dos valores filtrados
                            total_valores_filtrados(df_lancamentos_aggrid, tam_df_lancamentos_aggrid, 'Valor_Projetado')
                        with col2:
                            function_copy_dataframe_as_tsv(df_lancamentos_aggrid)
                        
                    else:
                        st.info("Não há despesas do tipo 'Lançamentos' para exibir.")
                else:
                    st.warning("Não há dados de projeções consolidadas disponíveis.")                
            else:
                st.warning("Não há dados disponíveis para gerar a tabela detalhada.")
        else:
            st.warning("Nenhuma projeção encontrada para os tipos de fluxo configurados.")
        
        return df_projecoes_consolidadas
    
    else:
        st.warning("Não há orçamentos futuros disponíveis para projeção por tipo de fluxo.")

    
def projecao_avancada_receitas_despesas(
        df_projecoes_consolidadas, df_orcamentos_futuros, df_orcamentos_filtrada,
        patrocinios_mensais, casas_selecionadas):
    
    # Verificando se temos dados de projeção disponíveis
    if isinstance(df_projecoes_consolidadas, pd.DataFrame) and not df_projecoes_consolidadas.empty:
        # Separando receitas e despesas das projeções
        receitas_projetadas = df_orcamentos_futuros.copy() if not df_orcamentos_futuros.empty else pd.DataFrame()
        despesas_projetadas = df_projecoes_consolidadas.copy()
        
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
            
            # 1. Criando gráfico
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
            st.plotly_chart(fig_projecao_mensal, width='stretch')
            
            st.divider()

            # 2. Métricas resumidas da projeção
            st.subheader(":material/heap_snapshot_large: Métricas de projeção")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_receitas_orcamento = df_receitas_consolidadas['Valor_Orcamento'].sum() if not df_receitas_consolidadas.empty else 0
                total_receitas_orcamento_fmt = format_brazilian(total_receitas_orcamento)
                st.metric("Receitas Orçamento", f"R$ {total_receitas_orcamento_fmt}")

            with col2:
                total_receitas_patrocinios = df_receitas_consolidadas['Valor_Patrocinios'].sum() if not df_receitas_consolidadas.empty else 0
                total_receitas_patrocinios_fmt = format_brazilian(total_receitas_patrocinios)
                st.metric("Receitas Patrocínios", f"R$ {total_receitas_patrocinios_fmt}")
            
            with col3:
                total_receitas_proj = df_receitas_consolidadas['Valor'].sum() if not df_receitas_consolidadas.empty else 0
                total_receitas_proj_fmt = format_brazilian(total_receitas_proj)
                st.metric("Total Receitas Projetadas", f"R$ {total_receitas_proj_fmt}")
            
            with col4:
                if total_receitas_proj > 0:
                    percentual_patrocinios = (total_receitas_patrocinios / total_receitas_proj) * 100
                    percentual_patrocinios_fmt = format_brazilian(percentual_patrocinios)
                    st.metric("Patrocínios/Total (%)", f"{percentual_patrocinios_fmt}%")
                else:
                    st.metric("Patrocínios/Total (%)", "N/A")
            
            # Métricas detalhadas das receitas
            col1, col2, col3 = st.columns(3)
            
            with col1:
                total_despesas_proj = despesas_data['Valor'].sum() if not despesas_data.empty else 0
                total_despesas_proj_fmt = format_brazilian(total_despesas_proj)
                st.metric("Total Despesas Projetadas", f"R$ {total_despesas_proj_fmt}")

            with col2:
                saldo_projetado = total_receitas_proj - total_despesas_proj
                saldo_projetado_fmt = format_brazilian(saldo_projetado)
                st.metric("Saldo Projetado", f"R$ {saldo_projetado_fmt}")

            with col3:
                if total_receitas_proj > 0:
                    margem_projetada = (saldo_projetado / total_receitas_proj) * 100
                    margem_projetada_fmt = format_brazilian(margem_projetada)
                    st.metric("Margem Projetada (%)", f"{margem_projetada_fmt}%")
                else:
                    st.metric("Margem Projetada (%)", "N/A")
            
            st.divider()

            # 3. Tabela resumida da projeção
            col1, col2 = st.columns([6, 1])
            with col1:
                st.subheader("Resumo da Projeção Avançada por Mês")
            
            # Criando tabela pivot usando os dados consolidadas
            if not df_receitas_consolidadas.empty:
                # Criando DataFrame para a tabela
                tabela_projecao = df_receitas_consolidadas[['Mes_Ano_Display', 'Valor_Orcamento', 'Valor_Patrocinios', 'Valor']].copy()
                tabela_projecao = tabela_projecao.rename(columns={
                    'Valor_Orcamento': 'Receitas Projetadas',
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
                colunas_ordenadas = ['Mes_Ano_Display', 'Receitas Projetadas', 'Receitas Patrocínios', 'Receitas Total', 'Despesas Projetadas', 'Saldo']
                tabela_projecao = tabela_projecao[colunas_ordenadas]
                
                pivot_projecao = tabela_projecao
            else:
                # Fallback se não houver receitas consolidadas
                pivot_projecao = pd.DataFrame(columns=['Mes_Ano_Display', 'Receitas Projetadas', 'Receitas Patrocínios', 'Receitas Total', 'Despesas Projetadas', 'Saldo'])
            
            # Exibindo tabela
            colunas_numericas = [col for col in pivot_projecao.columns if col != 'Mes_Ano_Display']
            pivot_projecao_aggrid, tam_pivot_projecao_aggrid = dataframe_aggrid(
                df=pivot_projecao,
                name="Resumo da Projeção Avançada Mensal",
                num_columns=colunas_numericas,
                fit_columns=ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW,
                fit_columns_on_grid_load=True
            )
            
            with col2:
                function_copy_dataframe_as_tsv(pivot_projecao_aggrid)
            
        else:
            st.warning("Não há dados de projeção para exibir no gráfico.")

    else:
        st.warning("Não há dados de projeções consolidadas disponíveis.")
        