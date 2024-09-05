import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands import Context
from utils.misc.bot_misc import all_cog_choices

"""
Owner cog
    This cog contains commands that are only available to the bot owner.
"""

class Owner(commands.Cog, name="owner"):
    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        The code in this event is executed when the bot is ready and has successfully logged in.
        """
        pass

    @commands.command(
        name="sync",
        description="Synchonizes the slash commands.",
    )
    @app_commands.describe(scope="The scope of the sync")
    @app_commands.choices(scope=[app_commands.Choice(name="global", value="global"), app_commands.Choice(name="guild", value="guild")])
    @commands.is_owner()
    async def sync(self, context: Context, scope: str) -> None:
        """
        Synchonizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the sync.
        """ 

        message = context.message

        context.bot.tree.clear_commands()

        if scope == "global":
            await context.bot.tree.sync()
        elif scope == "guild":
            context.bot.tree.copy_global_to(guild=context.guild)
        
        await message.add_reaction("✅")

    @commands.command(
        name="unsync",
        description="Unsynchonizes the slash commands.",
    )
    @app_commands.describe(
        scope="The scope of the sync."
    )
    @app_commands.choices(scope=[app_commands.Choice(name="global", value="global"), app_commands.Choice(name="guild", value="guild")])
    @commands.is_owner()
    async def unsync(self, context: Context, scope: str) -> None:
        """
        Unsynchonizes the slash commands.

        :param context: The command context.
        :param scope: The scope of the sync
        """

        message = context.message

        if scope == "global":
            context.bot.tree.clear_commands(guild=None)
            await context.bot.tree.sync()
        elif scope == "guild":
            context.bot.tree.clear_commands(guild=context.guild)
            await context.bot.tree.sync(guild=context.guild)
        
        await message.add_reaction("✅")

    @commands.hybrid_command(
        name="load",
        description="Load a cog",
    )
    @app_commands.describe(cog="The name of the cog to load")
    @commands.is_owner()
    @app_commands.choices(cog=all_cog_choices())
    async def load(self, context: Context, cog: str) -> None:
        """
        The bot will load the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to load.
        """
        message = context.message

        try:
            await self.bot.load_extension(f"cogs.{cog}")
            await message.add_reaction("✅")
        except Exception:
            embed = discord.Embed(
                description=f"Could not load the `{cog}` cog.", color=0xE02B2B
            )
            await message.add_reaction("❌")
            await context.send(embed=embed)
            return
        
    @commands.hybrid_command(
        name="unload",
        description="Unloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to unload")
    @commands.is_owner()
    @app_commands.choices(cog=all_cog_choices())
    async def unload(self, context: Context, cog: str) -> None:
        """
        The bot will unload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to unload.
        """
        message = context.message

        try:
            await self.bot.unload_extension(f"cogs.{cog}")
            await message.add_reaction("✅")
        except Exception:
            embed = discord.Embed(
                description=f"Could not unload the `{cog}` cog.", color=0xE02B2B
            )
            await message.add_reaction("❌")
            await context.send(embed=embed)
            return

    @commands.hybrid_command(
        name="reload",
        description="Reloads a cog.",
    )
    @app_commands.describe(cog="The name of the cog to reload")
    @commands.is_owner()
    @app_commands.choices(cog=all_cog_choices())
    async def reload(self, context: Context, cog: str) -> None:
        """
        The bot will reload the given cog.

        :param context: The hybrid command context.
        :param cog: The name of the cog to reload.
        """
        message = context.message

        if (cog == "all"):
            for extension in self.bot.extensions:
                try:
                    await self.bot.reload_extension(extension)
                except Exception:
                    embed = discord.Embed(
                        description=f"Could not reload the `{extension}` cog.", color=0xE02B2B
                    )
                    await message.add_reaction("❌")
                    await context.send(embed=embed)
                    return
            await message.add_reaction("✅")
            return

        try:
            await self.bot.reload_extension(f"cogs.{cog}")
            await message.add_reaction("✅")
        except Exception:
            embed = discord.Embed(
                description=f"Could not reload the `{cog}` cog.", color=0xE02B2B
            )

            await message.add_reaction("❌")
            await context.send(embed=embed)
            return

    @commands.hybrid_command(
        name="shutdown",
        description="Make the bot shutdown.",
    )
    @commands.is_owner()
    async def shutdown(self, context: Context) -> None:
        """
        Shuts down the bot.

        :param context: The hybrid command context.
        """

        message = context.message

        self.bot.logger.info("Shutting down.")
        self.bot.database.close()

        await message.add_reaction("✅")

        await self.bot.close()

async def setup(bot) -> None:
    await bot.add_cog(Owner(bot))