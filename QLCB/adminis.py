from QLCB.models import Airports, Flights, Stopovers, StopoverDetails, Roles, Employees, BookDetails, PaymentMethods, \
    Customers, Tickets, TicketTypes, Rules
from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose, AdminIndexView
from flask_login import current_user, logout_user
from flask import redirect, flash, request
from sqlalchemy.sql import func
from QLCB import admin, db, app
from hashlib import sha256
from QLCB import utils
import json

class AuthenticatedModelView(ModelView):
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        return current_user.role.roleName == 'Admin'

class AuthenticatedBaseView(BaseView):
    def is_accessible(self):
        if not current_user.is_authenticated:
            return False
        return current_user.role.roleName == 'Admin'

class RoleModelView(AuthenticatedModelView):
    column_exclude_list = ('employees')
    form_excluded_columns = ('employees')
    column_labels = dict(roleName='Role name')

    can_view_details = True
    can_create = True

class EmployeeModelView(AuthenticatedModelView):
    column_exclude_list = ('bookDetails', 'password', 'avatar')
    form_excluded_columns = ('bookDetails', 'avatar')
    column_labels = dict(username='Username',
                         password='Password',
                         employeeName='Name',
                         email='Email',
                         gender='Gender',
                         age='Age',
                         dob='DOB',
                         role='Role')

    def on_model_change(self, form, model, is_created):
        model.password = sha256((model.password + model.username).encode('utf-8')).hexdigest()
    def on_form_prefill(self, form, id):
        form.password.data = ''

class CustomerModelView(AuthenticatedModelView):
    column_exclude_list = ('bookDetails', 'password', 'avatar')
    form_excluded_columns = ('bookDetails', 'avatar')
    column_labels = dict(customerName='Name',
                         password='Password',
                         phone='Phone',
                         gender='Gender',
                         age='Age',
                         idNo='ID Number',
                         address='Address',)

    def on_model_change(self, form, model, is_created):
        model.password = sha256((model.password + model.phone).encode('utf-8')).hexdigest()
    def on_form_prefill(self, form, id):
        form.password.data = ''

class FlightModelView(AuthenticatedModelView):
    column_exclude_list = ('bookDetails', 'stopover_flights')
    form_excluded_columns = ('bookDetails', 'stopover_flights')
    column_labels = dict(takeOffTime='Take off time',
                         flightTime='Flight time(mins)',
                         noBusinessClass='Number of Business Class',
                         noEconomyClass='Number of Economy Class',
                         priceBusinessClass='Price of Business Class',
                         priceEconomyClass='Price of Economy Class',
                         startAirport='Departure airport',
                         destinationAirport='Arrival airport')

    def create_model(self, form):
        if form.flightTime.data < utils.get_rules(name="MIN_FLIGHT_TIME").value:
            flash('The minimum allowed flight time is ' + str(utils.get_rules(name="MIN_FLIGHT_TIME").value) + ' mins',
                  'error')
            return False
        return super().create_model(form)


    def update_model(self, form, model):
        if form.flightTime.data < utils.get_rules(name="MIN_FLIGHT_TIME").value:
            flash('The minimum allowed flight time is ' + str(utils.get_rules(name="MIN_FLIGHT_TIME").value) + ' mins',
                  'error')
            return False
        else:
            return super().update_model(form, model)

class AirportModelView(AuthenticatedModelView):
    column_exclude_list = ('outcommingFlights', 'incommingFlights')
    form_excluded_columns = ('outcommingFlights', 'incommingFlights')
    column_labels = dict(airportName='Airport name',
                         airportAddress='Airport address')

class StopoverModelView(AuthenticatedModelView):
    column_exclude_list = ('stopover_flights')
    form_excluded_columns = ('stopover_flights')
    column_labels = dict(stopoverName='Stopover name',
                         stopoverAddress='Stopover address')

class StopoverDetailModelView(AuthenticatedModelView):
    column_labels = dict(flight='Flight',
                         stopover='Stopover',
                         stopoverTime='Stopover time(mins)',
                         description='Description')

    def create_model(self, form):
        if form.stopoverTime.data > utils.get_rules(name="MAX_TIME_STOPOVER_PER_FLIGHT").value or form.stopoverTime.data < utils.get_rules(name="MIN_TIME_STOPOVER_PER_FLIGHT").value:
            flash('The maximum allowed flight time is from ' +
                  str(utils.get_rules(name="MIN_TIME_STOPOVER_PER_FLIGHT").value) + ' to ' +
                  str(utils.get_rules(name="MAX_TIME_STOPOVER_PER_FLIGHT").value) + ' mins',
                  'error')
            return False

        l = utils.get_rules(name="MAX_STOPOVER_PER_FLIGHT").value
        c = db.session.query(func.count(StopoverDetails.idFlight)).filter(
            StopoverDetails.idFlight == form.flight.data.id).scalar()
        if c >= l:
            flash('This flight has reached the maximum of ' + str(l) + ' intermediate flights', 'error')
            return False
        else:
            return super().create_model(form)

    def update_model(self, form, model):
        if form.stopoverTime.data > utils.get_rules(name="MAX_TIME_STOPOVER_PER_FLIGHT").value:
            flash('The maximum allowed flight time is ' + str(utils.get_rules("MAX_TIME_STOPOVER_PER_FLIGHT").value) + ' mins', 'error')
            return False
        elif form.stopoverTime.data < utils.get_rules(name="MIN_TIME_STOPOVER_PER_FLIGHT").value:
            flash('The minimum allowed flight time is ' + str(utils.get_rules("MIN_TIME_STOPOVER_PER_FLIGHT").value) + ' mins', 'error')
            return False
        else:
            return super().update_model(form, model)


class BookDetailModelView(AuthenticatedModelView):
    column_exclude_list = ('tickets')
    form_excluded_columns = ('tickets')
    column_labels = dict(bookTime='Book time',
                         noBusinessClass='Number of business class tickets',
                         noEconomyClass='Number of economy class tickets',
                         employee='Employee',
                         customer='Customer',
                         flight='Flight',
                         paymentMethod='Payment method')

    def create_model(self, form):
        if form.noBusinessClass.data == 0 and form.noEconomyClass.data == 0:
            flash('The total number of tickets must be more than 0', 'error')
            return False

        l = utils.get_rules(name="MAX_DATE_ALLOWED_BOOKING_BEFORE_TAKEOFF").value
        if (form.flight.data.takeOffTime.date() - form.bookTime.data.date()).days < l:
            flash(
                'This flight cannot be booked because the flight has already taken off/reservation must be made prior to departure date ' + str(l) + ' day',
                'error')
            return False

        c = db.session.query(func.sum(BookDetails.noBusinessClass),
                             func.sum(BookDetails.noEconomyClass)).filter(
            BookDetails.idFlight == form.flight.data.id).one()

        remain_noBusinessClass = form.flight.data.noBusinessClass - (c[0] if c[0] else 0)
        remain_noEconomyClass = form.flight.data.noEconomyClass - (c[1] if c[1] else 0)

        if remain_noBusinessClass == 0 and remain_noEconomyClass == 0:
            flash('Flight ' + str(form.flight.data.id) + ' is sold out', 'error')
        elif form.noBusinessClass.data > remain_noBusinessClass or form.noEconomyClass.data > remain_noEconomyClass :
            flash('The number of tickets booked is larger than the number of tickets available for the flight (Flight ' + str(form.flight.data.id)
                  + ' left ' + str(remain_noBusinessClass) + ' Business class tickets and ' + str(remain_noEconomyClass) + ' Economy class tickets)', 'error')
        else:
            ret = super().create_model(form)
            try:
                for i in range(0, ret.noBusinessClass):
                    t = Tickets(price=ret.flight.priceBusinessClass, idType=1, idBookDetail=ret.id)
                    db.session.add(t)
                for i in range(0, ret.noEconomyClass):
                    t = Tickets(price=ret.flight.priceEconomyClass, idType=2, idBookDetail=ret.id)
                    db.session.add(t)
                db.session.commit()
            except Exception as ex:
                flash('Error creating ticket: ' + str(ex), 'error')
                db.session.rollback()
            return ret

    def update_model(self, form, model):
        if form.noBusinessClass.data == 0 and form.noEconomyClass.data == 0:
            flash('The total number of tickets must be more than 0', 'error')
            return False

        db.session.delete(model)
        model = self.create_model(form)
        if model == None:
            db.session.rollback()
            return False
        return True

class TicketTypeModelView(AuthenticatedModelView):
    column_exclude_list = ('tickets')
    form_excluded_columns = ('tickets')
    column_labels = dict(typeName='Type name')

class TicketModelView(AuthenticatedModelView):
    form_excluded_columns = ('price')
    column_labels = dict(price='Price',
                         ticketType='Ticket type',
                         bookDetail='Book detail')
    def on_model_change(self, form, model, is_created):
        model.price = sha256((model.password + model.phone).encode('utf-8')).hexdigest()
    can_delete = False
    can_create = False
    can_edit = False

class PaymentMethodModelView(AuthenticatedModelView):
    column_exclude_list = ('bookDetails')
    form_excluded_columns = ('bookDetails')
    column_labels = dict(PMethodName='Payment method name',
                         description='Description')

class ReportView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        year = request.args.get('year')
        other = request.args.get('other')
        if year and other == 'month':
            revenue_report = utils.report_monthOfYear(year=int(year))
            ticket_report = utils.report_tickets_months(year=int(year))
            chartName = "Monthly statistics of " + year
        elif year and other == 'quarter':
            revenue_report = utils.report_quarterOfYear(year=int(year))
            ticket_report = utils.report_tickets_quarter(year=int(year))
            chartName = "Quarter statistics of " + year
        else:
            revenue_report = utils.report_allYear()
            ticket_report = utils.report_tickets_year()
            chartName = "Statistics by all year"

        reveue_labels = list(data[0] for data in revenue_report)

        revenue_data = list(data[1] for data in revenue_report)

        ticket = {}
        ticket_labels = []
        for i in ticket_report:
            try:
                if not i[0] in ticket_labels:
                    ticket_labels.append(i[0])
                ticket[i[1]].append(i[2])
            except:
                ticket[i[1]] = [i[2]]
        print(ticket)
        ticket_data = list(ticket.values())
        ticket_type = list(ticket.keys())

        workYear = utils.getYear()

        return self.render('admin/report.html',
                           revenue_labels=json.dumps(reveue_labels),
                           ticket_labels=json.dumps(ticket_labels),
                           revenue_data=json.dumps(revenue_data),
                           ticket_data=json.dumps(ticket_data),
                           ticket_type=json.dumps(ticket_type),
                           workYear=workYear,
                           chartName=json.dumps(chartName)
                           )

class LogoutView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/admin')

class RuleModelView(AuthenticatedModelView):
    pass

admin.add_view(RoleModelView(Roles, db.session, name='Roles'))
admin.add_view(EmployeeModelView(Employees, db.session, name='Employees'))
admin.add_view(CustomerModelView(Customers, db.session, name='Customers'))
admin.add_view(RuleModelView(Rules, db.session, name='Rules'))
admin.add_view(AirportModelView(Airports, db.session, name='Airports'))
admin.add_view(FlightModelView(Flights, db.session, name='Flights'))
admin.add_view(StopoverModelView(Stopovers, db.session, name='Stopovers'))
admin.add_view(StopoverDetailModelView(StopoverDetails, db.session, name='Stopover details'))
admin.add_view(BookDetailModelView(BookDetails, db.session, name='Book details'))
admin.add_view(TicketTypeModelView(TicketTypes, db.session, name='Ticket types'))
admin.add_view(TicketModelView(Tickets, db.session, name='Tickets'))
admin.add_view(PaymentMethodModelView(PaymentMethods, db.session, name='Payment'))
admin.add_view(ReportView(name="Report"))
admin.add_view(LogoutView(name="Log out"))
