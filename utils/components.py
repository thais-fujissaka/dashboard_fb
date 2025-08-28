import pandas as pd
import streamlit as st
import io
from utils.functions.date_functions import *
from utils.queries import *
from st_aggrid import AgGrid, GridOptionsBuilder, ColumnsAutoSizeMode
from st_aggrid import GridUpdateMode, JsCode, StAggridTheme
from streamlit_echarts import st_echarts

def input_selecao_casas(lista_casas_retirar, key):
    # Dataframe com IDs e nomes das casas
    df_casas = get_casas_validas()
    # Remove casas da lista_casas_retirar
    df_casas = df_casas[~df_casas["Casa"].isin(lista_casas_retirar)].sort_values(by="Casa").reset_index(drop=True)
    # Adiciona a opção "Todas as Casas"
    lista_casas_validas = ["Todas as Casas"] + df_casas["Casa"].to_list()

    # Se o usuário não tem acesso a todas as casas, mostra apenas as casas que ele tem acesso
    user_email = st.session_state['user_email']
    lista_ids_casas_acesso = st.secrets["user_access"][user_email]
    if -1 not in lista_ids_casas_acesso:
        df_casas = df_casas[df_casas["ID_Casa"].isin(lista_ids_casas_acesso)].sort_values(by="Casa").reset_index(drop=True)
        lista_casas_validas = df_casas["Casa"].to_list()

    df_validas = pd.DataFrame(lista_casas_validas, columns=["Casa"])
    casa = st.selectbox("Casa", lista_casas_validas, key=key)

    if casa == "Todas as Casas":
        id_casa = -1  # Valor padrão para "Todas as Casas"
        casa = "Todas as Casas"
        id_zigpay = -1
    else:
        df = df_casas.merge(df_validas, on="Casa", how="inner")
        # Definindo um dicionário para mapear nomes de casas a IDs de casas
        mapeamento_ids = dict(zip(df["Casa"], df["ID_Casa"]))
        # Definindo um dicionário para mapear IDs de casas a IDs da Zigpay
        mapeamento_zigpay = dict(zip(df["Casa"], df["ID_Zigpay"]))

        # Obtendo o ID da casa selecionada
        id_casa = mapeamento_ids[casa]
        # Obtendo o ID da Zigpay correspondente ao ID da casa
        id_zigpay = mapeamento_zigpay[casa]

    return id_casa, casa, id_zigpay


def input_periodo_datas(key):
    today = get_today()
    jan_this_year = get_jan_this_year(today)
    first_day_this_month_this_year = get_first_day_this_month_this_year(today)
    last_day_this_month_this_year = get_last_day_this_month_this_year(today)

    # Inicializa o input com o mês atual
    date_input = st.date_input("Período",
                            value=(first_day_this_month_this_year, last_day_this_month_this_year),
                            min_value=jan_this_year,
                            format="DD/MM/YYYY",
                            key=key
                            )
    return date_input


def seletor_mes(label, key):
  # Dicionário para mapear os meses
  meses = {
      "Janeiro": "01",
      "Fevereiro": "02",
      "Março": "03",
      "Abril": "04",
      "Maio": "05",
      "Junho": "06",
      "Julho": "07",
      "Agosto": "08",
      "Setembro": "09",
      "Outubro": "10",
      "Novembro": "11",
      "Dezembro": "12"
  }

  # Obter o mês atual para defini-lo como padrão
  mes_atual_num = get_today().month
  nomes_meses = list(meses.keys())
  mes_atual_nome = nomes_meses[mes_atual_num - 1]

  # Seletor de mês
  mes = st.selectbox(label, nomes_meses, index=nomes_meses.index(mes_atual_nome), key=key)

  # Obter o mês correspondente ao mês selecionado
  mes_selecionado = meses[mes]

  return mes_selecionado


def seletor_ano(ano_inicio, ano_fim, key):
   anos = list(range(ano_inicio, ano_fim + 1))
   anos_ordenados = sorted(anos, reverse=True)
   ano_atual = datetime.datetime.now().year 
   index_padrao = anos_ordenados.index(ano_atual)
   ano = st.selectbox("Selecionar ano:", anos_ordenados, index=index_padrao,key=key)
   return ano


def button_download(df, file_name, key):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=f"{file_name}")
    excel_data = output.getvalue()

    st.download_button(
        label=":material/download: Download Excel",
        data=excel_data,
        file_name=f"{file_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="tertiary",
        key=f'{key}'
    )


def seletor_vendedor(label, df_vendedores, key):
    
    lista_vendedores = df_vendedores['ID - Responsavel'].tolist()
    lista_vendedores.insert(0, "Todos os vendedores")

    vendedor = st.selectbox(label, lista_vendedores, key=key)
    if vendedor == "Todos os vendedores":
        id_vendedor = -1  # Valor padrão para "Todos"
        nome_vendedor = "Todos os vendedores"
    else:
        # Extrai o ID do vendedor selecionado
        id_vendedor = int(vendedor.split(" - ")[0])
        nome_vendedor = vendedor.split(" - ")[1]
    return id_vendedor, nome_vendedor


def seletor_vendedor_logado(label, df_vendedores, lista_vendedores_logado, key):

    # Recupera o email do usuário
    user_email = st.session_state["user_email"]

    # Verifica se o usuário tem acesso a todos os vendedores
    if user_email in st.secrets["comissions_total_access"]["users"]:
        lista_vendedores = df_vendedores['ID - Responsavel'].tolist()
        lista_vendedores.insert(0, "Todos os vendedores")
    else:
        # Filtra somente o vendedor logado
        lista_vendedores = lista_vendedores_logado

    # Seletor de vendedor
    vendedor = st.selectbox(label, lista_vendedores, key=key)
    if vendedor == "Todos os vendedores":
        id_vendedor = -1  # Valor padrão para "Todos"
        nome_vendedor = "Todos os vendedores"
    else:
        # Extrai o ID do vendedor selecionado
        if vendedor:
            id_vendedor = int(vendedor.split(" - ")[0])
            nome_vendedor = vendedor.split(" - ")[1]
        else:
            id_vendedor = int(lista_vendedores[0].split(" - ")[0])
            nome_vendedor = lista_vendedores[0].split(" - ")[1]

    return id_vendedor, nome_vendedor

def kpi_card(title, value, background_color="#FFFFFF", title_color="#333", value_color="#000"):
    html = f"""
    <div style="
        background-color: {background_color};
        border: 1px solid rgba(49, 51, 63, 0.2);
        border-radius: 10px;
        padding: 16px;
        height: 120px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: none;
        margin: 0px;
        cursor: default;
        transition: none;
    ">
        <div style="font-size: 14px; color: {title_color}; font-weight: normal; margin-bottom: 6px;">
            {title}
        </div>
        <div style="font-size: 24px; color: {value_color}; font-weight: bold;">
            {value}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def dataframe_aggrid(df, name, num_columns=[], percent_columns=[], df_details=None, coluns_merge_details=None, coluns_name_details=None, key="default"):
    # Converter colunas selecionadas para float com limpeza de texto
    for col in num_columns:
        if col in df.columns:
            df[f"{col}_NUM"] = (
                df[col]
                .astype(str)
                .str.upper()
                .str.replace(r'[A-Z$R\s]', '', regex=True)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False)
            )
            df[f"{col}_NUM"] = pd.to_numeric(df[f"{col}_NUM"], errors='coerce')

            # Formatar a coluna original como string BR
            df[col] = df[f"{col}_NUM"].apply(
                lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notnull(x) else ""
            )

    for col in percent_columns:
        if col in df.columns:
            df[f"{col}_NUM"] = (
                df[col]
                .astype(str)
                .str.replace('%', '', regex=False)
                .str.replace(',', '.', regex=False)
                .str.replace('−', '-', regex=False)
                .str.replace('–', '-', regex=False)
                .str.replace(r'[^\d\.\-]', '', regex=True)
            )
            df[f"{col}_NUM"] = pd.to_numeric(df[f"{col}_NUM"], errors='coerce')

            # Formatar a coluna original como string percentual
            df[col] = df[f"{col}_NUM"].apply(
                lambda x: f"{x:.2f}%".replace('.', ',') if pd.notnull(x) else ""
            )

    # Definir cellStyle para pintar valores negativos/positivos
    cellstyle_code = JsCode("""
    function(params) {
        const value = params.data[params.colDef.field + '_NUM'];
        if (value === null || value === undefined || isNaN(value)) {
            return {};
        }
        if (value < 0) {
            return {
                color: '#ff7b7b',
                fontWeight: 'bold'
            };
        }
        if (value > 0) {
            return {
                color: '#90ee90',
                fontWeight: 'bold'
            };
        }
        return {};
    }
    """)

    # Construir grid options builder
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_default_column(resizable=True, sortable=True, filterable=True)

    # Esconder colunas _NUM e detail
    for col in num_columns + percent_columns:
        if f"{col}_NUM" in df.columns:
            gb.configure_column(f"{col}_NUM", hide=True, type=["numericColumn"])
    if "detail" in df.columns:
        gb.configure_column("detail", hide=True)

    # Auto-ajustar todas as colunas
    for col in df.columns:
        gb.configure_column(col, autoSize=True)

    grid_options = gb.build()

    grid_options["suppressSizeToFit"] = True  
    grid_options["suppressColumnVirtualisation"] = True

    # Auto-size para TODAS as colunas (inclui header/label)
    grid_options["onGridReady"] = JsCode("""
    function(params) {
    var allColumnIds = [];
    params.columnApi.getAllColumns().forEach(function(c) { allColumnIds.push(c.getColId()); });
    params.columnApi.autoSizeColumns(allColumnIds, false); // false => considera header
    }
    """)

    if df_details is not None:
        df['detail'] = df[coluns_merge_details].apply(
            lambda i: df_details[df_details[coluns_merge_details] == i].to_dict('records')
        )

        special_column = {
            "field": coluns_name_details,
            "cellRenderer": "agGroupCellRenderer",
            "checkboxSelection": False,
        }

        other_columns = []
        for col in df.columns:
            if col in [coluns_name_details, "detail"]:
                continue
            col_def = {"field": col}
            if col in num_columns + percent_columns:
                col_def["cellStyle"] = cellstyle_code
            other_columns.append(col_def)

        columnDefs = [special_column] + other_columns

        detail_columnDefs = [{"field": c} for c in df_details.columns]

        grid_options.update({
            "masterDetail": True,
            "columnDefs": columnDefs,
            "detailCellRendererParams": {
                "detailGridOptions": {
                    "columnDefs": detail_columnDefs,
                    "suppressColumnVirtualisation": True,  # idem para o detalhe
                    "onFirstDataRendered": JsCode("""
                        function(params) {
                            var allColumnIds = [];
                            params.columnApi.getAllColumns().forEach(function(c){ allColumnIds.push(c.getColId()); });
                            params.columnApi.autoSizeColumns(allColumnIds, false);
                        }
                    """),
                },
                "getDetailRowData": JsCode("function(params) {params.successCallback(params.data.detail);}"),
            },
            "rowData": df.to_dict('records'),
            "enableRangeSelection": True,
            "suppressRowClickSelection": True,
            "cellSelection": True,
            "rowHeight": 40,
            "defaultColDef": {
                "minWidth": 100,
                "autoHeight": False,
                "filter": True,
            }
        })

    else:
        grid_options.update({
            "enableRangeSelection": True,
            "suppressRowClickSelection": False,
            "cellSelection": False,
            "rowHeight": 40,
            "defaultColDef": {
                "minWidth": 100,
                "autoHeight": False,
                "filter": True,
            }
        })

    # Criar DataFrame sem colunas técnicas
    cols_to_drop = [col for col in df.columns if col.endswith('_NUM') or col == 'detail']
    df_to_show = df.drop(columns=cols_to_drop, errors='ignore')

    # Ajustar columnDefs se não for masterDetail
    if "masterDetail" not in grid_options:
        grid_options["columnDefs"] = [{"field": col} for col in df_to_show.columns]

    # Adicionar efeito zebra (linhas alternadas)
    if st.session_state.get("base_theme") == "dark":
        custom_theme = (StAggridTheme(base="balham").withParams().withParts('colorSchemeDark'))
    # Zebra escura
        grid_options["getRowStyle"] = JsCode('''
        function(params) {
            if (params.node.rowIndex % 2 === 0) {
                return { background: '#222', color: '#fff' };
            } else {
                return { background: '#333', color: '#fff' };
            }
        }
        ''')
    else:
    # Zebra clara (padrão)
        custom_theme = (StAggridTheme(base="balham").withParams())
        grid_options["getRowStyle"] = JsCode('''
        function(params) {
            if (params.node.rowIndex % 2 === 0) {
                return { background: '#fff', color: '#111' };
            } else {
                return { background: '#e60e6e6', color: '#111' };
            }
        }
        ''')

    # Mostrar AgGrid
    grid_response = AgGrid(
        df_to_show,
        gridOptions=grid_options,
        enable_enterprise_modules=True,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        key=f"aggrid_{name}_{key}",
        theme=custom_theme,
        height=min(len(df_to_show)*40+34+11, 399),
        custom_css={
        ".ag-root-wrapper": {
            "border-radius": "10px",   # cantos arredondados
            "overflow": "hidden",      # evita vazar conteúdo nas bordas
            "border": "1px solid #ddd" 
        }, ".ag-cell": {
            "font-family": "'Source Sans Pro', sans-serif",
            "font-size": "14px",
            "display": "flex",              
            "align-items": "center",
        },
        ".ag-header-cell-text": {
            "font-family": "'Source Sans Pro', sans-serif",
            "font-size": "15px",
            "font-weight": "600",
        },
    }
    )

    filtered_df = grid_response['data']
    filtered_df = filtered_df.drop(columns=[col for col in filtered_df.columns if col.endswith('_NUM')], errors='ignore')
    return filtered_df, len(filtered_df)


def component_plotPizzaChart(labels, sizes, name, max_columns=8):
    chart_key = f"{labels}_{sizes}_{name}_"
    
    # Organize os dados para mostrar apenas um número limitado de categorias
    if len(labels) > max_columns:
        # Ordenar os dados e pegar os "max_columns" maiores
        sorted_data = sorted(zip(sizes, labels), reverse=True)[:max_columns]
        
        # Dados dos "Outros"
        others_value = sum(size for size, label in zip(sizes, labels) if (size, label) not in sorted_data)
        sorted_data.append((others_value, "Outros"))
        
        # Desempacotar os dados para labels e sizes
        sizes, labels = zip(*sorted_data)
    else:
        # Caso contrário, use todos os dados
        sizes, labels = sizes, labels

    # Preparar os dados para o gráfico
    data = [{"value": size, "name": label} for size, label in zip(sizes, labels)]
    
    options = {
        "tooltip": {
            "trigger": "item",
            "formatter": "{b}: {c} ({d}%)"
        },
        "legend": {
        "orient": "vertical",
        "right": 55,
        "top": "middle",
        "type": "scroll",  # Adiciona rolagem se muitos itens
        "height": 200,
        "textStyle": {
            "fontWeight": "normal",
            "fontSize": 10,
            "color": "#444"
        }
    },
        "grid": {  
            "left": "50%", 
            "right": "50%", 
            "containLabel": True
        },
    # "color": [
    #     "#8b0000", "#910d0d", "#971a1a", "#9d2828", "#a33535",
    #     "#a94343", "#af5050", "#b65e5e", "#bc6b6b", "#c27979",
    #     "#c88686", "#ce9494", "#d4a1a1", "#dbafaf", "#e1bcbc",
    #     "#e7caca", "#edd7d7", "#f3e5e5", "#f9f2f2", "#ffffff"
    #     ],
        "series": [
        {
            "name": "Quantidade",
            "type": "pie",
            "radius": ["40%", "75%"],
            "center": ["30%", "50%"],  # Gráfico mais à esquerda 
                "data": data,
                "label": {
                    "show": False  # Garante que os rótulos não apareçam nas fatias
                },
                "labelLine": {
                    "show": False  # Remove as linhas que puxam os rótulos
                },
                "minAngle": 5,  
                "itemStyle": {
                    "borderRadius": 8,
                    "borderColor": "#fff",
                    "borderWidth": 2  
                },
                "selectedMode": "single",
                "selectedOffset": 8,  
                "emphasis": {
                    "label": {
                        "show": False  # Impede que o rótulo apareça ao passar o mouse
                    },
                    "itemStyle": {
                        "shadowBlur": 10,
                        "shadowOffsetX": 0,
                        "shadowColor": "rgba(0, 0, 0, 0.5)"
                    }
                }
            }
        ]
    }
    
    st_echarts(options=options, height="350px", key=chart_key)

