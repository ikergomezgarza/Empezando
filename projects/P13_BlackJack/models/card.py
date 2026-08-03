from dataclasses import dataclass
from enum import Enum
import random

class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"
    
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