from pydantic import BaseModel


class AISuggestionOut(BaseModel):
    response: str
    based_on_similar: list[int]


class SimilarTicketOut(BaseModel):
    ticket_id: int
    subject: str
    status: str
    similarity: float


class SimilarTicketsOut(BaseModel):
    items: list[SimilarTicketOut]
