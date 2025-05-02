import datetime
import calendar
import pandas as pd

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

def df_format_date_brazilian(df, date_column):
  df = df.copy()
  df[date_column] = pd.to_datetime(df[date_column])
  df[date_column] = df[date_column].dt.strftime('%d-%m-%Y')
  return df

def formata_data_sem_horario(data):
    if isinstance(data, str):
        data = datetime.datetime.strptime(data, "%d-%m-%Y")
    data_formatada = data.strftime("%d-%m-%Y")
    return data_formatada

def formata_data_horario_zero(data):
    if isinstance(data, str):
        data = datetime.datetime.strptime(data, "%Y-%m-%d 00:00:00")
    data_formatada = data.strftime("%Y-%m-%d 00:00:00")
    return data_formatada


def df_formata_data_horario_zero(df, date_column):
    df[date_column] = df[date_column].apply(lambda x: formata_data_horario_zero(x))
    return df

def df_formata_data_sem_horario(df, date_column):
    df[date_column] = df[date_column].apply(lambda x: formata_data_sem_horario(x))
    return df