from pydantic import BaseModel, EmailStr


class AuthSchema(BaseModel):
    email: EmailStr


class VerificationCodeSchema(BaseModel):
    email: EmailStr
    code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class LogoutResponse(BaseModel):
    msg: str
