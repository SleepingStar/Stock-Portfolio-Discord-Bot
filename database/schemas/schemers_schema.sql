CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY,
    created TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Portfolios (
    portfolio_key INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    portfolio_id INTEGER DEFAULT 0,
    name TEXT NOT NULL,
    description TEXT,
    created TEXT NOT NULL,

    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Stocks (
    stock_key INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    portfolio_key INTEGER NOT NULL,
    
    ticker TEXT NOT NULL,
    created TEXT NOT NULL,

    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(portfolio_key) REFERENCES Portfolios(portfolio_key) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Orders (
    order_key INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    portfolio_key INTEGER NOT NULL,
    stock_key INTEGER NOT NULL,

    order_id INTEGER DEFAULT 0,
    ticker TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL NOT NULL,
    created TEXT NOT NULL,
    status TEXT NOT NULL,
    type TEXT NOT NULL,
    gain_loss REAL DEFAULT 0,

    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(portfolio_key) REFERENCES Portfolios(portfolio_key) ON DELETE CASCADE,
    FOREIGN KEY(stock_key) REFERENCES Stocks(stock_key) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Dividends (
    dividend_key INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    portfolio_key INTEGER NOT NULL,
    stock_key INTEGER NOT NULL,

    dividend_id INTEGER DEFAULT 0,
    ticker TEXT NOT NULL,
    dividend REAL NOT NULL,
    created TEXT NOT NULL,

    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(portfolio_key) REFERENCES Portfolios(portfolio_key) ON DELETE CASCADE,
    FOREIGN KEY(stock_key) REFERENCES Stocks(stock_key) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Options (
    option_key INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    portfolio_key INTEGER NOT NULL,
    stock_key INTEGER NOT NULL,

    option_id INTEGER DEFAULT 0,
    ticker TEXT NOT NULL,
    strike REAL NOT NULL,
    quantity REAL NOT NULL,
    premium REAL NOT NULL,
    created TEXT NOT NULL,
    expires TEXT NOT NULL,
    result TEXT NOT NULL,
    type TEXT NOT NULL,
    gain_loss REAL DEFAULT 0,

    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(portfolio_key) REFERENCES Portfolios(portfolio_key) ON DELETE CASCADE,
    FOREIGN KEY(stock_key) REFERENCES Stocks(stock_key) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Watchlists (
    watchlist_key INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    watchlist_id INTEGER DEFAULT 0,
    name TEXT NOT NULL,
    description TEXT,
    created TEXT NOT NULL,

    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Watching (
    watching_key INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    watchlist_key INTEGER NOT NULL,

    ticker TEXT NOT NULL,
    created TEXT NOT NULL,
    
    FOREIGN KEY(user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(watchlist_key) REFERENCES Watchlists(watchlist_key) ON DELETE CASCADE
);
