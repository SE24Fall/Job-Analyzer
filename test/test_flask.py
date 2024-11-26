"""
Test suite for Flask application endpoints.
This module contains unit tests for login, password reset, user signup,
and search functionalities.
"""

from src.app import app, add, mongodb_client
import pandas as pd

db = mongodb_client.db
client = app.test_client()


def test_invalid_login_empty_ip1():
    """
    Test invalid login with empty email and password.
    """
    email = ''
    password = ''
    response = client.post(
        '/login',
        data={"email": email, "password": password},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_invalid_login_empty_ip2():
    """
    Test invalid login with empty email and a random password.
    """
    email = ''
    password = 'xyz'
    response = client.post(
        '/login',
        data={"email": email, "password": password},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_invalid_login_empty_ip3():
    """
    Test invalid login with a random email and empty password.
    """
    email = 'abc'
    password = ''
    response = client.post(
        '/login',
        data={"email": email, "password": password},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_invalid_login_empty_ip4():
    """
    Test invalid login with empty email and correct password.
    """
    email = ''
    password = 'correct_password'
    response = client.post(
        '/login',
        data={"email": email, "password": password},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_invalid_login_empty_ip5():
    """
    Test invalid login with valid email and empty password.
    """
    email = 'valid@gmail.com'
    password = ''
    response = client.post(
        '/login',
        data={"email": email, "password": password},
        follow_redirects=True
    )
    assert response.status_code == 200


def test_reset_password_ip1():
    """
    Test password reset with all fields empty.
    """
    email = ''
    new_password = ''
    confirm_password = ''
    response = client.post(
        '/reset',
        data={
            "email": email,
            "new_password": new_password,
            "confirm_password": confirm_password
        }
    )
    assert response.status_code == 200


def test_reset_password_ip2():
    """
    Test password reset with valid email, new password, and blank confirm password.
    """
    email = "valid@email.com"
    new_password = "abc"
    confirm_password = ""
    response = client.post(
        '/reset',
        data={
            "email": email,
            "new_password": new_password,
            "confirm_password": confirm_password
        }
    )
    assert response.status_code == 200


def test_reset_password_ip3():
    """
    Test password reset with invalid email and blank confirm password.
    """
    email = "invalid@email.com"
    new_password = "abc"
    confirm_password = ""
    response = client.post(
        '/reset',
        data={
            "email": email,
            "new_password": new_password,
            "confirm_password": confirm_password
        }
    )
    assert response.status_code == 200


def test_reset_password_ip4():
    """
    Test password reset with all fields correct.
    """
    email = "valid@email.com"
    new_password = "abc"
    confirm_password = "abc"
    response = client.post(
        '/reset',
        data={
            "email": email,
            "new_password": new_password,
            "confirm_password": confirm_password
        }
    )
    assert response.status_code == 200


def test_reset_password_ip5():
    """
    Test password reset with valid email, new password, and mismatched confirm password.
    """
    email = "valid@email.com"
    new_password = "abc"
    confirm_password = "cba"
    response = client.post(
        '/reset',
        data={
            "email": email,
            "new_password": new_password,
            "confirm_password": confirm_password
        }
    )
    assert response.status_code == 200


def add_sample_data():
    """
    Adds sample data entry to the database for testing purposes.
    """
    sequence_document = db.counter.find_one_and_update(
        {"name": "job-counter"},
        {"$inc": {"value": 1}},
        return_document=True
    )

    next_id = sequence_document["value"]
    job_dict = {
        "_id": next_id,
        "Job Title": "Software Engineer, New Grad",
        "Company Name": "IXL Learning",
        "Location": "Raleigh, NC",
        "Date Posted": "2 days ago",
        "Total Applicants": "Over 200 applicants",
        "Job Description": "IXL Learning, a leading edtech company with products used by millions",
        "Job Link": "https://www.linkedin.com/jobs/view/3200864048",
        "Seniority level": "Not Applicable",
        "Employment type": "Full-time",
        "Job function": "Engineering and Information Technology",
        "Industries": "E-Learning Providers",
        "skills": "linux,react,ui,scala,sql,python,java"
    }

    df = pd.DataFrame([job_dict])
    add(db, df)
