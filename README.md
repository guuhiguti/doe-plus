# Doe+

**Responsável:** Gustavo Higuti (pessoa física)

Plataforma web para OSCs (Organizações da Sociedade Civil) gerenciarem doações: conecta **colaboradores** que oferecem itens ou tempo voluntário com **pedidos de ajuda**, sugerindo e confirmando "matches" entre oferta e demanda.

## Funcionalidades

- **Cadastro e login** da equipe da OSC, com catálogo de itens padrão criado automaticamente.
- **Formulários públicos** (sem necessidade de login) para colaboradores se cadastrarem e oferecerem itens/tempo, e para solicitantes registrarem pedidos de ajuda. Cada OSC tem links únicos e regeneráveis.
- **Cruzamento (matching)** entre pedidos pendentes e ofertas disponíveis do mesmo item, com confirmação manual ou modo automático.
- **Dashboard** com estatísticas por período (hoje, mês, 90 dias, personalizado): total de pedidos, taxa de atendimento, ranking de itens mais pedidos, série temporal.
- **Catálogo de itens** organizado por categoria (Alimento, Roupa, Higiene, Financeiro, Outro), com CRUD.
- **Relatórios** com exportação em CSV de colaboradores e pedidos.
- **Tema claro/escuro** por usuário.

## Stack

- [Flask 3](https://flask.palletsprojects.com/) + Blueprints
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/) (ORM) + [Flask-Migrate](https://flask-migrate.readthedocs.io/) (migrações via Alembic)
- [Flask-Login](https://flask-login.readthedocs.io/) (autenticação) + [Flask-WTF](https://flask-wtf.readthedocs.io/) (proteção CSRF)
- [PostgreSQL](https://www.postgresql.org/) via [psycopg 3](https://www.psycopg.org/psycopg3/)
- [uv](https://docs.astral.sh/uv/) para gerenciamento de dependências e ambiente virtual

## Requisitos

- Python 3.14+
- PostgreSQL rodando localmente (ou acessível via `DATABASE_URL`)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) instalado

## Configuração local

1. Clone o repositório e instale as dependências:

   ```bash
   uv sync
   ```

2. Copie o arquivo de variáveis de ambiente e preencha os valores:

   ```bash
   cp .env.example .env
   ```

   - `DATABASE_URL`: string de conexão do Postgres (ex.: `postgresql+psycopg://postgres:senha@localhost:5432/doeplus`)
   - `SECRET_KEY`: gere com `python -c "import secrets; print(secrets.token_hex(32))"`
   - `ADMIN_PASSWORD_HASH`: senha do painel administrativo (`/admin`), como hash. Gere com
     `python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SUA_SENHA'))"`
   - `SESSION_COOKIE_SECURE`: defina como `true` em produção (HTTPS)

3. Crie o banco de dados (se ainda não existir) e aplique as migrações:

   ```bash
   uv run flask db upgrade
   ```

4. Rode a aplicação em modo de desenvolvimento:

   ```bash
   uv run flask run --debug
   ```

   A aplicação sobe em `http://localhost:5000`.

## Estrutura do projeto

```
app.py               # criação e configuração da aplicação Flask, registro de blueprints
config.py            # configuração via variáveis de ambiente
extensions.py        # instâncias de db, login_manager e csrf
models.py            # modelos SQLAlchemy (Organization, User, Collaborator, CatalogItem, HelpRequest, Offer)
matching.py          # lógica de sugestão e confirmação de matches
analytics.py         # cálculo de estatísticas do dashboard por período
routes/              # blueprints (auth, admin, main, colaboradores, equipe, itens, pedidos, matches, relatorios, public_forms)
usuarios.py          # validação compartilhada de dados de usuário
templates/           # templates Jinja2
static/              # CSS e imagens
migrations/          # migrações Alembic geradas pelo Flask-Migrate
```

## Painel administrativo

Acesse `/admin` e informe a senha definida em `ADMIN_PASSWORD_HASH`. A tela lista todas as
instituições cadastradas com o número de usuários, colaboradores, pedidos e ofertas, o último
login e a última atividade, classificando cada uma como **ativa**, **ociosa**, **inativa** ou
**sem uso** conforme a data mais recente de acesso ou lançamento de dados. É independente do
login das OSCs (usa apenas a sessão de administrador).

Em `/admin/usuarios` há um CRUD dos usuários (criar, editar, redefinir senha, excluir),
com filtro por instituição. Na tela de Instituições, a ação **Excluir** apaga a instituição
e, em cascata, todos os usuários, colaboradores, pedidos e ofertas vinculados.

Cada instituição gerencia a própria equipe em **Dashboard → Equipe**
(`/dashboard/equipe`). Cada instituição tem um **responsável** (`User.is_owner`) — quem
criou a conta. Regras:

- Só o responsável adiciona, edita ou remove membros.
- Os demais membros veem a lista e editam apenas os próprios dados (nome, e-mail, senha).
- O responsável não pode ser removido nem editado por outro membro (apenas por ele mesmo
  ou pelo painel admin).

No painel admin, o formulário de usuário tem a opção **Responsável pela instituição**, que
transfere o papel (removendo de quem o tinha).

## Migrações

O histórico de alterações do banco fica em `migrations/versions/`. Ao alterar `models.py`, gere uma nova migração e aplique com:

```bash
uv run flask db migrate -m "descrição da mudança"
uv run flask db upgrade
```

## Licença

Copyright (c) 2026 Doe+ — Gustavo Higuti. Todos os direitos reservados — veja [LICENSE](LICENSE).
