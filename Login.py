import streamlit as st
from utils.user import *
from utils.queries import *
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
        st.title(":calendar: Controle de Eventos")
        st.write("")

        with st.container(border=True):
            userName = st.text_input(
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
                    args=(userName, password),
                    type="primary",
                    use_container_width=True,
                )
    else:
        permissao, Nomeuser, username = config_permissoes_user()
        st.write("Você está logado!")
        st.markdown("Redirecionando...")
        if "Admin Dash Eventos" in permissao:
            st.switch_page("pages/1_Calendário_de_Eventos.py")
        elif "Gazit" in permissao:
            st.switch_page("pages/6_Gazit.py")

if __name__ == "__main__":
    main()
