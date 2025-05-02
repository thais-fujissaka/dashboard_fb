import streamlit as st
import pandas as pd
import datetime
from workalendar.america import Brazil
from utils.components import *
from utils.functions.date_functions import *
from utils.functions.general_functions import *
from utils.queries import *
from utils.queries import GET_EVENTOS_PRICELESS, GET_PARCELAS_EVENTOS_PRICELESS
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

st.set_page_config(
	page_title="Controle de Eventos",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
	config_sidebar()
	st.title("Controle de Eventos")

	st.write("Informações sobre eventos")



if __name__ == '__main__':
  main()
