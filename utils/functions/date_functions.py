import datetime
import calendar
import pandas as pd
import numpy as np
from workalendar.america import Brazil

def get_today():
    return datetime.datetime.now()

def get_last_year(today):
    return today.year - 1

def get_jan_last_year(last_year):
    return datetime.datetime(last_year, 1, 1)

def get_jan_this_year(today):
    return datetime.datetime(today.year, 1, 1)

def get_last_day_of_month(today):
    return calendar.monthrange(today.year, today.month)[1]

def get_first_day_this_month_this_year(today):
    return datetime.datetime(today.year, today.month, 1)

def get_last_day_this_month_this_year(today):
    return datetime.datetime(today.year, today.month, get_last_day_of_month(today))

def get_dec_this_year(today):
    return datetime.datetime(today.year, 12, 31)

def get_start_of_three_months_ago(today):
    month_sub_3 = today.month - 3
    year = today.year
    if month_sub_3 <= 0:
        month_sub_3 += 12
        year -= 1
    return datetime.datetime(year, month_sub_3, 1)


def get_first_and_last_day_of_month():
    # Inicializa o calendário do Brasil
    cal = Brazil()
    today = datetime.datetime.today()

    # Determinar o primeiro e último dia do mês passado
    first_day_of_current_month = today.replace(day=1) 

    # Usar esses valores como default
    data_inicio_default = first_day_of_current_month.date()
    data_fim_default = today.date()

    return data_inicio_default, data_fim_default

def df_format_date_brazilian(df, date_column):
  df = df.copy()
  df[date_column] = pd.to_datetime(df[date_column], errors="coerce")
  df[date_column] = df[date_column].dt.strftime('%d-%m-%Y')
  return df


def df_format_date_columns_brazilian(df, date_columns):
    df = df.copy()
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
            df[col] = df[col].dt.strftime('%d/%m/%Y')
        else:
            print(f"Aviso: coluna '{col}' não encontrada no DataFrame.")
    return df


def formata_data_horario_zero_str(data):
    if isinstance(data, str):
        data = datetime.datetime.strptime(data, "%Y-%m-%d 00:00:00")
    data_formatada = data.strftime("%Y-%m-%d 00:00:00")
    return data_formatada


def df_formata_data_horario_zero_str(df, date_column):
    df[date_column] = df[date_column].apply(lambda x: formata_data_horario_zero_str(x))
    return df


def formata_data_sem_horario(data):
    if pd.isnull(data):
        return None
    
    # Converte qualquer tipo reconhecível para Timestamp
    if isinstance(data, (np.datetime64, pd.Timestamp, datetime.date, datetime.datetime)):
        return pd.to_datetime(data).strftime("%d-%m-%Y")
    
    if isinstance(data, str):
        try:
            return pd.to_datetime(data).strftime("%d-%m-%Y")
        except ValueError:
            return ""  # string inválida para conversão
    
    return ""  # tipo não reconhecido


def df_formata_data_sem_horario(df, date_column):
    df[date_column] = df[date_column].apply(lambda x: formata_data_sem_horario(x))
    return df


def df_formata_datas_sem_horario(df, date_columns):
    if df is not None and not df.empty:
        df = df.copy()
        for column in date_columns:
            if column in df.columns:
                df[column] = df[column].apply(
                    lambda x: formata_data_sem_horario(x) if pd.notnull(x) else x
                )
    return df


def formata_data_sem_horario_YYYY_MM_DD(data):
    if pd.isnull(data):
        return None
    if isinstance(data, str):
        try:
            data = datetime.datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            return ""  # string inválida para conversão
    return data.strftime("%Y-%m-%d")


def df_formata_datas_sem_horario_YYYY_MM_DD(df, date_columns):
    df = df.copy()
    for column in date_columns:
        df[column] = df[column].apply(lambda x: formata_data_sem_horario_YYYY_MM_DD(x) if not pd.isnull(x) else x)
    return df


def filtrar_por_datas(dataframe, data_inicio, data_fim, categoria):
    data_inicio = pd.Timestamp(data_inicio)
    data_fim = pd.Timestamp(data_fim)

    dataframe.loc[:, categoria] = pd.to_datetime(
        dataframe[categoria],
        errors='coerce'
    )

    dataframe_filtered = dataframe.loc[
        (dataframe[categoria] >= data_inicio) & (dataframe[categoria] <= data_fim)
    ]

    return dataframe_filtered
