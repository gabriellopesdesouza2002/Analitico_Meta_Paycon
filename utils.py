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
from dateutil import parser  # Usaremos parser para lidar com strings de data/hora




def get_odoo2(model: str, data: dict, auth: dict, filters: list = [], uid: int = None, limit: int = None) -> list[dict]:
    """
    Retrieves data from an Odoo model using XML-RPC, applying filters, and adjusts times to America/Sao_Paulo.

    Args:
        model (str): The name of the Odoo model to retrieve data from.
        data (dict): A dictionary containing additional arguments to pass to the XML-RPC call.
        filters (list): A list of tuples representing the filters to apply. Each tuple should contain
                        the field name, the operator, and the value to filter by.

    Returns:
        list[dict]: List of dictionaries containing the data from the Odoo model.
    """
    URL_RPC = auth['URL_RPC']
    DB_RPC = auth['DB_RPC']
    USERNAME_RPC = auth['USERNAME_RPC']
    PASSWORD_RPC = auth['PASSWORD_RPC']
    context = ssl._create_unverified_context()

    # Establish the connection to Odoo
    common = client.ServerProxy(f'{URL_RPC}xmlrpc/2/common', context=context)
    if uid is None:
        uid = common.authenticate(DB_RPC, USERNAME_RPC, PASSWORD_RPC, {})
    models = client.ServerProxy('{}/xmlrpc/2/object'.format(URL_RPC), context=context)

    # Apply filters to the search call
    domain = filters if filters else []
    
    # If a limit is provided, use it in the data argument for search_read
    if limit is not None:
        if 'limit' in data:
            # Respect the lower of the two limits if 'limit' was already in 'data'
            data['limit'] = min(data['limit'], limit)
        else:
            data['limit'] = limit

    # Retrieve data from Odoo
    values = models.execute_kw(DB_RPC, uid, PASSWORD_RPC, model, 'search_read', [domain], data)

    # Convert datetime fields to America/Sao_Paulo timezone
    saopaulo_tz = pytz.timezone('America/Sao_Paulo')
    for record in values:
        for key, value in record.items():
            if isinstance(value, str):
                try:
                    # Attempt to parse the datetime string using dateutil.parser
                    dt = parser.parse(value)
                    if dt.tzinfo is None:
                        # Assume UTC if no timezone info is present
                        dt = pytz.utc.localize(dt)
                    # Convert to Sao Paulo timezone
                    record[key] = dt.astimezone(saopaulo_tz).strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError):
                    # Ignore non-datetime strings or parsing errors
                    pass

    return values

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
    if df.empty:
        return "R$ 0,00"
    # Garantir que initial_date e end_date sejam timezone-naive, alinhados com o DataFrame
    initial_date_naive = pd.Timestamp(initial_date).replace(tzinfo=None)
    end_date_naive = pd.Timestamp(end_date).replace(tzinfo=None)

    # Filtrar pelo intervalo de datas
    df_filtrado = df[
        (df['x_start_datetime'] >= initial_date_naive) &
        (df['x_start_datetime'] <= end_date_naive)
    ]

    # Garantir que a coluna x_honorarios seja numérica
    df_filtrado['x_honorarios'] = pd.to_numeric(df_filtrado['x_honorarios'], errors='coerce')

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
    if df.empty:
        return "Não há nenhuma tarefa registrada ainda no periodo selecionado."
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
    return f"#### Até agora, a tarefa que você mais trabalhou direto foi: \n##### *{task} - {cliente}*\n\n#### O tempo que você ficou trabalhando nisso foi\n ###### **{formatted_time} Horas/Minutos**\n\n#### Essa é a descrição da tarefa:\n\n{name}"


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
    # Definir o fuso horário GMT-3
    gmt_minus_3 = pytz.timezone('America/Sao_Paulo')

    # Converter initial_date e end_date para timezone-aware (GMT-3)
    initial_date_formatted = pd.Timestamp(initial_date).replace(tzinfo=gmt_minus_3)
    end_date_formatted = pd.Timestamp(end_date).replace(tzinfo=gmt_minus_3)

    # Criar ou carregar o arquivo Excel existente
    if os.path.exists(nome_arquivo):
        df_existente = pd.read_excel(nome_arquivo)
    else:
        df_existente = pd.DataFrame()

    # Garantir que o arquivo existente e o novo DataFrame tenham os mesmos tipos de dados
    if not df_existente.empty:
        df_existente['id'] = df_existente['id'].astype(str)

    df['id'] = df['id'].astype(str)

    # Verificar duplicatas com base na coluna "id"
    if not df_existente.empty:
        novos_registros = df[~df['id'].isin(df_existente['id'])]
        df_final = pd.concat([df_existente, novos_registros], ignore_index=True)
    else:
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


def atualizar_e_salvar_excel_robusto(df, initial_date, end_date, nome_arquivo='dados_atualizados.xlsx'):
    """
    Atualiza um arquivo Excel com novos dados, aplica GMT-3 às colunas de data,
    remove o fuso horário antes de salvar e retorna os dados no intervalo fornecido.
    
    :param df: DataFrame com os dados a serem salvos.
    :param initial_date: Data inicial do filtro no formato datetime.date.
    :param end_date: Data final do filtro no formato datetime.date.
    :param nome_arquivo: Nome do arquivo Excel para salvar (padrão: 'dados_atualizados.xlsx').
    :return: DataFrame atualizado e filtrado pelo intervalo fornecido.
    """
    # Definir o fuso horário GMT-3
    gmt_minus_3 = pytz.timezone('America/Sao_Paulo')

    # Converter initial_date e end_date para timezone-naive
    initial_date_formatted = pd.Timestamp(initial_date).replace(tzinfo=None)
    end_date_formatted = pd.Timestamp(end_date).replace(tzinfo=None)

    # Carregar o arquivo existente ou criar um novo
    if os.path.exists(nome_arquivo):
        df_existente = pd.read_excel(nome_arquivo)

        # Garantir que a coluna 'id' seja string para evitar problemas na comparação
        df_existente['id'] = df_existente['id'].astype(str)
    else:
        df_existente = pd.DataFrame()

    # Converter a coluna 'id' do novo DataFrame para string
    df['id'] = df['id'].astype(str)

    # Remover duplicatas com base na coluna 'id'
    if not df_existente.empty:
        df_atualizado = pd.concat([df_existente, df], ignore_index=True).drop_duplicates(subset=['id'], keep='last')
    else:
        df_atualizado = df

    # Converter as colunas de datas para timezone-naive para garantir consistência
    df_atualizado['x_start_datetime'] = pd.to_datetime(df_atualizado['x_start_datetime'], errors='coerce').dt.tz_localize(None)
    df_atualizado['x_end_datetime'] = pd.to_datetime(df_atualizado['x_end_datetime'], errors='coerce').dt.tz_localize(None)

    # Verificar se há valores nulos após as conversões
    if df_atualizado['x_start_datetime'].isna().any() or df_atualizado['x_end_datetime'].isna().any():
        raise ValueError("Há valores nulos em 'x_start_datetime' ou 'x_end_datetime'. Verifique os dados.")

    # Salvar todos os dados no Excel (sem filtro)
    df_atualizado.to_excel(nome_arquivo, index=False)

    # Filtrar os dados pelo intervalo de datas para retorno
    df_filtrado = df_atualizado[
        (df_atualizado['x_start_datetime'] >= initial_date_formatted) &
        (df_atualizado['x_start_datetime'] <= end_date_formatted)
    ]

    return df_filtrado


def calcular_salario(horas_extras, salario_bruto):
    """
    Calcula o salário líquido considerando horas extras e descontos.

    Args:
        horas_extras: String no formato hh:mm representando as horas extras.
        salario_bruto: Valor do salário bruto.

    Returns:
        O valor do salário líquido.
    """

    # Converter horas extras para um decimal
    horas_extras_decimal = float(horas_extras.replace(':', '.')) / 100

    # Calcular o valor das horas extras
    valor_horas_extras = salario_bruto * horas_extras_decimal

    # Calcular o salário bruto com as horas extras
    salario_com_extras = salario_bruto + valor_horas_extras

    # Aplicar o desconto de 15.52%
    desconto = salario_com_extras * 0.1552
    salario_liquido = salario_com_extras - desconto

    return f"R$ {salario_liquido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')


def calcular_diferenca(horas_extras, salario_bruto, comissao=0):
    """
    Calcula o valor adicional considerando horas extras e comissão.

    Args:
        horas_extras: String no formato hh:mm representando as horas extras.
        salario_bruto: Valor do salário bruto.
        comissao: Valor da comissão adicional (não será somado ao salário, apenas retornado como diferença).

    Returns:
        O valor adicional formatado.
    """

    # Converter horas extras para um decimal
    horas_extras_decimal = float(horas_extras.replace(':', '.')) / 100

    # Calcular o valor das horas extras
    valor_horas_extras = salario_bruto * horas_extras_decimal

    # Calcular o valor adicional total
    valor_total_adicional = valor_horas_extras + comissao

    # Retornar o valor adicional formatado
    return f"R$ {valor_total_adicional:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')



def concatenar_colunas_em_string(df):
    """
    Concatena todas as colunas de um DataFrame em uma única string, separando os valores por espaço.

    Parâmetros:
        df (pd.DataFrame): O DataFrame de entrada.

    Retorna:
        str: Uma única string contendo os valores concatenados das colunas.
    """
    # Converte todas as colunas para strings e concatena com espaço
    resultado = df.astype(str).agg(' '.join, axis=1).str.cat(sep=' ')
    return resultado


def calcular_salario_liquido(salario_bruto):
    """
    Calcula o salário líquido aplicando um desconto fixo de 15,52% (INSS e IR),
    e retorna o valor formatado como R$.

    Args:
        salario_bruto (float): O valor do salário bruto.

    Returns:
        str: O salário líquido formatado no padrão brasileiro (R$).
    """
    # Aplicar o desconto de 15,52%
    desconto = salario_bruto * 0.1552

    # Calcular o salário líquido
    salario_liquido = salario_bruto - desconto

    # Retornar o valor formatado
    return f"R$ {salario_liquido:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')



def filtrar_fora_horario_comercial(df, coluna_inicio='x_start_datetime', coluna_fim='x_end_datetime'):
    """
    Filtra as linhas de um DataFrame cujos horários estão fora do horário comercial (9h às 18h).

    Args:
        df (pd.DataFrame): O DataFrame a ser analisado.
        coluna_inicio (str): O nome da coluna contendo os horários de início.
        coluna_fim (str): O nome da coluna contendo os horários de término.

    Returns:
        pd.DataFrame: Um DataFrame com as linhas fora do horário comercial.
    """
    # Converter as colunas para datetime
    # Converter as colunas para datetime
    df[coluna_inicio] = pd.to_datetime(df[coluna_inicio])
    df[coluna_fim] = pd.to_datetime(df[coluna_fim])

    # Adicionar colunas com as horas (apenas o número da hora)
    df["hora_inicio"] = df[coluna_inicio].dt.hour
    df["hora_fim"] = df[coluna_fim].dt.hour

    # Definir os limites do horário comercial
    hora_inicio = 9
    hora_fim = 18

    # Filtrar as linhas fora do horário comercial
    fora_horario = df[
        (df["hora_inicio"] < hora_inicio) | 
        (df["hora_inicio"] >= hora_fim) |
        (df["hora_fim"] < hora_inicio) |
        (df["hora_fim"] >= hora_fim)
    ]

    return fora_horario


def soma_horas_9_18(df):
    # 1) Converter colunas para datetime
    df['x_start_datetime'] = pd.to_datetime(df['x_start_datetime'])
    df['x_end_datetime']   = pd.to_datetime(df['x_end_datetime'])

    # 2) Filtrar as linhas que começam às 9h (ou depois) e terminam às 18h (ou antes)
    df_filtrado = df[
        (df['x_start_datetime'].dt.hour >= 9) &
        (df['x_end_datetime'].dt.hour <= 18)
    ].copy()

    # 3) Somar as horas (x_end_datetime - x_start_datetime)
    total_horas_dec = 0.0
    for _, row in df_filtrado.iterrows():
        delta = row['x_end_datetime'] - row['x_start_datetime']
        total_horas_dec += delta.total_seconds() / 3600.0  # converte para horas decimais

    # 4) Converter horas decimais para string "HH:MM"
    horas_inteiras = int(total_horas_dec)  # ex.: 146
    minutos = int(round((total_horas_dec - horas_inteiras) * 60))  # ex.: 0.9 * 60 = 54

    # Montar a string no formato "HH:MM" 
    # (sem zero à esquerda para horas muito grandes, mas minutos em 2 dígitos)
    resultado = f"{horas_inteiras}:{minutos:02d}"

    return resultado


def calcular_horas_comissao(meta, horas_uteis_str):
    """
    Calcula quantas horas acima (ou abaixo) da meta há, com base nas horas úteis.
    
    Args:
        meta (int|float): Meta de horas.
        horas_uteis_str (str): Total de horas úteis em formato "HH:MM".
        
    Returns:
        str: Diferença no formato "HH:MM" ou "-HH:MM".
    """
    # 1) Separar HH:MM
    hh, mm = horas_uteis_str.split(":")
    
    # 2) Converter para decimal
    horas_uteis_decimal = float(hh) + float(mm)/60.0

    # 3) Subtrair a meta
    diferenca_decimal = horas_uteis_decimal - meta

    # 4) Transformar a diferença em string "HH:MM"
    horas_abs = int(abs(diferenca_decimal))
    minutos_abs = int(round((abs(diferenca_decimal) - horas_abs) * 60))
    resultado = f"{horas_abs:02d}:{minutos_abs:02d}"

    # 5) Se negativo, prefixar "-"
    if diferenca_decimal < 0:
        resultado = f"-{resultado}"

    return resultado
