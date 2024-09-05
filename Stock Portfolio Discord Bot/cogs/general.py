import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from utils.misc.bot_misc import all_cog_choices

"""
General Cog
    This cog contains general commands that are available to all users.
"""

class General(commands.Cog, name="general"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        The code in this event is executed when the bot is ready and has successfully logged in.
        """
        pass

    @commands.hybrid_command(
        name="help", description="List all commands the bot has loaded."
    )
    @app_commands.describe(cog="The cog to get the commands from")
    @app_commands.choices(cog=all_cog_choices())
    async def help(self, context: Context, cog: str = "") -> None:
        """
        List all commands the bot has loaded.

        :param context: The hybrid command context.
        :param cog: The cog to get the commands from.
        """
        if cog != "":
            cog_object = self.bot.get_cog(cog.lower())
            if cog_object is not None:
                embed = discord.Embed(
                    title=f"{cog_object.qualified_name} Commands",
                    description=f"{cog_object.description}",
                    color=0xBEBEFE,
                )
                commands = cog_object.get_commands()
                data = []
                for command in commands:
                    data.append(f"{command.name} - {command.description}")
                embed.add_field(
                    name="Commands", value="\n".join(data), inline=False
                )
                await context.send(embed=embed)
            else:
                await context.send("That cog does not exist.")
            return

        prefix = self.bot.config["prefix"]
        embed = discord.Embed(
            title="Help", description="List of available commands:", color=0xBEBEFE
        )
        for i in self.bot.cogs:
            if i == "owner" and not (await self.bot.is_owner(context.author)):
                continue
            
            cog_object = self.bot.get_cog(i.lower())
            commands = cog_object.get_commands()
            data = []
            for command in commands:
                description = command.description.partition("\n")[0]
                data.append(f"{prefix}{command.name} - {description}")
            help_text = "\n".join(data)
            embed.add_field(
                name=i.capitalize(), value=f"```{help_text}```", inline=False
            )
        await context.send(embed=embed)

async def setup(bot) -> None:
    await bot.add_cog(General(bot))
