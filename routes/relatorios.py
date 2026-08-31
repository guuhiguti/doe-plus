import csv
import io
from datetime import datetime, timezone

from flask import Blueprint, Response, abort, render_template, request
from flask_login import current_user, login_required

from models import Collaborator, HelpRequest

relatorios_blueprint = Blueprint("relatorios", __name__)


@relatorios_blueprint.route("/")
@login_required
def relatorio():
    collaborators = (
        Collaborator.query.filter_by(organization_id=current_user.organization_id)
        .order_by(Collaborator.created_at.desc())
        .all()
    )
    help_requests = (
        HelpRequest.query.filter_by(organization_id=current_user.organization_id)
        .order_by(HelpRequest.created_at.desc())
        .all()
    )
    pendentes = sum(1 for p in help_requests if p.status == "pendente")
    atendidos = sum(1 for p in help_requests if p.status == "atendido")

    return render_template(
        "relatorios/relatorio.html",
        collaborators=collaborators,
        help_requests=help_requests,
        pendentes=pendentes,
        atendidos=atendidos,
        gerado_em=datetime.now(timezone.utc),
    )


@relatorios_blueprint.route("/csv")
@login_required
def csv_export():
    tipo = request.args.get("tipo")
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    if tipo == "colaboradores":
        writer.writerow(["Nome", "E-mail", "Telefone", "Área", "Cadastrado em"])
        for c in Collaborator.query.filter_by(organization_id=current_user.organization_id):
            writer.writerow([c.name, c.email, c.phone, c.area, c.created_at])
    elif tipo == "pedidos":
        writer.writerow(["Solicitante", "Contato", "Item", "Quantidade", "Descrição", "Status", "Criado em"])
        for p in HelpRequest.query.filter_by(organization_id=current_user.organization_id):
            writer.writerow(
                [p.requester_name, p.contact, f"{p.item.category} — {p.item.name}", p.quantity, p.description, p.status, p.created_at]
            )
    else:
        abort(400)

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={tipo}.csv"},
    )
