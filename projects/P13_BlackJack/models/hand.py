from projects.P13_BlackJack.models.card import Card

class Hand:
    
    def __init__(self, from_split: bool = False, bet: int = 0):
        self.cards: list[Card] = []
        self.from_split = from_split
        self.bet = bet
        self.doubled = False
        self.resolved = False
        
    def add(self, card: Card):
        self.cards.append(card)
        
    def value(self) -> int:
        total = sum(c.value for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return total
    
    def is_bust(self) -> bool:
        return self.value() > 21
    
    def is_blackjack(self) -> bool:
        return (
            self.value() == 21 
            and len(self.cards) == 2 
            and not self.from_split
        )
    
    def is_soft(self) -> bool:
        total = sum(c.value for c in self.cards)
        aces = sum(1 for c in self.cards if c.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return aces > 0
    
    def can_split(self) -> bool:
        return (
            len(self.cards) == 2
            and self.cards[0].rank == self.cards[1].rank
        )
    
    def can_double(self) -> bool:
        return len(self.cards) == 2 and not self.doubled