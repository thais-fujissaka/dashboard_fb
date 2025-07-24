import pandas as pd
import streamlit as st
import io
from utils.functions.date_functions import *
from utils.queries import *

def input_selecao_casas(lista_casas_retirar, key):
    
    df_casas = get_casas_validas()
    df_casas = df_casas[~df_casas["Casa"].isin(lista_casas_retirar)].sort_values(by="Casa").reset_index(drop=True)
    lista_casas_validas = ["Todas as Casas"] + df_casas["Casa"].to_list()
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


import streamlit as st

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
