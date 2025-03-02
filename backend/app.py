import os
from flask import Flask, render_template, flash, redirect, url_for, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy.orm import DeclarativeBase
import logging
from logging.handlers import RotatingFileHandler
import traceback

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info('Application startup')

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///notehive.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "uploads")

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Import routes after app initialization to avoid circular imports
from models import User, Note, Department
from forms import LoginForm, RegistrationForm, UploadForm

@app.errorhandler(Exception)
def handle_error(error):
    logger.error(f'Unhandled error: {error}')
    logger.error(traceback.format_exc())
    return 'Internal Server Error', 500

@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception as e:
        logger.error(f'Error loading user {user_id}: {e}')
        return None

@app.route('/')
def index():
    try:
        departments = Department.query.all()
        recent_notes = Note.query.order_by(Note.upload_date.desc()).limit(10).all()
        return render_template('dashboard.html', departments=departments, recent_notes=recent_notes)
    except Exception as e:
        logger.error(f'Error in index route: {e}')
        flash('Error loading dashboard')
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()
            logger.info(f'Login attempt for email: {form.email.data}')
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                logger.info(f'Successful login for user: {user.id}')
                return redirect(url_for('index'))
            logger.warning(f'Failed login attempt for email: {form.email.data}')
            flash('Invalid email or password')
        return render_template('login.html', form=form)
    except Exception as e:
        logger.error(f'Error in login route: {e}')
        flash('Error processing login')
        return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    try:
        if current_user.is_authenticated:
            return redirect(url_for('index'))

        form = RegistrationForm()
        if form.validate_on_submit():
            logger.info(f'Registration attempt for email: {form.email.data}')
            user = User(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data
            )
            user.password_hash = generate_password_hash(form.password.data)
            db.session.add(user)
            db.session.commit()
            logger.info(f'Successfully registered user: {user.id}')
            flash('Registration successful!')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)
    except Exception as e:
        logger.error(f'Error in register route: {e}')
        flash('Error processing registration')
        return render_template('register.html', form=form)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    try:
        form = UploadForm()
        form.department.choices = [(d.id, d.name) for d in Department.query.all()]

        if form.validate_on_submit():
            file = form.file.data
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                logger.info(f'File uploaded: {filename} by user {current_user.id}')

                note = Note(
                    title=form.title.data,
                    subject=form.subject.data,
                    description=form.description.data,
                    filename=filename,
                    department_id=form.department.data,
                    user_id=current_user.id
                )
                db.session.add(note)
                db.session.commit()
                logger.info(f'Note created: {note.id}')
                flash('File uploaded successfully!')
                return redirect(url_for('index'))
        return render_template('upload.html', form=form)
    except Exception as e:
        logger.error(f'Error in upload route: {e}')
        flash('Error processing file upload')
        return render_template('upload.html', form=form)

@app.route('/search')
def search():
    try:
        query = request.args.get('q', '')
        dept_id = request.args.get('dept')
        logger.info(f'Search request - query: {query}, dept: {dept_id}')

        if query or dept_id:
            notes_query = Note.query
            if query:
                notes_query = notes_query.filter(
                    Note.title.ilike(f'%{query}%') | 
                    Note.description.ilike(f'%{query}%')
                )
            if dept_id:
                notes_query = notes_query.filter_by(department_id=dept_id)
            notes = notes_query.all()
        else:
            notes = []
        return render_template('search.html', notes=notes, query=query)
    except Exception as e:
        logger.error(f'Error in search route: {e}')
        flash('Error processing search')
        return render_template('search.html', notes=[], query=query)

@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        logger.info('User logged out successfully')
        flash('You have been logged out successfully.')
        return redirect(url_for('login'))
    except Exception as e:
        logger.error(f'Error in logout route: {e}')
        return redirect(url_for('index'))

@app.route('/download_note/<int:note_id>')
@login_required
def download_note(note_id):
    try:
        note = Note.query.get_or_404(note_id)
        logger.info(f'Note download request: {note_id} by user {current_user.id}')
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            note.filename,
            as_attachment=True
        )
    except Exception as e:
        logger.error(f'Error downloading note {note_id}: {e}')
        flash('Error downloading file')
        return redirect(url_for('index'))

with app.app_context():
    try:
        db.create_all()
        logger.info('Database tables created successfully')

        # Create departments if they don't exist
        departments = [
            'Computer Science',
            'Information Technology',
            'Data Science',
            'Cybersecurity',
            'Civil Engineering',
            'Mechanical Engineering',
            'Electrical Engineering',
            'Electronics Engineering',
            'Chemical Engineering',
            'Biotechnology',
            'Mathematics',
            'Physics',
            'Chemistry'
        ]
        for dept_name in departments:
            if not Department.query.filter_by(name=dept_name).first():
                department = Department(name=dept_name)
                db.session.add(department)
                logger.info(f'Added department: {dept_name}')
        db.session.commit()
        logger.info('Initial departments created successfully')
    except Exception as e:
        logger.error(f'Error during database initialization: {e}')