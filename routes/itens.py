from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import CatalogItem, HelpRequest, Offer

itens_blueprint = Blueprint("itens", __name__)


@itens_blueprint.route("/")
@login_required
def listar():
    items = (
        CatalogItem.query.filter_by(organization_id=current_user.organization_id)
        .order_by(CatalogItem.category, CatalogItem.name)
        .all()
    )
    por_categoria = {}
    for item in items:
        por_categoria.setdefault(item.category, []).append(item)
    return render_template("itens/lista.html", por_categoria=por_categoria)


@itens_blueprint.route("/novo", methods=["GET", "POST"])
@login_required
def novo():
    if request.method == "POST":
        category = request.form["category"].strip()
        name = request.form["name"].strip()

        existente = CatalogItem.query.filter_by(
            organization_id=current_user.organization_id, category=category, name=name
        ).first()
        if existente:
            flash("Esse item já existe nessa categoria.", "error")
            return render_template("itens/formulario.html", category=category, name=name)

        db.session.add(CatalogItem(organization_id=current_user.organization_id, category=category, name=name))
        db.session.commit()
        flash("Item adicionado ao catálogo.", "success")
        return redirect(url_for("itens.listar"))

    return render_template("itens/formulario.html")


@itens_blueprint.route("/<int:item_id>/excluir", methods=["POST"])
@login_required
def excluir(item_id):
    item = db.session.get(CatalogItem, item_id)
    if item is None or item.organization_id != current_user.organization_id:
        flash("Item não encontrado.", "error")
        return redirect(url_for("itens.listar"))

    em_uso = (
        HelpRequest.query.filter_by(item_id=item.id).first()
        or Offer.query.filter_by(item_id=item.id).first()
    )
    if em_uso:
        flash("Esse item já está sendo usado em pedidos ou ofertas e não pode ser excluído.", "error")
        return redirect(url_for("itens.listar"))

    db.session.delete(item)
    db.session.commit()
    flash("Item removido do catálogo.", "success")
    return redirect(url_for("itens.listar"))
