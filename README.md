# Stock Portfolio Discord Bot

## Overview
This Discord bot allows users to manage their stock portfolios directly within a Discord server. Users can add, remove, and view stocks in their portfolios, and the bot stores this data using an SQLite database. The bot is built using Python and leverages the `discord.py` library for interacting with Discord using slash commands, as well as `sqlite3` for database management.

## Features

- **Add/Remove Shares**: Users can manage their shares of a company.
- **Add/Remove Options**: Users can manage their option trades.
- **Add/Remove Dividends** Users can manage their dividend earnings.
- **View Portfolio**: Users can view the details of their portfolio, including all the stocks they own, price at which they bought/sold it, and the number of shares for each.
- **Real-Time Data (Planned Feature)**: Users can view real-time or recent prices for the stocks they search for.
  

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/sleepingstar/stock-portfolio-bot.git
   cd stock-portfolio-bot
   ```
2. **Install Required Packages**
    ```bash
    pip install -r requirements.txt
    ```
3. **Configure the bot**
    * Create a `.env` and add the following:
        ```
        DISCORD_TOKEN={TOKEN_HERE}
        ```
    * Edit the `config.json` file to your liking:
        ```json
        {
            "prefix": "$",
            "disabled_cogs": ["{COG_NAME}"]
        }
        ```
    * Edit the `all_statuses.json` file to your liking:
        ```json
        {
            "statuses" : [
                {
                    "message": "{MESSAGE_HERE}", 
                    "mType": "{TIME HERE}"
                }
            ]
        }
        ```
        message: what the bot will display as it's status

        mTypes: when the status should display, choose one. `anytime, premarket, markethours, aftermarket`
    
    * [Optional] Replace the geckodriver.exe with a different version
        If you would like to replace the included geckodriver with a more recent version, please visit [Mozilla's Repository](https://github.com/mozilla/geckodriver/) to do so.

5. **Run the bot**

    ```bash
    python bot.py
    ```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

## Contributers
[Mateus Smith](https://github.com/SleepingStar)

[Nicholas Watts](https://github.com/Dabby-Tabby)

[Jacob Viveros](https://github.com/YakosWorkshop)
