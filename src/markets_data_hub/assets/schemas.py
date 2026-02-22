"""Schemas."""

from pydantic import (
    BaseModel,
    ConfigDict,
    field_validator
)
from typing import Optional
from datetime import date, datetime

class RbCertAuctionResult(BaseModel):
    """Riksbank certificats."""
    model_config = ConfigDict(extra='ignore')

    Anbudsdag: date
    Likviddag: date
    Forfallodag: date
    Rantesats : float
    Erbjuden_volym: float
    Totalt_budbelopp: float
    Tilldelad_volym: float
    Antal_bud: int
    Tilldelningsprocent : float
    Isin: str
    Source_url : str


class AuctionResult(BaseModel):
    model_config = ConfigDict(extra='ignore')

    Anbudsdag: date
    Lan: int
    Isin: str
    Kupong: Optional[float] = None
    Forfallodag: date
    Erbjuden_volym: Optional[str] = None
    Budvolym: Optional[int] = None
    Tilldelad_volym: Optional[int] = None
    Antal_bud: Optional[int] = None
    Antal_godkända_bud: Optional[int] = None
    Genomsnittlig_ranta: Optional[float] = None
    Lagsta_ranta: Optional[float] = None
    Hogst_accepterade_ranta: Optional[float] = None
    Tilldelning_hosta_ranta: Optional[float] = None
    Source_url : str


class SwestrResult(BaseModel):
    """SWESTR."""
    model_config = ConfigDict(extra='ignore')

    rate: float
    date: date
    pctl12_5: Optional[float] = None
    pctl87_5: Optional[float] = None
    volume: Optional[int] = None
    alternativeCalculation: bool
    alternativeCalculationReason: Optional[str] = None
    publicationTime: datetime
    republication: bool
    numberOfTransactions: Optional[int] = None
    numberOfAgents: Optional[int] = None

    @field_validator("numberOfAgents", "numberOfTransactions", "volume", mode="before")
    @classmethod
    def coerce_to_int(cls, v):
        if v is None:
            return None
        return int(v)