from email.message import EmailMessage
from functools import wraps

import smtplib
import ssl
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify  # noqa: E402
from flask_pymongo import PyMongo  # noqa: E402

from passlib.hash import pbkdf2_sha256
from pandas import DataFrame  # noqa: E402
import re  # noqa: E402
import numpy as np  # noqa: E402
from src.resume_analyzer import resume_analyzer
"""
The module app holds the function related to flask app and database.
"""
"""Copyright 2024 Ishwarya Anandakrishnan, Abishek Viswanath Pittamandalam, Ashwinkumar Manickam Vaithiyanathan

Use of this source code is governed by an MIT-style
license that can be found in the LICENSE file or at
https://opensource.org/licenses/MIT.
"""

app = Flask(__name__)
'''
Variable to load the app module
'''

app.secret_key = b'\xe1\x04B6\x89\xf7\xa0\xab\xd1L\x0e\xfb\x1c\x08"\xf6'
# client = pymongo.MongoClient('localhost', 27017)
# db = client.user_system

mongo_conn = "mongodb+srv://abivis2k:7aNqw7B9gsAfxznS@job-cluster.ayr8p.mongodb.net/db"
'''
Mongo connection string
'''
mongo_params = "?tlsAllowInvalidCertificates=true&retryWrites=true&w=majority"
'''
Mongo parameters
'''
app.config["MONGO_URI"] = mongo_conn + mongo_params

mongodb_client = PyMongo(app)
'''
Client connection
'''
db = mongodb_client.db

app.register_blueprint(resume_analyzer, url_prefix='/resume')

def login_required(f):
    """
    This function required login functionality
    """

    @wraps(f)
    def wrap(*args, **kwargs):
        '''
        This wrap function renders the redirect page
        '''
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')

    return wrap


@app.route('/reset', methods=["GET", "POST"])
def Reset_password():
    """
    Route : '/reset'
    Forgot password feature; also updates the password in MongoDB
    """
    # mongodb_client.db.users.find_one({"_id": user_id})
    # mongodb_client.db.users.find_one({'email': user['email']})

    if request.method == "POST":
        email = request.form["email"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        # Check if new passwords match
        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("reset"))

        if mongodb_client.db.users.find_one({'email': email}):

            # Hash and update the new password
            hashed_password = pbkdf2_sha256.hash(new_password)
            mongodb_client.db.users.update_one({"email": email}, {"$set": {"password": hashed_password}})

            flash("Your password has been updated successfully.", "success")
            return redirect("/")

    return render_template("reset-password.html")


@app.route('/signup')
def sgup():
    """
    Route: '/'
    The index function renders the index.html page.
    """
    return render_template('signup.html')


@app.route('/bookmark')
def bookmark():
    """
    Route: '/bookmark'
    Bookmark a job.
    """
    jobid = request.args.get('jobid')
    bookmarked_job = {
        'user_id': session['user']['_id'],
        'job_id': int(jobid)
    }
    db.userjob.insert_one(bookmarked_job)

    return redirect('/joblistings')


@app.route('/unbookmark')
def unbookmark():
    """
    Route: '/unbookmark'
    Unbookmark a job.
    """
    jobid = request.args.get('jobid')
    db.userjob.delete_one({'user_id': session['user']['_id'], 'job_id': int(jobid)})

    return redirect('/joblistings')


@app.route('/login')
def login():
    """
    Route: '/'
    The login function renders login.html page.
    """
    if 'isCredentialsWrong' not in session:
        session['isCredentialsWrong'] = False
    return render_template('login.html')


@app.route('/')
def index():
    """
    Route: '/'
    The index function renders the login.html page.
    """
    return redirect(url_for('login'))


@app.route('/home')
@login_required
def home():
    """
    Route: '/home'
    The home function renders the index.html page
    """

    return render_template('index.html')


# @app.route('/login')
# def login():
#     """
#     Route: '/login'
#     The index function renders the login.html page.
#     """
#     session['isCredentialsWrong'] = False
#     return render_template('login.html')


@app.route('/joblistings', methods=('GET','POST'))
def joblistings():
    '''
    This function fetches data from database on the search filter
    '''
    if request.method == 'POST':
        print("into req post")
        print(db.get_collection)
        job_df = read_from_db(request, db)
        job_count = job_df.shape[0]
        print(job_count)
        if job_df.empty:
            job_count = 0
            return render_template('no_jobs.html', job_count=job_count)
        job_df = job_df.drop('Job Description', axis=1)
        job_df = job_df.drop('_id', axis=1)
        job_df = job_df.drop('Industries', axis=1)
        job_df = job_df.drop('Job function', axis=1)
        job_df = job_df.drop('Total Applicants', axis=1)
        job_df['Job Link'] = '<a href=' + job_df['Job Link'] + '><div>' + " Apply " + '</div></a>'
        job_link = job_df.pop("Job Link")
        job_df.insert(7, "Job Link", job_link)
        job_df['Job Link'] = job_df['Job Link'].fillna('----')
        return render_template('job_posting.html', job_count=job_count,
                               tables=['''
                <style>
                    .table-class {border-collapse: collapse;    margin: 24px 0;
                        font-size: 15px; background-color: #000000;
                    font-family: sans-serif;    min-width: 500px;    }
                    .table-class thead tr {background-color: #002147;    color: #ffffff;
                    text-align: left; font-weight: 600; }
                    .table-class th,.table-class td {    text-align:center; padding: 12.4px 15.2px;}
                    .table-class tbody tr {border-bottom: 1px solid #ffffff; border-top-left-radius: 20px;
                    margin: 10px 0; border: 1px;border-color: white;}
                    .table-class tbody tr:nth-of-type(even) {    background-color: #20b2aa; color: white;}
                    .table-class tbody tr:nth-of-type(odd) {    background-color: #ffe4c4; }
                    .table-class tbody tr:last-of-type {    border-bottom: 2.1px solid #009878;}
                    .table-class tbody tr.active-row {  font-weight: bold;    color: #009878;}
                    table tr th { text-align:center; }
                </style>
            ''' + job_df.to_html(classes="table-class", render_links=True, escape=False)],
                               titles=job_df.columns.values)

    elif request.method == 'GET':  # If we hit redirect after bookmarking/unbookmarking a job listing.
        print("into req get")
        # Initializing a dummy POST data for the read_from_db function
        request.form = {}
        request.form['title'] = ''
        request.form['location'] = ''
        request.form['companyName'] = ''
        request.form['skills'] = ''
        job_df = read_from_db(request, db)
        job_count = job_df.shape[0]
        if job_df.empty:
            job_count = 0
            return render_template('no_jobs.html', job_count=job_count)
        job_df = job_df.drop('Job Description', axis=1)
        job_df = job_df.drop('_id', axis=1)
        job_df = job_df.drop('Industries', axis=1)
        job_df = job_df.drop('Job function', axis=1)
        job_df = job_df.drop('Total Applicants', axis=1)
        job_df['Job Link'] = '<a href=' + job_df['Job Link'] + '><div>' + " Apply " + '</div></a>'
        job_link = job_df.pop("Job Link")
        job_df.insert(7, "Job Link", job_link)
        job_df['Job Link'] = job_df['Job Link'].fillna('----')
        return render_template('job_posting.html', job_count=job_count,
                               tables=['''
                <style>
                    .table-class {border-collapse: collapse;    margin: 24px 0;
                        font-size: 15px; background-color: #000000;
                    font-family: sans-serif;    min-width: 500px;    }
                    .table-class thead tr {background-color: #002147;    color: #ffffff;
                    text-align: left; font-weight: 600; }
                    .table-class th,.table-class td {    text-align:center; padding: 12.4px 15.2px;}
                    .table-class tbody tr {border-bottom: 1px solid #ffffff; border-top-left-radius: 20px;
                    margin: 10px 0; border: 1px;border-color: white;}
                    .table-class tbody tr:nth-of-type(even) {    background-color: #20b2aa; color: white;}
                    .table-class tbody tr:nth-of-type(odd) {    background-color: #ffe4c4; }
                    .table-class tbody tr:last-of-type {    border-bottom: 2.1px solid #009878;}
                    .table-class tbody tr.active-row {  font-weight: bold;    color: #009878;}
                    table tr th { text-align:center; }
                </style>
            ''' + job_df.to_html(classes="table-class", render_links=True, escape=False)],
                               titles=job_df.columns.values)


@app.route('/search', methods=('GET', 'POST'))
def search():
    '''
    This functions fetches data from database on the search filter
    '''
    print(f"into search function ${request.method}")

    print(request)
    """
    Route: '/search'
    The search function renders the get_job_postings.html.
    Upon submission fetches the job postings from the database and renders job_posting.html
    """
    # if request.method == 'POST':
    #     print("into req post")
    #     print(db.get_collection)
    #     job_df = read_from_db(request, db)
    #     job_count = job_df.shape[0]
    #     print(job_count)
    #     if job_df.empty:
    #         job_count = 0
    #         return render_template('no_jobs.html', job_count=job_count)
    #     job_df = job_df.drop('Job Description', axis=1)
    #     job_df = job_df.drop('_id', axis=1)
    #     job_df = job_df.drop('Industries', axis=1)
    #     job_df = job_df.drop('Job function', axis=1)
    #     job_df = job_df.drop('Total Applicants', axis=1)
    #     job_df['Job Link'] = '<a href=' + job_df['Job Link'] + '><div>' + " Apply " + '</div></a>'
    #     job_link = job_df.pop("Job Link")
    #     job_df.insert(7, "Job Link", job_link)
    #     job_df['Job Link'] = job_df['Job Link'].fillna('----')
    #     return render_template('job_posting.html', job_count=job_count,
    #                            tables=['''
    # <style>
    #     .table-class {border-collapse: collapse;    margin: 24px 0;
    #         font-size: 15px; background-color: #000000;
    #     font-family: sans-serif;    min-width: 500px;    }
    #     .table-class thead tr {background-color: #002147;    color:#ffffff;
    #        text-align: left; font-weight: 600; }
    #     .table-class th,.table-class td {    text-align:center; padding: 12.4px 15.2px;}
    #     .table-class tbody tr {border-bottom: 1px solid #ffffff; border-top-left-radius: 20px;
    #      margin: 10px 0; border: 1px;border-color: white;}
    #     .table-class tbody tr:nth-of-type(even) {    background-color: #20b2aa; color: white;}
    #     .table-class tbody tr:nth-of-type(odd) {    background-color: #ffe4c4; }
    #     .table-class tbody tr:last-of-type {    border-bottom: 2.1px solid #009878;}
    #     .table-class tbody tr.active-row {  font-weight: bold;    color: #009878;}
    #     table tr th { text-align:center; }
    # </style>
    # ''' + job_df.to_html(classes="table-class", render_links=True, escape=False)],
    #         titles=job_df.columns.values)
    return render_template('get_job_postings.html')
#         .table-class tbody tr:nth-of-type(odd) {    background-color: #e4ad46; }
# ffe4c4


def add(db, job_data):
    """
    The add function adds the skills column and adds the job data to the database.
    """
    job_data['skills'] = [','.join(map(str, skill)) for skill in job_data['skills']]
    job_data['skills'] = job_data['skills'].replace(r'^\s*$', np.nan, regex=True)
    job_data['skills'] = job_data['skills'].fillna('----')
    db.jobs.insert_many(job_data.to_dict('records'))


def read_from_db(request, db):
    """
    The read_from_db function reads the job details based on the input provided using regex.
    Returns a DataFrame with the details
    """
    job_title = request.form['title']
    job_location = request.form['location']
    company_name = request.form['companyName']
    skills = request.form['skills']
    regex_char = ['.', '+', '*', '?', '^', '$', '(', ')', '[', ']', '{', '}', '|']

    for char in regex_char:
        skills = skills.replace(char, '\\' + char)

    rgx_title = re.compile('.*' + job_title + '.*', re.IGNORECASE)
    rgx_location = re.compile('.*' + job_location + '.*', re.IGNORECASE)
    rgx_company_name = re.compile('.*' + company_name + '.*', re.IGNORECASE)
    rgx_skills = re.compile('.*' + skills + '.*', re.IGNORECASE)

    data_filter = {}
    if job_title != '':
        data_filter['Job Title'] = rgx_title
    if job_location != '':
        data_filter['Location'] = rgx_location
    if company_name != '':
        data_filter['Company Name'] = rgx_company_name
    if skills != '':
        data_filter['skills'] = rgx_skills

    data = list(db.jobs.find(data_filter))
    user_id = session['user']['_id']
    bookmarked_jobs = list(db.userjob.find({'user_id': user_id}))
    for job in data:

        job_id = job['_id']
        flag = False

        for bookmarked_job in bookmarked_jobs:
            if bookmarked_job['job_id'] == job_id:
                flag = True
                break

        if flag:
            job['bookmarked'] = '1'
        else:
            job['bookmarked'] = '0'

    data = sorted(data, key=lambda x: x['bookmarked'], reverse=True)

    for job in data:
        if job['bookmarked'] == '1':
            job['bookmarked'] = '<a href="/unbookmark?jobid=' + str(job['_id']) + '">📍</a>'
        else:
            job['bookmarked'] = '<a href="/bookmark?jobid=' + str(job['_id']) + '">📌</a>'

    return DataFrame(list(data))

@app.route('/toggle-on', methods=['POST'])
def toggle_on():
    print("Toggle switch is now on!")
    jobs_list = list(db.jobs.find())
    if jobs_list is None:
        print("No Jobs")

    send_notification_email(jobs_list)
    # for job in jobs_list:
    #     send_notification_email(job)
    #     break
    return jsonify({'message': 'Function executed successfully'}), 200


def send_notification_email(jobs_list):

    sender = 'burnoutapp123@gmail.com'
    password = 'xszyjpklynmwqsgh'
    receiver = "shubhamkulkarni2421@gmail.com"

    subject = 'Job-Cruncher: New Job Notification'
    body = "Job Listings:\n\n"

    for jobs in jobs_list:
        body += f"""
    Job Title: {jobs['Job Title']}
    Company: {jobs['Company Name']}
    Location: {jobs['Location']}
    Job Function: {jobs['Job function']}
    Employment Type: {jobs['Employment type']}
    Industries: {jobs['Industries']}
    Date Posted: {jobs['Date Posted']}
    Job Description: {jobs['Job Description'][:200]}...

    """

    body += "\nFor more details, please check the job postings on our platform."

    try:

        em = EmailMessage()
        em['From'] = sender
        em['To'] = receiver
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, receiver, em.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")
        flash(
            'Failed to send Two-Factor Authentication code. Please try again.',
            'danger')