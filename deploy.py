import os
packages = 'payconpy streamlit plotly'

print('Criando arquivo .env para você colocar o usuário e senha')
with open('.env', 'w') as f:
    f.write(f'EMAIL_ODOO=SEU_EMAIL_NO_ODOO\n')
    f.write(f'API_KEY_ODOO=SUA_CHAVE_DE_API\n')
    f.write(f'SALARIO_JUNIOR=1983.33\n')
    f.write(f'SALARIO_PLENO=3345.15\n')
    f.write(f'SALARIO_SENIOR=4627.76\n')
    
    
print('Criando Ambiente Virtual')
os.system('python -m venv venv')
print('Criado!')
print('Baixando pacotes, vai demorar, pegue um café!')
os.system(f'.\\venv\\Scripts\\pip.exe install {packages}')
print('Executando o App')
os.system(f'streamlit run .\main.py')
