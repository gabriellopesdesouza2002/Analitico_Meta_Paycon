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

try:
    dotenv.load_dotenv()
    LOCALHOST = os.getenv('LOCALHOST', '')
except:
    LOCALHOST = ''

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
e_admin = col1.checkbox('Sou Admin no sistema', value=False)
if e_admin:
    usuario_rpc = col1.text_input('Seu nome', type="default")
    if not usuario_rpc:
        col1.warning('Você não colocou o nome da pessoa...')
else:
    usuario_rpc = ''
initial_date = col2.date_input('Data inicial', value=data_inicial, format='DD/MM/YYYY')
end_date = col2.date_input('Data final', value=data_final, format='DD/MM/YYYY')
meta = col2.radio('Qual a sua meta?', ('80', '100', '120'), index=2)
executar = col1.button('VEJA A SUA META!', type="primary", help='Clique aqui para ver o seu desempenho na data selecionada')

if LOCALHOST:
    apagar_minhas_horas = col2.button('Apagar planilha de histórico!', type="primary")
    if apagar_minhas_horas:
        try:
            os.remove('minhas_horas_totais.xlsx')
        except:pass

if executar:
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
        "x_tipo_lancamento": [],
        "name": [],
    }

    for i, record in enumerate(records_lines):
        id = record['id']
        name = record['name']
        x_end_datetime = record['x_end_datetime']
        x_tipo_lancamento = record['x_tipo_lancamento_id'][-1].lower()
        x_start_datetime = record['x_start_datetime']
        x_faturavel = record['x_faturavel']
        unit_amount = record['unit_amount']
        task = record['task_id'][1]
        cliente = record['project_id'][1]
        x_honorarios = record['x_honorarios']
        if 'call' in x_tipo_lancamento.lower():
            continue
            unit_amount = unit_amount / 2
        if 'Paycon - Comissionamento' in cliente:
            continue
        df_base['id'].append(id)
        df_base['name'].append(name)
        df_base['x_faturavel'].append(x_faturavel)
        df_base['x_end_datetime'].append(x_end_datetime)
        df_base['x_start_datetime'].append(x_start_datetime)
        df_base['unit_amount'].append(unit_amount)
        df_base['task'].append(task)
        df_base['cliente'].append(cliente)
        df_base['x_honorarios'].append(x_honorarios)
        df_base['x_tipo_lancamento'].append(x_tipo_lancamento)
        
    df = pd.DataFrame.from_dict(df_base)
    # st.table(df)
    if df.empty:
        st.warning(f'O Não há lançamentos para análise no mês selecionado...\nA data inicial escolhida foi: {initial_date.strftime("%d/%m/%Y")}\nA data final escolhida foi: {end_date.strftime("%d/%m/%Y")}')
        st.stop()
    else:
        if LOCALHOST:
            df = atualizar_e_salvar_excel_robusto(df, initial_date, end_date, nome_arquivo='minhas_horas_totais.xlsx')

    st.balloons()

    total_de_horas = soma_todas_as_horas(df)
    dias_uteis, distribuicao_horas = calcular_horas_restantes(df, int(meta))
    distribuicao_horas_formatada = [round(horas, 2) for horas in distribuicao_horas]
    date_analisys_meta = initial_date.strftime('%m/%Y')

    
    # col2.markdown(f"##### Dias úteis necessários para bater a meta 🗓️: **{dias_uteis}**")
    data_meta = data_para_bater_meta(distribuicao_horas_formatada, pais='BR', data_inicio=datetime.now())
    dia_bater_meta = data_meta.strftime('%d/%m/%Y')
    col1_metric, col2_metric, col3_metric, col4_metric, col5_metric, col6_metric = st.columns([1, 1, 1, 1, 1, 1]) 
    col1_metric.metric('Dias úteis necessários para bater a meta', value=len(distribuicao_horas_formatada), delta=f'{meta} Horas')
    col2_metric.metric('Horas faltantes para bater a meta', value=round(sum(distribuicao_horas)), delta=f'{meta} Horas')
    col3_metric.metric('Total de horas faturaveis até agora', value=total_de_horas, delta=f'{meta} Horas')
    col4_metric.metric('Horas feitas das 09h a 18h (considerado para iniciar a receber comissões)', value=soma_horas_9_18(df), delta=f'{meta} Horas')
    col5_metric.metric('Horas que entrarão como comissão (das quais são úteis das 09h a 18h)', value=calcular_horas_comissao(int(meta), soma_horas_9_18(df)))
    col6_metric.metric('Nesse ritmo, você baterá a meta no dia', value=dia_bater_meta)

    st.markdown(f"### Mês da análise selecionada: **{date_analisys_meta}**")
    st.markdown(f"### Distribuição de horas por dia útil para bater a meta: **{distribuicao_horas_formatada}**")

    st.markdown(f"---")
    resultado = tarefa_mais_trabalhada(df)
    st.markdown(resultado)
    st.markdown(f"---")

    # col2.markdown('----')
    # col2.markdown(f"##### Salário líquido com descontos de 15,52% (INSS e IR) 🤑: **{calcular_salario_liquido(salario_bruto)}**")
    # col2.markdown(f"##### Comissão liquida com descontos de 15,52% (INSS e IR) 🤑: **{calcular_diferenca(calcular_diferenca_horas(int(meta), total_de_horas), salario_bruto)}**")
    # col2.markdown(f"##### Salário com comissão líquido com descontos de 15,52% (INSS e IR) 🤑: **{calcular_salario(calcular_diferenca_horas(int(meta), total_de_horas), salario_bruto)}**")
    # col2.markdown('----')

    # st.success('Alguns analíticos...')
    col1_analitic, col2_analitic = st.columns([2, 2]) 
    df_horas_extras = filtrar_fora_horario_comercial(df)
    with col1_analitic:
        st.plotly_chart(criar_grafico_pizza_task(df, 'task'))
        st.plotly_chart(grafico_tempo_gasto_por_dia_hora_extra(df_horas_extras))
    with col2_analitic:
        st.plotly_chart(criar_grafico_pizza(df, 'cliente'))
        st.plotly_chart(grafico_tempo_vs_meta(df, meta=int(meta)))
    st.plotly_chart(grafico_tempo_gasto_por_dia(df))
    st.plotly_chart(plot_bubble_hours(df))
    # col2.plotly_chart(gerar_grafico_distribuicao_horas(distribuicao_horas_formatada, meta=int(meta)))
    # st.plotly_chart(analisar_horas_extras(df))
    
    texto = concatenar_coluna_name_em_string(df)
    texto = limpar_texto(texto)
    st.markdown('### Nuvem de Palavras de todas as descrições das tarefas')
    col1_temp, col2_temp, col3_temp = st.columns([1, 2, 1]) 
    with col2_temp:
        gerar_nuvem_de_palavras(texto, background_color='black', width=1050, height=550, scale=15, max_font_size=100)
    # st.table(df_horas_extras)
    
    if LOCALHOST:
        with st.expander('Quanto colocou na empresa?'):
            honorarios = calcular_honorarios_total(df, initial_date, end_date)
            st.write(f"Quanto você colocou na empresa 💰: {honorarios}")
    
    st.markdown('*Better Days!!!*')
    # st.dataframe(df)
