from functools import wraps
from flask import Flask, render_template, request, session, redirect, url_for, flash  # noqa: E402
from flask_pymongo import PyMongo  # noqa: E402

from passlib.hash import pbkdf2_sha256
from pandas import DataFrame  # noqa: E402
import re  # noqa: E402
import numpy as np  # noqa: E402

import os
from flask_pymongo import PyMongo
from flask_mail import Mail, Message
from pymongo import MongoClient
import gridfs
from pyresparser import ResumeParser
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import nltk

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

UPLOAD_FOLDER= 'uploads/'

# Ensure UPLOAD_FOLDER exists
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads/')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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


def perform_resume_analysis(parsed_data):
    """
    Analyzes the parsed resume data, assigns a score, and identifies issues.
    Returns a dictionary with the analysis results.
    """
    score = 0
    issues = []
    recommendations = []

    # Example Criteria
    # 1. Presence of Contact Information
    if parsed_data.get('email') and parsed_data.get('phone'):
        score += 20
    else:
        issues.append("Missing contact information (email or phone).")
        recommendations.append("Ensure your resume includes your email and phone number.")

    # 2. Presence of Skills
    if parsed_data.get('skills') and len(parsed_data['skills']) >= 5:
        score += 20
    else:
        issues.append("Insufficient skills listed.")
        recommendations.append("List at least 5 relevant skills related to your desired job.")

    # 3. Education Details
    if parsed_data.get('education') and len(parsed_data['education']) >= 1:
        score += 20
    else:
        issues.append("Education details missing.")
        recommendations.append("Include your educational background.")

    # 4. Experience Details
    if parsed_data.get('experience') and len(parsed_data['experience']) >= 1:
        score += 20
    else:
        issues.append("Work experience missing.")
        recommendations.append("Add your relevant work experience.")

    # 5. Certifications (Optional)
    if parsed_data.get('certifications') and len(parsed_data['certifications']) >= 1:
        score += 10
    else:
        recommendations.append("Consider adding relevant certifications to strengthen your resume.")

    # 6. Formatting and Length (Assumed based on parsing success)
    # Additional checks can be implemented based on specific requirements.
    # For simplicity, we'll assume formatting is adequate if parsing was successful.
    score += 10  # Assuming formatting is good

    # Ensure score does not exceed 100
    score = min(score, 100)

    analysis = {
        'score': score,
        'issues': issues,
        'recommendations': recommendations
    }

    return analysis

@app.route('/analyze_resume', methods=['GET'])
@login_required
def analyze_resume():
    """
    Route: '/analyze_resume'
    Analyzes the user's uploaded resume and displays the score and issues.
    """
    user_id = ObjectId(session['user']['_id'])
    user = db.users.find_one({'_id': user_id})

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('user_profile'))

    resume_fileid = user.get('resume_fileid')
    resume_filename = user.get('resume_filename')

    if not resume_fileid:
        flash("No resume uploaded to analyze.", "warning")
        return redirect(url_for('user_profile'))

    try:
        # Retrieve resume file from GridFS
        resume_file = fs.get(ObjectId(resume_fileid))
        resume_data = resume_file.read()

        # Save the resume to a temporary file for parsing
        temp_resume_path = os.path.join(app.config['UPLOAD_FOLDER'], f'temp_{secure_filename(resume_filename)}')
        with open(temp_resume_path, 'wb') as temp_file:
            temp_file.write(resume_data)

        # Parse the resume
        parsed_data = ResumeParser(temp_resume_path).get_extracted_data()

        # Remove the temporary file
        os.remove(temp_resume_path)

        if not parsed_data:
            flash("Failed to parse the resume.", "danger")
            return redirect(url_for('user_profile'))

        # Perform analysis (scoring and issue identification)
        analysis_result = perform_resume_analysis(parsed_data)

        # Render the analysis page with results
        return render_template('resume_analysis.html',
                               analysis=analysis_result,
                               resume_fileid=resume_fileid,
                               resume_filename=resume_filename)
    except gridfs.errors.NoFile:
        flash("Resume file not found.", "danger")
        return redirect(url_for('user_profile'))
    except LookupError:
        flash("NLTK stopwords not found. Please run the setup to download necessary resources.", "danger")
        return redirect(url_for('user_profile'))
    except Exception as e:
        flash(f"An error occurred during analysis: {str(e)}", "danger")
        return redirect(url_for('user_profile'))
