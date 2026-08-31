import uuid

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from matching import tentar_match_automatico
from models import CatalogItem, HelpRequest

pedidos_blueprint = Blueprint("pedidos", __name__)


def _get_owned_or_404(help_request_id):
    help_request = db.session.get(HelpRequest, help_request_id)
    if help_request is None or help_request.organization_id != current_user.organization_id:
        abort(404)
    return help_request


def _catalogo_por_categoria():
    items = (
        CatalogItem.query.filter_by(organization_id=current_user.organization_id)
        .order_by(CatalogItem.category, CatalogItem.name)
        .all()
    )
    por_categoria = {}
    for item in items:
        por_categoria.setdefault(item.category, []).append(item)
    return por_categoria


@pedidos_blueprint.route("/")
@login_required
def listar():
    help_requests = (
        HelpRequest.query.filter_by(organization_id=current_user.organization_id)
        .order_by(HelpRequest.created_at.desc())
        .all()
    )
    return render_template("pedidos/lista.html", help_requests=help_requests)


@pedidos_blueprint.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "POST":
        help_request = HelpRequest(
            organization_id=current_user.organization_id,
            item_id=request.form["item_id"],
            requester_name=request.form["requester_name"].strip(),
            contact=request.form.get("contact", "").strip(),
            quantity=int(request.form.get("quantity") or 1),
            description=request.form.get("description", "").strip(),
        )
        db.session.add(help_request)
        db.session.commit()
        tentar_match_automatico(current_user.organization, help_request.item_id)
        flash("Pedido de ajuda registrado com sucesso.", "success")
        return redirect(url_for("pedidos.listar"))

    return render_template("pedidos/formulario.html", help_request=None, por_categoria=_catalogo_por_categoria())


@pedidos_blueprint.route("/<int:help_request_id>/editar", methods=["GET", "POST"])
@login_required
def editar(help_request_id):
    help_request = _get_owned_or_404(help_request_id)

    if request.method == "POST":
        help_request.item_id = request.form["item_id"]
        help_request.requester_name = request.form["requester_name"].strip()
        help_request.contact = request.form.get("contact", "").strip()
        help_request.quantity = int(request.form.get("quantity") or 1)
        help_request.description = request.form.get("description", "").strip()
        db.session.commit()
        flash("Pedido de ajuda atualizado com sucesso.", "success")
        return redirect(url_for("pedidos.listar"))

    return render_template(
        "pedidos/formulario.html", help_request=help_request, por_categoria=_catalogo_por_categoria()
    )


@pedidos_blueprint.route("/<int:help_request_id>/excluir", methods=["POST"])
@login_required
def excluir(help_request_id):
    help_request = _get_owned_or_404(help_request_id)
    db.session.delete(help_request)
    db.session.commit()
    flash("Pedido de ajuda removido.", "success")
    return redirect(url_for("pedidos.listar"))


@pedidos_blueprint.route("/<int:help_request_id>/status", methods=["POST"])
@login_required
def alternar_status(help_request_id):
    help_request = _get_owned_or_404(help_request_id)
    help_request.status = "atendido" if help_request.status == "pendente" else "pendente"
    db.session.commit()
    return redirect(url_for("pedidos.listar"))


@pedidos_blueprint.route("/link/regenerar", methods=["POST"])
@login_required
def regenerar_link():
    current_user.organization.help_form_token = uuid.uuid4().hex
    db.session.commit()
    flash("Novo link de formulário de pedidos de ajuda gerado.", "success")
    return redirect(url_for("main.configuracoes"))
