from pydantic import BaseModel


class RankedPromo(BaseModel):
    """Represents a promo with an affinity score for a given user"""

    item_id: str
    score: float
