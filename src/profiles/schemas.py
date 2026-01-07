from pydantic import BaseModel, Field


class ProfileSchema(BaseModel):
    user_id: int
    first_name: str | None = Field(max_length=100, min_length=3)
    last_name: str | None = Field(max_length=100, min_length=3)
    bio: str | None

    class Config:
        from_attributes = True
