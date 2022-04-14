class Student:
    subjects=[]

    def __init__(self,
                 id,
                 firstname,
                 lastname,
                 gender,
                 dob,
                 faculty,
                 course_level,
                 course_name,
                 student_address,
                 email_address,
                 phone_number):
        self.id=id
        self.firstname=firstname
        self.lastname=lastname
        self.gender=gender
        self.dob=dob
        self.faculty=faculty
        self.course_level=course_level
        self.course_name=course_name
        self.student_address=student_address
        self.email_address=email_address
        self.phone_number=phone_number


