from app import db, app

with app.app_context():
    db.create_all()
    print("✅ database.db 파일 및 테이블 생성 완료")