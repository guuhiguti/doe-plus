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


class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = _normalizar_database_url(os.environ["DATABASE_URL"])
    SQLALCHEMY_TRACK_MODIFICATIONS = False
