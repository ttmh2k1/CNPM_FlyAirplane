from QLCB import db
from sqlalchemy import Column, Integer, String, Float, ForeignKey, NVARCHAR, DateTime, Date
from sqlalchemy.orm import relationship
from flask_login import UserMixin

class Roles(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    roleName = Column(NVARCHAR(100), nullable=False)

    employees = relationship('Employees', backref='role', lazy=True)

    def __str__(self):
        return self.roleName

class Employees(db.Model, UserMixin):
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, unique=True)
    employeeName = Column(NVARCHAR(100), nullable=False)
    dob = Column(Date)
    gender = Column(String(10))
    idNo = Column(String(100), unique=True)
    email = Column(String(100), unique=True)
    phone = Column(String(10), unique=True, nullable=False)
    password = Column(String(64), nullable=False)
    address = Column(NVARCHAR(200))
    avatar = Column(String(100))
    idRole = Column(Integer, ForeignKey(Roles.id), nullable=False)

    bookDetails = relationship('BookDetails', backref='employee', lazy=True)

    def __str__(self):
        return self.employeeName

class Customers(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    customerName = Column(NVARCHAR(100), nullable=False)
    dob = Column(Date)
    gender = Column(String(10))
    idNo = Column(String(100), unique=True)
    phone = Column(String(10), unique=True, nullable=False)
    password = Column(String(64), nullable=False)
    address = Column(NVARCHAR(200))
    avatar = Column(String(100))

    bookDetails = relationship('BookDetails', backref='customer', lazy=True)

    def __str__(self):
        return self.customerName

class Airports(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    airportName = Column(NVARCHAR(100), nullable=False)
    airportAddress = Column(NVARCHAR(200), nullable=False)

    def __str__(self):
        return 'Airport ' + self.airportName

class Stopovers(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    stopoverName = Column(NVARCHAR(100), nullable=False)
    stopoverAddress = Column(NVARCHAR(100), nullable=False)

    stopover_flights = relationship('StopoverDetails', backref='stopover', lazy=True)

    def __str__(self):
        return 'Intermediate airport ' + self.stopoverName

class Flights(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    takeOffTime = Column(DateTime, nullable=False)
    flightTime = Column(Float, nullable=False)
    noBusinessClass = Column(Integer, nullable=False)
    noEconomyClass = Column(Integer, nullable=False)

    priceBusinessClass = Column(Float, nullable=False)
    priceEconomyClass = Column(Float, nullable=False)

    idStartAirport = Column(Integer, ForeignKey(Airports.id), nullable=False)
    idDestinationAirport = Column(Integer, ForeignKey(Airports.id), nullable=False)

    startAirport = relationship('Airports', backref='outcommingFlights', foreign_keys=[idStartAirport], lazy=True)
    destinationAirport = relationship('Airports', backref='incommingFlights', foreign_keys=[idDestinationAirport], lazy=True)

    bookDetails = relationship('BookDetails', backref='flight', lazy=True)
    stopover_flights = relationship('StopoverDetails', backref='flight', lazy=True)

    def __str__(self):
        return 'Id flight ' + str(self.id)

class StopoverDetails(db.Model):
    idStopover = Column(Integer, ForeignKey(Stopovers.id), primary_key=True)
    idFlight = Column(Integer, ForeignKey(Flights.id), primary_key=True)
    stopoverTime = Column(Float, nullable=False)
    description = Column(NVARCHAR(200))

    def __str__(self):
        return 'Flight ' + str(self.idFlight) + ' - ' + str(self.stopover)

class PaymentMethods(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    PMethodName = Column(NVARCHAR(100), nullable=False)
    description = Column(NVARCHAR(100))

    bookDetails = relationship('BookDetails', backref='paymentMethod', lazy=True)

    def __str__(self):
        return self.PMethodName

class BookDetails(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    bookTime = Column(DateTime, nullable=False)
    noBusinessClass = Column(Integer, nullable=False)
    noEconomyClass = Column(Integer, nullable=False)

    idFlight = Column(Integer, ForeignKey(Flights.id), nullable=False)
    idCustomer = Column(Integer, ForeignKey(Customers.id), nullable=False)
    idEmployee = Column(Integer, ForeignKey(Employees.id))
    idPMethod = Column(Integer, ForeignKey(PaymentMethods.id), nullable=False)
    status = Column(Integer, default=1)
    orderKey = Column(NVARCHAR(100), unique=True)

    tickets = relationship('Tickets', cascade="all,delete", backref='bookDetail', lazy=True)

    def __str__(self):
        return 'Booking code: ' + str(self.id) + ' - Customer: ' + self.customer.customerName

class TicketTypes(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    typeName = Column(NVARCHAR(100), nullable=False)

    tickets = relationship('Tickets', backref='ticketType', lazy=True)

    def __str__(self):
        return self.typeName

class Tickets(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    price = Column(Float)
    idType = Column(Integer, ForeignKey(TicketTypes.id), nullable=False)
    idBookDetail = Column(Integer, ForeignKey(BookDetails.id), nullable=False)

class Rules(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    ruleName = Column(NVARCHAR(100), nullable=False)
    value = Column(Integer)
    description = Column(NVARCHAR(100))

    def __str__(self):
        return self.ruleName

if __name__ == '__main__':
    db.create_all()

    db.session.add(TicketTypes(typeName="Business Class"))
    db.session.add(TicketTypes(typeName="Economy Class"))

    db.session.add(Rules(ruleName="MIN_FLIGHT_TIME",value=30))
    db.session.add(Rules(ruleName="MAX_STOPOVER_PER_FLIGHT",value=2))
    db.session.add(Rules(ruleName="MIN_TIME_STOPOVER_PER_FLIGHT",value=10))
    db.session.add(Rules(ruleName="MAX_TIME_STOPOVER_PER_FLIGHT",value=20))
    db.session.add(Rules(ruleName="MAX_DATE_ALLOWED_BOOKING_BEFORE_TAKEOFF",value=1))

    try:
        db.session.commit()
    except Exception as ex:
        print(ex.args)


