import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.user import *
from utils.functions.cmv_teorico import *
from utils.queries_cmv import *

st.set_page_config(
    page_icon=":bar_chart:",
    page_title="Painel de CMV",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
    st.switch_page('Login.py')

from streamlit_echarts import st_echarts
import streamlit as st

def grafico_cmv_orcado(df_cmv_orcado):

    dados_cmv_orcado_em_reais = df_cmv_orcado['Valor Orçamento CMV'].astype(float).tolist()
    dados_cmv_orcado_porcentagem = df_cmv_orcado['% CMV Orçado'].astype(float).tolist()

    dict_meses = {
        1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
        7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
    }
    meses = [dict_meses[mes] for mes in df_cmv_orcado['Mês']]

    option = {
        "title": {
            "text": "CMV Orçado",
            "left": "center",
            "textStyle": {
            "fontSize": 18,
            "fontWeight": "bold",
            "color": "#333"
        }
        },
        "tooltip": {"trigger": "axis"},
        "legend": {
            "data": ["Valor CMV Orçado (R$)", "CMV Orçado (%)"],
            "bottom": 0,
            "left": "center"
        },
        "grid": {
            "left": "8%",
            "right": "8%",
            "top": "15%",
            "bottom": "15%",
            "containLabel": True
        },
        "xAxis": {
            "type": "category",
            "boundaryGap": False,
            "data": meses
        },
        "yAxis": [
            {
                "type": "value",
                "name": "Valor CMV Orçado (R$)",
                "position": "left",
                "axisLine": {"lineStyle": {"color": "#1E3A8A"}},
                "axisLabel": {"formatter": "R${value}"}
            },
            {
                "type": "value",
                "name": "% CMV Orçado",
                "position": "right",
                "axisLine": {"lineStyle": {"color": "#22C55E"}},
                "axisLabel": {"formatter": "{value}%"}
            }
        ],
        "series": [
            {
                "name": "Valor CMV Orçado (R$)",
                "type": "line",
                "yAxisIndex": 0,
                "data": dados_cmv_orcado_em_reais,
                "color": "#1E3A8A"
            },
            {
                "name": "CMV Orçado (%)",
                "type": "line",
                "yAxisIndex": 1,
                "data": dados_cmv_orcado_porcentagem,
                "color": "#22C55E"
            }
        ]
    }

    st_echarts(options=option, height="400px", key="grafico_cmv_orcado")


def main():
    # Sidebar
    config_sidebar()

    # Header
    col1, col2, col3 = st.columns([6, 1, 1], vertical_alignment="center")
    with col1:
        st.title(":bar_chart: Painel de CMV")
    with col2:
        st.button(label='Atualizar', key='atualizar', on_click=st.cache_data.clear)
    with col3:
        if st.button('Logout', key='logout'):
            logout()

    df_cmv_orcado = GET_CMV_ORCADO_AB()

    st.divider()
    col1, col2 = st.columns([1, 1])
    with col1:
        lista_retirar_casas = ['Bar Léo - Vila Madalena', 'Blue Note SP (Novo)', 'Edificio Rolim', 'Todas as Casas']
        id_casa, casa, id_zigpay = input_selecao_casas(lista_retirar_casas, 'selecao_casa')
    df_cmv_orcado = df_cmv_orcado[df_cmv_orcado['Casa'] == casa]
    with col2:
        ano = seletor_ano(2024, int(get_last_year(today=datetime.datetime.now()) + 1), 'ano', label='Selecione o ano')
    df_cmv_orcado = df_cmv_orcado[df_cmv_orcado['Ano'] == ano]
    st.divider()

    #st.dataframe(df_cmv_orcado, use_container_width=True)
    grafico_cmv_orcado(df_cmv_orcado)
    
    




        
if __name__ == '__main__':
    main()