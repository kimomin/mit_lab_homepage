# create_db.py
from app import db
db.drop_all()
db.create_all()
print("DB 초기화 완료")