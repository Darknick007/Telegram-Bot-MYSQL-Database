import os
import configparser  # pip install configparser
from telethon import TelegramClient, events  # pip install telethon
from datetime import datetime
import MySQLdb  # pip install mysqlclient
from config import api_id,api_hash,bot_token,hostname,username,password,database
# Initializing Configuration
print("Initializing configuration...")
config = configparser.ConfigParser()
config.read('config.ini')

API_ID = api_id
API_HASH = api_hash    
BOT_TOKEN = bot_token

# Ensure the directory exists for session storage
session_directory = os.path.join(os.path.dirname(__file__), "sessions")
os.makedirs(session_directory, exist_ok=True)
session_name = os.path.join(session_directory, "Bot")

# Read values for MySQLdb
HOSTNAME = hostname
USERNAME = username
PASSWORD = password
DATABASE = database

# Start the Client (telethon)
client = TelegramClient(session_name, API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# START COMMAND
@client.on(events.NewMessage(pattern="(?i)/start"))
async def start(event):
    # Get sender
    sender = await event.get_sender()
    SENDER = sender.id
    
    # Set text and send message
    text = "Hello i am a bot that can do CRUD operations inside a MySQL database"
    await client.send_message(SENDER, text)
@client.on(events.NewMessage(pattern="(?i)/help"))
async def help(event):
    sender = await event.get_sender()
    SENDER = sender.id

    help_message = """
**Available commands:**

* **/start:** Starts the bot and shows this help message.
* **/insert <product> <quantity>:** Inserts a new order into the database.
* **/select:** Displays all orders in the database.
* **/update <id> <new_product> <new_quantity>:** Modifies an existing order.
* **/delete <id>:** Deletes an order from the database.

**Examples:**
* `/insert milk 2`
* `/select`
* `/update 3 juice 1`
* `/delete 2`
    """

    await client.send_message(SENDER, help_message)
# Insert command
@client.on(events.NewMessage(pattern="(?i)/insert"))
async def insert(event):
    try:
        # Get the sender of the message
        sender = await event.get_sender()
        SENDER = sender.id

        # /insert bottle 10

        # Get the text of the user AFTER the /insert command and convert it to a list (splitting by SPACE " " symbol)
        list_of_words = event.message.text.split(" ")
        product = list_of_words[1]  # The second (1) item is the product
        quantity = list_of_words[2]  # The third (2) item is the quantity
        dt_string = datetime.now().strftime("%d/%m/%Y")  # Use the datetime library to the get the date (formatted as DAY/MONTH/YEAR)

        # Create the tuple "params" with all the parameters inserted by the user
        params = (product, quantity, dt_string)
        sql_command = "INSERT INTO orders VALUES (NULL, %s, %s, %s);"  # The initial NULL is for the AUTOINCREMENT id inside the table
        crsr.execute(sql_command, params)  # Execute the query
        conn.commit()  # Commit the changes

        # If at least 1 row is affected by the query we send specific messages
        if crsr.rowcount < 1:
            text = "Something went wrong, please try again"
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Order correctly inserted"
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e:
        print(e)
        await client.send_message(SENDER, "Something Wrong happened... Check your code!", parse_mode='html')
        return

# Function that creates a message containing a list of all the orders
def create_message_select_query(ans):
    text = ""
    for i in ans:
        id = i[0]
        product = i[1]
        quantity = i[2]
        creation_date = i[3]
        text += "<b>" + str(id) + "</b> | " + "<b>" + str(product) + "</b> | " + "<b>" + str(quantity) + "</b> | " + "<b>" + str(creation_date) + "</b>\n"
    message = "<b>Received 📖 </b> Information about orders:\n\n" + text
    return message

# SELECT COMMAND
@client.on(events.NewMessage(pattern="(?i)/select"))
async def select(event):
    try:
        # Get the sender of the message
        sender = await event.get_sender()
        SENDER = sender.id
        # Execute the query and get all (*) the orders
        crsr.execute("SELECT * FROM orders")
        res = crsr.fetchall()  # Fetch all the results
        # If there is at least 1 row selected, print a message with the list of all the orders
        # The message is created using the function defined above
        if res:
            text = create_message_select_query(res)
            await client.send_message(SENDER, text, parse_mode='html')
        # Otherwise, print a default text
        else:
            text = "No orders found inside the database."
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e:
        print(e)
        await client.send_message(SENDER, "Something Wrong happened... Check your code!", parse_mode='html')
        return

# UPDATE COMMAND
@client.on(events.NewMessage(pattern="(?i)/update"))
async def update(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        # Get the text of the user AFTER the /update command and convert it to a list (splitting by SPACE " " symbol)
        list_of_words = event.message.text.split(" ")
        id = int(list_of_words[1])  # Second (1) item is the id
        new_product = list_of_words[2]  # Third (2) item is the product
        new_quantity = list_of_words[3]  # Fourth (3) item is the quantity
        dt_string = datetime.now().strftime("%d/%m/%Y")  # We create the new date

        # Create the tuple with all the params inserted by the user
        params = (id, new_product, new_quantity, dt_string, id)

        # Create the UPDATE query, updating the product with a specific id so we must put the WHERE clause
        sql_command = "UPDATE orders SET id=%s, product=%s, quantity=%s, LAST_EDIT=%s WHERE id = %s"
        crsr.execute(sql_command, params)  # Execute the query
        conn.commit()  # Commit the changes

        # If at least 1 row is affected by the query we send a specific message
        if crsr.rowcount < 1:
            text = "Order with id {} is not present".format(id)
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Order with id {} correctly updated".format(id)
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e:
        print(e)
        await client.send_message(SENDER, "Something Wrong happened... Check your code!", parse_mode='html')
        return

@client.on(events.NewMessage(pattern="(?i)/delete"))
async def delete(event):
    try:
        # Get the sender
        sender = await event.get_sender()
        SENDER = sender.id

        # /delete 1

        # Get list of words inserted by the user
        list_of_words = event.message.text.split(" ")
        id = list_of_words[1]  # The second (1) element is the id

        # Create the DELETE query passing the id as a parameter
        sql_command = "DELETE FROM orders WHERE id = (%s);"

        # ans here will be the number of rows affected by the delete
        ans = crsr.execute(sql_command, (id,))
        conn.commit()

        # If at least 1 row is affected by the query we send a specific message
        if ans < 1:
            text = "Order with id {} is not present".format(id)
            await client.send_message(SENDER, text, parse_mode='html')
        else:
            text = "Order with id {} was correctly deleted".format(id)
            await client.send_message(SENDER, text, parse_mode='html')

    except Exception as e:
        print(e)
        await client.send_message(SENDER, "Something Wrong happened... Check your code!", parse_mode='html')
        return

# Create database function
def create_database(query):
    try:
        crsr_mysql.execute(query)
        print("Database created successfully")
    except Exception as e:
        print(f"WARNING: '{e}'")

# MAIN

if __name__ == '__main__':
    try:
        print("Initializing Database...")
        conn_mysql = MySQLdb.connect( host=HOSTNAME, user=USERNAME, passwd=PASSWORD )
        crsr_mysql = conn_mysql.cursor()

        query = "CREATE DATABASE "+str(DATABASE)
        create_database(query)
        conn = MySQLdb.connect( host=HOSTNAME, user=USERNAME, passwd=PASSWORD, db=DATABASE )
        crsr = conn.cursor()

        # Command that creates the "oders" table 
        sql_command = """CREATE TABLE IF NOT EXISTS orders ( 
            id INTEGER PRIMARY KEY AUTO_INCREMENT, 
            product VARCHAR(200),
            quantity INT(10), 
            LAST_EDIT VARCHAR(100));"""

        crsr.execute(sql_command)
        print("All tables are ready")
        
        print("Bot Started...")
        client.run_until_disconnected()

    except Exception as error:
        print('Cause: {}'.format(error))