from typing import Optional

from flask import Flask, render_template, request, redirect, url_for, flash
import pymongo
from flask_login import login_required, current_user, UserMixin, LoginManager, login_user, logout_user
from datetime import datetime

# declare app variable
app = Flask("Admin")
app.secret_key = '12345'

title = "Jupyter Dashboard"
heading = "TODO Reminder with Flask and MongoDB"

client = pymongo.MongoClient("mongodb://127.0.0.1:27017")
db = client.school_admin

# login code
login_manager = LoginManager(app)
dbuser = db.users.find_one()
users = db.users.find()


class User(UserMixin):
    def __init__(self, id, pw):
        self.id = id
        self.password = pw
        if self.id[0] == 'S':
            self.role = "Student"
            res = db.students.find_one({'_id': id})
            self.name = res['firstname'] + ' ' + res['lastname']
        elif self.id[0] == 'T':
            self.role = "Teacher"
            res = db.teachers.find_one({'_id': id})
            self.name = res['firstname'] + ' ' + res['lastname']
        elif self.id[0] == 'A':
            self.role = "Administrator"
            res = db.admins.find_one({'_id': id})
            self.name = res['firstname'] + ' ' + res['lastname']

    @staticmethod
    def get(user_id: str) -> Optional["User"]:
        result = db.creds.find_one({'_id': user_id.upper()})
        if result:
            return User(result['_id'], result['pw'])

    def __str__(self) -> str:
        return f"<Id: {self.id}, Role: {self.role}>"

    def __repr__(self) -> str:
        return self.__str__()


@login_manager.user_loader
def load_user(user_id) -> Optional[User]:
    return User.get(user_id)


@app.context_processor
def inject_global_vars():
    return {'users_logged_in': int(db.db_indices.find_one({'_id': 'users_logged_in'})['counter'])}


def redirect_url():
    return request.args.get('next') or request.referrer or url_for('index')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user_id = request.form["id"]
        user = User.get(user_id)
        if user and request.form["psw"] != user.password:
            db.creds.update_one({'_id': user.id},
                                {'$inc': {'attempts': 1}},
                                upsert=True
                                )
            flash("Incorrect Login Details. Please try again!")

        elif user and request.form["psw"] == user.password:
            login_user(user)
            print("Successful Login: " + str(current_user))
            db.creds.update_one({'_id': user_id},
                                {'$set': {'attempts': 0}},
                                upsert=True
                                )
            db.db_indices.update_one({'_id': 'users_logged_in'},
                                     {'$inc': {'counter': 1}},
                                     upsert=True
                                     )
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
    print("User logout: " + str(current_user))
    logout_user()
    res = db.db_indices.update_one({'_id': 'users_logged_in'},
                                   {'$inc': {'counter': -1}},
                                   upsert=True
                                   )
    print(res)
    return redirect(url_for('login'))


@app.route("/simple-render")
def simple_render():
    return "This is to show how Flask renders web pages"


@login_required
@app.route("/my-subjects")
def my_subjects(category=None):
    if current_user.role == "Administrator" or current_user.role == "Teacher":
        return redirect(url_for("all_subjects"))
    else:
        # cursor=db.students.find_one({'_id':existing_user.id})
        if request.args.get("category") is None:
            print(request.args.get("category"))
            category = "current"
        else:
            category = request.args.get("category")
        cursor = db.students.find_one({'_id': current_user.id})
        subjects = []
        if category=='current':
            subjects_codes = list(cursor['subjects'][category])
            print(subjects_codes)
            for i in subjects_codes:
                subjects.append(db.courses.find_one({'_id': i}))
            print(subjects)
        else:
            try:
                subjects_codes = list(cursor['subjects'][category])
            except:
                subjects_codes=[]
            finally:
                print(subjects_codes)
                for i in subjects_codes:
                    subjects.append(db.courses.find_one({'_id': i['course_id']}))
            print(subjects)


        return render_template('my_subjects.html', subjects=subjects,subjects_codes=subjects_codes, cat=category, user=current_user)


@login_required
@app.route("/all-subjects")
def all_subjects():
    subjects = list(db.courses.find())
    print(subjects)
    return render_template('all_subjects.html', subjects=subjects, user=current_user)


@login_required
@app.route("/addstudent", methods=['GET', 'POST'])
def addstudent():
    all_students = db.student_names.find()

    if request.method == 'POST':
        # if request.form['submit'].get == 'Do Something':
        #     pass # do something
        new_id = db.db_indices.find_one({'_id': 'index_students'})['curr_index']
        db.db_indices.update_one({'_id': 'index_students'},
                                 {'$inc': {'curr_index': 1}},
                                 upsert=True)
        s_id='S' + str(new_id).rjust(5, '0')
        dob_raw = request.form.get("dob")
        res=db.students.insert_one({
            '_id': s_id,
            'firstname': request.form.get("firstname"),
            'lastname': request.form.get("lastname"),
            'gender': request.form.get("gender"),
            'dob': datetime.strptime(dob_raw, "%Y-%m-%d").strftime("%d%m%Y"),
            'faculty': request.form.get("faculty"),
            'major_level': request.form.get("major_level"),
            'major': request.form.get("major"),
            'residence_address': request.form.get("residence_address"),
            'email': request.form.get("email"),
            'phone_number': request.form.get("phone_number"),
            'subjects': {
                'current': [],
                'past': []
            }
        })
        db.creds.insert_one({'_id':s_id,
                             'pw': "12345678",
                             'attempts': 0})
        print("inserted student " + res.inserted_id)
        flash("Student Added!", "success")
        return redirect(url_for('students'))

    return render_template('add_student.html', t=title, user=current_user)


@login_required
@app.route("/subjects/view-subject/<subject_id>/assign-grade/<student_id>", methods=['POST', "GET"])
def assign_grade(subject_id, student_id):
    subject=db.courses.find_one({'_id': subject_id})
    student=db.students.find_one({'_id': student_id})
    if request.method == 'POST':
        grade=int(request.form.get("grade"))
        pastsubjects=db.students.find_one({'_id': student_id})['subjects']['past']
        subject_already_graded=False
        for subj in pastsubjects:
            if subj["course_id"] ==  subject_id:
                subject_already_graded=True
                subj["grade"]=grade
                break
        if not subject_already_graded:
            new_entry={"course_id": subject_id,
                       "grade": grade}
            pastsubjects.append(new_entry)
        db.students.update_one(
                {'_id': student_id},
                {'$set': {"subjects.past": pastsubjects}},
                upsert=True
        )
        if grade>1:
            db.students.update_one(
                {'_id': student_id},
                {'$pull': {'subjects.current': subject_id}}
            )
            db.courses.update_one(
                {'_id': subject_id},
                {'$pull': {'enrolled_students': student_id}}
            )
        print('Graded Student!')
        return redirect(url_for('my_subjects'))

    return render_template('assign-grade.html', t="Assign grade to student",subject=subject, student=student, user=current_user)


@login_required
@app.route("/addsubject", methods=['GET', 'POST'])
def addsubject():
    all_students = db.student_names.find()

    if request.method == 'POST':
        new_id = db.db_indices.find_one({'_id': 'index_subjects'})['curr_index']
        db.db_indices.update_one({'_id': 'index_subjects'},
                                 {'$inc': {'curr_index': 1}},
                                 upsert=True)
        c_id='C' + str(new_id).rjust(5, '0')

        res=db.courses.insert_one({
            '_id': c_id,
            'subject_name': request.form.get("subject_name"),
            'subject_teacher': request.form.get("subject_teacher"),
            'location': request.form.get("location"),
            'max_headcount': request.form.get("max_headcount"),
            'current_headcount': 0,
            'student_level': request.form.get("student_level"),
            'subject_description': request.form.get("subject_description"),
            'enrolled_students': []
        })
        print("inserted subject " + res.inserted_id)
        flash("Subject Added!", "success")
        return redirect(url_for('students'))
    teachers = list(db.teachers.find())

    return render_template('add_subject.html', t="Add New Subject", teachers=teachers, user=current_user)


@login_required
@app.route("/student-info/update-details/<student_id>", methods=["GET", "POST"])
def update_student(student_id):
    student = db.students.find_one({'_id': student_id})

    if request.method == 'POST':
        if request.form['submit'] == "Update":

            res=db.students.update_one({'_id': student_id},
                                       {"$set": {
                'firstname': request.form.get("firstname"),
                'lastname': request.form.get("lastname"),
                'gender': request.form.get("gender"),
                'dob': datetime.strptime(request.form.get("dob"), "%Y-%m-%d").strftime("%d%m%Y"),
                'faculty': request.form.get("faculty"),
                'major_level': request.form.get("major_level"),
                'major': request.form.get("major"),
                'residence_address': request.form.get("residence_address"),
                'email': request.form.get("email"),
                'phone_number': request.form.get("phone_number")
            }})
            print("updated student " + res.inserted_id)
            flash("Student Updated!", "success")
            return redirect(url_for('students'))
        if request.form['submit'] == "Delete Student":
            res = db.students.delete_one({'_id': student_id})
            courses=list(db.courses.find())
            for course in courses:
                db.courses.update_one({'_id': course['_id']},
                                      {'$pull': {'enrolled_students': student_id}}
                                      )
                db.courses.update_one({'_id': course['_id']},
                                      {'$inc': {'current_headcount': -1}}
                                      )
            db.creds.delete_one({'_id': student_id})
            print("Deleted student " + student_id)
            flash("Student Deleted!", "success")
        return redirect(url_for('students'))

    return render_template('update_student.html', t=title,student=student, user=current_user)


@login_required
@app.route("/addteacher", methods=['GET', 'POST'])
def addteacher():
    all_students = db.student_names.find()

    if request.method == 'POST':
        # if request.form['submit'].get == 'Do Something':
        #     pass # do something
        stu = request.form.get("name")
        print(stu)
        all_students.append(stu)
        flash("Student Added!", "success")
        return redirect('/')

    return render_template('add_teacher.html', t=title, user=current_user)


@login_required
@app.route("/add-announcement", methods=['GET', 'POST'])
def add_announcement():
    if request.method == 'POST':
        # if request.form['submit'].get == 'Do Something':
        #     pass # do something
        id = db.db_indices.find_one({'_id': "index_ann"})['curr_index']
        db.db_indices.update_one({'_id': 'index_ann'},
                                 {'$inc': {'curr_index': 1}},
                                 upsert=True
                                 )
        title = request.form['title']
        body = request.form['body']
        recepient = request.form['announcements_recepients']
        new_announcement = {
            '_id': 'ANN' + str(id).rjust(5, '0'),
            'date': datetime.now().strftime('%Y%m%d%H%M'),
            'title': title,
            'body': body,
            'sender': current_user.name,
            'recepient': recepient
        }
        print(new_announcement)
        res = db.announcements.insert_one(new_announcement)
        print(res.inserted_id)
        flash("Announcement Sent to " + recepient + '!', "success")
        return redirect(url_for('view_announcements'))

    return render_template('add_announcement.html', t="New Announcement", user=current_user)


@login_required
@app.route("/students")
def students():
    all_students = list(db.students.find())
    student_count = len(list(all_students))
    return render_template('students.html', students=all_students, student_count=student_count, t=title,
                           user=current_user)


@login_required
@app.route("/teachers")
def teachers():
    all_teachers = db.teachers.find()
    return render_template('teachers.html', teachers=all_teachers, t="Teachers", user=current_user)


@login_required
@app.route("/announcements")
def view_announcements():
    announcements = db.announcements.find({"$or": [{"recepient": 'All'}, {"recepient": current_user.role}]}).sort(
        "date", -1)

    return render_template('announcements.html', announcements=announcements, t=title, user=current_user)


@login_required
@app.route("/student-info/<student_id>")
def view_student(student_id):
    student = db.students.find_one({'_id': student_id})
    if student is not None:
        return render_template('student_details.html', student=student, t=title, user=current_user)
    else:
        return url_for('page_not_found', category='Student', t="Student", user=current_user)


# TODO: change route to announcements/view_announcements/<id>
@login_required
@app.route("/announcements/view-announcement/<announcement_id>")
def view_announcement(announcement_id):
    ann = db.announcements.find_one({'_id': announcement_id})

    if ann is not None:
        return render_template('view_announcement.html', ann=ann, user=current_user,
                               t=ann['title'] + " - From: " + ann['sender'])
    else:
        return render_template('404.html', t=title, user=current_user)


@login_required
@app.route("/subjects/view-subject/<subject_id>", methods=['POST', "GET"])
def view_subject(subject_id):
    subject = db.courses.find_one({'_id': subject_id})
    students = db.students.find()
    print(subject)
    subject_completed=False
    grade=None
    if subject is None:
        return render_template('404.html', t=title, user=current_user, cat="Subject")
    elif request.method == 'POST':
        if request.form['submit'] == "Drop Subject":
            db.students.update_one({'_id': current_user.id},
                                   {'$pull': {
                                       'subjects.current': subject_id
                                   }
                                   }
                                   )
            db.courses.update_one({'_id': subject_id},
                                  {'$pull': {'enrolled_students': current_user.id}}
                                  )
            db.courses.update_one({'_id': subject_id},
                                  {'$inc': {'current_headcount': -1}}
                                  )

            print("Dropped subject in DB")
        elif request.form['submit'] == "Register for Subject":
            db.students.update_one({'_id': current_user.id},
                                   {'$push': {'subjects.current': subject_id}}
                                   )
            db.courses.update_one({'_id': subject_id},
                                  {'$push': {'enrolled_students': current_user.id}}
                                  )
            db.courses.update_one({'_id': subject_id},
                                  {'$inc': {'current_headcount': 1}}
                                  )
            print("Registered for subject in DB")

        return redirect(url_for('view_subject', subject_id=subject['_id']))

    else:

        subject = db.courses.find_one({'_id': subject_id})
        if current_user.role=="Student":
            current_user_past_subjects=db.students.find_one({'_id': current_user.id})['subjects']['past']
            for i in current_user_past_subjects:
                if i["course_id"]==subject_id:
                    subject_completed=True
                    grade=i["grade"]
                    break
            print(subject)
            return render_template('view_subject.html', subject=subject, students=students,subject_completed=subject_completed, grade=grade, t='View Subject',
                                   user=current_user)
        else:
            return render_template('view_subject.html', subject=subject, students=students, t='View Subject',
                                   user=current_user)


@login_required
@app.errorhandler(404)
def page_not_found(e, category="Page"):
    # note that we set the 404 status explicitly
    return render_template('404.html', cat=category.upper(), user=current_user), 404


@app.route("/layout")
def layout():
    title = "Example of a Template"
    return render_template('layout.html', t=title)


@login_required
@app.route("/profile")
def profile():
    uid = current_user.id
    if uid[0] == "S":
        this_user = db.students.find_one({'_id': current_user.id})
    elif uid[0] == "T":
        this_user = db.teachers.find_one({'_id': current_user.id})
    elif uid[0] == "A":
        this_user = db.admins.find_one({'_id': current_user.id})

    print(this_user)
    return render_template('profile.html', this_user=this_user, t="Profile", user=current_user)


@app.template_filter()
def format_datetime(value, format='date'):
    if format == 'date':
        formatted_date = datetime.strptime(value, "%d%m%Y").strftime("%d/%m/%Y")
    elif format == 'datetime':
        formatted_date = datetime.strptime(value, "%Y%m%d%H%M").strftime("%d/%m/%Y %I:%M %p")
    return formatted_date


@app.template_filter()
def count_results(collection):
    return len(list(collection))


@app.template_filter()
def get_student_name(id):
    student = db.students.find_one({'_id': id})
    if student:
        return student['firstname'] + " " + student['lastname']
    else:
        return None


if __name__ == "__main__":
    app.run()
