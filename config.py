import os
from dotenv import load_dotenv

load_dotenv()


def _normalizar_database_url(url):
    """Provedores como o Render fornecem postgres:// ou postgresql://;
    o psycopg3 exige o driver explícito postgresql+psycopg://."""
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo) and "+psycopg" not in url:
            return url.replace(prefixo, "postgresql+psycopg://", 1)
    return url


def _flag(nome, padrao=False):
    return os.environ.get(nome, str(padrao)).strip().lower() in ("1", "true", "yes")


class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = _normalizar_database_url(os.environ["DATABASE_URL"])
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Painel administrativo (/admin). Gere o hash com:
    #   python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('SUA_SENHA'))"
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Defina SESSION_COOKIE_SECURE=true no ambiente de produção (HTTPS).
    SESSION_COOKIE_SECURE = _flag("SESSION_COOKIE_SECURE", False)
