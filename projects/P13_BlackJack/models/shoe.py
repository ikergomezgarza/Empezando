from .card import Card, Suit
import random
from collections import Counter
import statistics

class Shoe:
    
    RANKS = [ "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
    
    def __init__(self, num_decks: int = 1):
        self.num_decks = num_decks
        self.cards = []
        self.count = 0
        self.true_count = 0
        self.count_shoe = []
        self.count_log = []
        self.build()
        
    def build(self):
        if self.count_shoe:
            self.update_count_log()
        self.cards= [
            Card(rank, suit)
            for _ in range(self.num_decks)
            for suit in Suit
            for rank in self.RANKS
              
        ]
        random.shuffle(self.cards)
        self.count = 0
        self.true_count = 0 
        self.count_shoe = []
        
        
    def cards_remaining(self):
        return len(self.cards)
    
    def draw(self) -> Card:
        
        if self.cards[-1].rank in ("2", "3", "4", "5", "6"):
                    self.count += 1
        elif self.cards[-1].rank in ("10", "J", "Q", "K", "A"):
            self.count -= 1
        else:
            pass
        
        decks_remaining = (len(self.cards)) / 52
        self.true_count = self.count / decks_remaining
        self.count_shoe.append(self.true_count)
            
        return self.cards.pop()
    
    def can_rebuild_deck(self):
        return len(self.cards) < (self.num_decks * 52 * 1/4)
    
    def update_count_log(self, ignore: set = {-1, 0, 1}) -> float:

        filtered = [c for c in self.count_shoe if c not in ignore]
        mode = Counter(filtered).most_common(1)[0][0] if filtered else None

        resume = {"minimum" : min(self.count_shoe),
                  "maximun" : max(self.count_shoe),
                  "avg"     : statistics.mean(self.count_shoe),
                  "mode_excl_neutral": mode,}
        
        self.count_log.append(resume)
    
    
        
  
    
