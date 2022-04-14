class Teacher:
    courses_instructed = []

    def __init__(self,
                 id,
                 firstname,
                 lastname,
                 gender,
                 dob,
                 faculty,
                 qualification,
                 office_hrs,
                 email_address,
                 phone_number):
        self.id = id
        self.firstname = firstname
        self.lastname = lastname
        self.gender = gender
        self.dob = dob
        self.faculty = faculty
        self.qualification = qualification
        self.office_hrs = office_hrs
        self.email_address = email_address
        self.phone_number = phone_number


