# **Barcelona Bicing Telegram Bot**
A Telegram bot that provides operations with Barcelona's Bicing system in realtime.

## **Start using the bot**
The bot can be used straightaway without the need to install anything.  
Add it on Telegram through the name t.me/BicingAP2_bot and start typing the commands! (_See section "commands"_).  
It can be used as any other Telegram bot. It may be used on a private chat or a group.  

<br/><br/>

## **Running the program files**
To use the program independently of the official version on the server, the source files are provided.

#### **Creating a Telegram bot**
A new Telegram bot is needed in order to run it on your own. Make sure to follow the [official instructions](https://telegram.org/blog/bot-revolution) to create it.  
Once a token is obtained, place it in a text file (`token.txt`) on the same folder as the source code.

#### **Architecture of the project**
The project consists of four main files:  
`README.md` -> The current README file  
`bot.py` -> The code regarding the bot. Serves as a layer between Telegram and the main project.  
`data.py` -> The main functions of the project. May be used independently from _`bot.py`_.  
`requirements.txt` -> (_See the next section, "prerequisites"_).  
In order to run the bot, the _`bot.py`_ and _`data.py`_ files should be kept on the same directory.

#### **Prerequisites**
To run the project a Pyhton 3 interpreter is needed (may already be installed by default in some computers).  
Some Python libraries are also required; those can be seen in the requirements.txt file. We recomend installing them through pip with the command `pip install -r requirements.txt`. They can, however, be installed separately or through any other medium.  
Internet connection is also necessary, both to download the data every time it is needed and to run the bot through Telegram.

#### **Final steps**
Once everything is in place, the only thing needed is to run the bot (the `bot.py` file) through the interpreter.

<br/><br/>

## **Commands**
The user interacts with the bot through commands. Here is a list of them with a brief description.  
Any typed command should start with a forward slash (/). Any possible argument a command may require should be separated by a blank space.

##### **Start**
	
	/start
Initializes the conversation with the bot and assigns a default graph to the user with distance 1000.  
It is required before typing other commands.

##### **Help**
	
	/help
Displays a list of possible commands, with a brief description of all of them.  
May be used before starting.

##### **Graph**
	
	/graph <distance>
Creates a new graph with the given distance (that is, only the nodes that are less than the given distance apart are connected). The new graph will remain the same until a new one is created through the same command.  
Note that by default a graph with distance 1000 will be created. The argument _distance_ is necessary.

##### **Edges**
	
	/edges
Displays the number of edges the current graph has.

##### **Nodes**
	
	/nodes
Displays the number of nodes the current graph has.

##### **Connected components**
	
	/components
Displays the number of connected components the current graph has.  
An isolated station counts as a single connected component.

##### **Plot graph**
	
	/plotgraph
Sends an image of the current graph.

##### **Route**
	
	/route <address #1>, <address #2>
Sends an image of the shortest path between two given addresses of Barcelona.

##### **Distribute**
	
	/distribute <# of bikes> <# of docks>
Displays the cost and most expensive movement to acomplish the minimum cost distribution of bikes that follows the given conditions.  
_# of bikes_ refers to the minimum number of available bikes any station is required to have.  
_# of docks_ refers to the minimum number of available docks any station is required to have.  
Updates the number of available bikes and docks for future commands. If the distribution is not possible, nothing is modified.
Both arguments are necessary.

##### **Update**
	
	/update
For efficiency reasons, since the stations are unlikely to change during the conversation, the data is downloaded only once at the beginning and resued to build other graphs with different distances.  
This commmand allows to update the data the graph is built on, downloading it again and constructing a new graph with the same preferences.  
It also updates the current available bikes and docks with real data.

##### **Authors**
	
	/authors
Shows the name of the authors of this project.  
May be used before starting.

<br/><br/>

## **References**
#### **Official statement of the project**
The instructions of the project (in Catalan) can be found [here](https://github.com/jordi-petit/ap2-bicingbot-2019).

#### **Python modules used**
[NetworkX](https://networkx.github.io/): used for representing and dealing with graphs.  
[pandas](https://pandas.pydata.org/): used for obtaining and dealing with the dataframes.  
[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot): used for communicating with the bot.  
[Haversine](https://pypi.org/project/haversine/): used for obtaining distances through coordinates.  
[GeoPy](https://geopy.readthedocs.io/en/stable/): used for obtaining the coordinates of addresses.  
[Static Map](https://github.com/komoot/staticmap): used for generating the images of maps.
