# API de Tarefas

API REST simples feita com **Flask** e **SQLite** (CRUD completo, validação de entrada e tratamento de erros).

## Como rodar

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

A API sobe em `http://127.0.0.1:5000`. O banco (`tarefas.db`) é criado automaticamente.

## Endpoints

| Método | Rota             | Descrição                                        | Sucesso |
|--------|------------------|--------------------------------------------------|---------|
| GET    | `/tarefas`       | Lista tarefas (`?concluida=true` ou `false`)     | 200     |
| POST   | `/tarefas`       | Cria tarefa                                      | 201     |
| GET    | `/tarefas/<id>`  | Busca uma tarefa                                 | 200     |
| PUT    | `/tarefas/<id>`  | Atualiza campos enviados                         | 200     |
| DELETE | `/tarefas/<id>`  | Apaga tarefa                                     | 204     |

Erros retornam JSON no formato `{"erro": "mensagem", "detalhes": {...}}` com status 400, 401, 404, 405 ou 500.

## Exemplos

```bash
# criar
curl -X POST http://127.0.0.1:5000/tarefas \
  -H "Content-Type: application/json" \
  -d '{"titulo": "Estudar backend", "descricao": "Flask + SQLite"}'

# listar
curl http://127.0.0.1:5000/tarefas

# marcar como concluída
curl -X PUT http://127.0.0.1:5000/tarefas/1 \
  -H "Content-Type: application/json" \
  -d '{"concluida": true}'

# apagar
curl -X DELETE http://127.0.0.1:5000/tarefas/1
```

## Testes

```bash
python -m unittest -v
```

13 testes automatizados cobrem o CRUD, a validação de entrada, uma tentativa de SQL injection e a autenticação.

## Autenticação (opcional)

Por padrão a API é aberta. Para exigir uma chave, defina a variável `API_KEY` antes de subir:

```bash
API_KEY=minha-chave python app.py          # Windows (PowerShell): $env:API_KEY="minha-chave"; python app.py
curl -H "X-API-Key: minha-chave" http://127.0.0.1:5000/tarefas
```

Sem a chave (ou com chave errada) a resposta é `401`.

## Decisões técnicas

- Queries SQL sempre parametrizadas (protege contra SQL injection).
- Validação de tipos e tamanho em todos os campos antes de gravar.
- Conexão com o banco por requisição, fechada automaticamente ao final.
- Comparação da chave de API com `hmac.compare_digest`, que evita ataques de timing.
