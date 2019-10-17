from arcpy import Describe, ExecuteError, ArcSDESQLExecute
from os import path


class TrelloFeatureClass:
    """A class intended to gather info about a feature class for input to a Trello card. This builds upon the
    Describe object in arcpy."""
    def __init__(self, tuple_path):
        self.tuple_path = tuple_path
        self.full_path = path.join(*self.tuple_path)
        self.connection = tuple_path[0]
        self._desc_workspace = Describe(self.connection)
        self.database = self._desc_workspace.connectionProperties.instance.split(":")[-1].upper()
        self.dataset = self.tuple_path[1] if len(self.tuple_path) == 3 else None
        self.owner, self.name = self.tuple_path[-1].split(".")
        self.unique_name = ".".join([self.database, self.owner, self.name]).upper()
        self.num_records = self.record_count()

    def __getattr__(self, attr):
        """Pass any other attribute or method calls through to the underlying Describe object"""
        return getattr(self._desc_workspace, attr)

    def record_count(self):
        try:
            query = """SELECT COUNT(*) FROM {}""".format(self.tuple_path[-1].upper())
            execute_object = ArcSDESQLExecute(self.connection)
            result = execute_object.execute(query)
            return int(result)
        except (ExecuteError, TypeError):
            return None

    def has_no_records(self):
        """Determines if there are any records in the feature class to analyze."""
        return True if self.num_records == 0 else False

    def geometry_type(self):
        """Describes the feature class rather than the workspace and return the shape type"""
        try:
            desc = Describe(self.full_path)
            if desc.dataType == 'FeatureClass':
                return desc.shapeType
            else:
                return None
        except OSError:
            return None


class TrelloCard(TrelloFeatureClass):
    def __init__(self, obj, service_dict, ez_dict):
        super().__init__(obj.tuple_path)
        self.services_list = service_dict[self.unique_name]if self.unique_name in service_dict else None
        self.ez_list = ez_dict[self.unique_name] if self.unique_name in ez_dict else None
