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
    segmento: str | None = None


class SegmentTemplateRequest(BaseModel):
    segmento: str
    template: str


class SelectedLeadFilters(BaseModel):
    segmento: str = ""
    cidade: str = ""
    estado: str = ""
    temperatura: str = ""
    com_whatsapp: str = ""
    com_site: str = ""
    prospectador: str = ""


class HistoryRefreshBatchRequest(BaseModel):
    history_ids: list[int]


class SpreadsheetImportRequest(BaseModel):
    filename: str
    content_base64: str
    prospectador: str = ""


class BackupRestoreRequest(BaseModel):
    filename: str = "lead-scraper-backup.db"
    content_base64: str
