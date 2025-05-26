import streamlit as st
from utils.user import *
from utils.queries import *

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
        st.write("Você está logado!")
        st.markdown("Redirecionando para a página Home...")
        st.switch_page("pages/1_Home.py")

if __name__ == "__main__":
    main()
