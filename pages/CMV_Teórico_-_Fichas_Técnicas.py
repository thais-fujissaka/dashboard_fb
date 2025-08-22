import streamlit as st
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries import *
from utils.user import *

st.set_page_config(
	page_icon=":material/rubric:",
	page_title="CMV Teórico - Fichas Técnicas",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
    
    config_sidebar()
    st.markdown("# CMV Teórico - Fichas Técnicas")

if __name__ == '__main__':
  main()