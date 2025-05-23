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
	page_icon=":calendar:",
	page_title="Calendário de Eventos",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
    
    config_sidebar()

    # Recupera dados dos eventos
    df_eventos = GET_EVENTOS_PRICELESS()

    # Substitui NaT ou datas nulas por uma data padrão ou remove linhas
    df_eventos = df_eventos.dropna(subset=["Data_Evento"])

    # Força espaçamento e quebra no DOM
    st.markdown("<div style='margin-top: 30px'></div>", unsafe_allow_html=True)
    st.title("📅 Calendário de Eventos")
    st.divider()
    
    json_eventos = dataframe_to_json_calendar(df_eventos)

    # Renderiza o calendário
    selected = st_calendar(
        events=json_eventos,
        options=get_calendar_options(),
        custom_css=get_custom_css(),
        key="calendar",
    )

if __name__ == '__main__':
  main()