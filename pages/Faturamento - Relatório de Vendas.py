import streamlit as st
import pandas as pd
from utils.queries_financeiro import *
from utils.functions.financeiro_faturamento_zigpay import *
from utils.functions.produtos_relatorio_vendas import *
from utils.functions.general_functions import *
from utils.components import *
from utils.user import logout

st.set_page_config(
  layout = 'wide',
  page_title = 'Relatório de Vendas',
  page_icon='🛍️',
  initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
  st.switch_page('Login.py')


def grafico_linhas_faturamento_tipos(df, coluna_soma: str, key):
    
    df = df.copy()

    # Mapeamento de inglês → abreviado em português sem acento
    dias_semana_abrev = {
        "Monday": "Seg",
        "Tuesday": "Ter",
        "Wednesday": "Qua",
        "Thursday": "Qui",
        "Friday": "Sex",
        "Saturday": "Sab",
        "Sunday": "Dom"
    }

    df['Data_Evento'] = pd.to_datetime(df['Data_Evento'])
    df[coluna_soma] = df[coluna_soma].astype(float)

    # Cria uma coluna com o dia da semana abreviado
    df['Dia da Semana'] = df['Data_Evento'].dt.day_name().map(dias_semana_abrev)

    # Formatar rótulo Data + Dia
    df.loc[:, 'Data_Label'] = df['Data_Evento'].dt.strftime("%Y-%m-%d") + " (" + df['Dia da Semana'] + ")"

    df = df.groupby(['Data_Evento', 'Tipo', 'Data_Label']).agg({
      coluna_soma: 'sum',
      'Dia da Semana': 'first'
    }).reset_index()
  
    todas_datas = df['Data_Evento'].unique()
    todos_tipos = df['Tipo'].unique()

    idx = pd.MultiIndex.from_product(
        [todas_datas, todos_tipos],
        names=['Data_Evento', 'Tipo']
    )

    # Reindexar preenchendo zeros
    df = (
        df.set_index(['Data_Evento', 'Tipo'])
          .reindex(idx, fill_value=0)
          .reset_index()
    )

    # Recriar a coluna Data_Label depois do reindex
    df['Data_Label'] = df['Data_Evento'].dt.strftime("%Y-%m-%d") + " (" + df['Data_Evento'].dt.day_name().map(dias_semana_abrev) + ")"

    # Preparar séries de dados para o gráfico
    datas = df.drop_duplicates('Data_Evento').sort_values('Data_Evento')['Data_Label'].tolist()
    series = []
    for tipo in todos_tipos:
        serie_categoria = df[df['Tipo'] == tipo].sort_values('Data_Evento')
        series.append({
            "name": tipo,
            "type": "line",
            "stack": "Total",
            "areaStyle": {},
            "emphasis": {"focus": "series"},
            "data": serie_categoria[coluna_soma].astype(float).tolist(),
        })

    # Configurações do gráfico
    options = {
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "cross", "label": {"backgroundColor": "#6a7985"}},
        },
        "legend": {"data": todos_tipos.tolist()},
        "toolbox": {"feature": {"saveAsImage": {}}},
        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True},
        "xAxis": [{"type": "category", "boundaryGap": False, "data": datas}],
        "yAxis": [{"type": "value"}],
        "series": series,
    }

    # Renderizar no Streamlit
    return st_echarts(options=options, height="400px", key=key)



def main():
  config_sidebar()
  col, col2, col3 = st.columns([6, 1, 1])
  with col:
    st.title('🛍️ Relatório de Vendas')
  with col2:
    st.button(label="Atualizar", on_click = st.cache_data.clear)
  with col3:
    if st.button("Logout"):
      logout()
  st.divider()

  lojasComDados = preparar_dados_lojas_user_financeiro()
  data_inicio_default, data_fim_default = get_first_and_last_day_of_month()
  lojas_selecionadas, data_inicio, data_fim = criar_seletores(lojasComDados, data_inicio_default, data_fim_default)

  st.divider()

  OrcamentoFaturamento = config_orcamento_faturamento(lojas_selecionadas, data_inicio, data_fim) 
  orcamfatformatado = OrcamentoFaturamento.copy()
  categorias_desejadas = ['Alimentos', 'Bebidas', 'Couvert', 'Gifts']
  soma_valor_bruto = orcamfatformatado.loc[orcamfatformatado['Categoria'].isin(categorias_desejadas), 'Valor Bruto'].sum()
  soma_valor_bruto = format_brazilian(soma_valor_bruto)
  orcamfatformatado = format_columns_brazilian(orcamfatformatado, ['Orçamento', 'Valor Bruto', 'Desconto', 'Valor Líquido', 'Faturam - Orçamento'])
  orcamfatformatado.loc[orcamfatformatado['Orçamento'] == '0,00', 'Atingimento %'] = '-'
  
  st.markdown('<div style="page-break-before: always;"></div>', unsafe_allow_html=True)

  FaturamentoZig = config_Faturamento_zig(lojas_selecionadas, data_inicio, data_fim)


  col0, col1, col2 = st.columns([0.1, 2.6, 0.1])
  with col1:
    # Filtro por categoria desejada
    col1, col2 = st.columns([1, 1])
    with col1:
      categoria = st.selectbox(label='Selecione Categoria', options=categorias_desejadas)
    FaturamentoZigClasse = filtrar_por_classe_selecionada(FaturamentoZig, 'Categoria', [categoria])
    classificacoes = obter_valores_unicos_ordenados(FaturamentoZigClasse, 'Tipo')
    with col2:
      classificacoes_selecionadas = st.multiselect(label='Selecione Tipos', options=classificacoes)
    FaturamentoZigClasse = filtrar_por_classe_selecionada(FaturamentoZigClasse, 'Tipo', classificacoes_selecionadas)
    FaturamentoZigClasseAgrupado = FaturamentoZigClasse.copy().groupby(['Data_Evento', 'ID Produto', 'Nome Produto']).agg({
      'Loja': 'first',
      'Categoria': 'first',
      'Tipo': 'first',
      'Preço Unitário': 'first',
      'Quantia comprada': 'sum',
      'Desconto': 'sum',
      'Valor Bruto Venda': 'sum',
      'Valor Líquido Venda': 'sum'
    }).reset_index()
    st.write('')

    st.subheader("Curva de Faturamento por Tipo de Produto")
    grafico_linhas_faturamento_tipos(FaturamentoZigClasse, 'Valor Bruto Venda', 'grafico_linhas_faturamento_tipos')
    st.write('')
    st.subheader(f"Número de Vendas de {categoria} por Tipo")
    grafico_linhas_faturamento_tipos(FaturamentoZigClasse, 'Quantia comprada', 'grafico_linhas_quantias_tipos')

    col1, col2 = st.columns([4, 1], vertical_alignment = "center")
    with col1:
        st.markdown('### Itens Vendidos Detalhado por Transação')
    with col2:
        button_download(FaturamentoZigClasse, f'itens', f'download_itens')
    FaturamentoZigClasse = format_columns_brazilian(FaturamentoZigClasse, ['Valor Bruto Venda', 'Valor Líquido Venda', 'Preço Unitário'])
    st.dataframe(FaturamentoZigClasse, width='stretch', hide_index=True)


    col1, col2 = st.columns([4, 1], vertical_alignment = "center")
    with col1:
        st.markdown('### Itens Vendidos Agrupados por Data')
    with col2:
        button_download(FaturamentoZigClasseAgrupado, f'itens_agrupados', f'download_itens_agrupados')
    FaturamentoZigClasse = format_columns_brazilian(FaturamentoZigClasseAgrupado, ['Valor Bruto Venda', 'Valor Líquido Venda', 'Preço Unitário'])
    st.dataframe(FaturamentoZigClasse, width='stretch', hide_index=True)


if __name__ == '__main__':
  main()
