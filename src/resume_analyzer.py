"""
Resume Analyzer Module
This module provides functionality to analyze resumes by comparing them with
job descriptions to calculate ATS (Applicant Tracking System) and matching scores.
"""

import os
import re
from collections import Counter
import docx
import pdfplumber
from flask import Blueprint, request, render_template
from werkzeug.utils import secure_filename
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Blueprint for the resume analyzer
resume_analyzer = Blueprint('resume_analyzer', __name__)
# Configuration for file uploads
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    """
    Check if the uploaded file has a valid extension.

    Args:
        filename (str): Name of the uploaded file.

    Returns:
        bool: True if the file has a valid extension, otherwise False.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text(file_path):
    """
    Extract text from a PDF or DOCX file.

    Args:
        file_path (str): Path to the uploaded file.

    Returns:
        str: Extracted text from the file.

    Raises:
        ValueError: If the file format is not supported.
    """
    if file_path.endswith('.pdf'):
        with pdfplumber.open(file_path) as pdf:
            return "\n".join(
                page.extract_text() for page in pdf.pages if page.extract_text()
            ).strip()
    if file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs).strip()
    raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")


def preprocess_text(text):
    """
    Preprocess text by removing special characters, numbers, and converting
    to lowercase.

    Args:
        text (str): Input text to preprocess.

    Returns:
        list: A list of words from the processed text.
    """
    text = re.sub(r'[^\w\s]', '', text)  # Remove special characters
    text = re.sub(r'\d+', '', text)  # Remove numbers
    return text.lower().split()  # Convert to lowercase and split into words


def calculate_ats_score(resume_words, job_words):
    """
    Calculate the ATS score based on keyword overlap between the resume
    and job description.

    Args:
        resume_words (list): List of words from the resume.
        job_words (list): List of words from the job description.

    Returns:
        float: ATS score as a percentage.
    """
    resume_counter = Counter(resume_words)
    job_counter = Counter(job_words)
    matching_keywords = sum((resume_counter & job_counter).values())
    total_keywords = sum(job_counter.values())
    return (matching_keywords / total_keywords) * 100 if total_keywords > 0 else 0.0


def calculate_matching_score(resume_text, job_description):
    """
    Calculate the matching score using TF-IDF and cosine similarity.

    Args:
        resume_text (str): Extracted text from the resume.
        job_description (str): Job description text.

    Returns:
        float: Matching score as a percentage.
    """
    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform([resume_text, job_description])
    similarity = cosine_similarity(vectors[0:1], vectors[1:2])
    return similarity[0][0] * 100


@resume_analyzer.route('/analyzer', methods=['GET'])
def analyzer_page():
    """
    Render the Resume Analyzer page.
    """
    return render_template('resume_analyzer.html')


@resume_analyzer.route('/analyze-resume', methods=['POST'])
def analyze_resume():
    """
    Handle the resume analysis and render the results page.
    """
    # Validate the request
    if (
        'resume' not in request.files
        or 'job_name' not in request.form
        or 'job_description' not in request.form
    ):
        return render_template(
            'resume_analyzer.html',
            error="All fields are required. Please fill out all fields and try again."
        )

    job_name = request.form['job_name']
    job_description = request.form['job_description']
    file = request.files['resume']

    # Validate the file type
    if not file or not allowed_file(file.filename):
        return render_template(
            'resume_analyzer.html',
            error="Invalid resume file. Only PDF or DOCX files are allowed."
        )

    # Save the uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # Extract text from the resume
        resume_text = extract_text(filepath)
        if not resume_text:
            raise ValueError("Could not extract text from the resume.")

        # Preprocess texts
        resume_words = preprocess_text(resume_text)
        job_words = preprocess_text(job_description)

        # Calculate scores
        ats_score = calculate_ats_score(resume_words, job_words)
        matching_score = calculate_matching_score(resume_text, job_description)

        # Render results page
        return render_template(
            'resume_results.html',
            job_name=job_name,
            ats_score=f"{round(ats_score, 2)}%",
            matching_score=f"{round(matching_score, 2)}%"
        )
    except (ValueError, FileNotFoundError) as error:
        return render_template(
            'resume_analyzer.html',
            error=f"An error occurred during analysis: {str(error)}"
        )
    finally:
        # Ensure the uploaded file is removed
        if os.path.exists(filepath):
            os.remove(filepath)
