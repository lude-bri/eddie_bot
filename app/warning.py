"""
Warning module for analyzing student performance.

This module provides a functions to retrieve and analyze student performance data,
calculate timelines, and determine warning statuses based on performance metrics.
"""

import logging
from pprint import pprint
from app.getters import get_timeline, extract_project_data
from app.time import timed


# Get Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
pprint(logger)


@timed
def warning_status(student_data):
  """
  Determine the warning status of a student based on their performance data.

  This function analyzes a student's project and exam scores to determine if they
  trigger any warning conditions. It calculates averages and checks against predefined
  criteria to assess whether a student might be cheating or needs help.

  Args:
      student_data (dict): A dictionary containing the student's performance data,
                           including project scores and exam results.

  Returns:
      int: A status code indicating the student's warning status:
           - 1: Potential cheating detected.
           - 2: Student may need help.
           - 3: No warning triggered.

  Raises:
      Exception: If there is an error in retrieving or processing the student's data.
  """
  logger.info("warning_status()")
  # Initialize exam_avg with a default value
  exam_avg = 0

  # Retrieve the current week and day
  week, day = get_timeline(student_data)
  # Retrieve the student's project data
  progress_data = extract_project_data(student_data)
  # Initialize variables for calculating averages
  student_project_avg = 0
  student_exam_avg = 0
  nbr_projs = 0

  # Calculate the average project score
  for project_name, score in progress_data.items():
    if project_name.startswith("C Piscine C" or "C Piscine Shell") and isinstance(
      score, int
    ):
      student_project_avg += score
      nbr_projs += 1

  # Calculate the average project score if there are any projects
  if nbr_projs != 0:
    student_project_avg /= nbr_projs
  # Determine the average project and exam scores for the current week
  match week:
    case 1:
      avg_project = "C Piscine C 01"
      if day in ["Saturday", "Sunday"]:
        exam_avg = 26
        student_exam_avg = progress_data.get("C Piscine Exam 00", 0)
      else:
        exam_avg = 0
        student_exam_avg = 0
    case 2:
      avg_project = "C Piscine C 03"
      if "C Piscine Exam 00" in progress_data and day not in ["Saturday", "Sunday"]:
        exam_avg = 26
        student_exam_avg = progress_data.get("C Piscine Exam 00", 0)
      elif "C Piscine Exam 01" in progress_data and day in ["Saturday", "Sunday"]:
        exam_avg = 29
        student_exam_avg = progress_data.get("C Piscine Exam 01", 0)
    case 3:
      avg_project = "C Piscine C 05"
      if "C Piscine Exam 01" in progress_data and day not in ["Saturday", "Sunday"]:
        exam_avg = 29
        student_exam_avg = progress_data.get("C Piscine Exam 01", 0)
      elif "C Piscine Exam 02" in progress_data and day in ["Saturday", "Sunday"]:
        exam_avg = 30
        student_exam_avg = progress_data.get("C Piscine Exam 02", 0)
    case 4:
      avg_project = "C Piscine C 07"
      if "C Piscine Exam 02" in progress_data and day not in ["Saturday", "Sunday"]:
        exam_avg = 30
        student_exam_avg = progress_data.get("C Piscine Exam 02", 0)
      elif "C Piscine Final Exam" in progress_data and day in ["Saturday", "Sunday"]:
        exam_avg = 30
        student_exam_avg = progress_data.get("C Piscine Final Exam", 0)
    case _:
      avg_project = "C Piscine C 07"
      exam_avg = 30
      if "C Piscine Final Exam" in progress_data:
        student_exam_avg = progress_data.get("C Piscine Final Exam", 0)

  # Ensure student_exam_avg is not None
  if student_exam_avg is None:
    student_exam_avg = 0

  # Ensure progress_data[avg_project] is not None
  if avg_project in progress_data and progress_data[avg_project] is None:
    progress_data[avg_project] = 0

  # Check if the exam's score average is below the week's average and the project's score average is above the week's average or the project's score average is 90
  if exam_avg > student_exam_avg:
    if (
      avg_project in progress_data and progress_data[avg_project] >= 40
    ) or student_project_avg >= 90:
      return 1

  match week:
    case 2:
      if day not in ["Monday"]:
        if (
          "C Piscine Shell 00" not in progress_data
          or "C Piscine C 00" not in progress_data
        ):
          return 2
    case 3:
      if day not in ["Monday"]:
        if (
          "C Piscine C 01" not in progress_data or "C Piscine C 02" not in progress_data
        ):
          return 2
        else:
          if (
            "C Piscine Shell 00" not in progress_data
            or "C Piscine C 00" not in progress_data
          ):
            return 2
    case 4:
      if day not in ["Monday"]:
        if (
          "C Piscine C 03" not in progress_data or "C Piscine C 04" not in progress_data
        ):
          return 2
        else:
          if (
            "C Piscine C 01" not in progress_data
            or "C Piscine C 02" not in progress_data
          ):
            return 2
    case _:
      pass

  return 3


"""
Triggers for cheating:
    1. If pisciner's projects delivered are above the week's average
    2. If pisciner's project's score average is 90
    3. If pisciner's exam's score average is below the week's average 
    and the project's score average is above the week's average

Triggers for helping:
    1. If pisciner hasn't delivered Shell00 and C00 in week 2 (tuesday)
    2. If pisciner hasn't delivered C01 and C02 in week 3 (tuesday)
    3. If pisciner hasn't delivered C03 and C04 in week 4 (tuesday)

Notes:
    - It always uses the lastest exam result to do the calculation (basically it updates the exam score on saturday)
    - Check the 'piscine_analytics.pdf' for the average scores of each project and exam
"""
