import plotly.express as px
from utils import *
from charts import *
import streamlit as st
import holidays
import calendar
import datetime
import pandas as pd
import pytz
from datetime import datetime
from dateutil import parser  # Usaremos parser para lidar com strings de data/hora
import ssl
from xmlrpc import client


dotenv.load_dotenv()
EMAIL_ODOO = os.getenv('EMAIL_ODOO')
API_KEY_ODOO = os.getenv('API_KEY_ODOO')
if EMAIL_ODOO == 'SEU_EMAIL_NO_ODOO' or API_KEY_ODOO == 'SUA_CHAVE_DE_API':
    st.warning('VOCÊ NÃO CONFIGUROU O ARQUIVO .ENV...')

SALARIO_JUNIOR = st.secrets.odoo.salario_junior
SALARIO_PLENO = st.secrets.odoo.salario_pleno
SALARIO_SENIOR = st.secrets.odoo.salario_senior

st.set_page_config(layout="wide")
st.title('Analítico da Meta Faturável 📊')
st.caption(f'## Veja como você vai se sair esse em **{datetime.now().strftime("%m/%Y")}**')
uid_odoo = None

hoje = datetime.today()
data_inicial = primeiro_dia_util_mes(hoje)
data_final = ultimo_dia_util_mes(hoje)

col1, col2 = st.columns(2)
email_odoo = col1.text_input('Seu email do Odoo', type="default")
api_key_odoo = col1.text_input('Sua API Key do Odoo', type="password")
usuario_rpc = col1.text_input('Seu nome completo', type="default")
if not usuario_rpc:
    col1.warning('Você não colocou seu nome...')
meta = col2.radio('Qual a sua meta?', ('80', '100', '120'), index=2)
initial_date = col1.date_input('Data inicial', value=data_inicial, format='DD/MM/YYYY')
end_date = col1.date_input('Data final', value=data_final, format='DD/MM/YYYY')
if meta == '80':
    salario_bruto = col2.number_input('Seu salário bruto', value=float(SALARIO_JUNIOR), min_value=0.0, step=0.01, format="%.2f")
elif meta == '100':
    salario_bruto = col2.number_input('Seu salário bruto', value=float(SALARIO_PLENO), min_value=0.0, step=0.01, format="%.2f")
elif meta == '120':
    salario_bruto = col2.number_input('Seu salário bruto', value=float(SALARIO_SENIOR), min_value=0.0, step=0.01, format="%.2f")
executar = col1.button('Veja a sua meta!')
apagar_minhas_horas = col2.button('Apagar planilha de histórico!', type="primary")
if apagar_minhas_horas:
    try:
        os.remove('minhas_horas_totais.xlsx')
    except:pass

if executar and usuario_rpc:
    URL_RPC = st.secrets.odoo.url_rpc
    DB_RPC = st.secrets.odoo.db_rpc
    USERNAME_RPC = email_odoo.strip()
    PASSWORD_RPC = api_key_odoo.strip()
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
    records_lines = get_odoo2('account.analytic.line', data, AUTH, filter_odoo)
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
    if df.empty:
        print('O df está vazio')
    # else:
    #     df = atualizar_e_salvar_excel_robusto(df, initial_date, end_date, nome_arquivo='minhas_horas_totais.xlsx')


    total_de_horas = soma_todas_as_horas(df)
    dias_uteis, distribuicao_horas = calcular_horas_restantes(df, int(meta))
    distribuicao_horas_formatada = [round(horas, 2) for horas in distribuicao_horas]
    date_analisys_meta = initial_date.strftime('%m/%Y')

    resultado = tarefa_mais_trabalhada(df)
    col1.markdown(resultado)
    
    col2.markdown('### Dados Estratégicos')
    col2.markdown(f"##### Mês da análise selecionada: **{date_analisys_meta}**")
    col2.markdown(f"##### Dias úteis necessários para bater a meta 🗓️: **{dias_uteis}**")
    col2.markdown(f"##### Distribuição de horas por dia útil para bater a meta: **{distribuicao_horas_formatada}**")
    col2.markdown(f"##### Total de horas faturaveis até agora 🕑: **{total_de_horas}**")
    col2.markdown(f"##### Horas extras (comissão) feita 💰: **{calcular_diferenca_horas(int(meta), total_de_horas)}**")
    col2.markdown('----')
    col2.markdown(f"##### Salário líquido com descontos de 15,52% (INSS e IR) 🤑: **{calcular_salario_liquido(salario_bruto)}**")
    col2.markdown(f"##### Comissão liquida com descontos de 15,52% (INSS e IR) 🤑: **{calcular_diferenca(calcular_diferenca_horas(int(meta), total_de_horas), salario_bruto)}**")
    col2.markdown(f"##### Salário com comissão líquido com descontos de 15,52% (INSS e IR) 🤑: **{calcular_salario(calcular_diferenca_horas(int(meta), total_de_horas), salario_bruto)}**")
    col2.markdown('----')

    # st.success('Alguns analíticos...')
    col1.plotly_chart(criar_grafico_pizza_task(df, 'task'))
    col2.plotly_chart(criar_grafico_pizza(df, 'cliente'))
    # st.plotly_chart(analisar_horas_extras(df))
    
    df_horas_extras = filtrar_fora_horario_comercial(df)
    col1.plotly_chart(grafico_tempo_gasto_por_dia(df))
    col2.plotly_chart(grafico_tempo_gasto_por_dia_hora_extra(df_horas_extras))
    st.plotly_chart(grafico_tempo_vs_meta(df, meta=int(meta)))
    texto = concatenar_colunas_em_string(df)
    texto = re.sub(r' irá | foi | nao | um | ele | não | para | 0 | na | se | o | em | ou | que | e | quando | por | para | de | da | ao | pela | x | uma', ' ', texto, flags=re.IGNORECASE)
    gerar_nuvem_de_palavras(texto, background_color='black', width=550, height=550, scale=15, max_font_size=50)
    # st.table(df_horas_extras)
    
    # with st.expander('$?'):
    #     honorarios = calcular_honorarios_total(df, initial_date, end_date)
    #     st.write(f"Quanto você colocou na empresa 💰: {honorarios}")

    # st.dataframe(df)
