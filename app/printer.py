"""
Printer module for formatting student information.

This module provides functions to format student data into a readable string format
for display in Slack messages.
"""

import logging
from datetime import datetime, timedelta
from .warning import warning_status
from app.time import timed
from app.getters import get_logtime
from pprint import pprint

from app.globals import global_project_counts

# Get Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
pprint(logger)


@timed
def format_student_info(student_data):
  """
  Format student information into a readable string.

  Args:
      student_data (dict): The student data dictionary containing information about the student.

  Returns:
      str: A formatted string containing the student's information.
  """
  logger.debug("format_student_info()")

  # Extract basic student information
  first_name = student_data["first_name"]
  last_name = student_data["last_name"]
  login = student_data["login"]
  cursus = student_data["cursus_users"][-1]["cursus"]["name"]
  level = student_data["cursus_users"][-1]["level"]
  projects = student_data["projects_users"]
  location = student_data["location"]
  milestone = student_data["cursus_users"][-1]["blackholed_at"]
  small_image_url = student_data["image"]["versions"]["small"]
  intra_url = "https://profile.intra.42.fr/users/" + student_data["login"]

  today = datetime.now()
  # Get Weekly Logtime
  start_of_week = today - timedelta(days=today.weekday() + 7)
  end_of_week = start_of_week + timedelta(days=4)
  week_logtime = get_logtime(
    student_data, start_of_week.strftime("%Y-%m-%d"), end_of_week.strftime("%Y-%m-%d")
  )
  # Get Monthly Logtime
  start_of_month = today - timedelta(days=today.weekday() + 31)
  end_of_month = start_of_month + timedelta(days=31)
  month_logtime = get_logtime(
    student_data, start_of_month.strftime("%Y-%m-%d"), end_of_month.strftime("%Y-%m-%d")
  )

  # Extract exam information
  exams = [
    project
    for project in student_data["projects_users"]
    if "Exam" in project["project"]["name"]
  ]
  exams_str = "\n".join(
    [f">{p['project']['name']}:  `{p['final_mark'] or 'In Progress'}`" for p in exams]
  )

  # Extract non-exam project information
  only_projects = [
    project for project in projects if "Exam" not in project["project"]["name"]
  ]
  recent_projects = sorted(
    only_projects, key=lambda x: x["marked_at"] or "", reverse=True
  )[:10]
  projects_str = "\n".join(
    [
      f">{p['project']['name']}:  `{p['final_mark'] or 'In Progress'}`"
      for p in recent_projects
    ]
  )

  # Get the warning status for the student
  warning = warning_status(student_data)
  match warning:
    case 1:
      warning_msg = "🚨 (_Possibly cheating_)"
    case 2:
      warning_msg = "🚼 (_Needs help_)"
    case _:
      warning_msg = "✅ (_No flags raised_)"

  # Format the student information into a readable string
  return f"""
Howdy, Eddie42 here! :wave:
Oh my cosmic circuits, prepare to be dazzled by the stellar brilliance of this digital superstar! 🚀✨

*User:*     `<{intra_url}|{login}>`
*Name:*    `{first_name} {last_name}`
*Milestone:* `{milestone or "N/A"}`
*Monthly Logtime:* `{month_logtime:.2f}`
*Weekly Logtime:* `{week_logtime:.2f}`
*Cluster:* `{location}`
*Cursus:*   `{cursus}`
*Level:*     `{level:.2f}`


📂 *Recent Projects :*
{projects_str if projects_str else "Hmm... no recent projects? Even in the vast digital cosmos, mysteries abound!"}

📝 *Exams :* 
{exams_str if exams_str else "No exams recorded yet? Keep soaring, future legend!"}

*Warning Status:* {warning_msg}
(Just a friendly beep-boop reminder from your ever-optimistic Eddie!)

And feast your eyes on this pixel-perfect portrait of a brilliant coder: 👀✨ {small_image_url}

Keep shining bright, you magnificent bundle of code and creativity! 💫
"""


@timed
def format_piscine_projects():
  """
  Format and print project validation counts from global_project_counts.

  Args:
      piscine_data (list): List of student data (not used directly here but kept for consistency)

  Prints:
      Formatted list of project names and their validation counts
  """
  if not global_project_counts:
    return "No project validations recorded yet!"

  # Format as a string with Slack-friendly formatting
  lines = [
    f"*{project_name}*: {count} validated"
    for project_name, count in sorted(global_project_counts.items())
  ]
  return "\n".join(lines)
