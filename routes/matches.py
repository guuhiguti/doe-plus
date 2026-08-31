from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from matching import confirmar_match, encontrar_sugestoes
from models import HelpRequest, Offer

matches_blueprint = Blueprint("matches", __name__)


@matches_blueprint.route("/")
@login_required
def listar():
    sugestoes = encontrar_sugestoes(current_user.organization_id)
    return render_template("matches/lista.html", sugestoes=sugestoes)


@matches_blueprint.route("/confirmar", methods=["POST"])
@login_required
def confirmar():
    help_request = db.session.get(HelpRequest, request.form["help_request_id"])
    offer = db.session.get(Offer, request.form["offer_id"])

    if (
        help_request is None
        or offer is None
        or help_request.organization_id != current_user.organization_id
        or offer.organization_id != current_user.organization_id
    ):
        abort(404)

    confirmar_match(help_request, offer)
    flash("Match confirmado! Pedido marcado como atendido.", "success")
    return redirect(url_for("matches.listar"))


@matches_blueprint.route("/auto-match", methods=["POST"])
@login_required
def alternar_auto_match():
    organization = current_user.organization
    organization.auto_match_enabled = not organization.auto_match_enabled
    db.session.commit()
    flash(
        "Confirmação automática ativada." if organization.auto_match_enabled else "Confirmação automática desativada.",
        "success",
    )
    return redirect(url_for("main.configuracoes"))
