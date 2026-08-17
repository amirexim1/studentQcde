import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import pymysql
import pytz

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql+pymysql://user:password@localhost/student_tracker')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Iran timezone
IRAN_TZ = pytz.timezone('Asia/Tehran')

# ==================== DATABASE MODELS ====================

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IRAN_TZ))
    
    # Relationships
    study_sessions = db.relationship('StudySession', backref='user', lazy=True, cascade='all, delete-orphan')
    class_schedules = db.relationship('ClassSchedule', backref='user', lazy=True, cascade='all, delete-orphan')
    exams = db.relationship('Exam', backref='user', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='user', lazy=True, cascade='all, delete-orphan')
    meditation_sessions = db.relationship('MeditationSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class StudySession(db.Model):
    __tablename__ = 'study_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    topic = db.Column(db.String(200), nullable=True)
    start_time = db.Column(db.DateTime, default=lambda: datetime.now(IRAN_TZ))
    end_time = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IRAN_TZ))

class ClassSchedule(db.Model):
    __tablename__ = 'class_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Saturday, 6=Friday (Iranian week)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    teacher = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IRAN_TZ))

class Exam(db.Model):
    __tablename__ = 'exams'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    exam_date = db.Column(db.DateTime, nullable=False)
    exam_type = db.Column(db.String(50), nullable=True)  # e.g., 'کتبی', 'شفاهی', 'عملی'
    topics = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='upcoming')  # upcoming, completed, missed
    score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IRAN_TZ))

class Assignment(db.Model):
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed, overdue
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IRAN_TZ))

class MeditationSession(db.Model):
    __tablename__ = 'meditation_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    session_type = db.Column(db.String(50), nullable=True)  # e.g., 'تنفس', 'ذهن‌آگاهی', 'بدن‌اسکن'
    notes = db.Column(db.Text, nullable=True)
    session_date = db.Column(db.DateTime, default=lambda: datetime.now(IRAN_TZ))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(IRAN_TZ))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==================== WEB ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        if User.query.filter_by(username=username).first():
            flash('این نام کاربری قبلاً گرفته شده است.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('این ایمیل قبلاً ثبت شده است.', 'danger')
            return render_template('register.html')
        
        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('ثبت‌نام با موفقیت انجام شد. حالا وارد شوید.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('خطایی رخ داد. لطفاً دوباره تلاش کنید.', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    today = datetime.now(IRAN_TZ).date()
    
    # Today's study sessions
    today_sessions = StudySession.query.filter(
        db.func.date(StudySession.start_time) == today,
        StudySession.user_id == current_user.id
    ).all()
    
    # Total study time this week
    week_start = today - timedelta(days=today.weekday())
    week_sessions = StudySession.query.filter(
        StudySession.start_time >= week_start,
        StudySession.user_id == current_user.id
    ).all()
    total_study_minutes = sum(s.duration_minutes or 0 for s in week_sessions)
    
    # Upcoming exams
    upcoming_exams = Exam.query.filter(
        Exam.exam_date >= datetime.now(IRAN_TZ),
        Exam.user_id == current_user.id,
        Exam.status == 'upcoming'
    ).order_by(Exam.exam_date).limit(5).all()
    
    # Pending assignments
    pending_assignments = Assignment.query.filter(
        Assignment.due_date >= datetime.now(IRAN_TZ),
        Assignment.user_id == current_user.id,
        Assignment.status == 'pending'
    ).order_by(Assignment.due_date).limit(5).all()
    
    # Recent meditation sessions
    recent_meditations = MeditationSession.query.filter(
        MeditationSession.user_id == current_user.id
    ).order_by(MeditationSession.session_date.desc()).limit(5).all()
    
    # Today's classes
    today_day = today.weekday()
    today_classes = ClassSchedule.query.filter(
        ClassSchedule.day_of_week == today_day,
        ClassSchedule.user_id == current_user.id
    ).order_by(ClassSchedule.start_time).all()
    
    return render_template('dashboard.html',
                         today_sessions=today_sessions,
                         total_study_minutes=total_study_minutes,
                         upcoming_exams=upcoming_exams,
                         pending_assignments=pending_assignments,
                         recent_meditations=recent_meditations,
                         today_classes=today_classes,
                         today=today)

@app.route('/study', methods=['GET', 'POST'])
@login_required
def study_log():
    if request.method == 'POST':
        subject = request.form.get('subject')
        topic = request.form.get('topic')
        duration = request.form.get('duration')
        notes = request.form.get('notes')
        
        session = StudySession(
            user_id=current_user.id,
            subject=subject,
            topic=topic,
            duration_minutes=int(duration) if duration else None,
            notes=notes,
            end_time=datetime.now(IRAN_TZ)
        )
        
        db.session.add(session)
        db.session.commit()
        
        flash('جلسه مطالعه با موفقیت ثبت شد.', 'success')
        return redirect(url_for('study_log'))
    
    # Get all study sessions for this user
    sessions = StudySession.query.filter_by(user_id=current_user.id)\
        .order_by(StudySession.start_time.desc()).limit(50).all()
    
    return render_template('study_log.html', sessions=sessions)

@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            subject = request.form.get('subject')
            day = int(request.form.get('day'))
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            teacher = request.form.get('teacher')
            location = request.form.get('location')
            
            from datetime import datetime as dt
            schedule = ClassSchedule(
                user_id=current_user.id,
                subject=subject,
                day_of_week=day,
                start_time=dt.strptime(start_time, '%H:%M').time(),
                end_time=dt.strptime(end_time, '%H:%M').time(),
                teacher=teacher,
                location=location
            )
            
            db.session.add(schedule)
            db.session.commit()
            flash('کلاس با موفقیت اضافه شد.', 'success')
        
        elif action == 'delete':
            schedule_id = request.form.get('id')
            schedule = ClassSchedule.query.filter_by(id=schedule_id, user_id=current_user.id).first()
            if schedule:
                db.session.delete(schedule)
                db.session.commit()
                flash('کلاس حذف شد.', 'success')
        
        return redirect(url_for('schedule'))
    
    schedules = ClassSchedule.query.filter_by(user_id=current_user.id)\
        .order_by(ClassSchedule.day_of_week, ClassSchedule.start_time).all()
    
    days_fa = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه']
    
    return render_template('schedule.html', schedules=schedules, days_fa=days_fa)

@app.route('/exams', methods=['GET', 'POST'])
@login_required
def exams():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            subject = request.form.get('subject')
            exam_date = request.form.get('exam_date')
            exam_type = request.form.get('exam_type')
            topics = request.form.get('topics')
            
            exam = Exam(
                user_id=current_user.id,
                subject=subject,
                exam_date=datetime.strptime(exam_date, '%Y-%m-%dT%H:%M'),
                exam_type=exam_type,
                topics=topics
            )
            
            db.session.add(exam)
            db.session.commit()
            flash('آزمون با موفقیت اضافه شد.', 'success')
        
        elif action == 'complete':
            exam_id = request.form.get('id')
            score = request.form.get('score')
            exam = Exam.query.filter_by(id=exam_id, user_id=current_user.id).first()
            if exam:
                exam.status = 'completed'
                exam.score = float(score) if score else None
                db.session.commit()
                flash('وضعیت آزمون به‌روز شد.', 'success')
        
        elif action == 'delete':
            exam_id = request.form.get('id')
            exam = Exam.query.filter_by(id=exam_id, user_id=current_user.id).first()
            if exam:
                db.session.delete(exam)
                db.session.commit()
                flash('آزمون حذف شد.', 'success')
        
        return redirect(url_for('exams'))
    
    exams_list = Exam.query.filter_by(user_id=current_user.id)\
        .order_by(Exam.exam_date.desc()).all()
    
    return render_template('exams.html', exams=exams_list)

@app.route('/assignments', methods=['GET', 'POST'])
@login_required
def assignments():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            subject = request.form.get('subject')
            title = request.form.get('title')
            description = request.form.get('description')
            due_date = request.form.get('due_date')
            
            assignment = Assignment(
                user_id=current_user.id,
                subject=subject,
                title=title,
                description=description,
                due_date=datetime.strptime(due_date, '%Y-%m-%dT%H:%M')
            )
            
            db.session.add(assignment)
            db.session.commit()
            flash('تکلیف با موفقیت اضافه شد.', 'success')
        
        elif action == 'complete':
            assignment_id = request.form.get('id')
            assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first()
            if assignment:
                assignment.status = 'completed'
                assignment.completed_at = datetime.now(IRAN_TZ)
                db.session.commit()
                flash('تکلیف به عنوان انجام‌شده علامت‌گذاری شد.', 'success')
        
        elif action == 'delete':
            assignment_id = request.form.get('id')
            assignment = Assignment.query.filter_by(id=assignment_id, user_id=current_user.id).first()
            if assignment:
                db.session.delete(assignment)
                db.session.commit()
                flash('تکلیف حذف شد.', 'success')
        
        return redirect(url_for('assignments'))
    
    assignments_list = Assignment.query.filter_by(user_id=current_user.id)\
        .order_by(Assignment.due_date.asc()).all()
    
    return render_template('assignments.html', assignments=assignments_list)

@app.route('/meditation', methods=['GET', 'POST'])
@login_required
def meditation():
    if request.method == 'POST':
        duration = request.form.get('duration')
        session_type = request.form.get('session_type')
        notes = request.form.get('notes')
        
        session = MeditationSession(
            user_id=current_user.id,
            duration_minutes=int(duration),
            session_type=session_type,
            notes=notes
        )
        
        db.session.add(session)
        db.session.commit()
        
        flash('جلسه مدیتیشن با موفقیت ثبت شد.', 'success')
        return redirect(url_for('meditation'))
    
    sessions = MeditationSession.query.filter_by(user_id=current_user.id)\
        .order_by(MeditationSession.session_date.desc()).limit(50).all()
    
    return render_template('meditation.html', sessions=sessions)

@app.route('/reports')
@login_required
def reports():
    # Calculate statistics
    total_sessions = StudySession.query.filter_by(user_id=current_user.id).count()
    total_study_time = db.session.query(db.func.sum(StudySession.duration_minutes))\
        .filter_by(user_id=current_user.id).scalar() or 0
    
    total_meditations = MeditationSession.query.filter_by(user_id=current_user.id).count()
    total_meditation_time = db.session.query(db.func.sum(MeditationSession.duration_minutes))\
        .filter_by(user_id=current_user.id).scalar() or 0
    
    completed_assignments = Assignment.query.filter_by(
        user_id=current_user.id, 
        status='completed'
    ).count()
    
    completed_exams = Exam.query.filter_by(
        user_id=current_user.id, 
        status='completed'
    ).count()
    
    # Study by subject
    subject_stats = db.session.query(
        StudySession.subject,
        db.func.count(StudySession.id),
        db.func.sum(StudySession.duration_minutes)
    ).filter_by(user_id=current_user.id).group_by(StudySession.subject).all()
    
    # Last 7 days activity
    today = datetime.now(IRAN_TZ).date()
    last_7_days = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_sessions = StudySession.query.filter(
            db.func.date(StudySession.start_time) == day,
            StudySession.user_id == current_user.id
        ).all()
        day_minutes = sum(s.duration_minutes or 0 for s in day_sessions)
        last_7_days.append({
            'date': day,
            'minutes': day_minutes,
            'day_name': day.strftime('%A')[:3]
        })
    
    return render_template('reports.html',
                         total_sessions=total_sessions,
                         total_study_time=total_study_time,
                         total_meditations=total_meditations,
                         total_meditation_time=total_meditation_time,
                         completed_assignments=completed_assignments,
                         completed_exams=completed_exams,
                         subject_stats=subject_stats,
                         last_7_days=last_7_days)

# ==================== MAIN ====================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
