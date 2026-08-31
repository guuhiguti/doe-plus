from flask import Blueprint, abort, render_template, request

from extensions import db
from matching import tentar_match_automatico
from models import CatalogItem, Collaborator, HelpRequest, Offer, Organization

public_forms_blueprint = Blueprint("public_forms", __name__)


def _get_org_by_token_or_404(field, token):
    organization = Organization.query.filter_by(**{field: token}).first()
    if organization is None:
        abort(404)
    return organization


def _catalogo_por_categoria(organization_id):
    items = (
        CatalogItem.query.filter_by(organization_id=organization_id)
        .order_by(CatalogItem.category, CatalogItem.name)
        .all()
    )
    por_categoria = {}
    for item in items:
        por_categoria.setdefault(item.category, []).append(item)
    return por_categoria


@public_forms_blueprint.route("/colaborador/<token>", methods=["GET", "POST"])
def colaborador(token):
    organization = _get_org_by_token_or_404("collaborator_form_token", token)
    por_categoria = _catalogo_por_categoria(organization.id)

    if request.method == "POST":
        if not request.form.get("consentimento"):
            return render_template(
                "public/colaborador_form.html",
                organization=organization,
                por_categoria=por_categoria,
                erro="É necessário concordar com o uso dos dados para enviar o formulário.",
            )

        collaborator = Collaborator(
            organization_id=organization.id,
            name=request.form["name"].strip(),
            email=request.form.get("email", "").strip(),
            phone=request.form.get("phone", "").strip(),
            area=request.form.get("area", "").strip(),
        )
        db.session.add(collaborator)
        db.session.flush()

        offer_type = request.form["offer_type"]
        offer = Offer(
            organization_id=organization.id,
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
            tentar_match_automatico(organization, offer.item_id)

        return render_template("public/obrigado.html", organization=organization)

    return render_template("public/colaborador_form.html", organization=organization, por_categoria=por_categoria)


@public_forms_blueprint.route("/pedido/<token>", methods=["GET", "POST"])
def pedido(token):
    organization = _get_org_by_token_or_404("help_form_token", token)
    por_categoria = _catalogo_por_categoria(organization.id)

    if request.method == "POST":
        if not request.form.get("consentimento"):
            return render_template(
                "public/pedido_form.html",
                organization=organization,
                por_categoria=por_categoria,
                erro="É necessário concordar com o uso dos dados para enviar o formulário.",
            )

        help_request = HelpRequest(
            organization_id=organization.id,
            item_id=request.form["item_id"],
            requester_name=request.form["requester_name"].strip(),
            contact=request.form.get("contact", "").strip(),
            quantity=int(request.form.get("quantity") or 1),
            description=request.form.get("description", "").strip(),
        )
        db.session.add(help_request)
        db.session.commit()

        tentar_match_automatico(organization, help_request.item_id)

        return render_template("public/obrigado.html", organization=organization)

    return render_template("public/pedido_form.html", organization=organization, por_categoria=por_categoria)
