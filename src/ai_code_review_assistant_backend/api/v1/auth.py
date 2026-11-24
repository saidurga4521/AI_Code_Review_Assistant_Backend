from fastapi import APIRouter,HTTPException,status,Depends
from fastapi.security import OAuth2PasswordBearer
from ai_code_review_assistant_backend.config import settings
from typing import Optional
from sqlalchemy.orm import Session
from ai_code_review_assistant_backend.db.session import get_db
from ai_code_review_assistant_backend.schemas.auth import UserResponse,UserRegisterRequest,UserLoginRequest,TokenResponse
from ai_code_review_assistant_backend.db.models import User
from ai_code_review_assistant_backend.services.auth_service import decode_access_token,hash_password,verify_password,create_access_token


router=APIRouter(
  prefix='/auth',
  tags=['Authentication']
)

#schema for extracting the 'Bearer <token>' header
oauth2_schema =OAuth2PasswordBearer(
  tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_current_user(
    token:str=Depends(oauth2_schema),
    db:Session=Depends(get_db)
) ->User:
  
  credentials_exception=HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='could not validate credentials',
    headers={'WWW-Authenticate':'Bearer'}
  )

  payload=decode_access_token(token)
  if payload is None:
    raise credentials_exception

  user_id=payload.get('sub')
  if user_id is None:
    raise credentials_exception

  user=db.query(User).filter(User.id == int(user_id)).first()

  if user is None:
    raise credentials_exception
  if not user.is_active:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='Inactive user account'
    )
  return user

#1.POST auth/register ->Register the user
@router.post('/register',response_model=UserResponse,status_code=status.HTTP_201_CREATED)
def register_user(request:UserRegisterRequest,db:Session=Depends(get_db)):
  """
  Register a new user account
  """
  print('enterred...')
  existing_user=db.query(User).filter(User.email == request.email).first()
  if existing_user:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='user already exists'
    )
  try:
    new_user=User(
      email=request.email,
      hashed_password=hash_password(request.password),
      full_name=request.full_name,
      is_active=True,
      is_superuser=False
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
  
  except Exception as e:
    db.rollback()
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail=f"Database error during regestration:{str(e)}"
    ) 

#2.POST /auth/login ->Authentication
@router.post('/login',response_model=TokenResponse)
def login_user(request:UserLoginRequest,db:Session =Depends(get_db)):
  """
  Authenticates with email and password
  """
  user=db.query(User).filter(User.email == request.email).first()
  if not user or not verify_password(request.password,user.hashed_password):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail='Invalid email or password'
    )

  if not user.is_active:
     raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="User account is deactivated."
      )

  # create the new access token
  token=create_access_token(data={'sub':str(user.id),'email':user.email})
  return {
    'status':True,
    'access_token':token,
    'token_type':'bearer'
  }

#3.GET /auth/me ->Protected route
@router.get('/me',response_model=UserResponse)
def get_currrent_user_profile(current_user:User=Depends(get_current_user)):
  """
  Get profile information of the currently authenticated user.
  Requires Bearer JWT token
  """
  return current_user
  

