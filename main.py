from flask import Flask, render_template, request, redirect, url_for, flash
import os
import pymongo




# declare app variable
app = Flask("name")
app.secret_key='12345'

title="Jupyter Dashboard"
heading = "TODO Reminder with Flask and MongoDB"

client=pymongo.MongoClient("mongodb://127.0.0.1:27017")
db=client.school_admin
todos=db.todo
username = "Hwezha"
role="Admin"
students=["Hwezha"]
student_id=0

def redirect_url():
    return request.args.get('next') or request.referrer or url_for('index')

@app.route("/")
@app.route('/admin')
def tasks():
    print(username)
    return render_template('index.html', students=students, username=username, role=role, t=title, h=heading)

@app.route("/test")
def testpage():
    a1="active"
    return render_template('add_student.html', a1=a1, t=title, h=heading)

@app.route("/addstudent", methods=['GET', 'POST'])
def addstudent():
    if request.method == 'POST':
        # if request.form['submit'].get == 'Do Something':
        #     pass # do something
        stu=request.form.get("name")
        print(stu)
        students.append(stu)
        flash("Student Added!", "success")
        return redirect('/')

    return render_template('add_student.html', student_id=student_id, t=title, h=heading)

if __name__ == "__main__":
    app.run()
