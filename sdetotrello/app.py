import json
from .utils import management as mgmt

# Extract configurations
with open("config.json", 'r') as config_file:
    configs = json.load(config_file)

# Create a list of all database connections to comb through
connections = []
for val in configs["database_connections"].values():
    connections += val
# Create a list of keywords that the feature class must contain
filters = configs["filters"]


def main():
    # Summarize all features in all database connections
    items = mgmt.find_in_database(connections, filters)
