

To run this application we have to create database on your localhost

    id = fields.IntField(pk=True)
    username = fields.CharField(50, unique=True)
    password_hash = fields.CharField(128)
    phone_no = fields.data.CharField(100)
    email = fields.CharField(128)

download pakages using 
 
 pip install -r requirements.txt
