import requests
import smtplib
from pprint import pprint
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime






















with open("/Users/adamhorvitz/PycharmProjects/pythonProject/CodingBat Teacher Report.html") as page:
    soup = BeautifulSoup(page, 'html.parser')

#print(soup.prettify())

tbody = soup.find_all('tbody')[2]
# pprint(tbody)

emailList = []
for x in range(2, len(tbody)-2):
    tr = tbody.find_all('tr')[x]
    # email = tr.find_all(
    #     "a", string=lambda text: "@" in text.lower()
    # )
    row_data = tr.findAll(text=True)
    email = row_data[0]
    if len(row_data) > 2:
        points = float(row_data[-1])
    else:
        points = 0.0
    emailList.append([email, points])

    pprint(emailList)



# email_elements = [
#     p_element.parent.parent.parent for p_element in email
# ]

#print(email_elements.prettify())

'''
job_elements = results.find_all("div", class_="card-content")
for job_element in job_elements:
    title_element = job_element.find("h2", class_="title")
    company_element = job_element.find("h3", class_="company")
    location_element = job_element.find("p", class_="location")
    print(title_element.text.strip())
    print(company_element.text.strip())
    print(location_element.text.strip())
    print()

python_jobs = results.find_all(
    "h2", string=lambda text: "python" in text.lower()
)

python_job_elements = [
    h2_element.parent.parent.parent for h2_element in python_jobs
]

links = job_element.find_all("a")
for link in links:
    link_url = link["href"]
    print(f"Apply here: {link_url}\n")
'''