import os
import json
from requests import request
from arcpy.da import Walk


def find_in_database(database_connections: list, filters: list = None) -> list:
    """ Finds all possible feature classes within the sde connection provided based on a list of pattern matches, and
    returns a list representing that file path broken into [sde, dataset (if it exists), feature class]. For example,
    the requester might only want to find the path of feature classes that contain "wF", "sw", and "Flood". If no
    patterns are provided, the function will return all feature classes in the sde_path.

    :param database_connections: A list of system paths to databases or database connections
    :param filters: A list of optional strings to filter the data
    :return: An Identifier object
    """
    # Initialize empty container for gathering all items in the database
    items = list()

    # Iterate over the databases
    for conn in database_connections:
        walker = Walk(conn, ['FeatureDataset', 'FeatureClass'])
        for directory, folders, files in walker:
            for f in files:
                # if the feature class has already been summarized
                if any(f in x[-1] for x in items):
                    continue
                # if the feature class is not in a dataset
                elif any(directory.endswith(x) for x in [".sde", ".gdb", ".mdb"]):
                    items.append((directory, f))
                # if it is in a dataset
                else:
                    dataset = directory.split(os.sep).pop()
                    items.append((os.path.dirname(directory), dataset, f))
        del walker

    # Filter based on args passed to the function
    if not filters or len(filters) == 0:  # If no args are given or the list passed to args is empty
        return items
    else:  # else, return filtered
        filtered_items = list(filter(lambda x: any(arg.lower() in x[-1].lower() for arg in filters), items))
        return filtered_items


def extract_service_info(input_files: list, filters: list = None) -> dict:
    """Extracts service definition info from pre-defined json structures, and summarizes services by layer.

    :param input_files: A list of file paths to json files used to define services
    :param filters: A list of keywords that filter the resulting dictionary
    :return: A dictionary of FeatureClass: [service1_name, service2_name, etc] pairs
    """
    # Extract data from json files into a list
    json_input = list()
    for service_definition in input_files:
        with open(service_definition, 'r') as f:
            json_input.append(json.load(f))

    # Parse these data structures for information on source and layer name
    services_by_layer = dict()
    for j in json_input:
        for mxd in j['mxds']:
            for dataframe in mxd['dataframes']:
                for layer in dataframe['layers']:
                    if not layer['isGroupLayer']:
                        fc = layer['dataSource'].split(os.sep).pop().upper()
                        database = layer['Service'].split(':')[-1].upper()
                        unique_name = ".".join([database, fc])
                        if unique_name not in services_by_layer:
                            services_by_layer[unique_name] = [mxd['mxd']['filepath']]
                        else:
                            services_by_layer[unique_name].append(mxd['mxd']['filepath'])

    # Filter the dictionary
    if filters and isinstance(filters, list):
        filtered_services_by_layer = dict()
        for k, v in services_by_layer.items():
            if any(arg.upper() in k for arg in filters):
                filtered_services_by_layer[k] = v
        return filtered_services_by_layer
    else:
        return services_by_layer


def extract_trello_labels(board: str, key: str, token: str, save_to_file: bool = False) -> dict:
    """Extracts labels from a trello board and saves them locally as a dictionary

    :param board: the id of the board (from the short URL, not the SHA one
    :param key: user's API key
    :param token: user's API token
    :param save_to_file: Whether to save to json file. If yes, saves to ./sdetotrello/trello_labels.json
    :return:
    """
    url = "https://api.trello.com/1/boards/{}/labels".format(board)
    query = {"fields": ["id", "name", "color"],
             "key": key,
             "token": token}
    response = request("GET", url, params=query)
    json_data = json.loads(response.text)

    labels = dict()
    for resp in json_data:
        if resp["name"] != "":
            labels[resp["id"]] = {"name": resp["name"], "color": resp["color"]}

    if save_to_file:
        with open("./sdetotrello/data/trello_labels.json", "w") as json_file:
            json.dump(labels, json_file)
    else:
        return labels
