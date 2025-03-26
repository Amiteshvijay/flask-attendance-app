from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime, date
from models import db, Employee, Attendance  # ✅ Single import of db & models

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yoursecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  # ✅ Proper way to bind db with Flask

# ------------------------------
# Routes
# ------------------------------
@app.route('/')
def home():
    total_employees = Employee.query.count()

    today = date.today()
    today_attendance = Attendance.query.filter_by(date=today).all()

    clocked_in = len([a for a in today_attendance if a.clock_in_time])
    clocked_out = len([a for a in today_attendance if a.clock_out_time])

    return render_template(
        'home.html',
        total_employees=total_employees,
        clocked_in=clocked_in,
        clocked_out=clocked_out,
        today=today
    )

@app.route('/employees')
def employee_list():
    employees = Employee.query.all()
    return render_template('employees.html', employees=employees)

@app.route('/employees/new', methods=['POST'])
def create_employee():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')
    department = request.form.get('department')
    salary = request.form.get('salary', 0)

    if not (first_name and last_name and email):
        flash("Please fill in required fields.")
        return redirect(url_for('employee_list'))

    existing_employee = Employee.query.filter_by(email=email).first()
    if existing_employee:
        flash("Employee with this email already exists.")
        return redirect(url_for('employee_list'))

    new_employee = Employee(
        first_name=first_name,
        last_name=last_name,
        email=email,
        department=department,
        salary=float(salary or 0)
    )
    db.session.add(new_employee)
    db.session.commit()
    flash("Employee added!")
    return redirect(url_for('employee_list'))

@app.route('/attendance', methods=['GET', 'POST'])
def attendance_form():
    employees = Employee.query.all()

    if request.method == 'POST':
        employee_id = request.form.get('employee_id')
        action = request.form.get('action')
        date_str = request.form.get('date')
        att_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else date.today()

        emp = Employee.query.get(employee_id)
        if not emp:
            flash("Invalid employee.")
            return redirect(url_for('attendance_form'))

        if action == 'clock_in':
            existing_record = Attendance.query.filter_by(
                employee_id=employee_id, date=att_date, clock_out_time=None
            ).first()

            if existing_record:
                flash("Already clocked in.")
            else:
                db.session.add(Attendance(
                    employee_id=employee_id,
                    date=att_date,
                    clock_in_time=datetime.now()
                ))
                db.session.commit()
                flash("Clocked in.")
        elif action == 'clock_out':
            record = Attendance.query.filter_by(
                employee_id=employee_id, date=att_date, clock_out_time=None
            ).first()
            if record:
                record.clock_out_time = datetime.now()
                db.session.commit()
                flash("Clocked out.")
            else:
                flash("No clock-in record found.")
        return redirect(url_for('attendance_form'))

    return render_template('attendance_form.html', employees=employees)

@app.route('/attendance/records')
def attendance_list():
    records = Attendance.query.order_by(Attendance.date.desc(), Attendance.clock_in_time.desc()).all()
    return render_template('attendance_list.html', records=records)

# ------------------------------
# Main
# ------------------------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
