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
                # If everything fails, Write unknown
                return "Unknown"

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
    def __init__(self, short_link, key, token):
        self.short_link = short_link
        self.key = key
        self.token = token
        self.info = self.get_info()
        self.lists = {i["name"]: i["id"] for i in self.info["lists"]}
        self.labels = self.info["labels"]
        self.checklists = self.info["checklists"]

    def get_info(self):
        url = "https://api.trello.com/1/boards/{id}".format(id=self.short_link)
        query = {"fields": ["id", "name"],
                 "labels": "all",
                 "lists": "open",
                 "checklists": "all",
                 "key": self.key,
                 "token": self.token
                 }
        resp = request("GET", url, params=query)
        return resp.json()


class TrelloCard(TrelloFeatureClass):
    def __init__(self, tuple_path, key, token, label_dict, checklist_dict, service_dict, ez_dict):
        super().__init__(tuple_path)
        self.key = key
        self.token = token
        self.label_dict = label_dict
        self.checklist_dict = checklist_dict
        self.label_ids = self.load_labels()
        self.priority = len(self.label_ids)
        self.in_services = service_dict[self.unique_name]if self.unique_name in service_dict else None
        self.in_ez_layers = ez_dict[self.unique_name] if self.unique_name in ez_dict else None

    def load_description(self):
        """Gives a custom formatted description to use inside of a Feature Class's Trello Card"""
        description = """**SME:** (write down who the SME is here, if applicable)\n**Database:** {database}\n**Owner:** {owner}\n**Dataset:** {dataset}\n**Geometry Type:** {geom}\n**Registered as Versioned:** {versioned}""".format(
            database=self.database,
            owner=self.owner,
            dataset=self.dataset,
            geom=self.geometry_type(),
            versioned=self.isVersioned)

        if isinstance(self.record_count(), str) or self.record_count() > 0:
            description += """\n**Number of Records:** {count}""".format(count=self.record_count())
        if self.in_services:
            description += """\n**Appears in the following services:**\n\n"""
            for s in self.in_services:
                description += """- {}\n""".format(s)
        if self.in_ez_layers:
            description += """\n**Appears in the following EZ Layers:**\n\n"""
            for e in self.in_ez_layers:
                description += """- {}\n""".format(e)

        return description

    def load_labels(self) -> list:
        """Returns a list of label ids to be used for each Feature Class card"""
        boolean_labels = {
            'green': self.is_event(),
            'orange': self.attachments_enabled(),
            'red': True if self.in_services else False,
            'purple': self.has_no_records(),
            'blue': True if self.dataset else False,
            'black': True if self.in_ez_layers else False
        }
        colors_to_apply = [k for k, v in boolean_labels.items() if v]

        if len(colors_to_apply) > 0:
            label_ids = [d["id"] for d in self.label_dict if any(arg == d["color"] for arg in colors_to_apply)]
            return label_ids
        else:
            return list()

    def post_card(self, trello_lists: dict,):
        url = "https://api.trello.com/1/cards"
        query = {"idList": trello_lists[self.database],
                 "idLabels": self.label_ids,
                 "key": self.key,
                 "token": self.token,
                 "pos": "bottom",
                 "name": self.tuple_path[-1],
                 "desc": self.load_description()}
        response = request("POST", url, params=query)

        card_id = response.json()["id"]
        self.apply_checklists(card_id)

    def apply_checklists(self, in_card_id):
        """Applies checklists to a card. If the card is not an event layer, or has no records, 
        the function will not add checklists for tasks associated with feature classes that 
        have those properties. Used by default in the post_card method."""
        checklists = {check["id"]: check["name"].replace("TEMPLATE ", "") for check in self.checklist_dict if
                      "TEMPLATE" in check["name"]}
        # remove checklists with the following keys if their associated tests prove true
        remove = {"BEEHIVE": not self.is_event(), "CONVERSION": self.has_no_records()}
        for key, value in remove.items():
            if value:
                checklists = {k: v for k, v in checklists.items() if key not in v}

        url = "https://api.trello.com/1/cards/{id}/checklists".format(id=in_card_id)
        for k, v in checklists.items():
            query = {"idChecklistSource": k,
                     "name": v,
                     "key": self.key,
                     "token": self.token,
                     "pos": "bottom"}
            response = request("POST", url, params=query)
