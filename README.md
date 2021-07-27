

To run this application we have to create database on your localhost
datebase name = fastapi
table name = user

    id = fields.IntField(pk=True)
    username = fields.CharField(50, unique=True)
    password_hash = fields.CharField(128)
    phone_no = fields.data.CharField(100)
    email = fields.CharField(128)
    image_url = fields.CharField(128)
    keywords = fields.CharField(500)

download pakages using 
 
 pip install -r requirements.txt
 
 create a folder templates and add all html files to it
