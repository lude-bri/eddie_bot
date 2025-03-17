"""
API module for interacting with the 42 API.

This module provides functions to obtain from the 42 API:
- obtain API tokens,
- validate students,
- retrieve student data,
- retrieve piscine data,
- retrieve exam data,
- retrieve scale data,
- retrieve student locations.
"""

import os
import json
import requests
import time
import datetime
import logging
from app.time import timed
from pprint import pprint
from requests_cache import CachedSession
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
# from colorama import Fore, Back, Style

# token Caching
TOKEN_EXPIRY = None
API_TOKEN = None

# Initialize requests_cache (cache expires after 30min)
cached_session = CachedSession("42api_cache", backend="sqlite", expire_after=1800)
piscine_data = {}
studentReqCount = 0

# Get Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
pprint(logger)


@timed
def get_42_api_token():
  """
  Obtain an API token from the 42 API.

  Returns:
      str: The access token for the 42 API.

  Raises:
      Exception: If the token request fails.
  """
  logger.info("get_42_api_token()")
  global API_TOKEN, TOKEN_EXPIRY
  if API_TOKEN and TOKEN_EXPIRY and datetime.datetime.now() < TOKEN_EXPIRY:
    return API_TOKEN  # Use cached token if still valid

  client_id = os.getenv("INTRA_UID")
  client_secret = os.getenv("INTRA_SECRET")
  token_url = "https://api.intra.42.fr/oauth/token"

  # Prepare the data for the token request
  data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
  }

  # Send the token request
  response = requests.request("POST", token_url, data=data)
  if response.status_code == 200:
    json_data = response.json()
    API_TOKEN = json_data["access_token"]
    TOKEN_EXPIRY = datetime.datetime.now() + datetime.timedelta(
      seconds=json_data["expires_in"] - 60
    )
    return API_TOKEN
  else:
    raise Exception("Failed to obtain 42 API token")


@timed
def validate_student(user):
  """
  Validate if a student exists in the 42 API.

  Args:
      user (str): The username of the student.

  Returns:
      bool: True if the student exists, False otherwise.
  """
  logger.info("validate_student()")
  # Obtain the API token
  token = get_42_api_token()
  url = f"https://api.intra.42.fr/v2/users/{user}"  # Build URL
  headers = {"Authorization": f"Bearer {token}"}  # Set auth headers
  response = cached_session.get(url, headers=headers)  # Send request to validate
  return response.status_code == 200


@timed
def get_student_data(user):
  """
  Retrieve the location of a student or computer from the 42 API.

  Args:
      identifier (str): The student username or computer identifier.
      campus (str): The campus identifier.

  Returns:
      tuple: A tuple containing the username and location if found, (None, None) otherwise.
  """
  logger.info("get_student_data()")
  global studentReqCount
  try:
    studentReqCount += 1
    logger.info(f"Call {studentReqCount}")

    token = get_42_api_token()
    url = f"https://api.intra.42.fr/v2/users/{user}"  # Build URL
    headers = {"Authorization": f"Bearer {token}"}  # Set auth headers
    # Set the request parameters
    params = {
      "page[size]": 100,
    }
    response = None
    try:
      response = cached_session.get(url, headers=headers, params=params)  # Send request
      response.raise_for_status()  # Raise HTTPError for bad responses
      if response.status_code == 200:
        return response.json()
      else:
        logging.error(f"Unexpected status code: {response.status_code}")
        return None
    except requests.exceptions.RequestException as e:  # Log if request fails
      logging.error(f"Error fetching student data for user {user}: {str(e)}")
      if response:
        logging.error(f"Response content: {response.text}")
      else:
        logging.error("No response received")
      return None

  except Exception as e:
    logging.error(f"Error in get_student_data for user {user}: {str(e)}")
    return None


@timed
def get_piscine_data(campus, year, month):
  """
  Retrieve piscine data for a specific campus and time period.

  Args:
      campus (int): The campus identifier.
      year (int): The year of the piscine.
      month (int): The month of the piscine.

  Returns:
      list: A list of dictionaries containing piscine data if successful, None otherwise.

  Raises:
      requests.exceptions.RequestException: If the request to the 42 API fails.
      Exception: For any other errors encountered during the process.
  """
  logger.info("get_piscine_data()")
  try:
    token = get_42_api_token()
    url = f"https://api.intra.42.fr/v2/campus/{campus}/users"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
      "filter[pool_year]": year,
      "filter[pool_month]": month,
      "page[size]": 100,
    }
    piscine_data = []
    page = 1

    # Create a session to reuse connections
    sessionCounter = 0
    counter = 0
    sessionCounter += 1
    cached_session.headers.update(headers)
    # Set up retry strategy for transient errors
    retries = Retry(
      total=3,
      backoff_factor=1,
      status_forcelist=[429, 500, 502, 503, 504],
      allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retries)
    cached_session.mount("https://", adapter)
    cached_session.mount("http://", adapter)
    pprint("get_piscine_data()")
    pprint(f"Session count: {sessionCounter}")
    pprint(f"Session: {cached_session}")

    while True:
      params["page[number]"] = page
      counter += 1
      response = None
      pprint(f"Page count: {counter}")
      pprint(f"params: {params}")
      try:
        response = cached_session.get(url, params=params, timeout=10)
        if response.from_cache:
          print(f"Cache hit for page {page}")
        else:
          print(f"Cache miss for page {page}")
        response.raise_for_status()  # Raise for HTTP errors
        data = response.json()
        # If fewer items than the page size, we are on the last page
        if not data:
          break  # Exit when no there's no more data
        piscine_data.extend(data)
        page += 1
      except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching page {page}: {str(e)}")
        if response is not None:
          logging.error(f"Response content: {response.text}")
        return None

    logging.info("get_piscine_data() done")
    return piscine_data

  except Exception as e:
    logging.error(f"Error in get_piscine_data: {str(e)}")
    return None


@timed
def get_student_location(identifier, campus):
  """
  Retrieve the location of a student or computer from the 42 API.

  Args:
      identifier (str): The student username or computer identifier.
      campus (str): The campus identifier.

  Returns:
      tuple: A tuple containing the username and location if found, (None, None) otherwise.
  """
  logger.info("get_student_location()")
  try:
    if identifier:  # validate identifier
      if (  # Check if identifier is a computer
        identifier.startswith("c")
        and identifier.find("r") != -1
        and identifier.find("s") != -1
      ):
        data = get_user_at_location(identifier, campus)  # Get user data
        if isinstance(data, list) and len(data) > 0:
          location = data[0].get("location")
          user = data[0].get("login", {}).get("login")
        else:
          return None, None
      else:
        # Get the student data
        data = get_student_data(identifier)
        if data is None:
          return None, None
        location = data.get("location")
        user = data.get("login")

      return user, location
    else:
      return None, None

  except Exception as e:
    logging.error(f"Unexpected error in get_student_location: {str(e)}")
    return None, None


@timed
def get_user_at_location(identifier, campus):
  """
  Retrieve user data at a specific location from the 42 API.

  Args:
      identifier (str): The computer identifier.
      campus (str): The campus identifier.

  Returns:
      list: A list containing the user data if found, an empty list otherwise.
  """
  logger.info("get_user_at_location()")
  try:
    token = get_42_api_token()
    url = "https://api.intra.42.fr/v2/locations"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
      "filter[campus_id]": 58, # Porto
      "page[size]": 30,
    }
    location_data = []
    page = 1

    counter = 0
    while True:
      params["page[number]"] = page
      response = None
      try:
        location_data = cached_session.get(
          url, headers=headers, params=params
        )  # Get location data
        # Raises an HTTPError for bad responses
        location_data.raise_for_status()
        data = location_data.json()
        data.extend(data)
        if len(data) < params["page[size]"]:
          break
        # Filter the data based on the identifier (host)
        filtered_data = [entry for entry in data if entry["host"] == identifier]
        # pprint(filtered_data)
        page += 1
        if filtered_data:
          user_data = filtered_data[0]["user"]
          return [
            {
              "location": filtered_data[0]["host"],
              "login": {"login": user_data["login"]},
            }
          ]
        else:
          return []
      except requests.exceptions.RequestException as e:  # Log if request fails
        logging.error(f"Error fetching page {page}: {str(e)}")
        if response:
          logging.error(f"Response content: {response.text}")
        else:
          logging.error("No response received")
        return None

  except Exception as e:  # Log unexpected errors
    logging.error(f"Unexpected error in get_user_at_location: {str(e)}")
    return []


@timed
def get_logtime_data(pisciner, begin_at, end_at):
  """
  Retrieve logtime data for a specific pisciner within a given time range.

  Args:
      pisciner (dict): A dictionary containing pisciner information;
      begin_at (str): The start date and time for the logtime data in ISO 8601 format.
      end_at (str): The end date and time for the logtime data in ISO 8601 format.

  Returns:
      dict: A dictionary containing the logtime data if successful, None otherwise.

  Raises:
      requests.exceptions.RequestException: If the request to the 42 API fails.
      Exception: For any other errors encountered during the process.
  """
  user = pisciner["login"]
  id = pisciner["id"]
  print(f"get_logtime_data for {user} w/ id {id}")

  token = get_42_api_token()
  url = f"https://api.intra.42.fr/v2/users/{id}/locations_stats"  # Build URL
  headers = {"Authorization": f"Bearer {token}"}  # Set auth headers
  # Set the request parameters
  params = {
    "begin_at": begin_at,
    "end_at": end_at,
  }
  response = None

  try:
    response = cached_session.get(url, headers=headers, params=params)  # Send request
    response.raise_for_status()  # Raise HTTPError for bad responses
    if response.status_code == 200:
      # pprint(response)
      return response.json()
    else:
      logging.error(f"Unexpected status code: {response.status_code}")
      return None
  except requests.exceptions.RequestException as e:  # Log if request fails
    logging.error(f"Error fetching student data for user {id}: {str(e)}")
    if response:
      logging.error(f"Response content: {response.text}")
    else:
      logging.error("No response received")
    return None

  except Exception as e:
    logging.error(f"Error in get_student_data for user {user}: {str(e)}")
    return None


@timed
def get_exam_data(pisciner, project):
  """
  Retrieve exam data for a specific pisciner and project.

  Args:
      pisciner (dict): A dictionary containing pisciner information, including 'login' and 'id'.
      project (int): The project identifier.

  Returns:
      dict: A dictionary containing the exam data if successful, None otherwise.

  Raises:
      requests.exceptions.RequestException: If the request to the 42 API fails.
      Exception: For any other errors encountered during the process.
  """
  user = pisciner["login"]
  id = pisciner["id"]
  print(f"get_exam_data for {user} w/ id {id}")

  token = get_42_api_token()
  url = "https://api.intra.42.fr/v2/projects_users"
  headers = {"Authorization": f"Bearer {token}"}  # Set auth headers
  params = {
    "project_id": project,
    "filter[user_id]": id,
    "page[size]": 30,
  }

  response = None

  try:
    response = cached_session.get(url, headers=headers, params=params)  # Send request
    response.raise_for_status()  # Raise HTTPError for bad responses
    if response.status_code == 200:
      return response.json()
    else:
      logging.error(f"Unexpected status code: {response.status_code}")
      return None

  except requests.exceptions.RequestException as e:  # Log if request fails
    logging.error(f"Error fetching student data for user {id}: {str(e)}")
    if response:
      logging.error(f"Response content: {response.text}")
    else:
      logging.error("No response received")
    return None

  except Exception as e:
    logging.error(f"Error in get_student_data for user {user}: {str(e)}")
    return None


@timed
def get_scale_data(pisciner, begin_at, end_at):
  """
  Retrieve scale data for a specific pisciner within a given time range.
  How many evaluations a pisciner has performed.

  Args:
      pisciner (dict): A dictionary containing pisciner information, including 'login' and 'id'.
      begin_at (str): The start date and time for the scale data in ISO 8601 format.
      end_at (str): The end date and time for the scale data in ISO 8601 format.

  Returns:
      dict: A dictionary containing the scale data if successful, None otherwise.

  Raises:
      requests.exceptions.RequestException: If the request to the 42 API fails.
      Exception: For any other errors encountered during the process.
  """
  user = pisciner["login"]
  id = pisciner["id"]
  print(f"get_scale_data for {user} w/ id {id}")

  token = get_42_api_token()
  url = f"https://api.intra.42.fr/v2/users/{id}/locations_stats"  # Build URL
  headers = {"Authorization": f"Bearer {token}"}  # Set auth headers
  # Set the request parameters
  params = {
    "range": {
      "updated_at": f"{begin_at}, {end_at}",
    },
    "user_id" : id,
  }
  response = None

  try:
    response = cached_session.get(url, headers=headers, params=params)  # Send request
    response.raise_for_status()  # Raise HTTPError for bad responses
    if response.status_code == 200:
      pprint(response)
      return response.json()
    else:
      logging.error(f"Unexpected status code: {response.status_code}")
      return None
  except requests.exceptions.RequestException as e:  # Log if request fails
    logging.error(f"Error fetching student data for user {id}: {str(e)}")
    if response:
      logging.error(f"Response content: {response.text}")
    else:
      logging.error("No response received")
    return None

  except Exception as e:
    logging.error(f"Error in get_student_data for user {user}: {str(e)}")
    return None
