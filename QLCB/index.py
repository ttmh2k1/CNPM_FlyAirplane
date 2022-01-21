import math
from functools import wraps

import cloudinary
from cloudinary import uploader

from QLCB import app, login
from QLCB.models import *
from flask import request, render_template, redirect, session, url_for, flash, jsonify
from sqlalchemy import and_
from hashlib import sha256
import base64
from flask_login import current_user, login_user, login_required
from QLCB.adminis import *

@app.route('/')
def home():
    return redirect(url_for('homeCus'))

@app.route('/customer')
def homeCus():
    return render_template('/homeCus.html')

@app.route('/employee')
def homeEmp():
    return render_template('employee/homeEmp.html')

@login.user_loader
def load_usr(id):
    return Employees.query.get(int(id))

def login_customer_required(f):
    @wraps(f)
    def check(*args, **kwargs):
        if not session.get('customer_acc'):
            return redirect(url_for('login_customer', next=request.url))
        return f(*args, **kwargs)
    return check

def login_employee_required(f):
    @wraps(f)
    def check(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_employee', next=request.url))
        return f(*args, **kwargs)
    return check

@app.route('/login-admin', methods=['post'])
def login():
    if not current_user.is_authenticated or not current_user.role.roleName == "Admin":
        username = request.form.get('username')
        password = request.form.get('password')
        password = sha256((password + username).encode('utf-8')).hexdigest()
        admin_user = db.session.query(Employees).join(Roles).filter(and_(
            Employees.username == username,
            Employees.password == password,
            Roles.roleName == 'Admin')).first()
        if admin_user:
            login_user(admin_user)

        else:
            flash('Login failed', 'error')
    return redirect('/admin')

@app.route('/login-employee', methods=['post', 'get'])
def login_employee():
    if not current_user.is_authenticated:
        if request.method == 'GET':
            return render_template('employee/login.html')
        username = request.form.get('username')
        password = request.form.get('password')
        password = sha256((password + username).encode('utf-8')).hexdigest()
        employee_user = db.session.query(Employees).join(Roles).filter(and_(
            Employees.username == username,
            Employees.password == password)).first()
        if employee_user:
            login_user(employee_user)
        else:
            return render_template('employee/login.html', error="Login failed!", isEmp=True)
    return redirect(request.args.get('next') if request.args.get('next') else '/employee')

@app.route('/employee-fgPassword', methods=['post', 'get'])
def reset_employee_password():
    msg = ""
    err = ""
    if current_user.is_authenticated:
        return redirect(url_for('change_password_employee'))
    if request.method == "POST":
        employee = utils.get_employees(phone=request.form.get('phone'))
        if employee:
            if utils.employee_change_password(employee=employee, newpwd=request.form.get('password')):
                msg = "Reset password success!"
            else:
                err = "Something wrong! Please try again!"
        else:
            err = "Check your phone number!"
    return render_template('employee/forgetpw.html', msg=msg, isEmp=True, error=err)

@app.route('/fgPassword', methods=['post', 'get'])
def reset_password():
    msg = ""
    err = ""
    if session['customer_acc']:
        return redirect(url_for('change_password_customer'))
    if request.method == "POST":
        customer = utils.get_customers(phone=request.form.get('phone'))
        if customer:
            if utils.customer_change_password(customer=customer, newpwd=request.form.get('password')):
                msg = "Reset password success!"
            else:
                err = "Something wrong! Please try again!"
        else:
            err = "Check your phone number!"
    return render_template('forgetpw.html', msg=msg, error=err)


@app.route('/login', methods=['get', 'post'])
def login_customer():
    error = ""
    if request.method == 'POST':
        phone = request.form.get('phone')
        password = request.form.get('password')
        password = sha256((password + phone).encode('utf-8')).hexdigest()
        user = db.session.query(Customers).filter(and_(
            Customers.phone == phone,
            Customers.password == password)).first()
        if user: # nếu đăng nhập thành công
            session['customer_acc'] = {
                "id": user.id,
                "customerName": user.customerName,
            }
            return redirect(request.args.get('next', '/'))
        else:
            error = "Login failed!"
    else:
        if session.get('customer_acc'):
            return redirect('/')
    return render_template('/login.html', error=error)

@app.route('/signup', methods=['get','post'])
def signup():
    isSignup = True
    msg = ''
    err = ''
    if request.method == "POST":
        data = request.form.copy()
        del data['repassword']
        try:
            if utils.add_customer(**data):
                msg = "Signup success!"
            else:
                err = "Phone number is already exist!"
        except Exception as ex:
            print(ex.args)
            err = "Something wrong! Please try again!"
    return render_template('/login.html', isSignup=isSignup, err=err, msg=msg)

@app.route('/logout')
def logout_customer():
    session['customer_acc'] = None
    return redirect('/customer')

@app.route('/logout-employee')
def logout_employee():
    logout_user()
    return redirect('/employee')

@app.context_processor
def common_context():
    customer_acc = session.get('customer_acc')
    return {
        "customer_acc": customer_acc
}

@app.route('/flight-list', methods=['post', 'get'])
def show_flight():
    isEmp = request.args.get("isEmp")
    flights = utils.get_flights(start=int(request.form.get("start", 0)),
                                destination=int(request.form.get("destination", 0)),
                                page=request.args.get("page", 1),
                                takeOffTime=request.form.get("takeOffTime"))
    slots = {}
    for f in flights[0]:
        slots[f.id] = utils.get_slot_remain(f.id)

    page_num = math.ceil(flights[1] / app.config["PAGE_SIZE"])
    airport_name = utils.get_airports_name()

    return render_template('flight-list.html',
                           airport_name=airport_name,
                           flights=flights[0],
                           date_rule=utils.get_rules(name="MAX_DATE_ALLOWED_BOOKING_BEFORE_TAKEOFF").value,
                           page_num=page_num,
                           page_cur=request.args.get("page", 1),
                           isEmp=isEmp,
                           slots=slots)

@app.route('/manage-flight-route')
@login_employee_required
def route():
    flights = utils.get_flights(flew=True)
    return render_template('employee/manage-flight-route.html', isEmp=True, list_route=flights)

@app.route('/booking/<fid>', methods=['GET', 'POST'])
@login_employee_required
def book(fid):
    flight = utils.get_flights(id=fid)
    customers = utils.get_customers()
    error = ""
    msg = None
    if request.method == 'POST':
        no_business = int(request.form.get('noBusiness'))
        no_economy = int(request.form.get('noEconomy'))
        employee = current_user
        customer = utils.get_customers(request.form.get('cid'))
        pay_method = utils.get_pay_methods('Cash')
        if pay_method:
            if utils.add_booking(noEconomyClass=no_economy, noBusinessClass=no_business,
                                 customer=customer, employee=employee, flight=flight,
                                 pay_method=pay_method, orderKey=None, status=1):
                msg = "Booking Successful!"
            else:
                error="Something Wrong! Please try again!"
        else:
            error = "Payment method is unavailable!"
    slot = utils.get_slot_remain(fid=flight.id)
    cusJson = []
    for c in customers:
        cusJson.append({
            "id": c.id,
            "name": c.customerName,
            "phone": c.phone if c.phone else '',
            "idNo": c.idNo if c.idNo else ''
        })
    return render_template('booking.html',
                           customers=cusJson,
                           flight=flight,
                           slot=slot,
                           isEmp=True,
                           error=error,
                           msg=msg)

@app.route('/bookingOnline/<fid>', methods=['GET', 'POST'])
@login_customer_required
def book_online(fid):
    flight = utils.get_flights(id=fid)
    error = []
    msg = None

    if request.method == 'POST':
        amount = request.form.get('total')
        try:
            a = utils.payByMomo(totalPrice=str(amount), domain=request.root_url)
            if a['errorCode'] == 0:
                if utils.add_booking(noEconomyClass=int(request.form.get('noEconomy')),
                                     noBusinessClass=int(request.form.get('noBusiness')),
                                     customer=utils.get_customers(session.get('customer_acc')['id']),
                                     employee=None,
                                     flight=flight,
                                     pay_method=utils.get_pay_methods('Momo'),
                                     orderKey=a['orderId'],
                                     status=0):
                    return redirect(a['payUrl'])
            else:
                error.append(a['localMessage'])
        except Exception as ex:
            print(ex.args)
            error.append("Something wrong! Please try again!")

    slot = utils.get_slot_remain(fid)
    return render_template('/booking.html',
                           flight=flight,
                           slot=slot,
                           error=error,
                           msg=msg)

@app.route('/api/momo/notify', methods=['POST'])
def online_bill():
    errorCode = '99'
    if request.form.get('errorCode') == '0':
        orderId = request.form.get('orderId')
        book_detail = utils.get_book_detail(orderKey=orderId)
        if book_detail.status == 0:
            if utils.add_tickets(bookDetail=book_detail) and utils.paid_book_detail(book_detail=book_detail):
                errorCode = '0'
    return jsonify({
        'errorCode': errorCode
    })

@app.route('/momo/return')
def momo_return():
    msg = ''
    error = ''
    if request.args.get('errorCode') == '0':
        msg = 'Booking success!'
    else:
        error = 'Booking failed! Please try again!'
    return render_template('homeCus.html', msg=msg, error=error)

@app.route('/booking-history')
@login_customer_required
def book_history():
    customer = session['customer_acc']
    book_list = utils.get_book_detail(cid=customer['id'])
    return render_template('booking-history.html',
                    book_list=book_list)

@app.route('/flight-detail/<id>')
def schedule_customer(id):
    isEmp = request.args.get("isEmp")
    flight = utils.get_flights(id=id)
    slot = utils.get_slot_remain(id)
    stopovers = utils.get_stopover_detail(fid=id)
    return render_template('schedule.html',
                           flight=flight,
                           slot=slot,
                           isEmp=isEmp,
                           stopovers=stopovers)

@app.route('/manage-customer')
@login_employee_required
def manage_customer():
    customers = utils.get_customers()
    return render_template('/employee/manage-customer.html', isEmp=True, list_customer=customers)


@app.route('/add-customer', methods=['GET', 'POST'])
@login_employee_required
def add_customer():
    msg = ''
    err = ''
    if request.method == "POST":
        data = request.form.copy()
        try:
            if utils.add_customer(**data, password=data['phone']):
                msg = "Add customer success!"
            else:
                err = "Phone number is already exist!"
        except Exception as ex:
            print(ex.args)
            err = "Something wrong! Please try again!"
    return render_template('/employee/add-customer.html', isEmp=True, err=err, msg=msg)

@app.route('/changePwEmp', methods=['GET', 'POST'])
@login_employee_required
def change_password_employee():
    msg = ''
    err = ''
    if request.method == "POST":
        oldpwd = sha256((request.form.get('oldPassword') + current_user.username).encode('utf-8')).hexdigest()
        if oldpwd == current_user.password:
            if utils.employee_change_password(employee=current_user, newpwd=request.form.get('newPassword')):
                msg = 'Change password success!'
            else:
                err = 'Something wrong! Pleas try again!'
        else:
            err = 'Incorrect password!'
    return render_template('/changePw.html', isEmp=True, msg=msg, err=err)

@app.route('/changePw', methods=['GET', 'POST'])
@login_customer_required
def change_password_customer():
    msg = ''
    err = ''
    if request.method == "POST":
        cid = session['customer_acc']['id']
        customer = utils.get_customers(id=cid)
        oldpwd = sha256((request.form.get('oldPassword') + customer.phone).encode('utf-8')).hexdigest()
        if oldpwd == customer.password:
            if utils.customer_change_password(customer=customer, newpwd=request.form.get('newPassword')):
                msg = 'Change password success!'
            else:
                err = 'Something wrong! Pleas try again!'
        else:
            err = 'Incorrect password!'
    return render_template('/changePw.html', msg=msg, err=err)

@app.route('/profileEmp', methods=['post', 'get'])
@login_employee_required
def edit_employee_profile():
    mes = []
    if request.method == 'POST':
        data = request.form.copy()
        avatar = request.files['avatar']
        if avatar:
            info = cloudinary.uploader.upload(avatar)
            data['avatar'] = info['secure_url']
        else:
            data['avatar'] = None
        if utils.edit_employee(current_user, **data, error=mes):
            return redirect(url_for('edit_employee_profile'))
        else:
            if data['avatar']:
                cloudinary.uploader.destroy(info['public_id'])

    return render_template('employee/profileEmp.html', isEmp=True, mes=mes)

@app.route('/profile', methods=['post', 'get'])
@login_customer_required
def edit_customer_profile():
    customer_acc = session['customer_acc']
    id = customer_acc['id']
    error_info=[]
    error = ''
    if request.method == 'POST':
        data = request.form.copy()
        avatar = request.files['avatar']
        if avatar:
            info = cloudinary.uploader.upload(avatar)
            data['avatar'] = info['secure_url']
        else:
            data['avatar'] = None
        if utils.edit_customer(id, **data, error=error_info):
            return redirect(url_for('edit_customer_profile'))
        else:
            if data['avatar']:
                cloudinary.uploader.destroy(info['public_id'])
            if 'idNo' in error_info[0][0]:
                error = 'IdNo is already exist!'
            elif 'phone' in error_info[0][0]:
                error = 'Phone number is already exist!'
    customer = utils.get_customers(id)
    return render_template('/profile.html', customer=customer, err=error)


@app.route('/about-us')
def about_us():
    isEmp = request.args.get('isEmp')
    return render_template('/about-us.html', isEmp=isEmp)


if __name__ == '__main__':
    app.run(debug= True, host="0.0.0.0", port=5000)