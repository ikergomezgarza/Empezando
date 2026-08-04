from .card import Card, Suit
import random

class Shoe:
    
    RANKS = [ "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    
    def __init__(self, num_decks: int = 1):
        self.num_decks = num_decks
        self.cards = []
        self.build()
        
    def build(self):
        
        self.cards= [
            Card(rank, suit)
            for _ in range(self.num_decks)
            for suit in Suit
            for rank in self.RANKS
              
        ]
        random.shuffle(self.cards)
        
    def cards_remaining(self):
        return len(self.cards)
    
    def draw(self) -> Card:
        if len(self.cards) < (self.num_decks * 52 * 1/4):
            self.build()
        return self.cards.pop()