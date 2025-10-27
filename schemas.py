from pydantic import BaseModel

class DocumentBase(BaseModel):
    description: str | None = None

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    filename: str
    path: str

    class Config:
        orm_mode = True
