import streamlit as st
import pandas as pd
from utils.components import *
from streamlit_echarts import st_echarts
from utils.functions.general_functions import *
from utils.functions.parcelas import *

def dataframe_to_json_calendar(df_eventos):
    """
    Converte um DataFrame de eventos em um formato JSON adequado para o calendário.
    """
    # Remove eventos declinados
    df_eventos = df_eventos[df_eventos['Status_Evento'] != 'Declinado']

    # Formata Data_Evento para o formato YYYY-MM-DD (preparar para inserir no JSON)
    df_eventos = df_formata_datas_sem_horario_YYYY_MM_DD(df_eventos, ['Data_Evento'])


    eventos_json = []
    for _, row in df_eventos.iterrows():
        # Define a cor baseada no status
        if row['Status_Evento'] == 'Confirmado':
            cor = '#007BFF'  # Azul
        elif row['Status_Evento'] == 'Em negociação':
            cor = '#F97316'  # Laranja
        else:
            cor = '#9CA3AF'  # Cinza para outros status

        evento = {
            "allDay": True,
            "title": f"{row['Nome_do_Evento']}",
            "start": row['Data_Evento'],
            "end": row['Data_Evento'],
            "color": cor,
            "status": row['Status_Evento']
        }
        eventos_json.append(evento)
    return eventos_json


def get_custom_css():
    """Retorna a string com CSS customizado para o calendário."""
    return """
    /* ======== BOTÕES ======== */
    .fc-button {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        padding: 6px 12px !important;
        font-weight: 500 !important;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        transition: all 0.2s ease;
    }
    .fc-button:hover {
        background-color: #f9fafb !important;
        border-color: #9ca3af !important;
    }
    .fc-button:disabled {
        background-color: #f3f4f6 !important;
        color: #9ca3af !important;
        border-color: #e5e7eb !important;
    }
    /* ======== TÍTULO ======== */
    .fc-toolbar-title {
        font-size: 22px;
        color: #111827;
        font-weight: 600;
    }
    /* ======== FUNDO DO CALENDÁRIO ======== */
    .fc {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    /* ======== EVENTOS ======== */
    .fc-daygrid-event {
        border-radius: 6px;
        padding: 2px 4px;
        font-size: 13px;
        font-weight: 500;
        border: none;
    }
    .fc-daygrid-event:hover {
        opacity: 0.8;
        cursor: pointer;
    }
    .fc-event-title {
        white-space: normal !important;
    }
    /* ======== BARRA DE NAVEGAÇÃO SUPERIOR ======== */
    .fc-toolbar.fc-header-toolbar {
        margin-bottom: 12px;
    }
    /* ======== DIAS ======== */
    .fc-daygrid-day-number {
        color: #374151;
        font-weight: 500;
    }
    .fc-col-header-cell-cushion {
        color: #6b7280;
        font-weight: 500;
    }
    /* ======== OVERFLOW DE EVENTOS ======== */
    .fc-daygrid-more-link {
        color: #3b82f6;
        font-weight: 500;
    }
    """

def get_calendar_options():
    """Retorna o dicionário com opções de configuração do calendário."""
    return {
        "locale": "pt-br",
        "initialView": "dayGridMonth",
        "height": 700,
        "headerToolbar": {
            "start": "prev,next today",
            "center": "title",
            "end": "dayGridMonth,timeGridWeek,timeGridDay,listWeek",
        },
        "dayMaxEvents": False,
    }