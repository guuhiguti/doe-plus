from datetime import datetime, timedelta, timezone

from extensions import db
from models import CatalogItem, Collaborator, HelpRequest

PERIODOS_VALIDOS = {"hoje", "mes", "90dias", "tudo", "personalizado"}

PERIODO_LABELS = {
    "hoje": "Hoje",
    "mes": "Este mês",
    "90dias": "Últimos 90 dias",
    "tudo": "Todo o período",
    "personalizado": "Personalizado",
}


def resolver_periodo(periodo, inicio_str=None, fim_str=None, org_created_at=None):
    """Retorna (periodo_normalizado, inicio, fim) como datetimes com timezone UTC."""
    agora = datetime.now(timezone.utc)
    fim = agora

    if periodo == "hoje":
        inicio = agora.replace(hour=0, minute=0, second=0, microsecond=0)
    elif periodo == "90dias":
        inicio = agora - timedelta(days=90)
    elif periodo == "tudo":
        inicio = org_created_at or (agora - timedelta(days=3650))
    elif periodo == "personalizado" and inicio_str and fim_str:
        try:
            inicio = datetime.strptime(inicio_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            fim = datetime.strptime(fim_str, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )
        except ValueError:
            periodo, inicio, fim = "mes", _inicio_mes(agora), agora
    else:
        periodo, inicio = "mes", _inicio_mes(agora)

    return periodo, inicio, fim


def _inicio_mes(agora):
    return agora.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _granularidade(inicio, fim):
    span_dias = (fim - inicio).days
    if span_dias <= 31:
        return "dia"
    if span_dias <= 180:
        return "semana"
    return "mes"


def _bucket_key(dt, granularidade):
    if granularidade == "dia":
        return dt.date()
    if granularidade == "semana":
        return (dt - timedelta(days=dt.weekday())).date()
    return dt.date().replace(day=1)


def _bucket_label(data, granularidade):
    if granularidade == "mes":
        return data.strftime("%m/%Y")
    return data.strftime("%d/%m")


def estatisticas_periodo(organization_id, inicio, fim):
    pedidos = HelpRequest.query.filter(
        HelpRequest.organization_id == organization_id,
        HelpRequest.created_at >= inicio,
        HelpRequest.created_at <= fim,
    ).all()

    colaboradores_total = Collaborator.query.filter(
        Collaborator.organization_id == organization_id,
        Collaborator.created_at >= inicio,
        Collaborator.created_at <= fim,
    ).count()

    total_pedidos = len(pedidos)
    pendentes = sum(1 for p in pedidos if p.status == "pendente")
    atendidos = sum(1 for p in pedidos if p.status == "atendido")
    taxa_atendimento = round((atendidos / total_pedidos) * 100) if total_pedidos else 0

    contagem_itens = {}
    for p in pedidos:
        contagem_itens[p.item_id] = contagem_itens.get(p.item_id, 0) + 1
    ranking = sorted(contagem_itens.items(), key=lambda kv: kv[1], reverse=True)[:6]
    itens_ranking = []
    for item_id, quantidade in ranking:
        item = db.session.get(CatalogItem, item_id)
        itens_ranking.append({"nome": item.name if item else "Item removido", "quantidade": quantidade})

    granularidade = _granularidade(inicio, fim)
    buckets = {}
    for p in pedidos:
        chave = _bucket_key(p.created_at, granularidade)
        buckets[chave] = buckets.get(chave, 0) + 1
    serie_temporal = [
        {"label": _bucket_label(data, granularidade), "quantidade": quantidade}
        for data, quantidade in sorted(buckets.items())
    ]

    return {
        "colaboradores_total": colaboradores_total,
        "total_pedidos": total_pedidos,
        "pendentes": pendentes,
        "atendidos": atendidos,
        "taxa_atendimento": taxa_atendimento,
        "itens_ranking": itens_ranking,
        "max_item_quantidade": max((i["quantidade"] for i in itens_ranking), default=1),
        "serie_temporal": serie_temporal,
        "max_serie_quantidade": max((s["quantidade"] for s in serie_temporal), default=1),
    }
