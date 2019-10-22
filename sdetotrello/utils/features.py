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

    def is_event(self) -> bool:
        event_layer_keywords = ['INSPECT', 'REPAIR', 'MAINT', "EVENT", "BREAK", "INCIDENT"]
        return any(arg in self.unique_name for arg in event_layer_keywords)

    def record_count(self):
        """Returns the number of records within a table by executing a SQL query in the database"""
        execute_object = ArcSDESQLExecute(self.connection)
        try:
            query_name = ".".join([self.owner, self.name[:26]])
            query = """SELECT COUNT(*) FROM {}_EVW""".format(query_name.upper())
            result = execute_object.execute(query)
            return int(result)
        except (ExecuteError, TypeError, AttributeError):
            try:
                query_name = ".".join([self.owner, self.name[:30]])
                query = """SELECT COUNT(*) FROM {}""".format(query_name.upper())
                result = execute_object.execute(query)
                return int(result)
            except (ExecuteError, TypeError, AttributeError):
                # If everything fails, assume the layer has records
                return 1

    def has_no_records(self) -> bool:
        """Returns true if the table in question has no records"""
        return True if self.record_count() == 0 else False

    def attachments_enabled(self) -> bool:
        suffix = "__ATTACH"
        attachment_table_name = self.name + suffix

        if len(attachment_table_name) > 30:
            attachment_table_name = attachment_table_name[:30]
        exist_path = path.join(self.connection, ".".join([self.owner, attachment_table_name]))

        return Exists(exist_path)

    def geometry_type(self):
        """Describes the feature class rather than the workspace and return the shape type"""
        try:
            if self.dataType == 'FeatureClass':
                return self.shapeType
            else:
                return None
        except (ExecuteError, OSError):
            return None

class TrelloBoard:
    def __init__(self, board_id, url_board_id):
        self.board_id = board_id
        self.url_board_id = url_board_id

    def get_lists(self):
        url = "https://api.trello.com/1/boards/{}/lists".format(self.url_board_id)
        query = {"cards": "none",
                 "filter": "all",
                 "fields": ["id", "name"]}

        resp = request("GET", url, params=query)
        json_resp = json.loads(resp.text)



class TrelloCard(TrelloFeatureClass):
    def __init__(self, obj, board, key, token, service_dict, ez_dict):
        super().__init__(obj.tuple_path)
        self.board = board
        self.key = key
        self.token = token
        self.services_list = service_dict[self.unique_name]if self.unique_name in service_dict else None
        self.ez_list = ez_dict[self.unique_name] if self.unique_name in ez_dict else None

    def get_priority(self, label_defs: dict):
        return len(self.load_labels(label_defs))

    def load_description(self):
        """Gives a custom formatted description to use inside of a Feature Class's Trello Card"""
        description = """{metadata}\n\n**SME:** (write down who the SME is here, if applicable)\n**Database:** {database}\n**Owner:** {owner}\n**Dataset:** {dataset}\n**Geometry Type:** {geom}\n**Registered as Versioned:** {versioned}""".format(
            metadata="Metadata goes here",
            database=self.database,
            owner=self.owner,
            dataset=self.dataset,
            geom=self.geometry_type(),
            versioned=self.isVersioned)

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
        boolean_labels = {
            'green': self.is_event(),
            'orange': self.attachments_enabled(),
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
                 "pos": "bottom",
                 "name": self.tuple_path[-1],
                 "desc": self.load_description()}
        response = request("POST", url, params=query)
        return response.status_code

    def apply_checklists(self, checklist_defs: dict) -> list:

        # TODO: write control flow for dealing with Beehive checklist
        # TODO: write a loop that posts checklists to each new card
