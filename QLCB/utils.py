import hmac
import json
import uuid
from datetime import datetime
from urllib.request import urlopen, Request

from pymysql import Date
from sqlalchemy import func, extract

from QLCB.models import BookDetails, Tickets, Flights, TicketTypes, Airports, PaymentMethods, Employees, Customers, \
    Stopovers, StopoverDetails, Rules
from QLCB import db, app
from flask_login import current_user
from hashlib import sha256

# Các năm
def report_allYear():
    report = db.session.query(extract('year', BookDetails.bookTime), func.sum(Tickets.price)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .group_by(extract('year', BookDetails.bookTime)).all()

    return report

# tháng trong năm
def report_monthOfYear(year):
    report = db.session.query(extract('month', BookDetails.bookTime), func.sum(Tickets.price)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .filter(extract('year', BookDetails.bookTime) == year)\
        .group_by(extract('month', BookDetails.bookTime)).all()

    month = []
    for i in range(1, 13):
        month.append((i, 0))
    for i in report:
        month[i[0] - 1] = i

    return month

def report_quarterOfYear(year):
    report = db.session.query(extract('quarter', BookDetails.bookTime), func.sum(Tickets.price)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .filter(extract('year', BookDetails.bookTime) == year)\
        .group_by(extract('quarter', BookDetails.bookTime)).all()

    quarter = [(1, 0), (2, 0), (3, 0), (4, 0)]
    for i in report:
        quarter[i[0] - 1] = i

    return quarter

def report_tickets_year():
    report = db.session.query(extract('year', BookDetails.bookTime), TicketTypes.typeName, func.count(Tickets.id)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .join(TicketTypes,
              Tickets.idType == TicketTypes.id)\
        .group_by(extract('year', BookDetails.bookTime),
                  Tickets.idType,
                  TicketTypes.typeName)\
        .order_by(extract('year', BookDetails.bookTime), Tickets.idType).all()

    return report

def report_tickets_months(year):
    report = db.session.query(extract('month', BookDetails.bookTime), TicketTypes.typeName, func.count(Tickets.id)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .join(TicketTypes,
              Tickets.idType == TicketTypes.id)\
        .filter(extract('year', BookDetails.bookTime) == year)\
        .group_by(extract('month', BookDetails.bookTime),
                  Tickets.idType,
                  TicketTypes.typeName)\
        .order_by(extract('month', BookDetails.bookTime), Tickets.idType).all()

    return report

def report_tickets_quarter(year):
    report = db.session.query(extract('quarter', BookDetails.bookTime), TicketTypes.typeName, func.count(Tickets.id)) \
        .join(BookDetails,
              Tickets.idBookDetail == BookDetails.id) \
        .join(TicketTypes,
              Tickets.idType == TicketTypes.id)\
        .filter(extract('year', BookDetails.bookTime) == year)\
        .group_by(extract('quarter', BookDetails.bookTime),
                  Tickets.idType,
                  TicketTypes.typeName)\
        .order_by(extract('quarter', BookDetails.bookTime), Tickets.idType).all()

    return report

def getYear():
    query = db.session.query(BookDetails.bookTime)
    date = [row[0] for row in query.all()]
    year = set([i.year for i in date])
    return year

def get_ticket_types():
    return TicketTypes.query.all()

def get_flights(start=None, destination=None, page=None, id=None, flew=False, takeOffTime=None):
    flights = Flights.query
    if id:
        return flights.get(id)

    if not flew:
        today = Date.today()
        flights = flights.filter(Flights.takeOffTime > today)
    if start:
        flights = flights.filter(Flights.idStartAirport == start)
    if destination:
        flights = flights.filter(Flights.idDestinationAirport == destination)

    if takeOffTime:
        from datetime import datetime
        takeOffTime = datetime.strptime(takeOffTime, '%Y-%m-%d')
        flights = flights.filter(extract('day', Flights.takeOffTime) == takeOffTime.day,
                                 extract('month', Flights.takeOffTime) == takeOffTime.month,
                                 extract('year', Flights.takeOffTime) == takeOffTime.year)

    flights = flights.order_by(Flights.takeOffTime)

    if page:
        size = app.config["PAGE_SIZE"]
        start = (int(page)-1)*size
        end = start + size
        return flights.all()[start:end], len(flights.all())
    return flights.all()

def get_airports_name():
    return Airports.query.with_entities(Airports.airportName, Airports.id).all()


def count_flights():
    return Flights.query.count()


def add_booking(noBusinessClass, noEconomyClass, customer, employee, flight, pay_method, orderKey, status):
    import datetime
    bookTime = datetime.datetime.now()
    b = BookDetails(noBusinessClass=noBusinessClass, noEconomyClass=noEconomyClass,
                    bookTime=bookTime, customer=customer, employee=employee,
                    flight=flight, paymentMethod=pay_method,
                    orderKey=orderKey, status=status)
    db.session.add(b)
    if status == 0:
        try:
            db.session.commit()
            return True
        except:
            return False
    else:
        billAdd = False
        try:
            billAdd = True
            return add_tickets(bookDetail=b)
        except Exception as ex:
            db.session.rollback()
            if billAdd:
                db.session.delete(b)
                db.session.commit()
            print(ex.args)
            return False

def add_tickets(bookDetail):
    try:
        for i in range(0, bookDetail.noBusinessClass):
            t = Tickets(price=bookDetail.flight.priceBusinessClass, idType=1, bookDetail=bookDetail)
            db.session.add(t)
        for i in range(0, bookDetail.noEconomyClass):
            t = Tickets(price=bookDetail.flight.priceEconomyClass, idType=2, bookDetail=bookDetail)
            db.session.add(t)
        db.session.commit()
        return True
    except Exception as ex:
        print(ex.args)
        return False


def payByMomo(totalPrice, domain):
    # domain = 'http://14.160.134.135:65001/'
    endpoint = "https://test-payment.momo.vn/gw_payment/transactionProcessor"
    partnerCode = "MOMO544Q20211126"
    accessKey = "FoblaCbnWl9gdHeg"
    serectkey = "8QCHW2eoJJWhZU6TJp0L2dKlngawMaP8"
    orderInfo = "Thanh toán vé máy bay "
    returnUrl = domain + 'momo/return'
    notifyurl = domain + 'api/momo/notify'
    amount = totalPrice
    orderId = str(uuid.uuid4())
    requestId = str(uuid.uuid4())
    requestType = "captureMoMoWallet"
    extraData = "merchantName=;merchantId="  # pass empty value if your merchant does not have stores else merchantName=[storeName]; merchantId=[storeId] to identify a transaction map with a physical store
    # before sign HMAC SHA256 with format
    # partnerCode=$partnerCode&accessKey=$accessKey&requestId=$requestId&amount=$amount&orderId=$oderId&orderInfo=$orderInfo&returnUrl=$returnUrl&notifyUrl=$notifyUrl&extraData=$extraData
    rawSignature = "partnerCode=" + partnerCode + "&accessKey=" + accessKey + "&requestId=" + requestId + "&amount=" + amount + "&orderId=" + orderId + "&orderInfo=" + orderInfo + "&returnUrl=" + returnUrl + "&notifyUrl=" + notifyurl + "&extraData=" + extraData
    h = hmac.new(bytes(serectkey, 'utf-8'), rawSignature.encode('utf8'), sha256)
    signature = h.hexdigest()
    data = {
        'partnerCode': partnerCode,
        'accessKey': accessKey,
        'requestId': requestId,
        'amount': amount,
        'orderId': orderId,
        'orderInfo': orderInfo,
        'returnUrl': returnUrl,
        'notifyUrl': notifyurl,
        'extraData': extraData,
        'requestType': requestType,
        'signature': signature
    }
    data = json.dumps(data).encode('utf-8')
    clen = len(data)
    req = Request(endpoint, data, {'Content-Type': 'application/json', 'Content-Length': clen})
    f = urlopen(req)
    response = f.read()
    f.close()
    return json.loads(response)


def add_customer(name, phone, password, dob=None, gender=None, idNo=None, address=None):
    password = sha256((password + phone).encode('utf-8')).hexdigest()
    customer = Customers(customerName=name, phone=phone, password=password,
                         dob=dob if dob else None, gender=gender,
                         idNo=idNo if idNo else None,
                         address=address if address else None)
    db.session.add(customer)
    try:
        db.session.commit()
        return True
    except Exception as ex:
        db.session.rollback()
        print(ex.args)
        return False

def get_customers(id=None, phone=None):
    customers = Customers.query
    if id:
        return customers.get(int(id))
    if phone:
        return customers.filter(Customers.phone == phone).first()
    return customers.all()

def edit_customer(id, name, dob, gender, idNo, phone, address, avatar, error):
    customer = get_customers(id)
    customer.customerName = name
    customer.dob = dob if dob else None
    customer.gender = gender
    customer.idNo = idNo if idNo else None
    customer.phone = phone
    customer.address = address if address else None
    customer.avatar = avatar if avatar else customer.avatar
    try:
        db.session.commit()
    except Exception as ex:
        error.append(ex.args)
        db.session.rollback()
        return False
    return True

def get_employees(id=None, phone = None):
    employees = Employees.query
    if id:
        return employees.get(int(id))
    if phone:
        return employees.filter(Employees.phone == phone).first()
    return employees.all()

def edit_employee(employee, username, employeeName, dob, gender, idNo, email, phone, address, avatar, error):
    employee.username = username
    employee.employeeName = employeeName
    employee.dob = dob if dob else None
    employee.gender = gender
    employee.idNo = idNo if idNo else None
    employee.email = email if email else None
    employee.phone = phone if phone else None
    employee.address = address if address else None
    employee.avatar = avatar if avatar else employee.avatar
    try:
        db.session.commit()
    except Exception as ex:
        error.append(ex.args)
        db.session.rollback()
        return False
    return True

def get_pay_methods(name=None):
    pm = PaymentMethods.query
    if name:
        return pm.filter(PaymentMethods.PMethodName == name).first()
    return pm.all()

def get_book_detail(id = None, orderKey = None, cid= None):
    book_details = BookDetails.query
    if id:
        return BookDetails.query.get(id)
    if orderKey:
        return book_details.filter(BookDetails.orderKey == orderKey).first()
    if cid:
        book_details = book_details.filter(BookDetails.idCustomer == cid)
    return book_details.all()

def get_stopover_detail(fid = None):
    sd = StopoverDetails.query
    if fid:
        sd = sd.filter(StopoverDetails.idFlight == fid)
    return sd.all()

def get_tickets(cid=None):
    tickets = Tickets.query
    if cid:
        tickets = tickets.filter(Tickets.id)
    return tickets.all()

def get_slot_remain(fid):
    b, e = db.session.query(func.sum(BookDetails.noBusinessClass),
                         func.sum(BookDetails.noEconomyClass))\
        .filter(BookDetails.idFlight == fid, BookDetails.status == 1).first()
    return {
        "economy": e if e else 0,
        "business": b if b else 0
    }

def paid_book_detail(book_detail):
    try:
        book_detail.status = 1
        db.session.add(book_detail)
        db.session.commit()
        return True
    except Exception as ex:
        print(ex.args)
        return False

def add_ticket_type(name):
    ticket_type = TicketTypes(typeName=name)
    db.session.add(ticket_type)
    try:
        db.session.commit()
    except Exception as ex:
        print(ex.args)

def customer_change_password(customer, newpwd):
    newpwd = sha256((newpwd + customer.phone).encode('utf-8')).hexdigest()
    customer.password = newpwd
    db.session.add(customer)
    try:
        db.session.commit()
        return True
    except Exception as ex:
        print(ex.args)
        return False

def employee_change_password(employee, newpwd):
    newpwd = sha256((newpwd + employee.username).encode('utf-8')).hexdigest()
    employee.password = newpwd
    db.session.add(employee)
    try:
        db.session.commit()
        return True
    except Exception as ex:
        print(ex.args)
        return False

def get_rules(id=None, name=None):
    rules = Rules.query
    if name:
        return rules.filter(Rules.ruleName == name).first()
    if id:
        return rules.get(id)