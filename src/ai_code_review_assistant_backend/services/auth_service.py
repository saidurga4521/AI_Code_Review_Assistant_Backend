import datetime
from typing import Optional,Dict,Any
import bcrypt
import jwt

from ai_code_review_assistant_backend.config import settings

def hash_password(password:str)->str:
  """
  Hashes a plain-text password using bcrypt
  """
  salt=bcrypt.gensalt()
  hash_password=bcrypt.hashpw(password.encode('utf-8'),salt)
  return hash_password.decode('utf-8')

def verify_password(plain_password:str,hashed_password:str)->bool:
  """
  verify plain text password against hashed password
  """
  return bcrypt.checkpw(
    plain_password.encode('utf-8'),
    hashed_password.encode('utf-8')
  )

def create_access_token(data:Dict[str,Any],expires_delta:Optional[datetime.timedelta]=None)->str:
  """
  creates a signed JWT token
  """
  to_encode=data.copy()
  now=datetime.datetime.now(datetime.timezone.utc)
  delta=expires_delta or datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE)
  expire=now+delta

  #add the expire in payload
  to_encode.update({'exp':expire})

  encode_jwt=jwt.encode(to_encode,settings.JWT_SECRET_KEY,algorithm=settings.ALGORITHM)
  return encode_jwt

def decode_access_token(token:str)->Dict[str,Any]:
  """
  Decodes and validates a JWT Token.Retruns a payload or None
  if invalid/expired
  """
  try:
    payload=jwt.decode(token,settings.JWT_SECRET_KEY,algorithms=[settings.ALGORITHM])
    return payload
  except jwt.PyJWTError:
    return None

  

