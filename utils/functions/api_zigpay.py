import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import calendar

def get_compradores_zigpay_api(data_inicio, data_fim, id_zigpay):

    headers = {
            'Authorization': st.secrets["api_zigpay"]["token"],
    }  

    url = "https://api.zigcore.com.br/integration/erp/compradores"
    df = pd.DataFrame()
    
    params = {          
        "dtinicio": pd.to_datetime(data_inicio).strftime("%Y-%m-%dT%H:%M:%S"),
        "dtfim": pd.to_datetime(data_fim).strftime("%Y-%m-%dT%H:%M:%S"),
        "loja": f"{id_zigpay}"
    }
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        compradores = response.json()
        df = pd.DataFrame(compradores)
        
    else:
        print(f"Erro {response.status_code} na requisição de compradores.")
        print(response.text)

    return df


def df_compradores_zigpay_mes(mes, ano, id_zigpay):
    data_inicio = pd.Timestamp(f"{ano}-{mes:02d}-01")

    if datetime.now().month == mes and datetime.now().year == ano:
        data_fim = pd.Timestamp(datetime.now())
    else:
        data_fim = pd.Timestamp(datetime(ano, mes, calendar.monthrange(ano, mes)[1]))
    
    print(data_inicio, data_fim)
    df = pd.DataFrame()
    
    # Usar intervalo de 3 dias para garantir que fica dentro do limite de 5
    for data in pd.date_range(start=data_inicio, end=data_fim, freq='3D'):
        data_inicio_requisicao = data
        data_fim_requisicao = min(data + pd.DateOffset(days=2), data_fim)  # 3 dias completos
        
        if data_inicio_requisicao <= data_fim_requisicao:
            print(data_inicio_requisicao, data_fim_requisicao)
            df_resultado = get_compradores_zigpay_api(data_inicio_requisicao, data_fim_requisicao, id_zigpay)
            df = pd.concat([df, df_resultado], ignore_index=True)

    return df
