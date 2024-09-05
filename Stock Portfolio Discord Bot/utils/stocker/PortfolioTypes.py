import json
from sqlite3 import Row

"""
PortfolioTypes
    This module is used to create the different types of orders and options that a user can have in their portfolio.
    Easy to pass in a dictionary and convert it to an object.
"""

class UserOrder:
    def __init__(self, 
                 price: float | None = None, 
                 quantity: float | None = None, 
                 created: str | None = None, 
                 status: str | None = None, 
                 orderType: str | None = None, 
                 gain_loss: float | None = None):
        
        # DATABASE_NAME : DESCRIPTION -> VALUES
        self.price = price # price : price of the stock
        self.quantity = quantity # quantity : quantity of the stock
        self.created = created # created : time of order
        self.status = status # status : status of the order -> filled, pending, cancelled
        self.orderType = orderType # type : buy, sell
        self.gain_loss = gain_loss # gain_loss : gain or loss of the order

    # Update the order with new values
    def updateOrder(self,
                 price: float | None = None, 
                 quantity: float | None = None, 
                 created: str | None = None, 
                 status: str | None = None, 
                 orderType: str | None = None, 
                 gain_loss: float | None = None) -> None:
        
        self.price = price if price is not None else self.price
        self.quantity = quantity if quantity is not None else self.quantity
        self.created = created if created is not None else self.created
        self.status = status if status is not None else self.status
        self.orderType = orderType if orderType is not None else self.orderType
        self.gain_loss = gain_loss if gain_loss is not None else self.gain_loss

    # Convert a dictionary to an order
    def fromDict(self, data: Row) -> None:
        self.price = data['price']
        self.quantity = data['quantity']
        self.created = data['created']
        self.status = data['status']
        self.orderType = data['orderType']
        self.gain_loss = data['gain_loss']

    # Convert the order to a string
    def __str__(self) -> str:
        return json.dumps(self.__dict__)
    
class UserOption:
    def __init__(self, 
                 ticker: str | None = None, 
                 strike: float | None = None, 
                 quantity: float | None = None, 
                 premium: float | None = None, 
                 created: str | None = None, 
                 expires: str | None = None, 
                 status: str | None = None, 
                 optionType: str | None = None, 
                 gain_loss: float | None = None): 
        
        self.ticker = ticker # ticker : ticker of the stock option
        self.strike = strike # strike : strike price of the option
        self.quantity = quantity # quantity : quantity of the option
        self.premium = premium # premium : premium of the option
        self.created = created # created : time of option order
        self.expires = expires # expires : expiration date of the option
        self.status = status # status : status of the option -> filled, pending, cancelled, expired, exercised, sold
        self.optionType = optionType # type : type of option -> call, put
        self.gain_loss = gain_loss # gain_loss : gain or loss of the option

        # Embed
        # (status) 
        # quantity ticker strike @ premium on expires
        # created 
    
    # Update the option with new values
    def updateOption(self, newOption: 'UserOption') -> None:
        self.strike = newOption.strike if newOption.strike is not None else self.strike
        self.quantity = newOption.quantity if newOption.quantity is not None else self.quantity
        self.premium = newOption.premium if newOption.premium is not None else self.premium
        self.created = newOption.created if newOption.created is not None else self.created
        self.expires = newOption.expires if newOption.expires is not None else self.expires
        self.status = newOption.status if newOption.status is not None else self.status
        self.optionType = newOption.optionType if newOption.optionType is not None else self.optionType
        self.gain_loss = newOption.gain_loss if newOption.gain_loss is not None else self.gain_loss

    # Convert a dictionary to an option
    def fromDict(self, data: Row) -> None:
        self.ticker = data['ticker']
        self.strike = data['strike']
        self.quantity = data['quantity']
        self.premium = data['premium']
        self.created = data['created']
        self.expires = data['expires']
        self.status = data['status']
        self.optionType = data['optionType']
        self.gain_loss = data['gain_loss']

    # Convert the option to a string
    def __str__(self) -> str:
        return json.dumps(self.__dict__)