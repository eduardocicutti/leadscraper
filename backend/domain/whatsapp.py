import re
import urllib.parse

DEFAULT_MESSAGE_TEMPLATE = (
    "Olá! Tudo bem? 😊\n\n"
    "Entrei em contato porque identificamos que a *{empresa}* pode se beneficiar "
    "com soluções digitais personalizadas — seja um site institucional, landing page, "
    "sistema web ou aplicativo mobile.\n\n"
    "Posso te apresentar como podemos ajudar? Seria rapidinho! 🚀"
)


def phone_digits(telefone: str | None) -> str:
    return re.sub(r"\D", "", telefone or "")


def whatsapp_digits(telefone: str | None) -> str:
    digits = phone_digits(telefone)
    if not digits:
        return ""
    if not digits.startswith("55"):
        digits = "55" + digits
    return digits


def format_phone_br(telefone: str | None) -> str:
    digits = phone_digits(telefone)
    if not digits:
        return ""
    if digits.startswith("55") and len(digits) in (12, 13):
        digits = digits[2:]
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    return digits


def render_message(template: str, *, nome_empresa: str, segmento: str = "", cidade: str = "", estado: str = "", prospectador: str = "") -> str:
    values = {
        "empresa": nome_empresa or "sua empresa",
        "segmento": segmento or "",
        "cidade": cidade or "",
        "estado": estado or "",
        "prospectador": prospectador or "",
    }
    try:
        return template.format(**values)
    except Exception:
        return template


def build_whatsapp_link(
    telefone: str | None,
    nome_empresa: str,
    message_template: str = DEFAULT_MESSAGE_TEMPLATE,
    segmento: str = "",
    cidade: str = "",
    estado: str = "",
    prospectador: str = "",
    custom_message: str | None = None,
) -> str:
    digits = whatsapp_digits(telefone)
    if not digits:
        return ""
    template = custom_message.strip() if custom_message and custom_message.strip() else message_template
    msg = render_message(
        template,
        nome_empresa=nome_empresa,
        segmento=segmento,
        cidade=cidade,
        estado=estado,
        prospectador=prospectador,
    )
    encoded = urllib.parse.quote(msg)
    return f"https://wa.me/{digits}?text={encoded}"