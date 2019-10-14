from arcpy import Describe, ExecuteError, GetCount_management
from os import path


class TrelloFeatureClass:
    """A class intended to gather info about a feature class for input to a Trello card. This builds upon the
    Describe object in arcpy."""
    def __init__(self, tuple_path):
        self.tuple_path = tuple_path
        self.full_path = path.join(*self.tuple_path)
        self._desc_workspace = Describe(self.tuple_path[0])
        self.owner, self.name = self.tuple_path[-1].split(".")
        self.dataset = self.tuple_path[1] if len(self.tuple_path) == 3 else None
        self.database = self._desc_workspace.connectionProperties.instance.split(":")[-1].upper()
        self.unique_name = ".".join([self.database, self.owner, self.name])

    def __getattr__(self, attr):
        """Pass any other attribute or method calls through to the underlying Describe object"""
        return getattr(self._desc_workspace, attr)

    def has_no_records(self):
        """Determines if there are any records in the feature class to analyze."""
        try:
            count = int(GetCount_management(self.full_path).getOutput(0))
            return True if count == 0 else False
        except ExecuteError:
            # TODO: Add info logging describing an error in retrieving a feature count
            return None
