import datetime
from pydantic import EmailStr,BaseModel,Field
from typing import Optional

#1.Request body for User Registration
class UserRegisterRequest(BaseModel):
  email:EmailStr=Field(...,example='developer@example.com',description='user email address')
  password:str=Field(...,example='secure password',description='user password')
  full_name:Optional[str]=Field(None,example='durgaprasad',description='users full name')

#2.Request Body for User Login
class UserLoginRequest(BaseModel):
    email: EmailStr = Field(..., example="developer@company.com")
    password: str = Field(..., example="SecurePassword123!")

# 3.Response Body containing the JWT Token
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# 4.User Profile Response
class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime.datetime
    class Config:
        from_attributes = True      