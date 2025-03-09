import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, cast, String
from datetime import datetime
import json

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///household_services.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)

class Professional(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    fullname = db.Column(db.String(100), nullable=False)
    service = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(20), nullable=False)
    document = db.Column(db.String(200), nullable=False)
    picture = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    service_relation = db.relationship('Service', backref='professionals', lazy=True)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    base_price = db.Column(db.Float, nullable=False)
    service_subtype = db.Column(db.String(100), nullable=False)
    avg_rating = db.Column(db.Float, nullable=True)

class ServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    booking_request_date = db.Column(db.DateTime, nullable=False)
    booking_created_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    remark = db.Column(db.String(100), nullable=True)
    user = db.relationship('User', backref='requests')
    professional = db.relationship('Professional', backref='requests')
    service = db.relationship('Service', backref='requests')

class RejectedServiceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey('professional.id'), nullable=False)
    service_request_id = db.Column(db.Integer, db.ForeignKey('service_request.id'), nullable=False)
    professional = db.relationship('Professional', backref='rejected_requests')
    service_request = db.relationship('ServiceRequest', backref='rejected_by')

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "adminpass"

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def login():
    message = session.pop('message', '')
    return render_template('login.html', message=message)

@app.route('/login', methods=['POST'])
def handle_login():
    email = request.form['email']
    password = request.form['password']

    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        return redirect(url_for('admin_dashboard'))

    user = User.query.filter_by(email=email, password=password).first()
    if user:
        session['user_email'] = user.email
        return redirect(url_for('user_dashboard'))

    professional = Professional.query.filter_by(email=email, password=password).first()
    
    if professional:
        session['user_email'] = professional.email
        return redirect(url_for('professional_dashboard'))

    error = "Invalid credentials. Please check your email and password."
    return render_template('login.html', error=error)

@app.route('/professional_signup')
def professional_signup():
    email_exists = session.pop('email_exists', False)
    services = Service.query.all()
    return render_template('professional_signup.html', email_exists=email_exists, services=services)

@app.route('/professional_register', methods=['POST'])
def handle_professional_register():
    email = request.form['email']
    password = request.form['password']
    fullname = request.form['fullname']
    p = request.form['service']
    experience = request.form['experience']
    address = request.form['address']
    pincode = request.form['pincode']
    file = request.files['document']
    picture = request.files['picture']

    existing_user = User.query.filter_by(email=email).first()
    existing_professional = Professional.query.filter_by(email=email).first()
    if existing_user or existing_professional:
        session['email_exists'] = True
        return redirect(url_for('professional_signup'))

    if file and file.filename.endswith('.pdf') and picture and picture.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        professional = Professional(
            email=email,
            password=password,
            fullname=fullname,
            service=p,
            experience=experience,
            document='',
            picture='',
            address=address,
            pincode=pincode
        )
        db.session.add(professional)
        db.session.commit()

        document_path = os.path.join(UPLOAD_FOLDER, f'{professional.id}.pdf')
        file.save(document_path)
        professional.document = f'{professional.id}.pdf'

        picture_path = os.path.join(UPLOAD_FOLDER, f'{professional.id}_picture.jpg')
        picture.save(picture_path)
        professional.picture = f'{professional.id}_picture.jpg'

        db.session.commit()

        return redirect(url_for('registration_success', role='professional', user_id=professional.id))

    session['message'] = 'Please upload a valid PDF document and a JPG image file.'
    return redirect(url_for('professional_signup'))

@app.route('/edit_professional_profile', methods=['GET', 'POST'])
def edit_professional_profile():
    professional_email = session.get('user_email')
    print(professional_email)
    if not professional_email:
        flash('Please log in to update your profile!', 'danger')
        return redirect(url_for('login'))

    professional = Professional.query.filter_by(email=professional_email).first()

    if not professional:
        flash('Professional not found, please log in again.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        professional_id = request.form['professional_id']
        full_name = request.form['fullname']
        service_id = request.form['service']
        experience = request.form['experience']
        address = request.form['address']
        pincode = request.form['pincode']

        professional.fullname = full_name
        professional.service = service_id
        professional.experience = experience
        professional.address = address
        professional.pincode = pincode

        db.session.commit()

        flash('Your professional profile has been updated successfully!', 'success')

        return redirect(url_for('professional_dashboard'))

    services = Service.query.all()
    return render_template('edit_professional_profile.html', professional=professional, services=services)

@app.route('/signup')
def create_account():
    email_exists = session.pop('email_exists', False)
    return render_template('signup.html', email_exists=email_exists)

@app.route('/signup', methods=['POST'])
def handle_register():
    email = request.form['email']
    password = request.form['password']
    fullname = request.form['fullname']
    address = request.form['address']
    pincode = request.form['pincode']

    existing_user = User.query.filter_by(email=email).first()
    existing_professional = Professional.query.filter_by(email=email).first()
    if existing_user or existing_professional:
        session['email_exists'] = True 
        return redirect(url_for('create_account'))

    user = User(
        email=email,
        password=password,
        fullname=fullname,
        address=address,
        pincode=pincode
    )
    db.session.add(user)
    db.session.commit()

    return redirect(url_for('registration_success', role='user', user_id=user.id))

@app.route('/registration_success')
def registration_success():
    role = request.args.get('role')
    user_id = request.args.get('user_id')
    return render_template('registration_success.html', role=role, user_id=user_id)

@app.route('/user_dashboard')
def user_dashboard():
    services = Service.query.all()
    user_email = session.get('user_email')
    user = User.query.filter_by(email=user_email).first()

    if not user:
        return redirect(url_for('login'))

    user_name = user.fullname
    user_id = user.id

    grouped_services = {}
    for service in services:
        category = service.service_name
        professionals = Professional.query.filter_by(service=service.id).all()
        
        if professionals: 
            if category not in grouped_services:
                grouped_services[category] = []
            grouped_services[category].append(service)
    service_requests = ServiceRequest.query.filter_by(user_id=user.id).all()
    user_services = []
    for req in service_requests:
        professional = Professional.query.get(req.professional_id) if req.professional_id else None
        user_services.append({
            "id": req.id,
            "name": req.service.service_name,
            "subtype": req.service.service_subtype,
            "date": req.booking_request_date,
            "professional_name": professional.fullname if professional else "Will be assigned shortly",
            "email": professional.email if professional else "N/A",
            "status": req.status.lower(),
            "rating": req.rating,
        })

    return render_template(
        'user_dashboard.html',
        user_name=user_name,
        grouped_services=grouped_services,
        user_services=user_services,
        user=user,
        user_id=user_id
    )

@app.route('/edit_profile', methods=['POST'])
def edit_profile():
    user_email = session.get('user_email')
    user = User.query.filter_by(email=user_email).first()

    if not user:
        return redirect(url_for('login'))

    user_id = request.form['user_id']
    full_name = request.form['fullname']
    email = request.form['email']
    address = request.form['address']
    pincode = request.form['pincode']

    user.fullname = full_name
    user.email = email
    user.address = address
    user.pincode = pincode

    db.session.commit()
    flash('Your profile has been updated successfully!', 'success')
    return redirect(url_for('user_dashboard'))

@app.route('/service_details/<category>')
def service_details(category):
    services = Service.query.filter_by(service_name=category).all()
    available_services = []
    for service in services:
        professionals = Professional.query.filter_by(service=service.id).all()
        if professionals: 
            available_services.append(service)
    
    user_id = request.args.get('user_id')
    if available_services:
        return render_template('service_details.html', service_name=category, services=available_services, user_id=user_id)
    else:
        return "No services found for this category", 404

@app.route('/book_service/<int:service_id>', methods=['GET', 'POST'])
def book_service(service_id):
    user_id = request.args.get('user_id')
    service_date = request.args.get('date') 
    service_time = request.args.get('time')

    if not user_id or not service_date or not service_time:
        return "User ID, Service Date, or Time is missing", 400

    try:
        service_datetime_str = f"{service_date} {service_time}"
        service_date_obj = datetime.strptime(service_datetime_str, "%Y-%m-%d %H:%M")
        booking_date = datetime.utcnow()
        new_request = ServiceRequest(
            user_id=user_id,
            service_id=service_id,
            booking_request_date=service_date_obj,
            booking_created_date=booking_date,
            status='Requested'
        )
        db.session.add(new_request)
        db.session.commit()

        booking_id = new_request.id
        return redirect(url_for('booking_confirmation', booking_id=booking_id))

    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD.", 400

@app.route('/booking_confirmation/<int:booking_id>')
def booking_confirmation(booking_id):
    booking = ServiceRequest.query.get_or_404(booking_id)
    service = Service.query.get_or_404(booking.service_id)
    prof_name = "Will be assigned shortly"
    if (booking.professional_id is not None):
        professionals = Professional.query.filter(Professional.id == booking.professional_id).all()
        prof_name = professionals[0].fullname
    
    return render_template(
        'booking_confirmation.html',
        booking_id=booking.id,
        professional_name = prof_name,
        service_id=service.id,
        service_name=service.service_name,
        service_subtype=service.service_subtype,
        booking_date=booking.booking_request_date,
        base_price=service.base_price
    )

@app.route('/professional_dashboard')
def professional_dashboard():
    professional_email = session.get('user_email')
    if not professional_email:
        return redirect(url_for('handle_login'))

    professional = Professional.query.filter_by(email=professional_email).first()
    if not professional:
        return redirect(url_for('login'))

    if professional.status != 'Approved':
        return render_template('professional_dashboard.html', 
                            professional_name=professional.fullname, 
                            professional=professional,
                            approval_pending=True)

    professional_service_id = professional.service 
    professional_service_subtype = professional.service_relation.service_subtype 

    open_services = ServiceRequest.query.filter(
        ServiceRequest.professional_id == None,
        ServiceRequest.status == 'Requested',
        ServiceRequest.service_id == professional_service_id, 
        ServiceRequest.service.has(Service.service_subtype == professional_service_subtype), 
        ~ServiceRequest.id.in_(db.session.query(RejectedServiceRequest.service_request_id).filter_by(professional_id=professional.id))  # Exclude rejected requests
    ).all()

    assigned_services = ServiceRequest.query.filter_by(professional_id=professional.id, status='Assigned').all()
    closed_services = ServiceRequest.query.filter_by(professional_id=professional.id, status='Closed').all()

    def service_to_dict(service_request):
        return {
            "id": service_request.id,
            "customer_name": service_request.user.fullname,
            "customer_email": service_request.user.email,
            "location": f"{service_request.user.address}, {service_request.user.pincode}",
            "name": service_request.service.service_name,
            "subtype": service_request.service.service_subtype,
            "pincode":  service_request.user.pincode,
            "date": service_request.booking_request_date.strftime("%Y-%m-%d %H:%M") if service_request.booking_request_date else "",
            "rating": service_request.rating if service_request.rating is not None else "N/A",
            "remark": service_request.remark if service_request.remark is not None else "N/A",
        }

    open_services = [service_to_dict(s) for s in open_services]
    assigned_services = [service_to_dict(s) for s in assigned_services]
    closed_services = [service_to_dict(s) for s in closed_services]

    return render_template(
        'professional_dashboard.html',
        professional_name=professional.fullname,
        professional=professional,
        open_services=open_services,
        assigned_services=assigned_services,
        closed_services=closed_services
    )

@app.route('/accept_service/<int:service_id>', methods=['POST'])
def accept_service(service_id):
    professional_email = session.get('user_email')
    if not professional_email:
        return redirect(url_for('handle_login'))

    professional = Professional.query.filter_by(email=professional_email).first()
    if not professional:
        return redirect(url_for('login'))

    service_request = ServiceRequest.query.filter_by(id=service_id, status='Requested', professional_id=None).first()
    if service_request:
        service_request.status = 'Assigned'
        service_request.professional_id = professional.id 
        db.session.commit()

    return redirect(url_for('professional_dashboard'))

@app.route('/reject_service/<int:service_id>', methods=['POST'])
def reject_service(service_id):
    professional_email = session.get('user_email')
    if not professional_email:
        return redirect(url_for('handle_login'))

    professional = Professional.query.filter_by(email=professional_email).first()
    if not professional:
        return redirect(url_for('login'))

    service_request = ServiceRequest.query.filter_by(id=service_id, status='Requested', professional_id=None).first()
    if service_request:
        rejected_entry = RejectedServiceRequest(professional_id=professional.id, service_request_id=service_request.id)
        db.session.add(rejected_entry)
        db.session.commit()

    return redirect(url_for('professional_dashboard'))

@app.route('/close_service/<int:service_id>', methods=['POST'])
def close_service(service_id):
    service = ServiceRequest.query.get(service_id)
    if service and service.status == 'Assigned':
        service.status = 'Closed'
        db.session.commit()
        flash('Service has been closed.', 'success')
    else:
        flash('Service not found or is already closed.', 'danger')
    return redirect(url_for('user_dashboard'))

@app.route('/cancel_service_request/<int:service_id>', methods=['POST'])
def cancel_service_request(service_id):
    service = ServiceRequest.query.get(service_id)
    if service and service.status != 'closed':
        service.status = 'Cancelled'
        db.session.commit()
        flash('Your service request has been cancelled.', 'success')
    else:
        flash('Unable to cancel the service request.', 'danger')
    return redirect(url_for('user_dashboard'))

def update_service_avg_rating(service_id):
    avg_rating = db.session.query(
        db.func.avg(ServiceRequest.rating)
    ).filter(
        ServiceRequest.service_id == service_id,
        ServiceRequest.rating.isnot(None)
    ).scalar()

    service = Service.query.get(service_id)
    if service:
        service.avg_rating = avg_rating
        db.session.commit()

@app.route('/rate_service/<int:service_id>', methods=['GET', 'POST'])
def rate_service(service_id):
    service_request = ServiceRequest.query.get(service_id)

    if not service_request:
        flash('Service request not found!', 'danger')
        return redirect(url_for('user_dashboard'))
    service = service_request.service
    professional = service_request.professional

    if request.method == 'POST':
        rating = request.form.get('rating') 
        remark = request.form.get('remarks')

        if(remark == ""):
            remark = "-"
        if not rating:
            flash('Please provide a rating!', 'danger')
            return redirect(url_for('rate_service', service_id=service_id))

        try:
            service_request.rating = int(rating)
            service_request.remark = remark
            db.session.commit()

            update_service_avg_rating(service_request.service_id)

            flash('Your rating and remarks have been submitted successfully!', 'success')
            return redirect(url_for('user_dashboard'))

        except Exception:
            db.session.rollback()
            flash('An error occurred while submitting your feedback. Please try again.', 'danger')
            return redirect(url_for('rate_service', service_id=service_id))

    return render_template(
        'rate_service.html',
        service_id=service_id,
        service_name=service.service_name,
        service_subtype=service.service_subtype,
        description=service.description,
        date=service_request.booking_request_date.strftime('%Y-%m-%d'),
        professional_id=professional.id if professional else 'N/A',
        professional_name=professional.fullname if professional else 'N/A',
        professional_email=professional.email if professional else 'N/A'
    )

@app.route('/admin_dashboard')
def admin_dashboard():
    services = Service.query.all()
    professionals = Professional.query.filter(Professional.status != 'deleted').all() 
    service_requests = ServiceRequest.query.all()
    users = User.query.all()
    services_list = []
    for req in service_requests:
        professional = Professional.query.get(req.professional_id) if req.professional_id else None
        services_list.append({
            "id": req.id,
            "user_id": req.user_id,
            "service_id": req.service_id,
            "req_date": req.booking_request_date,
            "professional_id": professional.id if professional else "Not assigned",
            "rating": req.rating,
            "remark": req.remark,
            "status": req.status,
        })

    return render_template('admin_dashboard.html', 
                        services=services, 
                        professionals=professionals,
                        users=users,
                        services_list=services_list)

@app.route('/approve_professional/<int:id>', methods=['POST'])
def approve_professional(id):
    professional = Professional.query.get(id)
    if professional:
        professional.status = 'Approved'
        db.session.commit()
        return '', 204 
    return 'Professional not found', 404

@app.route('/block_professional/<int:id>', methods=['POST'])
def block_professional(id):
    professional = Professional.query.get(id)
    if professional:
        professional.status = 'Blocked'
        db.session.commit()
        return '', 204 
    return 'Professional not found', 404

@app.route('/unblock_professional/<int:id>', methods=['POST'])
def unblock_professional(id):
    professional = Professional.query.get(id)
    if professional:
        professional.status = 'Approved'
        db.session.commit()
        return '', 204  
    return 'Professional not found', 404

@app.route('/reject_professional/<int:id>', methods=['POST'])
def reject_professional(id):
    professional = Professional.query.get(id)
    if professional:
        document_path = os.path.join(UPLOAD_FOLDER, professional.document)
        picture_path = os.path.join(UPLOAD_FOLDER, professional.picture)
        if os.path.exists(document_path):
            os.remove(document_path)
        if os.path.exists(picture_path):
            os.remove(picture_path)

        db.session.delete(professional)
        db.session.commit()
        return '', 204  
    return 'Professional not found', 404

@app.route('/get_professional_details/<int:id>')
def get_professional_details(id):
    professional = Professional.query.get(id)
    if professional:
        ser = Service.query.get(professional.service)
        rejected_service_count = db.session.query(
            db.func.count(RejectedServiceRequest.id).label('rejected_count')
        ).filter(RejectedServiceRequest.professional_id == id).scalar()
        document_url = url_for('static', filename=f'uploads/{professional.document}') if professional.document else None
        picture_url = url_for('static', filename=f'uploads/{professional.picture}') if professional.picture else None
        return jsonify({
            'id': professional.id,
            'email': professional.email,
            'fullname': professional.fullname,
            'service': professional.service,
            'ser_name': ser.service_name,
            'ser_sub': ser.service_subtype,
            'rejected_service_count': rejected_service_count,
            'experience': professional.experience,
            'address': professional.address,
            'pincode': professional.pincode,
            'status': professional.status,
            'document_url': document_url,
            'picture_url': picture_url
        })
    return jsonify({'error': 'Professional not found'}), 404

@app.route('/admin_search', methods=['GET', 'POST'])
def admin_search():
    search_results = None
    search_text = ''
    search_by = ''

    if request.method == 'POST':
        search_text = request.form.get('search_text').strip()
        search_by = request.form.get('search_by')

        if search_by == 'users':
            search_results = User.query.filter(
                User.fullname.ilike(f"%{search_text}%") | 
                User.pincode.ilike(f"%{search_text}%") | 
                User.address.ilike(f"%{search_text}%") | 
                User.email.ilike(f"%{search_text}%")
            ).all()

        elif search_by == 'professionals':
            search_results = Professional.query.filter(
                Professional.fullname.ilike(f"%{search_text}%") | 
                Professional.pincode.ilike(f"%{search_text}%") | 
                Professional.email.ilike(f"%{search_text}%")
            ).all()

        elif search_by == 'services':
            search_results = Service.query.filter(
                Service.service_name.ilike(f"%{search_text}%") | 
                Service.service_subtype.ilike(f"%{search_text}%") | 
                Service.description.ilike(f"%{search_text}%")
            ).all()

        elif search_by == 'service_requests':
            query = ServiceRequest.query.join(User, User.id == ServiceRequest.user_id)\
                                        .join(Professional, Professional.id == ServiceRequest.professional_id, isouter=True)\
                                        .join(Service, Service.id == ServiceRequest.service_id)
            
            if search_text:
                query = query.filter(
                    Professional.fullname.ilike(f"%{search_text}%") |  
                    User.pincode.ilike(f"%{search_text}%") | 
                    ServiceRequest.status.ilike(f"%{search_text}%") | 
                    ServiceRequest.booking_request_date.cast(String).ilike(f"%{search_text}%")
                )

            search_results = query.all()

    return render_template(
        'admin_search.html',
        search_results=search_results,
        search_text=search_text,
        search_by=search_by
    )

@app.route('/professional_search/<int:id>', methods=['GET', 'POST'])
def professional_search(id):
    search_results = None
    search_text = ''
    search_by = ''
    if request.method == 'POST':
        search_text = request.form.get('search_text').strip()
        search_by = request.form.get('search_by')

        if search_by == 'date':
            query = ServiceRequest.query.join(User, User.id == ServiceRequest.user_id)\
                                        .join(Professional, Professional.id == ServiceRequest.professional_id, isouter=True)
            query = query.filter(ServiceRequest.booking_request_date.cast(String).ilike(f"%{search_text}%"))
            search_results = query.filter(Professional.id == id).all()

        elif search_by == 'pincode':
            query = ServiceRequest.query.join(User, User.id == ServiceRequest.user_id)\
                                        .join(Professional, Professional.id == ServiceRequest.professional_id, isouter=True)\
                                        .join(Service, Service.id == ServiceRequest.service_id)
            
            query = query.filter(User.pincode.ilike(f"%{search_text}%"))
            query = query.filter(Professional.id == id)
            search_results = query.all()

        elif search_by == 'address':
            query = ServiceRequest.query.join(User, User.id == ServiceRequest.user_id)\
                                        .join(Professional, Professional.id == ServiceRequest.professional_id, isouter=True)\
                                        .join(Service, Service.id == ServiceRequest.service_id)
            
            query = query.filter(User.address.ilike(f"%{search_text}%"))
            query = query.filter(Professional.id == id)
            search_results = query.all()

        elif search_by == 'status':
            query = ServiceRequest.query.join(User, User.id == ServiceRequest.user_id)\
                                        .join(Professional, Professional.id == ServiceRequest.professional_id, isouter=True)
            query = query.filter(ServiceRequest.status.ilike(f"%{search_text}%"))
            search_results = query.filter(Professional.id == id).all()

    return render_template(
        'professional_search.html',
        id=id,
        search_results=search_results,
        search_text=search_text,
        search_by=search_by
    )

@app.route('/user_search/<int:id>', methods=['GET', 'POST'])
def user_search(id):
    search_results = None
    search_text = ''
    search_by = ''
    if request.method == 'POST':
        search_text = request.form.get('search_text').strip()
        search_by = request.form.get('search_by')

        if search_by == 'date':
            query = ServiceRequest.query.join(User, User.id == ServiceRequest.user_id)\
                                        .join(Professional, Professional.id == ServiceRequest.professional_id, isouter=True)\
                                        .join(Service, Service.id == ServiceRequest.service_id)
            query = query.filter(ServiceRequest.booking_request_date.cast(String).ilike(f"%{search_text}%"))
            search_results = query.filter(User.id == id).all()

        elif search_by == 'services':
            query = Service.query.filter(Service.service_name.ilike(f"%{search_text}%") | Service.service_subtype.ilike(f"%{search_text}%"))
            search_results = query.all()

        elif search_by == 'status':
            query = ServiceRequest.query.join(User, User.id == ServiceRequest.user_id)\
                                        .join(Professional, Professional.id == ServiceRequest.professional_id, isouter=True)
            query = query.filter(ServiceRequest.status.ilike(f"%{search_text}%"))
            search_results = query.filter(User.id == id).all()

    return render_template(
        'user_search.html',
        id=id,
        search_results=search_results,
        search_text=search_text,
        search_by=search_by
    )

@app.route('/admin_summary')
def admin_summary():
    avg_rating_data = Service.query.with_entities(
        Service.service_subtype,
        Service.avg_rating
    ).all()

    customer_data = {
        "labels": [row[0] for row in avg_rating_data],
        "datasets": [{
            "label": "Average Rating",
            "data": [round(row[1], 2) if row[1] is not None else 0 for row in avg_rating_data],
            "backgroundColor": ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0'],
        }]
    }

    avg_professional_rating_data = Professional.query.with_entities(
        Professional.fullname,
        db.func.avg(ServiceRequest.rating).label('avg_rating')
    ).outerjoin(ServiceRequest).filter(Professional.status == 'Approved').group_by(Professional.fullname).all()

    avg_professional_rating_data = {
        "labels": [row[0] for row in avg_professional_rating_data],
        "datasets": [{
            "label": "Average Rating",
            "data": [row[1] for row in avg_professional_rating_data],
            "backgroundColor": '#42A5F5',
        }]
    }

    professional_status_data = Professional.query.with_entities(
        Professional.status,
        db.func.count(Professional.id).label('count')
    ).group_by(Professional.status).all()

    professional_status_data = {
        "labels": [row[0] for row in professional_status_data],
        "datasets": [{
            "label": "Number of professionals",
            "data": [row[1] for row in professional_status_data],
            "backgroundColor": ['#FF6384', '#36A2EB', '#FFCE56'],
        }]
    }

    professionals_by_subcategory_data = Professional.query.with_entities(
        Service.service_subtype,
        db.func.count(Professional.id).label('count')
    ).join(Service).group_by(Service.service_subtype).all()

    professionals_by_subcategory_data = {
        "labels": [row[0] for row in professionals_by_subcategory_data],
        "datasets": [{
            "label": "Registered Professionals",
            "data": [row[1] for row in professionals_by_subcategory_data],
            "backgroundColor": ['#FF5733', '#33FF57', '#3357FF', '#F3F337'],
        }]
    }

    return render_template(
        'admin_summary.html',
        customer_data=json.dumps(customer_data),
        avg_professional_rating_data=json.dumps(avg_professional_rating_data),
        professional_status_data=json.dumps(professional_status_data),
        professionals_by_subcategory_data=json.dumps(professionals_by_subcategory_data)
    )

@app.route('/professional_summary')
def professional_summary():
    professional_email = session.get('user_email')

    if not professional_email:
        return redirect(url_for('login'))

    professional = Professional.query.filter_by(email=professional_email).first()

    if not professional:
        return redirect(url_for('login'))

    professional_id = professional.id

    avg_professional_rating_data = db.session.query(
        db.func.avg(ServiceRequest.rating).label('avg_rating')
    ).filter(
        ServiceRequest.professional_id == professional_id,
        ServiceRequest.rating.isnot(None)
    ).scalar()

    if avg_professional_rating_data is None:
        avg_professional_rating_data = 0

    avg_professional_rating_chart_data = {
        "labels": ["Your Average Rating", "Remaining"],
        "datasets": [{
            "label": "Average Rating",
            "data": [avg_professional_rating_data],
            "backgroundColor": ['#4CAF50'],  
        }]
    }

    service_request_status_data = db.session.query(
        ServiceRequest.status,
        db.func.count(ServiceRequest.id).label('count')
    ).filter(ServiceRequest.professional_id == professional_id).group_by(ServiceRequest.status).all()

    rejected_service_count = db.session.query(
        db.func.count(RejectedServiceRequest.id).label('rejected_count')
    ).filter(RejectedServiceRequest.professional_id == professional_id).scalar()

    status_dict = {row[0]: row[1] for row in service_request_status_data}
    if 'Rejected' not in status_dict:
        status_dict['Rejected'] = rejected_service_count

    service_request_status_chart_data = {
        "labels": list(status_dict.keys()),
        "datasets": [{
            "label": "Number of Service Requests",
            "data": list(status_dict.values()),
            "backgroundColor": ['#FF6384', '#36A2EB', '#FFCE56', '#FF5733'],
        }]
    }

    return render_template(
        'professional_summary.html',
        professional_id=professional_id,
        avg_professional_rating_chart_data=json.dumps(avg_professional_rating_chart_data),
        service_request_status_chart_data=json.dumps(service_request_status_chart_data),
    )

@app.route('/user_summary', methods=['GET'])
def user_summary():
    user_email = session.get('user_email')
    if not user_email:
        return "User not logged in", 401

    user = User.query.filter_by(email=user_email).first()
    if not user:
        return "User not found", 404
    id = user.id
    results = db.session.query(
        ServiceRequest.status, func.count(ServiceRequest.id)
    ).filter(
        ServiceRequest.user_id == user.id
    ).group_by(ServiceRequest.status).all()

    status_counts = {status: count for status, count in results}
    counts = {
        'Requested': status_counts.get('Requested', 0),
        'Closed': status_counts.get('Closed', 0),
        'Assigned': status_counts.get('Assigned', 0)
    }

    chart_data = {
        'labels': ['Requested', 'Closed', 'Assigned'],
        'datasets': [{
            'label': 'Service Requests',
            'data': [counts['Requested'], counts['Closed'], counts['Assigned']],
            'backgroundColor': ['#007bff', '#28a745', '#ffc107'],
            'borderColor': ['#0056b3', '#1e7e34', '#d39e00'],
            'borderWidth': 2
        }]
    }

    return render_template('user_summary.html', chart_data=json.dumps(chart_data), id=id)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully!'}), 200
    return jsonify({'message': 'User not found!'}), 404

@app.route('/add_service', methods=['POST'])
def add_service():
    data = request.get_json()
    service_name = data.get('service_name')
    description = data.get('description')
    base_price = data.get('base_price')
    service_subtype = data.get('service_subtype')

    new_service = Service(
        service_name=service_name,
        description=description,
        base_price=base_price,
        service_subtype = service_subtype
    )

    db.session.add(new_service)
    db.session.commit()

    return jsonify({"message": "Service added successfully!"}), 200

@app.route('/delete_service/<int:service_id>', methods=['DELETE'])
def delete_service(service_id):
    service = Service.query.get(service_id)
    if service: 
        db.session.delete(service)
        db.session.commit()
        return jsonify({'message': 'Service deleted successfully!'}), 200
    return jsonify({'message': 'Service not found!'}), 404

@app.route('/get_service_details/<int:service_id>', methods=['GET'])
def get_service_details(service_id):
    service = Service.query.get(service_id)
    if service:
        return jsonify({
            'id': service.id,
            'service_name': service.service_name,
            'description': service.description,
            'base_price': service.base_price,
            'service_subtype': service.service_subtype
        })
    return jsonify({'error': 'Service not found'}), 404

@app.route('/edit_service', methods=['POST'])
def edit_service():
    data = request.json 

    service_id = data.get('service_id')
    service_name = data.get('service_name')
    description = data.get('description')
    base_price = data.get('base_price')
    service_subtype = data.get('service_subtype')

    service = Service.query.get(service_id)
    if service:
        service.service_name = service_name
        service.description = description
        service.base_price = base_price
        service.service_subtype = service_subtype
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'error': 'Service not found'}), 404

@app.route('/get_service_details_with_professionals/<int:service_id>', methods=['GET'])
def get_service_details_with_professionals(service_id):
    service = Service.query.get(service_id)
    if not service:
        return jsonify({"error": "Service not found"}), 404

    professionals = Professional.query.filter_by(service=service.id).all()
    professionals_data = [{"id": p.id, "fullname": p.fullname} for p in professionals]

    return jsonify({
        "id": service.id,
        "service_name": service.service_name,
        "description": service.description,
        "base_price": service.base_price,
        "rating": service.avg_rating,
        "service_subtype": service.service_subtype,
        "professionals": professionals_data
    })

@app.route('/edit_service_req', methods=['POST'])
def edit_service_req():
    service_id = request.form['service_id']
    service = ServiceRequest.query.get(service_id)

    if service:
        service.name = request.form['name']
        service.subtype = request.form['subtype']
        service.professional_name = request.form['professional_name']
        service.email = request.form['email']
        service.booking_request_date = datetime.strptime(request.form['date'], "%Y-%m-%d %H:%M:%S")
        service.status = request.form['status'].title()

        db.session.commit()
        return redirect(url_for('user_dashboard'))

    return 'Service not found', 404

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(port=8000, debug=True)
