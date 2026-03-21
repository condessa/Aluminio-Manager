# Código certo ec comprovado
import smtplib
from email.message import EmailMessage

remetente = 'aluminiomanager@gmail.com'  
destinatario = 'condessasilva@gmail.com'  # substituir pelo email da firma da ficha de registo
assunto = 'Envio de chave'

# Gerar ou definir a chave (isso viria do seu programa de gerar chaves)
chave_ativacao = "LOKI-FRTV-ARDT-ADFE"  # exemplo

# Montar a mensagem de forma limpa
mensagem = f"""
Obrigado por se registar no Aluminio Manager.
Esta é a sua chave de ativação: {chave_ativacao}
Esta chave é vitalícia.
"""

# Senha de app do Gmail (já está correta)
senha = 'qerz vupu wgai aqif'

msg = EmailMessage()
msg['From'] = remetente
msg['To'] = destinatario
msg['Subject'] = assunto
msg.set_content(mensagem)

try:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as email:
        email.login(remetente, senha)
        email.send_message(msg)
    print('✅ Email foi enviado com sucesso')
except Exception as e:
    print(f'❌ Erro ao enviar email: {e}')

