from pydantic import BaseModel


class User(BaseModel):
    id: str
    email: str
    name: str | None = None
    picture: str | None = None
    role: str
    createdAt: str | None = None
    updatedAt: str | None = None


class GoogleLoginRequest(BaseModel):
    id_token: str


class LoginResponseData(BaseModel):
    token: str
    user: User

