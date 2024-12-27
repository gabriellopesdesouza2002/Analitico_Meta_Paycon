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

# Exemplo de uso:
horas_extras = "09:50"
horas_extras = "00:00"
salario_bruto = 4627.76  # senior
salario_bruto = 3345.15  # pleno
salario_bruto = 1983.33  # junior
resultado = calcular_salario(horas_extras, salario_bruto)
print("Salário líquido:", resultado)