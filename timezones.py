"""Conversão de datas/horas para o horário de Brasília (America/Sao_Paulo).

Tudo é armazenado em UTC no banco; a exibição para o usuário usa o fuso de
Brasília, que é o padrão de Campinas/São Paulo.
"""

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

TZ_BRASILIA = ZoneInfo("America/Sao_Paulo")


def to_brasilia(dt):
    """Converte um datetime (UTC, aware ou naive) para o horário de Brasília."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(TZ_BRASILIA)


def agora_brasilia():
    """Instante atual no horário de Brasília."""
    return datetime.now(TZ_BRASILIA)


def formatar(dt, formato="%d/%m/%Y %H:%M"):
    """Formata um datetime já convertido para o horário de Brasília."""
    convertido = to_brasilia(dt)
    return convertido.strftime(formato) if convertido else ""
