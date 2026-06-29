HIGH_FIT_SEGMENTS = [
    "clínica", "consultório", "odontologia", "dentista", "médico", "saúde",
    "advocacia", "advogado", "escritório", "contabilidade", "contador",
    "imobiliária", "imóveis", "corretor",
    "academia", "personal", "fitness",
    "restaurante", "lanchonete", "delivery", "alimentação",
    "hotel", "pousada", "turismo",
    "escola", "curso", "educação", "colégio",
    "loja", "comércio", "varejo", "e-commerce",
    "construtora", "engenharia", "arquitetura",
    "pet", "veterinário",
    "beleza", "estética", "salão", "barbearia",
    "tecnologia", "software", "startup",
    "indústria", "manufatura", "fábrica",
    "logística", "transportadora",
    "financeiro", "investimento", "seguro",
]

PORTE_KEYWORDS = {
    "MEI / Autônomo": ["autônomo", "individual", "freelancer", "mei"],
    "Micro empresa": ["micro", "microempresa"],
    "Pequena empresa": ["pequena", "ltda", "me "],
    "Média empresa": ["média", "médio porte"],
    "Grande empresa": ["grande", "s/a", "sa ", "grupo ", "holding", "nacional", "rede "],
}


def classify_porte(nome: str, categoria: str, avaliacoes: int) -> str:
    texto = f"{nome} {categoria}".lower()
    for porte, keywords in PORTE_KEYWORDS.items():
        if any(keyword in texto for keyword in keywords):
            return porte
    if not avaliacoes:
        return "Micro empresa"
    if avaliacoes >= 500:
        return "Grande empresa"
    if avaliacoes >= 200:
        return "Média empresa"
    if avaliacoes >= 50:
        return "Pequena empresa"
    return "Micro empresa"


def score_lead(lead: dict) -> tuple[str, int]:
    score = 0
    avaliacoes = lead.get("avaliacoes") or 0
    nota = lead.get("nota") or 0.0
    tem_site = bool(lead.get("site"))
    tem_tel = bool(lead.get("telefone"))
    categoria = (lead.get("categoria") or "").lower()
    nome = (lead.get("nome") or "").lower()
    porte = lead.get("porte") or ""

    if not tem_site:
        score += 25
    else:
        score += 5

    if avaliacoes >= 100:
        score += 20
    elif avaliacoes >= 50:
        score += 15
    elif avaliacoes >= 10:
        score += 10
    elif avaliacoes >= 1:
        score += 5

    if nota >= 4.5:
        score += 15
    elif nota >= 4.0:
        score += 10
    elif nota >= 3.5:
        score += 5

    if any(keyword in categoria or keyword in nome for keyword in HIGH_FIT_SEGMENTS):
        score += 20
    if tem_tel:
        score += 10

    porte_pts = {
        "Grande empresa": 15,
        "Média empresa": 12,
        "Pequena empresa": 10,
        "Micro empresa": 5,
        "MEI / Autônomo": 2,
    }
    score += porte_pts.get(porte, 5)
    score = min(score, 100)

    if score >= 70:
        classificacao = "🔥 Quente"
    elif score >= 45:
        classificacao = "🟡 Morno"
    else:
        classificacao = "❄️ Frio"

    return classificacao, score
