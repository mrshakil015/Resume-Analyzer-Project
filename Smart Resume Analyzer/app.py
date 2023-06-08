import re
import os
import io
import nltk
import docx2txt
import mimetypes
import MySQLdb.cursors
from nltk.util import ngrams
from datetime import datetime
from flask_mysqldb import MySQL
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams
from pdfminer.converter import TextConverter
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.pdfinterp import PDFResourceManager
from flask import Flask,send_file, render_template, request, redirect, url_for, session
from builtins import enumerate
from jinja2 import Environment

env = Environment()
env.globals.update(enumerate=enumerate)

  
app = Flask(__name__)
  
  
app.secret_key = 'xyzsdfg'
  
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'user-system'
  
mysql = MySQL(app)

app.config['UPLOAD_FOLDER'] = 'uploads'

### Home page Section 
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/admindashboard')
def admindashboard():
    return render_template('admindashboard.html')

@app.route('/user')
def user():
    return render_template('user.html')

@app.route('/ranking')
def ranking():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM extracted_text ORDER BY matching DESC")
    data = cur.fetchall()
    print("Data is: ", data)
    print("Data type: ",type(data))
    return render_template('ranking.html', data=data, enumerate=enumerate)

@app.route('/candidatedetails')
def candidatedetails():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM extracted_text ORDER BY matching DESC")
    data = cur.fetchall()
    print("Data is: ", data)
    print("Data type: ",type(data))
    return render_template('candidatedetails.html', data=data, enumerate=enumerate)

@app.route('/job')
def job():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM requirement_text")
    data = cur.fetchall()
    return render_template('job.html', data=data)

### Login Section 
@app.route('/login', methods =['GET', 'POST'])
def login():
    mesage = ''
    if request.method == 'POST' and 'role' in request.form and 'email' in request.form and 'password' in request.form:
        role = request.form['role']
        email = request.form['email']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE role = % s AND email = % s AND password = % s', (role, email, password, ))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['userid'] = user['userid']
            session['role'] = user['role']
            session['name'] = user['name']
            session['email'] = user['email']
            mesage = 'Logged in successfully !'
            if user['role'] == 'Admin':
                return render_template('admindashboard.html')
            elif user['role'] == 'User':
                return render_template('user.html')
            else:
                mesage = 'Invalid role!'
           
        else:
            mesage = 'Please enter correct role/ email / password !'
    return render_template('login.html', mesage= mesage)

### Logout Section 
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('userid', None)
    session.pop('role', None)
    session.pop('email', None)
    return redirect(url_for('login'))

### Registration Section 
@app.route('/register', methods =['GET', 'POST'])
def register():
    mesage = ''
    if request.method == 'POST' and 'role' in request.form and 'name' in request.form and 'password' in request.form and 'email' in request.form :
        role = request.form['role']
        userName = request.form['name']
        password = request.form['password']
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM user WHERE email = % s', (email, ))
        account = cursor.fetchone()
        if account:
            mesage = 'Account already exists !'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            mesage = 'Invalid email address !'
        elif not role or not userName or not password or not email:
            mesage = 'Please fill out the form !'
        else:
            cursor.execute('INSERT INTO user VALUES (NULL,% s, % s, % s, % s)', (role, userName, email, password, ))
            mysql.connection.commit()
            mesage = 'You have successfully registered !'
    elif request.method == 'POST':
        mesage = 'Please fill out the form !'
    return render_template('register.html', mesage = mesage)

@app.route('/upload', methods=['POST'])
def upload_file():
    if session.get('loggedin') and session.get('role') == 'Admin':  # Check if user is logged in and has admin role
        target = os.path.join('static/upload')
        if not os.path.isdir(target):
            os.mkdir(target)
        for file in request.files.getlist('file'):
            filename = file.filename
            destination = "/".join([target, filename])
            file.save(destination)
            
        message = 'File successfully uploaded!'
        return redirect(url_for('admin_checkfiletype', filename=filename, destination=destination, target=target))
    elif session.get('loggedin') and session.get('role') == 'User':  # Check if user is logged in and has user role
        target = os.path.join('static/upload')
        if not os.path.isdir(target):
            os.mkdir(target)
        for file in request.files.getlist('file'):
            filename = file.filename
            destination = "/".join([target, filename])
            file.save(destination)
        message = 'File successfully uploaded!'
        #return render_template('user.html', message=message)
        return redirect(url_for('user_checkfiletype', filename=filename, destination=destination, target=target))
    else:
        message = "You need to login to upload files."
        return redirect(url_for('login', message=message))


### Admin Check file type
@app.route('/admin_checkfiletype')
def admin_checkfiletype():
    
    filename = request.args.get('filename')
    destination = request.args.get('destination')
    target = request.args.get('target')
    mimetype, _ = mimetypes.guess_type(filename)
    if mimetype == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        filetype='DOCX'
    elif mimetype == 'application/pdf':
        filetype='PDF'
    else:
        filetype='Unknown'
    mesage = (filename+' File successfully uploaded!'+destination)
    return redirect(url_for('admin_extracttext', mesage=mesage, filetype=filetype, filename=filename,destination=destination, target=target))

###User check file type
@app.route('/user_checkfiletype')
def user_checkfiletype():
    filename = request.args.get('filename')
   
    destination = request.args.get('destination')
    target = request.args.get('target')
    mimetype, _ = mimetypes.guess_type(filename)
    if mimetype == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        filetype='DOCX'
    elif mimetype == 'application/pdf':
        filetype='PDF'
    else:
        filetype='Unknown'
    mesage = (filename+' File(s) successfully uploaded!'+destination)
    return redirect(url_for('user_extracttext', mesage=mesage, filetype=filetype, filename=filename,destination=destination, target=target))
    

#### Extract text from file

###User Extract text from file
@app.route('/admin_extracttext')
def admin_extracttext():
    filename = request.args.get('filename')
    filetype = request.args.get('filetype')
    destination = request.args.get('destination')
    target = request.args.get('target')

    if destination is None:
        # Handle the case where the file path is None
        message = 'Error: File path is None'
        return render_template('admindashboard.html', message=message)
    elif filetype == 'DOCX':
        try:
            # Read in the docx file and extract the text          
            docx_path = os.path.join(target, filename)
            requirementtext = extract_text_from_docx(docx_path)
            
            requirementfilename= filename
            #Extract filename without extension
            filename, extension = os.path.splitext(filename)

            text = requirementtext
            cnamestart = text.find("Company Name:")
            cnameend = text.find("Job Title:")
            companyname = text[cnamestart:cnameend].replace("Company Name: ", "")

            titlestart = text.find("Job Title:")
            titleend = text.find("Qualification:")
            jobtitle = text[titlestart:titleend].replace("Job Title: ", "")


            edustart = text.find("Qualification:")
            eduend = text.find("Total Experience:")
            qualification = text[edustart:eduend].replace("Qualification: ", "")

            #Requirement skills
            skillstart = text.find("Skill:")
            requirementskill = text[skillstart:].replace("Skill: ", "")
            requirementskill = [skill.strip() for skill in requirementskill.split(',')]
            requirementskill = ", ".join(requirementskill)
            requirementskill = requirementskill.lower()
                      
            #Requirement experience
            experience = None
            match = re.search(r'\d+', text)
            if match is not None:
                requirementexperience = int(match.group())
            
            #Extract Result
            results = extracted_results(requirementtext)
            results=', '.join(results)
       
            #Database Connection
            cur = mysql.connection.cursor()
           
            cur.execute("SELECT * FROM requirement_text WHERE requirementfilename=%s", (requirementfilename,))
            result = cur.fetchone()
            if result is None:
                cur.execute("TRUNCATE TABLE requirement_text")
                cur.execute("INSERT INTO requirement_text (requirementfilename,filename, requirementtext, companyname, jobtitle, qualification, requirementskill, requirementexperience) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (requirementfilename,filename, requirementtext, companyname, jobtitle, qualification, requirementskill, requirementexperience))
                mysql.connection.commit()
                message = 'File successfully uploaded!'
            else:
                message =requirementfilename+' File already exists in database'
            cur.close()
            return render_template('admindashboard.html', message=message)
            #return redirect(url_for('candidatename', filename=filename))
        except Exception as e:
            message = f'Error211: {str(e)}'
            return render_template('admindashboard.html', message=message)
    elif filetype == 'PDF':
        try:
            requirementtext = extract_text_from_pdf(destination)
            
            ##Extract information from requirement
            text = requirementtext
            cnamestart = text.find("Company Name:")
            cnameend = text.find("Job Title:")
            companyname = text[cnamestart:cnameend].replace("Company Name: ", "")

            titlestart = text.find("Job Title:")
            titleend = text.find("Qualification:")
            jobtitle = text[titlestart:titleend].replace("Job Title: ", "")


            edustart = text.find("Qualification:")
            eduend = text.find("Total Experience:")
            qualification = text[edustart:eduend].replace("Qualification: ", "")

            skillstart = text.find("Skill:")
            requirementskill = text[skillstart:].replace("Skill: ", "")

            requirementskill= requirementskill.lower()
            experience = None
            match = re.search(r'\d+', text)
            if match is not None:
                requirementexperience = int(match.group())
                
            #Extract Result
            results = extracted_results(text)
            results=', '.join(results)
            
          
            #Database connection
            cur = mysql.connection.cursor()
            # Check if the data has already been stored in the database
            requirementfilename= filename
            cur.execute("SELECT * FROM requirement_text WHERE requirementfilename=%s", (requirementfilename,))
            result = cur.fetchone()
            if result is None:
                cur.execute("INSERT INTO requirement_text (requirementfilename, requirementtext, companyname, jobtitle, qualification, requirementskill, requirementexperience) VALUES (%s, %s, %s, %s, %s, %s, %s)", (requirementfilename, requirementtext, companyname, jobtitle, qualification, requirementskill, requirementexperience))
                mysql.connection.commit()
                message = 'File successfully uploaded!'
            else:
                message =requirementfilename+' File already exists in database'
            cur.close()
            return render_template('admindashboard.html', message=message)
        except Exception as e:
            message = f'Error2: {str(e)}'
            return render_template('admindashboard.html', message=message)
    else:
        message = 'Unknown file type'
        return render_template('admindashboard.html', message=message)


###User Extract text from file
@app.route('/user_extracttext')
def user_extracttext():
    filename = request.args.get('filename')
    filetype = request.args.get('filetype')
    destination = request.args.get('destination')
    target = request.args.get('target')
    username = session['name']
    
    
    
    #Extract candidate name
    candidate, extension = os.path.splitext(filename)
    
    if destination is None:
        # Handle the case where the file path is None
        message = 'Error: File path is None'
        return render_template('user.html', message=message)
    elif filetype == 'DOCX':
        try:
            # Read in the docx file and extract the text          
            docx_path = os.path.join(target, filename)
            text = extract_text_from_docx(docx_path)
           
            #Extract Result
            results = extracted_results(text)
            results=', '.join(results)
            
        #Extract contactinfo
            contactinfo = extract_contactinfo(text)
            phone =[]
            email=[]
            for match in contactinfo:
                if '@' in match:
                    email.append(match)
                else:
                    phone.append(match)
            phone = ', '.join(phone)
            email = ', '.join(email)
            
            #Extract Skill
            cur = mysql.connection.cursor()
            cur.execute("SELECT requirementskill FROM requirement_text WHERE id= 1")
            SKILLS = cur.fetchone()
            SKILLS = " ".join(SKILLS)
            SKILLS = [skill.strip() for skill in SKILLS.split(',')]
            reqskill_sim= SKILLS
            
            extracted_skills = extract_skills(text, SKILLS)
            extracted_skills = ', '.join(extracted_skills)
            reskill_sim = [skill.strip() for skill in extracted_skills.split(',')]
            
            #Extract Total Work Experience
            totalexperience = extract_experience(text)
            
            #Requirement Similarity
            cur.execute("SELECT requirementexperience FROM requirement_text WHERE id= 1")
            requirementexperience= cur.fetchone()
            requirementexperience = float(requirementexperience[0])
            resumeexperience= float(totalexperience)
            workexp_sim = ((resumeexperience)/(requirementexperience))*100
            workexp_sim = round(workexp_sim, 2)
            
            skill_sim = (len(reskill_sim)/len(reqskill_sim))*100
            skill_sim = round(skill_sim, 2)
            
            final_similarity= round((workexp_sim+skill_sim)/2,)
            matching= final_similarity
                  
            # Retrieve all the rows from the database and sort them by matching percentage in descending order
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM extracted_text WHERE filename=%s", (filename,))
            result = cur.fetchone()
            if result is None:
                # File does not exist in database, so insert it
                cur.execute("INSERT INTO extracted_text (username,filename, text,candidate,email, phone, results,resumeskills,totalexperience,matching) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (username,filename, text,candidate,email,phone,results,extracted_skills,totalexperience,matching))
                mysql.connection.commit()
                message = filename+' File successfully uploaded!'
            else:
                # File already exists in database, so display message
                message = filename+' File already exists in database'
            cur.close()

            return render_template('user.html', message=message)

            #return redirect(url_for('candidatename', filename=filename))
        except Exception as e:
            message = f'Error11: {str(e)}'
            return render_template('user.html', message=message)
    elif filetype == 'PDF':
        try:
            text = extract_text_from_pdf(destination)
            
            #Extract Result
            results = extracted_results(text)
            results=', '.join(results)
            
            #Extract contactinfo
            contactinfo = extract_contactinfo(text)
            phone =[]
            email=[]
            for match in contactinfo:
                if '@' in match:
                    email.append(match)
                else:
                    phone.append(match)
            phone = ', '.join(phone)
            email = ', '.join(email)
            
            #Extract Skill
            cur = mysql.connection.cursor()
            cur.execute("SELECT requirementskill FROM requirement_text WHERE id= 1")
            SKILLS = cur.fetchone()
            SKILLS = " ".join(SKILLS)
            SKILLS = [skill.strip() for skill in SKILLS.split(',')]
            reqskill_sim= SKILLS
            
            extracted_skills = extract_skills(text, SKILLS)
            extracted_skills = ', '.join(extracted_skills)
            reskill_sim = [skill.strip() for skill in extracted_skills.split(',')]
            
            #Extract Total Work Experience
            totalexperience = extract_experience(text)
            
            #Requirement Similarity
            cur.execute("SELECT requirementexperience FROM requirement_text WHERE id= 1")
            requirementexperience= cur.fetchone()
            requirementexperience = float(requirementexperience[0])
            resumeexperience= float(totalexperience)
            workexp_sim = ((resumeexperience)/(requirementexperience))*100
            workexp_sim = round(workexp_sim, 2)
            
            skill_sim = (len(reskill_sim)/len(reqskill_sim))*100
            skill_sim = round(skill_sim, 2)
            
            final_similarity= round((workexp_sim+skill_sim)/2,)
            matching= final_similarity
            
            # Retrieve all the rows from the database and sort them by matching percentage in descending order
            cur = mysql.connection.cursor()
            cur.execute("SELECT * FROM extracted_text WHERE filename=%s", (filename,))
            result = cur.fetchone()
            if result is None:
                # File does not exist in database, so insert it
                cur.execute("INSERT INTO extracted_text (username,filename, text,candidate,email, phone, results,resumeskills,totalexperience,matching) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (username,filename, text,candidate,email,phone,results,extracted_skills,totalexperience,matching))
                mysql.connection.commit()
                message = filename+' File successfully uploaded!'
            else:
                # File already exists in database, so display message
                message = filename+' File already exists in database'
            cur.close()

            return render_template('user.html', message=message)

            #return redirect(url_for('candidatename', filename=filename))
        except Exception as e:
            message = f'Error11: {str(e)}'
            return render_template('user.html', message=message)
    else:
        message = 'Unknown file type'
        return render_template('user.html', message=message)


#Extract Working Experience
def extract_experience(text):
    pattern = r'(\w{3}\s*\d{4})\s*-\s*(\w{3}\s*\d{4}|\bPresent\b)'
    matches = re.findall(pattern, text)
    totalexperience = 0
    for start_date, end_date in matches:
        start_year = datetime.strptime(start_date, '%b %Y').year
        if end_date == 'Present':
            end_year = datetime.now().year
            end_month = datetime.now().month
        else:
            end_year = datetime.strptime(end_date, '%b %Y').year
            end_month = datetime.strptime(end_date, '%b %Y').month
        # Check if start date is in the future
        if start_year > datetime.now().year or (start_year == datetime.now().year and datetime.now().month < datetime.strptime(start_date, '%b %Y').month):
            # Assume start date is at the beginning of the year
            start_date = 'Jan ' + str(start_year)
            start_year = datetime.strptime(start_date, '%b %Y').year
        # Calculate total duration in years, rounded to one decimal place
        totalexperience += round((end_year - start_year + (end_month - datetime.strptime(start_date, '%b %Y').month) / 12), 1)
        totalexperience = round(totalexperience, 1)
    print("Total experience: ", totalexperience)
    return str(totalexperience)

###EXTRACT Skills
def extract_skills(text, skills):
    # Remove forward slashes from the text
    text = text.replace("/", " ")

    # Convert skills and words to lowercase
    skills = [skill.lower() for skill in skills]
    words = nltk.word_tokenize(text.lower())

    # Create  bigrams, and trigrams from the words
    bigrams = list(ngrams(words, 2))
    trigrams = list(ngrams(words, 3))

    # Extract matching skills
    extracted_skills = []
    for word in words:
        if word in skills:
            extracted_skills.append(word)
    for bigram in bigrams:
        ngram_str = ' '.join(bigram)
        if ngram_str in skills:
            extracted_skills.append(ngram_str)
    for trigram in trigrams:
        ngram_str = ' '.join(trigram)
        if ngram_str in skills:
            extracted_skills.append(ngram_str)

    return extracted_skills

### PDF extract function 
def extract_text_from_pdf(pdf_path):
    resource_manager = PDFResourceManager()
    output_string = io.StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    converter = TextConverter(resource_manager, output_string, codec=codec, laparams=laparams)
    with open(pdf_path, 'rb') as fh:
        interpreter = PDFPageInterpreter(resource_manager, converter)
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            interpreter.process_page(page)
    converter.close()
    text = output_string.getvalue()
    output_string.close()
    return text

### Extract Result
def extracted_results(text):
    results = []
    resultp = re.compile(r'(H.S.C|S.S.C|J.S.C)|(BACHELOR|MASTER|DOCTOR) OF (ARTS|SCIENCE|SOCIAL SCIENC|BUSINESS ADMINISTRATION|LAWS|EDUCATION|MEDICINE AND SURGERY|PHILOSOPHY)|(BACHELOR|MASTER|DOCTOR) OF (ARTS|SCIENCE|SOCIAL SCIENCE|Social Science|BUSINESS ADMINISTRATION|LAWS|EDUCATION|MEDICINE AND SURGERY|PHILOSOPHY) \((BA|BSC|BBA|LLB|BED|MBBS|MA|MSC|MBA|LLM|MED|PHD)\)|(SECONDARY SCHOOL|HIGHER SECONDARY|JUNIOR SCHOOL|PRIMARY SCHOOL|PRIMARY EDUCATION COMPLETION|MADRASAH EDUCATION)\s+(CERTIFICATE|COMPLETION) \((S.S.C|H.S.C|J.S.C|P.S.C|P.E.C|M.E.C)|(S S C|H S C|J S C|P S C|P E C|M E C)\)|(Secondary School|Higher Secondary|Junior School|Primary School|Primary Education Completion|Madrasah Education)\S+(Certificate|Completion)|(SECONDARY SCHOOL|HIGHER SECONDARY|JUNIOR SCHOOL|PRIMARY SCHOOL|PRIMARY EDUCATION COMPLETION|MADRASAH EDUCATION)\s+(CERTIFICATE|COMPLETION)|(Bachelor|Master|Doctor)|(Bachelor|Master|Doctor) of (Arts|Science|Business Administration|Laws|Education|Medicine and Surgery|Philosophy) \((BA|BSc|BBA|LLB|BEd|MBBS|MA|MSc|MBA|LLM|MEd|PhD)\)|(Secondary School|Higher Secondary|Junior School|Primary School|Primary Education Completion|Madrasah Education) (Certificate|Completion) \((S.S.C|H.S.C|J.S.C|P.S.C|P.E.C|M.E.C)\)|(Institute\s{0,}:\s{0,}\w+\s+\w+|institute\s{0,}:\s{0,}\w+\s+\w+|INSTITUTE\s{0,}:\s{0,}\w+\s+\w+|Institution\s{0,}:\s{0,}\w+\s+\w+|institution\s{0,}:\s{0,}\w+\s+\w+|INSTITUTION\s{0,}:\s{0,}\w+\s+\w+|UNIVERSITY\s{0,}:\s{0,}\w+\s+\w+|University\s{0,}:\s{0,}\w+\s+\w+|university\s{0,}:\s{0,}\w+\s+\w+)|Result\s+:\s+\w+\s+\w+|(GPA)\s+\d{1,2}.\d{1,2}|(GPA):\s+\d{1,2}.\d{1,2}|(GPA)\s+:\d{1,2}.\d{1,2}|(GPA)\s+:\s+\d{1,2}.\d{1,2}|(GPA):\d{1,2}.\d{1,2}|(GPA)\d{1,2}.\d{1,2}|(G.P.A)\s+\d{1,2}.\d{1,2}|(G.P.A):\s+\d{1,2}.\d{1,2}|(G.P.A)\s+:\d{1,2}.\d{1,2}|(G.P.A)\s+:\s+\d{1,2}.\d{1,2}|(G.P.A):\d{1,2}.\d{1,2}|(G.P.A)\d{1,2}.\d{1,2}|(gpa)\s+\d{1,2}.\d{1,2}|(gpa):\s+\d{1,2}.\d{1,2}|(gpa)\s+:\d{1,2}.\d{1,2}|(gpa)\s+:\s+\d{1,2}.\d{1,2}|(gpa):\d{1,2}.\d{1,2}|(gpa)\d{1,2}.\d{1,2}|(g.p.a)\s+\d{1,2}.\d{1,2}|(g.p.a):\s+\d{1,2}.\d{1,2}|(g.p.a)\s+:\d{1,2}.\d{1,2}|(g.p.a)\s+:\s+\d{1,2}.\d{1,2}|(g.p.a):\d{1,2}.\d{1,2}|(g.p.a)\d{1,2}.\d{1,2}|(CGPA)\s+\d{1,2}.\d{1,2}|(CGPA):\s+\d{1,2}.\d{1,2}|(CGPA)\s+:\d{1,2}.\d{1,2}|(CGPA)\s+:\s+\d{1,2}.\d{1,2}|(CGPA):\d{1,2}.\d{1,2}|(CGPA)\d{1,2}.\d{1,2}|(C.G.P.A)\s+\d{1,2}.\d{1,2}|(C.G.P.A):\s+\d{1,2}.\d{1,2}|(C.G.P.A)\s+:\d{1,2}.\d{1,2}|(C.G.P.A)\s+:\s+\d{1,2}.\d{1,2}|(C.G.P.A):\d{1,2}.\d{1,2}|(C.G.P.A)\d{1,2}.\d{1,2}|(cgpa)\s+\d{1,2}.\d{1,2}|(cgpa):\s+\d{1,2}.\d{1,2}|(cgpa)\s+:\d{1,2}.\d{1,2}|(cgpa)\s+:\s+\d{1,2}.\d{1,2}|(cgpa):\d{1,2}.\d{1,2}|(cgpa)\d{1,2}.\d{1,2}|(c.g.p.a)\s+\d{1,2}.\d{1,2}|(c.g.p.a):\s+\d{1,2}.\d{1,2}|(c.g.p.a)\s+:\d{1,2}.\d{1,2}|(c.g.p.a)\s+:\s+\d{1,2}.\d{1,2}|(c.g.p.a):\d{1,2}.\d{1,2}|(c.g.p.a)\d{1,2}.\d{1,2}|(RESULT)\s+\d{1,2}.\d{1,2}|(RESULT):\s+\d{1,2}.\d{1,2}|(RESULT)\s+:\d{1,2}.\d{1,2}|(RESULT)\s+:\s+\d{1,2}.\d{1,2}|(RESULT):\d{1,2}.\d{1,2}|(RESULT)\d{1,2}.\d{1,2}|(result)\s+\d{1,2}.\d{1,2}|(result):\s+\d{1,2}.\d{1,2}|(result)\s+:\d{1,2}.\d{1,2}|(result)\s+:\s+\d{1,2}.\d{1,2}|(result):\d{1,2}.\d{1,2}|(result)\d{1,2}.\d{1,2}|(Result)\s+\d{1,2}.\d{1,2}|(Result):\s+\d{1,2}.\d{1,2}|(Result)\s+:\d{1,2}.\d{1,2}|(Result)\s+:\s+\d{1,2}.\d{1,2}|(Result):\d{1,2}.\d{1,2}|(Result)\d{1,2}.\d{1,2}') #Extract result
    matchesresult = resultp.finditer(text)
    for match in matchesresult:
        results.append(match.group(0))
    return results

### Extract Contact Information
def extract_contactinfo(text):
    contactinfo=[]
    contactpattern = re.compile(r'[a-zA-Z0-9-\.]+@[a-zA-Z-\.]*\.(com|edu|net|co|org)|\d{11,13}|\d{4,5}-\d{6,7}|\d{4,5}\s\d{6,7}|\+\d{2,3}\s\d{4,5}-\d{6,7}|\+\d{13}|\+\d{7}\s\d{6,7}|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b') 
    matchescontact = contactpattern.finditer(text)
    for match in matchescontact:
        contactinfo.append(match.group())
    return contactinfo

### Extract text form docx file
def extract_text_from_docx(docx_path):
    txt = docx2txt.process(docx_path)
    if txt:
        return txt.replace('\t',' ')
    return None


### File Download Section
@app.route('/download')   
def download_file():
    dfile = "static/upload/DemoResume.docx"
    return send_file(dfile,as_attachment=True)

@app.route('/admindownload')   
def admindownload_file():
    dfile = "static/upload/Requirement.docx"
    return send_file(dfile,as_attachment=True)

### App run section
if __name__ == "__main__":
    app.run(debug=True,port=8000)
