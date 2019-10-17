import json
from .utils import management as mgmt

# Extract configurations
with open(r".\configs\config.json", 'r') as config_file:
    configs = json.load(config_file)
with open(r".\configs\trello.json", "r") as config_file:
    trello_configs = json.load(config_file)

# Create a list of all database connections to comb through
connections = list()
for val in configs["database_connections"].values():
    connections += val
# Create a list of keywords that the feature class must contain
filters = configs["filters"]
# Create a list of data source to inspect
service_defs = configs["services"]
# Create a file path to EZ Layer data
ez_defs = configs["ez_layers"]

# Initialize the trello board
board = trello_configs['board']
# Initialize the list names
lists = trello_configs['lists']
# Initialize the labels names
labels = trello_configs['labels']
# Initialize the list names
checklists = trello_configs['checklists']


def main():
    # Summarize all features in all database connections
    items = mgmt.find_in_database(connections, filters)
