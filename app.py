import os
import locale
from flask import Flask, render_template, request, redirect, url_for, flash, session
import fdb
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# ---------------------------
# Configuração de idioma
# ---------------------------
try:
    locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_TIME, 'portuguese_brazil')
    except:
        pass

# ---------------------------
# Configuração Flask
# ---------------------------
app = Flask(__name__)
# Em produção, leia de variável de ambiente. Aqui tem fallback para desenvolvimento.
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'minha-chave-secreta-local')

# ---------------------------
# Configuração do banco Firebird
# ---------------------------
DB_CONFIG = {
    'host': 'localhost',
    'database': r'C:\Users\mathe\OneDrive\Documentos\GitHub\Trabalho-final-de-ano-2025\BANCO.FDB',
    'user': 'SYSDBA',
    'password': 'masterkey'
}

def get_conn():
    """Retorna uma conexão nova com o Firebird."""
    return fdb.connect(**DB_CONFIG)

# ---------------------------
# Helpers de sessão / usuário
# ---------------------------
def usuario_logado():
    if 'id_pessoa' in session:
        return obter_usuario_por_id(session['id_pessoa'])
    return None

def login_obrigatorio():
    if 'id_pessoa' not in session:
        flash('Você precisa estar logado para acessar esta página.', 'warning')
        return redirect(url_for('login'))
    return None

# ---------------------------
# Funções SQL - NOTE: agora retornam dicionários quando útil
# ---------------------------
def obter_usuario_por_email(email):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT ID_PESSOA, NOME, EMAIL, TEL, CPF, SENHA FROM USUARIOS WHERE EMAIL = ?", (email,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            'id_pessoa': row[0],
            'nome': row[1],
            'email': row[2],
            'tel': row[3],
            'cpf': row[4],
            'senha': row[5]
        }
    finally:
        conn.close()

def obter_usuario_por_id(id_pessoa):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("SELECT ID_PESSOA, NOME, EMAIL, TEL, CPF, SENHA FROM USUARIOS WHERE ID_PESSOA = ?", (id_pessoa,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            'id_pessoa': row[0],
            'nome': row[1],
            'email': row[2],
            'tel': row[3],
            'cpf': row[4],
            'senha': row[5]
        }
    finally:
        conn.close()

def inserir_usuario(nome, email, tel, cpf, senha_hash):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO USUARIOS (NOME, EMAIL, TEL, CPF, SENHA)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, email, tel, cpf, senha_hash))
        conn.commit()
        # Retornar ID inserido se necessário (Firebird pode precisar de RETURNING; omitido por simplicidade)
    finally:
        conn.close()

def usuario_para_dict(usuario_obj):
    """Recebe dicionário retornado por obter_usuario_por_id/email e padroniza para templates."""
    if not usuario_obj:
        return None
    return {
        'id': usuario_obj.get('id_pessoa'),
        'nome': usuario_obj.get('nome'),
        'email': usuario_obj.get('email'),
        'tel': usuario_obj.get('tel'),
        'cpf': usuario_obj.get('cpf'),
        # NÃO enviar senha para templates
    }

def obter_pet_por_id(id_pet):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT ID_PET, NOME, RACA, PESO, IDADE, DONO_ID
            FROM PETS
            WHERE ID_PET = ?
        """, (id_pet,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            'id': row[0],
            'nome': row[1],
            'raca': row[2],
            'peso': row[3],
            'idade': row[4],
            'dono_id': row[5]
        }
    finally:
        conn.close()

def inserir_pet(nome, raca, peso, idade, dono_id):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO PETS (NOME, RACA, PESO, IDADE, DONO_ID)
            VALUES (?, ?, ?, ?, ?)
        """, (nome, raca, peso, idade, dono_id))
        conn.commit()
    finally:
        conn.close()

def obter_consultas_usuario(id_dono):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT 
                C.ID_CONSULTA,
                C.DONO_ID,
                C.PET_ID,
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
        consultas_dict = []
        for c in consultas:
            consultas_dict.append({
                'id_consulta': c[0],
                'dono_id': c[1],
                'pet_id': c[2],
                'tipo': c[3],
                'descricao': c[4],
                'datahora': c[5],
                'pet_nome': c[6]
            })
        return consultas_dict
    finally:
        conn.close()

def inserir_consulta(dono_id, pet_id, tipo, descricao, datahora):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO CONSULTAS (DONO_ID, PET_ID, TIPO, DESCRICAO, DATAHORA)
            VALUES (?, ?, ?, ?, ?)
        """, (dono_id, pet_id, tipo, descricao, datahora))
        conn.commit()
    finally:
        conn.close()

def inserir_prontuario(pet_id, dono_id, tipo, dose_rec=None, dose_res=None, desid=None, soro_res=None):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO PRONTUARIO (PET_ID, DONO_ID, TIPO, DOSE_RECOMENDADA,
            DOSE_RESULTADO, DESIDRATACAO, SORO_RESULTADO)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pet_id, dono_id, tipo, dose_rec, dose_res, desid, soro_res))
        conn.commit()
    except Exception as e:
        # Log no console para debug local
        print(f"Erro ao inserir prontuário: {e}")
        conn.rollback()
    finally:
        conn.close()

def obter_pets_usuario(id_dono):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT ID_PET, NOME, RACA, PESO, IDADE
            FROM PETS
            WHERE DONO_ID = ?
        """, (id_dono,))
        pets = cur.fetchall()
        pets_dict = []
        for pet in pets:
            pets_dict.append({
                'id': pet[0],
                'nome': pet[1],
                'raca': pet[2],
                'peso': pet[3],
                'idade': pet[4]
            })
        return pets_dict
    finally:
        conn.close()

def obter_ultimo_prontuario(id_pet):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT FIRST 1 * FROM PRONTUARIO
            WHERE PET_ID = ?
            ORDER BY ID_PRONTUARIO DESC
        """, (id_pet,))
        row = cur.fetchone()
        if row:
            # cur.description traz nomes das colunas; limpei espaços e deixei minúsculo
            cols = [col[0].strip().lower() for col in cur.description]
            return dict(zip(cols, row))
        return None
    except Exception as e:
        print(f"Erro ao obter último prontuário: {e}")
        return None
    finally:
        conn.close()

# ---------------------------
# Listas fixas
# ---------------------------
opcoes_atend = ["Banho", "Vacinação", "Consulta", "Exames", "Odonto", "Fisioterapia", "Atendimento domiciliar"]
opcoes_especies = ["Cão", "Gato", "Pássaro", "Peixe", "Tartaruga"]

# ---------------------------
# Rotas
# ---------------------------
@app.route('/')
def index():
    usuario = None
    if 'id_pessoa' in session:
        usuario_tuple = obter_usuario_por_id(session['id_pessoa'])
        usuario = usuario_para_dict(usuario_tuple)
    return render_template('index.html', usuario=usuario)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    try:
        email = request.form.get('email', '').strip()
        senha = request.form.get('senha', '')

        user = obter_usuario_por_email(email)
        if not user:
            flash('E-mail ou senha incorretos', 'warning')
            return redirect(url_for('login'))

        hashed = user.get('senha')
        if not hashed or not check_password_hash(hashed, senha):
            flash('E-mail ou senha incorretos', 'warning')
            return redirect(url_for('login'))

        # Autenticação ok
        session['id_pessoa'] = user['id_pessoa']
        session['nome'] = user['nome']
        session['email'] = user['email']

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
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        tel = request.form.get('tel', '').strip()
        cpf = request.form.get('cpf', '').strip()
        senha = request.form.get('senha', '')
        confirmar = request.form.get('confirmarSenha', '')

        if senha != confirmar:
            flash('As senhas não coincidem', 'warning')
            return redirect(url_for('cadastrar'))

        if obter_usuario_por_email(email):
            flash('E-mail já cadastrado', 'warning')
            return redirect(url_for('cadastrar'))

        senha_hash = generate_password_hash(senha)
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
        usuario_tuple = obter_usuario_por_id(session['id_pessoa'])
        usuario_dict = usuario_para_dict(usuario_tuple)
        pets = obter_pets_usuario(session['id_pessoa'])
        consultas = obter_consultas_usuario(session['id_pessoa'])
        return render_template('dashboard.html', usuario=usuario_dict, pets=pets, consultas=consultas)
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
        nome = request.form.get('nome', '').strip()
        raca = request.form.get('raca', '').strip()
        idade = int(request.form.get('idade', 0))
        peso = float(request.form.get('peso', 0))

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
        flash('Faça login para agendar um serviço.', 'warning')
        return redirect(url_for('login'))

    usuario = obter_usuario_por_id(session['id_pessoa'])
    pets = obter_pets_usuario(session['id_pessoa'])  # retorna lista de dicts
    opcoes = ['Consulta', 'Banho', 'Tosa', 'Vacinação']

    if request.method == 'POST':
        id_pet = request.form['pet_agendar']
        tipo = request.form['tipo']
        datahora = request.form['datahora']
        descricao = request.form['desc']

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO AGENDAMENTOS (ID_PET, TIPO, DATAHORA, DESCRICAO)
            VALUES (?, ?, ?, ?)
        """, (id_pet, tipo, datahora, descricao))
        conn.commit()
        conn.close()

        flash('Agendamento criado com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('agendar.html', usuario=usuario, pets=pets, opcoes=opcoes)

@app.route('/editar_pet/<int:id_pet>', methods=['GET', 'POST'])
def editar_pet(id_pet):
    if 'id_pessoa' not in session:
        flash('Você precisa estar logado para editar um pet.', 'warning')
        return redirect(url_for('login'))

    pet = obter_pet_por_id(id_pet)
    if not pet or pet['dono_id'] != session['id_pessoa']:
        flash('Pet não encontrado ou você não tem permissão para editá-lo.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            nome = request.form.get('nome', '').strip()
            raca = request.form.get('raca', '').strip()
            idade = int(request.form.get('idade', 0))
            peso = float(request.form.get('peso', 0))

            if idade <= 0 or peso <= 0:
                flash('Idade e peso devem ser maiores que zero.', 'warning')
                return redirect(url_for('editar_pet', id_pet=id_pet))

            conn = get_conn()
            cur = conn.cursor()
            try:
                cur.execute("""
                    UPDATE PETS
                    SET NOME = ?, RACA = ?, IDADE = ?, PESO = ?
                    WHERE ID_PET = ? AND DONO_ID = ?
                """, (nome, raca, idade, peso, id_pet, session['id_pessoa']))
                conn.commit()
            finally:
                conn.close()

            flash('Pet atualizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            flash(f'Erro ao atualizar pet: {e}', 'error')
            return redirect(url_for('editar_pet', id_pet=id_pet))

    return render_template('editarPet.html', pet=pet, especies=opcoes_especies)

@app.route('/remover_pet/<int:id_pet>')
def remover_pet(id_pet):
    if 'id_pessoa' not in session:
        return redirect(url_for('login'))

    try:
        pet = obter_pet_por_id(id_pet)
        if not pet or pet['dono_id'] != session['id_pessoa']:
            flash('Pet não encontrado ou você não tem permissão para removê-lo.', 'error')
            return redirect(url_for('dashboard'))

        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM PETS WHERE ID_PET = ?", (id_pet,))
            conn.commit()
        finally:
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
    try:
        cur.execute("SELECT ID_CONSULTA, DONO_ID, PET_ID, TIPO, DESCRICAO, DATAHORA FROM CONSULTAS WHERE ID_CONSULTA = ?", (id_consulta,))
        consulta_row = cur.fetchone()
    finally:
        conn.close()

    if not consulta_row:
        flash('Consulta não encontrada.', 'error')
        return redirect(url_for('dashboard'))

    consulta = {
        'id_consulta': consulta_row[0],
        'dono_id': consulta_row[1],
        'pet_id': consulta_row[2],
        'tipo': consulta_row[3],
        'descricao': consulta_row[4],
        'datahora': consulta_row[5]
    }

    if consulta['dono_id'] != session['id_pessoa']:
        flash('Você não tem permissão para editar esta consulta.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        pets = obter_pets_usuario(session['id_pessoa'])
        return render_template('editarConsulta.html', consulta=consulta, pets=pets, opcoes=opcoes_atend)

    try:
        tipo = request.form.get('tipo', '').strip()
        desc = request.form.get('desc', '').strip()
        pet_id = int(request.form.get('pet_agendar'))
        datahora = datetime.strptime(request.form.get('datahora'), '%Y-%m-%dT%H:%M')

        if datahora < datetime.now():
            flash('A data/hora não pode ser no passado.', 'warning')
            return redirect(url_for('editar_consulta', id_consulta=id_consulta))

        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE CONSULTAS SET TIPO=?, DESCRICAO=?, PET_ID=?, DATAHORA=?
                WHERE ID_CONSULTA=?
            """, (tipo, desc, pet_id, datahora, id_consulta))
            conn.commit()
        finally:
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
        try:
            cur.execute("SELECT DONO_ID FROM CONSULTAS WHERE ID_CONSULTA = ?", (id_consulta,))
            consulta = cur.fetchone()
            if not consulta or consulta[0] != session['id_pessoa']:
                flash('Consulta não encontrada ou você não tem permissão para desmarcá-la.', 'error')
                return redirect(url_for('dashboard'))

            cur.execute("DELETE FROM CONSULTAS WHERE ID_CONSULTA = ?", (id_consulta,))
            conn.commit()
        finally:
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
    if not pet or pet['dono_id'] != session['id_pessoa']:
        flash('Pet não encontrado.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == "GET":
        return render_template('calcularDose.html', pet=pet)

    try:
        # Permitir que o usuário entre com dose por kg (ex: 2.5 mg/kg)
        dose_recomendada = float(request.form.get('dose', 0))
        if dose_recomendada <= 0:
            flash('Dose deve ser maior que zero.', 'warning')
            return redirect(url_for('calcular_dose', id_pet=id_pet))

        peso = float(pet['peso'])
        dose_resultado = peso * dose_recomendada

        inserir_prontuario(id_pet, session['id_pessoa'], 'Dose Medicamento',
                          dose_rec=dose_recomendada, dose_res=dose_resultado)

        flash(f"Dose calculada: {dose_resultado:.2f} mg", 'success')
    except Exception as e:
        flash(f'Erro ao calcular dose: {e}', 'error')

    return redirect(url_for('dashboard'))

@app.route('/calcular_soro/<int:id_pet>', methods=["GET", "POST"])
def calcular_soro(id_pet):
    if 'id_pessoa' not in session:
        return redirect(url_for('login'))

    pet = obter_pet_por_id(id_pet)
    if not pet or pet['dono_id'] != session['id_pessoa']:
        flash('Pet não encontrado.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == "GET":
        return render_template('calcularSoro.html', pet=pet)

    try:
        # Aceitar desidratação como porcentagem (ex: 5 para 5%) ou fração (0.05)
        desidratacao_raw = float(request.form.get('desid', 0))
        if desidratacao_raw <= 0:
            flash('Percentual de desidratação deve ser maior que zero.', 'warning')
            return redirect(url_for('calcular_soro', id_pet=id_pet))

        # Normalizar: se usuário deu 5 => entendemos 5% => 0.05
        if desidratacao_raw > 1:
            desidratacao = desidratacao_raw / 100.0
        else:
            desidratacao = desidratacao_raw

        base_fluido = 50  # mL/kg
        peso = float(pet['peso'])
        soro_resultado = desidratacao * base_fluido * peso

        inserir_prontuario(id_pet, session['id_pessoa'], 'Soro',
                          desid=desidratacao, soro_res=soro_resultado)

        flash(f"Volume de soro calculado: {soro_resultado:.2f} mL", 'success')
    except Exception as e:
        flash(f"Erro ao calcular soro: {e}", 'error')

    return redirect(url_for('dashboard'))

@app.route('/editar_usuario', methods=['GET', 'POST'])
def editar_usuario():
    if 'id_pessoa' not in session:
        return redirect(url_for('login'))

    usuario_obj = obter_usuario_por_id(session['id_pessoa'])
    usuario_dict = usuario_para_dict(usuario_obj)

    if request.method == 'GET':
        # NÃO enviar senha para o template. Template deve deixar o campo senha vazio.
        return render_template('editarUser.html', usuario=usuario_dict)

    try:
        nome = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip()
        tel = request.form.get('tel', '').strip()
        cpf = request.form.get('cpf', '').strip()
        senha = request.form.get('senha', '').strip()

        conn = get_conn()
        cur = conn.cursor()
        try:
            if senha:
                # Se usuário informou nova senha -> hash e atualiza senha
                senha_hash = generate_password_hash(senha)
                cur.execute("""
                    UPDATE USUARIOS 
                    SET NOME = ?, EMAIL = ?, TEL = ?, CPF = ?, SENHA = ?
                    WHERE ID_PESSOA = ?
                """, (nome, email, tel, cpf, senha_hash, session['id_pessoa']))
            else:
                # Senha não informada -> NÃO modifica a senha armazenada
                cur.execute("""
                    UPDATE USUARIOS 
                    SET NOME = ?, EMAIL = ?, TEL = ?, CPF = ?
                    WHERE ID_PESSOA = ?
                """, (nome, email, tel, cpf, session['id_pessoa']))
            conn.commit()
        finally:
            conn.close()

        # Atualiza sessão com novos dados
        session['nome'] = nome
        session['email'] = email

        flash('Dados atualizados com sucesso!', 'success')
        return redirect(url_for('dashboard'))
    except Exception as e:
        flash(f'Erro ao atualizar dados: {e}', 'error')
        return redirect(url_for('editar_usuario'))

# ---------------------------
# Inicialização
# ---------------------------
if __name__ == '__main__':
    # Em produção retire debug=True e configure host & port conforme necessário
    app.run(debug=True)
