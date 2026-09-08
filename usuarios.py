"""Validação compartilhada de dados de usuário (painel admin e painel de equipe)."""

from models import User

SENHA_MIN = 8


def validar_usuario(name, email, password, senha_obrigatoria, usuario_atual=None):
    """Retorna uma mensagem de erro (str) ou None se os dados forem válidos."""
    if not name:
        return "Informe o nome do usuário."
    if not email:
        return "Informe o e-mail."
    existente = User.query.filter_by(email=email).first()
    if existente and (usuario_atual is None or existente.id != usuario_atual.id):
        return "Já existe um usuário com esse e-mail."
    if (senha_obrigatoria or password) and len(password) < SENHA_MIN:
        return f"A senha deve ter ao menos {SENHA_MIN} caracteres."
    return None
