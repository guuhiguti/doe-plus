import functools
import time
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import func
from werkzeug.security import check_password_hash

from extensions import db
from models import Collaborator, HelpRequest, Offer, Organization, User
from usuarios import validar_usuario

admin_blueprint = Blueprint("admin", __name__)

# Janelas (em dias) para classificar o uso de cada instituição.
DIAS_ATIVA = 14
DIAS_OCIOSA = 60

# Proteção simples contra força bruta no login (por IP, em memória do processo).
MAX_TENTATIVAS = 5
BLOQUEIO_SEGUNDOS = 300
_tentativas = {}


def _ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0].strip()


def _bloqueado(ip):
    registro = _tentativas.get(ip)
    if not registro:
        return False
    falhas, ultima = registro
    if falhas < MAX_TENTATIVAS:
        return False
    if time.time() - ultima > BLOQUEIO_SEGUNDOS:
        _tentativas.pop(ip, None)
        return False
    return True


def _registrar_falha(ip):
    falhas, _ = _tentativas.get(ip, (0, 0))
    _tentativas[ip] = (falhas + 1, time.time())


def admin_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)

    return wrapped


@admin_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if session.get("is_admin"):
        return redirect(url_for("admin.painel"))

    if request.method == "POST":
        ip = _ip()
        if _bloqueado(ip):
            flash("Muitas tentativas. Tente novamente em alguns minutos.", "error")
            return render_template("admin/login.html")

        hash_ref = current_app.config.get("ADMIN_PASSWORD_HASH")
        senha = request.form.get("password", "")
        if hash_ref and check_password_hash(hash_ref, senha):
            _tentativas.pop(ip, None)
            session["is_admin"] = True
            return redirect(url_for("admin.painel"))

        _registrar_falha(ip)
        flash("Senha incorreta.", "error")

    return render_template("admin/login.html")


@admin_blueprint.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin.login"))


def _contagem_por_org(model):
    return dict(
        db.session.query(model.organization_id, func.count(model.id))
        .group_by(model.organization_id)
        .all()
    )


def _ultimo_por_org(model, coluna):
    return dict(
        db.session.query(model.organization_id, func.max(coluna))
        .group_by(model.organization_id)
        .all()
    )


@admin_blueprint.route("/")
@admin_required
def painel():
    agora = datetime.now(timezone.utc)

    usuarios = _contagem_por_org(User)
    colaboradores = _contagem_por_org(Collaborator)
    pedidos = _contagem_por_org(HelpRequest)
    ofertas = _contagem_por_org(Offer)

    ult_login = _ultimo_por_org(User, User.last_login_at)
    ult_colab = _ultimo_por_org(Collaborator, Collaborator.created_at)
    ult_pedido = _ultimo_por_org(HelpRequest, HelpRequest.created_at)
    ult_oferta = _ultimo_por_org(Offer, Offer.created_at)

    linhas = []
    for org in Organization.query.order_by(Organization.created_at.desc()).all():
        marcos = [
            d
            for d in (
                ult_login.get(org.id),
                ult_colab.get(org.id),
                ult_pedido.get(org.id),
                ult_oferta.get(org.id),
            )
            if d is not None
        ]
        ultima_atividade = max(marcos) if marcos else None
        total_dados = (
            colaboradores.get(org.id, 0)
            + pedidos.get(org.id, 0)
            + ofertas.get(org.id, 0)
        )

        if ultima_atividade is None or total_dados == 0:
            status = "sem uso"
        elif agora - ultima_atividade <= timedelta(days=DIAS_ATIVA):
            status = "ativa"
        elif agora - ultima_atividade <= timedelta(days=DIAS_OCIOSA):
            status = "ociosa"
        else:
            status = "inativa"

        linhas.append(
            {
                "org": org,
                "usuarios": usuarios.get(org.id, 0),
                "colaboradores": colaboradores.get(org.id, 0),
                "pedidos": pedidos.get(org.id, 0),
                "ofertas": ofertas.get(org.id, 0),
                "ultimo_login": ult_login.get(org.id),
                "ultima_atividade": ultima_atividade,
                "status": status,
            }
        )

    resumo = {
        "total": len(linhas),
        "ativa": sum(1 for linha in linhas if linha["status"] == "ativa"),
        "ociosa": sum(1 for linha in linhas if linha["status"] == "ociosa"),
        "inativa": sum(1 for linha in linhas if linha["status"] == "inativa"),
        "sem uso": sum(1 for linha in linhas if linha["status"] == "sem uso"),
    }

    return render_template("admin/painel.html", linhas=linhas, resumo=resumo, agora=agora)


# --------------------------------------------------------------------------- #
# CRUD de usuários
# --------------------------------------------------------------------------- #

def _ler_form_usuario():
    return {
        "organization_id": request.form.get("organization_id", type=int),
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "password": request.form.get("password", ""),
        "is_owner": request.form.get("is_owner") == "1",
    }


def _aplicar_responsavel(usuario, org_id, is_owner):
    """Garante no máximo um responsável por instituição."""
    if is_owner:
        User.query.filter_by(organization_id=org_id).update(
            {"is_owner": False}, synchronize_session=False
        )
        usuario.is_owner = True
    else:
        usuario.is_owner = False


def _validar_usuario(form, usuario):
    if not form["organization_id"] or not db.session.get(Organization, form["organization_id"]):
        return "Selecione uma instituição válida."
    return validar_usuario(
        form["name"], form["email"], form["password"],
        senha_obrigatoria=usuario is None, usuario_atual=usuario,
    )


@admin_blueprint.route("/usuarios")
@admin_required
def usuarios():
    org_id = request.args.get("org", type=int)
    query = User.query.order_by(User.created_at.desc())
    if org_id:
        query = query.filter_by(organization_id=org_id)
    return render_template(
        "admin/usuarios.html",
        usuarios=query.all(),
        orgs=Organization.query.order_by(Organization.name).all(),
        org_id=org_id,
        agora=datetime.now(timezone.utc),
    )


@admin_blueprint.route("/usuarios/novo", methods=["GET", "POST"])
@admin_required
def usuario_novo():
    orgs = Organization.query.order_by(Organization.name).all()
    form = {"organization_id": request.args.get("org", type=int)}

    if request.method == "POST":
        form = _ler_form_usuario()
        erro = _validar_usuario(form, None)
        if erro:
            flash(erro, "error")
        else:
            usuario = User(
                organization_id=form["organization_id"],
                name=form["name"],
                email=form["email"],
            )
            usuario.set_password(form["password"])
            db.session.add(usuario)
            _aplicar_responsavel(usuario, form["organization_id"], form["is_owner"])
            db.session.commit()
            flash("Usuário criado.", "success")
            return redirect(url_for("admin.usuarios", org=form["organization_id"]))

    return render_template("admin/usuario_form.html", orgs=orgs, usuario=None, form=form)


@admin_blueprint.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@admin_required
def usuario_editar(user_id):
    usuario = db.get_or_404(User, user_id)
    orgs = Organization.query.order_by(Organization.name).all()
    form = {
        "organization_id": usuario.organization_id,
        "name": usuario.name,
        "email": usuario.email,
        "password": "",
        "is_owner": usuario.is_owner,
    }

    if request.method == "POST":
        form = _ler_form_usuario()
        erro = _validar_usuario(form, usuario)
        if erro:
            flash(erro, "error")
        else:
            usuario.organization_id = form["organization_id"]
            usuario.name = form["name"]
            usuario.email = form["email"]
            if form["password"]:
                usuario.set_password(form["password"])
            _aplicar_responsavel(usuario, form["organization_id"], form["is_owner"])
            db.session.commit()
            flash("Usuário atualizado.", "success")
            return redirect(url_for("admin.usuarios", org=usuario.organization_id))

    return render_template("admin/usuario_form.html", orgs=orgs, usuario=usuario, form=form)


@admin_blueprint.route("/usuarios/<int:user_id>/excluir", methods=["POST"])
@admin_required
def usuario_excluir(user_id):
    usuario = db.get_or_404(User, user_id)
    org_id = usuario.organization_id
    db.session.delete(usuario)
    db.session.commit()
    flash("Usuário excluído.", "success")
    return redirect(url_for("admin.usuarios", org=org_id))


@admin_blueprint.route("/instituicoes/<int:org_id>/excluir", methods=["POST"])
@admin_required
def instituicao_excluir(org_id):
    org = db.get_or_404(Organization, org_id)
    nome = org.name
    db.session.delete(org)
    db.session.commit()
    flash(
        f'Instituição "{nome}" excluída, junto com usuários, colaboradores, '
        "pedidos e ofertas vinculados.",
        "success",
    )
    return redirect(url_for("admin.painel"))
