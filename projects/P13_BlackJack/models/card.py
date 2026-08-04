from dataclasses import dataclass
from enum import Enum
import random

from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "PNG-cards-1.3"

class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"

RANK_NAMES = {
    "J": "jack",
    "Q": "queen",
    "K": "king",
    "A": "ace",
}
    
@dataclass
class Card:
    
    rank: str
    suit: Suit
    
    @property
    def value(self):
        if self.rank in ("J", "Q", "K"):
            return 10 
        if self.rank == "A":
            return 11
        return int(self.rank)
    
    def __str__(self):
        return f"{self.rank}{self.suit.value}"
    
    def image_path(self) -> str:
        suit_name = self.suit.name.lower()
        rank_name = RANK_NAMES.get(self.rank, self.rank)  # J/Q/K/A -> words, 2-10 unchanged
        return str(ASSETS_DIR / f"{rank_name}_of_{suit_name}.png")