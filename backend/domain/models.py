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


class SelectedLead(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    source_history_id: int | None = Field(default=None, foreign_key="searchhistory.id")
    source_lead_id: int | None = Field(default=None, foreign_key="lead.id")
    company_name: str
    phone: str | None = None
    normalized_phone: str | None = Field(default=None, index=True)
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
    maps_url: str | None = Field(default=None, index=True)
    segmento: str | None = None
    city: str | None = None
    state: str | None = None
    prospectador: str | None = None
    notes: str = ""
    custom_message: str = ""
    last_message_updated_at: datetime | None = None
    selected_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AppSetting(SQLModel, table=True):
    key: str = Field(primary_key=True)
    value: str
    updated_at: datetime = Field(default_factory=datetime.now)