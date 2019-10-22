import json

from os import path

from arcpy import Describe, ExecuteError, ArcSDESQLExecute, Exists
from requests import request


class TrelloFeatureClass:
    """A class intended to gather info about a feature class for input to a Trello card. This builds upon the
    Describe object in arcpy."""
    def __init__(self, tuple_path):
        self.tuple_path = tuple_path
        self.full_path = path.join(*self.tuple_path)
        self.connection = tuple_path[0]
        self._desc = self.get_describe()
        self.database = Describe(self.connection).connectionProperties.instance.split(":")[-1].upper()
        self.dataset = self.tuple_path[1] if len(self.tuple_path) == 3 else None
        self.owner, self.name = self.tuple_path[-1].split(".")
        self.unique_name = ".".join([self.database, self.owner, self.name]).upper()

    def __getattr__(self, attr):
        """Pass any other attribute or method calls through to the underlying Describe object"""
        try:
            return getattr(self._desc, attr)
        except AttributeError:
            return None

    def get_describe(self):
        """Returns a describe object if the table exists, otherwise returns None. Gets around an OSError if the table
        is corrupted."""
        try:
            desc = Describe(self.full_path)
            return desc
        except OSError:
            return None

    def record_count(self):
        """Returns the number of records within a table by executing a SQL query in the database"""
        try:
            query_name = self.tuple_path[-1]  # The OWNER.Feature name
            if self.isVersioned:  # Use the versioned view to get a count
                if len(self.name) + 4 > 30:  # +4 for the addition of "_EVW", Oracle has 30 char limit on table name
                    query_name = ".".join([self.owner, self.name[:26]])
                query = """SELECT COUNT(*) FROM {}_EVW""".format(query_name.upper())
            else:
                if len(self.name) > 30:
                    query_name = ".".join([self.owner, self.name[:30]])
                query = """SELECT COUNT(*) FROM {}""".format(query_name.upper())
            execute_object = ArcSDESQLExecute(self.connection)
            result = execute_object.execute(query)
            return int(result)
        except (ExecuteError, TypeError):
            return None

    def has_no_records(self) -> bool:
        """Returns true if the table in question has no records"""
        return True if self.record_count() == 0 else False

    def has_attachments(self) -> bool:
        attach_suffixes = ["__ATTACH", "__ATTACH_EVW", "Photos"]
        attach = any(Exists(self.full_path + suffix) for suffix in attach_suffixes)
        return attach

    def geometry_type(self):
        """Describes the feature class rather than the workspace and return the shape type"""
        try:
            if self.dataType == 'FeatureClass':
                return self.shapeType
            else:
                return None
        except (ExecuteError, OSError):
            return None


class TrelloCard(TrelloFeatureClass):
    def __init__(self, obj, board, key, token, service_dict, ez_dict):
        super().__init__(obj.tuple_path)
        self.board = board
        self.key = key
        self.token = token
        self.services_list = service_dict[self.unique_name]if self.unique_name in service_dict else None
        self.ez_list = ez_dict[self.unique_name] if self.unique_name in ez_dict else None

    def load_description(self):
        """Gives a custom formatted description to use inside of a Feature Class's Trello Card"""
        description = """{metadata}\n\n**SME:** (write down who the SME is here, if applicable)\n**Database:** {database}\n**Owner:** {owner}\n**Dataset:** {dataset}\n**Geometry Type:** {geom}""".format(
            metadata="Metadata goes here",
            database=self.database,
            owner=self.owner,
            dataset=self.dataset,
            geom=self.geometry_type())

        if self.record_count() > 0:
            description += """\n**Number of Records:** {count}""".format(count=self.record_count())
        if self.services_list:
            description += """\n**Appears in the following services:**\n\n"""
            for s in self.services_list:
                description += """- {}\n""".format(s)
        if self.ez_list:
            description += """\n**Appears in the following EZ Layers:**\n\n"""
            for e in self.ez_list:
                description += """- {}\n""".format(e)

        return description

    def load_labels(self, label_defs: dict) -> list:
        """Returns a list of label ids to be used for each Feature Class card"""
        event_layer_keywords = ['INSPECTION', 'REPAIR', 'MAINT', "EVENT"]
        boolean_labels = {
            'green': True if any(arg in self.unique_name for arg in event_layer_keywords) else False,
            'orange': self.has_attachments(),
            'red': True if self.services_list else False,
            'purple': self.has_no_records(),
            'blue': True if self.dataset else False,
            'black': True if self.ez_list else False
        }
        colors_to_apply = [k for k, v in boolean_labels.items() if v]

        if len(colors_to_apply) > 0:
            label_ids = [k for k, v in label_defs.items() if any(arg == v["color"] for arg in colors_to_apply)]
            return label_ids
        else:
            return list()

    def post_card(self, trello_lists: dict, label_defs: dict):
        url = "https://api.trello.com/1/cards"
        query = {"idList": trello_lists[self.database],
                 "idLabels": self.load_labels(label_defs),
                 "key": self.key,
                 "token": self.token,
                 "pos": "top",
                 "name": self.tuple_path[-1],
                 "desc": self.load_description()}
        response = request("POST", url, params=query)
        return response.status_code

    def apply_checklists(self, checklist_defs: dict) -> list:
        event_layer_keywords = ['INSPECTION', 'REPAIR', 'MAINT']
        event = True if any(arg in self.unique_name for arg in event_layer_keywords) else False
        # TODO: write control flow for dealing with Beehive checklist
        # TODO: write a loop that posts checklists to each new card
