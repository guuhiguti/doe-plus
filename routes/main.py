from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from analytics import PERIODO_LABELS, estatisticas_periodo, resolver_periodo
from extensions import db
from matching import encontrar_sugestoes
from models import Collaborator, HelpRequest

main_blueprint = Blueprint("main", __name__)


@main_blueprint.route("/")
def index():
    return render_template("index.html")


@main_blueprint.route("/dashboard")
@login_required
def dashboard():
    organization = current_user.organization

    periodo, inicio, fim = resolver_periodo(
        request.args.get("periodo", "mes"),
        request.args.get("inicio"),
        request.args.get("fim"),
        org_created_at=organization.created_at,
    )
    stats = estatisticas_periodo(organization.id, inicio, fim)

    colaboradores_recentes = (
        Collaborator.query.filter_by(organization_id=organization.id)
        .order_by(Collaborator.created_at.desc())
        .limit(5)
        .all()
    )
    pedidos_recentes = (
        HelpRequest.query.filter_by(organization_id=organization.id)
        .order_by(HelpRequest.created_at.desc())
        .limit(5)
        .all()
    )
    total_sugestoes = len(encontrar_sugestoes(organization.id))

    return render_template(
        "dashboard.html",
        stats=stats,
        periodo=periodo,
        periodo_labels=PERIODO_LABELS,
        inicio=inicio,
        fim=fim,
        colaboradores_recentes=colaboradores_recentes,
        pedidos_recentes=pedidos_recentes,
        total_sugestoes=total_sugestoes,
    )


@main_blueprint.route("/dashboard/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    organization = current_user.organization

    if request.method == "POST":
        nome = request.form["organization_name"].strip()
        if nome:
            organization.name = nome
            db.session.commit()
            flash("Perfil da OSC atualizado.", "success")
        return redirect(url_for("main.perfil"))

    return render_template("perfil.html", organization=organization)


@main_blueprint.route("/dashboard/configuracoes")
@login_required
def configuracoes():
    organization = current_user.organization
    link_colaborador = url_for(
        "public_forms.colaborador", token=organization.collaborator_form_token, _external=True
    )
    link_pedido = url_for("public_forms.pedido", token=organization.help_form_token, _external=True)

    return render_template(
        "configuracoes.html",
        organization=organization,
        link_colaborador=link_colaborador,
        link_pedido=link_pedido,
    )


@main_blueprint.route("/dashboard/configuracoes/tema", methods=["POST"])
@login_required
def alternar_tema():
    tema = request.form.get("tema")
    if tema in ("claro", "escuro"):
        current_user.theme = tema
        db.session.commit()
    return redirect(url_for("main.configuracoes"))
