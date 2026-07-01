from pydantic import BaseModel


class ScrapeRequest(BaseModel):
    segmento: str
    cidade: str
    estado: str
    max_results: int = 30
    prospectador: str = ""


class LeadPayload(BaseModel):
    id: int | None = None
    history_id: int | None = None
    source_history_id: int | None = None
    source_lead_id: int | None = None
    nome: str
    categoria: str = ""
    nota: float | None = None
    avaliacoes: int | None = None
    endereco: str | None = None
    telefone: str | None = None
    is_whatsapp: bool = False
    whatsapp_link: str = ""
    site: str | None = None
    url_maps: str = ""
    porte: str = ""
    classificacao: str = ""
    score: int = 0
    cidade: str = ""
    estado: str = ""
    prospectador: str = ""


class SelectedLeadsRequest(BaseModel):
    leads: list[LeadPayload]


class SelectedLeadUpdate(BaseModel):
    notes: str | None = None
    prospectador: str | None = None
    custom_message: str | None = None


class MessageTemplateRequest(BaseModel):
    template: str


class HistoryRefreshBatchRequest(BaseModel):
    history_ids: list[int]