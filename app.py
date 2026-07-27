from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ===================================
# SECRET KEY
# ===================================
app.secret_key = "employee_management_secret"

# ===================================
# DATABASE CONFIGURATION
# ===================================
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:ROOT@localhost/employee_management"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ===================================
# MAIL CONFIGURATION
# ===================================
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USE_SSL"] = False
app.config["MAIL_USERNAME"] = "munisaikasetty@gmail.com"
app.config["MAIL_PASSWORD"] = "vnle jwon ifwu cgox"

mail = Mail(app)

serializer = URLSafeTimedSerializer(app.secret_key)

# ===================================
# ADMIN TABLE
# ===================================
class Admin(db.Model):
    __tablename__ = "admin"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# ===================================
# EMPLOYEE TABLE
# ===================================


@app.route("/")
def home():
    print(session)
    return redirect('/login')

@app.route("/about")
def about():
    return render_template("about.html")

class Employee(db.Model):
    __tablename__ = "employee"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(100), unique=True, nullable=False)

    password = db.Column(db.String(255), nullable=False)

    department = db.Column(db.String(100), nullable=False)

    salary = db.Column(db.Integer, nullable=False)

    role = db.Column(db.String(100), nullable=False)


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        admin = Admin.query.filter_by(email=email).first()

        if admin and check_password_hash(admin.password, password):

            session.clear()
            session["admin"] = admin.email

            flash("Login Successful", "success")

            return redirect(url_for("dashboard"))

        flash("Invalid Email or Password", "danger")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("register"))

        admin = Admin.query.filter_by(email=email).first()

        if admin:
            flash("Email already registered. Please login.", "warning")
            return redirect(url_for("login"))

        new_admin = Admin(
            name=name,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(new_admin)
        db.session.commit()

        flash("Registration Successful. Please Login.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form["email"].strip().lower()

        print("Entered Email:", email)

        admin = Admin.query.filter_by(email=email).first()

        print("Admin Found:", admin)

        if admin:

            token = serializer.dumps(email, salt="reset-password")

            reset_link = url_for(
                "reset_password",
                token=token,
                _external=True
            )

            msg = Message(
                "Reset Password",
                sender=app.config["MAIL_USERNAME"],
                recipients=[email]
            )

            msg.body = f"Click the link:\n\n{reset_link}"

            mail.send(msg)

            flash("Password reset link sent.", "success")
            return redirect(url_for("login"))

        else:
            flash("Email is not registered.", "danger")

    return render_template("forgot_password.html") 
@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):

    try:
        email = serializer.loads(
            token,
            salt="reset-password",
            max_age=1800      # 30 minutes
        )

    except Exception:

        flash("Reset link is invalid or expired.", "danger")

        return redirect(url_for("forgot_password"))

    if request.method == "POST":

        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:

            flash("Passwords do not match.", "danger")

            return redirect(request.url)

        admin = Admin.query.filter_by(email=email).first()

        if admin:

            admin.password = generate_password_hash(password)

            db.session.commit()

            flash("Password updated successfully. Please login.", "success")

            return redirect(url_for("login"))

    return render_template("reset_password.html")

@app.route("/logout")
def logout():

    session.clear()   # Clear all session data

    flash("Logged Out Successfully", "success")

    return redirect(url_for("login"))

def login_required():

    return "admin" in session

@app.route("/dashboard")
def dashboard():

    if not login_required():

        return redirect(url_for("login"))

    employees=Employee.query.all()

    return render_template("dashboard.html",employees=employees)

@app.route("/contact", methods=["GET", "POST"])
def contact():

    if "admin" not in session:
        return redirect(url_for("login"))

    employees = Employee.query.all()

    if request.method == "POST":

        employee_email = request.form["email"]

        subject = request.form["subject"]

        message = request.form["message"]

        msg = Message(
            subject,
            sender=app.config["MAIL_USERNAME"],
            recipients=[employee_email]
        )

        msg.body = message

        try:

            mail.send(msg)

            flash("Email sent successfully.", "success")

        except Exception as e:

            flash(f"Error sending email: {e}", "danger")

        return redirect(url_for("contact"))

    return render_template("contact.html", employees=employees)

@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():

    if "admin" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        # Find the first missing ID
        employees = Employee.query.order_by(Employee.id).all()

        new_id = 1

        for emp in employees:
            if emp.id == new_id:
                new_id += 1
            else:
                break

        employee = Employee(
    id=new_id,
    name=request.form["name"],
    email=request.form["email"],
    password=generate_password_hash("employee123"),
    department=request.form["department"],
    salary=request.form["salary"],
    role=request.form["role"]
)
        db.session.add(employee)
        db.session.commit()

        flash("Employee Added Successfully", "success")

        return redirect(url_for("dashboard"))

    return render_template("add_employee.html")

@app.route("/edit_employee/<int:id>", methods=["GET", "POST"])
def edit_employee(id):

    if "admin" not in session:
        return redirect(url_for("login"))

    employee = Employee.query.get_or_404(id)

    if request.method == "POST":

        employee.name = request.form["name"]
        employee.email = request.form["email"]
        employee.department = request.form["department"]
        employee.salary = request.form["salary"]
        employee.role = request.form["role"]

        db.session.commit()

        flash("Employee Updated Successfully", "success")

        return redirect(url_for("dashboard"))

    return render_template("edit_employee.html", employee=employee)

@app.route("/delete_employee/<int:id>")
def delete_employee(id):

    if "admin" not in session:
        return redirect(url_for("login"))

    employee = Employee.query.get_or_404(id)

    db.session.delete(employee)

    db.session.commit()

    flash("Employee Deleted Successfully", "success")

    return redirect(url_for("dashboard"))
@app.route("/hr_login", methods=["GET", "POST"])
def hr_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        employee = Employee.query.filter_by(
            email=email,
            role="HR"
        ).first()

        if employee and check_password_hash(employee.password, password):

            session["hr"] = employee.email

            flash("HR Login Successful", "success")

            return redirect(url_for("hr_dashboard"))

        flash("Invalid HR Email or Password", "danger")

    return render_template("hr_login.html")

@app.route("/hr_dashboard")
def hr_dashboard():

    if "hr" not in session:
        return redirect(url_for("hr_login"))

    employees = Employee.query.all()

    return render_template(
        "hr_dashboard.html",
        employees=employees
    )

if __name__=="__main__":
    app.run(debug=True)    