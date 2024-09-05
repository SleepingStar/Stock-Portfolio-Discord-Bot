import os
import sys
import json
import pytz
import random
from datetime import datetime, time
from discord.app_commands import Choice

"""
==============================================================================================================
This file contains functions that the bot uses in niche cases.
==============================================================================================================
"""

THIS_FOLDER = os.path.realpath(os.path.dirname(__file__)) # Get the current folder

# Get the path to the config file
CONFIG_FILE = os.path.join(THIS_FOLDER, "..", "..", "config.json")
if not os.path.isfile(CONFIG_FILE):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(CONFIG_FILE, encoding='utf-8') as f:
        config = json.load(f)

# Get the path to the all_statuses.json file
STATUSES_FILE = os.path.join(THIS_FOLDER, "all_statuses.json")
if not os.path.isfile(STATUSES_FILE):
    sys.exit("'all_statuses.json' not found! Please add it and try again.")
else:
    with open(STATUSES_FILE, encoding='utf-8') as f:
        statuses_json = json.load(f)

COG_FOLDER = os.path.join(THIS_FOLDER, "..", "..", "cogs")
if not os.path.isdir(COG_FOLDER):
    sys.exit("'cogs' folder not found! Please add it and try again.")


"""
==============================================================================================================
This function will return all the cogs that are loaded in the bot in the format of a list of discord.Choice.
==============================================================================================================
"""

# This function will return all the cogs that are loaded in the bot.
def all_cog_choices():
    """
    This function will return all the cogs that are loaded in the bot.
    """
    cogChoices = [] # List of choices for the cogs
    for file in os.listdir(COG_FOLDER): # Loop through the files in the cogs folder
        if file.endswith(".py"):
            extension = file[:-3] # Get the name of the cog
            # Check if the cog is disabled
            if extension in config["disabled_cogs"]: 
                continue # Skip the cog if it is disabled
            cogChoices.append(Choice(name=extension.capitalize(), value=extension)) # Add the cog to the list of choices
    cogChoices.append(Choice(name="All", value="all")) # Add the choice to get all cogs
    return cogChoices # Return the list of choices

"""
==============================================================================================================
This function will return all the statuses that the bot can use from the all_statuses.json file.
==============================================================================================================
"""

# This class is used to store a single status of the bot
class BotStatus:
    def __init__(self, message: str, mType: str):
        self.message = message # The message that will be displayed
        self.mType = mType # The type of message that will be displayed (timed, anytime)

    async def toJson(self) -> dict:
        return {
            "message": self.message,
            "mType": self.mType
        }

# This class is used to store all the statuses that the bot can use
class Statuses:
    def __init__(self) -> None:
        self.statuses = []
    
        if (statuses_json != None):
            for status in statuses_json["statuses"]:
                self.statuses.append(BotStatus(status["message"], status["mType"]))

    # This function is used to get a new status
    async def getNewStatus(self) -> str:
        new_status: BotStatus = random.choice(self.statuses) # Get a random status
        canUpdate = await self.isItOpen(new_status.mType) # Check if the status can be updated

        while (canUpdate == -1):
            new_status = random.choice(self.statuses) # Get a random status
            canUpdate = await self.isItOpen(new_status.mType) # Check if the status can be updated

        return new_status.message # Return the new status
    
    # This function is used to check if a time is between two other times
    async def betweenTime(self, start_time, end_time, check_time, timezone='America/Chicago'):
        # Convert times to datetime objects
        start = datetime.combine(datetime.today(), start_time)
        end = datetime.combine(datetime.today(), end_time)
        check = datetime.combine(datetime.today(), check_time)
        
        # Convert start and end times to specified timezone
        tz = pytz.timezone(timezone)
        start = tz.localize(start)
        end = tz.localize(end)
        check = tz.localize(check)
        
        # Check if check_time is between start_time and end_time
        return start <= check <= end
    
    # This function is used to check if the market is open
    async def isItOpen(self, mType: str) -> int:
        if (mType == "anytime"):
            return 0
        elif (mType == "markethours" and await self.betweenTime(time(8, 30), time(16, 0), datetime.now().time())):
            return 1
        elif (mType == "afterhours" and await self.betweenTime(time(16, 0), time(20, 0), datetime.now().time())):
            return 2
        elif (mType == "premarket" and await self.betweenTime(time(4, 0), time(8, 30), datetime.now().time())):
            return 3
        else:
            return -1

    # This function is used to upload a new status
    async def uploadNewStatus(self, new_status: BotStatus) -> bool:
        self.statuses.append(new_status)

        try:
            with open(f"{os.path.realpath(os.path.dirname(__file__))}\\all_statuses.json", "w") as f:
                json_data = await self.toJson()
                json_string = json.dumps(json_data, indent=4)
                f.write(json_string)
            return True
        except:
            return False

    # This function is used to convert the statuses to JSON
    async def toJson(self) -> dict:
        return {
            "statuses": [await status.toJson() for status in self.statuses]
        }