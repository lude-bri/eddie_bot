"""
This module contains functions to retrieve and format student data.

Functions:
    get_project_data(student_data): Retrieve and format project data for a student.
    get_timeline(student_data): Calculate the timeline for a student's cursus.
    get_nvalidated_projects(student_data): Get number of validated projects.
    get_logtime(pisciner, week, date): Get pisciner logtime
    get_exams(pisciner, project): Get pisciner exams
    get_scale(pisciner, week, date): Get pisciner scale.
"""

import logging
from pprint import pprint
from datetime import datetime, timedelta
# from colorama import Fore, Back, Style
from app.api import get_logtime_data, get_exam_data, get_scale_data
from app.time import timed

# Get Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
pprint(logger)


@timed
def extract_project_data(student_data):
  """
  Retrieve and format project data for a student.

  Args:
    student_data (dict): The student data dictionary containing information about the student.

  Returns:
    dict: A dictionary containing the project names and their corresponding final marks.
  """
  logger.info("extract_project_data()")
  projects = student_data["projects_users"]
  progress_data = {}

  # Extract exam projects from the student's project data
  exams = [
    project
    for project in student_data["projects_users"]
    if "Exam" in project["project"]["name"]
  ]
  # Fill progress_data with exam results
  for exam in exams:
    progress_data[exam["project"]["name"]] = exam.get("final_mark", "In Progress")

  # Extract non-exam projects from the student's project data
  only_projects = [
    project for project in projects if "Exam" not in project["project"]["name"]
  ]
  # Fill progress_data with project results
  for project in only_projects:
    progress_data[project["project"]["name"]] = project.get("final_mark", "In Progress")

  return progress_data


@timed
def get_timeline(student_data):
  """
  Calculate the timeline for a student's cursus.

  Args:
    student_data (dict): The student data dictionary containing information about the student.

  Returns:
    tuple: A tuple containing the current week number and the current day of the week.
  """
  logger.info("get_timeline()")
  # start_date = datetime.strptime(
  #   student_data["cursus_users"][-1]["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
  # )
  # Default fallback start_date (e.g., epoch time: 1970-01-01)
  fallback_date = datetime(1970, 1, 1)
  start_date = fallback_date
  
  # Safely attempt to get start_date
  if isinstance(student_data, dict) and "cursus_users" in student_data:
    cursus_users = student_data["cursus_users"]
    if isinstance(cursus_users, list) and cursus_users:
      try:
        start_date_str = cursus_users[-1]["created_at"]
        start_date = datetime.strptime(start_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
      except (KeyError, ValueError) as e:
        logger.warning(f"Failed to parse 'created_at': {e}. Using fallback date.")
  cur_date = datetime.now()

  # Calculate the difference in days between the start date and the current date
  days_difference = (cur_date - start_date).days
  # Calculate the current week number
  week = (days_difference // 7) + 1
  if week > 4:
    week = 5

  # Get the current day of the week
  day = cur_date.weekday()
  # Convert the day number to a string representation
  day_str = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ][day]

  return week, day_str


@timed
def get_nvalidated_projects(student_data):
  """
  Count the number of validated projects for a student.

  Args:
    student_data (dict): The student data dictionary containing information about the student.

  Returns:
    int: The number of validated projects.
  """
  logger.info("get_nvalidated_projects()")
  projects_users = student_data["projects_users"]
  validated = 0
  for proj in projects_users:
    if proj["validated?"]:
      validated += 1
  print(f"""
{student_data["login"]} validated: {validated} projects
""")
  return validated


@timed
def get_logtime(pisciner, begin_at, end_at):
  """
  Calculate the total logtime for a pisciner within a specified time range.

  Args:
    pisciner (dict): A dictionary containing pisciner information, including 'login'.
    begin_at (str): The start date and time for the logtime data in ISO 8601 format.
    end_at (str): The end date and time for the logtime data in ISO 8601 format.

  Returns:
    float: The total logtime in hours.

  Raises:
    requests.exceptions.RequestException: If the request to the 42 API fails.
    Exception: For any other errors encountered during the process.
  """
  logger.info("get_logtime()")
  user = pisciner["login"]

  print(f"""
Getting {user} logtime from
{begin_at} to {end_at}
""")

  logtime_data = get_logtime_data(pisciner, begin_at, end_at)
  if logtime_data is None:
    logging.error("No logtime data received; returning 0.0 logtime.")
    return 0.0  # or handle the error as appropriate
  pprint(logtime_data)

  logtime = 0.0
  for time_str in logtime_data.values():
    # Split into hours, minutes, seconds, and microseconds
    parts = time_str.split(".")
    hms = parts[0]
    microseconds = int(parts[1]) if len(parts) > 1 else 0
    # Split hours, minutes, seconds
    hours, minutes, seconds = map(int, hms.split(":"))
    # Calculate total seconds including microseconds
    total_seconds = hours * 3600 + minutes * 60 + seconds + microseconds / 1e6
    # Convert to hours and add to logtime
    logtime += total_seconds / 3600

  return logtime


@timed
def get_exams(pisciner, project):
  """
  Retrieve exam data for a specific pisciner and project.

  Args:
    pisciner (dict): A dictionary containing pisciner information, including 'login'.
    project (str): The name of the project for which to retrieve exam data.

  Returns:
    dict: A dictionary containing the exam data if successful, None otherwise.
  """
  user = pisciner["login"]
  print(f"Getting {user} exams")

  exams = get_exam_data(pisciner, project)

  return exams


@timed
def get_scale(pisciner, begin_at, end_at):
  """p
  Retrieve scale data for a pisciner within a specified time range.

  Args:
    pisciner (dict): A dictionary containing pisciner information, including 'login'.
    begin_at (str): The start date and time for the scale data in ISO 8601 format.
    end_at (str): The end date and time for the scale data in ISO 8601 format.

  Returns:
    dict: A dictionary containing the scale data if successful, None otherwise.
  """
  user = pisciner["login"]
  print(f"Getting {user} scale")

  scale = get_scale_data(pisciner, begin_at, end_at)

  return scale
