from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import random
import os
import io
import math
from xhtml2pdf import pisa 
import qrcode
import base64
from datetime import datetime

app = Flask(__name__)

# ==========================================
# PRODUCTION-READY CONFIGURATION
# (Pulls from server environment, with local fallbacks)
# ==========================================
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "aks_academy_secure_key_2026")

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME", "aksacademyranchi@gmail.com")      
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD", "cjqwvbdzpqpqseok")  
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("MAIL_USERNAME", "aksacademyranchi@gmail.com")
mail = Mail(app)

# ==========================================
# CONSTANTS & DATA
# ==========================================
ADMIN_USER = os.environ.get("AKS_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("AKS_ADMIN_PASS", "aks123")

def get_absolute_path(uri, rel):
    if uri.startswith('static/'):
        return os.path.abspath(os.path.join(app.root_path, uri))
    return uri

# FOLDERS
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'students')
app.config['GALLERY_FOLDER'] = os.path.join('static', 'uploads', 'gallery')
app.config['PROGRESS_FOLDER'] = os.path.join('static', 'uploads', 'progress')
app.config['MATERIAL_FOLDER'] = os.path.join('static', 'uploads', 'materials')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['GALLERY_FOLDER'], exist_ok=True)
os.makedirs(app.config['PROGRESS_FOLDER'], exist_ok=True)
os.makedirs(app.config['MATERIAL_FOLDER'], exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///aks_academy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ==========================================
# DATABASE MODELS
# ==========================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False) # Expanded size for hashes

class StaffAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, default="staff")
    password = db.Column(db.String(255), nullable=False) # Expanded size for hashes

class StudyMaterial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    batch = db.Column(db.String(100), nullable=False) 
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.String(20), default=lambda: datetime.now().strftime("%d-%b-%Y"))

class SatApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    batch = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="Pending")
    date_applied = db.Column(db.String(20), default=lambda: datetime.now().strftime("%d-%b-%Y"))
    last_call_date = db.Column(db.String(20))
    message = db.Column(db.Text)
    next_call_date = db.Column(db.String(20))

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    student = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(100), nullable=False)
    session_year = db.Column(db.String(20)) 
    subjects = db.Column(db.String(255))    
    student_email = db.Column(db.String(100))
    dob = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    father_name = db.Column(db.String(100))
    mother_name = db.Column(db.String(100))
    student_phone = db.Column(db.String(20))
    parent_phone = db.Column(db.String(20))
    permanent_address = db.Column(db.String(255)) 
    local_address = db.Column(db.String(255))     
    pincode = db.Column(db.String(10))
    source = db.Column(db.String(50))
    current_board = db.Column(db.String(50))
    current_school = db.Column(db.String(255))
    add_jee_neet = db.Column(db.String(10))
    prev_board = db.Column(db.String(50))
    prev_school = db.Column(db.String(255))
    prev_year = db.Column(db.String(10))
    prev_marks = db.Column(db.String(50))
    prev_percentage = db.Column(db.String(20))
    prev_division = db.Column(db.String(50))
    student_image = db.Column(db.String(255))
    aadhar_card = db.Column(db.String(255))
    
    total_fee = db.Column(db.Integer)        
    discount_applied = db.Column(db.String(100), default="None")
    payable_fee = db.Column(db.Integer)
    payment_plan = db.Column(db.String(50))  
    amount_paid = db.Column(db.Integer) 
    
    status = db.Column(db.String(20), default="Pending") 
    admission_date = db.Column(db.String(20), default=lambda: datetime.now().strftime("%d-%b-%Y"))
    last_call_date = db.Column(db.String(20))
    message = db.Column(db.Text)
    next_call_date = db.Column(db.String(20))

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)

class ProgressReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(150), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.String(20), default=lambda: datetime.now().strftime("%d-%b-%Y"))

class Enquiry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    course_interest = db.Column(db.String(100))
    status = db.Column(db.String(20), default="Pending")
    date_submitted = db.Column(db.String(20), default=lambda: datetime.now().strftime("%d-%b-%Y"))
    last_call_date = db.Column(db.String(20))
    message = db.Column(db.Text)
    next_call_date = db.Column(db.String(20))

COURSE_DATA = [
    {"id": "pre-found-9", "category": "Pre-Foundation", "name": "Pre-Foundation (Class 9)", "price": 25000, "img": "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&q=80&w=400", "desc": "Building strong logic, mathematics, and core science concepts early.", "tag": "Early Start", "duration": "1 Year"},
    {"id": "pre-found-10", "category": "Pre-Foundation", "name": "Pre-Foundation (Class 10)", "price": 25000, "img": "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&q=80&w=400", "desc": "Focused board exam preparation for Class 10 students.", "tag": "Board Prep", "duration": "1 Year"},
    {"id": "pre-found-9-10", "category": "Pre-Foundation", "name": "Pre-Foundation (Class 9 & 10)", "price": 50000, "img": "https://images.unsplash.com/photo-1509062522246-3755977927d7?auto=format&fit=crop&q=80&w=400", "desc": "Comprehensive 2-year integrated program.", "tag": "Integrated", "duration": "2 Years"},
    {"id": "found-11", "category": "Foundation", "name": "Foundation (Class 11)", "price": 45500, "img": "/static/images/Boards.jpg", "desc": "Solidifying Class 11 concepts crucial for board exams.", "tag": "Core Base", "duration": "1 Year"},
    {"id": "found-12", "category": "Foundation", "name": "Foundation (Class 12)", "price": 45500, "img": "/static/images/Boards.jpg", "desc": "Intensive Class 12 board focus to maximize your percentage.", "tag": "Board Prep", "duration": "1 Year"},
    {"id": "found-11-12", "category": "Foundation", "name": "Foundation (Class 11 & 12)", "price": 91000, "img": "/static/images/Boards.jpg", "desc": "Comprehensive board exam preparation synchronized with entrance training.", "tag": "Integrated", "duration": "2 Years"},
    {"id": "target-jee", "category": "Target", "name": "Target Batch (JEE)", "price": 65000, "img": "/static/images/Jee.jpg", "desc": "Intensive Full PCM Syllabus training specifically for JEE Mains & Advanced.", "tag": "Engineering", "duration": "1 Year"},
    {"id": "target-neet", "category": "Target", "name": "Target Batch (NEET)", "price": 65000, "img": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?auto=format&fit=crop&q=80&w=400", "desc": "Rigorous Biology, Physics, and Chemistry training targeting top medical colleges.", "tag": "Medical", "duration": "1 Year"},
    {"id": "target-nda", "category": "Target", "name": "Target Batch (NDA)", "price": 65000, "img": "https://pcprd.azureedge.net/content/1db86efa68b0.jpg", "desc": "Dedicated Defense entrance training with strategic math and general ability guidance.", "tag": "Defense", "duration": "6 Months"}
]

def generate_admission_pdf(enroll):
    html = render_template('admission_pdf.html', enroll=enroll)
    result = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=result, link_callback=get_absolute_path)
    result.seek(0)
    return result

# ==========================================
# PUBLIC ROUTES
# ==========================================
@app.route('/')
def home(): 
    slides = Gallery.query.limit(15).all()
    return render_template('index.html', slides=slides)

@app.route('/about')
def about(): return render_template('about.html')

@app.route('/courses')
def courses(): return render_template('courses.html', courses=COURSE_DATA)

@app.route('/course/<course_id>')
def course_detail(course_id):
    course = next((item for item in COURSE_DATA if item["id"] == course_id), None)
    if not course:
        flash("Course not found.", "warning")
        return redirect(url_for('courses'))
    emi_price = round(course.get('price', 0) / 3)
    return render_template('course_detail.html', course=course, emi_price=emi_price)

@app.route('/coming_soon')
def coming_soon():
    if 'user' not in session: return redirect(url_for('login'))
    return render_template('coming_soon.html')

@app.route('/apply_sat')
def apply_sat():
    return render_template('apply_sat.html', courses=COURSE_DATA)

@app.route('/submit_sat', methods=['POST'])
def submit_sat():
    new_sat = SatApplication(
        name=request.form.get('sat_name'),
        email=request.form.get('sat_email'),
        phone=request.form.get('sat_phone'),
        batch=request.form.get('sat_batch')
    )
    db.session.add(new_sat)
    db.session.commit()
    flash("AKS-SAT Application submitted successfully! Our counseling team will contact you with your exam details soon.", "success")
    return redirect(url_for('home'))

@app.route('/submit_enquiry', methods=['POST'])
def submit_enquiry():
    new_enq = Enquiry(
        name=request.form.get('enquiry_name'),
        phone=request.form.get('enquiry_phone'),
        email=request.form.get('enquiry_email'),
        course_interest=request.form.get('course_interest', 'General Enquiry')
    )
    db.session.add(new_enq)
    db.session.commit()
    flash("Enquiry submitted successfully! Our counselor will contact you within 24 hours.", "success")
    return redirect(request.referrer or url_for('courses'))

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'user' not in session:
        flash("Please login to purchase a course", "warning")
        return redirect(url_for('login'))

    course_name = request.form.get('course_name')
    payment_plan = request.form.get('payment_plan', 'full')
    total_fee = int(request.form.get('price', 0))
    payable_fee = total_fee 

    if payment_plan == 'emi_3':
        amount_paid = math.ceil(payable_fee / 3)
        plan_name = "3 Months EMI"
    elif payment_plan == 'emi_6':
        amount_paid = math.ceil(payable_fee / 6)
        plan_name = "6 Months EMI"
    else:
        amount_paid = payable_fee
        plan_name = "Full Payment"

    subjects = request.form.getlist('subjects')
    subjects_str = ", ".join(subjects) if subjects else "N/A"

    image_file = request.files.get('student_image')
    filename = "default_avatar.png"
    if image_file and image_file.filename:
        filename = secure_filename(f"dp_{session['user_id']}_{image_file.filename}")
        image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    aadhar_file = request.files.get('aadhar_card')
    aadhar_filename = "Not_Provided"
    if aadhar_file and aadhar_file.filename:
        aadhar_filename = secure_filename(f"aadhar_{session['user_id']}_{aadhar_file.filename}")
        aadhar_file.save(os.path.join(app.config['UPLOAD_FOLDER'], aadhar_filename))

    prev_marks = f"{request.form.get('prev_obtained_marks', '')} / {request.form.get('prev_max_marks', '')}"

    new_enrollment = Enrollment(
        user_id=session['user_id'],
        student=session['user'],
        course=course_name,
        session_year=request.form.get('session_year'),
        subjects=subjects_str,
        student_email=request.form.get('student_email'),
        dob=request.form.get('dob'),
        gender=request.form.get('gender'),
        father_name=request.form.get('father_name'),
        mother_name=request.form.get('mother_name'),
        student_phone=request.form.get('student_phone'),
        parent_phone=request.form.get('parent_phone'),
        permanent_address=request.form.get('permanent_address'),
        local_address=request.form.get('local_address'),
        pincode=request.form.get('pincode'),
        source=request.form.get('source'),
        current_board=request.form.get('current_board', 'N/A'),
        current_school=request.form.get('current_school', 'N/A'),
        add_jee_neet="Yes" if request.form.get('add_jee_neet') else "No",
        prev_board=request.form.get('prev_board'),
        prev_school=request.form.get('prev_school'),
        prev_year=request.form.get('prev_year'),
        prev_marks=prev_marks,
        prev_percentage=request.form.get('prev_percentage'),
        prev_division=request.form.get('prev_division'),
        student_image=filename,
        aadhar_card=aadhar_filename,
        total_fee=total_fee,
        discount_applied="None",
        payable_fee=payable_fee,
        payment_plan=plan_name,
        amount_paid=amount_paid,
        status="Pending" 
    )
    db.session.add(new_enrollment)
    db.session.commit()

    try:
        pdf_file = generate_admission_pdf(new_enrollment)
        msg = Message("Application Received - AKS Academy", recipients=[new_enrollment.student_email])
        msg.body = f"Dear {new_enrollment.student},\n\nYour application for '{new_enrollment.course}' has been successfully submitted to AKS Academy!\n\nPlease find your preliminary admission slip attached to this email. You can complete your admission by making the payment using the QR code provided on the website or contacting the admin desk.\n\nRegards,\nAKS Academy Administration"
        msg.attach(f"Application_Slip_{new_enrollment.student}.pdf", "application/pdf", pdf_file.read())
        mail.send(msg)
    except Exception as e:
        pass

    upi_id = "9430336006@okbizaxis"
    payee_name = "AKS Academy"
    upi_url = f"upi://pay?pa={upi_id}&pn={payee_name}&am={amount_paid}&cu=INR"
    
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    qr_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return render_template('upi_payment.html', enroll=new_enrollment, qr_code=qr_base64)

@app.route('/download_slip/<int:enroll_id>')
def download_slip(enroll_id):
    if 'user' not in session and not session.get('admin_logged_in') and not session.get('staff_logged_in'): 
        return redirect(url_for('login'))
    enroll = Enrollment.query.get_or_404(enroll_id)
    pdf_file = generate_admission_pdf(enroll)
    return send_file(pdf_file, as_attachment=False, download_name=f"Admission_Receipt_{enroll.student}.pdf", mimetype='application/pdf')


# ==========================================
# ADMIN & STAFF SHARED VIEWS & ACTIONS
# ==========================================
@app.route('/admin')
def admin():
    if not (session.get('admin_logged_in') or session.get('staff_logged_in')): 
        return redirect(url_for('login'))
        
    staff_acct = StaffAccount.query.first()
    
    return render_template('admin.html', 
                           users=User.query.all(), 
                           enrollments=Enrollment.query.order_by(Enrollment.id.desc()).all(),
                           slides=Gallery.query.all(),
                           reports=ProgressReport.query.order_by(ProgressReport.id.desc()).all(),
                           enquiries=Enquiry.query.order_by(Enquiry.id.desc()).all(),
                           materials=StudyMaterial.query.order_by(StudyMaterial.id.desc()).all(),
                           sat_apps=SatApplication.query.order_by(SatApplication.id.desc()).all(),
                           staff_acct=staff_acct,
                           courses=COURSE_DATA)

@app.route('/admin/preview/<int:enroll_id>')
def admin_preview(enroll_id):
    if not (session.get('admin_logged_in') or session.get('staff_logged_in')): 
        return redirect(url_for('login'))
    enroll = Enrollment.query.get_or_404(enroll_id)
    return render_template('admin_preview.html', enroll=enroll)

@app.route('/admin/collect_fee/<int:enroll_id>', methods=['POST'])
def collect_fee(enroll_id):
    if not (session.get('admin_logged_in') or session.get('staff_logged_in')): 
        return redirect(url_for('login'))
        
    enroll = Enrollment.query.get_or_404(enroll_id)
    payment_type = request.form.get('payment_type')
    
    if '3 Month' in enroll.payment_plan:
        emi_amount = math.ceil(enroll.payable_fee / 3)
    elif '6 Month' in enroll.payment_plan:
        emi_amount = math.ceil(enroll.payable_fee / 6)
    else:
        emi_amount = enroll.payable_fee

    if payment_type == 'installment':
        enroll.amount_paid += emi_amount
        if enroll.amount_paid > enroll.payable_fee:
            enroll.amount_paid = enroll.payable_fee
        base_msg = f"Installment payment of ₹{'{:,}'.format(emi_amount)} logged successfully!"
        
    elif payment_type == 'full':
        enroll.amount_paid = enroll.payable_fee
        base_msg = "Student account marked as 100% Fully Paid."
        
    db.session.commit()

    try:
        pdf_file = generate_admission_pdf(enroll)
        msg = Message("Payment Received - AKS Academy", recipients=[enroll.student_email])
        msg.body = f"Dear {enroll.student},\n\nWe have successfully recorded your recent fee payment.\n\nPlease find your updated official fee receipt attached to this email.\n\nThank you,\nAKS Academy"
        msg.attach(f"Updated_Receipt_{enroll.student}.pdf", "application/pdf", pdf_file.read())
        mail.send(msg)
        flash(base_msg + " Updated receipt was emailed to the student automatically.", "success")
    except Exception as e:
        flash(base_msg + " (Warning: Database updated, but the email failed to send.)", "warning")

    return redirect(url_for('admin_preview', enroll_id=enroll.id))

@app.route('/admin/upload_material', methods=['POST'])
def upload_material():
    if not (session.get('admin_logged_in') or session.get('staff_logged_in')): return redirect(url_for('login'))
    title = request.form.get('title')
    batch = request.form.get('batch')
    mat_file = request.files.get('material_file')
    
    if mat_file and mat_file.filename:
        filename = secure_filename(f"mat_{random.randint(1000,9999)}_{mat_file.filename}")
        mat_file.save(os.path.join(app.config['MATERIAL_FOLDER'], filename))
        new_mat = StudyMaterial(title=title, batch=batch, filename=filename)
        db.session.add(new_mat)
        db.session.commit()
        flash("Study Material uploaded and assigned to batch successfully!", "success")
    else:
        flash("Please attach a valid PDF file.", "danger")
    return redirect(url_for('admin'))


@app.route('/admin/sat/resolve/<int:sat_id>')
def resolve_sat(sat_id):
    if not (session.get('admin_logged_in') or session.get('staff_logged_in')): return redirect(url_for('login'))
    sat = SatApplication.query.get_or_404(sat_id)
    sat.status = "Contacted"
    db.session.commit()
    flash("SAT Applicant marked as contacted.", "success")
    return redirect(url_for('admin'))


# ==========================================
# FOLLOW UP TRACKERS (STAFF & ADMIN)
# ==========================================
@app.route('/admin/enrollment/update/<int:enroll_id>', methods=['POST'])
def update_enrollment_followup(enroll_id):
    if not (session.get('admin_logged_in') or session.get('staff_logged_in')): return redirect(url_for('login'))
    enroll = Enrollment.query.get_or_404(enroll_id)
    new_call_date = request.form.get('last_call_date')
    new_message = request.form.get('new_message') 
    if new_message and new_message.strip():
        timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
        call_info = f" (Called on: {new_call_date})" if new_call_date else ""
        log_entry = f"➤ [{timestamp}]{call_info}\n{new_message.strip()}"
        if enroll.message:
            enroll.message = enroll.message + "\n\n" + log_entry
        else:
            enroll.message = log_entry
    enroll.last_call_date = new_call_date
    enroll.next_call_date = request.form.get('next_call_date')
    db.session.commit()
    flash("Course Admission follow-up logged successfully.", "success")
    return redirect(url_for('admin'))

@app.route('/admin/sat/update/<int:sat_id>', methods=['POST'])
def update_sat(sat_id):
    if not (session.get('admin_logged_in') or session.get('staff_logged_in')): return redirect(url_for('login'))
    sat = SatApplication.query.get_or_404(sat_id)
    new_call_date = request.form.get('last_call_date')
    new_message = request.form.get('new_message') 
    if new_message and new_message.strip():
        timestamp = datetime.now().strftime("%d-%b-%Y %I:%M %p")
        call_info = f" (Called on: {new_call_date})" if new_call_date else ""
        log_entry = f"➤ [{timestamp}]{call_info}\n{new_message.strip()}"
        if sat.message:
            sat.message = sat.message + "\n\n" + log_entry
        else:
            sat.message = log_entry
    sat.last_call_date = new_call_date
    sat.next_call_date = request.form.get('next_call_date')
    sat.status = request.form.get('status')
    db.session.commit()
    flash("AKS-SAT Application follow-up logged successfully.", "success")
    return redirect(url_for('admin'))


# ==========================================
# ADMIN ONLY RESTRICTED ACTIONS
# ==========================================
def admin_only():
    if not session.get('admin_logged_in'):
        flash("Permission Denied: Only Admins can perform this action.", "danger")
        return True
    return False

@app.route('/admin/update_staff', methods=['POST'])
def update_staff():
    if admin_only(): return redirect(url_for('admin'))
    staff_acct = StaffAccount.query.first()
    if not staff_acct:
        staff_acct = StaffAccount()
        db.session.add(staff_acct)
    
    # NEW: Secure Password Hashing
    staff_acct.username = request.form.get('new_staff_user')
    staff_acct.password = generate_password_hash(request.form.get('new_staff_pass'))
    db.session.commit()
    
    flash("Staff Portal credentials have been successfully updated and secured!", "success")
    return redirect(url_for('admin'))

@app.route('/admin/apply_discount/<int:enroll_id>', methods=['POST'])
def apply_discount(enroll_id):
    if admin_only(): return redirect(url_for('admin_preview', enroll_id=enroll_id))
    enroll = Enrollment.query.get_or_404(enroll_id)
    discount_pct = int(request.form.get('discount_pct') or 0)
    new_plan = request.form.get('new_payment_plan')
    if discount_pct in [10, 20, 30, 40, 50]:
        discount_amount = int(enroll.total_fee * (discount_pct / 100.0))
        enroll.discount_applied = f"AKS-SAT Scholarship ({discount_pct}% OFF)"
        enroll.payable_fee = enroll.total_fee - discount_amount
    elif discount_pct == 0:
        enroll.discount_applied = "None"
        enroll.payable_fee = enroll.total_fee
        
    if new_plan == 'emi_3':
        enroll.payment_plan = "3 Months EMI"
        enroll.amount_paid = math.ceil(enroll.payable_fee / 3)
    elif new_plan == 'emi_6':
        enroll.payment_plan = "6 Months EMI"
        enroll.amount_paid = math.ceil(enroll.payable_fee / 6)
    else: 
        enroll.payment_plan = "Full Payment"
        enroll.amount_paid = enroll.payable_fee
        
    db.session.commit()
    flash(f"Financial details and Payment Plan updated successfully!", "success")
    return redirect(url_for('admin_preview', enroll_id=enroll.id))

@app.route('/admin/confirm_approve/<int:enroll_id>')
def confirm_approve(enroll_id):
    if admin_only(): return redirect(url_for('admin_preview', enroll_id=enroll_id))
    enroll = Enrollment.query.get_or_404(enroll_id)
    enroll.status = "Approved"
    db.session.commit()
    try:
        pdf_file = generate_admission_pdf(enroll)
        msg = Message("Admission Confirmed - AKS Academy", recipients=[enroll.student_email])
        msg.body = f"Dear {enroll.student},\n\nCongratulations! Your admission to AKS Academy for the course '{enroll.course}' has been officially verified and approved.\n\nPlease find your official admission receipt attached to this email. You may keep this for your records.\n\nWelcome to AKS Academy!\n\nRegards,\nAdmin Desk"
        msg.attach(f"Official_Receipt_{enroll.student}.pdf", "application/pdf", pdf_file.read())
        mail.send(msg)
        flash_text = f"Admission for {enroll.student} approved and the Official Receipt was emailed successfully!"
    except Exception as e:
        flash_text = f"Admission for {enroll.student} approved, but the email failed to send. Check server logs."
    flash(flash_text, "success")
    return redirect(url_for('admin'))

@app.route('/admin/reject/<int:enroll_id>')
def reject_enrollment(enroll_id):
    if admin_only(): return redirect(url_for('admin_preview', enroll_id=enroll_id))
    enroll = Enrollment.query.get_or_404(enroll_id)
    enroll.status = "Rejected"
    db.session.commit()
    flash(f"Admission for {enroll.student} was rejected.", "warning")
    return redirect(url_for('admin'))

@app.route('/admin/complete/<int:enroll_id>')
def complete_enrollment(enroll_id):
    if admin_only(): return redirect(url_for('admin_preview', enroll_id=enroll_id))
    enroll = Enrollment.query.get_or_404(enroll_id)
    enroll.status = "Completed"
    db.session.commit()
    flash(f"Course for {enroll.student} has been marked as Completed.", "info")
    return redirect(url_for('admin'))

@app.route('/admin/delete_enrollment/<int:enroll_id>')
def delete_enrollment(enroll_id):
    if admin_only(): return redirect(url_for('admin'))
    enroll = Enrollment.query.get_or_404(enroll_id)
    db.session.delete(enroll)
    db.session.commit()
    flash(f"Record permanently deleted.", "dark")
    return redirect(url_for('admin'))

@app.route('/admin/download_report')
def download_admin_report():
    if admin_only(): return redirect(url_for('admin'))
    enrolls = Enrollment.query.all()
    html = render_template('admin_report_pdf.html', enrolls=enrolls)
    result = io.BytesIO()
    pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=result, link_callback=get_absolute_path)
    result.seek(0)
    return send_file(result, as_attachment=False, download_name="AKS_Academy_Master_Backup.pdf", mimetype='application/pdf')

@app.route('/admin/gallery/delete/<int:slide_id>')
def delete_gallery(slide_id):
    if admin_only(): return redirect(url_for('admin'))
    slide = Gallery.query.get_or_404(slide_id)
    db.session.delete(slide)
    db.session.commit()
    flash("Slide removed from homepage.", "dark")
    return redirect(url_for('admin'))

@app.route('/admin/progress/delete/<int:report_id>')
def delete_progress(report_id):
    if admin_only(): return redirect(url_for('admin'))
    report = ProgressReport.query.get_or_404(report_id)
    try:
        os.remove(os.path.join(app.config['PROGRESS_FOLDER'], report.filename))
    except:
        pass
    db.session.delete(report)
    db.session.commit()
    flash("Progress report deleted successfully.", "dark")
    return redirect(url_for('admin'))

@app.route('/admin/material/delete/<int:mat_id>')
def delete_material(mat_id):
    if admin_only(): return redirect(url_for('admin'))
    mat = StudyMaterial.query.get_or_404(mat_id)
    try:
        os.remove(os.path.join(app.config['MATERIAL_FOLDER'], mat.filename))
    except:
        pass
    db.session.delete(mat)
    db.session.commit()
    flash("Study material removed.", "dark")
    return redirect(url_for('admin'))

@app.route('/admin/enquiry/delete/<int:enq_id>')
def delete_enquiry(enq_id):
    if admin_only(): return redirect(url_for('admin'))
    enq = Enquiry.query.get_or_404(enq_id)
    db.session.delete(enq)
    db.session.commit()
    flash("Enquiry deleted.", "dark")
    return redirect(url_for('admin'))

@app.route('/admin/sat/delete/<int:sat_id>')
def delete_sat(sat_id):
    if admin_only(): return redirect(url_for('admin'))
    sat = SatApplication.query.get_or_404(sat_id)
    db.session.delete(sat)
    db.session.commit()
    flash("SAT Application deleted.", "dark")
    return redirect(url_for('admin'))

# ==========================================
# REGISTRATION & SECURE LOGIN
# ==========================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        raw_password = request.form['password']
        
        if User.query.filter_by(email=email).first():
            flash("Email already exists!", "danger")
        else:
            # NEW: Secure Password Hashing
            hashed_pw = generate_password_hash(raw_password)
            db.session.add(User(name=name, email=email, phone=phone, password=hashed_pw))
            db.session.commit()
            flash("Success! Please Login.", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        l_type = request.form.get('login_type')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if l_type == 'admin':
            if email == ADMIN_USER and password == ADMIN_PASS:
                session['admin_logged_in'] = True
                return redirect(url_for('admin'))
            else:
                flash("Invalid Admin credentials", "danger")
                
        elif l_type == 'staff':
            staff_acct = StaffAccount.query.first()
            current_staff_user = staff_acct.username if staff_acct else "staff"
            current_staff_pass_hash = staff_acct.password if staff_acct else generate_password_hash("aksstaff")

            # Supports logging into older unhashed DB entries gracefully!
            if email == current_staff_user:
                if check_password_hash(current_staff_pass_hash, password) or current_staff_pass_hash == password:
                    session['staff_logged_in'] = True
                    return redirect(url_for('admin'))
            flash("Invalid Office Staff credentials", "danger")
                
        else:
            user = User.query.filter_by(email=email).first()
            # Supports logging into older unhashed student entries gracefully!
            if user:
                if check_password_hash(user.password, password) or user.password == password:
                    session['user'], session['user_id'] = user.name, user.id
                    return redirect(url_for('dashboard'))
            flash("Invalid Student credentials", "danger")
            
    return render_template('login.html')

# ==========================================
# OTP & ACCOUNT RECOVERY ROUTES
# ==========================================
@app.route('/forgot-password')
def forgot_password():
    session.pop('reset_email', None)
    session.pop('reset_otp', None)
    return render_template('verify_otp.html')

@app.route('/request-otp', methods=['POST'])
def request_otp():
    email = request.form.get('email')
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Email not registered.", "danger")
        return redirect(url_for('forgot_password'))
    
    otp = str(random.randint(100000, 999999))
    session['reset_otp'], session['reset_email'] = otp, email
    
    try:
        msg = Message("Reset Password OTP - AKS Academy", recipients=[email], body=f"Your security OTP is: {otp}\n\nPlease do not share this code with anyone.")
        mail.send(msg)
        return redirect(url_for('verify_otp'))
    except Exception as e:
        flash(f"EMAIL SERVER BLOCKED IT! Check console logs.", "danger")
        return redirect(url_for('forgot_password'))

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if not session.get('reset_email'):
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        if request.form.get('otp') == session.get('reset_otp'):
            return redirect(url_for('reset_password'))
        else:
            flash("Incorrect OTP. Please try again.", "danger")
    return render_template('verify_otp.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if not session.get('reset_email'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        user = User.query.filter_by(email=session.get('reset_email')).first()
        if user:
            # NEW: Securely Hash the reset password
            user.password = generate_password_hash(request.form.get('new_password'))
            db.session.commit()
            session.pop('reset_email', None)
            session.pop('reset_otp', None)
            flash("Password updated successfully! Please login.", "success")
            return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect(url_for('login'))
    enrolls = Enrollment.query.filter_by(user_id=session['user_id']).all()
    reports = ProgressReport.query.filter_by(user_id=session['user_id']).order_by(ProgressReport.id.desc()).all()
    materials = StudyMaterial.query.order_by(StudyMaterial.id.desc()).all()
    return render_template('dashboard.html', name=session['user'], enrollments=enrolls, reports=reports, materials=materials)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Initialize default staff securely
        if not StaffAccount.query.first():
            hashed_default = generate_password_hash("aksstaff")
            db.session.add(StaffAccount(username="staff", password=hashed_default))
            db.session.commit()
    app.run(host="0.0.0.0", debug=True)
