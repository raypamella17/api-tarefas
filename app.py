"""API REST de tarefas — Flask + SQLite.

Endpoints:
    GET    /tarefas            lista (filtro opcional: ?concluida=true|false)
    POST   /tarefas            cria
    GET    /tarefas/<id>       busca uma
    PUT    /tarefas/<id>       atualiza
    DELETE /tarefas/<id>       apaga
"""
import hmac
import os
import sqlite3

from flask import Flask, g, jsonify, request

DATABASE = os.environ.get("DATABASE", "tarefas.db")
# Se API_KEY estiver definida, toda requisição precisa enviar o header X-API-Key.
API_KEY = os.environ.get("API_KEY")

app = Flask(__name__)


@app.before_request
def checar_chave():
    if API_KEY:
        enviada = request.headers.get("X-API-Key", "")
        # compare_digest evita ataques de timing na comparação da chave
        if not hmac.compare_digest(enviada, API_KEY):
            return erro(401, "chave de API inválida ou ausente")


# ---------- Banco de dados ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS tarefas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL DEFAULT '',
                concluida INTEGER NOT NULL DEFAULT 0,
                criada_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def para_dict(row):
    d = dict(row)
    d["concluida"] = bool(d["concluida"])
    return d


# ---------- Validação ----------
def validar(dados, parcial=False):
    """Retorna (dados_limpos, erros)."""
    erros = {}
    limpos = {}

    if not isinstance(dados, dict):
        return None, {"corpo": "envie um JSON válido"}

    if "titulo" in dados or not parcial:
        titulo = dados.get("titulo")
        if not isinstance(titulo, str) or not titulo.strip():
            erros["titulo"] = "obrigatório, texto não vazio"
        elif len(titulo) > 120:
            erros["titulo"] = "máximo de 120 caracteres"
        else:
            limpos["titulo"] = titulo.strip()

    if "descricao" in dados:
        if not isinstance(dados["descricao"], str):
            erros["descricao"] = "deve ser texto"
        else:
            limpos["descricao"] = dados["descricao"]

    if "concluida" in dados:
        if not isinstance(dados["concluida"], bool):
            erros["concluida"] = "deve ser true ou false"
        else:
            limpos["concluida"] = int(dados["concluida"])

    return limpos, erros


def erro(status, mensagem, detalhes=None):
    corpo = {"erro": mensagem}
    if detalhes:
        corpo["detalhes"] = detalhes
    return jsonify(corpo), status


# ---------- Rotas ----------
@app.get("/tarefas")
def listar():
    filtro = request.args.get("concluida")
    db = get_db()
    if filtro is None:
        rows = db.execute("SELECT * FROM tarefas ORDER BY id").fetchall()
    elif filtro.lower() in ("true", "false"):
        valor = int(filtro.lower() == "true")
        rows = db.execute(
            "SELECT * FROM tarefas WHERE concluida = ? ORDER BY id", (valor,)
        ).fetchall()
    else:
        return erro(400, "parâmetro 'concluida' deve ser true ou false")
    return jsonify([para_dict(r) for r in rows])


@app.post("/tarefas")
def criar():
    dados = request.get_json(silent=True)
    limpos, erros = validar(dados)
    if erros:
        return erro(400, "dados inválidos", erros)

    db = get_db()
    cur = db.execute(
        "INSERT INTO tarefas (titulo, descricao, concluida) VALUES (?, ?, ?)",
        (limpos["titulo"], limpos.get("descricao", ""), limpos.get("concluida", 0)),
    )
    db.commit()
    row = db.execute("SELECT * FROM tarefas WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(para_dict(row)), 201


@app.get("/tarefas/<int:tarefa_id>")
def buscar(tarefa_id):
    row = get_db().execute(
        "SELECT * FROM tarefas WHERE id = ?", (tarefa_id,)
    ).fetchone()
    if row is None:
        return erro(404, "tarefa não encontrada")
    return jsonify(para_dict(row))


@app.put("/tarefas/<int:tarefa_id>")
def atualizar(tarefa_id):
    db = get_db()
    if db.execute("SELECT 1 FROM tarefas WHERE id = ?", (tarefa_id,)).fetchone() is None:
        return erro(404, "tarefa não encontrada")

    dados = request.get_json(silent=True)
    limpos, erros = validar(dados, parcial=True)
    if erros:
        return erro(400, "dados inválidos", erros)
    if not limpos:
        return erro(400, "nenhum campo para atualizar")

    # nomes das colunas vêm do código (nunca do cliente); valores vão parametrizados
    campos = ", ".join(f"{col} = ?" for col in limpos)
    db.execute(
        f"UPDATE tarefas SET {campos} WHERE id = ?",
        (*limpos.values(), tarefa_id),
    )
    db.commit()
    row = db.execute("SELECT * FROM tarefas WHERE id = ?", (tarefa_id,)).fetchone()
    return jsonify(para_dict(row))


@app.delete("/tarefas/<int:tarefa_id>")
def apagar(tarefa_id):
    db = get_db()
    cur = db.execute("DELETE FROM tarefas WHERE id = ?", (tarefa_id,))
    db.commit()
    if cur.rowcount == 0:
        return erro(404, "tarefa não encontrada")
    return "", 204


# ---------- Erros globais ----------
@app.errorhandler(404)
def nao_encontrado(_e):
    return erro(404, "rota não encontrada")


@app.errorhandler(405)
def metodo_nao_permitido(_e):
    return erro(405, "método não permitido nesta rota")


@app.errorhandler(500)
def erro_interno(_e):
    return erro(500, "erro interno do servidor")


init_db()

if __name__ == "__main__":
    app.run(debug=True)
