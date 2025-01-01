import plotly.express as px
import streamlit as st
import pandas as pd
import calendar
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
import datetime
import holidays


def grafico_tempo_gasto_por_dia(df, 
                                coluna_data="x_start_datetime", 
                                coluna_tempo="unit_amount"):
    """
    Gera um gráfico de linha mostrando o tempo total gasto por dia,
    MAS APENAS considerando as tarefas cujo horário de início está 
    entre 9h e 18h (sem tratar partes de tarefas que comecem antes ou terminem depois).

    Args:
        df (pd.DataFrame): O DataFrame contendo os dados.
        coluna_data (str): Nome da coluna com as datas/hora de início.
        coluna_tempo (str): Nome da coluna com o tempo da tarefa (unit_amount).

    Returns:
        plotly.graph_objs._figure.Figure: Figura do Plotly com o gráfico de linha.
    """
    # Converte a coluna de datas para datetime
    df[coluna_data] = pd.to_datetime(df[coluna_data])
    
    # Extrai somente a hora em outra coluna para facilitar o filtro
    df["hora_inicio"] = df[coluna_data].dt.hour

    # Filtrar apenas registros que iniciaram entre 9:00 e 17:59
    df_filtrado = df[(df["hora_inicio"] >= 9) & (df["hora_inicio"] < 18)]

    # Criar uma coluna com apenas as datas (sem o horário)
    df_filtrado["dia"] = df_filtrado[coluna_data].dt.date

    # Agrupar por dia e somar o tempo (unit_amount)
    df_resumo = df_filtrado.groupby("dia")[coluna_tempo].sum().reset_index()

    # Criar o gráfico de linha
    fig = px.line(
        df_resumo, 
        x="dia", 
        y=coluna_tempo, 
        title="Tempo Gasto por Dia (Somente Inícios entre 9h e 18h)",
        labels={"dia": "Dia", coluna_tempo: "Tempo Gasto (Horas)"}
    )
    fig.update_traces(mode="lines+markers")

    return fig
    

def grafico_tempo_gasto_por_dia_hora_extra(df, coluna_data_inicio="x_start_datetime", coluna_data_fim="x_end_datetime", coluna_tempo="unit_amount"):
    """
    Gera um gráfico de linha mostrando o tempo total gasto por dia considerando apenas horas extras
    (antes das 9h ou após as 18h).

    Args:
        df (pd.DataFrame): O DataFrame contendo os dados.
        coluna_data_inicio (str): Nome da coluna com as datas de início.
        coluna_data_fim (str): Nome da coluna com as datas de término.
        coluna_tempo (str): Nome da coluna com o tempo da tarefa (unit_amount).

    Returns:
        plotly.graph_objects.Figure: Gráfico de linha com as horas extras por dia.
    """
    # Converter as colunas de datas para datetime
    df[coluna_data_inicio] = pd.to_datetime(df[coluna_data_inicio])
    df[coluna_data_fim] = pd.to_datetime(df[coluna_data_fim])

    # Filtrar registros antes das 9h ou após as 18h
    filtro_hora_extra = (
        (df[coluna_data_inicio].dt.time < datetime.time(9, 0)) | 
        (df[coluna_data_fim].dt.time > datetime.time(18, 0))
    )
    df_horas_extras = df[filtro_hora_extra]

    # Criar uma coluna com apenas as datas (sem o horário)
    df_horas_extras["dia"] = df_horas_extras[coluna_data_inicio].dt.date

    # Agrupar por dia e somar o tempo das tarefas
    df_resumo = df_horas_extras.groupby("dia")[coluna_tempo].sum().reset_index()

    # Criar o gráfico de linha
    fig = px.line(
        df_resumo, 
        x="dia", 
        y=coluna_tempo, 
        title="Tempo Gasto por Dia (Horas Extras)",
        labels={"dia": "Dia", coluna_tempo: "Tempo Gasto (Horas)"}
    )
    fig.update_traces(mode="lines+markers")

    return fig
def grafico_horas_extras(df, coluna_inicio="x_start_datetime", coluna_fim="x_end_datetime"):
    """
    Gera um gráfico de linha com os dias e as horas extras calculadas.

    Args:
        df (pd.DataFrame): O DataFrame contendo os dados.
        coluna_inicio (str): Nome da coluna com os horários de início.
        coluna_fim (str): Nome da coluna com os horários de término.

    Returns:
        None: Exibe o gráfico diretamente no Streamlit.
    """
    # Converter as colunas para datetime
    df[coluna_inicio] = pd.to_datetime(df[coluna_inicio])
    df[coluna_fim] = pd.to_datetime(df[coluna_fim])

    # Criar uma coluna com a data (sem o horário)
    df["dia"] = df[coluna_inicio].dt.date

    # Definir os horários de início e fim do expediente
    hora_inicio_comercial = pd.Timestamp("09:00:00").time()
    hora_fim_comercial = pd.Timestamp("18:00:00").time()

    # Função para calcular as horas extras
    def calcular_horas_extras(row):
        inicio = row[coluna_inicio]
        fim = row[coluna_fim]

        # Verificar horas antes do início do expediente
        horas_extras_antes = 0
        if inicio.time() < hora_inicio_comercial:
            horas_extras_antes = (pd.Timestamp.combine(inicio.date(), hora_inicio_comercial) - inicio).total_seconds() / 3600

        # Verificar horas após o fim do expediente
        horas_extras_depois = 0
        if fim.time() > hora_fim_comercial:
            horas_extras_depois = (fim - pd.Timestamp.combine(fim.date(), hora_fim_comercial)).total_seconds() / 3600

        return horas_extras_antes + horas_extras_depois

    # Aplicar a função para calcular as horas extras
    df["horas_extras"] = df.apply(calcular_horas_extras, axis=1)

    # Agrupar por dia e somar as horas extras
    df_resumo = df.groupby("dia")["horas_extras"].sum().reset_index()

    # Criar o gráfico de linha
    fig = px.line(
        df_resumo, 
        x="dia", 
        y="horas_extras", 
        title="Horas Extras por Dia",
        labels={"dia": "Dia", "horas_extras": "Horas Extras"}
    )
    fig.update_traces(mode="lines+markers")

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig)




def gerar_nuvem_de_palavras(texto, max_words=100, background_color="#ffffff", width=800, height=400, scale=2, max_font_size=40):
    """
    Gera e exibe uma nuvem de palavras.

    Parâmetros:
        texto (str): O texto para gerar a nuvem de palavras.
        max_words (int): O número máximo de palavras na nuvem.
        background_color (str): Cor de fundo da nuvem (em formato hexadecimal).
        width (int): Largura da imagem da nuvem de palavras.
        height (int): Altura da imagem da nuvem de palavras.
        scale (float): Fator de escala para aumentar a qualidade da imagem.
        max_font_size (int): Tamanho máximo da fonte para as palavras.
    """
    if not texto.strip():
        st.warning("Por favor, insira algum texto!")
        return

    # Geração da nuvem de palavras com dimensões ajustadas e qualidade melhorada
    wordcloud = WordCloud(
        max_words=max_words,
        background_color=background_color,
        width=width,
        height=height,
        scale=scale,
        max_font_size=max_font_size
    ).generate(texto)

    # Plotando a nuvem de palavras
    fig, ax = plt.subplots(figsize=(width / 100, height / 100))  # Ajuste do tamanho da figura
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig, use_container_width=False)



def criar_grafico_pizza_task(df, campo_task):
    """
    Cria e exibe um gráfico de pizza no Streamlit com base na distribuição do campo 'task'.
    
    Parâmetros:
    - df: DataFrame contendo os dados.
    - campo_task: Nome da coluna que representa as tasks no DataFrame.
    """
    # Contar a quantidade de ocorrências por task
    task_counts = df[campo_task].value_counts().reset_index()
    task_counts.columns = ['Task', 'Execuções']

    # Criar o gráfico de pizza
    fig = px.pie(
        task_counts,
        names='Task',
        values='Execuções',
        title='Quantas execuções por Tarefa',
        hole=0.3,
    )

    # Exibir o gráfico no Streamlit
    return fig
    


def criar_grafico_pizza(df, campo_cliente):
    """
    Cria e exibe um gráfico de pizza no Streamlit com base na distribuição do campo 'cliente'.
    
    Parâmetros:
    - df: DataFrame contendo os dados.
    - campo_cliente: Nome da coluna que representa os clientes no DataFrame.
    """
    # Contar a quantidade de ocorrências por cliente
    cliente_counts = df[campo_cliente].value_counts().reset_index()
    cliente_counts.columns = ['Cliente', 'Execuções']

    # Criar o gráfico de pizza
    fig = px.pie(
        cliente_counts,
        names='Cliente',
        values='Execuções',
        title='Distribuição de Execução por Cliente',
        hole=0.3,
    )

    # Exibir o gráfico no Streamlit
    return fig
    


def analisar_horas_extras(df, col_start='x_start_datetime', col_unit='unit_amount'):
    """
    Analisa as horas trabalhadas fora do horário padrão (após 18h ou fins de semana).
    
    :param df: DataFrame com os dados.
    :param col_start: Coluna com a data/hora de início (padrão: 'x_start_datetime').
    :param col_unit: Coluna com as horas faturáveis (padrão: 'unit_amount').
    :return: Gráfico de barras Plotly.
    """
    # Garantir que as colunas sejam datetime e numéricas
    df[col_start] = pd.to_datetime(df[col_start], errors='coerce')
    df[col_unit] = pd.to_numeric(df[col_unit], errors='coerce')

    # Adicionar colunas auxiliares
    df['is_weekend'] = df[col_start].dt.weekday >= 5  # Sábado e Domingo são 5 e 6
    df['hour'] = df[col_start].dt.hour
    df['is_extra'] = df['is_weekend'] | (df['hour'] >= 18)  # Fins de semana ou após 18h

    # Calcular as horas extras e normais
    total_horas = df[col_unit].sum()
    total_horas_extras = df.loc[df['is_extra'], col_unit].sum()
    percentual_extras = (total_horas_extras / total_horas) * 100 if total_horas > 0 else 0

    # Preparar os dados para o gráfico
    horas_extras = df.loc[df['is_extra'], col_unit].sum()
    horas_normais = df.loc[~df['is_extra'], col_unit].sum()
    categorias = ['Normais', 'Extras']
    valores = [horas_normais, horas_extras]

    # Criar o gráfico de barras
    fig = go.Figure(
        data=[
            go.Bar(x=categorias, y=valores, marker_color=['blue', 'red'])
        ]
    )

    # Configurar o layout do gráfico
    fig.update_layout(
        title=f"Análise de Horas Extras (Extras: {percentual_extras:.2f}%)",
        xaxis_title="Tipo de Hora",
        yaxis_title="Total de Horas",
        template="plotly_dark",
    )

    return fig, total_horas_extras, percentual_extras


import pandas as pd
import plotly.graph_objects as go

import pandas as pd
import plotly.graph_objects as go

import pandas as pd
import plotly.graph_objects as go

def analisar_horas_extras_com_df_atualizado(df, col_start='x_start_datetime', col_unit='unit_amount', col_project='cliente', col_task='task'):
    """
    Analisa as horas trabalhadas fora do horário padrão (após 18h ou fins de semana)
    e retorna o gráfico e o DataFrame filtrado.

    :param df: DataFrame com os dados.
    :param col_start: Coluna com a data/hora de início (padrão: 'x_start_datetime').
    :param col_unit: Coluna com as horas faturáveis (padrão: 'unit_amount').
    :param col_project: Coluna com o nome do projeto (padrão: 'project_id').
    :param col_task: Coluna com o nome da tarefa (padrão: 'task_id').
    :return: Gráfico de barras Plotly e DataFrame com horas extras.
    """
    # Garantir que a coluna seja datetime e sem alterações de fuso horário
    df[col_start] = pd.to_datetime(df[col_start], errors='coerce')

    # Garantir que o fuso horário seja "America/Sao_Paulo" sem re-aplicar mudanças
    if df[col_start].dt.tz is None:
        df[col_start] = df[col_start].dt.tz_localize('America/Sao_Paulo')

    # Garantir que a coluna de horas seja numérica
    df[col_unit] = pd.to_numeric(df[col_unit], errors='coerce')

    # Adicionar colunas auxiliares
    df['is_weekend'] = df[col_start].dt.weekday >= 5  # Sábado e Domingo são 5 e 6
    df['hour'] = df[col_start].dt.hour
    df['is_extra'] = df['is_weekend'] | (df['hour'] >= 18)  # Fins de semana ou após 18h

    # Calcular as horas extras e normais
    total_horas = df[col_unit].sum()
    total_horas_extras = df.loc[df['is_extra'], col_unit].sum()
    percentual_extras = (total_horas_extras / total_horas) * 100 if total_horas > 0 else 0

    # Preparar os dados para o gráfico
    horas_extras = df.loc[df['is_extra'], col_unit].sum()
    horas_normais = df.loc[~df['is_extra'], col_unit].sum()
    categorias = ['Normais', 'Extras']
    valores = [horas_normais, horas_extras]

    # Criar o gráfico de barras
    fig = go.Figure(
        data=[
            go.Bar(x=categorias, y=valores, marker_color=['blue', 'red'])
        ]
    )

    # Configurar o layout do gráfico
    fig.update_layout(
        title=f"Análise de Horas Extras (Extras: {percentual_extras:.2f}%)",
        xaxis_title="Tipo de Hora",
        yaxis_title="Total de Horas",
        template="plotly_dark",
    )

    # Filtrar apenas as horas extras para retornar como DataFrame
    df_horas_extras = df[df['is_extra']].copy()

    # Adicionar a coluna 'Tipo de Hora Extra' diretamente antes de remover 'is_weekend'
    df_horas_extras['Tipo de Hora Extra'] = df_horas_extras['is_weekend'].map(
        {True: 'Fim de Semana', False: 'Após 18h'}
    )

    # Selecionar colunas relevantes para análise
    df_horas_extras = df_horas_extras[[col_start, col_unit, col_project, col_task, 'hour', 'Tipo de Hora Extra']].copy()

    # Renomear colunas para melhor visualização
    df_horas_extras.rename(
        columns={
            col_start: 'Data/Hora Início',
            col_unit: 'Horas Faturáveis',
            col_project: 'Projeto',
            col_task: 'Tarefa',
            'hour': 'Hora do Dia'
        },
        inplace=True
    )

    return fig, df_horas_extras


def grafico_tempo_vs_meta(df, coluna_data="x_start_datetime", coluna_tempo="unit_amount", meta=40):
    """
    Gera um gráfico de linha mostrando o tempo gasto por dia em comparação com as horas necessárias para atingir a meta.

    Args:
        df (pd.DataFrame): O DataFrame contendo os dados.
        coluna_data (str): Nome da coluna com as datas.
        coluna_tempo (str): Nome da coluna com o tempo da tarefa (unit_amount).
        meta (int): Meta de horas a serem distribuídas.

    Returns:
        fig (plotly.graph_objects.Figure): O gráfico comparando horas gastas e meta.
    """
    # Converter a coluna de datas para datetime
    df[coluna_data] = pd.to_datetime(df[coluna_data])

    # Criar uma coluna com apenas as datas (sem o horário)
    df["dia"] = df[coluna_data].dt.date

    # Agrupar por dia e somar o tempo das tarefas
    df_resumo = df.groupby("dia")[coluna_tempo].sum().reset_index()
    df_resumo = df_resumo.sort_values("dia")

    # Calcular a distribuição das horas necessárias
    dias_uteis = len(df_resumo)
    horas_por_dia = meta / dias_uteis
    distribuicao_horas_formatada = [round(horas_por_dia, 2)] * dias_uteis

    # Adicionar a distribuição ao DataFrame
    df_resumo["horas_meta"] = distribuicao_horas_formatada

    # Criar o gráfico comparativo
    fig = px.line(
        df_resumo,
        x="dia",
        y=[coluna_tempo, "horas_meta"],
        title="Comparação de Tempo Gasto e Meta Diária (Abaixo da linha, está fora de bater a meta do dia)",
        labels={"dia": "Dia", "value": "Horas", "variable": "Métrica"},
    )
    fig.update_traces(mode="lines+markers")

    return fig


def plot_bubble_hours(df):
    # Converte a coluna de data/hora para datetime
    df["datetime"] = pd.to_datetime(df["x_start_datetime"], errors="coerce")

    # Extrai o dia numérico da semana (0=Seg, 1=Ter, ..., 6=Dom)
    df["weekday_num"] = df["datetime"].dt.dayofweek

    # Filtra apenas de segunda(0) a sexta(4)
    df = df[df["weekday_num"] <= 4]

    # Mapeia manualmente o dia da semana
    day_map_pt = {
       0: "segunda-feira",
       1: "terça-feira",
       2: "quarta-feira",
       3: "quinta-feira",
       4: "sexta-feira"
    }
    df["dia_semana"] = df["weekday_num"].map(day_map_pt)

    # Define a ordem (segunda a sexta)
    ordem_dias = [
       "segunda-feira", "terça-feira",
       "quarta-feira",  "quinta-feira",
       "sexta-feira"
    ]
    df["dia_semana"] = pd.Categorical(df["dia_semana"], categories=ordem_dias, ordered=True)

    # Mapeia manualmente o mês
    month_map_pt = {
       1: "jan",   2: "fev",   3: "mar",  4: "abr",
       5: "mai",   6: "jun",   7: "jul",  8: "ago",
       9: "set",  10: "out",  11: "nov", 12: "dez"
    }
    df["month_num"] = df["datetime"].dt.month
    df["mes"] = df["month_num"].map(month_map_pt)

    # Soma as horas (unit_amount) por Mês e Dia da Semana
    grouped = df.groupby(["mes", "dia_semana"], as_index=False)["unit_amount"].sum()

    # Cria o gráfico de bolhas:
    #   - Eixo X: dia da semana (segunda a sexta)
    #   - Eixo Y: mês (jan. a dez.)
    fig = px.scatter(
        grouped,
        x="dia_semana",
        y="mes",
        size="unit_amount",
        color="unit_amount",
        color_continuous_scale="Reds",
        size_max=50,
        title="Frequência de Horas por Mês (Quais dias da semana que você está mais engajado)"
    )

    # Inverte a ordem do eixo Y se quiser do jan para baixo até dez
    fig.update_yaxes(autorange="reversed")

    return fig


def gerar_grafico_distribuicao_horas(lista_horas, meta=120):
    """
    Gera um gráfico de barras com a distribuição das horas por dia útil para atingir a meta.
    
    Parâmetros:
    - lista_horas (list): Lista de horas já registradas.
    - meta (int): Meta de horas desejada.
    
    Retorna:
    - fig (plotly.graph_objects.Figure): Gráfico de barras com a distribuição.
    """
    # Total de horas já registradas
    total_hours = sum(lista_horas)
    horas_restantes = max(0, meta - total_hours)

    # Configuração dos feriados no Brasil
    brasil_holidays = holidays.Brazil()

    # Data de hoje
    hoje = datetime.date.today()

    # Lista de dias úteis futuros, distribuição de horas e datas
    distribuicao_horas = []
    datas = []

    while horas_restantes > 0:
        # Incrementa o dia
        hoje += datetime.timedelta(days=1)

        # Verifica se é dia útil
        if hoje.weekday() < 5 and hoje not in brasil_holidays:
            horas_do_dia = min(8, horas_restantes)  # Aloca no máximo 8 horas por dia
            distribuicao_horas.append(horas_do_dia)
            datas.append(hoje)
            horas_restantes -= horas_do_dia

    # Criação do gráfico com Plotly
    fig = go.Figure(
        data=go.Bar(
            x=[data.strftime("%d/%m/%Y") for data in datas],
            y=distribuicao_horas,
            marker=dict(color="blue"),
        )
    )
    fig.update_layout(
        title="Distribuição de Horas por Dia Útil para Atingir a Meta",
        xaxis_title="Datas (Dias Úteis)",
        yaxis_title="Horas",
        template="plotly_dark",
    )

    return fig