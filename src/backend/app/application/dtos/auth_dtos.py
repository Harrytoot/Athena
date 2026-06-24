from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    display_name: str = Field(default="", alias="displayName")

    model_config = {"populate_by_name": True}


class TokenResponse(BaseModel):
    access_token: str = Field(alias="accessToken")
    token_type: str = Field(default="bearer", alias="tokenType")
    user_id: str = Field(alias="userId")
    username: str
    display_name: str = Field(alias="displayName")

    model_config = {"populate_by_name": True}


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    display_name: str = Field(alias="displayName")
    is_active: bool = Field(alias="isActive")

    model_config = {"populate_by_name": True}
