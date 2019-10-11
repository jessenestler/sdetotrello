from arcpy import ArcSDESQLExecute, Describe, ExecuteError, GetCount_management, ListFields
from os import path


class TrelloFeatureClass:
    """A class intended to gather info about a feature class for input to a Trello card. This builds upon the
    Describe object in arcpy."""
    def __init__(self, iterator_path):
        self._desc = Describe(self.full_path)
        self.full_path = path.join(*iterator_path)
        self.owner, self.name = iterator_path[-1].split(".")
        self.dataset = iterator_path[1] if len(iterator_path) == 3 else None

    def __getattr__(self, item):
        """Pass any other attribute or method calls through to the underlying Describe object"""
        return getattr(self._desc, item)

    def has_records(self):
        """Determines if there are any records in the feature class to analyze."""
        try:
            count = int(GetCount_management(self.full_path).getOutput(0))
            return True if count >= 1 else False
        except ExecuteError:
            # TODO: Add info logging describing an error in retrieving a feature count
            return None
