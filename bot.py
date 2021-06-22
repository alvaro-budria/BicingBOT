import data as dt
import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
import networkx as nx
import re


dict_graphs = dict()


# Sends a message to the user through Telegram
def send_to_user(bot, message, idnum, markdown=False):
    if markdown:
        bot.send_message(chat_id=idnum, text=message, parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        bot.send_message(chat_id=idnum, text=message)


# Sends an error message
def send_error(bot, error, idnum):
    print(error)  # Prints the error on the terminal window as well.
    print(idnum)
    try:
        send_to_user(bot, error, idnum)
    except Exception as e:
        print(e)


# Returns an error if the user's id has no associated graph
def check_id(id):
    if id not in dict_graphs:
        raise ValueError("No graph has been created yet")


# Returns error if the number of arguments is not the one expected
def check_args(passed, expected, strictmax=True):
    if len(passed) > expected and strictmax:
        raise ValueError("Too many arguments")
    elif len(passed) < expected:
        raise ValueError("Too few arguments")


# The default start function.
def start(bot, update):
    try:
        send_to_user(bot, "A new graph created with distance 1000.\nAll commands are available now.", update.message.chat_id)
        usr_id = update.message.from_user["id"]

        # Assign a new graph to the user
        global dict_graphs
        if usr_id not in dict_graphs:
            dict_graphs[usr_id] = [dt.build_graph(), 1000, dt.get_dataframe(True)]  # store the graph, its radius and (stations, bikes that stations have)
    except Exception as e:
        send_error(bot, "Error: " + e.args[0], update.message.chat_id)


# Displays the possible commands and other useful information.
def help(bot, update):
    message = '''
    The available commands are:
    - */start* : starts the bot. A new graph is created with distance 1,000.
    - */help* : displays the possible commands with a brief description.
    - */graph* <_distance_> : create a new graph with a given distance.
    - */edges* : the number of edges the graph currently has.
    - */nodes* : the number of nodes the graph currently has.
    - */components* : the number of connected components the graph currently has.
    - */plotgraph* : get an image of the current graph.
    - */route* <_address #1_>, <_address #2_> : computes the shortest path between the given addresses.
    - */distribute* <_bikes_>, <_docks_> : distributes the bikes to fit the demand
    '''
    bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=telegram.ParseMode.MARKDOWN)


# Prints the number of edges of the current user's graph.
def edges(bot, update):
    try:
        usr_id = update.message.from_user["id"]
        check_id(usr_id)
        text = dt.number_edges(dict_graphs[usr_id][0])
        send_to_user(bot, text, update.message.chat_id)
    except Exception as e:
        send_error(bot, "Error: " + e.args[0], update.message.chat_id)


# Prints the number of nodes of the current user's graph.
def nodes(bot, update):
    try:
        usr_id = update.message.from_user["id"]
        check_id(usr_id)
        text = dt.number_nodes(dict_graphs[usr_id][0])
        send_to_user(bot, text, update.message.chat_id)
    except Exception as e:
        send_error(bot, "Error: " + e.args[0], update.message.chat_id)


# Prints the number of connected components of the current user's graph.
def components(bot, update):
    try:
        usr_id = update.message.from_user["id"]
        check_id(usr_id)
        text = dt.number_components(dict_graphs[usr_id][0])
        send_to_user(bot, text, update.message.chat_id)
    except Exception as e:
        send_error(bot, "Error: " + e.args[0], update.message.chat_id)


def plotgraph(bot, update):
    try:
        usr_id = update.message.from_user["id"]
        check_id(usr_id)
        dt.draw_graph(dict_graphs[usr_id][0])
        bot.send_photo(chat_id=update.message.chat_id, photo=open("stations.png", "rb"))
    except Exception as e:
        send_error(bot, "Error: " + e.args[0], update.message.chat_id)


# Prints the shortest route between two given addresses.
def route(bot, update, args):
    try:
        usr_id = update.message.from_user["id"]
        check_id(usr_id)
        check_args(args, 2, False)

        # Join all the arguments as a single address
        address = ""
        for word in args:
            address = address + " " + word
        dt.shortest_path(dict_graphs[usr_id][0], address)
        bot.send_photo(chat_id=update.message.chat_id, photo=open("path.png", "rb"))
    except Exception as e:
        send_error(bot, "Error: " + e.args[0], update.message.chat_id)


# Updates the graph with a new given distance.
def graph(bot, update, args):
    try:
        usr_id = update.message.from_user["id"]
        check_id(usr_id)
        check_args(args, 1)

        # Check it is a number with the correct format
        if str(args[0]) != "0" and not re.match(r"\d+\.*\d*", str(args[0])):
            raise ValueError("Distance must be a positive number")

        global dict_graphs
        dict_graphs[usr_id] = [dt.build_graph(args[0], dict_graphs[usr_id][0]), float(args[0]), dict_graphs[usr_id][2]]
        send_to_user(bot, "Graph updated to distance " + args[0], update.message.chat_id)
    except Exception as e:
        send_error(bot, "Error: " + e.args[0], update.message.chat_id)


# Displays information of the cost of distributing the bycicles.
def distribute(bot, update, args):
    try:
        usr_id = update.message.from_user["id"]
        check_id(usr_id)
        check_args(args, 2)

        # Check they are non-negative integers
        if (not re.match('^[0-9]+$', str(args[0])) or not re.match('^[0-9]+$', str(args[1])) or
                int(args[0]) < 0 or int(args[1]) < 0):
            raise ValueError("Demands must be positive integers or 0")

        info = dt.minflow((int(args[0]), int(args[1])), dict_graphs[usr_id][1], dict_graphs[usr_id][2])
        send_to_user(bot, info, update.message.chat_id, True)
    except Exception as e:
        if e.args[0] == "impossible":
            bot.send_message(chat_id=update.message.chat_id, text="The distribution is not possible")
        else:
            send_error(bot, "Error: " + e.args[0], update.message.chat_id)


# Displays the names of the authors of this project
def authors(bot, update):
    try:
        message = dt.authors()
        bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode=telegram.ParseMode.MARKDOWN)
    except Exception as e:
        send_error(bot, "Error: " + e.args[0], update.message.chat_id)


# Updates the graph with the same distance but new information
def update(bot, update):
    try:
        usr_id = update.message.from_user["id"]

        global dict_graphs
        dict_graphs[usr_id] = [dt.build_graph(dict_graphs[usr_id][1], None), dict_graphs[usr_id][1], dt.get_dataframe(True)]
        send_to_user(bot, "Graph updated", update.message.chat_id)
    except Exception as e:
        send_error(bot, "Error: " + e.args[0], update.message.chat_id)


# The access token located in "token.txt"
TOKEN = open('token.txt').read().strip()

# Objects necessary to work with Telegram.
updater = Updater(token=TOKEN)
dispatcher = updater.dispatcher

# The possible commands to wait for.
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('help', help))
dispatcher.add_handler(CommandHandler('edges', edges))
dispatcher.add_handler(CommandHandler('nodes', nodes))
dispatcher.add_handler(CommandHandler('components', components))
dispatcher.add_handler(CommandHandler('plotgraph', plotgraph))
dispatcher.add_handler(CommandHandler('graph', graph, pass_args=True))
dispatcher.add_handler(CommandHandler('route', route, pass_args=True))
dispatcher.add_handler(CommandHandler('distribute', distribute, pass_args=True))
dispatcher.add_handler(CommandHandler('update', update))
dispatcher.add_handler(CommandHandler('authors', authors))

# Starts the bot.
updater.start_polling()
