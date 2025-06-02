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
    df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()
    
    # Substitui NaT ou datas nulas por uma data padrão ou remove linhas
    df_eventos = df_eventos.dropna(subset=["Data_Evento"])

    # Força espaçamento e quebra no DOM
    st.markdown("<div style='margin-top: 30px'></div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([6, 1, 1])
    with col1:
        st.title("📅 Calendário de Eventos")
    with col2:
        st.button(label='Atualizar', key='atualizar_calendario', on_click=st.cache_data.clear)
    with col3:
        if st.button('Logout', key='logout_calendario'):
            logout()
               
    st.divider()
    
    json_eventos = dataframe_to_json_calendar(df_eventos)
    
    # Renderiza o calendário
    selected = st_calendar(
        events=json_eventos,
        options=get_calendar_options(),
        custom_css=get_custom_css(),
        key="calendar",
    )

    # Adiciona a legenda de cores dos eventos
    st.markdown("""
    <div style="margin-top: -24px; padding: 10px; background-color: #ffffff; border-radius: 12px; border: 1px solid #e5e7eb; display: flex; align-items: center;">
        <h6 style="padding: 0">Legenda:</h6>
        <div style="display: flex; gap: 16px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 16px; height: 16px; background-color: #22C55E; border-radius: 4px; margin-right: 8px;"></div>
                <span>Confirmado</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 16px; height: 16px; background-color: #EAB308; border-radius: 4px; margin-right: 8px;"></div>
                <span>Em negociação</span>
            </div>
            <div style="display: flex; align-items: center;">
                <div style="width: 16px; height: 16px; background-color: #EF4444; border-radius: 4px; margin-right: 8px;"></div>
                <span>Declinados</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")

    if selected:
        
        if selected.get("callback") == "eventClick":
            id_evento_seleciondo = selected["eventClick"]["event"]["id"]
            with st.container(border=True):
                st.write("")
                col1, col2, col3 = st.columns([1, 15, 1])
                with col2:
                    infos_evento(id_evento_seleciondo, df_eventos)
                    st.write("")
                    mostrar_parcelas(id_evento_seleciondo, df_parcelas)
                    st.write("")
                    st.write("")
        else:
            st.info("Selecione um evento no calendário para ver os detalhes.")

if __name__ == '__main__':
  main()