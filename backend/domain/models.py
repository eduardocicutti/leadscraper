from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class SearchHistory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    keyword: str
    city: str
    state: str
    status: str
    leads_found: int = 0
    prospectador: str
    created_at: datetime = Field(default_factory=datetime.now)

    leads: list["Lead"] = Relationship(
        back_populates="search_history",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Lead(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    search_history_id: int = Field(foreign_key="searchhistory.id")
    company_name: str
    phone: str | None = None
    is_whatsapp: bool = False
    whatsapp_link: str | None = None
    website: str | None = None
    address: str | None = None
    rating: float | None = None
    review_count: int | None = None
    category: str | None = None
    porte: str | None = None
    score: int = 0
    classificacao: str | None = None
    maps_url: str | None = None

    search_history: SearchHistory = Relationship(back_populates="leads")
