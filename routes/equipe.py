from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import User
from usuarios import validar_usuario

equipe_blueprint = Blueprint("equipe", __name__)


def _membro_da_equipe(user_id):
    user = db.session.get(User, user_id)
    if user is None or user.organization_id != current_user.organization_id:
        abort(404)
    return user


def _ler_form():
    return {
        "name": request.form.get("name", "").strip(),
        "email": request.form.get("email", "").strip().lower(),
        "password": request.form.get("password", ""),
    }


@equipe_blueprint.route("/")
@login_required
def listar():
    membros = (
        User.query.filter_by(organization_id=current_user.organization_id)
        .order_by(User.created_at.asc())
        .all()
    )
    return render_template("equipe/lista.html", membros=membros)


@equipe_blueprint.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if not current_user.is_owner:
        abort(403)
    form = {}
    if request.method == "POST":
        form = _ler_form()
        erro = validar_usuario(form["name"], form["email"], form["password"], senha_obrigatoria=True)
        if erro:
            flash(erro, "error")
        else:
            membro = User(
                organization_id=current_user.organization_id,
                name=form["name"],
                email=form["email"],
            )
            membro.set_password(form["password"])
            db.session.add(membro)
            db.session.commit()
            flash("Membro adicionado à equipe.", "success")
            return redirect(url_for("equipe.listar"))

    return render_template("equipe/formulario.html", membro=None, form=form)


@equipe_blueprint.route("/<int:user_id>/editar", methods=["GET", "POST"])
@login_required
def editar(user_id):
    membro = _membro_da_equipe(user_id)
    if not current_user.is_owner and membro.id != current_user.id:
        abort(403)
    form = {"name": membro.name, "email": membro.email, "password": ""}

    if request.method == "POST":
        form = _ler_form()
        erro = validar_usuario(
            form["name"], form["email"], form["password"],
            senha_obrigatoria=False, usuario_atual=membro,
        )
        if erro:
            flash(erro, "error")
        else:
            membro.name = form["name"]
            membro.email = form["email"]
            if form["password"]:
                membro.set_password(form["password"])
            db.session.commit()
            flash("Membro atualizado.", "success")
            return redirect(url_for("equipe.listar"))

    return render_template("equipe/formulario.html", membro=membro, form=form)


@equipe_blueprint.route("/<int:user_id>/excluir", methods=["POST"])
@login_required
def excluir(user_id):
    membro = _membro_da_equipe(user_id)
    if not current_user.is_owner:
        abort(403)
    if membro.is_owner:
        flash("O responsável pela instituição não pode ser removido.", "error")
    else:
        db.session.delete(membro)
        db.session.commit()
        flash("Membro removido da equipe.", "success")
    return redirect(url_for("equipe.listar"))
