import plotly.express as px
from utils import *
from charts import *
import streamlit as st
import holidays
import calendar
import datetime
import pandas as pd

dotenv.load_dotenv()
EMAIL_ODOO = os.getenv('EMAIL_ODOO')
API_KEY_ODOO = os.getenv('API_KEY_ODOO')

st.set_page_config(layout="wide")
st.title('Analítico da Meta Faturável 📊')
st.caption(f'## Veja como você vai se sair esse em **{datetime.datetime.now().strftime("%m/%Y")}**')
uid_odoo = None

hoje = datetime.date.today()
data_inicial = primeiro_dia_util_mes(hoje)
data_final = ultimo_dia_util_mes(hoje)

col1, col2 = st.columns(2)

usuario_rpc = col1.text_input('Seu nome completo', type="default")
if not usuario_rpc:
    col1.warning('Você não colocou seu nome...')
meta = col2.radio('Qual a sua meta?', ('80', '100', '120'), index=2)
initial_date = col1.date_input('Data inicial', value=data_inicial, format='DD/MM/YYYY')
end_date = col1.date_input('Data final', value=data_final, format='DD/MM/YYYY')

executar = st.button('Veja a sua meta!')


if executar and usuario_rpc:
    URL_RPC = "https://payconautomacoes.odoo.com/"
    DB_RPC = "payconautomacoes"
    USERNAME_RPC = EMAIL_ODOO
    PASSWORD_RPC = API_KEY_ODOO
    AUTH = {
        "URL_RPC": URL_RPC,
        "DB_RPC": DB_RPC,
        "USERNAME_RPC": USERNAME_RPC,
        "PASSWORD_RPC": PASSWORD_RPC
    }
    if uid_odoo is None:
        uid_odoo = authenticate_odoo(AUTH)

    data = {'fields': [
        'id',
        'name',
        'x_faturavel',
        'x_end_datetime',
        'x_start_datetime',
        'unit_amount',
        'task_id',
        'project_id',
        'x_tipo_lancamento_id',
        'x_honorarios',
        'employee_id',
        ]}
    initial_date_formatted = initial_date.strftime('%Y-%m-%d')
    end_date_formatted = end_date.strftime('%Y-%m-%d')
    filter_odoo = ["&", "&", ("date", ">=", initial_date_formatted), ("date", "<=", end_date_formatted), ("employee_id", "ilike", usuario_rpc), ("x_faturavel", "=", 'faturavel')]
    records_lines = get_odoo('account.analytic.line', data, AUTH, filter_odoo)
    df_base = {
        "id" : [],
        "cliente" : [],
        "task" : [],
        "x_faturavel": [],
        "x_end_datetime": [],
        "x_start_datetime":[],
        "unit_amount":[],
        "x_honorarios": [],
        "name": [],
    }

    for i, record in enumerate(records_lines):
        id = record['id']
        name = record['name']
        x_end_datetime = record['x_end_datetime']
        x_start_datetime = record['x_start_datetime']
        x_faturavel = record['x_faturavel']
        unit_amount = record['unit_amount']
        task = record['task_id'][1]
        cliente = record['project_id'][1]
        x_honorarios = record['x_honorarios']
        df_base['id'].append(id)
        df_base['name'].append(name)
        df_base['x_faturavel'].append(x_faturavel)
        df_base['x_end_datetime'].append(x_end_datetime)
        df_base['x_start_datetime'].append(x_start_datetime)
        df_base['unit_amount'].append(unit_amount)
        df_base['task'].append(task)
        df_base['cliente'].append(cliente)
        df_base['x_honorarios'].append(x_honorarios)
    df = pd.DataFrame.from_dict(df_base)
    df = atualizar_e_salvar_excel_robusto(df, initial_date, end_date, nome_arquivo='minhas_horas_totais.xlsx')


    total_de_horas = soma_todas_as_horas(df)
    dias_uteis, distribuicao_horas = calcular_horas_restantes(df, int(meta))
    distribuicao_horas_formatada = [round(horas, 2) for horas in distribuicao_horas]
    date_analisys_meta = initial_date.strftime('%m/%Y')

    resultado = tarefa_mais_trabalhada(df)
    col1.markdown(resultado)
    
    col2.markdown('----')
    col2.markdown('### Dados Estratégicos')
    col2.markdown(f"##### Mês da análise selecionada: **{date_analisys_meta}**")
    # col2.markdown('----')
    col2.markdown(f"##### Dias úteis necessários para bater a meta 🗓️: **{dias_uteis}**")
    # col2.markdown('----')
    col2.markdown(f"##### Distribuição de horas por dia útil para bater a meta: **{distribuicao_horas_formatada}**")
    # col2.markdown('----')
    col2.markdown(f"##### Total de horas faturaveis até agora 🕑: **{total_de_horas}**")
    # col2.markdown('----')
    col2.markdown(f"##### Horas extras (comissão) feita 💰: **{calcular_diferenca_horas(int(meta), total_de_horas)}**")
    col2.markdown('----')

    st.success('Alguns analíticos...')
    criar_grafico_pizza_task(df, 'task')
    criar_grafico_pizza(df, 'cliente')
    # st.plotly_chart(analisar_horas_extras(df))
    with st.expander('$?'):
        honorarios = calcular_honorarios_total(df, initial_date, end_date)
        st.write(f"Quanto você colocou na empresa 💰: {honorarios}")

    # st.dataframe(df)
