"""
Main entry point for the Slack bot application.

This module sets up logging, initializes the Slack bot, and starts the SocketModeHandler
to listen for events from Slack.
"""

import os
from slack_bolt.adapter.socket_mode import SocketModeHandler
import app.slack_bot as slack_bot


def main():
  """
  Main function to start the Slack bot application.

  This function initializes the SocketModeHandler with the Slack app and starts it.
  It raises an exception if the SLACK_APP_TOKEN environment variable is not set.
  """
  try:
    # Initialize the SocketModeHandler with the Slack app and token
    handler = SocketModeHandler(
      slack_bot.app, 
      os.environ["SLACK_APP_TOKEN"],
      # logging.Logger("eddie42.slack_bot")
    )
    handler.start()
  except KeyError:
    # Raise an exception if the SLACK_APP_TOKEN environment variable is not set
    raise Exception("SLACK_APP_TOKEN environment variable not set")


# Entry point for the script
if __name__ == "__main__":
  main()
