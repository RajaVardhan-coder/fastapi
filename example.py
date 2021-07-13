import jwt, random
import regex as re 
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status 
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from passlib.hash import bcrypt 
from tortoise import fields 
from tortoise.contrib.fastapi import register_tortoise 
from tortoise.contrib.pydantic import pydantic_model_creator 
from tortoise.models import Model 

app = FastAPI()

JWT_SECRET = 'myjwtsecret'

class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(50, unique=True)
    password_hash = fields.CharField(128)
    phone_no = fields.data.CharField(100)
    email = fields.CharField(128)

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)
    
    
def is_valid_mail(email):
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if(re.search(regex ,email)):
        return True
    else:
        return False

def is_valid_phone(phone):
    regex = "^[0-9]{10}$"
    if(re.search(regex ,phone)):
        return True
    else:
        return False

User_Pydantic = pydantic_model_creator(User, name='User')
UserIn_Pydantic = pydantic_model_creator(User, name='UserIn', exclude_readonly=True)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

async def authenticate_user(username: str, password: str):
    user = await User.get(username=username)
    if not user:
        return False 
    if not user.verify_password(password):
        return False
    return user 


@app.post('/token')
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid username or password'
        )

    user_obj = await User_Pydantic.from_tortoise_orm(user)

    token = jwt.encode(user_obj.dict(), JWT_SECRET)

    return {'access_token' : token, 'token_type' : 'bearer'}


async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        user = await User.get(id=payload.get('id'))
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid username or password'
        )

    return await User_Pydantic.from_tortoise_orm(user)


@app.post('/register', response_model=User_Pydantic)
async def create_user(Username : str, Password : str, Phone_no : str , Email : str):
    user_obj = User(username=Username, password_hash=bcrypt.hash(Password), phone_no = Phone_no, email = Email)
    email_verification = is_valid_mail(Email)
    phone_varification = is_valid_phone(Phone_no)
    if(email_verification != True or phone_varification != True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid Email or Phone number'
        )
    await user_obj.save()
    return await User_Pydantic.from_tortoise_orm(user_obj)



@app.get('/users/id', response_model=User_Pydantic)
async def get_user(user: User_Pydantic = Depends(get_current_user)):
    return await User_Pydantic.from_queryset_single(User.get(id=user.id))


@app.patch('/users/id', response_model=User_Pydantic)
async def put_user(Phone_no : Optional[str] = None , Email : Optional[str] = None , user: User_Pydantic = Depends(get_current_user)):
    email_verification = phone_varification = True
    if Email:
        email_verification = is_valid_mail(Email)
        if(email_verification != True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail='Invalid Email'
            )
        await User.filter(id=user.id).update(email = Email)
        return await User_Pydantic.from_queryset_single(User.get(id=user.id))
    if Phone_no:
        phone_varification = is_valid_phone(Phone_no)
        if(phone_varification != True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail='Invalid Phone number'
            )
        await User.filter(id=user.id).update(phone_no = Phone_no)
        return await User_Pydantic.from_queryset_single(User.get(id=user.id))

    return await User_Pydantic.from_queryset_single(User.get(id=user.id))


@app.delete('/users/id', response_model=User_Pydantic)
async def delete_user(user: User_Pydantic = Depends(get_current_user)):
    deleted_count = await User.filter(id=user.id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"User {user} not found")


register_tortoise(
    app, 
    db_url='mysql://root@localhost:3306/fastapi',
    modules={'models': ['example']},
    generate_schemas=True,
    add_exception_handlers=True
    )