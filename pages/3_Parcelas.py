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
	page_title="Parcelas",
	layout="wide",
	initial_sidebar_state="collapsed"
)

if 'loggedIn' not in st.session_state or not st.session_state['loggedIn']:
	st.switch_page('Login.py')

def main():
	config_sidebar()
	st.title("Parcelas")

	df_eventos = GET_EVENTOS_PRICELESS()
	df_parcelas = GET_PARCELAS_EVENTOS_PRICELESS()

	st.dataframe(df_eventos, use_container_width=True, hide_index=True)
	st.dataframe(df_parcelas, use_container_width=True, hide_index=True)



if __name__ == '__main__':
  main()
