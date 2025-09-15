from flask import Flask, render_template, redirect, url_for, flash, session, request, abort
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from calendar import month_name
from flask_migrate import Migrate
from PIL import Image
from werkzeug.utils import secure_filename
import os, io, uuid
import shutil
import uuid
import secrets
import cloudinary
import cloudinary.uploader
import cloudinary.api


app = Flask(__name__)

csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')  
app.config['WTF_CSRF_ENABLED'] = True 

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

cloudinary.config(
  cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"),
  api_key = os.environ.get("CLOUDINARY_API_KEY"),
  api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)

app.config['MAX_CONTENT_LENGTH'] = 64*1024*1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}

BASE_UPLOAD_FOLDER = os.path.join(app.root_path, 'static/upload')
os.makedirs(BASE_UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def random_name(original: str) -> str:
    """충돌/추측 방지용 간단 랜덤 파일명."""
    safe = secure_filename(original)
    stem, ext = os.path.splitext(safe)
    return f"{uuid.uuid4().hex}{ext.lower()}"

def upload_to_cloudinary(file_storage, folder="gallery"):
    if not allowed_file(file_storage.filename):
        raise ValueError("Disallowed file type")

    ext = file_storage.filename.rsplit('.', 1)[-1].lower() #디버깅용

    result = cloudinary.uploader.upload(
        file_storage,
        folder=folder,
        resource_type="auto",  
        public_id=str(uuid.uuid4())  
    )
    return result["secure_url"], result["public_id"]

def save_file(file_storage, subdir) -> str:
    """
    파일 저장(이미지는 리사이즈/압축, pdf는 그대로).
    반환값: DB에 저장할 상대경로 'gallery/xxxx.ext'
    """
    filename = file_storage.filename or ''
    if not allowed_file(filename):
        raise ValueError('Disallowed file type')

    ext = filename.rsplit('.', 1)[-1].lower()
    out_dir = os.path.join(BASE_UPLOAD_FOLDER, subdir)
    os.makedirs(out_dir, exist_ok=True)
    out_name = random_name(filename)
    out_path = os.path.join(out_dir, out_name)

    # PDF는 그대로 저장
    if ext == 'pdf':
        file_storage.save(out_path)
        return f"{subdir}/{out_name}"

    # 이미지: Pillow로 열어서 너무 크면 리사이즈 후 저장
    img = Image.open(file_storage.stream)

    # 긴 변 기준 2000px로 제한 (원본이 더 작으면 그대로)
    max_side = 2000
    w, h = img.size
    scale = min(1.0, float(max_side) / max(w, h))
    if scale < 1.0:
        new_size = (int(w * scale), int(h * scale))
        img = img.resize(new_size, Image.LANCZOS)

    # 포맷 처리 (JPEG는 알파 없음)
    fmt = img.format or ext.upper()
    if fmt == 'JPG':
        fmt = 'JPEG'
    if fmt.upper() in ('JPEG', 'JPG') and img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # 저장 품질(간단): JPEG만 품질 85, 그 외는 기본 저장
    save_kwargs = {}
    if fmt.upper() in ('JPEG', 'JPG'):
        save_kwargs.update(dict(quality=85, optimize=True, progressive=True))
        fmt = 'JPEG'  # 명확히

    # 최종 확장자: 포맷에 맞춰 통일(선택)
    final_ext = 'jpg' if fmt.upper() == 'JPEG' else ext
    out_name = f"{os.path.splitext(out_name)[0]}.{final_ext}"
    out_path = os.path.join(out_dir, out_name)

    img.save(out_path, format=fmt.upper(), **save_kwargs)

    return f"{subdir}/{out_name}"

db = SQLAlchemy(app)

migrate = Migrate(app, db)

## csrf_token을 템플릿에서 사용할 수 있도록 설정
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)

## 상위 페이지들 라우트

@app.route('/vision')
def vision():
    return render_template('vision.html')

@app.route('/researchareas')
def researchareas():
    return render_template('researchareas.html')

@app.route('/professor')
def professor():
    return render_template('professor.html', body_class='professor-page')

@app.route('/current')
def current():
    members = [
        {
            "name": "Dong-Geun Lee",
            "role": "M.S. Student",
            "email": "qqwwas1234@gmail.com",
            "photo": "upload/members/이동근.png"
        },
        {
            "name": "Jin-Ho Lee",
            "role": "M.S. Student",
            "email": "jinho6606@naver.com",
            "photo": "upload/members/이진호.png"
        },
        {
            "name": "Min-Seo Song",
            "role": "Undergraduate Student",
            "email": "minseo7250@gmail.com",
            "photo": "upload/members/송민서.png"
        },
        {
            "name": "Gyu-Min Kim",
            "role": "Undergraduate Student",
            "email": "sprtms0814@gmail.com",
            "photo": "upload/members/김규민.png"
        },
        {
            "name": "Jiseon Park",
            "role": "Undergraduate Student",
            "email": "a01094670355@gmail.com",
            "photo": "upload/members/박지선.png"
        },
        {
            "name": "Seong-Hun Lee",
            "role": "Undergraduate Student",
            "email": "ss2396ss@gmail.com",
            "photo": "upload/members/이성훈.png"
        },
        {
            "name": "Chaehyeon Kim",
            "role": "Undergraduate Student",
            "email": "aulife4scarlette@gmail.com",
            "photo": "upload/members/김채현.png"
        }, 
        {
            "name": "Seoyoung Moon",
            "role": "Undergraduate Student",
            "email": "moon84615@gmail.com",
            "photo": "upload/members/문서영.png"
        }, 
        {
            "name": "Yoonseok Ju",
            "role": "Undergraduate Student",
            "email": "jys090799@gmail.com",
            "photo": "upload/members/주윤석.png"
        },
        {
            "name": "Joonhyeok Oh",
            "role": "Undergraduate Student",
            "email": "wnsgur011717@gmail.com",
            "photo": "upload/members/오준혁.png"
        }, 
        {
            "name": "Jonathan",
            "role": "Undergraduate Student",
            "email": "alpaomegastartend@gmail.com",
            "photo": "upload/members/조나단.png"
        }, 
        {
            "name": "Seongmin Kim",
            "role": "Undergraduate Student",
            "email": "ksiemomnign@gmail.com",
            "photo": "upload/members/김성민.png"
        },
        {
            "name": "Jun Jang",
            "role": "Undergraduate Student",
            "email": "jj010822@gmail.com",
            "photo": "upload/members/장준.png"
        },  
        {
            "name": "Deokhyeon Kim",
            "role": "Undergraduate Student",
            "email": "matho7830@gmail.com",
            "photo": "upload/members/김덕현.png"
        },
        {
            "name": "Subin Yoon",
            "role": "Undergraduate Student",
            "email": "operativeyoon@gmail.com",
            "photo": "upload/members/윤수빈.png"
        }           

    ]
    return render_template('current.html', members=members, body_class='current-page')

@app.route('/alumni')
def alumni():
    return render_template('alumni.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


###################################################################### paper 페이지

class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(500), nullable=False)
    journal = db.Column(db.String(200), nullable=False)
    month = db.Column(db.String(50))
    year = db.Column(db.Integer, nullable=False)
    link = db.Column(db.String(300), nullable=True)
    
@app.route('/paper')
def paper():
    selected_year = request.args.get('year', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    all_papers = Paper.query.all()
    
    MONTH_ORDER = {month: index for index, month in enumerate(month_name) if month}
    sorted_papers = sorted(
        all_papers,
        key=lambda p: (
            p.year,
            MONTH_ORDER.get(p.month, 0)  # 잘못된 month 값은 0 처리되어 맨 뒤로
        ),
        reverse=True
    )
    
    years = sorted(list({p.year for p in sorted_papers}), reverse=True)
    if selected_year != 'all':
        sorted_papers = [p for p in sorted_papers if str(p.year) == selected_year]
    
    total = len(sorted_papers)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_papers = sorted_papers[start:end]
    
    return render_template('paper.html',
                            papers=paginated_papers,
                            all_papers=sorted_papers if selected_year == 'all' else None,
                            selected_year=selected_year,
                            years=years,
                            page=page,
                            total=total,
                            per_page=per_page)

@app.route('/paper/create', methods=['GET', 'POST'])
@login_required
def paper_create_post():
    if not getattr(current_user, 'is_admin', False):
        abort(403)
        
    form = Paper()
    if request.method == 'POST':
        new_paper = Paper(
            title=request.form.get('title'),
            author=request.form.get('author'),
            journal=request.form.get('journal'),
            month=request.form.get('month'),
            year=request.form.get('year'),
            link=request.form.get('link')
        )
        db.session.add(new_paper)
        db.session.commit()
        return redirect(url_for('paper'))
    return render_template('paper_create_post.html', form=form)

@app.route('/paper/delete/<int:paper_id>', methods=['POST'])
@login_required
def paper_delete_post(paper_id):
    if not getattr(current_user, 'is_admin', False):
        abort(403)

    paper = Paper.query.get_or_404(paper_id)
    db.session.delete(paper)
    db.session.commit()
    flash('Paper deleted successfully.', 'success')
    return redirect(url_for('paper', year=request.args.get('year', 'all')))
######################################################################


###################################################################### conferences 페이지

class Conference(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    conference = db.Column(db.String(200), nullable=False)
    month = db.Column(db.String(50))
    year = db.Column(db.Integer, nullable=False)
    
@app.route('/conference')
def conference():
    selected_year = request.args.get('year', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = 15
    
    all_conferences = Conference.query.all()
    
    MONTH_ORDER = {month: index for index, month in enumerate(month_name) if month}
    sorted_conferences = sorted(
        all_conferences,
        key=lambda p: (
            p.year,
            MONTH_ORDER.get(p.month, 0) 
        ),
        reverse=True
    )
    
    years = sorted(list({p.year for p in sorted_conferences}), reverse=True)
    if selected_year != 'all':
        sorted_conferences = [p for p in sorted_conferences if str(p.year) == selected_year]
    
    total = len(sorted_conferences)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_conferences = sorted_conferences[start:end]
    
    return render_template('conference.html',
                            conferences=paginated_conferences,
                            all_conferences=sorted_conferences if selected_year == 'all' else None,
                            selected_year=selected_year,
                            years=years,
                            page=page,
                            total=total,
                            per_page=per_page)

@app.route('/conference/create', methods=['GET', 'POST'])
@login_required
def conference_create_post():
    if not getattr(current_user, 'is_admin', False):
        abort(403)

    form = Conference()
    if request.method == 'POST':
        new_conference = Conference(
            title=request.form.get('title'),
            author=request.form.get('author'),
            conference=request.form.get('conference'),
            month=request.form.get('month'),
            year=request.form.get('year')
        )
        db.session.add(new_conference)
        db.session.commit()
        return redirect(url_for('conference'))
    return render_template('conference_create_post.html', form=form)

@app.route('/conference/delete/<int:conference_id>', methods=['POST'])
@login_required
def conference_delete_post(conference_id):
    if not getattr(current_user, 'is_admin', False):
        abort(403)

    conference = Conference.query.get_or_404(conference_id)
    db.session.delete(conference)
    db.session.commit()
    flash('Paper deleted successfully.', 'success')
    return redirect(url_for('conference', year=request.args.get('year', 'all')))
######################################################################


###################################################################### 사진 갤러리 페이지
## 사진 갤러리용 데이터베이스 모델
class GalleryPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    thumbnail_id = db.Column(db.Integer, db.ForeignKey('gallery_image.id'), nullable=True)
    
    thumbnail = db.relationship(
        'GalleryImage', 
        foreign_keys=[thumbnail_id],
        post_update=True)
    images = db.relationship(
        'GalleryImage', 
        backref='post', lazy=True, 
        cascade="all, delete-orphan",
        foreign_keys='GalleryImage.post_id')

class GalleryImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    public_id = db.Column(db.String(500), nullable=True)
    description = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('gallery_post.id'), nullable=True)
    order = db.Column(db.Integer, default=0)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
## 갤러리 라우트
@app.route('/gallery')
def gallery():
    posts = GalleryPost.query.order_by(GalleryPost.date.desc()).all()
    return render_template('gallery.html', posts=posts, body_class='gallery-page')

@app.route('/gallery/<int:post_id>')
def gallery_view_post(post_id):
    post = GalleryPost.query.get_or_404(post_id)
    images = GalleryImage.query.filter_by(post_id=post.id).order_by(GalleryImage.order.asc()).all()
    return render_template('gallery_view_post.html', post=post, images=images)

## 업로드 라우트
@app.route('/gallery/create', methods=['GET', 'POST'])
@login_required
def gallery_create_post():
    if not getattr(current_user, 'is_admin', False):
        abort(403)

    if request.method == 'POST':
        title = request.form.get('title')
        date_str = request.form.get('date')  
        date = datetime.strptime(date_str, "%Y-%m-%d") 
        
        urls = request.form.getlist('images[]')
        descriptions = request.form.getlist('descriptions[]')
        thumbnail_index = int(request.form.get('thumbnail_index', 0))

        post = GalleryPost(title=title, date=date)
        db.session.add(post)
        db.session.commit()  # post.id 필요하므로 먼저 커밋

        for idx, url in enumerate(urls):
                                 
                image = GalleryImage(
                    filename=url,
                    public_id=None,
                    description=descriptions[idx] if idx < len(descriptions) else '',
                    post_id=post.id
                    )
                db.session.add(image)
                db.session.flush()  
                if idx == thumbnail_index:
                    post.thumbnail = image
        db.session.commit()
        flash("Gallery post created.")
        return redirect(url_for('gallery'))

    return render_template('gallery_create_post.html')  # 게시글 생성 폼

## 게시물 삭제 라우트
@app.route('/gallery/delete_post/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = GalleryPost.query.get_or_404(post_id)
    
    if not getattr(current_user, 'is_admin', False):
        abort(403)

    # 포함된 이미지 모두 가져오기
    images = post.images

    # DB에서 이미지 → 게시물 순서로 삭제
    for image in images:
        db.session.delete(image)
    db.session.delete(post)
    db.session.commit()

    flash('Gallery post deleted.')
    return redirect(url_for('gallery'))

## 게시물 수정 라우트
@app.route('/gallery/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def gallery_edit_post(post_id):
    post = GalleryPost.query.get_or_404(post_id)
    
    if not getattr(current_user, 'is_admin', False):
        abort(403)
    
    images = GalleryImage.query.filter_by(post_id=post.id).order_by(GalleryImage.order.asc()).all()

    if request.method == 'POST':
        post.title = request.form.get('title')
        date_str = request.form.get('date')
        post.date = datetime.strptime(date_str, "%Y-%m-%d")
        
        # 수정된 기존 이미지 정보 반영
        image_ids = request.form.getlist("image_ids")
        for image_id in image_ids:
            image = GalleryImage.query.get(int(image_id))
            desc = request.form.get(f'descriptions_{image_id}', '')
            image.description = desc
            
        db.session.commit()

        urls = request.form.getlist('images[]')
        descriptions = request.form.getlist('descriptions[]')
        thumbnail_index = request.form.get('thumbnail_index')
        
        new_uploaded_images = []
        
        for idx, url in enumerate(urls):
            if url.strip():
                image = GalleryImage(
                    filename=url,
                    public_id=None,
                    description=descriptions[idx] if idx < len(descriptions) else '',
                    post_id=post.id
                )
                db.session.add(image)
                db.session.flush()
                new_uploaded_images.append((f'new_{idx}', image))
        db.session.commit()
        
        if thumbnail_index:
            if thumbnail_index.startswith('new_'):
                for new_key, img_obj in new_uploaded_images:
                    if new_key == thumbnail_index:
                        post.thumbnail = img_obj
                        break
            else:
                try:
                    thumbnail_id = int(thumbnail_index)
                    existing = GalleryImage.query.get(thumbnail_id)
                    if existing and existing.post_id == post.id:
                        post.thumbnail = existing
                except ValueError:
                    pass
        db.session.commit()
        flash('Post updated successfully.')
        return redirect(url_for('gallery_view_post', post_id=post.id))

    return render_template('gallery_edit_post.html', post=post, images=images)


## 이미지 삭제 라우트
@app.route('/gallery/<int:post_id>/delete_image/<int:image_id>', methods=['POST'])
@login_required
def delete_image_from_post(post_id, image_id):
    image = GalleryImage.query.get_or_404(image_id)
    
    if not getattr(current_user, 'is_admin', False):
        abort(403)

    # DB 삭제
    db.session.delete(image)
    db.session.commit()
    return '', 204
######################################################################


###################################################################### 공지 페이지
class NoticeAttachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    notice_id = db.Column(db.Integer, db.ForeignKey('notice.id'), nullable=False)

class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    view_count = db.Column(db.Integer, default=0)

    attachments = db.relationship('NoticeAttachment', backref='notice', cascade='all, delete-orphan')
      
@app.route('/notice')
def notice():
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    return render_template('notice.html', notices=notices)

@app.route('/notice/<int:notice_id>')
def notice_view_post(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    notice.view_count += 1
    db.session.commit()
    return render_template('notice_view_post.html', notice=notice)


@app.route('/notice/create', methods=['GET', 'POST'])
@login_required
def notice_create_post():
    if not getattr(current_user, 'is_admin', False):
        abort(403)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        files = request.files.getlist('files')
        
        # 공지 생성
        notice = Notice(title=title, content=content)
        db.session.add(notice)
        db.session.commit() 
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                subdir = f'notices/notice_{notice.id}'
                out_dir = os.path.join(BASE_UPLOAD_FOLDER, subdir)
                os.makedirs(out_dir, exist_ok=True)

                filepath = os.path.join(out_dir, filename)
                file.save(filepath)

                # DB에는 상대 경로만 저장
                rel_path = f'{subdir}/{filename}'
                attachment = NoticeAttachment(filename=rel_path, notice_id=notice.id)
            db.session.add(attachment)

        db.session.commit()
        flash('공지사항이 등록되었습니다.')
        return redirect(url_for('notice'))

    return render_template('notice_create_post.html', notice=None)


@app.route('/notice/edit/<int:notice_id>', methods=['GET', 'POST'])
@login_required
def notice_edit_post(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    
    if not getattr(current_user, 'is_admin', False):
        abort(403)


    if request.method == 'POST':
        notice.title = request.form['title']
        notice.content = request.form['content']
        
        files = request.files.getlist('files')
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                subdir = f'notices/notice_{notice.id}'
                out_dir = os.path.join(BASE_UPLOAD_FOLDER, subdir)
                os.makedirs(out_dir, exist_ok=True)

                filepath = os.path.join(out_dir, filename)
                file.save(filepath)

                # DB에는 상대 경로만 저장
                rel_path = f'{subdir}/{filename}'
                attachment = NoticeAttachment(filename=rel_path, notice_id=notice.id)
                db.session.add(attachment)

        delete_ids = request.form.getlist('delete_attachments')
        for att_id in delete_ids:
            attachment = NoticeAttachment.query.get(int(att_id))
            if attachment:
                filepath = os.path.join(BASE_UPLOAD_FOLDER, attachment.filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                db.session.delete(attachment)

        db.session.commit()
        flash('수정되었습니다.')
        return redirect(url_for('notice_view_post', notice_id=notice.id))

    return render_template('notice_edit_post.html', notice=notice)


@app.route('/notice/delete/<int:notice_id>', methods=['POST'])
@login_required
def delete_notice(notice_id):
    if not getattr(current_user, 'is_admin', False):
        abort(403)

    notice = Notice.query.get_or_404(notice_id)
    
    for att in list(notice.attachments):  # relationship 있다고 가정
        abs_path = os.path.join(BASE_UPLOAD_FOLDER, att.filename)
        if os.path.exists(abs_path):
            os.remove(abs_path)
        db.session.delete(att)
        
    db.session.delete(notice)
    db.session.commit()
    flash('삭제되었습니다.')
    return redirect(url_for('notice'))
######################################################################


###################################################################### 홈화면
@app.route('/')
def home():
    MONTH_ORDER = {month: index for index, month in enumerate(month_name) if month}
    all_papers = Paper.query.all()
    sorted_papers = sorted(
        all_papers,
        key=lambda p: (p.year, MONTH_ORDER.get(p.month, 0)),
        reverse=True
    )
    latest_papers = sorted_papers[:10]

    return render_template("index.html", latest_papers=latest_papers)

###################################################################### 회원가입, 로그인, 로그아웃
## Flask-Login 초기화
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


## 사용자 모델 정의하기
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(500), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return '<User {self.username}>'
    
with app.app_context():
    db.create_all
    

## 사용자 로더 함수 정의하기
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/protected') # 이 단락은 필수 아님. 디버깅용
@login_required
def protected():
  return f'Logged in as {current_user.username}'


## 회원가입 라우트
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        pw = request.form['password']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('이미 존재하는 아이디입니다.')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(pw)

        user = User(username=username, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html', body_class="container mt-5")


## 로그인 라우트
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pw = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, pw):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('Invalid credentials')
    return render_template('login.html', body_class="login-page")


## 로그아웃 라우트
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
######################################################################


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
