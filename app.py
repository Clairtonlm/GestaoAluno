from flask import Flask, render_template, request, redirect, session, url_for
from supabase import create_client, Client
from weasyprint import HTML
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Chave secreta mais segura

# Configurações do Supabase
SUPABASE_URL = "https://jolrkzfdkoqdfuyigkfg.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpvbHJremZka29xZGZ1eWlna2ZnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzQ1NTczOTgsImV4cCI6MjA1MDEzMzM5OH0.MXKkb00xbj1TK0_c6X8n5c1BKSMF5UVrvJEjZVATOp0"

# Inicializar Supabase com tratamento de erro
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    print(f"Erro ao inicializar Supabase: {e}")
    supabase = None

@app.route('/')
def index():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        if not supabase:
            error = "Erro de configuração do Supabase"
            return render_template('login.html', error=error)
        
        try:
            # Log detalhado do login
            print(f"Tentando login com email: {email}")
            
            # Método atual de autenticação do Supabase
            response = supabase.auth.sign_in_with_password({
                "email": email, 
                "password": password
            })
            print("Resposta de autenticação:", response)
            
            # Verificar se a autenticação foi bem-sucedida
            if response and hasattr(response, 'user'):
                session['user'] = response.user.id
                return redirect(url_for('dashboard'))
            else:
                error = "Falha na autenticação. Verifique suas credenciais."
                print("Detalhes do erro de autenticação:", response)
        
        except Exception as e:
            # Captura e registra qualquer erro de autenticação
            print(f"Erro de login completo: {type(e).__name__} - {str(e)}")
            error = f"Erro de login: {str(e)}"
    
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if not supabase:
            error = "Erro de configuração do Supabase"
            return render_template('register.html', error=error)
        
        # Validação de senha
        if password != confirm_password:
            error = "As senhas não coincidem"
            return render_template('register.html', error=error)
        
        try:
            # Log detalhado do registro
            print(f"Tentando registrar usuário: {email}")
            
            # Método atual de registro do Supabase
            response = supabase.auth.sign_up({
                "email": email, 
                "password": password
            })
            print("Resposta de registro:", response)
            
            # Verificar se o usuário foi criado com sucesso
            if response and hasattr(response, 'user'):
                print(f"Usuário registrado com sucesso: {response.user}")
                return redirect(url_for('login'))
            else:
                error = "Falha ao registrar usuário"
                print("Detalhes do erro de registro:", response)
        
        except Exception as e:
            # Captura e registra qualquer erro de registro
            print(f"Erro de registro completo: {type(e).__name__} - {str(e)}")
            error = f"Erro de registro: {str(e)}"
    
    return render_template('register.html', error=error)

@app.route('/recover', methods=['GET', 'POST'])
def recover():
    if request.method == 'POST':
        email = request.form['email']
        response = supabase.auth.api.reset_password_for_email(email)
        if response.get('error'):
            return "Erro ao enviar e-mail de recuperação!"
        return "E-mail de recuperação enviado com sucesso!"
    return render_template('recover.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        subject = request.form['subject']
        grade = float(request.form['grade'])
        supabase.table('grades').insert({'user_id': session['user'], 'subject': subject, 'grade': grade}).execute()
    
    data = supabase.table('grades').select('*').eq('user_id', session['user']).execute()
    grades = data['data']
    avg_grade = sum(item['grade'] for item in grades) / len(grades) if grades else 0

    return render_template('dashboard.html', grades=grades, avg_grade=avg_grade)

@app.route('/boletim')
def boletim():
    if 'user' not in session:
        return redirect(url_for('login'))

    data = supabase.table('grades').select('*').eq('user_id', session['user']).execute()
    grades = data['data']
    avg_grade = sum(item['grade'] for item in grades) / len(grades) if grades else 0

    html = render_template('boletim.html', grades=grades, avg_grade=avg_grade)
    pdf = HTML(string=html).write_pdf()
    
    response = app.response_class(pdf, mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'inline; filename=boletim.pdf'
    return response

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
