from typing import Optional

from flask import Flask, render_template, request, redirect, url_for, flash
import os
import pymongo
from flask_login import login_required, current_user, UserMixin, LoginManager, login_user,logout_user
from classes.AnnouncementClass import Announcement
from datetime import timedelta
from datetime import datetime
import time

# declare app variable
app = Flask("Admin")

app.secret_key='12345'

title="Jupyter Dashboard"
heading = "TODO Reminder with Flask and MongoDB"

client=pymongo.MongoClient("mongodb://127.0.0.1:27017")
db=client.school_admin
todos=db.todo
username = "takudan123"
role="Admin"
student_id=0


#login code
login_manager=LoginManager(app)
dbuser= db.users.find_one()
users=db.users.find()
class User(UserMixin):
    def __init__(self, id, email, pw):
        self.id=id
        self.email=email
        self.password=pw
        if self.id[0]=='S': self.role="Student"
        elif self.id[0]=='T': self.role= "Teacher"
        elif self.id[0]=='A': self.role="Administrator"

    @staticmethod
    def get(user_id: str) -> Optional["User"]:
        result=db.users.find_one({'_id':user_id})
        if result:
            userfound=User(result['_id'],result['email'],result['pw'])
            return userfound

    def __str__(self) -> str:
        return f"<Id: {self.id}, Role: {self.role}>"

    def __repr__(self) -> str:
        return self.__str__()


existing_user=User(id=dbuser['_id'],
               email=dbuser['email'],
               pw=dbuser['pw'])


print(existing_user)

@login_manager.user_loader
def load_user(user_id)->Optional[User]:
    return User.get(user_id)


def redirect_url():
    return request.args.get('next') or request.referrer or url_for('index')


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':

        id=request.form["uname"]

        #queery users doc for user with id
        #user=User.get(id)

        pw=request.form["psw"]
        if id==existing_user.id and pw==existing_user.password:
            login_user(existing_user)

            flash("User Logged in Succesfully!")
            time.sleep(1)
            print(current_user)
            return redirect(url_for('dashboard'))
        else:
            flash("Incorrect Login Details. Please try again!")

    return render_template('login.html')


@login_required
@app.route('/')
@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    print(str(current_user))
    return render_template('dashboard.html', user=current_user, t=title)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route("/simple-render")
def simple_render():
    return "This is to show how Flask renders web pages"

@login_required
@app.route("/subjects")
def subjects(category=None):
    # cursor=db.students.find_one({'_id':existing_user.id})
    print(request.args.get("category"))
    print(category)

    if request.args.get("category") is None: category="current"
    else: category=request.args.get("category")
    cursor=db.students.find_one({'_id':'S00003'})
    subjects=cursor['subjects'][category]

    print(subjects)


    return render_template('subjects.html', subjects=subjects, cat=category,user=current_user)


@login_required
@app.route("/addstudent", methods=['GET', 'POST'])
def addstudent():
    all_students = db.student_names.find()

    if request.method == 'POST':
        # if request.form['submit'].get == 'Do Something':
        #     pass # do something
        stu=request.form.get("name")
        print(stu)
        all_students.append(stu)
        flash("Student Added!", "success")
        return redirect('/')

    return render_template('add_student.html', t=title, role=role)

@login_required
@app.route("/students")
def students():
    all_students = db.student_names.find()
    student_count=len(list(all_students))
    return render_template('students.html', students=all_students, student_count=student_count, t=title, role=role)

@login_required
@app.route("/teachers")
def teachers():
    # TODO Students and Teachers cannot edit teacher info. Only view it. Admins can edit teacher info.
    teachers = db.student_names.find()
    return render_template('teachers.html', students=teachers, t=title, role=role)

@login_required
@app.route("/announcements")
def view_announcements():
    announcements = db.announcements.find()
    return render_template('announcements.html', announcements=announcements, t=title, role=role)

@login_required
@app.route("/student-info/<student_id>")
def view_student(student_id):
    student=db.student_names.find_one({'_id': student_id})
    if student != None:
        return render_template('student_details.html', student=student, t=title, h=heading)
    else:
        return render_template('404.html', t=title, role=role)

# TODO: change route to announcements/view_announcements/<id>
@login_required
@app.route("/announcements/view-announcement/<announcement_id>")
def view_announcement(announcement_id):
    ann = db.announcements.find_one({'_id': announcement_id})

    if ann != None:
        parsed_date=datetime.strptime(ann['date'], '%d%m%Y%H%M').strftime('%d/%m/%Y %I:%M %p')
        return render_template('view_announcement.html', ann=ann, parsed_date=parsed_date, t=ann['title']+" - From: " + ann['sender'])
    else:
        return render_template('404.html', t=title, role=role)

@login_required
@app.route("/subjects/view-subject/<subject_id>")
def view_subject(subject_id):
    subject = db.courses.find_one({'_id': subject_id})

    if subject != None:
        return render_template('view_subject.html', subject=subject, t='View Subject')
    else:
        return render_template('404.html', t=title, role=role)

@app.errorhandler(404)
def page_not_found(e, category="Page"):
    # note that we set the 404 status explicitly
    return render_template('404.html', cat=category.upper(), role=role), 404

@app.route("/layout")
def layout():
    title="Example of a Template"
    return render_template('layout.html', t=title)

if __name__ == "__main__":
    app.run()

