# This is a work in progress and is not yet complete. The code in this file is not yet functional and is not yet ready for use.

import os
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context

"""
Stocks Cog
    This cog contains commands that allow users to search for stocks and view stock information.
"""

# ========================
# Constants
# ========================

root_path = os.path.realpath(os.path.join(os.path.dirname(__file__), '..')) # Root path
yf_period_pretty = ["1 Day", "5 Days", "1 Month", "3 Months", "6 Months", "1 Year", "2 Years", "5 Years", "10 Years", "Year to Date", "Max"]
yf_period_finance = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
yf_period_choices = [app_commands.Choice(name=p, value=f) for p, f in zip(yf_period_pretty, yf_period_finance)]

# ========================
# Cog
# ========================

class Stocks(commands.Cog, name="stocks"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.colors: dict = self.bot.colors if self.bot.colors is not None else {
            "green": discord.Color.green(),
            "red": discord.Color.red(),
            "teal": discord.Color.teal(),
            "pink": discord.Color.purple()
        }
        self.holding_gifs = []

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        The code in this event is executed when the bot is ready and has successfully logged in.
        """
        # Traverse the directory tree starting from 'root_path/assets/hold'
        for root, dirs, files in os.walk(os.path.join(root_path, "assets", "hold")):
            for file in files:
                # Check if the file has a .gif extension
                if not file.endswith(".gif"):
                    continue  # Skip files that are not .gif
                
                # Construct the full path to the .gif file and append it to the list
                self.holding_gifs.append(os.path.join(root, file))

        self.colors = self.bot.colors

    @commands.hybrid_group(
        name="yahoo",
        description="Yahoo Finance commands"
    )
    @app_commands.describe(
        ticker="The stock you want to search for.",
        period="The period of time to search for the stock. Default is 1 day."
    )
    @app_commands.choices(status=yf_period_choices)
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    async def yahoo(self, context: Context, ticker: str, period = "1d") -> None:
        """
        Yahoo Finance commands

        :param context: The application command context.
        """
        pass        


    @yahoo.command(
        name="news",
        description="Displays the latest news for a specific stock",
    )
    @app_commands.describe(
        ticker="The stock you want to search for."
    )
    async def news(self, context: Context, ticker: str) -> None:
        """
        Displays the latest news for a specific stock

        :param context: The application command context.
        :param ticker: The stock that should be searched for.
        """
        pass

    @commands.hybrid_command(
        name="feargreed",
        description="Displays the Fear & Greed Index",
    )
    async def feargreed(self, context: Context) -> None:
        """
        Displays the Fear & Greed Index

        :param context: The application command context.
        """
        pass
    
async def setup(bot):
    await bot.add_cog(Stocks(bot))