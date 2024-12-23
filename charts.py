import plotly.express as px
import streamlit as st
import pandas as pd
import calendar
import plotly.graph_objects as go


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
    st.plotly_chart(fig)


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
    st.plotly_chart(fig)


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

