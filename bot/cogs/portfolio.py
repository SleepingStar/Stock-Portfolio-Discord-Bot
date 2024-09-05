# This file is mostly complete and is ready for use. Report any bugs to the github repository.
import os
import discord
import asyncio
import datetime
from re import search, sub
from discord import app_commands
from discord.ext import commands
from discord.app_commands import Choice
from discord.ext.commands import Context
from utils.stocker.PortfolioTypes import UserOrder
from utils.stocker.PortfolioTypes import UserOption
from utils.db_manager.user_manager import UserManager

"""
Portfolio Cog
    This cog allows the user to manage their collection of "investments" through the different commands. 
    Sooner or later, there will be a web interface to manage the portfolios.
"""

# =========
# Constants
# =========

# ticker_options
try:
    with open(os.path.join(os.path.dirname(__file__), "..", "assets", "tickers.txt"), "r") as f:
        tickers = f.read().splitlines()
        ticker_options = [Choice(name=ticker, value=ticker) for ticker in tickers]
except:
    ticker_options = []

# status_options
status_options = [Choice(name="Filled", value="Filled"), Choice(name="Pending", value="Pending")]


class Portfolio(commands.Cog, name="portfolio"):
    def __init__(self, bot) -> None:
        self.bot = bot
        self.database_users: UserManager = bot.database_users
        self.colors: dict = self.bot.colors if self.bot.colors is not None else {
            "green": discord.Color.green(),
            "red": discord.Color.red(),
            "teal": discord.Color.teal(),
            "pink": discord.Color.purple(),
            "blue": discord.Color.blue(),
            "purple": discord.Color.purple(),
            "yellow": discord.Color.gold(),
            "orange": discord.Color.orange()
        }
        self.databaseFormat: str = "%m-%d-%Y %I:%M:%S %p" 
        self.fullFormat: str = "%A %B %d, %Y at %I:%M %p"
    
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """
        The code in this event is executed when the bot is ready and has successfully logged in.
        """
        pass

    # ========================================================================================================================================================================
    # User Functions
    # ========================================================================================================================================================================

    @commands.hybrid_command(
        name="register",
        description="Registers the user from the database.",
    )
    async def register(self, context: Context) -> None:
        """
        Registers the user to the bot.

        :param context: The application command context.
        """
        
        # Check if user is registered
        if (await self.database_users.does_user_exist(context.author.id)): 
            embed = self.errorEmbed("You are already registered!")
            await context.send(embed=embed)
            return
        
        # Get user name
        in_name = context.author.global_name if context.author.global_name != None else context.author.name 

        # Add user to database
        success = await self.database_users.create_user(context.author.id, in_name) 
        
        if (not success):
            embed = self.errorEmbed("Error registering user! Please try again later.")
            await context.send(embed=embed)
            return
    
        # Get user count
        user_count = await self.database_users.get_total_user_count()

        # Send success message
        embed = discord.Embed(
            title="Welcome!",
            description="You have been successfully registered!", 
            color=self.colors["green"],
            timestamp=datetime.datetime.now()
        )
        embed.add_field(name="What now?", value="Use the \"/help portfolio\" to see what's next!", inline=False)
        embed.set_footer(text=f"You are the {ordinal(user_count)} user!")
        
        await context.send(embed=embed)

    @commands.hybrid_command(
        name="unregister",
        description="Unregisters the user from the database.",
    )
    async def unregister(self, context: Context) -> None:
        """
        Unregisters the user from the bot.

        :param context: The application command context.
        """

        # Check if user is registered
        if (not await self.database_users.does_user_exist(context.author.id)): 
            embed = self.errorEmbed("You are not registered!")
            await context.send(embed=embed)
            return
        
        success = await self.database_users.delete_user(context.author.id) # Delete user from database

        # Check if user was successfully unregistered
        if (not success):
            embed = self.errorEmbed("Error unregistering user! Please try again later.")
            await context.send(embed=embed)
            return

        embed = discord.Embed(
            title="Goodbye!",
            description="You have been successfully unregistered!", 
            color=self.colors["green"],
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="Use the /register command to register again.")

        await context.send(embed=embed)

    @commands.hybrid_command(
        name="user",
        description="Displays the user's information.",
    )
    @app_commands.describe(
        user="The user whose information should be displayed."
    )
    async def user(self, context: Context, user: discord.User = commands.Author) -> None:
        """
        Displays the user's information.

        :param context: The application command context.
        :param user: The user whose information should be displayed.
        """

        # You or They
        isSelf: bool = user == context.author
        title_your: str = f"{user.display_name}'s" if not isSelf else "Your"
        you: str = "you" if isSelf else "they"
        your: str = "your" if isSelf else "their"

        # Check if user is registered
        if not await self.database_users.does_user_exist(user.id): 
            embed = self.errorEmbed(f"{you.capitalize()} are not registered!")
            await context.send(embed=embed)
            return

        userObject = await self.database_users.get_user(user.id) # Get user

        if (userObject == None):
            embed = self.errorEmbed("Error getting user information! Please try again later.")
            await context.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"{title_your} Profile",
            description=f"Registered since {userObject['created']}",
            color=self.colors["teal"]
        )
        avatar_url = user.avatar.url if user.avatar != None else user.default_avatar.url
        embed.set_author(name=f"{user.display_name}", icon_url=avatar_url)
        embed.set_footer(text=f"{userObject['user_id']}")

        # Portfolio Field
        details = ""

        portfoliosObject = await self.database_users.get_portfolios(user.id) # Get portfolios
        portfolioList = list(portfoliosObject) if portfoliosObject != None else [] # Convert portfolios to list
        portfolioCount = len(portfolioList) # Get portfolio count

        # Portfolio Details
        if portfolioCount == 0:
            details = "No portfolios."
        else:
            for i in portfolioList:
                details += f"Portfolio {i['portfolio_id']} : {i['name']}\n"
    
        embed.add_field(name=f"{portfolioCount} {plural('portfolio')}", value=details, inline=False)

        # Watchlist Field
        details = ""

        watchlistObject = await self.database_users.get_watchlists(user.id) # Get watchlist from database
        watchlistList = list(watchlistObject) if watchlistObject != None else [] # Convert watchlist to list
        watchlistCount = len(watchlistList) # Get watchlist count

        # Watchlist Details
        if watchlistCount == 0:
            details = "No watchlists."
        else:
            for i in watchlistList:
                details += f"Watchlist {i['watchlist_id']} : {i['name']}\n"

        embed.add_field(name=f"{watchlistCount} {plural('watchlist')}", value=details, inline=False)

        await context.send(embed=embed)

    # ========================================================================================================================================================================
    # Portfolio Functions
    # ========================================================================================================================================================================
    @commands.hybrid_group(
        name="portfolio",
        description="The portfolio commands.",
    )
    async def portfolio_group(self, context: Context) -> None:
        """
        The portfolio group command.

        :param context: The application command context.
        """
        pass
    # ========================================================================================================================================================================

    @portfolio_group.command(
        name="create",
        description="Lets the user create a new portfolio.",
    )
    @app_commands.describe(
        name="The name of the portfolio that should be created.",
        description="The description of the portfolio that should be created."
    )
    async def create_portfolio(self, context: Context, name: str = "", description: str = "") -> None:
        """
        Creates a portfolio.

        :param context: The application command context.
        :param name: The name of the portfolio that should be created.
        :param description: The description of the portfolio that should be created.
        """

        user_exists = await self.database_users.does_user_exist(context.author.id) # Check if user is registered

        # Check if user is registered
        if (not user_exists): 
            embed = self.errorEmbed("You need to register first before you can create portfolios!")
            await context.send(embed=embed)
            return
        
        portfolio = await self.database_users.create_portfolio(context.author.id, name, description) # Create portfolio

        if (portfolio != None):
            timestampObject = datetime.datetime.strptime(portfolio["created"], self.databaseFormat)
            embed = discord.Embed(
                title=f"\"{portfolio['name']}\" has been successfully created!",
                description=f"{portfolio['description']}", 
                color=self.colors["green"],
                timestamp=timestampObject
            )
            embed.add_field(name="What now?", value="Use the \"/help portfolio\" to see what's next!", inline=False)
            embed.set_footer(text=f"ID: {portfolio['portfolio_id']}")
        else:
            embed = self.errorEmbed("Error creating portfolio! Please try again later.")

        await context.send(embed=embed)

    @portfolio_group.command(
        name="delete",
        description="Deletes a portfolio.",
    )
    @app_commands.describe(
        id="The ID of the portfolio that should be deleted."
    )
    async def delete_portfolio(self, context: Context, id: int) -> None:
        """
        Deletes a portfolio.

        :param context: The application command context.
        :param id: The ID of the portfolio that should be deleted.
        """ 

        user_exists = await self.database_users.does_user_exist(context.author.id) # Check if user is registered

        # Check if user is registered
        if (not user_exists): 
            embed = self.errorEmbed("You need to register first before you can delete portfolios!")
            await context.send(embed=embed)
            return
        
        portfolio = await self.database_users.get_portfolio(context.author.id, id) # Get portfolio

        # Check if user has a portfolio with the given id
        if (portfolio == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            embed.set_footer(text="Use the /portfolios command to view your portfolios.")
            await context.send(embed=embed)
            return
        
        old_name = portfolio["name"] # Get the old name
        old_id = portfolio["portfolio_id"] # Get the old id

        await self.database_users.delete_portfolio(context.author.id, id) # Delete portfolio
        
        embed = discord.Embed(
            title=f"\"{old_name}\" has been successfully deleted!",
            description=f"Please note that all your portfolio ids will be shifted down by one after deleting a portfolio.",
            color=self.colors["green"],
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text=f"ID: ~~{old_id}~~")

        await context.send(embed=embed) 

    @portfolio_group.command(
        name="view",
        description="Displays the user's portfolio.",
    )
    @app_commands.describe(
        user="The user whose portfolio should be displayed.",
        id="The ID of the portfolio that should be displayed."
    )
    async def view_portfolio(self, context: Context, user: discord.User = commands.Author, id: int = 0) -> None:
        """
        Displays the user's portfolio.

        :param context: The application command context.
        :param user: The user whose portfolio should be displayed.
        :param id: The id of the portfolio that should be displayed.
        """

        # You or They
        isSelf: bool = user == context.author
        title_your: str = f"{user.display_name}'s" if not isSelf else "Your"
        you: str = "you" if isSelf else "they"
        your: str = "your" if isSelf else "their"

        # Check if user is registered
        if not await self.database_users.does_user_exist(user.id): 
            embed = self.errorEmbed(f"{you.capitalize()} need to register first before you can view {your} portfolio!")
            await context.send(embed=embed)
            return

        # Get portfolio
        portfolio = await self.database_users.get_portfolio(user.id, id)

        if (portfolio == None):
            embed = self.errorEmbed(f"Error getting {your} portfolio! Please try again later.")
            await context.send(embed=embed)
            return
        
        datetimeObject = datetime.datetime.strptime(portfolio["created"], self.databaseFormat)

        embed = discord.Embed(
            title=f"{portfolio['name']}",
            description=f"{portfolio['description']}",
            color=self.colors["teal"],
            timestamp=datetimeObject
        )

        avatar_url = user.avatar.url if user.avatar != None else user.default_avatar.url
        embed.set_author(name=f"{title_your} Portfolio", icon_url=avatar_url)
        embed.set_footer(text=f"ID: {portfolio['portfolio_id']}")

        all_stocks = await self.database_users.get_stocks(user.id, id)

        if (all_stocks == None):
            embed = self.errorEmbed(f"Error getting {your} stocks! Please try again later.")
            await context.send(embed=embed)
            return
        
        if len(list(all_stocks)) == 0:
            if user == context.author:
                embed.add_field(name="No stocks in this portfolio!", value="Use the /stock add command to add a stock.", inline=False)
            else:
                embed.add_field(name="No stocks in this portfolio!", value=f"{user.display_name} needs to add a stock.", inline=False)  
            await context.send(embed=embed)
            return

        total_investment = await self.database_users.get_portfolio_investment(user.id, id)
        total_quantity = await self.database_users.get_portfolio_quantity(user.id, id)
        total_gain = await self.database_users.get_portfolio_gain_loss(user.id, id)
        total_dividends = await self.database_users.get_portfolio_dividends(user.id, id)
        if total_dividends != None and total_investment != None and total_gain != None:
            total = total_gain + total_investment + total_dividends
        
        embed.color = self.colors["green"] if total >= 0 else self.colors["red"]
        embed.add_field(name="Total Investment", value=f"${total_investment}", inline=True)
        embed.add_field(name="Total Quantity", value=f"{total_quantity}", inline=True)
        embed.add_field(name="Total Gain/Loss", value=f"${total_gain}", inline=True)
        embed.add_field(name="Total Dividends", value=f"${total_dividends}", inline=True)
        embed.add_field(name="Total", value=f"${total}", inline=True)

        for stock in all_stocks:
            ticker = stock["ticker"]
            stock_quantity = await self.database_users.get_stock_quantity(user.id, id, ticker)
            stock_investment = await self.database_users.get_stock_investment(user.id, id, ticker)
            stock_gain_loss = await self.database_users.get_stock_gain_loss(user.id, id, ticker)

            if stock_gain_loss != None:
                plus_minus = "+" if stock_gain_loss >= 0 else "-"
            gain_loss = str(stock_gain_loss).replace("-", "")

            embed.add_field(name=f"{ticker}", value=f"{stock_quantity} shares @ ${stock_investment}", inline=True)
            embed.add_field(name=f"${stock_gain_loss}", value=f"{plus_minus} ${gain_loss}", inline=True)

        await context.send(embed=embed)

    @portfolio_group.command(
        name="list",
        description="Displays the user's portfolios.",
    )
    @app_commands.describe(
        user="The user whose portfolios should be displayed."
    )
    async def list_portfolios(self, context: Context, user: discord.User = commands.Author) -> None:
        """
        Displays the user's portfolios.

        :param context: The application command context.
        :param user: The user whose portfolios should be displayed.
        """

        # You or They
        isSelf: bool = user == context.author
        title_your: str = f"{user.display_name}'s" if not isSelf else "Your"
        you: str = "you" if isSelf else "they"
        your: str = "your" if isSelf else "their"

        if not await self.database_users.does_user_exist(user.id):
            embed = self.errorEmbed(f"{you.capitalize()} need to register first before you can view {your} portfolios!")
            await context.send(embed=embed)
            return

        portfolios = await self.database_users.get_portfolios(user.id)

        if (portfolios == None):
            embed = self.errorEmbed(f"Error getting {your} portfolios! Please try again later.")
            await context.send(embed=embed)
            return

        portfolios = sorted(portfolios, key=lambda x: x["created"], reverse=True)
        
        if len(portfolios) == 0 and user == context.author:
            description = "Use the /portfolio create command to create a new portfolio."
        elif len(portfolios) == 0 and user != context.author:
            description = f"{user.display_name} has not started a profile yet!"
        else:
            description = f"Use the /portfolio command to view a specific portfolio."

        embed = discord.Embed(
            title=f"{you.capitalize()} have {len(portfolios)} portfolios!",
            description=description,
            color=self.colors["teal"]
        )

        avatar_url = user.avatar.url if user.avatar != None else user.default_avatar.url
        embed.set_author(name=f"{title_your} Portfolios", icon_url=avatar_url)

        for portfolio in portfolios:
            embed.add_field(name=f"[{portfolio['portfolio_id']}] {portfolio['name']}", value=f"{portfolio['description']}", inline=True)
            embed.add_field(name="Created", value=f"{portfolio['created']}", inline=False)

        await context.send(embed=embed)

    # ========================================================================================================================================================================
    # Stock Functions
    # ========================================================================================================================================================================
    @commands.hybrid_group(
        name="stock",
        description="The stock commands.",
    )
    async def stock_group(self, context: Context) -> None:
        """
        The stock group command.

        :param context: The application command context.
        """
        pass
    # ========================================================================================================================================================================

    @stock_group.command(
        name="add",
        description="Adds a stock to a portfolio.",
    )
    @app_commands.describe(
        ticker="The stock that should be added to the portfolio.",
        id="The ID of the portfolio that the stock should be added to."
    )
    @app_commands.choices(ticker=ticker_options)
    async def add_stock(self, context: Context, ticker: str, id: int = 0) -> None:
        """
        Adds a stock to a portfolio.

        :param context: The application command context.
        :param ticker: The stock that should be added to the portfolio.
        :param id: The id of the portfolio that the stock should be added to.
        """

        # Check if user is registered
        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can add stocks!")
            await context.send(embed=embed)
            return
        
        portfolio = await self.database_users.get_portfolio(context.author.id, id) # Get portfolio
        # Check if user has a portfolio with the given ID
        if (portfolio == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            embed.set_footer(text="Use the /portfolio command to view your portfolios.")
            await context.send(embed=embed)
            return
        
        # Check if stock is in database
        if (await self.database_users.get_stock(context.author.id, id, ticker) != None):
            embed = self.errorEmbed("Stock is already in your portfolio!")
            await context.send(embed=embed)
            return
        
        stock_id = await self.database_users.add_stock(context.author.id, id, ticker) # Add stock to database

        if (stock_id == -1):
            embed = self.errorEmbed("Error adding stock! Please try again later.")
            await context.send(embed=embed)
            return
        
        embed = self.successEmbed(f"{ticker} has been successfully added to portfolio \"{portfolio['name']}\"", datetime.datetime.now())
        embed.set_footer(text=f"ID: {stock_id}")
        await context.send(embed=embed)

    # ========================================================================================================================================================================
    # Order Functions
    # ========================================================================================================================================================================
    @commands.hybrid_group(
        name="order",
        description="The order commands.",
    )
    async def order_group(self, context: Context) -> None:
        """
        The order group command.

        :param context: The application command context.
        """
        pass
    # ========================================================================================================================================================================

    @order_group.command(
        name="buy",
        description="Adds a stock to a portfolio.",
    )
    @app_commands.describe(
        ticker="The stock you want to buy.", 
        price="The price the stock was bought at.", 
        quantity="The amount of the stock you bought", 
        status="The status of the stock purchase.", 
        tstamp="The timestamp of the stock purchase. (Optional: Use the format 'MM-DD-YYYY HH:MM:SS AM/PM')",
        id="The ID of the portfolio that the stock belongs to."
    )
    @app_commands.choices(ticker=ticker_options, status=status_options)
    async def buy_order(self, context: Context, ticker: str, price: float, quantity: float, status: str, tstamp: str = "", id: int = 0) -> None:
        """
        Buys a certain stock

        :param context: The application command context.
        :param ticker: The stock that should be bought by the user.
        :param price: The price the stock was bought at.
        :param status: The status of the stock purchase.
        :param tstamp: The timestamp of the stock purchase.
        :param id: The id of the portfolio that the stock belongs to.
        """

        # Check if user is registered
        if (not await self.database_users.does_user_exist(context.author.id)): 
            embed = self.errorEmbed("You need to register first before you can buy stocks!")
            await context.send(embed=embed)
            return
        
        # Check if user has a portfolio with the given ID
        user_portfolio = await self.database_users.get_portfolio(context.author.id, id)
        if (user_portfolio == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            embed.set_footer(text="Use the /portfolio command to view your portfolios.")
            await context.send(embed=embed)
            return
        
        # Check if timestamp is empty
        if tstamp == "":
            tstampObject = datetime.datetime.now()
            tstamp = tstampObject.strftime(self.databaseFormat)
        else:
            tstampObject = datetime.datetime.strptime(tstamp, self.databaseFormat)

        # Check if stock is in database
        user_stock = await self.database_users.get_stock(context.author.id, id, ticker)
        
        if (user_stock == None):
            index = await self.database_users.add_stock(context.author.id, id, ticker) # Add stock to database

            if (index == -1):
                embed = self.errorEmbed("Error adding stock! Please try again later.")
                await context.send(embed=embed)
                return
        
        # Add order to database
        uOrder = UserOrder(price, quantity, tstamp, status, "Buy")
        order_id = await self.database_users.add_order(context.author.id, id, ticker, uOrder)

        if (order_id == -1):
            embed = self.errorEmbed("Error adding order! Please try again later.")
            await context.send(embed=embed)
            return  

        # Send success message
        embed = discord.Embed(
            title=f"{status}!",
            description=f"{ticker} : Bought {quantity} shares @ ${price}",
            color=self.colors["green"],
            timestamp=tstampObject
        )
        embed.add_field(name="Want to sell the stock?", value="Use the /sell command to sell the stock.", inline=False)
        embed.set_footer(text=f"ID: {order_id}")
        await context.send(embed=embed)

    @order_group.command(
        name="sell",
        description="Sells a stock from a portfolio.",
    )
    @app_commands.describe(
        ticker="The stock you want to sell.", 
        price="The price the stock was sold at.", 
        quantity="The amount of the stock you sold", 
        status="The status of the stock sale.",
        tstamp="The timestamp of the stock sale. (Optional: Use the format 'MM-DD-YYYY HH:MM:SS AM/PM')",
        id="The ID of the portfolio that the stock belongs to."
    )
    @app_commands.choices(ticker=ticker_options, status=status_options)
    async def sell_order(self, context: Context, ticker: str, price: float, quantity: float, status: str, tstamp: str = "", id: int = 0) -> None:
        """
        Sells a certain stock

        :param context: The application command context.
        :param ticker: The stock that should be sold by the user.
        :param price: The price the stock was sold at.
        :param status: The status of the stock sale.
        :param tstamp: The timestamp of the stock sale.
        :param id: The id of the portfolio that the stock belongs to.
        """

        # Check if user is registered
        if not await self.database_users.does_user_exist(context.author.id): 
            embed = self.errorEmbed("You need to register first before you can sell stocks!")
            await context.send(embed=embed)
            return
        
        # Check if user has a portfolio with the given ID
        if (await self.database_users.get_portfolio(context.author.id, id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            embed.set_footer(text="Use the /portfolio command to view your portfolios.")
            await context.send(embed=embed)
            return
        
        if tstamp == "":
            tstampObject = datetime.datetime.now()
            tstamp = tstampObject.strftime(self.databaseFormat)
        else:
            tstampObject = datetime.datetime.strptime(tstamp, self.databaseFormat)
        
        uOrder = UserOrder(price, quantity, tstamp, status, "Sell") # Create UserOrder object
        order_id = await self.database_users.add_order(context.author.id, id, ticker, uOrder) # Add order to database

        if (order_id == -1):
            embed = self.errorEmbed("Error adding order! Please try again later.")
            await context.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"{status}!",
            description=f"{ticker}: Sold {quantity} shares @ ${price}",
            color=self.colors["green"],
            timestamp=tstampObject
        )
        embed.set_footer(text=f"ID: {order_id}")
        await context.send(embed=embed)

    @order_group.command(
        name="view",
        description="Displays a specific order.",
    )
    @app_commands.describe(
        ticker="The stock you want to view orders for.",
        id="The ID of the order that should be displayed.",
        portfolio_id="The ID of the portfolio that the stock belongs to.",
        user="The user whose order should be displayed."
    )
    @app_commands.choices(ticker=ticker_options)
    async def view_order(self, context: Context, ticker: str, id: int, portfolio_id: int = 0, user: discord.User = commands.Author) -> None:
        """
        Displays a specific order.

        :param context: The application command context.
        :param ticker: The stock that should be displayed.
        :param id: The ID of the order that should be displayed.
        :param portfolio_id: The ID of the portfolio that the stock belongs to.
        :param user: The user whose order should be displayed.
        """

        # You or They
        isSelf: bool = user == context.author
        title_your: str = f"{user.display_name}'s" if not isSelf else "Your"
        you: str = "you" if isSelf else "they"
        your: str = "your" if isSelf else "their"
        
        # Check if user is registered
        if not await self.database_users.does_user_exist(user.id): 
            embed = self.errorEmbed(f"{you.capitalize()} need to register first before you can {your} view orders!")
            await context.send(embed=embed)
            return
        
        order = await self.database_users.get_order(user.id, portfolio_id, ticker, id)

        # Check if the order exists
        if (order == None):
            embed = self.errorEmbed(f"{you.capitalize()} do not have an order with that ID!")
            await context.send(embed=embed)
            return
        
        if order['status'] == "Pending":
            color = self.colors["orange"]
        elif order['status'] == "Filled":
            color = self.colors["green"]
        else:
            color = self.colors["red"]

        embed = discord.Embed(
            title=f"{title_your} order [{id}] for {ticker}",
            description=f"{order['quantity']} @ {order['price']}",
            color=self.colors["pink"],
            timestamp=datetime.datetime.strptime(order["created"], "%m-%d-%Y %I:%M:%S %p")
        )
        avatar_url = user.avatar.url if user.avatar != None else user.default_avatar.url
        embed.set_author(name=f"{order['status']}", icon_url=avatar_url)
        embed.set_footer(text=f"ID: {id}")

        await context.send(embed=embed)

    @order_group.command(
        name="list",
        description="Displays the user's orders.",
    )
    @app_commands.describe(
        ticker="The stock you want to view orders for.",
        id="The ID of the portfolio that should be displayed.",
        user="The user whose orders should be displayed."
    )
    @app_commands.choices(ticker=ticker_options)
    async def list_orders(self, context: Context, ticker: str, id: int = 0, user: discord.User = commands.Author) -> None:
        """
        Displays the user's orders.

        :param context: The application command context.
        :param id: The ID of the portfolio that should be displayed.
        :param user: The user whose orders should be displayed.
        """

        # You or They
        isSelf: bool = user == context.author
        title_your: str = f"{user.display_name}'s" if not isSelf else "Your"
        you: str = "you" if isSelf else "they"
        your: str = "your" if isSelf else "their"
            
        # Check if user is registered
        if not await self.database_users.does_user_exist(user.id): 
            embed = self.errorEmbed(f"{you.capitalize()} need to register first before you can view {your} orders!")
            await context.send(embed=embed)
            return
        
        # Check if user has a portfolio with the given ID
        if (await self.database_users.get_portfolio(user.id, id) == None):
            embed = self.errorEmbed(f"{you.capitalize()} do not have a portfolio with that ID!")
            await context.send(embed=embed)
            return
        
        all_orders = await self.database_users.get_orders(user.id, id, ticker)

        if all_orders is None:
            embed = self.errorEmbed(f"{you.capitalize()} do not have any orders for this stock!")
            await context.send(embed=embed)
            return
        
        all_orders = sorted(all_orders, key=lambda x: x["created"], reverse=True)

        # Check if the user has any orders
        if len(all_orders) == 0:
            embed = self.errorEmbed(f"{you.capitalize()} do not have any orders for this stock!")
            await context.send(embed=embed)
            return
        

        embed = discord.Embed(
            title=f"{title_your} orders for {ticker}",
            description=f"Use the /order command to view a specific order.",
            color=self.colors["pink"]
        )
        avatar_url = user.avatar.url if user.avatar != None else user.default_avatar.url
        embed.set_author(name=f"{len(all_orders)} orders", icon_url=avatar_url)
        embed.set_footer(text=f"ID: {id}")

        for order in all_orders:
            order_date = datetime.datetime.strptime(order["created"], "%m-%d-%Y %I:%M:%S %p").strftime("%b %d, %Y at %I:%M %p")
            embed.add_field(
                name=f"Order [{order['order_id']}] on {order_date}",
                value=f"Type: {order['type']}\nPrice: {order['price']}\nQuantity: {order['quantity']}\nStatus: {order['status']}",
                inline=False
            )

        await context.send(embed=embed)

    @order_group.command(
        name="delete",
        description="Deletes a specific order.",
    )
    @app_commands.describe(
        ticker="The ID of the order that should be deleted.",
        id="The ID of the order that should be deleted.",
        portfolio_id="The ID of the portfolio that the stock belongs to."
    )
    @app_commands.choices(ticker=ticker_options)
    async def delete_order(self, context: Context, ticker: str, id: int, portfolio_id: int = 0) -> None:
        """
        Deletes a specific order.

        :param context: The application command context.
        :param ticker: The stock that should be deleted.
        :param id: The ID of the order that should be deleted.
        :param portfolio_id: The ID of the portfolio that the stock belongs to.
        """
        
        # Check if user is registered
        if not await self.database_users.does_user_exist(context.author.id): 
            embed = self.errorEmbed("You need to register first before you can delete orders!")
            await context.send(embed=embed)
            return
        
        order = await self.database_users.get_order(context.author.id, portfolio_id, ticker, id)

        # Check if the order exists
        if (order == None):
            embed = self.errorEmbed("You do not have an order with that ID!")
            await context.send(embed=embed)
            return
        
        await self.database_users.delete_order(context.author.id, portfolio_id, ticker, id)

        embed = discord.Embed(
            title=f"Order [{id}] has been successfully deleted!",
            description=f"Please note that all your order ids will be shifted down by one after deleting an order.",
            color=self.colors["green"]
        )
        embed.set_footer(text=f"ID: ~~{id}~~")
        await context.send(embed=embed)

    @order_group.command(
        name="update",
        description="Updates a specific order."
    )
    @app_commands.describe(
        ticker="The stock you want to update orders for.",
        id="The ID of the order that should be updated.",
        price="The new price of the stock.",
        quantity="The new quantity of the stock.",
        status="The new status of the stock.",
        tstamp="The new timestamp of the stock. (Optional: Use the format 'MM-DD-YYYY HH:MM:SS AM/PM')",
        portfolio_id="The ID of the portfolio that the stock belongs to."
    )
    @app_commands.choices(ticker=ticker_options, status=status_options)
    async def update_order(self, 
                           context: Context, 
                           ticker: str, 
                           id: int, 
                           price: float | None = None, 
                           quantity: float | None = None, 
                           status: str | None = None, 
                           tstamp: str | None = None, 
                           gain_loss: float | None = None,
                           portfolio_id: int = 0) -> None:
        """
        Updates a specific order.

        :param context: The application command context.
        :param ticker: The stock that should be updated.
        :param id: The ID of the order that should be updated.
        :param price: The new price of the stock.
        :param quantity: The new quantity of the stock.
        :param status: The new status of the stock.
        :param tstamp: The new timestamp of the stock.
        :param portfolio_id: The ID of the portfolio that the stock belongs to.
        """

        # Check if user is registered
        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can update orders!")
            await context.send(embed=embed)
            return
        
        # Check if user has a portfolio with the given ID
        if (await self.database_users.get_portfolio(context.author.id, portfolio_id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            embed.set_footer(text="Use the /portfolio command to view your portfolios.")
            await context.send(embed=embed)
            return
        
        orderObject = await self.database_users.get_order(context.author.id, portfolio_id, ticker, id)
        
        # Check if the order exists
        if (orderObject == None):
            embed = self.errorEmbed("You do not have an order with that ID!")
            await context.send(embed=embed)
            return

        updatedOrder = UserOrder(orderObject['price'], orderObject['quantity'], orderObject['created'], orderObject['status'], orderObject['type'], orderObject['gain_loss']) # Previous Order
        updatedOrder.updateOrder(price, quantity, tstamp, status, updatedOrder.orderType, gain_loss) # Update order

        await self.database_users.update_order(context.author.id, portfolio_id, id, ticker, updatedOrder) # Update order in database
        
        embed = discord.Embed(
            title=f"Order [{id}] has been successfully updated!",
            description=f"{ticker} : {quantity} @ {price}",
            color=self.colors["green"]
        )
        embed.set_footer(text=f"ID: {id}")
        await context.send(embed=embed)

    @order_group.command(
        name="purge",
        description="Deletes all cancelled orders in a portfolio."
    )
    @app_commands.describe(
        id="The ID of the portfolio that should be purged.",
        ticker="The stock you want to purge orders for. (Optional: Defaulted to 'all')"
    )
    @app_commands.choices(ticker=ticker_options)
    async def purge_orders(self, context: Context, id: int, ticker: str = "all") -> None:
        """
        Deletes all cancelled orders in a portfolio.

        :param context: The application command context.
        :param id: The ID of the portfolio that should be purged.
        """

        # Check if user is registered
        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can purge orders!")
            await context.send(embed=embed)
            return
        
        # Check if user has a portfolio with the given ID
        if (await self.database_users.get_portfolio(context.author.id, id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            embed.set_footer(text="Use the /portfolio command to view your portfolios.")
            await context.send(embed=embed)
            return
        
        # warn user that all orders will be deleted
        embed = discord.Embed(
            title=f"Warning!",
            description=f"Are you sure you want to purge all orders in this portfolio?",
            color=self.colors["orange"]
        )
        embed.set_footer(text="This action cannot be undone.")
        sent = await context.send(embed=embed)

        await sent.add_reaction("✅")
        await sent.add_reaction("❌")

        def check(reaction, user):
            return user == context.author and str(reaction.emoji) in ["✅", "❌"]
        
        try:
            reaction, user = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"Action Cancelled!",
                description=f"Your action has been cancelled.",
                color=self.colors["red"]
            )
            await context.send(embed=embed)
            return
        
        if str(reaction.emoji) == "❌":
            embed = discord.Embed(
                title=f"Action Cancelled!",
                description=f"Your action has been cancelled.",
                color=self.colors["red"]
            )
            await context.send(embed=embed)
            return

        await self.database_users.purge_orders(context.author.id, id, ticker) # Purge orders in database

        embed = discord.Embed(
            title=f"Orders have been successfully purged!",
            description=f"Remember that all your order IDs will be shifted down after purging orders.",
            color=self.colors["green"]
        )
        await context.send(embed=embed)

    # ========================================================================================================================================================================
    # Dividend Functions
    # ========================================================================================================================================================================
    @commands.hybrid_group(
        name="dividend",
        description="The dividend commands.",
    )
    async def dividend_group(self, context: Context) -> None:
        """
        The dividend group command.

        :param context: The application command context.
        """
        pass
    # ========================================================================================================================================================================

    @dividend_group.command(
        name="add",
        description="Adds a dividend to a stock",
    )
    @app_commands.describe(
        ticker="The stock you want to add a dividend to.",
        dividend="The dividend amount.",
        id="The ID of the portfolio that the stock belongs to.",
        tstamp="The timestamp of the dividend. (Optional: Use the format 'MM-DD-YYYY HH:MM:SS AM/PM')"
    )
    async def add_dividend(self, 
                           context: Context, 
                           ticker: str, 
                           dividend: float, 
                           id: int = 0, 
                           tstamp: str = "") -> None:
        """
        Adds a dividend to a stock

        :param context: The application command context.
        :param ticker: The stock that should be added a dividend to.
        :param dividend: The dividend amount.
        :param id: The id of the portfolio that the stock belongs to.
        :param tstamp: The timestamp of the dividend.
        """

        # Check if user is registered
        if not await self.database_users.does_user_exist(context.author.id): 
            embed = self.errorEmbed("You need to register first before you can add dividends!")
            await context.send(embed=embed)

        # Check if user has a portfolio with the given ID
        if (await self.database_users.get_portfolio(context.author.id, id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            embed.set_footer(text="Use the /portfolio command to view your portfolios.")
            await context.send(embed=embed)
            return
        
        # Check if stock exists
        stock = await self.database_users.get_stock(context.author.id, id, ticker)
        if (stock == None):
            await self.database_users.add_stock(context.author.id, id, ticker) # Add stock to database
        
        if tstamp == "":
            tstampObject = datetime.datetime.now()
            tstamp = tstampObject.strftime(self.databaseFormat)

        dividend_id = await self.database_users.add_dividend(context.author.id, id, ticker, dividend, tstamp) # Add dividend to database

        embed = discord.Embed(
            title=f"Success!",
            description=f"Dividend of ${dividend} has been successfully added to stock {ticker}!",
            color=self.colors["green"],
            timestamp=tstampObject
        )
        embed.set_footer(text=f"ID: {dividend_id}")
        await context.send(embed=embed)

    @dividend_group.command(
        name="list",
        description="Displays the user's dividends.",
    )
    @app_commands.describe(
        ticker="The stock you want to view dividends for.",
        id="The ID of the portfolio that should be displayed.",
        user="The user whose dividends should be displayed."
    )
    async def list_dividends(self, 
                             context: Context, 
                             ticker: str = "all", 
                             id: int = 0, 
                             user: discord.User = commands.Author) -> None:
        """
        Displays the user's dividends.

        :param context: The application command context.
        :param ticker: The stock that should be viewed dividends for.
        :param id: The ID of the portfolio that should be displayed.
        :param user: The user whose dividends should be displayed.
        """

        # You or They
        isSelf: bool = user == context.author
        title_your: str = f"{user.display_name}'s" if not isSelf else "Your"
        you: str = "you" if isSelf else "they"
        your: str = "your" if isSelf else "their"
        avatar_url = user.avatar.url if user.avatar != None else user.default_avatar.url

        # Check if user is registered
        if not await self.database_users.does_user_exist(user.id): 
            embed = self.errorEmbed(f"{you.capitalize()} need to register first before you can view {your} dividends!")
            await context.send(embed=embed)
            return
        
        # Check if user has a portfolio with the given ID
        if (await self.database_users.get_portfolio(user.id, id) == None):
            embed = self.errorEmbed(f"{you.capitalize()} do not have a portfolio with that ID!")
            embed.set_footer(text=f"Use the \"/portfolios\" command to view {your} portfolios.")
            await context.send(embed=embed)
            return
        
        if (ticker == "all"):
            all_dividends = await self.database_users.get_dividends(user.id, id)
            
            if all_dividends is None:
                embed = self.errorEmbed(f"{you.capitalize()} do not have any dividends!")
                await context.send(embed=embed)
                return
            
            all_dividends = sorted(all_dividends, key=lambda x: x["created"], reverse=True)

            # Check if the user has any dividends
            if len(all_dividends) == 0:
                embed = self.errorEmbed(f"{you.capitalize()} do not have any dividends!")
                await context.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"{title_your} Dividends",
                description=f"Use the \"/dividends [ticker]\" command to view dividends for a specific stock.",
                color=self.colors["blue"]
            )
            
            embed.set_author(name=f"{len(all_dividends)}", icon_url=avatar_url)

            for dividend in all_dividends:
                owns = await self.database_users.get_dividend_count_by_ticker(user.id, id, dividend["ticker"])
                embed.add_field(name=f"{dividend['ticker']}", value=f"{owns} dividends", inline=False)
            
            await context.send(embed=embed)
            return

        stock = await self.database_users.get_stock(user.id, id, ticker)
        
        # Check if stock exists
        if (stock == None):
            embed = self.errorEmbed(f"{you.capitalize} do not have a stock with that ticker!")
            await context.send(embed=embed)
            return

        all_dividends = await self.database_users.get_dividends_by_ticker(user.id, id, ticker)

        if all_dividends is None:
            embed = self.errorEmbed(f"{you.capitalize()} do not have any dividends for this stock!")
            await context.send(embed=embed)
            return
        
        all_dividends = sorted(all_dividends, key=lambda x: x["created"], reverse=True)

        # Check if the user has any dividends
        if len(all_dividends) == 0:
            embed = self.errorEmbed(f"{you.capitalize()} do not have any dividends for this stock!")
            await context.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"{title_your} Dividends for {ticker}",
            description=f"{len(all_dividends)} dividends found!",
            color=self.colors["blue"]
        )
        embed.set_author(name=f"{len(all_dividends)}", icon_url=avatar_url)

        for dividend in all_dividends:
            added = datetime.datetime.strptime(dividend["created"], "%m-%d-%Y %I:%M:%S %p").strftime("%b %d, %Y at %I:%M %p")
            embed.add_field(name=f"[{dividend['dividend_id']}] : {added}", value=f"${dividend['dividend']}", inline=False)

        await context.send(embed=embed)

    @dividend_group.command(
        name="delete",
        description="Deletes a specific dividend.",
    )
    @app_commands.describe(
        ticker="The stock that the dividend is for.",
        id="The id of the dividend that should be deleted.",
        portfolio_id="The id of the portfolio that the dividend is in."
    )
    @app_commands.choices(ticker=ticker_options)
    async def delete_dividend(self, context: Context, ticker: str, id: int, portfolio_id: int = 0) -> None:
        """
        Deletes a specific dividend.

        :param context: The application command context.
        :param ticker: The stock that the dividend is for.
        :param id: The id of the dividend that should be deleted.
        :param portfolio_id: The id of the portfolio that the dividend is in.
        """
        
        # Check if user is registered | If not, send an error message
        if not await self.database_users.does_user_exist(context.author.id): 
            embed = self.errorEmbed("You need to register first before you can delete dividends!")
            await context.send(embed=embed)
            return
        
        # Check if user has a portfolio with the given ID | If not, send an error message
        if (await self.database_users.get_portfolio(context.author.id, portfolio_id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            await context.send(embed=embed)
            return

        # Check if stock exists | If not, send an error message
        if (await self.database_users.get_stock(context.author.id, portfolio_id, ticker) == None):
            embed = self.errorEmbed("You do not have a stock with that ticker!")
            await context.send(embed=embed)
            return

        dividend = await self.database_users.get_dividend(context.author.id, portfolio_id, ticker, id) # Get dividend

        # Check if the dividend exists | If not, send an error message
        if (dividend == None):
            embed = self.errorEmbed("You do not have a dividend with that ID!")
            await context.send(embed=embed)
            return
        
        await self.database_users.delete_dividend(context.author.id, portfolio_id, ticker, id) # Delete dividend

        embed = discord.Embed(
            title=f"Success!",
            description=f"Please note that all your dividend ids will be shifted down by one after deleting a dividend.",
            color=self.colors["green"]
        )
        embed.set_footer(text=f"ID: ~~{id}~~")

        await context.send(embed=embed)
        
    # ========================================================================================================================================================================
    # Watchlist Functions
    # ========================================================================================================================================================================
    @commands.hybrid_group(
        name="watchlist",
        description="The watchlist commands.",
    )
    async def watchlist_group(self, context: Context) -> None:
        """
        The watchlist group command.

        :param context: The application command context.
        """
        pass
    # ========================================================================================================================================================================

    @watchlist_group.command(
        name="list",
        description="Displays the user's watchlists.",
    )
    @app_commands.describe(
        user="The user whose watchlists should be displayed."
    )
    async def list_watchlists(self, context: Context, user: discord.User = commands.Author) -> None:
        """
        Displays the user's watchlists.
        
        :param context: The application command context.
        """

        isSelf: bool = user == context.author
        title_your: str = f"{user.display_name}'s" if not isSelf else "Your"
        you: str = "you" if isSelf else "they"
        your: str = "your" if isSelf else "their"
        avatar_url = user.avatar.url if user.avatar != None else user.default_avatar.url

        if not await self.database_users.does_user_exist(user.id):
            embed = discord.Embed(
                description=f"{you.capitalize()} need to register first before you can view {your} watchlists!", color=self.colors["red"]
            )
            await context.send(embed=embed)
            return

        watchlists = await self.database_users.get_watchlists(user.id)

        if watchlists == None:
            embed = discord.Embed(
                description=f"{you.capitalize()} do not have any watchlists!", color=self.colors["red"]
            )
            await context.send(embed=embed)
            return
        
        watchlists = sorted(watchlists, key=lambda x: x["created"], reverse=True)

        if len(watchlists) == 0:
            embed = discord.Embed(
                description=f"{you.capitalize()} do not have any watchlists!", color=self.colors["red"]
            )
            await context.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"{len(watchlists)} Watchlists Found!",
            description=f"Use the /watchlist [id] command to view a specific watchlist.",
            color=self.colors["purple"]
        )
        embed.set_author(name=f"{title_your} Watchlists", icon_url=avatar_url)

        for watchlist in watchlists:
            watching_count = await self.database_users.get_watchlist_stock_count(user.id, watchlist["watchlist_id"])
            watching_date = datetime.datetime.strptime(watchlist["created"], "%m-%d-%Y %I:%M:%S %p").strftime("%B %d, %Y at %I:%M %p")
            
            embed.add_field(name=f"[{watchlist['watchlist_id']}] {watchlist['name']}", value=f"{watchlist['description']}", inline=False)
            embed.add_field(name=f"Watching {watching_count} stocks.", value=f"Created on {watching_date}", inline=True)

        await context.send(embed=embed)

    @watchlist_group.command(
        name="view",
        description="Displays the user's watchlist.",
    )
    @app_commands.describe(
        id="The ID of the watchlist that should be displayed.",
        user="The user whose watchlist should be displayed."
    )
    async def view_watchlist(self, context: Context, id: int = 0, user: discord.User = commands.Author) -> None:
        """
        Displays the user's watchlist.

        :param context: The application command context.
        :param id: The ID of the watchlist that should be displayed.
        :param user: The user whose watchlist should be displayed.
        """
        
        isSelf: bool = user == context.author
        title_your: str = f"{user.display_name}'s" if not isSelf else "Your"
        you: str = "you" if isSelf else "they"
        your: str = "your" if isSelf else "their"
        avatar_url = user.avatar.url if user.avatar != None else user.default_avatar.url

        if not await self.database_users.does_user_exist(user.id):
            embed = self.errorEmbed(f"{you.capitalize()} need to register first before you can view {your} watchlists!")
            await context.send(embed=embed)
            return

        watchlist = await self.database_users.get_watchlist(user.id, id)

        if watchlist == None:
            embed = self.errorEmbed(f"{you.capitalize()} do not have a watchlist with that ID!")
            await context.send(embed=embed)
            return

        embed = discord.Embed(
            title=f"{watchlist['name']}",
            description=f"{watchlist['description']}",
            timestamp=datetime.datetime.strptime(watchlist["created"], "%m-%d-%Y %H:%M:%S %p"),
            color=self.colors["purple"]
        )
        embed.set_author(name=f"{title_your} Watchlist", icon_url=avatar_url)
        embed.set_footer(text=f"ID: {watchlist['watchlist_id']}")

        all_stocks = await self.database_users.get_watchlist_stocks(user.id, watchlist["watchlist_id"])
        
        if all_stocks == None:
            embed.add_field(name="It's empty!", value="No stocks in this watchlist!", inline=False)
            await context.send(embed=embed)
            return
        
        all_stocks = sorted(all_stocks, key=lambda x: x["created"], reverse=True)

        if len(all_stocks) == 0:
            embed.add_field(name="It's empty!", value="No stocks in this watchlist!", inline=False)
            await context.send(embed=embed)
            return
        
        all_text = ""
        for stock in all_stocks:
            since = datetime.datetime.strptime(watchlist["created"], "%m-%d-%Y %I:%M:%S %p").strftime("%B %d, %Y")
            all_text += f"{stock['ticker']} | watching since ({since})\n"

        embed.add_field(name=f"{len(all_stocks)} stocks found!", value=all_text, inline=False)

        await context.send(embed=embed)

    @watchlist_group.command(
        name="add",
        description="Adds a stock to the user's watchlist either by ID or by name.",
    )
    @app_commands.describe(
        ticker="The stock that should be added to the watchlist.",
        id="The id of the watchlist that the stock should be added to.",
        name="The name of the watchlist that the stock should be added to."
    )
    @app_commands.choices(ticker=ticker_options)
    async def add_watching(self, context: Context, ticker: str, id: int = 0, name: str = "") -> None:
        """
        Adds a stock to the user's watchlist.

        :param context: The application command context.
        :param ticker: The stock that should be added to the watchlist.
        :param id: The id of the watchlist that the stock should be added to.
        :param name: The name of the watchlist that the stock should be added to.
        """

        # Check if user is registered
        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can add stocks!")
            await context.send(embed=embed)
            return
        
        if name == "":
            
            # Check if user has a watchlist with the given ID
            if (await self.database_users.get_watchlist(context.author.id, id) == None):
                embed = self.errorEmbed("You do not have a watchlist with that ID!")
                embed.set_footer(text="Use the /watchlists command to view your watchlists.")
                await context.send(embed=embed)
                return
            
            # Check if stock is in database
            if (await self.database_users.is_stock_watched(context.author.id, id, ticker) != None):
                embed = self.errorEmbed(f"{ticker} is already in this watchlist!")
                await context.send(embed=embed)
                return
            
            await self.database_users.add_stock_to_watchlist(context.author.id, id, ticker)
        else:
            
            # Check if user has a watchlist with the given ID
            if (await self.database_users.get_watchlist_by_name(context.author.id, name) == None):
                embed = self.errorEmbed("You do not have a watchlist with that name!")
                embed.set_footer(text="Use the /watchlists command to view your watchlists.")
                await context.send(embed=embed)
                return
            
            # Check if stock is in database
            if (await self.database_users.is_stock_watched_by_name(context.author.id, name, ticker) != None):
                embed = self.errorEmbed(f"{ticker} is already in this watchlist!")
                await context.send(embed=embed)
                return
            
            await self.database_users.add_stock_to_watchlist_by_name(context.author.id, name, ticker)

        embed = self.successEmbed(f"{ticker} has been successfully added to this watchlist!", datetime.datetime.now())
        await context.send(embed=embed)

    @watchlist_group.command(
        name="remove",
        description="Removes a stock from the user's watchlist either by ID or by name.",
    )
    @app_commands.describe(
        ticker="The stock that should be removed from the watchlist.",
        id="The id of the watchlist that the stock should be removed from.",
        name="The name of the watchlist that the stock should be removed from."
    )
    @app_commands.choices(ticker=ticker_options)
    async def remove_watching(self, context: Context, ticker: str, id: int = 0, name: str = "") -> None:
        """
        Removes a stock from the user's watchlist.

        :param context: The application command context.
        :param ticker: The stock that should be removed from the watchlist.
        :param id: The id of the watchlist that the stock should be removed from.
        :param name: The name of the watchlist that the stock should be removed from.
        """

        if name == "":
            # Check if user is registered
            if not await self.database_users.does_user_exist(context.author.id):
                embed = self.errorEmbed("You need to register first before you can remove stocks!")
                await context.send(embed=embed)
                return
            
            # Check if user has a watchlist with the given ID
            if (await self.database_users.get_watchlist(context.author.id, id) == None):
                embed = self.errorEmbed("You do not have a watchlist with that ID!")
                embed.set_footer(text="Use the /watchlists command to view your watchlists.")
                await context.send(embed=embed)
                return
            
            # Check if stock is in database
            if (await self.database_users.is_stock_watched(context.author.id, id, ticker) == None):
                embed = self.errorEmbed(f"{ticker} is not in this watchlist!")
                await context.send(embed=embed)
                return
            
            await self.database_users.remove_stock_from_watchlist(context.author.id, id, ticker)
        else:
            # Check if user is registered
            if not await self.database_users.does_user_exist(context.author.id):
                embed = self.errorEmbed("You need to register first before you can remove stocks!")
                await context.send(embed=embed)
                return
            
            # Check if user has a watchlist with the given ID
            if (await self.database_users.get_watchlist_by_name(context.author.id, name) == None):
                embed = self.errorEmbed("You do not have a watchlist with that name!")
                embed.set_footer(text="Use the /watchlists command to view your watchlists.")
                await context.send(embed=embed)
                return
            
            # Check if stock is in database
            if (await self.database_users.is_stock_watched_by_name(context.author.id, name, ticker) == None):
                embed = self.errorEmbed(f"{ticker} is not in this watchlist!")
                await context.send(embed=embed)
                return
            
            await self.database_users.remove_stock_from_watchlist_by_name(context.author.id, name, ticker)

        embed = self.successEmbed(f"{ticker} has been successfully removed from this watchlist!", datetime.datetime.now())
        await context.send(embed=embed)

    @watchlist_group.command(
        name="create",
        description="Creates a watchlist.",
    )
    @app_commands.describe(
        name="The name of the watchlist that should be created.",
        description="The description of the watchlist that should be created."
    )
    async def create_watchlist(self, context: Context, name: str = "", description: str = "") -> None:
        """
        Creates a watchlist.

        :param context: The application command context.
        :param name: The name of the watchlist that should be created.
        :param description: The description of the watchlist that should be created.
        """
        
        # Check if user is registered
        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can create watchlists!")
            await context.send(embed=embed)
            return

        watchlist_id = await self.database_users.create_watchlist(context.author.id, name, description)

        if watchlist_id == -1:
            embed = self.successEmbed(f"Watchlist \"{name}\" has been successfully created!", datetime.datetime.now())
            embed.set_footer(text=f"ID: {watchlist_id}")
            embed.add_field(name="Want to add stocks to the watchlist?", value="Use the \"/watch [ticker] [id or name]\" command to add stocks to the watchlist.", inline=False)
        else:
            embed = self.errorEmbed("An error occurred while creating the watchlist! Please try again later.")
        await context.send(embed=embed)

    @watchlist_group.command(
        name="delete",
        description="Deletes a watchlist.",
    )
    @app_commands.describe(
        id="The id of the watchlist that should be deleted."
    )
    async def delete_watchlist(self, context: Context, id: int) -> None:
        """
        Deletes a watchlist.

        :param context: The application command context.
        :param id: The id of the watchlist that should be deleted.
        """
        
        # Check if user is registered
        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can delete watchlists!")
            await context.send(embed=embed)
            return
        
        # Check if watchlist exists
        if (await self.database_users.get_watchlist(context.author.id, id) == None):
            embed = self.errorEmbed("You do not have a watchlist with that ID!")
            await context.send(embed=embed)
            return

        await self.database_users.delete_watchlist(context.author.id, id)

        embed = self.successEmbed("Please note that all your watchlist ids will be shifted down by one after deleting a watchlist.", datetime.datetime.now())
        embed.set_footer(text=f"ID: ~~{id}~~")

        await context.send(embed=embed)

    # ========================================================================================================================================================================
    # Option Functions
    # ========================================================================================================================================================================
    @commands.hybrid_group(
        name="option",
        description="The option commands."
    )
    async def option_group(self, context: Context) -> None:
        """
        The option group command.

        :param context: The application command context.
        """
        pass
    # ========================================================================================================================================================================

    @option_group.command(
        name="list",
        description="Displays the user's options."
    )
    @app_commands.describe(
        ticker="The stock you want to view options for.",
        id="The ID of the portfolio that should be displayed.",
        user="The user whose options should be displayed."
    )
    @app_commands.choices(ticker=ticker_options)
    async def list_options(self, context: Context, ticker: str = "all", id: int = 0, user: discord.User = commands.Author) -> None:
        """
        Displays the user's options.

        :param context: The application command context.
        :param ticker: The stock you want to view options for.
        :param id: The ID of the portfolio that should be displayed.
        :param user: The user whose options should be displayed.
        """

        isSelf: bool = user == context.author
        title_your: str = f"{user.display_name}'s" if not isSelf else "Your"
        you: str = "you" if isSelf else "they"
        your: str = "your" if isSelf else "their"
        avatar_url = user.avatar.url if user.avatar != None else user.default_avatar.url

        if not await self.database_users.does_user_exist(user.id):
            embed = self.errorEmbed(f"{you.capitalize()} need to register first before you can view {your} options!")
            await context.send(embed=embed)
            return
        
        if (await self.database_users.get_portfolio(user.id, id) == None):
            embed = self.errorEmbed(f"{you.capitalize()} do not have a portfolio with that ID!")
            embed.set_footer(text=f"Use the \"/portfolios\" command to view {your} portfolios.")
            await context.send(embed=embed)
            return
        
        if (ticker == "all"):
            all_options = await self.database_users.get_options(user.id, id)
            
            if all_options is None:
                embed = self.errorEmbed(f"{you.capitalize()} do not have any options!")
                await context.send(embed=embed)
                return
            
            all_options = sorted(all_options, key=lambda x: x["created"], reverse=True)

            if len(all_options) == 0:
                embed = self.errorEmbed(f"{you.capitalize()} do not have any options!")
                await context.send(embed=embed)
                return
            
            embed = discord.Embed(
                title=f"{len(all_options)} Options Found!",
                description=f"Use the \"/options [ticker]\" command to view options for a specific stock.",
                color=self.colors["blue"]
            )
            
            embed.set_author(name=f"{title_your} Options", icon_url=avatar_url)

            for option in all_options:
                calls = await self.database_users.get_call_count(user.id, id, option["ticker"])
                puts = await self.database_users.get_put_count(user.id, id, option["ticker"])
                embed.add_field(name=f"{option['ticker']} : {calls + puts} options", value=f"{calls} calls & {puts} puts", inline=False)
            
            await context.send(embed=embed)
            return
        
        stock = await self.database_users.get_stock(user.id, id, ticker)

        if (stock == None):
            embed = self.errorEmbed(f"{you.capitalize} do not have a stock with that ticker!")
            await context.send(embed=embed)
            return
        
        all_options = await self.database_users.get_options_by_ticker(user.id, id, ticker)

        if all_options is None:
            embed = self.errorEmbed(f"{you.capitalize()} do not have any options for this stock!")
            await context.send(embed=embed)
            return
        
        all_options = sorted(all_options, key=lambda x: x["created"], reverse=True)

        if len(all_options) == 0:
            embed = self.errorEmbed(f"{you.capitalize()} do not have any options for this stock!")
            await context.send(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"{len(all_options)} options found!",
            description=f"Use the \"/option [ticker] [id]\" command to view a specific option.",
            color=self.colors["blue"]
        )
        embed.set_author(name=f"{title_your} Options for {ticker}", icon_url=avatar_url)

        for option in all_options:
            embed.add_field(name=f"[{option['option_id']}] {option['type']} on {option['created']}", value=f"{option['expires']} {option['strike']} | {option['quantity']} @ ${option['premium']}", inline=False)
            
            if option["status"] in ["filled", "pending", "cancelled"]:
                embedValue = "Still active."
            else:
                embedValue = f"${option['gainloss']}"
            
            embed.add_field(name=f"{option['status']}", value=embedValue, inline=True)

    @option_group.command(
        name="view",
        description="Displays a specific option."
    )
    @app_commands.describe(
        ticker="The stock you want to view options for.",
        id="The ID of the option that should be displayed.",
        portfolio_id="The ID of the portfolio that the stock belongs to.",
        user="The user whose option should be displayed."
    )
    @app_commands.choices(ticker=ticker_options)
    async def view_option(self, context: Context, ticker: str, id: int, portfolio_id: int = 0, user: discord.User = commands.Author) -> None:
        """
        Displays a specific option.

        :param context: The application command context.
        :param ticker: The stock you want to view options for.
        :param id: The ID of the option that should be displayed.
        :param portfolio_id: The ID of the portfolio that the stock belongs to.
        :param user: The user whose option should be displayed.        
        """

        isSelf: bool = user == context.author
        title_your: str = f"{user.display_name}'s" if not isSelf else "Your"
        you: str = "you" if isSelf else "they"
        your: str = "your" if isSelf else "their"
        avatar_url = user.avatar.url if user.avatar != None else user.default_avatar.url

        if (not await self.database_users.does_user_exist(user.id)):
            embed = self.errorEmbed(f"{you.capitalize()} need to register first before you can view {your} options!")
            await context.send(embed=embed)
            return
        
        if (await self.database_users.get_portfolio(user.id, portfolio_id) == None):
            embed = self.errorEmbed(f"{you.capitalize()} do not have a portfolio with that ID!")
            embed.set_footer(text=f"Use the \"/portfolios\" command to view {your} portfolios.")
            await context.send(embed=embed)
            return

        option = await self.database_users.get_option(user.id, portfolio_id, ticker, id)

        if option == None:
            embed = self.errorEmbed(f"{you.capitalize()} do not have an option with that ID!")
            await context.send(embed=embed)
            return

        embedTimestamp = datetime.datetime.strptime(option["expires"], "%m-%d-%Y %I:%M:%S %p").strftime("%B %d, %Y at %I:%M %p")
        embedTimestamp = datetime.datetime.strptime(embedTimestamp, "%B %d, %Y at %I:%M %p")

        if option["status"] in ["filled", "pending", "cancelled"]:
            if option["type"] == "call":
                embedColor = self.colors["green"]
            else:
                embedColor = self.colors["red"]
        else:
            embedColor = self.colors["green"] if option["gain_loss"] >= 0 else self.colors["red"]

        embed = discord.Embed(
            title=f"{option['ticker']} {option['type']} Option",
            description=f"Strike price of ${option['strike']} and a premium of ${option['premium']}.\nExpires on {option['expires']}.\nCreated on {option['created']}",
            color=embedColor,
            timestamp=embedTimestamp
        )
        embed.set_author(name=f"{title_your}", icon_url=avatar_url)
        embed.set_footer(text=f"ID: {option['option_id']}")

        if option["status"] in ["filled", "pending", "cancelled"]:
            embedValue = "Still active."
        else:
            embedValue = f"${option['gainloss']}"
        
        embed.add_field(name=f"{option['status']}", value=embedValue, inline=False)

        await context.send(embed=embed)

    @option_group.command(
        name="delete",
        description="Deletes a specific option."
    )
    @app_commands.describe(
        ticker="The stock that the option is for.",
        id="The ID of the option that should be deleted.",
        portfolio_id="The ID of the portfolio that the stock belongs to."
    )
    @app_commands.choices(ticker=ticker_options)
    async def delete_option(self, context: Context, ticker: str, id: int, portfolio_id: int = 0) -> None:
        """
        Deletes a specific option.

        :param context: The application command context.
        :param ticker: The stock that the option is for.
        :param id: The ID of the option that should be deleted.
        :param portfolio_id: The ID of the portfolio that the stock belongs to.
        """

        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can delete options!")
            await context.send(embed=embed)
            return
        
        if (await self.database_users.get_portfolio(context.author.id, portfolio_id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_stock(context.author.id, portfolio_id, ticker) == None):
            embed = self.errorEmbed("You do not have a stock with that ticker!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_option(context.author.id, portfolio_id, ticker, id) == None):
            embed = self.errorEmbed("You do not have an option with that ID!")
            await context.send(embed=embed)
            return

        await self.database_users.delete_option(context.author.id, portfolio_id, ticker, id)

        embed = self.successEmbed("Please note that all your option ids will be shifted down by one after deleting an option.", datetime.datetime.now())
        embed.set_footer(text=f"ID: ~~{id}~~")

        await context.send(embed=embed)

    @option_group.command(
        name="call",
        description="Adds a call option to a stock."
    )
    @app_commands.describe(
        ticker="The stock you want to add a call option to.",
        premium="The premium of the call option.",
        strike="The strike price of the call option.",
        expiry="The expiry date of the call option.",
        quantity="The quantity of the call option.",
        id="The ID of the portfolio that the stock belongs to.",
        status="The status of the call option (Filled or Pending, default is Filled)."
    )
    @app_commands.choices(ticker=ticker_options, status=status_options)
    async def call(self, context: Context, ticker: str, premium: float, strike: float, expiry: str, quantity: int, id: int = 0, status: str = "Filled", tstamp: str = "") -> None:
        """
        Adds a call option to a stock.

        :param context: The application command context.
        :param ticker: The stock you want to add a call option to.
        :param premium: The premium of the call option.
        :param strike: The strike price of the call option.
        :param expiry: The expiry date of the call option.
        :param quantity: The quantity of the call option.

        """

        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can add options!")
            await context.send(embed=embed)
            return
        
        if (await self.database_users.get_portfolio(context.author.id, id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_stock(context.author.id, id, ticker) == None):
            embed = self.errorEmbed("You do not have a stock with that ticker!")
            await context.send(embed=embed)
            return

        if (tstamp == ""):
            tstampObject = datetime.datetime.now()
            tstamp = tstampObject.strftime("%m-%d-%Y %I:%M:%S %p")
        else:
            tstampObject = datetime.datetime.strptime(tstamp, "%m-%d-%Y %I:%M:%S %p")
            tstamp = tstampObject.strftime("%m-%d-%Y %I:%M:%S %p")

        uOption = UserOption(ticker, strike, quantity, premium, tstamp, expiry, status, "call", 0.0)
        await self.database_users.add_option(context.author.id, id, ticker, uOption)

        embed = self.successEmbed(f"A call option for {ticker} has been successfully added to your portfolio!", tstampObject)
        await context.send(embed=embed)

    @option_group.command(
        name="put",
        description="Adds a put option to a stock."
    )
    @app_commands.describe(
        ticker="The stock you want to add a put option to.",
        premium="The premium of the put option.",
        strike="The strike price of the put option.",
        expiry="The expiry date of the put option.",
        quantity="The quantity of the put option.",
        id="The ID of the portfolio that the stock belongs to.",
        status="The status of the put option (Filled or Pending, default is Filled)."
    )
    @app_commands.choices(ticker=ticker_options, status=status_options)
    async def put(self, context: Context, ticker: str, premium: float, strike: float, expiry: str, quantity: int, status: str = "Filled", tstamp: str = "", id: int = 0) -> None:
        """
        Adds a put option to a stock.
        
        :param context: The application command context.
        :param ticker: The stock you want to add a put option to.
        :param premium: The premium of the put option.
        :param strike: The strike price of the put option.
        :param expiry: The expiry date of the put option.
        :param quantity: The quantity of the put option.
        :param status: The status of the put option (Filled or Pending, default is Filled).
        :param tstamp: The timestamp of the put option.
        :param id: The ID of the portfolio that the stock belongs to.
        """

        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can add options!")
            await context.send(embed=embed)
            return
        
        if (await self.database_users.get_portfolio(context.author.id, id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_stock(context.author.id, id, ticker) == None):
            embed = self.errorEmbed("You do not have a stock with that ticker!")
            await context.send(embed=embed)
            return
        
        tstampObject = datetime.datetime.now() if tstamp == "" else datetime.datetime.strptime(tstamp, "%m-%d-%Y %I:%M:%S %p")
        tstamp = tstampObject.strftime("%m-%d-%Y %I:%M:%S %p")

        uOption = UserOption(ticker, strike, quantity, premium, tstamp, expiry, status, "put", 0.0)
        await self.database_users.add_option(context.author.id, id, ticker, uOption)

        embed = self.successEmbed(f"A put option for {ticker} has been successfully added to your portfolio!", tstampObject)
        await context.send(embed=embed)

    @option_group.command(
        name="exercise",
        description="Exercises an option."
    )
    @app_commands.describe(
        ticker="The stock that the option is for.",
        id="The ID of the option that should be exercised.",
        portfolio_id="The ID of the portfolio that the stock belongs to."
    )
    @app_commands.choices(ticker=ticker_options)
    async def exercise(self, context: Context, ticker: str, id: int, gain_loss: float, portfolio_id: int = 0) -> None:
        """
        Exercises an option.

        :param context: The application command context.
        :param ticker: The stock that the option is for.
        :param id: The ID of the option that should be exercised.
        :param gain_loss: The gain or loss of the option.
        :param portfolio_id: The ID of the portfolio that the stock belongs to
        """

        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can exercise options!")
            await context.send(embed=embed)
            return
        
        if (await self.database_users.get_portfolio(context.author.id, portfolio_id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_stock(context.author.id, portfolio_id, ticker) == None):
            embed = self.errorEmbed("You do not have a stock with that ticker!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_option(context.author.id, portfolio_id, ticker, id) == None):
            embed = self.errorEmbed("You do not have an option with that ID!")
            await context.send(embed=embed)
            return

        await self.database_users.exercise_option(context.author.id, portfolio_id, ticker, id, gain_loss)

        embed = self.successEmbed(f"Option {id} has been successfully exercised!", datetime.datetime.now())
        await context.send(embed=embed)

    @option_group.command(
        name="expire",
        description="Expires an option."
    )
    @app_commands.describe(
        ticker="The stock that the option is for.",
        id="The ID of the option that should be expired.",
        portfolio_id="The ID of the portfolio that the stock belongs to."
    )
    @app_commands.choices(ticker=ticker_options)
    async def expire(self, context: Context, ticker: str, id: int, gain_loss: float, portfolio_id: int = 0) -> None:
        """
        Expires an option.

        :param context: The application command context.
        :param ticker: The stock that the option is for.
        :param id: The ID of the option that should be expired.
        :param gain_loss: The gain or loss of the option.
        :param portfolio_id: The ID of the portfolio that the stock belongs to
        """

        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can expire options!")
            await context.send(embed=embed)
            return
        
        if (await self.database_users.get_portfolio(context.author.id, portfolio_id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_stock(context.author.id, portfolio_id, ticker) == None):
            embed = self.errorEmbed("You do not have a stock with that ticker!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_option(context.author.id, portfolio_id, ticker, id) == None):
            embed = self.errorEmbed("You do not have an option with that ID!")
            await context.send(embed=embed)
            return

        await self.database_users.expire_option(context.author.id, portfolio_id, ticker, id, gain_loss)

        embed = self.successEmbed(f"Option {id} has been successfully expired!", datetime.datetime.now())
        await context.send(embed=embed)

    @option_group.command(
        name="update",
        description="Updates an option."
    )
    @app_commands.describe(
        ticker="The stock that the option is for.",
        id="The ID of the option that should be updated.",
        portfolio_id="The ID of the portfolio that the stock belongs to.",
        premium="The new premium of the option.",
        strike="The new strike price of the option.",
        expiry="The new expiry date of the option.",
        quantity="The new quantity of the option.",
        status="The new status of the option.",
        tstamp="The new timestamp of the option."
    )
    @app_commands.choices(ticker=ticker_options, status=status_options)
    async def update_option(self, context: Context, ticker: str, id: int, premium = None, strike = None, expiry = None, quantity = None, status = None, tstamp = None, portfolio_id: int = 0) -> None:
        """
        Updates an option.

        :param context: The application command context.
        :param ticker: The stock that the option is for.
        :param id: The ID of the option that should be updated.
        :param premium: The new premium of the option.
        :param strike: The new strike price of the option.
        :param expiry: The new expiry date of the option.
        :param quantity: The new quantity of the option.
        :param status: The new status of the option.
        :param tstamp: The new timestamp of the option.
        :param portfolio_id: The ID of the portfolio that the stock belongs to
        """

        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can update options!")
            await context.send(embed=embed)
            return
        
        if (await self.database_users.get_portfolio(context.author.id, portfolio_id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_stock(context.author.id, portfolio_id, ticker) == None):
            embed = self.errorEmbed("You do not have a stock with that ticker!")
            await context.send(embed=embed)
            return

        toUpdate = await self.database_users.get_option(context.author.id, portfolio_id, ticker, id)
        if (toUpdate == None):
            embed = self.errorEmbed("You do not have an option with that ID!")
            await context.send(embed=embed)
            return
        
        oldOption = UserOption()
        oldOption.fromDict(toUpdate)
        
        newOption = UserOption(ticker, strike, quantity, premium, tstamp, expiry, status)
        oldOption.updateOption(newOption)

        await self.database_users.update_option(context.author.id, portfolio_id, ticker, id, oldOption)

        embed = self.successEmbed(f"Option {id} has been successfully updated!", datetime.datetime.now())
        await context.send(embed=embed)

    @option_group.command(
        name="close",
        description="Closes an option."
    )
    @app_commands.describe(
        ticker="The stock that the option is for.",
        id="The ID of the option that should be closed.",
        portfolio_id="The ID of the portfolio that the stock belongs to."
    )
    @app_commands.choices(ticker=ticker_options)
    async def close_option(self, context: Context, ticker: str, id: int, gainloss: float, portfolio_id: int = 0) -> None:
        """
        Closes an option.

        :param context: The application command context.
        :param ticker: The stock that the option is for.
        :param id: The ID of the option that should be closed.
        :param gainloss: The gain or loss of the option.
        :param portfolio_id: The ID of the portfolio that the stock belongs to
        """

        if not await self.database_users.does_user_exist(context.author.id):
            embed = self.errorEmbed("You need to register first before you can close options!")
            await context.send(embed=embed)
            return
        
        if (await self.database_users.get_portfolio(context.author.id, portfolio_id) == None):
            embed = self.errorEmbed("You do not have a portfolio with that ID!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_stock(context.author.id, portfolio_id, ticker) == None):
            embed = self.errorEmbed("You do not have a stock with that ticker!")
            await context.send(embed=embed)
            return

        if (await self.database_users.get_option(context.author.id, portfolio_id, ticker, id) == None):
            embed = self.errorEmbed("You do not have an option with that ID!")
            await context.send(embed=embed)
            return

        await self.database_users.close_option(context.author.id, portfolio_id, ticker, id, gainloss)

        embed = self.successEmbed(f"Option {id} has been successfully closed!", datetime.datetime.now())
        await context.send(embed=embed)

    # ========================================================================================================================================================================
    # Helper Functions
    # ========================================================================================================================================================================

    # Function to create an error embed
    def errorEmbed(self, description: str, timestamp = None) -> discord.Embed:
        return discord.Embed(
            title="Error!",
            description=description,
            color=self.colors["red"],
            timestamp=timestamp
        )
    
    # Function to create a success embed
    def successEmbed(self, description: str, timestamp = None) -> discord.Embed:
        return discord.Embed(
            title="Success!",
            description=description,
            color=self.colors["green"],
            timestamp=timestamp
        )

    # Function to convert a date to a specific format
    def date_toFormat(self, date: str | datetime.datetime, fromFormat: str = "", toFormat: str = "") -> str:
        fromFormat = self.databaseFormat if fromFormat == "" else fromFormat
        toFormat = self.fullFormat if toFormat == "" else toFormat

        if isinstance(date, datetime.datetime):
            return date.strftime(toFormat)
        else:
            return datetime.datetime.strptime(date, fromFormat).strftime(toFormat)

# ========================================================================================================================================================================
# Helper Functions
# ========================================================================================================================================================================

"""
Function to return the ordinal of a number

CREDIT: https://codegolf.stackexchange.com/questions/4707/outputting-ordinal-numbers-1st-2nd-3rd#answer-4712
"""
def ordinal(n):
    return str(n)+("th" if 4<=n%100<=20 else {1:"st",2:"nd",3:"rd"}.get(n%10, "th"))


"""
Function to convert a word to its plural form

CREDIT: https://www.geeksforgeeks.org/python-program-to-convert-singular-to-plural/
"""
def plural(word: str) -> str:
    # Check if word is ending with s,x,z or is ending with ah,eh,ih,oh,uh,dh,gh,kh,ph,rh,th
    if search('[sxz]$', word) or search('[^aeioudgkprt]h$', word):
    
        return sub('$', 'es', word) # Make it plural by adding es in end
    
    # Check if word is ending with ay,ey,iy,oy,uy
    elif search('[aeiou]y$', word):
    
        return sub('y$', 'ies', word) # Make it plural by removing y from end adding ies to end
    
    # In all the other cases
    else:
        return word + 's' # Make the plural of word by adding s in end

# ========================================================================================================================================================================
# Cog Setup
# ========================================================================================================================================================================

async def setup(bot) -> None:
    await bot.add_cog(Portfolio(bot))