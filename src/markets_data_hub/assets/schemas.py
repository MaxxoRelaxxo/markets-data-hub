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
    