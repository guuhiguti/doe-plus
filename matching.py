from extensions import db
from models import HelpRequest, Offer


def encontrar_sugestoes(organization_id):
    """Pedidos pendentes que têm ao menos uma oferta disponível do mesmo item."""
    pendentes = (
        HelpRequest.query.filter_by(organization_id=organization_id, status="pendente")
        .order_by(HelpRequest.created_at.asc())
        .all()
    )
    sugestoes = []
    for pedido in pendentes:
        oferta = Offer.query.filter_by(
            organization_id=organization_id,
            item_id=pedido.item_id,
            offer_type="item",
            status="disponivel",
        ).order_by(Offer.created_at.asc()).first()
        if oferta:
            sugestoes.append((pedido, oferta))
    return sugestoes


def confirmar_match(help_request, offer):
    help_request.status = "atendido"
    offer.status = "utilizada"
    offer.matched_help_request_id = help_request.id
    db.session.commit()


def tentar_match_automatico(organization, item_id):
    """Se a OSC tiver ativado o modo automático, confirma o primeiro par pedido/oferta disponível para esse item."""
    if not organization.auto_match_enabled:
        return None

    pedido = (
        HelpRequest.query.filter_by(organization_id=organization.id, item_id=item_id, status="pendente")
        .order_by(HelpRequest.created_at.asc())
        .first()
    )
    oferta = (
        Offer.query.filter_by(
            organization_id=organization.id, item_id=item_id, offer_type="item", status="disponivel"
        )
        .order_by(Offer.created_at.asc())
        .first()
    )
    if pedido and oferta:
        confirmar_match(pedido, oferta)
        return pedido, oferta
    return None
