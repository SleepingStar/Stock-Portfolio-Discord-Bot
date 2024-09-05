import datetime
from sqlite3 import Row
from typing import Iterable
from .manager import DatabaseManager
from utils.stocker.PortfolioTypes import UserOrder
from utils.stocker.PortfolioTypes import UserOption

"""
User Manager
    This class contains functions that are used to interact with the user database.
"""

class UserManager(DatabaseManager):
    def __init__(self) -> None:
        super().__init__() # Initialize the DatabaseManager

    # ========================================================================================================================================================================
    # User Functions | DONE
    # ========================================================================================================================================================================

    # This function is used to check if a user exists in the database
    async def does_user_exist(self, user_id: int) -> bool:
        if self.connection is None:
            return False

        # Check if the user exists in the database
        async with self.connection.execute(
            "SELECT * FROM Users WHERE user_id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None # Return if the user exists or not

    # This function is used to add a user to the database
    async def create_user(self, user_id: int, user_name) -> bool:
        if self.connection is None or self.logger is None:
            return False

        now = datetime.datetime.now().strftime(self.date_format) # Get the current timestamp

        try:
            # Insert the user into the database
            await self.connection.execute(
                "INSERT INTO Users (user_id, created) VALUES (?, ?)",
                (user_id, now,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"added user \"{user_name}\" {user_id}")

            return True
        
        except Exception as e:
            await self.connection.rollback() # Rollback the changes 
            self.logger.error(f"error adding user {user_id} : {e}") # Log the error

            return False

    # This function is used to delete a user from the database
    async def delete_user(self, user_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        # Delete the user from the database
        try: 
            await self.connection.execute(
                "DELETE FROM Users WHERE user_id = ?", (user_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"deleted user {user_id}")

            return True
        except Exception as e:
            await self.connection.rollback() # Rollback the changes
            self.logger.error(f"error deleting user {user_id} : {e}")

            return False

    # This function is used to get a user from the database
    async def get_user(self, user_id: int) -> Row | None:
        if self.connection is None or self.logger is None:
            return None
        
        # Get the user from the database
        async with self.connection.execute(
            "SELECT * FROM Users WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchone()
        
    # This function is used to get all users in the database
    async def get_all_users(self) -> Iterable[Row] | None:
        if self.connection is None or self.logger is None:
            return None
        
        # Get all users from the database
        async with self.connection.execute(
            "SELECT * FROM Users"
        ) as cursor:
            return await cursor.fetchall()
    
    # This function is used to get the total number of users in the database
    async def get_total_user_count(self) -> int:
        if self.connection is None or self.logger is None:
            return -1
        
        # Execute the SQL query to get the total number of users
        async with self.connection.execute("SELECT COUNT(*) FROM Users") as cursor:
            # Fetch the status and return the count
            status = await cursor.fetchone()
            return status[0] if status else 0  # Return 0 if no status found

    async def get_user_gain_loss(self, user_id: int) -> float | None:
        portfolios = await self.get_portfolios(user_id)

        if not portfolios:
            return None

        gain_loss = 0

        for portfolio in portfolios:
            portfolio_gl = await self.get_portfolio_gain_loss(user_id, portfolio["portfolio_id"])
            gain_loss += portfolio_gl if portfolio_gl else 0
        
        return gain_loss

    # ========================================================================================================================================================================
    # Portfolio Functions
    # ========================================================================================================================================================================

    # This function is used to check if a portfolio exists in the database
    async def does_portfolio_exist(self, user_id: int, portfolio_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        # Check if the portfolio exists in the database
        async with self.connection.execute(
            "SELECT * FROM Portfolios WHERE user_id = ? AND portfolio_id = ?",
            (user_id, portfolio_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None

    # This function is used to create a portfolio for a user
    async def create_portfolio(self, user_id: int, name: str = "", description: str = "") -> Row | None:
        if self.connection is None or self.logger is None:
            return None
        
        try:
            portfolio_id = await self.get_portfolio_count(user_id) # Get the current portfolio count
            created = datetime.datetime.now().strftime(self.date_format)
            
            # Check if the portfolio name is empty
            if name == "":
                name = f"Portfolio {portfolio_id}"

            if description == "":
                description = "No description provided."
            
            # Insert the portfolio into the database
            await self.connection.execute(
                "INSERT INTO Portfolios (user_id, portfolio_id, name, description, created) VALUES (?, ?, ?, ?, ?)",
                (user_id, portfolio_id, name, description, created,)
            )
            
            await self.connection.commit() # Commit the changes

            portfolio = await self.get_portfolio(user_id, portfolio_id) # Return the portfolio

            if not portfolio:
                return None
            
            self.logger.info(f"{user_id} created portfolio : {portfolio['portfolio_key']} - {name}") # Log the creation of the portfolio

            return portfolio
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error creating portfolio for {user_id} : {e}")
            return None
        
    # This function is used to delete a portfolio from the database
    async def delete_portfolio(self, user_id: int, portfolio_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        try:
            # Delete the portfolio from the database
            portfolio = await self.get_portfolio(user_id, portfolio_id)

            if not portfolio:
                return False
            
            portfolio_key = portfolio["portfolio_key"]

            await self.connection.execute(
                "DELETE FROM Portfolios WHERE user_id = ? AND portfolio_id = ?",
                (user_id, portfolio_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} deleted portfolio {portfolio_key}") # Log the deletion of the portfolio
            await self.update_portfolio_indexes(user_id) # Update the portfolio indexes

            return True

        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error deleting portfolio for {user_id} : {e}")

            return False

    # This function is used to rename a portfolio from the database
    async def rename_portfolio(self, user_id: int, portfolio_id: int, new_name: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        try:
            portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

            if not portfolio:
                return False

            old_name = portfolio["name"] # Get the old name
            portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

            # Update the portfolio name in the database
            await self.connection.execute(
                "UPDATE Portfolios SET name = ? WHERE user_id = ? AND portfolio_id = ?",
                (new_name, user_id, portfolio_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} renamed portfolio {portfolio_key} : {old_name} --> {new_name}") # Log the change
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error renaming portfolio for {user_id} : {e}")
            return False
    
    # This function is used to update the portfolio description in the database
    async def update_portfolio_description(self, user_id: int, portfolio_id: int, description: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return False

        old_description = portfolio["description"]
        portfolio_key = portfolio["portfolio_key"]

        try:

            # Update the portfolio description in the database
            await self.connection.execute(
                "UPDATE Portfolios SET description = ? WHERE user_id = ? AND portfolio_id = ?",
                (description, user_id, portfolio_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} updated portfolio [{portfolio_key}] description : \"{old_description}\" --> \"{description}\"") # Log the change
            
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error updating portfolio [{portfolio_key}] description for {user_id} : {e}")
            return False
        
    # <-- GETTERS -->

    # This function is used to get a portfolio from the database
    async def get_portfolio(self, user_id: int, portfolio_id: int) -> Row | None:
        if self.connection is None or self.logger is None:
            return None
        # Get the portfolio from the database
        async with self.connection.execute(
            "SELECT * FROM Portfolios WHERE user_id = ? AND portfolio_id = ?",
            (user_id, portfolio_id,)
        ) as cursor:
            return await cursor.fetchone()

    # This function is used to get a portfolio from the database by name
    async def get_portfolio_byname(self, user_id: int, name: str) -> Row | None:
        if self.connection is None or self.logger is None:
            return None
        
        # Get the portfolio from the database
        async with self.connection.execute(
            "SELECT * FROM Portfolios WHERE user_id = ? AND name = ?",
            (user_id, name,)
        ) as cursor:
            return await cursor.fetchone()

    # This function is used to get the first portfolio of a user
    async def get_first_portfolio(self, user_id: int) -> Row | None:
        if self.connection is None or self.logger is None:
            return None
        
        # Get the first portfolio of the user from the database
        async with self.connection.execute(
            "SELECT * FROM Portfolios WHERE user_id = ? ORDER BY portfolio_id LIMIT 1",
            (user_id,)
        ) as cursor:
            return await cursor.fetchone()
        
    # This function is used to get all portfolios of a user
    async def get_portfolios(self, user_id: int) -> Iterable[Row] | None:
        if self.connection is None or self.logger is None:
            return None
        
        # Get all portfolios of the user from the database
        async with self.connection.execute(
            "SELECT * FROM Portfolios WHERE user_id = ?", (user_id,)
        ) as cursor:
            return await cursor.fetchall()
    
    # This function is used to get the total number of portfolios in the database
    async def get_total_portfolio_count(self) -> int:
        if self.connection is None or self.logger is None:
            return -1
        
        # Get the total number of portfolios in the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Portfolios"
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0

    # This function is used to get the number of portfolios of a user
    async def get_portfolio_count(self, user_id: int) -> int:
        if self.connection is None or self.logger is None:
            return -1
        
        # Get the total number of portfolios in the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Portfolios WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            all = await cursor.fetchone()          
            return all[0] if all else 0
    
    # <-- MISC FUNCTIONS -->

    # This function is used to update the portfolio indexes in the database
    async def update_portfolio_indexes(self, user_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        try:
            portfolios = await self.get_portfolios(user_id) # Get all portfolios of the user
            
            if not portfolios:
                return False
            
            portfolios = list(portfolios) # Convert the iterable to a list
            
            # Update the portfolio indexes in the database
            for new_id in range(len(portfolios)):
                await self.connection.execute(
                    "UPDATE Portfolios SET portfolio_id = ? WHERE user_id = ?",
                    (new_id, user_id,)
                )
                await self.connection.commit() # Commit the changes

            self.logger.info(f"Updated {len(portfolios)} portfolio indexes for {user_id}")
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error updating portfolio indexes for {user_id} : {e}")
            return False
    
    # This function is used to get the total investment of a portfolio
    async def get_portfolio_investment(self, user_id: int, portfolio_id: int) -> float | None:
        stocks = await self.get_stocks(user_id, portfolio_id)

        if not stocks:
            return None

        investment = 0

        for stock in stocks:
            stock_i = await self.get_stock_investment(user_id, portfolio_id, stock["ticker"])
            investment += stock_i if stock_i else 0
        
        return investment

    # This function is used to get the total quantity of a portfolio
    async def get_portfolio_quantity(self, user_id: int, portfolio_id: int) -> float | None:
        stocks = await self.get_stocks(user_id, portfolio_id)

        if not stocks:
            return None

        quantity = 0

        for stock in stocks:
            stock_q = await self.get_stock_quantity(user_id, portfolio_id, stock["ticker"])
            
            quantity += stock_q if stock_q else 0
        
        return quantity
    
    # This function is used to get the total gain or loss of a portfolio
    async def get_portfolio_gain_loss(self, user_id: int, portfolio_id: int) -> float | None:
        stocks = await self.get_stocks(user_id, portfolio_id)

        if not stocks:
            return None

        gain_loss = 0

        for stock in stocks:
            stock_gl = await self.get_stock_gain_loss(user_id, portfolio_id, stock["ticker"])
            gain_loss += stock_gl if stock_gl else 0

        portfolio_investment = await self.get_portfolio_investment(user_id, portfolio_id)
        
        return portfolio_investment + gain_loss if portfolio_investment else None
    
    # This function is used to get the total dividends of a portfolio
    async def get_portfolio_dividends(self, user_id: int, portfolio_id: int) -> float | None:
        dividends = await self.get_dividends(user_id, portfolio_id)

        if not dividends:
            return None

        total_dividends = 0

        for dividend in dividends:
            total_dividends += dividend["dividend"]
        
        return total_dividends

    # ========================================================================================================================================================================
    # Stock Functions
    # ========================================================================================================================================================================

    # This function is used to check if a stock exists in a user's portfolio
    async def does_stock_exist(self, user_id: int, portfolio_id: int, ticker: str) -> bool:
        if self.connection is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return False

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Check if the stock exists in the portfolio
        async with self.connection.execute(
            "SELECT * FROM Stocks WHERE user_id = ? AND portfolio_key = ? AND ticker = ?",
            (user_id, portfolio_key, ticker,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None 

    # This function is used to add a stock to a user's portfolio
    async def add_stock(self, user_id: int, portfolio_id: int, ticker: str) -> int:
        if self.connection is None or self.logger is None:
            return -1

        created = datetime.datetime.now().strftime(self.date_format) # Get the current timestamp
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return -1

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        try:
            # Add the stock to the portfolio
            await self.connection.execute(
                "INSERT INTO Stocks (user_id, portfolio_key, ticker, created) VALUES (?, ?, ?, ?)",
                (user_id, portfolio_key, ticker, created,)
            )
            
            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} added stock to portfolio {portfolio_key} : {ticker}")

            return await self.get_stock_count(user_id, portfolio_id) # Return the stock count
        
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error adding stock to portfolio {portfolio_key} : {e}")
            return -1

    # This function is used to delete a stock from a user's portfolio
    async def delete_stock(self, user_id: int, portfolio_id: int, ticker: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return False

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # delete the stock from the portfolio
        await self.connection.execute(
            "DELETE FROM Stocks WHERE user_id = ? AND portfolio_key = ? AND ticker = ?",
            (user_id, portfolio_key, ticker,)
        )

        await self.connection.commit() # Commit the changes

        self.logger.info(f"{user_id} deleted stock from portfolio {portfolio_key} : {ticker}")
        return True

    # <-- GETTERS -->

    # This function gets the stock data for a user's portfolio
    async def get_stock(self, user_id: int, portfolio_id: int, ticker: str) -> Row | None:
        if self.connection is None:
            return None
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return None
        
        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Get the stock from the database
        async with self.connection.execute(
            "SELECT * FROM Stocks WHERE user_id = ? AND portfolio_key = ? AND ticker = ?",
            (user_id, portfolio_key, ticker,)
        ) as cursor:
            return await cursor.fetchone()
   
    # This function is used to get all stocks in a user's portfolio
    async def get_stocks(self, user_id: int, portfolio_id: int) -> Iterable[Row] | None:
        if self.connection is None:
            return None
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return None

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Get all stocks in the portfolio from the database
        async with self.connection.execute(
            "SELECT * FROM Stocks WHERE user_id = ? AND portfolio_key = ?",
            (user_id, portfolio_key,)
        ) as cursor:
            return await cursor.fetchall()
    
    # This function is used to get the total number of stocks in a user's portfolio
    async def get_stock_count(self, user_id: int, portfolio_id: int) -> int:
        if self.connection is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return -1

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        async with self.connection.execute(
            "SELECT COUNT(*) FROM Stocks WHERE user_id = ? AND portfolio_key = ?",
            (user_id, portfolio_key,)
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0

    # This functions gets all the tickers under a user's portfolio
    async def get_portfolio_tickers(self, user_id: int, portfolio_id: int) -> Iterable[Row] | None:
        if self.connection is None:
            return None
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return None

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Get the tickers from the database
        async with self.connection.execute(
            "SELECT ticker FROM Stocks WHERE user_id = ? AND portfolio_key = ?",
            (user_id, portfolio_key,)
        ) as cursor:
            return await cursor.fetchall()

    # <-- MISC FUNCTIONS -->

    # This function is used to get the total investment of a stock in a user's portfolio
    async def get_stock_investment(self, user_id: int, portfolio_id: int, ticker: str) -> float | None:
        orders = await self.get_orders(user_id, portfolio_id, ticker)

        if not orders:
            return None

        investment = 0

        for order in orders:
            if order["status"] == "Filled" and order["type"] == "Buy":
                investment += order["price"] * order["quantity"]
            elif order["status"] == "Filled" and order["type"] == "Sell":
                investment -= order["price"] * order["quantity"]
        
        return investment
    
    # This function is used to get the total quantity of a stock in a user's portfolio
    async def get_stock_quantity(self, user_id: int, portfolio_id: int, ticker: str) -> float | None:
        orders = await self.get_orders(user_id, portfolio_id, ticker)

        if not orders:
            return None

        quantity = 0

        for order in orders:
            if order["status"] == "Filled" and order["type"] == "Buy":
                quantity += order["quantity"]
            elif order["status"] == "Filled" and order["type"] == "Sell":
                quantity -= order["quantity"]

        return quantity
    
    # This function is used to get the total gain or loss of a stock in a user's portfolio
    async def get_stock_gain_loss(self, user_id: int, portfolio_id: int, ticker: str) -> float | None:
        orders = await self.get_orders(user_id, portfolio_id, ticker)

        if not orders:
            return None

        gain_loss = 0

        for order in orders:
            if order["status"] == "Filled" and order["type"] == "Sell":
                gain_loss += order["price"] * order["quantity"]
            if order["status"] == "Filled" and order["type"] == "Buy":
                gain_loss -= order["price"] * order["quantity"]
            
        
        return gain_loss
    
    # ========================================================================================================================================================================
    # Order Functions | DONE
    # ========================================================================================================================================================================
    
    # This function is used to check if an order exists in a user's portfolio
    async def does_order_exist(self, user_id: int, portfolio_id: int, ticker: str, order_id: int) -> bool:
        if self.connection is None:
            return False

        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return False

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Check if the order exists in the portfolio
        async with self.connection.execute(
            "SELECT * FROM Orders WHERE user_id = ? AND portfolio_key = ? AND order_id = ? AND ticker = ?",
            (user_id, portfolio_key, order_id, ticker,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None
            
    # This function is used to add an order to a user's portfolio
    async def add_order(self, user_id: int, portfolio_id: int, ticker: str, uOrder: UserOrder) -> int:
        if self.connection is None or self.logger is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio
        stock = await self.get_stock(user_id, portfolio_id, ticker) # Get the stock key

        if not portfolio or not stock:
            return -1

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key
        stock_key = stock["stock_key"] # Get the stock key

        try:
            # Add the order to the database
            await self.connection.execute(
                "INSERT INTO Orders (user_id, portfolio_key, stock_key, ticker, quantity, price, status, created, type,) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, portfolio_key, stock_key, ticker, uOrder.quantity, uOrder.price, uOrder.status, uOrder.created, uOrder.orderType, )
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} added order to portfolio {portfolio_key} : {ticker}")

            return await self.get_order_count(user_id, portfolio_id) # Return the order count
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error adding order to portfolio {portfolio_key} : {e}")
            return -1

    # This function is used to delete an order from a user's portfolio
    async def delete_order(self, user_id: int, portfolio_id: int, ticker: str, order_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio
        order = await self.get_order(user_id, portfolio_id, ticker, order_id) # Get the order

        if not portfolio or not order:
            return False
        
        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key
        order_key = order["key"] # Get the order key

        try:
            # delete the order from the database
            await self.connection.execute(
                "DELETE FROM Orders WHERE user_id = ? AND portfolio_key = ? AND order_id = ? AND ticker = ?",
                (user_id, portfolio_key, order_id, ticker,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} deleted order from portfolio {portfolio_key} : {order_key} in {ticker}")
            await self.update_order_indexes(user_id, portfolio_id, ticker) # Update the order indexes

            return True

        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error deleting order from portfolio {portfolio_key} : {e}")
            return False

    # This function is used to update an order in a user's portfolio
    async def update_order(self, user_id: int, portfolio_id: int, order_id: int, ticker: str, uOrder: UserOrder) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio
        order = await self.get_order(user_id, portfolio_id, ticker, order_id)

        if not portfolio or not order:
            return False

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key
        order_key = order["order_key"] # Get the order key

        if not order_key or not portfolio_key:
            return False

        try:
            # Update the order in the database
            await self.connection.execute(
                "UPDATE Orders SET quantity = ?, price = ?, status = ?, created = ?, type = ? WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND order_key = ?",
                (uOrder.quantity, uOrder.price, uOrder.status, uOrder.created, uOrder.orderType, user_id, portfolio_key, ticker, order_key,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} updated order in portfolio {portfolio_key} : {order_key}")
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error updating order in portfolio {portfolio_key} : {e}")
            return False
      
    # <-- GETTERS -->

    # This function gets the order data for a user's portfolio
    async def get_order(self, user_id: int, portfolio_id: int, ticker: str, order_id: int) -> Row | None:
        
        if self.connection is None:
            return None

        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return None

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Get the order from the database
        async with self.connection.execute(
            "SELECT * FROM Orders WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND order_id = ?",
            (user_id, portfolio_key, ticker, order_id,)
        ) as cursor:
            return await cursor.fetchone()

    # This function is used to get all orders in a user's portfolio for a stock
    async def get_orders(self, user_id: int, portfolio_id: int, ticker: str) -> Iterable[Row] | None:
        if self.connection is None:
            return None
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return None

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Get all orders in the portfolio from the database for the stock
        async with self.connection.execute(
            "SELECT * FROM Orders WHERE user_id = ? AND portfolio_key = ? AND ticker = ?",
            (user_id, portfolio_key, ticker,)
        ) as cursor:
            return await cursor.fetchall()
    
    # This function is used to get the total number of orders in a user's portfolio
    async def get_order_count(self, user_id: int, portfolio_id: int) -> int:
        if self.connection is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return -1
        
        portfolio_key = portfolio["portfolio_key"]

        # Get the total number of orders in the portfolio from the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Orders WHERE user_id = ? AND portfolio_key = ?",
            (user_id, portfolio_key,)
        ) as cursor:
            all = await cursor.fetchone()            
            return await all[0] if all else 0

    # This function is used to get the total number of orders in the database
    async def get_total_order_count(self) -> int:
        if self.connection is None:
            return -1
        
        # Get the total number of orders in the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Orders"
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0
    
    # <-- MISC FUNCTIONS -->

    # This function is used to purge orders from a user's portfolio
    async def purge_orders(self, user_id: int, portfolio_id: int, ticker: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return False
        
        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        try:
            if ticker == "all":
                # Purge all orders from the database
                await self.connection.execute(
                    "DELETE FROM Orders WHERE user_id = ? AND portfolio_key = ? AND status = ?",
                    (user_id, portfolio_key, "Cancelled",)
                )
            else:
                # Purge the orders from the database
                await self.connection.execute(
                    "DELETE FROM Orders WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND status = ?",
                    (user_id, portfolio_key, ticker, "Cancelled",)
                )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} purged orders from portfolio {portfolio_key} : {ticker}")

            await self.update_order_indexes(user_id, portfolio_id, ticker) # Update the order indexes

            return True
        except Exception as e:
            await self.connection.rollback()
            await self.connection.rollback()
            self.logger.error(f"error purging orders from portfolio {portfolio_key} : {e}")
            return False
        
    # This function is used to update the order indexes in the database
    async def update_order_indexes(self, user_id: int, portfolio_id: int, ticker: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        if ticker == "all":
            stocks = await self.get_stocks(user_id, portfolio_id)

            if not stocks:
                return False
            
            stocks = list(stocks)

            for stock in stocks:
                await self.update_order_indexes(user_id, portfolio_id, stock["ticker"])

            return True

        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio
        orders = await self.get_orders(user_id, portfolio_id, ticker) # Get the orders

        if not portfolio or not orders:
            return False
        
        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        try:
            orders_list = list(orders)
            for i in range(len(orders_list)):
                await self.connection.execute(
                    "UPDATE Orders SET order_id = ? WHERE user_id = ? AND portfolio_key = ? AND ticker = ?",
                    (i, user_id, portfolio_key, ticker,)
                )
                await self.connection.commit()
            self.logger.info(f"updated {len(orders_list)} order indexes for {user_id}")
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error updating order indexes for {user_id} : {e}")
            return False

    # ========================================================================================================================================================================
    # Dividends Functions | DONE
    # ========================================================================================================================================================================

    # This function is used to check if a dividend exists in a user's portfolio
    async def does_dividend_exist(self, user_id: int, portfolio_id: int, ticker: str, dividend_id: int) -> bool:
        if self.connection is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return False
        
        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Check if the dividend exists in the portfolio
        async with self.connection.execute(
            "SELECT * FROM Dividends WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND dividend_id = ?",
            (user_id, portfolio_key, ticker, dividend_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None

    # This function is used to add a dividend to a user's portfolio
    async def add_dividend(self, user_id: int, portfolio_id: int, ticker: str, dividend: float, created: str) -> int:
        if self.connection is None or self.logger is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return -1

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key
        dividend_id = await self.get_dividend_count(user_id, portfolio_id) # Get the current dividend count

        try:
            # Add the dividend to the database
            await self.connection.execute(
                "INSERT INTO Dividends (user_id, portfolio_key, ticker, dividend_id, dividend, created) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, portfolio_key, ticker, dividend_id, dividend, created,)
            )

            await self.connection.commit() # Commit the changes

            dividend_object = await self.get_dividend(user_id, portfolio_id, ticker, dividend_id) # Get the dividend

            if not dividend_object:
                return -1

            self.logger.info(f"{user_id} added dividend to portfolio {portfolio_key} : {ticker} <-- {dividend} [{dividend_object['dividend_key']}]")   

            return dividend_id # Return the dividend index
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error adding dividend to portfolio {portfolio_key} : {e}")
            return -1

    # This function is used to delete a dividend from a user's portfolio
    async def delete_dividend(self, user_id: int, portfolio_id: int, ticker: str, dividend_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False

        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio
        dividend_object = await self.get_dividend(user_id, portfolio_id, ticker, dividend_id) # Get the dividend

        if not portfolio or not dividend_object:
            return False

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key
        dividend_key = dividend_object["dividend_key"] # Get the dividend key

        try:
            # Delete the dividend from the database
            await self.connection.execute(
                "DELETE FROM Dividends WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND dividend_id = ?",
                (user_id, portfolio_key, ticker, dividend_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} deleted dividend from portfolio {portfolio_key} : {ticker} <-- {dividend_key}")
            await self.update_dividend_indexes(user_id, portfolio_id) # Update the dividend indexes

            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error deleting dividend from portfolio {portfolio_key} : {e}")
            return False

    # <-- GETTERS -->

    # This function gets the dividend data for a user's portfolio
    async def get_dividend(self, user_id: int, portfolio_id: int, ticker: str, dividend_id: int) -> Row | None:
        if self.connection is None:
            return None
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return None

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Get the dividend from the database
        async with self.connection.execute(
            "SELECT * FROM Dividends WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND dividend_id = ?",
            (user_id, portfolio_key, ticker, dividend_id,)
        ) as cursor:
            return await cursor.fetchone()
    
    # This function is used to get all dividends in a user's portfolio
    async def get_dividends(self, user_id: int, portfolio_id: int) -> Iterable[Row] | None:
        if self.connection is None:
            return None
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return None

        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Get all dividends in the portfolio from the database
        async with self.connection.execute(
            "SELECT * FROM Dividends WHERE user_id = ? AND portfolio_key = ?",
            (user_id, portfolio_key,)
        ) as cursor:
            return await cursor.fetchall()
    
    # This function is used to get all dividends in a user's portfolio for a stock by ticker
    async def get_dividends_by_ticker(self, user_id: int, portfolio_id: int, ticker: str) -> Iterable[Row] | None:
        if self.connection is None:
            return None
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return None
        
        portfolio_key = portfolio["portfolio_key"]

        async with self.connection.execute(
            "SELECT * FROM Dividends WHERE user_id = ? AND portfolio_key = ? AND ticker = ?",
            (user_id, portfolio_key, ticker,)
        ) as cursor:
            return await cursor.fetchall()

    # This function is used to get the total number of dividends in the database
    async def get_total_dividend_count(self) -> int:
        if self.connection is None:
            return -1

        # Get the total number of dividends in the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Dividends"
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0
    
    # This function is used to get the total number of dividends in a user's portfolio
    async def get_dividend_count(self, user_id: int, portfolio_id: int) -> int:
        if self.connection is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return -1

        portfolio_key = portfolio["portfolio_key"]

        async with self.connection.execute(
            "SELECT COUNT(*) FROM Dividends WHERE user_id = ? AND portfolio_key = ?",
            (user_id, portfolio_key,)
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0

    # This function is used to get the total number of dividends in a user's portfolio for a stock by ticker
    async def get_dividend_count_by_ticker(self, user_id: int, portfolio_id: int, ticker: str) -> int:
        if self.connection is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return -1
        
        portfolio_key = portfolio["portfolio_key"]

        async with self.connection.execute(
            "SELECT COUNT(*) FROM Dividends WHERE user_id = ? AND portfolio_key = ? AND ticker = ?",
            (user_id, portfolio_key, ticker,)
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0

    # <-- MISC FUNCTIONS -->

    # This function is used to update the dividend indexes in the database
    async def update_dividend_indexes(self, user_id: int, portfolio_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False

        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio
        dividends = await self.get_dividends(user_id, portfolio_id) # Get all dividends in the portfolio

        if not portfolio or not dividends:
            return False
        
        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        try:
            # Update the dividend indexes in the database
            dividends_list = list(dividends)  # Convert Iterable[Row] to list
            for i in range(len(dividends_list)):
                await self.connection.execute(
                    "UPDATE Dividends SET dividend_id = ? WHERE user_id = ? AND portfolio_key = ?",
                    (i, user_id, portfolio_key,)
                )
                await self.connection.commit() # Commit the changes
            self.logger.info(f"updated {len(dividends_list)} dividend indexes for {user_id}")
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error updating dividend indexes for {user_id} : {e}")
            return False
        
    # ========================================================================================================================================================================
    # Options Functions
    # ========================================================================================================================================================================

    # This function is used to check if an option exists in a user's portfolio
    async def does_option_exist(self, user_id: int, portfolio_id: int, ticker: str, option_id: int) -> bool:
        if self.connection is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return False
        
        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        # Check if the option exists in the portfolio
        async with self.connection.execute(
            "SELECT * FROM Options WHERE user_id = ? AND portfolio_key = ? AND option_id = ? AND ticker = ?",
            (user_id, portfolio_key, option_id, ticker,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None
        
    # This function is used to add an option to a user's portfolio
    async def add_option(self, user_id: int, portfolio_id: int, ticker: str, uOption: UserOption) -> int:
        if self.connection is None or self.logger is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id)

        if not portfolio:
            return -1
        
        portfolio_key = portfolio["portfolio_key"]

        new_option_id = await self.get_option_count(user_id, portfolio_id) # Get the current option count
        created = datetime.datetime.now().strftime(self.date_format) # Get the current timestamp

        try:
            # Add the option to the database
            await self.connection.execute(
                "INSERT INTO Options (user_id, portfolio_key, ticker, option_id, type, strike, expires, quantity, premium, status, created) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user_id, portfolio_key, ticker, new_option_id, uOption.optionType, uOption.strike, uOption.expires, uOption.quantity, uOption.premium, uOption.status, created,)
            )

            await self.connection.commit() # Commit the changes

            option = await self.get_option(user_id, portfolio_id, ticker, new_option_id) # Get the option

            if not option:
                return -1
            
            option_key = option["option_key"]

            self.logger.info(f"{user_id} added option to portfolio {portfolio_key} : {ticker} <-- {option_key}")

            return new_option_id # Return the option index
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error adding option to portfolio {portfolio_key} : {e}")
            return -1
        
    # This function is used to delete an option from a user's portfolio
    async def delete_option(self, user_id: int, portfolio_id: int, ticker: str, option_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio
        option = await self.get_option(user_id, portfolio_id, ticker, option_id) # Get the option

        if not portfolio or not option:
            return False
        
        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key
        option_key = option["option_key"] # Get the option key

        try:
            # Delete the option from the database
            await self.connection.execute(
                "DELETE FROM Options WHERE user_id = ? AND portfolio_key = ? AND option_id = ? AND ticker = ?",
                (user_id, portfolio_key, option_id, ticker,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} deleted option from portfolio {portfolio_key} : {ticker} <-- {option_key}")

            await self.update_option_indexes(user_id, portfolio_id) # Update the option indexes

            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error deleting option from portfolio {portfolio_key} : {e}")
            return False
        
    # This function is used to update an option in a user's portfolio
    async def update_option(self, user_id: int, portfolio_id: int, ticker: str, option_id: int, uOption: UserOption) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio

        if not portfolio:
            return False
        
        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key

        try:
            # Update the option in the database
            await self.connection.execute(
                "UPDATE Options SET type = ?, strike = ?, expires = ?, quantity = ?, premium = ?, status = ? WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND option_id = ?",
                (uOption.optionType, uOption.strike, uOption.expires, uOption.quantity, uOption.premium, uOption.status, user_id, portfolio_key, ticker, option_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} updated option in portfolio {portfolio_key} : {ticker} <-- {option_id}")

            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error updating option in portfolio {portfolio_key} : {e}")
            return False
        
    # <-- GETTERS -->

    # This function gets the option data for a user's portfolio
    async def get_option(self, user_id: int, portfolio_id: int, ticker: str, option_id: int) -> Row | None:
        if self.connection is None:
            return None
        
        portfolio = await self.get_portfolio(user_id, portfolio_id)

        if not portfolio:
            return None
        
        portfolio_key = portfolio["portfolio_key"]

        # Get the option from the database
        async with self.connection.execute(
            "SELECT * FROM Options WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND option_id = ?",
            (user_id, portfolio_key, ticker, option_id,)
        ) as cursor:
            return await cursor.fetchone()
        
    # This function is used to get all options in a user's portfolio
    async def get_options(self, user_id: int, portfolio_id: int) -> Iterable[Row] | None:
        if self.connection is None:
            return None
        
        portfolio = await self.get_portfolio(user_id, portfolio_id)

        if not portfolio:
            return None
        
        portfolio_key = portfolio["portfolio_key"]

        # Get all options in the portfolio from the database
        async with self.connection.execute(
            "SELECT * FROM Options WHERE user_id = ? AND portfolio_key = ?",
            (user_id, portfolio_key,)
        ) as cursor:
            return await cursor.fetchall()
        
    # This function is used to get all options in a user's portfolio for a stock by ticker
    async def get_options_by_ticker(self, user_id: int, portfolio_id: int, ticker: str) -> Iterable[Row] | None:
        if self.connection is None:
            return None
        
        portfolio = await self.get_portfolio(user_id, portfolio_id)

        if not portfolio:
            return None
        
        portfolio_key = portfolio["portfolio_key"]

        # Get all options in the portfolio for the stock from the database
        async with self.connection.execute(
            "SELECT * FROM Options WHERE user_id = ? AND portfolio_key = ? AND ticker = ?",
            (user_id, portfolio_key, ticker,)
        ) as cursor:
            return await cursor.fetchall()
        
    # This function is used to get the total number of options in the database
    async def get_total_option_count(self) -> int:
        if self.connection is None:
            return -1
        
        # Get the total number of options in the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Options"
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0
        
    # This function is used to get the total number of options in a user's portfolio
    async def get_option_count(self, user_id: int, portfolio_id: int) -> int:
        if self.connection is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id)

        if not portfolio:
            return -1
        
        portfolio_key = portfolio["portfolio_key"]

        # Get the total number of options in the portfolio from the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Options WHERE user_id = ? AND portfolio_key = ?",
            (user_id, portfolio_key,)
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0
    
    # This function is used to get the total number of options in a user's portfolio for a stock by ticker
    async def get_option_count_by_ticker(self, user_id: int, portfolio_id: int, ticker: str) -> int:
        if self.connection is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id)

        if not portfolio:
            return -1
        
        portfolio_key = portfolio["portfolio_key"]

        # Get the total number of options in the portfolio for the stock from the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Options WHERE user_id = ? AND portfolio_key = ? AND ticker = ?",
            (user_id, portfolio_key, ticker,)
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0
    
    # This function is used to get the total number of call options in a user's portfolio for a stock by ticker
    async def get_call_count(self, user_id: int, portfolio_id: int, ticker: str) -> int:
        if self.connection is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id)

        if not portfolio:
            return -1
        
        portfolio_key = portfolio["portfolio_key"]

        # Get the total number of call options in the portfolio for the stock from the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Options WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND type = 'Call'",
            (user_id, portfolio_key, ticker,)
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0
        
    # This function is used to get the total number of put options in a user's portfolio for a stock by ticker
    async def get_put_count(self, user_id: int, portfolio_id: int, ticker: str) -> int:
        if self.connection is None:
            return -1
        
        portfolio = await self.get_portfolio(user_id, portfolio_id)

        if not portfolio:
            return -1
        
        portfolio_key = portfolio["portfolio_key"]

        # Get the total number of put options in the portfolio for the stock from the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Options WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND type = 'Put'",
            (user_id, portfolio_key, ticker,)
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0

    # <-- MISC FUNCTIONS -->

    # This function is used to update the option indexes in the database
    async def update_option_indexes(self, user_id: int, portfolio_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False

        portfolio = await self.get_portfolio(user_id, portfolio_id)

        if not portfolio:
            return False

        portfolio_key = portfolio["portfolio_key"]

        try:
            # Update the option indexes in the database
            options = await self.get_options(user_id, portfolio_id)

            if not options:
                return False

            options_list = list(options) # Convert Iterable[Row] to list

            for i in range(len(options_list)):
                await self.connection.execute(
                    "UPDATE Options SET option_id = ? WHERE user_id = ? AND portfolio_key = ?",
                    (i, user_id, portfolio_key,)
                )
                await self.connection.commit() # Commit the changes
            self.logger.info(f"updated {len(options_list)} option indexes for {user_id}")
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error updating option indexes for {user_id} : {e}")
            return False
    
    # This function is used to close an option in a user's portfolio
    async def close_option(self, user_id: int, portfolio_id: int, ticker: str, option_id: int, gain_loss: float) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id) # Get the portfolio
        option = await self.get_option(user_id, portfolio_id, ticker, option_id) # Get the option

        if not portfolio or not option:
            return False
        
        portfolio_key = portfolio["portfolio_key"] # Get the portfolio key
        option_key = option["option_key"] # Get the option key

        try:
            # Close the option in the database
            await self.connection.execute(
                "UPDATE Options SET status = 'Closed', gain_loss = ? WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND option_id = ?",
                (gain_loss, user_id, portfolio_key, ticker, option_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} closed option in portfolio {portfolio_key} : {ticker} <-- {option_key}")

            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error closing option in portfolio {portfolio_key} : {e}")
            return False

    # This function is used to expire an option in a user's portfolio
    async def expire_option(self, user_id: int, portfolio_id: int, ticker: str, option_id: int, gain_loss: float) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id)
        option = await self.get_option(user_id, portfolio_id, ticker, option_id)

        if not portfolio or not option:
            return False
        
        portfolio_key = portfolio["portfolio_key"]
        option_key = option["option_key"]

        try:
            # Expire the option in the database
            await self.connection.execute(
                "UPDATE Options SET status = 'Expired', gain_loss = ? WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND option_id = ?",
                (gain_loss, user_id, portfolio_key, ticker, option_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} expired option in portfolio {portfolio_key} : {ticker} <-- {option_key}")

            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error expiring option in portfolio {portfolio_key} : {e}")
            return False

    # This function is used to exercise an option in a user's portfolio
    async def exercise_option(self, user_id: int, portfolio_id: int, ticker: str, option_id: int, gain_loss: float) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        portfolio = await self.get_portfolio(user_id, portfolio_id)
        option = await self.get_option(user_id, portfolio_id, ticker, option_id)

        if not portfolio or not option:
            return False
        
        portfolio_key = portfolio["portfolio_key"]
        option_key = option["option_key"]

        try:
            # Exercise the option in the database
            await self.connection.execute(
                "UPDATE Options SET status = 'Exercised', gain_loss = ? WHERE user_id = ? AND portfolio_key = ? AND ticker = ? AND option_id = ?",
                (gain_loss, user_id, portfolio_key, ticker, option_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} exercised option in portfolio {portfolio_key} : {ticker} <-- {option_key}")

            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error exercising option in portfolio {portfolio_key} : {e}")
            return False

    # ========================================================================================================================================================================
    # Watchlists Functions
    # ========================================================================================================================================================================

    # This function is used to check if a watchlist exists in the database
    async def does_watchlist_exist(self, user_id: int, watchlist_id: int) -> bool:
        if self.connection is None:
            return False
        
        # Check if the watchlist exists in the database
        async with self.connection.execute(
            "SELECT * FROM Watchlists WHERE user_id = ? AND watchlist_id = ?",
            (user_id, watchlist_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None
    
    # This function is used to check if a watchlist exists in the database by name
    async def does_watchlist_exist_by_name(self, user_id: int, name: str) -> bool:
        if self.connection is None:
            return False
        
        # Check if the watchlist exists in the database
        async with self.connection.execute(
            "SELECT * FROM Watchlists WHERE user_id = ? AND name = ?",
            (user_id, name,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None

    # This function is used to create a watchlist for a user
    async def create_watchlist(self, user_id: int, name: str = "", description: str = "") -> int:
        if self.connection is None or self.logger is None:
            return -1
        

        try:
            new_watchlist_id = await self.get_watchlist_count(user_id) # Get the current watchlist count
            created = datetime.datetime.now().strftime(self.date_format)

            # Check if the watchlist name is empty
            if name == "":
                name = f"Watchlist {new_watchlist_id}"

            # Insert the watchlist into the database
            await self.connection.execute(
                "INSERT INTO Watchlists (user_id, watchlist_id, name, description, created) VALUES (?, ?, ?, ?, ?)",
                (user_id, new_watchlist_id, name, description, created,)
            )

            await self.connection.commit()

            watchlist = await self.get_watchlist(user_id, new_watchlist_id) # Get the watchlist

            if not watchlist:
                return -1
            
            watchlist_key = watchlist["watchlist_key"]

            self.logger.info(f"{user_id} created watchlist {watchlist_key} : {name}")

            return new_watchlist_id
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error creating watchlist for {user_id} : {e}")

            return -1
    
    # This function is used to delete a watchlist from the database
    async def delete_watchlist(self, user_id: int, watchlist_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        try:
            watchlist = await self.get_watchlist(user_id, watchlist_id) # Get the watchlist

            if not watchlist:
                return False

            watchlist_key = watchlist["watchlist_key"] # Get the watchlist key
            # Delete the watchlist from the database
            await self.connection.execute(
                "DELETE FROM Watchlists WHERE user_id = ? AND watchlist_id = ?",
                (user_id, watchlist_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} deleted watchlist {watchlist_key}")
            await self.update_watchlist_indexes(user_id) # Update the watchlist indexes

            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error deleting watchlist for {user_id} : {e}")
            return False

    # This function is used to rename a watchlist from the database
    async def rename_watchlist(self, user_id: int, watchlist_id: int, new_name: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        watchlist = await self.get_watchlist(user_id, watchlist_id) # Get the watchlist

        if not watchlist:
            return False

        watchlist_key = watchlist["watchlist_key"] # Get the watchlist key
        watchlist_old_name = watchlist["name"] # Get the old name

        try:
            # Update the watchlist name in the database
            await self.connection.execute(
                "UPDATE Watchlists SET wname = ? WHERE user_id = ? AND watchlist_id = ?",
                (new_name, user_id, watchlist_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} renamed watchlist {watchlist_key} : {watchlist_old_name} --> {new_name}") # Log the change
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error renaming watchlist for {user_id} : {e}")
            return False

    # <-- GETTERS -->

    # This function is used to get a watchlist from the database
    async def get_watchlist(self, user_id: int, watchlist_id: int) -> Row | None:
        if self.connection is None:
            return None
        
        # Get the watchlist from the database
        async with self.connection.execute(
            "SELECT * FROM Watchlists WHERE user_id = ? AND watchlist_id = ?",
            (user_id, watchlist_id,)
        ) as cursor:
            return await cursor.fetchone()
    
    # This function is used to get all watchlists of a user
    async def get_watchlists(self, user_id: int) -> Iterable[Row] | None:
        if self.connection is None:
            return None
        
        # Get all watchlists of the user from the database
        async with self.connection.execute(
            "SELECT * FROM Watchlists WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()
    
    # This function is used to get the number of watchlists of a user
    async def get_watchlist_count(self, user_id: int) -> int:
        if self.connection is None:
            return -1
        
        # Get the total number of watchlists in the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Watchlists WHERE user_id = ?",
            (user_id,)
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0

    # This function is used to get the total number of watchlists in the database
    async def get_total_watchlist_count(self) -> int:
        if self.connection is None:
            return -1
        
        # Get the total number of watchlists in the database
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Watchlists"
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0
    
    # This function is used to get a watchlist from the database by name
    async def get_watchlist_by_name(self, user_id: int, name: str) -> Row | None:
        if self.connection is None:
            return None
        
        # Get the watchlist from the database
        async with self.connection.execute(
            "SELECT * FROM Watchlists WHERE user_id = ? AND name = ?",
            (user_id, name,)
        ) as cursor:
            return await cursor.fetchone()
    
    # <-- MISC FUNCTIONS -->

    # This function is used to rename the description of a watchlist
    async def update_watchlist_description(self, user_id: int, watchlist_id: int, description: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        watchlist = await self.get_watchlist(user_id, watchlist_id) # Get the watchlist

        if not watchlist:
            return False
        
        watchlist_key = watchlist["watchlist_key"] # Get the watchlist key
        watchlist_old_description = watchlist["description"] # Get the old description

        try:
        # Update the watchlist description in the database
            await self.connection.execute(
                "UPDATE Watchlists SET description = ? WHERE user_id = ? AND watchlist_id = ?",
                (description, user_id, watchlist_id,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} updated watchlist {watchlist_key}'s description : \"{watchlist_old_description}\" --> \"{description}\"") # Log the change
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error updating watchlist {watchlist_key}'s description for {user_id} : {e}")
            return False
        
    # This function is used to update the watchlist indexes in the database
    async def update_watchlist_indexes(self, user_id: int) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        watchlists = await self.get_watchlists(user_id) # Get all watchlists of the user

        if not watchlists:
            return False
        
        try:
            watchlists = list(watchlists) # Convert Iterable[Row] to list
            # Update the watchlist indexes in the database
            for i in range(len(watchlists)):
                await self.connection.execute(
                    "UPDATE Watchlists SET watchlist_id = ? WHERE user_id = ?",
                    (i, user_id,)
                )
                await self.connection.commit() # Commit the changes

            self.logger.info(f"Updated {len(watchlists)} watchlist indexes for {user_id}")

            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error updating watchlist indexes for {user_id} : {e}")
            return False
   
    # ========================================================================================================================================================================
    # Watching Functions
    # ========================================================================================================================================================================

    # This function is used to check if a stock is being watched by a user
    async def is_stock_watched(self, user_id: int, watchlist_id: int, ticker: str) -> bool:
        if self.connection is None:
            return False
        
        watchlist = await self.get_watchlist(user_id, watchlist_id) # Get the watchlist

        if not watchlist:
            return False

        watchlist_key = watchlist["watchlist_key"] # Get the watchlist key

        # Check if the stock is being watched by the user
        async with self.connection.execute(
            "SELECT * FROM Watching WHERE user_id = ? AND watchlist_key = ? AND ticker = ?",
            (user_id, watchlist_key, ticker,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None
    
    # This function is used to check if a stock is being watched by a user by name
    async def is_stock_watched_by_name(self, user_id: int, watchlist_name: str, ticker: str) -> bool:
        if self.connection is None:
            return False
        
        watchlist = await self.get_watchlist_by_name(user_id, watchlist_name)

        if watchlist is None:
            return False
        
        watchlist_key = watchlist["watchlist_key"]

        async with self.connection.execute(
            "SELECT * FROM Watching WHERE user_id = ? AND watchlist_key = ? AND ticker = ?",
            (user_id, watchlist_key, ticker,)
        ) as cursor:
            row = await cursor.fetchone()
            return row is not None
        
    # This function is used to add a stock to a user's watchlist
    async def add_stock_to_watchlist(self, user_id: int, watchlist_id: int, ticker: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        watchlist = await self.get_watchlist(user_id, watchlist_id) # Get the watchlist

        if not watchlist:
            return False

        watchlist_key = watchlist["watchlist_key"] # Get the watchlist key

        try:
            # Add the stock to the watchlist
            await self.connection.execute(
                "INSERT INTO Watching (user_id, watchlist_key, ticker) VALUES (?, ?, ?)",
                (user_id, watchlist_key, ticker,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} added stock to watchlist {watchlist_key} : {ticker}")
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error adding stock to watchlist for {user_id} : {e}")
            return False
    
    # This function is used to add a stock to a user's watchlist by name
    async def add_stock_to_watchlist_by_name(self, user_id: int, watchlist_name: str, ticker: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        watchlist = await self.get_watchlist_by_name(user_id, watchlist_name)

        if watchlist is None:
            return False
        
        watchlist_key = watchlist["watchlist_key"]

        try:
            # Add the stock to the watchlist
            await self.connection.execute(
                "INSERT INTO Watching (user_id, watchlist_key, ticker) VALUES (?, ?, ?)",
                (user_id, watchlist_key, ticker,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} added stock to watchlist {watchlist_key} : {ticker}")
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error adding stock to watchlist for {user_id} : {e}")
            return False

    # This function is used to remove a stock from a user's watchlist
    async def remove_stock_from_watchlist(self, user_id: int, watchlist_id: int, ticker: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        watchlist = await self.get_watchlist(user_id, watchlist_id) # Get the watchlist

        if not watchlist:
            return False

        watchlist_key = watchlist["watchlist_key"]

        try:
            # Remove the stock from the watchlist
            await self.connection.execute(
                "DELETE FROM Watching WHERE user_id = ? AND watchlist_key = ? AND ticker = ?",
                (user_id, watchlist_key, ticker,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} removed stock from watchlist {watchlist_key} : {ticker}")
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error removing stock from watchlist for {user_id} : {e}")
            return False

    # This function is used to remove a stock from a user's watchlist by name
    async def remove_stock_from_watchlist_by_name(self, user_id: int, watchlist_name: str, ticker: str) -> bool:
        if self.connection is None or self.logger is None:
            return False
        
        watchlist = await self.get_watchlist_by_name(user_id, watchlist_name)

        if watchlist is None:
            return False
        
        watchlist_key = watchlist["watchlist_key"]

        try:
            # Remove the stock from the watchlist
            await self.connection.execute(
                "DELETE FROM Watching WHERE user_id = ? AND watchlist_key = ? AND ticker = ?",
                (user_id, watchlist_key, ticker,)
            )

            await self.connection.commit() # Commit the changes

            self.logger.info(f"{user_id} removed stock from watchlist {watchlist_key} : {ticker}")
            return True
        except Exception as e:
            await self.connection.rollback()
            self.logger.error(f"error removing stock from watchlist for {user_id} : {e}")
            return False

    # <-- GETTERS -->

    # This function is used to get all stocks in a user's watchlist
    async def get_watchlist_stocks(self, user_id: int, watchlist_id: int) -> Iterable[Row] | None:
        if self.connection is None:
            return None
        
        watchlist = await self.get_watchlist(user_id, watchlist_id) # Get the watchlist

        if not watchlist:
            return None
        
        watchlist_key = watchlist["watchlist_key"]

        # Get all stocks in the watchlist from the database
        async with self.connection.execute(
            "SELECT * FROM Watching WHERE user_id = ? AND watchlist_key = ?",
            (user_id, watchlist_key,)
        ) as cursor:
            return await cursor.fetchall()
    
    # This function is used to get the total number of stocks in a user's watchlist
    async def get_watchlist_stock_count(self, user_id: int, watchlist_id: int) -> int:
        if self.connection is None:
            return -1
        
        watchlist = await self.get_watchlist(user_id, watchlist_id) # Get the watchlist

        if not watchlist:
            return -1
        
        watchlist_key = watchlist["watchlist_key"]

        async with self.connection.execute(
            "SELECT COUNT(*) FROM Watching WHERE user_id = ? AND watchlist_key = ?",
            (user_id, watchlist_key,)
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0
    
    # This function is used to get the total number of stocks watched in the database
    async def get_total_watchlist_stock_count(self) -> int:
        if self.connection is None:
            return -1
        
        async with self.connection.execute(
            "SELECT COUNT(*) FROM Watching"
        ) as cursor:
            all = await cursor.fetchone()
            return all[0] if all else 0
