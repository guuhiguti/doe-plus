import uuid

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from matching import tentar_match_automatico
from models import CatalogItem, Collaborator, Offer

colaboradores_blueprint = Blueprint("colaboradores", __name__)


def _get_owned_or_404(collaborator_id):
    collaborator = db.session.get(Collaborator, collaborator_id)
    if collaborator is None or collaborator.organization_id != current_user.organization_id:
        abort(404)
    return collaborator


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


@colaboradores_blueprint.route("/")
@login_required
def listar():
    collaborators = (
        Collaborator.query.filter_by(organization_id=current_user.organization_id)
        .order_by(Collaborator.created_at.desc())
        .all()
    )
    return render_template("colaboradores/lista.html", collaborators=collaborators)


@colaboradores_blueprint.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "POST":
        collaborator = Collaborator(
            organization_id=current_user.organization_id,
            name=request.form["name"].strip(),
            email=request.form.get("email", "").strip(),
            phone=request.form.get("phone", "").strip(),
            area=request.form.get("area", "").strip(),
        )
        db.session.add(collaborator)
        db.session.commit()
        flash("Colaborador cadastrado com sucesso.", "success")
        return redirect(url_for("colaboradores.listar"))

    return render_template("colaboradores/formulario.html", collaborator=None)


@colaboradores_blueprint.route("/<int:collaborator_id>/editar", methods=["GET", "POST"])
@login_required
def editar(collaborator_id):
    collaborator = _get_owned_or_404(collaborator_id)

    if request.method == "POST":
        collaborator.name = request.form["name"].strip()
        collaborator.email = request.form.get("email", "").strip()
        collaborator.phone = request.form.get("phone", "").strip()
        collaborator.area = request.form.get("area", "").strip()
        db.session.commit()
        flash("Colaborador atualizado com sucesso.", "success")
        return redirect(url_for("colaboradores.listar"))

    ofertas = (
        Offer.query.filter_by(collaborator_id=collaborator.id).order_by(Offer.created_at.desc()).all()
    )
    return render_template("colaboradores/formulario.html", collaborator=collaborator, ofertas=ofertas)


@colaboradores_blueprint.route("/<int:collaborator_id>/excluir", methods=["POST"])
@login_required
def excluir(collaborator_id):
    collaborator = _get_owned_or_404(collaborator_id)
    db.session.delete(collaborator)
    db.session.commit()
    flash("Colaborador removido.", "success")
    return redirect(url_for("colaboradores.listar"))


@colaboradores_blueprint.route("/<int:collaborator_id>/ofertas/nova", methods=["GET", "POST"])
@login_required
def nova_oferta(collaborator_id):
    collaborator = _get_owned_or_404(collaborator_id)

    if request.method == "POST":
        offer_type = request.form["offer_type"]
        offer = Offer(
            organization_id=current_user.organization_id,
            collaborator_id=collaborator.id,
            offer_type=offer_type,
            notes=request.form.get("notes", "").strip(),
        )
        if offer_type == "item":
            offer.item_id = request.form["item_id"]
            offer.quantity = int(request.form.get("quantity") or 1)

        db.session.add(offer)
        db.session.commit()

        if offer_type == "item":
            tentar_match_automatico(current_user.organization, offer.item_id)

        flash("Oferta registrada com sucesso.", "success")
        return redirect(url_for("colaboradores.editar", collaborator_id=collaborator.id))

    return render_template(
        "colaboradores/oferta_formulario.html", collaborator=collaborator, por_categoria=_catalogo_por_categoria()
    )


@colaboradores_blueprint.route("/link/regenerar", methods=["POST"])
@login_required
def regenerar_link():
    current_user.organization.collaborator_form_token = uuid.uuid4().hex
    db.session.commit()
    flash("Novo link de formulário de colaboradores gerado.", "success")
    return redirect(url_for("main.configuracoes"))
