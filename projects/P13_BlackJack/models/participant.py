from projects.P13_BlackJack.models.hand import Hand

class Participant:
    """Shared behavior between Player and Dealer."""
    def __init__(self, name: str):
        self.name = name
        self.hand = Hand()

    def reset_hand(self):
        self.hand = Hand()
        
class Player(Participant):
    
    def __init__(self, name: str, chips: int = 100):
        super().__init__(name)
        self.chips = chips
        self.hands: list[Hand] = [Hand()]
        self.chip_history: list[int] = [chips]
    
    def place_bet(self, hand: Hand, amount: int):
        if amount > self.chips:
            raise ValueError("Not enough chips")
        hand.bet = amount
        self.chips -= amount
    
    def win_bet(self, hand: Hand, multiplier: float = 1.0):
        self.chips += hand.bet + (hand.bet * multiplier)
        hand.bet = 0
        
    def push_bet(self, hand: Hand):
        self.chips += hand.bet
        hand.bet = 0
        
        
class Dealer(Participant):
    
    def __init__(self):
        super().__init__("Dealer")
        
    def should_hit(self, hit_on_soft_17 : bool= True) -> bool:
        value= self.hand.value()
        if value < 17:
            return True
        if value == 17 and hit_on_soft_17 and self.is_soft():
            return True
        return False
        
    def is_soft(self) -> bool:
        total = sum(c.value for c in self.hand.cards)
        aces = sum(1 for c in self.hand.cards if c.rank == "A")
        while total > 21 and aces:
            total -= 10
            aces -= 1
        return aces > 0