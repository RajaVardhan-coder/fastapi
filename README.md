# fastapi
fastapi
#fastapi

To run this application we have to create database on your localhost

    id = fields.IntField(pk=True)
    username = fields.CharField(50, unique=True)
    password_hash = fields.CharField(128)
    phone_no = fields.data.CharField(100)
    email = fields.CharField(128)

Your can puerform CRUD operations using fastapi
