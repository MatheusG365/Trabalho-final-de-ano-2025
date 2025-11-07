from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'minha-chave-secreta'

# ---- Dados fictícios ----
usuario_ficticio = {
    "id": 1,
    "nome": "Matheus",
    "email": "teste@teste.com",
    "cpf": "12345678900",
    "tel": "11999999999",
    "senha": "123456"
}

pets_ficticios = [
    {"id": 1, "nome": "Rex", "raca": "Cachorro", "idade": 3, "peso": 12, "medicamento": 50, "soro": 200},
    {"id": 2, "nome": "Mimi", "raca": "Gato", "idade": 2, "peso": 4, "medicamento": 10, "soro": 50}
]

consultas_ficticias = [
    {"id": 1, "pet_agendar": 1, "tipo": "Vacina", "desc": "Vacina anual", "datahora": "2025-11-10T10:00"},
    {"id": 2, "pet_agendar": 2, "tipo": "Consulta geral", "desc": "Check-up", "datahora": "2025-11-11T15:00"}
]

# ---- Rotas ----
@app.route('/')
def index():
    return render_template('index.html', usuario=None)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        flash('Login simulado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('login.html', usuario=None)

@app.route('/logout')
def logout():
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        flash('Cadastro simulado com sucesso!', 'success')
        return redirect(url_for('login'))
    return render_template('cadastrar.html', usuario=None)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', usuario=usuario_ficticio,
                           pets=pets_ficticios, consultas=consultas_ficticias)

@app.route('/cadastrar_pet', methods=['GET', 'POST'])
def cadastrar_pet():
    if request.method == 'POST':
        flash('Pet cadastrado com sucesso (simulado)!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('cadastrarPet.html', usuario=usuario_ficticio)

@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if request.method == 'POST':
        flash('Agendamento criado com sucesso (simulado)!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('agendar.html', usuario=usuario_ficticio, pets=pets_ficticios)

@app.route('/editar_usuario', methods=['GET', 'POST'])
def editar_usuario():
    if request.method == 'POST':
        flash('Dados do usuário atualizados (simulado)!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('editarUser.html', usuario=usuario_ficticio)

@app.route('/editar_pet/<int:id_pet>', methods=['GET', 'POST'])
def editar_pet(id_pet):
    pet = next((p for p in pets_ficticios if p["id"] == id_pet), None)
    especies = ["Cachorro", "Gato", "Coelho", "Pássaro"]  # exemplo de raças
    if request.method == 'POST':
        flash(f'Pet "{pet["nome"]}" atualizado (simulado)!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('editarPet.html', pet=pet, usuario=usuario_ficticio, especies=especies)

@app.route('/remover_pet/<int:id_pet>')
def remover_pet(id_pet):
    flash('Pet removido (simulado)!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/editar_consulta/<int:id_consulta>', methods=['GET', 'POST'])
def editar_consulta(id_consulta):
    consulta = next((c for c in consultas_ficticias if c["id"] == id_consulta), None)
    opcoes = ["Vacina", "Consulta geral", "Exame"]
    if request.method == 'POST':
        flash('Consulta atualizada (simulado)!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('editarConsulta.html', consulta=consulta, usuario=usuario_ficticio,
                           pets=pets_ficticios, opcoes=opcoes)

@app.route('/desmarcar/<int:id_consulta>')
def desmarcar(id_consulta):
    flash('Consulta desmarcada (simulado)!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/calcular_dose/<int:id_pet>', methods=["GET", "POST"])
def calcular_dose(id_pet):
    pet = next((p for p in pets_ficticios if p["id"] == id_pet), None)
    if request.method == "POST":
        flash('Dose calculada (simulado)!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('calcularDose.html', pet=pet, usuario=usuario_ficticio)

@app.route('/calcular_soro/<int:id_pet>', methods=["GET", "POST"])
def calcular_soro(id_pet):
    pet = next((p for p in pets_ficticios if p["id"] == id_pet), None)
    if request.method == "POST":
        flash('Cálculo de soro realizado (simulado)!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('calcularSoro.html', pet=pet, usuario=usuario_ficticio)

# ---- Inicialização ----
if __name__ == '__main__':
    app.run(debug=True)
