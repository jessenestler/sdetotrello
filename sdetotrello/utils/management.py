import os
from arcpy.da import Walk


def find_in_database(database_connections: list = None, *args) -> tuple:
    """ Finds all possible feature classes within the sde connection provided based on a list of pattern matches, and
    returns a list representing that file path broken into [sde, dataset (if it exists), feature class]. For example,
    the requester might only want to find the path of feature classes that contain "wF", "sw", and "Flood". If no
    patterns are provided, the function will return all feature classes in the sde_path.

    :param database_connections: A list of system paths to databases or database connections
    :param args: A list of optional strings to filter the data
    :return: An Identifier object
    """
    items = list()
    for conn in database_connections:
        walker = Walk(conn, ['FeatureDataset', 'FeatureClass'])
        for directory, folders, files in walker:
            for f in files:
                # if the feature class has already been summarized
                if any(f in x for x in items):
                    continue
                # if the feature class is not in a dataset
                elif any(directory.endswith(x) for x in [".sde", ".gdb", ".mdb"]):
                    items.append((directory, f))
                # if it is in a dataset
                else:
                    dataset = directory.split(os.sep).pop()
                    items.append((directory[:-(1 + len(dataset))], dataset, f))
        del walker

    # Filter based on args passed to the function
    if not args or len(args) == 0:  # If no args are given or the list passed to args is empty
        for item in items:
            yield item
    else:  # else, return filtered
        filtered_items = list(filter(lambda x: any(arg.lower() in "".join(x).lower() for arg in args), items))
        for item in filtered_items:
            yield item
