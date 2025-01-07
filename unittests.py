from utils import *

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

    return salario_liquido

# # Exemplo de uso:
# horas_extras = "09:50"
# horas_extras = "00:00"
# salario_bruto = 4627.76  # senior
# salario_bruto = 3345.15  # pleno
# salario_bruto = 1983.33  # junior
# resultado = calcular_salario(horas_extras, salario_bruto)
# print("Salário líquido:", resultado)

def data_para_bater_meta(lista_tarefas, pais='BR', data_inicio=None):
    # Obtém o país para os feriados
    feriados = holidays.CountryHoliday(pais)
    
    # Define a data de início (hoje, se não for fornecida)
    if data_inicio is None:
        data_inicio = datetime.date.today()
    
    # Inicializa o contador de dias trabalhados
    dias_trabalhados = 0
    data_atual = data_inicio
    
    # Enquanto não atingirmos o número de dias necessários
    while dias_trabalhados < len(lista_tarefas):
        # Verifica se o dia atual é um dia útil (não é sábado, domingo ou feriado)
        if data_atual.weekday() < 5 and data_atual not in feriados:
            dias_trabalhados += 1
        # Se ainda não atingimos a meta, avança para o próximo dia
        if dias_trabalhados < len(lista_tarefas):
            data_atual += datetime.timedelta(days=1)
    
    # Retorna a data em que a meta será batida
    return data_atual

# Exemplo de uso
# Supondo que hoje seja 07/01/2025 (terça-feira)
hoje_simulado = datetime.datetime.now()

# Lista de tarefas
lista_tarefas = [1,2,3,4]  # len = 6

# Calcula a data para bater a meta
data_meta = data_para_bater_meta(lista_tarefas, data_inicio=hoje_simulado)
print(f"Você vai bater a meta no dia: {data_meta.strftime('%d/%m/%Y')}")
