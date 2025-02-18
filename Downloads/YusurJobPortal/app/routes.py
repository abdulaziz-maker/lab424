from flask import Blueprint, render_template, redirect, url_for, flash, request, Flask
from flask_login import login_user, logout_user, login_required, current_user
from app.models import Job, User, Certificate, db
from app import db, login_manager
from app.forms import LoginForm, JobForm, RegistrationForm
from werkzeug.utils import secure_filename
import os


main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/')
def home():
    jobs = Job.query.all()
    return render_template('home.html', jobs=jobs)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:  # بدون تشفير الآن
            login_user(user)
            flash("✅ تسجيل الدخول ناجح!", "success")
            return redirect(url_for('main.home'))
        else:
            flash("❌ البريد الإلكتروني أو كلمة المرور غير صحيحة!", "danger")

    return render_template("login.html", form=form)



@main.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user)

@main.route('/add-job', methods=['GET', 'POST'])
@login_required
def add_job():
    form = JobForm()
    if form.validate_on_submit():
        new_job = Job(
            title=form.title.data,
            description=form.description.data,
            company=form.company.data,
            employer_id=current_user.id
        )
        db.session.add(new_job)
        db.session.commit()
        flash("🎉 تم إضافة الوظيفة بنجاح!", "success")
        return redirect(url_for("main.home"))
    return render_template('add_job.html', form=form)

@main.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)

    if job.employer_id != current_user.id:
        flash("❌ لا يمكنك تعديل هذه الوظيفة!", "danger")
        return redirect(url_for('main.home'))

    form = JobForm(obj=job)
    if form.validate_on_submit():
        job.title = form.title.data
        job.description = form.description.data
        job.company = form.company.data
        db.session.commit()
        flash("✅ تم تحديث الوظيفة بنجاح!", "success")
        return redirect(url_for('main.home'))

    return render_template('edit_job.html', form=form, job=job)

@main.route('/delete-job/<int:job_id>', methods=['POST', 'GET'])
@login_required
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)

    if job.employer_id != current_user.id:
        flash("❌ لا يمكنك حذف هذه الوظيفة!", "danger")
        return redirect(url_for('main.home'))

    db.session.delete(job)
    db.session.commit()
    flash("🗑️ تم حذف الوظيفة بنجاح!", "success")
    return redirect(url_for('main.home'))

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash("🚪 تم تسجيل الخروج بنجاح!", "info")
    return redirect(url_for('main.home'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('🎉 تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/certificates'
app.secret_key = 'your_secret_key'  # يجب أن تستبدلها بمفتاح سري حقيقي

# التأكد من وجود مجلد رفع الملفات
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@main.route('/upload_certificate', methods=['GET', 'POST'])
@login_required
def upload_certificate():
    if request.method == 'POST':
        if 'certificate' not in request.files:
            flash('لم يتم رفع أي ملف!', 'danger')
            return redirect(request.url)

        file = request.files['certificate']
        if file.filename == '':
            flash('لم يتم اختيار ملف!', 'danger')
            return redirect(request.url)

        allowed_extensions = {'pdf', 'jpg', 'png'}
        if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            flash('نوع الملف غير مدعوم! يجب أن يكون PDF أو JPG أو PNG.', 'danger')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads/certificates', filename)
        file.save(filepath)

        new_certificate = Certificate(user_id=current_user.id, file_path=filepath)
        db.session.add(new_certificate)
        db.session.commit()

        flash('تم رفع الشهادة بنجاح!', 'success')
        return redirect(url_for('main.dashboard'))

    return render_template('upload_certificate.html')