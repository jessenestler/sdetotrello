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

    def extract_template_checklists(self, board_id, card_id, key, token):
        # TODO: add code that returns checklist names and ids to copy
        pass

    def define_description(self):
        """Gives a custom formatted description to use inside of a Feature Class's Trello Card"""
        description = """{metadata}

        **SME:** (write down who the SME is here, if applicable)
        **Database:** {database}
        **Owner:** {owner}
        **Dataset:** {dataset}
        **Geometry Type:** {geom}""".format(metadata="This is an item",
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

    def define_labels(self, all_items, label_dict):
        """Returns a list of label ids to be used for each Feature Class card"""
        event_layer_keywords = ['INSPECTION', 'REPAIR', 'MAINT']
        boolean_labels = {
            'green': True if any(arg in self.unique_name for arg in event_layer_keywords) else False,
            'orange': True if sum(1 for x in all_items if self.name in x.name) > 1 else False,
            'red': True if self.services_list else False,
            'purple': self.has_no_records(),
            'blue': True if self.dataset else False,
            'black': True if self.ez_list else False
        }
        # TODO: add code that will return the label ids rather than the color

    def define_checklists(self, checklist_dict):
        # TODO: add code that return a list of checklist ids to copy onto the new card
        pass
