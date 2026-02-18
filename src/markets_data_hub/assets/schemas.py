"""Schemas."""

from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

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