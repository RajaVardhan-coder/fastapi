import jwt, random, shutil
import regex as re 
from re import search
from fastapi import FastAPI, File, UploadFile
from typing import List
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, Request, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm 
from passlib.hash import bcrypt 
from tortoise import fields 
from tortoise.contrib.fastapi import register_tortoise 
from tortoise.contrib.pydantic import pydantic_model_creator 
from tortoise.models import Model 
import cloudinary
import cloudinary.uploader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates


app = FastAPI()
origins = ["*"]


templates = Jinja2Templates(directory="templates")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET = 'myjwtsecret'

class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(50, unique=True)
    password_hash = fields.CharField(128)
    phone_no = fields.data.CharField(100)
    email = fields.CharField(128)
    image_url = fields.CharField(128)
    keywords = fields.CharField(500)

    def verify_password(self, password):
        return bcrypt.verify(password, self.password_hash)
    
cloudinary.config(
    cloud_name= "dhdqtjncf",
    api_key= "994569699891913",
    api_secret= "LzLmHwlL_AGnPObfy5wm2jD4djM"
)


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
async def generate_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid username or password'
        )
    user_obj = await User_Pydantic.from_tortoise_orm(user)
    token = jwt.encode(user_obj.dict(), JWT_SECRET)
    return templates.TemplateResponse('layout.html', context={'request': request, 'access_token' : token, 'token_type' : 'bearer'})


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


@app.get('/register')
def Insert_User_Get(request: Request):  
    return templates.TemplateResponse('register.html', context={'request': request})


@app.post('/reg', response_model=User_Pydantic)
async def create_user(request: Request, Username : str = Form(...), Password : str = Form(...), Phone_no : str = Form(...), Email : str = Form(...), Keyword : str = Form(...)):
    user_obj = User(username=Username, password_hash=bcrypt.hash(Password), phone_no = Phone_no, email = Email, image_url = "", keywords = Keyword)
    email_verification = is_valid_mail(Email)
    phone_varification = is_valid_phone(Phone_no)
    if(email_verification != True or phone_varification != True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Invalid Email or Phone number'
        )
    await user_obj.save()
    await User_Pydantic.from_tortoise_orm(user_obj)
    return templates.TemplateResponse('success.html', context={'request': request})



@app.get('/login')
async def get_user_profile(request: Request):
    return templates.TemplateResponse('login.html', context={'request': request})



@app.get('/layout')
async def get_user_profile(request: Request):
    return templates.TemplateResponse('layout.html', context={'request': request})



@app.get('/users', response_model=List[User_Pydantic])
async def get_users(user: User_Pydantic = Depends(get_current_user)):
    print(user)
    return await User_Pydantic.from_queryset(User.all())


@app.get('/users/{s}', response_model=List[User_Pydantic])
async def get_user_keyword(s: str, user: User_Pydantic = Depends(get_current_user)):
    Listofusers = await User_Pydantic.from_queryset(User.all())

    listofusers = []
    listofusers = Listofusers 
    Listofreq = []

    s1 = s.lower()
    for i in listofusers:
        s2 = i.keywords.lower()
        if set(s1)==set(s2):
            Listofreq.append(i)
    return  Listofreq

@app.get('/user/{id}', response_model=User_Pydantic)
async def get_user(id : int, user: User_Pydantic = Depends(get_current_user)):
    return await User_Pydantic.from_queryset_single(User.get(id=id))


@app.delete('/users/profile', response_model=User_Pydantic)
async def delete_user(user: User_Pydantic = Depends(get_current_user)):
    deleted_count = await User.filter(id=user.id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"User {user} not found")


@app.patch('/users/profile', response_model=User_Pydantic)
async def put_user(file: Optional[UploadFile] = File(None), Phone_no : Optional[str] = None , Email : Optional[str] = None , Keyword : Optional[str] = None ,user: User_Pydantic = Depends(get_current_user)):
    if file:
        result = cloudinary.uploader.upload(file.file)
        url = result.get("url")
    else:
        url = ""
    if Email and Phone_no and Keyword:
        email_verification = is_valid_mail(Email)
        phone_varification = is_valid_phone(Phone_no)
        if(email_verification != True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail='Invalid Email'
            )
        if(phone_varification != True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail='Invalid Phone number'
            )
        keyword = user.keywords + "     " + Keyword
        await User.filter(id=user.id).update(phone_no = Phone_no, email = Email, image_url = url, Keyword=keywords)
    elif Email:
        email_verification = is_valid_mail(Email)
        if(email_verification != True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail='Invalid Email'
            )
        await User.filter(id=user.id).update(email = Email, image_url = url)
    elif Phone_no:
        phone_varification = is_valid_phone(Phone_no)
        if(phone_varification != True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail='Invalid Phone number'
            )
        await User.filter(id=user.id).update(phone_no = Phone_no, image_url = url)
    elif Keyword:
        keyword = user.keywords + "     " + Keyword
        await User.filter(id=user.id).update(keywords=keyword, image_url = url)
    else:
        await User.filter(id=user.id).update(image_url = url)
    return await User_Pydantic.from_queryset_single(User.get(id=user.id))



register_tortoise(
    app, 
    db_url='mysql://root@localhost:3306/fastapi',
    modules={'models': ['main']},
    generate_schemas=True,
    add_exception_handlers=True
    )