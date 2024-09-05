import aiosqlite
import logging

"""
This module contains the DatabaseManager class which is used to manage the database connection and operations.
"""

# ==========
# Constants
# ==========
log_folder = "./logs/"
schema_folder = "./database/schemas/"

# ==========
# Database Manager
# ==========
class DatabaseManager:
    def __init__(self) -> None:
        self.connection: aiosqlite.Connection | None = None # Connection to the database
        self.logger: logging.Logger | None = None # Logger instance
        self.date_format = "%m-%d-%Y %I:%M:%S %p" # Date format

    # ========================================================================================================================================================================
    # Database Functions
    # ========================================================================================================================================================================

    # This function is used to read an SQL file
    def read_sql_file(self, file_path: str) -> str:
        with open(file_path, 'r') as file:
            return file.read() # Read the SQL file and return the contents

    async def start(self, db_name: str, schema_name: str, logger_name: str, file_name: str):
        await self.file_handler(logger_name, file_name)
        await self.connect(db_name)
        await self.create_tables(schema_name)

    async def file_handler(self, logger_name: str, file_name: str):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(filename=f"{log_folder}{file_name}.log", encoding="utf-8", mode="w")
        file_handler_formatter = logging.Formatter(
            "[{asctime}] [{levelname}] {name}: {message}", f"{self.date_format}", style="{"
        )
        file_handler.setFormatter(file_handler_formatter)

        # Add the handlers
        self.logger.addHandler(file_handler)

    # This function is used to establish a connection to the database
    async def connect(self, db_name: str):
        if self.logger is not None:
            self.connection = await aiosqlite.connect(f"database/{db_name}") # Connect to the database
            self.connection.row_factory = aiosqlite.Row  # Use aiosqlite.Row for dictionary-like access
            await self.connection.execute("PRAGMA foreign_keys = ON;") # Enable foreign keys
            await self.connection.commit()

            self.logger.info(f"connection established") # Log the connection

    # This function is used to close the database connection
    async def close(self):
        if self.connection and self.logger is not None:
            await self.connection.close() # Close the connection
            self.connection = None # Set the connection to None

            self.logger.info(f"connection closed") # Log the closure
    
    # This function is used to reconnect to the database
    async def reconnect(self, db_name: str):
        if self.connection and self.logger is not None:
            await self.close() # Close the connection
            await self.connect(db_name) # Reconnect to the database

            self.logger.info(f"reconnected to the database") # Log the reconnection
    
    # This function is used to create the tables in the database
    async def create_tables(self, schema_name: str):
        sql = self.read_sql_file(f"{schema_folder}{schema_name}") # Read the SQL file
        
        if self.connection and self.logger is not None:
            if not sql:
                self.logger.error(f"Error reading SQL file")
                return
            try:
                async with self.connection.cursor() as cursor:
                    await cursor.executescript(sql) # Execute the SQL script
                    await self.connection.commit() # Commit the changes
                self.logger.info(f"tables created") # Log the creation of the tables
            except Exception as e:
                self.logger.error(f"Error creating tables: {str(e)}") # Log the error
