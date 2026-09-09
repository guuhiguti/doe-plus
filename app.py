from flask import Flask
from flask_migrate import Migrate

from config import Config
from extensions import csrf, db, login_manager
import models  # noqa: F401 ensures models are registered before migrations
from timezones import formatar as _formatar_brasilia
from routes.admin import admin_blueprint
from routes.auth import auth_blueprint
from routes.colaboradores import colaboradores_blueprint
from routes.equipe import equipe_blueprint
from routes.itens import itens_blueprint
from routes.main import main_blueprint
from routes.matches import matches_blueprint
from routes.pedidos import pedidos_blueprint
from routes.public_forms import public_forms_blueprint
from routes.relatorios import relatorios_blueprint

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
login_manager.init_app(app)
login_manager.login_view = "auth.login"
csrf.init_app(app)


@app.template_filter("data")
def _filtro_data(dt):
    """dd/mm/aaaa no horário de Brasília."""
    return _formatar_brasilia(dt, "%d/%m/%Y")


@app.template_filter("data_hora")
def _filtro_data_hora(dt):
    """dd/mm/aaaa hh:mm no horário de Brasília."""
    return _formatar_brasilia(dt, "%d/%m/%Y %H:%M")


@app.template_filter("data_iso")
def _filtro_data_iso(dt):
    """aaaa-mm-dd no horário de Brasília (para <input type=\"date\">)."""
    return _formatar_brasilia(dt, "%Y-%m-%d")


@login_manager.user_loader
def load_user(user_id):
    from models import User

    return db.session.get(User, int(user_id))


app.register_blueprint(main_blueprint, url_prefix="/")
app.register_blueprint(auth_blueprint, url_prefix="/auth")
app.register_blueprint(admin_blueprint, url_prefix="/admin")
app.register_blueprint(colaboradores_blueprint, url_prefix="/dashboard/colaboradores")
app.register_blueprint(pedidos_blueprint, url_prefix="/dashboard/pedidos")
app.register_blueprint(public_forms_blueprint, url_prefix="/formulario")
app.register_blueprint(relatorios_blueprint, url_prefix="/dashboard/relatorio")
app.register_blueprint(itens_blueprint, url_prefix="/dashboard/itens")
app.register_blueprint(matches_blueprint, url_prefix="/dashboard/cruzamentos")
app.register_blueprint(equipe_blueprint, url_prefix="/dashboard/equipe")

if __name__ == "__main__":
    app.run(debug=True)
