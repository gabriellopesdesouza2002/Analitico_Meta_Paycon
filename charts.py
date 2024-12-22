import plotly.express as px
import streamlit as st

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
    cliente_counts.columns = ['Tarefa', 'Execuções']

    # Criar o gráfico de pizza
    fig = px.pie(
        cliente_counts,
        names='Tarefa',
        values='Execuções',
        title='Distribuição de Execução por CLIENTE',
        hole=0.3,
    )

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig)
