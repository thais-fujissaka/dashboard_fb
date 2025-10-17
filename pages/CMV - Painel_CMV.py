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
    st.divider()




        
if __name__ == '__main__':
    main()