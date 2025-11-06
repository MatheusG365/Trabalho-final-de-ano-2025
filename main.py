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
app.secret_key = 'minha-chave-secreta'  # 🔒 troque por algo forte em produção

# Configuração do banco Firebird
DB_CONFIG = {
    'host': 'localhost',
    'database': r'C:\Users\Aluno\Desktop\Trabalho-final-de-ano-2025\BANCO.FDB',
    'user': 'SYSDBA',
    'password': 'sysdba'
}

def get_conn():
    return fdb.connect(**DB_CONFIG)


# ============================================================
# 🔹 Funções auxiliares
# ============================================================

def usuario_logado():
    """Retorna o usuário logado (tupla) ou None."""
    if 'id_pessoa' in session:
        return obter_usuario_por_id(session['id_pessoa'])
    return None


def login_obrigatorio():
    """Verifica login e redireciona se não estiver logado."""
    if 'id_pessoa' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('login'))
    return None


# ============================================================
# 🔹 Funções SQL
# ============================================================

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
    cur.execute("""
        INSERT INTO USUARIOS (NOME, EMAIL, TEL, CPF, SENHA)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, email, tel, cpf, senha))
    conn.commit()
    conn.close()

def obter_pet_por_id(id_pet):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT ID_PET, NOME, RACA, PESO, IDADE, DONO_ID
        FROM PETS
        WHERE ID_PET = ?
    """, (id_pet,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return None

    # Retorna como dicionário (mais seguro para o template)
    return {
        'id': row[0],
        'nome': row[1],
        'raca': row[2],
        'peso': row[3],
        'idade': row[4],
        'dono_id': row[5]
    }

def inserir_pet(nome, raca, peso, idade, dono_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO PETS (NOME, RACA, PESO, IDADE, DONO_ID)
        VALUES (?, ?, ?, ?, ?)
    """, (nome, raca, peso, idade, dono_id))
    conn.commit()
    conn.close()

def obter_consultas_usuario(id_dono):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            C.ID_CONSULTA,
            C.TIPO,
            C.DESCRICAO,
            C.DATAHORA,
            P.NOME AS PET_NOME
        FROM CONSULTAS C
        JOIN PETS P ON P.ID_PET = C.PET_ID
        WHERE C.DONO_ID = ?
        ORDER BY C.DATAHORA DESC
    """, (id_dono,))
    consultas = cur.fetchall()
    conn.close()
    return consultas

def inserir_consulta(dono_id, pet_id, tipo, descricao, datahora):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO CONSULTAS (DONO_ID, PET_ID, TIPO, DESCRICAO, DATAHORA)
        VALUES (?, ?, ?, ?, ?)
    """, (dono_id, pet_id, tipo, descricao, datahora))
    conn.commit()
    conn.close()

def inserir_prontuario(pet_id, dono_id, tipo, dose_rec=None, dose_res=None, desid=None, soro_res=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO PRONTUARIO (PET_ID, DONO_ID, TIPO, DOSE_RECOMENDADA,
        DOSE_RESULTADO, DESIDRATACAO, SORO_RESULTADO)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (pet_id, dono_id, tipo, dose_rec, dose_res, desid, soro_res))
    conn.commit()
    conn.close()

def obter_pets_usuario(id_dono):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT ID_PET, NOME, RACA, PESO, IDADE
        FROM PETS
        WHERE DONO_ID = ?
    """, (id_dono,))
    pets = cur.fetchall()
    conn.close()
    return pets



def obter_ultimo_prontuario(id_pet):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT FIRST 1 * FROM PRONTUARIO
        WHERE PET_ID = ?
        ORDER BY ID_PRONTUARIO DESC
    """, (id_pet,))
    row = cur.fetchone()
    cols = [col[0].strip().lower() for col in cur.description]
    conn.close()
    return dict(zip(cols, row)) if row else None


# ============================================================
# 🔹 Listas fixas
# ============================================================

opcoes_atend = ["Banho", "Vacinação", "Consulta", "Exames", "Odonto", "Fisioterapia", "Atendimento domiciliar"]
opcoes_especies = ["Cão", "Gato", "Pássaro", "Peixe", "Tartaruga"]


# ============================================================
# 🔹 Rotas
# ============================================================

@app.route('/')
def index():
    usuario = usuario_logado()
    return render_template('index.html', usuario=usuario)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    try:
        email = request.form['email']
        senha = request.form['senha']

        user = obter_usuario_por_email(email)
        if not user or not check_password_hash(user[5], senha):
            flash('E-mail ou senha incorretos', 'warning')
            return redirect(url_for('login'))

        session['id_pessoa'] = user[0]
        session['nome'] = user[1]
        session['email'] = user[2]

        flash('Login realizado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Erro ao realizar login: {e}', 'error')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))


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
        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('login'))
    except Exception as e:
        flash(f'Erro ao cadastrar: {e}', 'error')
        return redirect(url_for('cadastrar'))


@app.route('/dashboard')
def dashboard():
    if 'id_pessoa' not in session:
        return redirect(url_for('login'))

    try:
        usuario = obter_usuario_por_id(session['id_pessoa'])
        pets = obter_pets_usuario(session['id_pessoa'])
        consultas = obter_consultas_usuario(session['id_pessoa'])
        return render_template('dashboard.html', usuario=usuario, pets=pets, consultas=consultas)
    except Exception as e:
        flash(f'Erro ao carregar dashboard: {e}', 'error')
        return redirect(url_for('index'))



@app.route('/cadastrar_pet', methods=['GET', 'POST'])
def cadastrar_pet():
    if 'id_pessoa' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        return render_template('cadastrarPet.html', especies=opcoes_especies)

    try:
        nome = request.form['nome']
        raca = request.form['raca']
        idade = int(request.form['idade'])
        peso = float(request.form['peso'])

        if idade <= 0 or peso <= 0:
            flash('Idade e peso devem ser maiores que zero.', 'warning')
            return redirect(url_for('cadastrar_pet'))

        inserir_pet(nome, raca, peso, idade, session['id_pessoa'])
        flash('Pet cadastrado com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Erro ao cadastrar pet: {e}', 'error')
        return redirect(url_for('cadastrar_pet'))


@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if 'id_pessoa' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        pets = obter_pets_usuario(session['id_pessoa'])
        return render_template('agendar.html', pets=pets, opcoes=opcoes_atend)

    try:
        tipo = request.form['tipo']
        desc = request.form['desc']
        pet_id = int(request.form['pet_agendar'])
        datahora = datetime.strptime(request.form['datahora'], '%Y-%m-%dT%H:%M')

        if datahora < datetime.now():
            flash('A data/hora não pode ser no passado.', 'warning')
            return redirect(url_for('agendar'))

        inserir_consulta(session['id_pessoa'], pet_id, tipo, desc, datahora)
        flash('Consulta agendada com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Erro ao agendar: {e}', 'error')
        return redirect(url_for('agendar'))


@app.route('/editar_pet/<int:id_pet>', methods=['GET', 'POST'])
def editar_pet(id_pet):
    # 🔹 Verifica login
    if 'id_pessoa' not in session:
        flash('Você precisa estar logado para editar um pet.', 'warning')
        return redirect(url_for('login'))

    pet = obter_pet_por_id(id_pet)

    # 🔹 Garante que o pet pertence ao usuário logado
    if not pet or pet[5] != session['id_pessoa']:  # supondo que DONO_ID seja a 6ª coluna (índice 5)
        flash('Pet não encontrado ou você não tem permissão para editá-lo.', 'error')
        return redirect(url_for('dashboard'))

    # 🔹 Converte o pet (tupla) para dicionário, para o template funcionar
    pet_dict = {
        'id': pet[0],
        'nome': pet[1],
        'raca': pet[2],
        'peso': pet[3],
        'idade': pet[4],
        'dono_id': pet[5]
    }

    if request.method == 'POST':
        try:
            nome = request.form['nome']
            raca = request.form['raca']
            idade = request.form['idade']
            peso = request.form['peso']

            conn = get_conn()
            cur = conn.cursor()
            cur.execute("""
                UPDATE PETS
                SET NOME = ?, RACA = ?, IDADE = ?, PESO = ?
                WHERE ID_PET = ? AND DONO_ID = ?
            """, (nome, raca, idade, peso, id_pet, session['id_pessoa']))
            conn.commit()
            conn.close()

            flash('Pet atualizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Erro ao atualizar pet: {e}', 'error')
            return redirect(url_for('editar_pet', id_pet=id_pet))

    # 🔹 Retorna o template com os dados do pet e a lista de espécies
    return render_template('editar_pet.html', pet=pet_dict, especies=opcoes_especies)



@app.route('/remover_pet/<int:id_pet>')
def remover_pet(id_pet):
    if 'id_pessoa' not in session:
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
    if 'id_pessoa' not in session:
        return redirect(url_for('login'))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM CONSULTAS WHERE ID_CONSULTA = ?", (id_consulta,))
    consulta = cur.fetchone()
    conn.close()

    if not consulta:
        flash('Consulta não encontrada.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        pets = obter_pets_usuario(session['id_pessoa'])
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
    if 'id_pessoa' not in session:
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
    if 'id_pessoa' not in session:
        return redirect(url_for('login'))

    pet = obter_pet_por_id(id_pet)
    if not pet:
        flash('Pet não encontrado.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == "GET":
        return render_template('calcularDose.html', pet=pet)

    try:
        dose_recomendada = float(request.form['dose'])
        if dose_recomendada <= 0:
            flash('Dose deve ser maior que zero.', 'warning')
            return redirect(f'/calcular_dose/{id_pet}')

        peso = float(pet[3])
        dose_resultado = peso * dose_recomendada

        ultimo_prontuario = obter_ultimo_prontuario(id_pet)
        soro_res = ultimo_prontuario['soro_resultado'] if ultimo_prontuario else None
        desid = ultimo_prontuario['desidratacao'] if ultimo_prontuario else None

        inserir_prontuario(id_pet, session['id_pessoa'], 'Dose Medicamento',
                           dose_rec=dose_recomendada, dose_res=dose_resultado,
                           desid=desid, soro_res=soro_res)

        flash(f"Dose calculada: {dose_resultado:.2f} mg", 'success')
    except Exception as e:
        flash(f'Erro ao calcular dose: {e}', 'error')

    return redirect(url_for('dashboard'))


@app.route('/calcular_soro/<int:id_pet>', methods=["GET", "POST"])
def calcular_soro(id_pet):
    if 'id_pessoa' not in session:
        return redirect(url_for('login'))

    pet = obter_pet_por_id(id_pet)
    if not pet:
        flash('Pet não encontrado.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == "GET":
        return render_template('calcularSoro.html', pet=pet)

    try:
        desidratacao = float(request.form['desid'])
        if desidratacao <= 0:
            flash('Percentual de desidratação deve ser maior que zero.', 'warning')
            return redirect(f'/calcular_soro/{id_pet}')

        base_fluido = 50  # mL/kg
        peso = float(pet[3])
        soro_resultado = desidratacao * base_fluido * peso

        ultimo_prontuario = obter_ultimo_prontuario(id_pet)
        dose_rec = ultimo_prontuario['dose_recomendada'] if ultimo_prontuario else None
        dose_res = ultimo_prontuario['dose_resultado'] if ultimo_prontuario else None

        inserir_prontuario(id_pet, session['id_pessoa'], 'Soro',
                           desid=desidratacao, soro_res=soro_resultado,
                           dose_rec=dose_rec, dose_res=dose_res)

        flash(f"Volume de soro calculado: {soro_resultado:.2f} mL", 'success')
    except Exception as e:
        flash(f"Erro ao calcular soro: {e}", 'error')

    return redirect(url_for('dashboard'))


# ============================================================
# 🔹 Inicialização
# ============================================================

if __name__ == '__main__':
    app.run(debug=True)
