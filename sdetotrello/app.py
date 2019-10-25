import json
import os
from .utils.management import find_in_database, extract_service_info, extract_ez_layer_info, convert_to_trello_card
from .utils.features import TrelloCard, TrelloBoard

# Extract configurations
print("Extracting config info...")
with open(r".\sdetotrello\config.json", 'r') as config_file:
    configs = json.load(config_file)

# Create a list of all database connections to comb through
print("Assigning config info to variables...")
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
print("Extracting Trello Board info...")
board_id = configs["board_id"]
key = os.environ.get("KEY")
token = os.environ.get("TOKEN")
# Create a TrelloBoard object
board = TrelloBoard(board_id, key, token)
# Initialize the list names
lists = board.lists
# Initialize the label names
labels = board.labels
# Initialize the checklist names
checklists = board.checklists


def main():
    # Summarize all features in all database connections
    print("Extracting info about services...")
    services = extract_service_info(service_defs, filters)
    print("Extracting info about ez layers...")
    ez_layers = extract_ez_layer_info(ez_defs, filters)
    print("Extracting features from the database...")
    items = find_in_database(connections)
    print("Creating card objects...")
    cards = convert_to_trello_card(items, key, token, labels, checklists, services, ez_layers, filters)
    print("Sorting cards...")
    cards.sort(key=lambda x: (x.database, -len(x.load_labels())))
    for card in cards:
        print("Posting ", card.unique_name)
        card.post_card(lists)


main()
