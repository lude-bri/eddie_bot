"""
Initialization module for the app package.

This module imports and exposes the main components of the app package, making them
available for use when the package is imported.
"""

# from .globals import global_project_counts

# Import the Slack bot application and its commands
from .slack_bot import app, get_student, get_piscine

# Import functions and classes from the api module
from .api import (
  get_42_api_token,
  validate_student,
  get_student_data,
  get_piscine_data,
  get_logtime_data,
  get_exam_data,
)

from .getters import (
  get_timeline,
  extract_project_data,
  get_logtime,
  get_exams,
  get_scale,
)

# Import the function to format student information
from .printer import format_student_info, format_piscine_projects


# Import the function to get the warning status of a student
from .warning import warning_status

# Import the timed decorator
from .time import time

# Define the public API of the package
__all__ = [
  # Globals
  # "global_project_counts",
  # Slack Bot
  "app",
  "get_student",
  "get_piscine",
  "get_timeline",
  # API
  "get_42_api_token",
  "validate_student",
  "get_student_data",
  "get_piscine_data",
  "get_logtime_data",
  "get_exam_data",
  # Getters
  "get_logtime",
  "get_exams",
  "get_scale",
  "extract_project_data",
  # Printer
  "format_student_info",
  "format_piscine_projects",
  # Warning
  "warning_status",
  # Time
  "time",
]
