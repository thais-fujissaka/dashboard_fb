import streamlit as st
from streamlit_calendar import calendar as st_calendar
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries import *
from utils.functions.parcelas import *
from utils.user import *
from utils.functions.calendario_de_eventos import *

st.set_page_config(
	page_icon="📈",
	page_title="KPI's de Vendas Priceless- Conversão de Eventos",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
    
    config_sidebar()

    # Recupera dados dos eventos
    df_eventos = GET_EVENTOS_PRICELESS()
    df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()

    # Busca vendedores

    # Substitui NaT ou datas nulas por uma data padrão ou remove linhas
    df_eventos = df_eventos.dropna(subset=["Data_Evento"])

    # Força espaçamento e quebra no DOM
    st.markdown("<div style='margin-top: 30px'></div>", unsafe_allow_html=True)
    
    st.title("📈 KPI's de Vendas Priceless - Conversão de Eventos")
    st.divider()




    


    
         

if __name__ == '__main__':
  main()