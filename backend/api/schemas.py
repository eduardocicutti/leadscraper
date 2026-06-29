from pydantic import BaseModel


class ScrapeRequest(BaseModel):
    segmento: str
    cidade: str
    estado: str
    max_results: int = 30
    prospectador: str = ""
