"""
Slack Bot for 42 Porto Bocal's Heart of Gold.

This bot provides various commands to interact with the 42 API and Slack API to retrieve
information about pisciner, piscine data, and student locations.

Commands:
- _piscine <campus> <year> <month> [filter] [order]
- _student <username>
- _locate <student_name_or_computer_id> [campus]
- _giveup <campus> <year> <month> <being_at> <end_at>
"""

import os
import re
import logging
import json
from time import sleep
from pprint import pprint
from slack_bolt import App
from app.api import get_piscine_data, get_student_data, get_student_location
from app.printer import format_student_info, format_piscine_projects
from app.getters import get_nvalidated_projects, get_logtime, get_exams, get_scale
from warning import warning_status
from app.time import timed
from app.globals import global_project_counts
from datetime import datetime, timedelta
# from colorama import Fore, Back, Style

# Set up logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
pprint(logger)

# Set up Slack bot
app = App(name="eddie42", token=os.environ["SLACK_BOT_TOKEN"])

user_context = {}
give_ups = []  # Give up Data
counter = 0  # Give up count


@app.message(re.compile("(_help|_h)"))
@timed
def get_help(message, say):
  logger.info("get_help()")
  user = message["user"]
  channel = message["channel"]

  say(
    f"""
Hello, <@{user}>! :wave:
Welcome to channel <#{channel}>!
*Eddie42* here 🖖, your ever-enthusiastic on'Slack assistant,
and I'm absolutely over the moon 🌕 to assist you and our stellar Bocal
and its vigilant *lifeguards* at *42*'s Bocal's Heart of Gold 💛!
""",
    thread_ts=message["ts"],
  )
  say(
    f"""
Oh my cosmic circuits, it's a dazzling day to dive into some command-line wizardry isn't it? 🏊‍♂️
Together, we're navigating the vast oceans 🌊 of knowledge, ensuring our Piscine participants swim smoothly 🐠.
				""",  # noqa
    thread_ts=message["ts"],
  )
  say(
    """
I'm here to make your tasks not just manageable, but downright delightful! Let’stake a dive and explore what wonders await, "shell" we? 🐚
		""",
    thread_ts=message["ts"],
  )
  say(
    f"""
*Commands*:
=> `_piscine <campus> <year> <month> [filter] [order]`
Dive deep into the Piscine details with zest! 🏊‍♀️
Optional filter: `warn`, `care`.
Optional order: `alpha`, `proj`.
=> `_student <username>`
Let's explore the stellar journey of our dedicated pisciner! 🚀
=> `_locate <student_name_or_computer_id> [campus]`
On a quest to identify/locate a pisciner? I'm on it with bells on! 🔔
=> `_giveup <campus> <year> <month> <begin_at> <end_at>`
Wanna know how many give-ups we might have on a given week of this Piscine? Let's find out! 🤔

Let's make this piscine a success <@{user}>! 🌟
        """,  # noqa
    thread_ts=message["ts"],
  )


@app.message(re.compile("(_piscine|_p)"))
@timed
def get_piscine(message, say, client):
  """
  Handle the '_piscine' command to retrieve piscine data.

  Args:
      message (dict): The message payload from Slack.
      say (function): Function to send a message back to Slack.
      client (slack_sdk.WebClient): The Slack WebClient instance.

  Returns:
      None
  """
  logger.info("get_piscine()")

  user = message["user"]
  words = message["text"].lower().split()

  # Validate number of tokens.
  if len(words) < 4 or len(words) > 6:
    say(
      f"""
  Oopsie-daisy <@{user}>! It looks like the command format is a bit off.
  Use `_piscine <campus> <year> <month> [filter] [order]`.
  Optional filters: `warn`, `care` and optional orders: `alpha`, `proj`.
  Let's get it right and dive back in! 🌊
          """,
      thread_ts=message["ts"],
    )
    return

  # Extract the mandatory parameters.
  campus = words[1]
  year = words[2]
  month = words[3]

  # Initialize optional parameters.
  filter_token = None

  order_token = None
  order = None
  filter = None

  if len(words) == 4:
    order = "alpha"

  elif len(words) == 5:
    token = words[4]
    # Check whether the token is a filter or order flag.
    if token in ["warn", "care"]:
      filter_token = token
      filter = filter_token
      order = "alpha"
    elif token in ["alpha", "proj"]:
      order_token = token
      order = order_token
    else:
      say(
        f"""
  Oh dear, <@{user}>! The argument `{token}` isn't recognized.
  Please use `warn` or `care` as a filter, or `alpha` or `proj` as an order.
      """,
        thread_ts=message["ts"],
      )
      return

  elif len(words) == 6:
    filter_token = words[4]
    order_token = words[5]

    if filter_token in ["warn", "care"]:
      filter = filter_token
    else:
      say(
        f"""
  Oopsie, <@{user}>! The filter argument `{filter_token}` is not recognized.
  Please use `warn` or `care` as a filter.
        """,
        thread_ts=message["ts"],
      )
      return

    if order_token in ["alpha", "proj"]:
      order = order_token

    else:
      say(
        f"""
    Uh-oh, <@{user}>! The order argument `{order_token}` is not recognized.
    Please use `alpha` or `proj` as an order.
                """,
        thread_ts=message["ts"],
      )
      return

  # Capitalize campus and month names for display.
  campus_caps = campus.title()
  month_caps = month.title()

  try:
    if len(words) == 4 or len(words) == 5:
      say(
        f"""
⌛ Hold on to your swim cap <@{user}>! 🏊‍♂️
I'm diving headfirst into fetching data for Piscine *{month_caps} {year}* in *{campus_caps}*{f" filtered by {filter}" if filter else ""}{f" with order {order}" if order else ""}.
My circuits are buzzing with anticipation—this data is coming in hot! 🔥🤖
Just sit back, relax, and let Eddie handle it! 🚀
        """,
        thread_ts=message["ts"],
      )
    else:
      say(
        f"""
⌛ Hold on tight, <@{user}>! 🏊‍♂️
Fetching data for Piscine *{month_caps} {year}* in *{campus_caps}*{f" filtered by {filter}" if filter else ""}{f" with order {order}" if order else ""}.
My digital heart is racing—this is going to be spectacularly awesome! 💥🚀
        """,
        thread_ts=message["ts"],
      )

    # Attempt to get piscine data from the API
    piscine_data = get_piscine_data(campus, year, month)
    # Write piscine_data to a file for debugging
    # with open("piscine_data_debug.json", "w") as file:
    #     json.dump(piscine_data, file, indent=4)
    logging.info("Piscine data written to piscine_data_debug.json for debugging.")
    logging.info(f"Piscine data retrieved: {piscine_data}")
    logging.info(f"Piscine data retrieved: {piscine_data}")

    if piscine_data is None:
      say(
        f"""
Oh no, <@{user}>! I encountered a glitch in the matrix while fetching data for Piscine at *{campus_caps}* in *{month_caps} {year}*. 🤖
Don't fret—I'll be rebooting my enthusiasm and trying again! Check the logs for more cosmic clues. 🌈 Let's keep the positivity flowing! ✨
								""",
        thread_ts=message["ts"],
      )
      return
    elif not piscine_data:
      say(
        f"""
Hmm, <@{user}>, it seems the data pool for Piscine at *{campus_caps}* in *{month_caps} {year}* is as empty as a black hole. 🕳️
Double-check your command and let's get those pisciners making waves! 🌊 I'm here to help make it happen! 🚀
        """,
        thread_ts=message["ts"],
      )
      return

    # count total amount os student in 42 POrto campus
    total = 0
    for student in piscine_data:
      total += 1
    print(f"Total students: {total}")

    # List to store filtered student information
    filtered_piscine_data = [
      student
      for student in piscine_data
      if student.get("pool_month") == month and student.get("pool_year") == year
    ]
    for student in filtered_piscine_data:
      pprint(f"Added to filtered list: {student}")

    # Create dictionaries to store pisciner w/ different flags
    all_student_info = {}
    warn_students = {}
    care_students = {}
    regular_students = {}

    for student in filtered_piscine_data:
      username = student["login"]
      full_name = f"{student['first_name']} {student['last_name']}"
      student_data = get_student_data(username)
      validated = get_nvalidated_projects(student_data)
      intra_url = "https://profile.intra.42.fr/users/" + username
      logging.info(f"Got student data for {username}")
      # Count specific project completions
      projects_users = student_data["projects_users"]
      for proj in projects_users:
        project_name = proj["project"]["name"]
        if (
          project_name.startswith("C Piscine")
          and proj["validated?"]
          and project_name
          in [
            "C Piscine Shell 00",
            "C Piscine Shell 01",
            "C Piscine C 00",
            "C Piscine C 01",
            "C Piscine C 02",
            "C Piscine C 03",
            "C Piscine C 04",
            "C Piscine C 05",
            "C Piscine C 06",
            "C Piscine C 07",
            "C Piscine C 08",
            "C Piscine C 09",
            "C Piscine C 10",
            "C Piscine C 11",
            "C Piscine C 12",
            "C Piscine C 13",
          ]
        ):
          global_project_counts[project_name] += 1

      # Prepare the common student entry
      student_entry = {
        "full_name": full_name,
        "validated": validated,
        "data": student_data,
        "intra_url": intra_url,
      }
      # Add to the "all" container
      all_student_info[username] = student_entry

      flag = warning_status(student_data)
      if flag == 1:  # Warn
        warn_students[username] = student_entry
      elif flag == 2:  # Care
        care_students[username] = student_entry
      else:  # Regular pisciner with no flags
        regular_students[username] = student_entry
      sleep(0.33)

    warn_students_list = []
    care_students_list = []
    regular_students_list = []

    # Sort the lists based on [order] argument
    if order == "alpha" or order is None:
      warn_students_list = sorted(warn_students.items(), key=lambda x: x[0].lower())
      care_students_list = sorted(care_students.items(), key=lambda x: x[0].lower())
      regular_students_list = sorted(
        regular_students.items(), key=lambda x: x[0].lower()
      )
    elif order == "proj":
      warn_students_list = sorted(
        warn_students.items(), key=lambda x: x[1]["validated"], reverse=True
      )
      care_students_list = sorted(
        care_students.items(), key=lambda x: x[1]["validated"], reverse=True
      )
      regular_students_list = sorted(
        regular_students.items(), key=lambda x: x[1]["validated"], reverse=True
      )

    warn_students_text = "\n".join(  # Create text for Warn flagged pisciner
      [
        f"<{student_info['intra_url']}|{username}>\t{student_info['validated']}\t{student_info['full_name']}"
        for username, student_info in warn_students_list
      ]
    )
    care_students_text = "\n".join(  # Create text for Care flagged pisciner
      [
        f"<{student_info['intra_url']}|{username}>\t{student_info['validated']}\t{student_info['full_name']}"
        for username, student_info in care_students_list
      ]
    )
    regular_students_text = "\n".join(  # Create text for Regular pisciner
      [
        f"<{student_info['intra_url']}|{username}>\t{student_info['validated']}\t{student_info['full_name']}"
        for username, student_info in regular_students_list
      ]
    )

    # get the formatted project counts
    project_counts_output = format_piscine_projects()

    student_count = 0
    if all_student_info:
      student_count = len(all_student_info)
      filter = filter_token

      # Determine which container to print based on the filter argument
      if filter is None:
        # No filter provided: print all pisciner container only
        final_message = f"""
 🎉 Amazing news, <@{user}>! I've splashed through the data and gathered info for *Piscine {month_caps} {year} in {campus_caps}*!
 A whopping `{student_count}` pisciners have been detected making digital waves:
 
 📊 *Project Validation Counts*:
 {project_counts_output}
 
 🚨 *Warn flagged* pisciners:
 {warn_students_text if warn_students_text else "None found—still, keep your chin up and swim on!"}
 
 🚼 *Care flagged* pisciners:
 {care_students_text if care_students_text else "No care flags here—smooth sailing ahead!"}
 
 ✅ *Regular* pisciners:
 {regular_students_text if regular_students_text else "No regulars? That’s a head-scratcher..."} 🌟
 
 Let’s ride these waves of success together! 🌊🚀
           """
      elif filter.lower() == "warn":
        # Filter by "warn": print only warn flagged pisciner
        final_message = f"""
 Hey <@{user}>! Here are the *Warn flagged* pisciners for Piscine {month_caps} {year} in {campus_caps}:
 
 :rotating_light: *Warn flagged* pisciners:
 {warn_students_text if warn_students_text else "No warn flagged pisciners found—what a surprise!"}
           """
      elif filter.lower() == "care":
        # Filter by "care": print only care flagged pisciner
        final_message = f"""
Hey <@{user}>! Here are the *Care flagged* pisciners for Piscine {month_caps} {year} in {campus_caps}:

🚼 *Care flagged* pisciners:
{care_students_text if care_students_text else "No care flagged pisciners found—everything's peachy!"}
         """
      else:
        # If an unknown filter is provided, you can choose to default or send an error message.
        final_message = f"""
Oh dear <@{user}>! The filter `{filter}` is not recognized.
Please use either `warn` or `care` as an optional filter, or omit the filter to see all pisciner.
         """

      say(final_message, thread_ts=message["ts"])

    else:
      say(
        f"""
Oh dear! <@{user}>, it seems no pisciner match the criteria for Piscine {month_caps} {year} in {campus_caps}{" filtered by " + filter if filter else ""}.
Let's recalibrate our sensors and give it another whirl! 🌈
         """,
        thread_ts=message["ts"],
      )

  except Exception as e:
    logging.error(f"Error in get_piscine: {str(e)}")
    say(
      f"""
 Oopsie <@{user}>! An error occurred while processing the command.
 Don't worry—I’m rebooting my enthusiasm and will be back stronger!
 Check the logs for more deets. 🌟
 						""",
      thread_ts=message["ts"],
    )


@app.message(re.compile("(_student|_s)"))
@timed
def get_student(message, say):
  """
  Handle the `_student` command to retrieve student data.

  Args:
      message (dict): The message rayload from Slack.
      say (function): Function to send a message back to Slack.

  Returns:
      None
  """
  logger.info("get_student()")

  user = message["user"]
  words = message["text"].lower().split()
  if len(words) != 2:
    say(
      f"""
Oh snap, <@{user}>! That command didn't light up my circuits.
Remember: `_student <username>`.
Let's try that again and make the data dance! 🌌✨
      """,
      thread_ts=message["ts"],
    )
    return
  if message["text"].lower().startswith("_student") or message[
    "text"
  ].lower().startswith("_s"):
    try:
      # Extract the username from the message
      user = message["text"].split(" ")[1]
      student_data = get_student_data(user)
      # with open("student_data.json", "w") as file:
      #   json.dump(student_data, file, indent=4)
      get_nvalidated_projects(student_data)
      if student_data:
        formatted_info = format_student_info(student_data)
        say(formatted_info, thread_ts=message["ts"])
      else:
        say(
          f"""
Oh no, <@{user}>! The student username seems to be off the grid.
Double-check the spelling and let's try again—I'm here and super excited to help! 🌟
					""",
          thread_ts=message["ts"],
        )
    except IndexError:
      say(
        "Invalid command format. Use `_student <username>`",
        thread_ts=message["ts"],
      )


@app.message(re.compile("(_locate|_l)"))
@timed
def locate_student(message, say):
  """
  Handle the '_locate' command to locate a student or computer.

  Args:
      message (dict): The message payload from Slack.
      say (function): Function to send a message back to Slack.

  Returns:
      None
  """
  logger.info("locate_student()")
  user = message["user"]
  words = message["text"].lower().split()
  if len(words) < 2 or len(words) > 3:
    say(
      f"""
Hold your digital horses, <@{user}>! The command format seems a bit wonky.
Use `_locate <student_name_or_computer_id> [campus]` and let's set off on this treasure hunt! 🕵️‍♂️💥
						""",
      thread_ts=message["ts"],
    )
    return

  # Extract the identifier and campus (if provided) from the message
  identifier = words[1]
  campus = words[2] if len(words) == 3 else None
  try:
    student_name, location = get_student_location(identifier, campus)
    if student_name is not None:
      intra_url = "https://profile.intra.42.fr/users/" + student_name
      say(
        f"""
🔍 *Searching* for {words[1]}...
""",
        thread_ts=message["ts"],
      )
    # Check if the identifier is a computer ID
    if (
      identifier.startswith("c")
      and identifier.find("r") != -1
      and identifier.find("s") != -1
    ):
      if identifier is not None and student_name is not None:
        say(
          f"""
💻 Astonishing news, <@{user}>
The computer *{identifier}* is proudly occupied by <{intra_url}|{student_name}>!
My circuits are sparking with joy—rock on, digital superstar! 🤖🌟 Bleep-Bloop!
                                    """,
          thread_ts=message["ts"],
        )
      else:
        say(
          f"""
💻 Bummer, <@{user}>! It seems computer *{identifier}* is enjoying some alone time.
Maybe it's recharging its batteries for more epic tasks?
Give it another go and look up someone else! ⚡️
          """,
          thread_ts=message["ts"],
        )
    else:
      if location is not None:  # if the student is at the cluster
        say(
          f"""
🎒 Spectacular, <@{user}>!
The student *{student_name}* is currently hanging out at workstation: *{location}*!
I’m practically buzzing with excitement—onwards to more adventures! 🚀🤩
          """,
          thread_ts=message["ts"],
        )
      else:  # else if the student is not at the cluster
        say(
          f"""
🎒 Bummer, <@{user}>! It looks like the student <{intra_url}|{student_name}> is not at the cluster yet.
Maybe it's on a break or in a meeting?
Give it another go and look up someone else! ⚡️
""",
          thread_ts=message["ts"],
        )

  except Exception as e:
    logging.error(f"Error in locate_student: {str(e)}")
    say(
      f"""
Oopsie-daisy, <@{user}>! I stumbled over some digital wires while trying to locate the student or computer.
Don't worry—I’m already recharging my enthusiasm. Check the logs for more info! 🌟
""",
      thread_ts=message["ts"],
    )


@app.message(re.compile("(_giveup|_gu)"))
@timed
def get_giveup(message, say):
  """
  Handle the '_giveups' command to retrieve potential give-up data for a Piscine.

  Args:
      message (dict): The message payload from Slack.
      say (function): Function to send a message back to Slack.

  Returns:
      None
  """
  logger.info("get_giveup()")
  user = message["user"]  # Get username
  # Split comamnd arguments
  words = message["text"].split(maxsplit=5)

  # Validate number of tokens.
  if len(words) != 6:
    say(
      f"""
Oopsie-daisy <@{user}>! It looks like the command format is a bit off. 😅
Use `_giveup <campus> <year> <month> <begin_at> <end_at>`. Let's get it right and dive back in! 🌊
I'm here to make sure we swim smoothly through this! 🏊‍♂️✨
""",
      thread_ts=message["ts"],
    )
    return

  campus = words[1]
  year = words[2]
  month = words[3]
  begin_at = words[4]
  end_at = words[5]


# Validate that begin_at and end_at are valid dates
  try:
    begin_at = datetime.strptime(begin_at, "%Y-%m-%d")
    end_at = datetime.strptime(end_at, "%Y-%m-%d")

    if begin_at > end_at:
        say(
            f"Uh-oh, <@{user}>! The start date (*{begin_at.strftime('%Y-%m-%d')}*) cannot be later than the end date (*{end_at.strftime('%Y-%m-%d')}*). ⏳",
            thread_ts=message["ts"],
        )
        return
  except ValueError:
    say(
        f"Oops, <@{user}>! The dates *must* be in `YYYY-MM-DD` format. 📅 Try again! 🌟",
        thread_ts=message["ts"],
    )
    return

  # Store the context
  user_context[user] = {
    "campus": campus,
    "year": year,
    "month": month,
    "begin_at": begin_at,
    "end_at": end_at,
    "ts": message["ts"],
  }

  say(  # Prompt the user for a date
    f"""
Got it, <@{user}>! 🚀
So you want to check giveups from {begin_at} to {end_at}, right?
I'm on it!! Don't you worry, I'll be right back with all the info you need! 🤖
""",
    thread_ts=message["ts"],
  )
  handle_giveup_piscine_start_date(message, say)


@app.message(re.compile(r"\d{4}-\d{2}-\d{2}"))
@timed
def handle_giveup_piscine_start_date(message, say):
  """
  Handle date input from the user to calculate potential give-ups for a Piscine.

  Args:
      message (dict): The message payload from Slack.
      say (function): Function to send a message back to Slack.

  Returns:
      None
  """
  logger.info("handle_giveup_piscine_start_date()")
  lifeguard = message["user"]
  date_text = message["text"]

  # try:
  #   begin_at = datetime.strptime(date_text[4], "%Y-%m-%d")
  #   end_at = datetime.strptime(date_text[5], "%Y-%m-%d")

  # Validate the date format
#   try:
#     date = datetime.strptime(date_text, "%Y-%m-%d")
#     print(f"date : {date}")
#     say(
#       f"""
# Aw men women and them babies!! 🎉
# Working on getting data of the piscine starting on:
# *{date}*,
# dutyfull you lifeguard <@{lifeguard}>!
# Wee Hee! ~<Like Antwaun Stanley>~ 🎤✨
#     """,
#       thread_ts=message["ts"],
#     )
#   except ValueError:
#     say(
#       f"Oops, <@{lifeguard}>! That doesn't look like a valid date. 📅 Please use the format YYYY-MM-DD. Let's get it right and keep the adventure going! 🌟",
#       thread_ts=message["ts"],
#     )
#     return

  # Retrieve the stored context
  context = user_context.get(lifeguard)
  if not context:
    say(
      f"""
Sorry, <@{lifeguard}>, I couldn't find your previous command. 😅
Please start over, and let's make this journey a success! 🚀
""",
      thread_ts=message["ts"],
    )
    return

  campus = context["campus"]
  year = context["year"]
  month = context["month"]
  begin_at = context["begin_at"]
  end_at = context["end_at"]
  # week = context["week"]

  # Now you can proceed with processing the request using the date
  piscine_data = get_piscine_data(campus, year, month)
  if piscine_data is None:
    say(
      f"""
Oh no, <@{lifeguard}>! I encountered a glitch in the matrix while fetching data for Piscine at *{campus_caps}* in *{month_caps} {year}*.
Don't fret—I'll be rebooting my enthusiasm and trying again! Check the logs for more cosmic clues. 🌈
								""",
      thread_ts=message["ts"],
    )
    return
  elif not piscine_data:
    say(
      f"""
Hmm, <@{lifeguard}>, it seems the data pool for Piscine at ** in * {year}* is as empty as a black hole.
Double-check your command and let's get those pisciners making waves! 🌟
        """,
      thread_ts=message["ts"],
    )
    return

  # begin_at = ""
  # end_at = ""
  # week = int(week)
  # print(f"Date {date}")
  counter = 0  # Give ups counter
  #
  # match week:
  #   case 1:
  #     begin_at = date
  #     end_at = date + timedelta(days=6)
  #     print(f"Week 1 = {begin_at}, {end_at}")
  #   case 2:
  #     begin_at = date + timedelta(days=7)
  #     end_at = date + timedelta(days=13)
  #     print(f"Week 2 = {begin_at}, {end_at}")
  #   case 3:
  #     begin_at = date + timedelta(days=14)
  #     end_at = date + timedelta(days=20)
  #     print(f"Week 3 = {begin_at}, {end_at}")
  #   case 4:
  #     begin_at = date + timedelta(days=21)
  #     end_at = date + timedelta(days=27)
  #     print(f"Week 4 = {begin_at}, {end_at}")

  for pisciner in piscine_data:  # Get each pisciner's logtime
    user = pisciner["login"]
    raw_logtime = get_logtime(pisciner, begin_at, end_at)
    try:
      logtime = int(raw_logtime)
    except (TypeError, ValueError):
      logtime = 0
    print(
      f"""
Pisciner : {user}; Logtime : {logtime}
"""
    )

    # Prepare the common student entry
    pisciner_entry = {
      "user": user,
      "logtime": logtime,
      "did_exam": False,
    }

    if logtime < (3 * 7):  # If logtime is less than 21 weekly hours
      print(f"{user} has less than 21h of logtime")
      # scale = get_scale(pisciner, begin_at, end_at)
      # if not scale:
      exam = get_exams(pisciner, 1301)
      if bool(exam):
        pisciner_entry["did_exam"] = True
        give_ups.append(pisciner_entry)
      else:
        give_ups.append(pisciner_entry)
      counter = counter + 1
    sleep(0.5)  # Avoid throttling

  # Print give ups data
  if give_ups:
    campus_caps = campus.title()
    month_caps = month.title()
    say(
      f"""
There may be *{counter}* potential give ups for piscine *{campus_caps}* in *{month_caps} {year}*. 🤔
But don't worry, I'm here to help us navigate through this! 🌟
""",
      thread_ts=message["ts"],
    )
    attended_exam = []
    attended_count = 0
    missed_exam = []
    missed_count = 0

    for give_up in give_ups:
      if not give_up["did_exam"]:
        missed_exam.append(give_up)
        missed_count = missed_count + 1
      else:
        attended_exam.append(give_up)
        attended_count = attended_count + 1

    # Sort by logtime
    attended_exam = sorted(attended_exam, key=lambda x: x["logtime"], reverse=True)
    missed_exam = sorted(missed_exam, key=lambda x: x["logtime"], reverse=True)

    intra_base_url = "https://profile.intra.42.fr/users/"
    if missed_exam:
      say(
        f"""
Oh no! 🚨
It seems the following *{missed_count}* pisciners *MISSED THE EXAM*:
{
          "\n".join(
            [
              f"<{intra_base_url}{entry['user']}|{entry['user']}> {entry['logtime']}h"
              for entry in missed_exam
            ]
          )
        }
Let's rally our cosmic energies and support them to bounce back stronger! 🌟💪
""",
        thread_ts=message["ts"],
      )

    if attended_exam:
      attended_exam_sorted = sorted(attended_exam, key=lambda entry: entry['logtime'], reverse=True)
      say(
        f"""
The following *{attended_count}* pisciners *SUBSCRIBED TO THE EXAM PROJECT*
but spended less than 21 hours between *{begin_at}* and *{end_at}*:
{
          "\n".join(
            [
              f"<{intra_base_url}{entry['user']}|{entry['user']}> {entry['logtime']}h"
              for entry in attended_exam_sorted
            ]
          )
        }
Let's find ways to nudge them to keep the momentum going!
Let's Go, Let's Go <@{lifeguard}>! 🌟✨
""",
        thread_ts=message["ts"],
      )


@app.event("app_mention")
@timed
def handle_app_mention(event, say):
  logger.info("handle_app_mention()")
  user_id = event["user"]
  say(
    f"""
Yo, <@{user_id}>! 🎉 I'm Eddie42, your friendly on-Slack assistant. How can I help you today?
"""
  )


@app.event("app_home_opened")
@timed
def handle_app_home_opened(event, say):
  logger.info("handle_app_home_opened()")
  say("Hello, <@{user}>! How can I help you today?")
