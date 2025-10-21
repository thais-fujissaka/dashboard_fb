import streamlit as st
from utils.user import *
from utils.queries_eventos import *
from utils.functions.general_functions import config_permissoes_user

st.set_page_config(
    initial_sidebar_state="collapsed",
    page_title="Login",
    page_icon="🔑",
    layout="centered",
)


def main():

    st.markdown(
        """
    <style>
      section[data-testid="stSidebar"][aria-expanded="true"]{
        display: none;
      }
    </style>
    """,
        unsafe_allow_html=True,
    )

    if "loggedIn" not in st.session_state:
        st.session_state["loggedIn"] = False

    if not st.session_state["loggedIn"]:
        st.title(":bar_chart: Dashboard - FB")
        st.write("")

        with st.container(border=True):
            user_email = st.text_input(
                label="Login", value="", placeholder="nome@email.com"
            )
            password = st.text_input(
                label="Senha", value="", placeholder="senha", type="password"
            )
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.button(
                    "Login",
                    on_click=handle_login,
                    args=(user_email, password),
                    type="primary",
                    use_container_width=True,
                )
    else:
        permissao, Nomeuser, email = config_permissoes_user()
        st.write("Você está logado!")
        st.markdown("Redirecionando...")

        # Mapeamento de permissões para página inicial
        permissoes_pagina_inicial = {
            "Dev Dash FB": "pages/Eventos - Calendário_de_Eventos.py",
            "Acesso Admin Eventos": "pages/Eventos - Calendário_de_Eventos.py",
            "Acesso Eventos 1": "pages/Eventos - Calendário_de_Eventos.py",
            "Acesso Eventos 2": "pages/Eventos - Calendário_de_Eventos.py",
            "Acesso Eventos 3": "pages/Eventos - Calendário_de_Eventos.py",
            "Acesso Eventos 4": "pages/Eventos - Calendário_de_Eventos.py",
            "Acesso Eventos 5": "pages/Eventos - Calendário_de_Eventos.py",
            "Acesso Liderança Eventos": "pages/Eventos - Calendário_de_Eventos.py",
            "Acesso Admin Priceless Eventos": "pages/Eventos - Calendário_de_Eventos.py",
            "Gazit": "pages/Eventos - Gazit.py",
            "Acesso Conciliação": "pages/Conciliação - Conciliações.py",
            "Acesso Conciliação Casa": "pages/Conciliação - Conciliações.py",
            "Acesso CMV 1": "pages/CMV - CMV_Real.py",
            "Acesso Compras 1": "pages/Compras - Análises.py",
            "Acesso Financeiro 1": "pages/Financeiro - Despesas.py",
            "Acesso Financeiro 2": "pages/Financeiro - Despesas.py"
        }

        # Verifica a primeira permissão que existe no mapeamento
        for p, pagina in permissoes_pagina_inicial.items():
            if p in permissao:
                st.switch_page(pagina)
                break

if __name__ == "__main__":
    main()
