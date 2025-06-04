import streamlit as st
import requests

def login(userName: str, userPassword: str) -> bool:
    if (userName is None or userPassword is None):
        return False
    
    users = list(st.secrets["gazit_users"].keys())
    # Login via API (usuário não Gazit)
    if userName not in users:
      login_data = {
        "username": userName,
        "password": userPassword,
        "loginSource": 1,
      }
      response = requests.post('https://apps.blueprojects.com.br/fb/Security/Login',json=login_data).json()
      if "error" in response:
        return False
      elif response.get("data", {}).get("success") == True:
        print(login_data)
        return login_data
      else:
          return False
    # Login usuário Gazit 
    else:
      senha_correta = st.secrets["gazit_users"][userName]
      if userPassword == senha_correta:
        user_data = {
          "data": {
            "success": True,
            "user": {
              "name": userName,
              "permission": "Gazit"
            }
          }
        }
        print(user_data)
        return user_data
      else:
        return False


def logout():
  st.session_state['loggedIn'] = False
  st.switch_page('Login.py')


def handle_login(userName, password):
  #user data deve conter o usuario
  if user_data := login(userName, password):
    st.session_state['loggedIn'] = True
    st.session_state['userName'] = userName 
  else:
    st.session_state['loggedIn'] = False
    st.error("Email ou senha inválidos!!")


    