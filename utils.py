import pandas as pd
from payconpy.fpython.fpython import *
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import random
from payconpy.odoo.odoo_xmlrpc import *
import ssl
import plotly.express as px
import streamlit as st
import holidays
import calendar
import datetime
import pandas as pd
import pytz
import dotenv





def get_odoo(model: str, data: dict, auth: dict, filters: list = [], uid: int = None, limit: int = None) -> list[dict]:
    """
    Retrieves data from an Odoo model using XML-RPC, applying filters.

    Args:
        model (str): The name of the Odoo model to retrieve data from.
        data (dict): A dictionary containing additional arguments to pass to the XML-RPC call.
        filters (list): A list of tuples representing the filters to apply. Each tuple should contain
                        the field name, the operator, and the value to filter by.

    Returns:
        None

    Example:
        Here's an example of how you could use the get_all_odoo() function:

        ```
        def main():
            # Retrieve data from the 'res.partner' model, filtering by email
            model = 'res.partner'
            data = {'fields': ['name', 'email']}
            filters = [('email', '=', 'example@domain.com')]
            get_all_odoo(model, data, filters)

        if __name__ == "__main__":
            main()
        ```
    """
    URL_RPC = auth['URL_RPC']
    DB_RPC = auth['DB_RPC']
    USERNAME_RPC = auth['USERNAME_RPC']
    PASSWORD_RPC = auth['PASSWORD_RPC']
    context = ssl._create_unverified_context()

    common = client.ServerProxy(f'{URL_RPC}xmlrpc/2/common', context=context)
    if uid is None:
        uid = common.authenticate(DB_RPC, USERNAME_RPC, PASSWORD_RPC, {})
    models = client.ServerProxy('{}/xmlrpc/2/object'.format(URL_RPC), context=context)

    # Apply filters to the search call
    domain = []
    for filter in filters:
        domain.append(filter)
    
    # If a limit is provided, use it in the data argument for search_read
    if limit is not None:
        if 'limit' in data:
            # Respect the lower of the two limits if 'limit' was already in 'data'
            data['limit'] = min(data['limit'], limit)
        else:
            data['limit'] = limit

    values = models.execute_kw(DB_RPC, uid, PASSWORD_RPC, model, 'search_read', [domain], data)
    return values


def soma_todas_as_horas(df):
    total_hours = df["unit_amount"].sum()
    hours = int(total_hours)
    minutes = int((total_hours - hours) * 60)
    formatted_time = f"{hours:02d}:{minutes:02d}"
    return formatted_time

def calcular_honorarios_total(df, initial_date, end_date):
    """
    Calcula o total do campo x_honorarios no intervalo de datas especificado.
    
    :param df: DataFrame com os dados já formatados.
    :param initial_date: Data inicial do filtro no formato datetime.date.
    :param end_date: Data final do filtro no formato datetime.date.
    :return: String com o valor total formatado em reais brasileiros.
    """
    # Garantir que initial_date e end_date sejam timezone-aware, alinhados com o DataFrame
    gmt_minus_3 = pd.Timestamp(initial_date).tz_localize("America/Sao_Paulo")
    gmt_minus_3_end = pd.Timestamp(end_date).tz_localize("America/Sao_Paulo")

    # Filtrar pelo intervalo de datas (assumindo que as colunas já têm GMT-3 ou estão consistentes)
    df_filtrado = df[
        (df['x_start_datetime'] >= gmt_minus_3) &
        (df['x_start_datetime'] <= gmt_minus_3_end)
    ]

    # Calcular o total do campo x_honorarios
    total_honorarios = df_filtrado['x_honorarios'].sum()

    # Formatar como moeda brasileira (R$)
    total_honorarios_formatado = f"R$ {total_honorarios:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    return total_honorarios_formatado


def calcular_horas_restantes(df, total_desejado=120):
    """
    Calcula as horas restantes para atingir um total desejado considerando dias úteis.
    Retorna os dias úteis necessários e a distribuição das horas por dia útil.
    """
    import holidays
    import datetime

    # Total de horas já calculadas
    total_hours = df["unit_amount"].sum()
    
    # Definir o total desejado
    horas_restantes = total_desejado - total_hours

    # Configuração dos feriados no Brasil
    brasil_holidays = holidays.Brazil()

    # Data de hoje
    hoje = datetime.date.today()

    # Lista de dias úteis futuros e distribuição de horas
    dias_uteis = 0
    distribuicao_horas = []
    
    while horas_restantes > 0:
        # Incrementa o dia
        hoje += datetime.timedelta(days=1)

        # Verifica se é dia útil
        if hoje.weekday() < 5 and hoje not in brasil_holidays:
            dias_uteis += 1
            if horas_restantes >= 8:
                distribuicao_horas.append(8)  # Preenche o dia útil com 8 horas
                horas_restantes -= 8
            else:
                distribuicao_horas.append(horas_restantes)  # Preenche com as horas restantes
                horas_restantes = 0

    return dias_uteis, distribuicao_horas

def calcular_diferenca_horas(meta, total_horas):
    """
    Calcula a diferença entre a meta e o total de horas realizadas.
    Retorna o valor no formato HH:MM.
    """
    # Converter total realizado (exemplo "128:54") para horas decimais
    total_horas_split = total_horas.split(":")
    total_decimal = int(total_horas_split[0]) + int(total_horas_split[1]) / 60

    # Calcular a diferença
    diferenca_decimal = total_decimal - meta

    # Converter a diferença de volta para HH:MM
    horas = int(abs(diferenca_decimal))  # Parte inteira
    minutos = int((abs(diferenca_decimal) - horas) * 60)  # Parte decimal convertida para minutos

    # Formatar o resultado como HH:MM
    resultado = f"{horas:02d}:{minutos:02d}"

    # Indicar se o valor é positivo ou negativo
    if diferenca_decimal < 0:
        resultado = f"-{resultado}"

    return resultado
    
def primeiro_dia_util_mes(data):
    """
    Retorna o primeiro dia útil do mês da data fornecida.
    """
    brasil_holidays = holidays.Brazil()
    primeiro_dia = datetime.date(data.year, data.month, 1)

    while primeiro_dia.weekday() >= 5 or primeiro_dia in brasil_holidays:
        primeiro_dia += datetime.timedelta(days=1)
    
    return primeiro_dia

def ultimo_dia_util_mes(data):
    """
    Retorna o último dia útil do mês da data fornecida.
    """
    brasil_holidays = holidays.Brazil()
    
    # Obter o último dia do mês
    ultimo_dia_num = calendar.monthrange(data.year, data.month)[1]
    ultimo_dia = datetime.date(data.year, data.month, ultimo_dia_num)

    while ultimo_dia.weekday() >= 5 or ultimo_dia in brasil_holidays:
        ultimo_dia -= datetime.timedelta(days=1)
    
    return ultimo_dia


def tarefa_mais_trabalhada(df):
    """
    Retorna a tarefa em que você mais trabalhou, o tempo total formatado em horas (HH:MM),
    e a descrição da tarefa.

    Parâmetros:
    - df: DataFrame contendo os dados com as colunas 'task', 'unit_amount', e 'name'.

    Retorna:
    - String formatada com a tarefa, tempo total e descrição.
    """
    # Encontrar o índice do maior valor na coluna 'unit_amount'
    max_index = df['unit_amount'].idxmax()

    # Obter os valores correspondentes
    task = df.loc[max_index, 'task']
    unit_amount = df.loc[max_index, 'unit_amount']
    name = df.loc[max_index, 'name']
    cliente = df.loc[max_index, 'cliente']

    # Converter unit_amount para o formato HH:MM
    hours = int(unit_amount)
    minutes = int((unit_amount - hours) * 60)
    formatted_time = f"{hours:02d}:{minutes:02d}"

    # Retornar o texto formatado
    return f"#### Até agora, a tarefa que você mais ficou com o relógio ligado, trabalhando nela, foi: \n##### *{task} - {cliente}*\n\n#### O tempo que você ficou trabalhando nisso foi\n ###### **{formatted_time} Horas/Minutos**\n\n#### Essa é a descrição da tarefa:\n\n*{name}*"


def atualizar_e_salvar_excel(df, initial_date, end_date, nome_arquivo='dados_atualizados.xlsx'):
    """
    Atualiza um arquivo Excel com novos dados, aplica GMT-3 às colunas de data,
    remove o fuso horário antes de salvar e retorna os dados no intervalo fornecido.
    
    :param df: DataFrame com os dados a serem salvos.
    :param initial_date: Data inicial do filtro no formato datetime.date.
    :param end_date: Data final do filtro no formato datetime.date.
    :param nome_arquivo: Nome do arquivo Excel para salvar (padrão: 'dados_atualizados.xlsx').
    :return: DataFrame filtrado pelo intervalo de datas.
    """
    import pytz

    # Definir o fuso horário GMT-3
    gmt_minus_3 = pytz.timezone('America/Sao_Paulo')

    # Converter initial_date e end_date para timezone-aware (GMT-3)
    initial_date_formatted = pd.Timestamp(initial_date).replace(tzinfo=gmt_minus_3)
    end_date_formatted = pd.Timestamp(end_date).replace(tzinfo=gmt_minus_3)

    if os.path.exists(nome_arquivo):
        df_existente = pd.read_excel(nome_arquivo)
        ids_existentes = set(df_existente['id'])
        novos_registros = df[~df['id'].isin(ids_existentes)]
        
        if not novos_registros.empty:
            # Concatenar os novos registros com os existentes
            df_final = pd.concat([df_existente, novos_registros], ignore_index=True)
        else:
            # Se não houver novos registros, manter o DataFrame existente
            df_final = df_existente
    else:
        # Se o arquivo não existe, criar um novo com os dados fornecidos
        df_final = df

    # Converter as colunas de datas para timezone-aware (GMT-3)
    df_final['x_start_datetime'] = pd.to_datetime(df_final['x_start_datetime'], errors='coerce').dt.tz_localize('UTC').dt.tz_convert(gmt_minus_3)
    df_final['x_end_datetime'] = pd.to_datetime(df_final['x_end_datetime'], errors='coerce').dt.tz_localize('UTC').dt.tz_convert(gmt_minus_3)

    # Filtrar os dados pelo intervalo de datas
    df_filtrado = df_final[
        (df_final['x_start_datetime'] >= initial_date_formatted) &
        (df_final['x_start_datetime'] <= end_date_formatted)
    ]

    # Remover o fuso horário para salvar no Excel
    df_final['x_start_datetime'] = df_final['x_start_datetime'].dt.tz_localize(None)
    df_final['x_end_datetime'] = df_final['x_end_datetime'].dt.tz_localize(None)

    # Salvar o DataFrame final no arquivo Excel
    df_final.to_excel(nome_arquivo, index=False)

    # Retornar o DataFrame filtrado
    return df_filtrado
