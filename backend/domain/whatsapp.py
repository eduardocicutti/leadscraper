import re
import urllib.parse


def build_whatsapp_link(telefone: str, nome_empresa: str) -> str:
    if not telefone:
        return ""
    digits = re.sub(r"\D", "", telefone)
    if not digits.startswith("55"):
        digits = "55" + digits
    msg = (
        f"Olá! Tudo bem? 😊\n\n"
        f"Entrei em contato porque identificamos que a *{nome_empresa}* "
        f"pode se beneficiar com soluções digitais personalizadas — seja um site institucional, "
        f"landing page, sistema web ou aplicativo mobile.\n\n"
        f"Posso te apresentar como podemos ajudar? Seria rapidinho! 🚀"
    )
    encoded = urllib.parse.quote(msg)
    return f"https://wa.me/{digits}?text={encoded}"
