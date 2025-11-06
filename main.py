import locale
from flask import Flask, render_template, request, redirect, url_for, flash, session
import fdb
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Configuração de idioma
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    locale.setlocale(locale.LC_TIME, 'portuguese_brazil')

# Configuração Flask
app = Flask(__name__)
app.secret_key = 'minha-chave-secreta'

# Configuração do banco Firebird
DB_CONFIG = {
    'host': 'localhost',
    'database': r'C:\Users\Aluno\Desktop\Trabalho-final-de-ano-2025\BANCO.FDB',
    'user': 'SYSDBA',
    'password': 'sysdba'
}

def get_conn():
    return fdb.connect(**DB_CONFIG)

# Funções utilitárias SQL

def obter_usuario_por_email(email):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM USUARIOS WHERE EMAIL = ?", (email,))
    row = cur.fetchone()
    conn.close()
    return row

def obter_usuario_por_id(id_pessoa):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM USUARIOS WHERE ID_PESSOA = ?", (id_pessoa,))
    row = cur.fetchone()
    conn.close()
    return row

def inserir_usuario(nome, email, tel, cpf, senha):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO USUARIOS (NOME, EMAIL, TEL, CPF, SENHA) VALUES (?, ?, ?, ?, ?)", (nome, email, tel, cpf, senha))
    conn.commit()
    conn.close()

def obter_pets_usuario(id_pessoa):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM PETS WHERE DONO_ID = ?", (id_pessoa,))
    rows = cur.fetchall()
    conn.close()
    return rows

def inserir_pet(nome, raca, peso, idade, dono_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO PETS (NOME, RACA, PESO, IDADE, DONO_ID) VALUES (?, ?, ?, ?, ?)", (nome, raca, peso, idade, dono_id))
    conn.commit()
    conn.close()

def obter_consultas_usuario(id_pessoa):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM CONSULTAS WHERE DONO_ID = ?", (id_pessoa,))
    rows = cur.fetchall()
    conn.close()
    return rows

def inserir_consulta(dono_id, pet_id, tipo, descricao, datahora):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO CONSULTAS (DONO_ID, PET_ID, TIPO, DESCRICAO, DATAHORA) VALUES (?, ?, ?, ?, ?)", (dono_id, pet_id, tipo, descricao, datahora))
    conn.commit()
    conn.close()

def inserir_prontuario(pet_id, dono_id, tipo, dose_rec=None, dose_res=None, desid=None, soro_res=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO PRONTUARIO (PET_ID, DONO_ID, TIPO, DOSE_RECOMENDADA, DOSE_RESULTADO, DESIDRATACAO, SORO_RESULTADO)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (pet_id, dono_id, tipo, dose_rec, dose_res, desid, soro_res))
    conn.commit()
    conn.close()

def obter_pet_por_id(id_pet):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM PETS WHERE ID_PET = ?", (id_pet,))
    pet = cur.fetchone()
    conn.close()
    return pet

def obter_ultimo_prontuario(id_pet):
    """
    Retorna o último prontuário do pet como dict com chaves normalizadas (minúsculas).
    Se não existir, retorna None.
    """
    conn = get_conn()
    cur = conn.cursor()
    # Ajuste o ORDER BY para o nome correto da PK na sua tabela; aqui usei ID_PRONTUARIO como exemplo.
    cur.execute("""
        SELECT FIRST 1 *
        FROM PRONTUARIO
        WHERE PET_ID = ?
        ORDER BY ID_PRONTUARIO DESC
    """, (id_pet,))
    row = cur.fetchone()
    # fechar conexão
    conn.close()

    if not row:
        return None

    # normaliza nomes das colunas vindas do cursor.description
    cols = []
    for col in cur.description:
        name = col[0]
        # normaliza: tira espaços, deixa lowercase
        name = name.strip().lower()
        cols.append(name)

    # monta dict, cuidando se o número de colunas bate com o row
    dados = dict(zip(cols, row))
    return dados



# Listas fixas
opcoes_atend = ["Banho", "Vacinação", "Consulta", "Exames", "Odonto", "Fisioterapia", "Atendimento domiciliar"]
opcoes_especies = ["Cão", "Gato", "Pássaro", "Peixe", "Tartaruga"]

usuario_atual = None

# Rotas principais
@app.route('/')
def index():
    return render_template('index.html', usuario=usuario_atual)

@app.route('/login', methods=['GET', 'POST'])
def login():
    global usuario_atual
    if request.method == 'GET':
        return render_template('login.html')

    try:
        email = request.form['email']
        senha = request.form['senha']

        user = obter_usuario_por_email(email)
        if not user or not check_password_hash(user[5], senha):
            flash('E-mail ou senha incorretos', 'warning')
            return redirect(url_for('login'))

        usuario_atual = {
            'id': user[0], 'nome': user[1], 'email': user[2], 'tel': user[3], 'cpf': user[4]
        }
        flash('Login realizado com sucesso', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Erro ao realizar login: {e}', 'error')
        return redirect(url_for('login'))

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'GET':
        return render_template('cadastrar.html')

    try:
        nome = request.form['nome']
        email = request.form['email']
        tel = request.form['tel']
        cpf = request.form['cpf']
        senha = request.form['senha']
        confirmar = request.form['confirmarSenha']

        if senha != confirmar:
            flash('As senhas não coincidem', 'warning')
            return redirect(url_for('cadastrar'))

        senha_hash = generate_password_hash(senha)

        if obter_usuario_por_email(email):
            flash('E-mail já cadastrado', 'warning')
            return redirect(url_for('cadastrar'))

        inserir_usuario(nome, email, tel, cpf, senha_hash)
        flash('Usuário cadastrado com sucesso', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Erro ao cadastrar: {e}', 'error')
        return redirect(url_for('cadastrar'))

@app.route('/logout')
def logout():
    global usuario_atual
    usuario_atual = None
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if not usuario_atual:
        return redirect(url_for('login'))

    try:
        pets = obter_pets_usuario(usuario_atual['id'])
        consultas = obter_consultas_usuario(usuario_atual['id'])
        return render_template('dashboard.html', usuario=usuario_atual, pets=pets, consultas=consultas)
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {e}', 'error')
        return redirect(url_for('index'))

@app.route('/cadastrar_pet', methods=['GET', 'POST'])
def cadastrar_pet():
    if not usuario_atual:
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('cadastrarPet.html', usuario=usuario_atual, especies=opcoes_especies)

    try:
        nome = request.form['nome']
        raca = request.form['raca']
        idade = int(request.form['idade'])
        peso = float(request.form['peso'])

        if idade <= 0 or peso <= 0:
            flash('Idade e peso devem ser maiores que zero', 'warning')
            return redirect(url_for('cadastrar_pet'))

        inserir_pet(nome, raca, peso, idade, usuario_atual['id'])
        flash('Pet cadastrado com sucesso', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Erro ao cadastrar pet: {e}', 'error')
        return redirect(url_for('cadastrar_pet'))

@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if not usuario_atual:
        return redirect(url_for('login'))

    if request.method == 'GET':
        pets = obter_pets_usuario(usuario_atual['id'])
        return render_template('agendar.html', usuario=usuario_atual, pets=pets, opcoes=opcoes_atend)

    try:
        tipo = request.form['tipo']
        desc = request.form['desc']
        pet_id = int(request.form['pet_agendar'])
        datahora = datetime.strptime(request.form['datahora'], '%Y-%m-%dT%H:%M')

        if datahora < datetime.now():
            flash('A data/hora não pode ser no passado', 'warning')
            return redirect(url_for('agendar'))

        inserir_consulta(usuario_atual['id'], pet_id, tipo, desc, datahora)
        flash('Consulta agendada com sucesso', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Erro ao agendar: {e}', 'error')
        return redirect(url_for('agendar'))

@app.route('/editar_pet/<int:id_pet>', methods=['GET', 'POST'])
def editar_pet(id_pet):
    if not usuario_atual:
        return redirect(url_for('login'))

    pet = obter_pet_por_id(id_pet)
    if not pet:
        flash('Pet não encontrado', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        return render_template('editarPet.html', pet=pet)

    try:
        nome = request.form['nome']
        raca = request.form['raca']
        idade = int(request.form['idade'])
        peso = float(request.form['peso'])

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE PETS SET NOME=?, RACA=?, IDADE=?, PESO=? WHERE ID_PET=?
        """, (nome, raca, idade, peso, id_pet))
        conn.commit()
        conn.close()

        flash('Informações do pet atualizadas!', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar pet: {e}', 'error')

    return redirect(url_for('dashboard'))


@app.route('/remover_pet/<int:id_pet>')
def remover_pet(id_pet):
    if not usuario_atual:
        return redirect(url_for('login'))

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM PETS WHERE ID_PET = ?", (id_pet,))
        conn.commit()
        conn.close()
        flash('Pet removido com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao remover pet: {e}', 'error')

    return redirect(url_for('dashboard'))


@app.route('/editar_consulta/<int:id_consulta>', methods=['GET', 'POST'])
def editar_consulta(id_consulta):
    if not usuario_atual:
        return redirect(url_for('login'))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM CONSULTAS WHERE ID_CONSULTA = ?", (id_consulta,))
    consulta = cur.fetchone()
    conn.close()

    if not consulta:
        flash('Consulta não encontrada', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        pets = obter_pets_usuario(usuario_atual['id'])
        return render_template('editarConsulta.html', consulta=consulta, pets=pets, opcoes=opcoes_atend)

    try:
        tipo = request.form['tipo']
        desc = request.form['desc']
        pet_id = int(request.form['pet_agendar'])
        datahora = datetime.strptime(request.form['datahora'], '%Y-%m-%dT%H:%M')

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE CONSULTAS SET TIPO=?, DESCRICAO=?, PET_ID=?, DATAHORA=?
            WHERE ID_CONSULTA=?
        """, (tipo, desc, pet_id, datahora, id_consulta))
        conn.commit()
        conn.close()

        flash('Consulta atualizada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao editar consulta: {e}', 'error')

    return redirect(url_for('dashboard'))


@app.route('/desmarcar/<int:id_consulta>')
def desmarcar(id_consulta):
    if not usuario_atual:
        return redirect(url_for('login'))

    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM CONSULTAS WHERE ID_CONSULTA = ?", (id_consulta,))
        conn.commit()
        conn.close()
        flash('Consulta desmarcada com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao desmarcar consulta: {e}', 'error')

    return redirect(url_for('dashboard'))

@app.route('/calcular_dose/<int:id_pet>', methods=["GET", "POST"])
def calcular_dose(id_pet):
    if not usuario_atual:
        return redirect(url_for('login'))

    pet = obter_pet_por_id(id_pet)
    if not pet:
        flash('Pet não encontrado', 'error')
        return redirect(url_for('dashboard'))

    if request.method == "GET":
        return render_template('calcularDose.html', pet=pet)

    try:
        dose_recomendada = float(request.form['dose'])
        if dose_recomendada <= 0:
            flash('Dose deve ser maior que zero', 'warning')
            return redirect(f'/calcular_dose/{id_pet}')

        peso = float(pet[3])
        dose_resultado = peso * dose_recomendada

        # 🔍 Busca o último prontuário do pet
        ultimo_prontuario = obter_ultimo_prontuario(id_pet)

        # Copia valores anteriores se existirem
        soro_res = ultimo_prontuario['soro_res'] if ultimo_prontuario else None
        desid = ultimo_prontuario['desid'] if ultimo_prontuario else None

        # Cria novo prontuário completo
        inserir_prontuario(
            pet_id=id_pet,
            dono_id=usuario_atual['id'],
            tipo='Dose Medicamento',
            dose_rec=dose_recomendada,
            dose_res=dose_resultado,
            desid=desid,
            soro_res=soro_res
        )

        flash(f"Dose calculada: {dose_resultado:.2f} mg", 'success')
    except Exception as e:
        flash(f'Erro ao calcular dose: {e}', 'error')

    return redirect(url_for('dashboard'))



@app.route('/calcular_soro/<int:id_pet>', methods=["GET", "POST"])
def calcular_soro(id_pet):
    if not usuario_atual:
        return redirect(url_for('login'))

    pet = obter_pet_por_id(id_pet)
    if not pet:
        flash('Pet não encontrado', 'error')
        return redirect(url_for('dashboard'))

    if request.method == "GET":
        return render_template('calcularSoro.html', pet=pet)

    try:
        desidratacao = float(request.form['desid'])
        if desidratacao <= 0:
            flash('Percentual de desidratação deve ser maior que zero', 'warning')
            return redirect(f'/calcular_soro/{id_pet}')

        base_fluido = 50  # mL/kg
        peso = float(pet[3])
        soro_resultado = desidratacao * base_fluido * peso

        # 🔍 Busca o último prontuário do pet
        ultimo_prontuario = obter_ultimo_prontuario(id_pet)

        # Copia valores anteriores se existirem
        dose_rec = ultimo_prontuario['dose_rec'] if ultimo_prontuario else None
        dose_res = ultimo_prontuario['dose_res'] if ultimo_prontuario else None

        # Cria novo prontuário completo
        inserir_prontuario(
            pet_id=id_pet,
            dono_id=usuario_atual['id'],
            tipo='Soro',
            desid=desidratacao,
            soro_res=soro_resultado,
            dose_rec=dose_rec,
            dose_res=dose_res
        )

        flash(f"Volume de soro calculado: {soro_resultado:.2f} mL", 'success')
    except Exception as e:
        flash(f"Erro ao calcular soro: {e}", 'error')

    return redirect(url_for('dashboard'))




if __name__ == '__main__':
    app.run(debug=True)
