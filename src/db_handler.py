import sys, os, subprocess

from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa

from tkinter import StringVar, IntVar

try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = os.path.abspath('/etc/CYBERPATRIOT/')
    passExist = True
    if not os.path.exists(base_path):
        os.makedirs(base_path)
except Exception:
    base_path = os.path.abspath('/etc/CYBERPATRIOT/')
    passExist = False
db = os.path.join(base_path, 'save_data.db')

base = declarative_base()
engine = sa.create_engine('sqlite:///' + db)
base.metadata.bind = engine
session = orm.scoped_session(orm.sessionmaker())(bind=engine)


class SettingsModel(base):
    __tablename__ = "Settings"
    id = sa.Column(sa.Integer, primary_key=True)
    style = sa.Column(sa.String(128), nullable=False, default="black")
    desktop = sa.Column(sa.Text, nullable=False, default=" ")
    silent_mode = sa.Column(sa.Boolean, nullable=False, default=False)
    server_mode = sa.Column(sa.Boolean, nullable=False, default=False)
    server_name = sa.Column(sa.String(255))
    server_user = sa.Column(sa.String(255))
    server_pass = sa.Column(sa.String(128))
    tally_points = sa.Column(sa.Integer, nullable=False, default=0)
    tally_vuln = sa.Column(sa.Integer, nullable=False, default=0)
    current_points = sa.Column(sa.Integer, nullable=False, default=0)
    current_vuln = sa.Column(sa.Integer, nullable=False, default=0)

    def __init__(self, **kwargs):
        super(SettingsModel, self).__init__(**kwargs)


class Settings:
    def __init__(self):
            if session.query(SettingsModel).scalar() is None:
                self.settings = SettingsModel()
                session.add(self.settings)
                session.commit()
            else:
                self.settings = session.query(SettingsModel).one()

    def get_settings(self, config=True):
        if config:
            return {"Style": StringVar(value=self.settings.style), "Desktop": StringVar(value=self.settings.desktop), "Silent Mode": StringVar(value=self.settings.silent_mode), "Server Mode": StringVar(value=self.settings.server_mode), "Server Name": StringVar(value=self.settings.server_name), "Server User": StringVar(value=self.settings.server_user), "Server Password": StringVar(value=self.settings.server_pass), "Tally Points": StringVar(value=self.settings.tally_points), "Tally Vulnerabilities": StringVar(value=self.settings.tally_vuln)}
        else:
            return {"Desktop": self.settings.desktop, "Silent Mode": self.settings.silent_mode, "Server Mode": self.settings.server_mode, "Server Name": self.settings.server_name, "Server User": self.settings.server_user, "Server Password": self.settings.server_pass, "Tally Points": self.settings.tally_points, "Tally Vulnerabilities": self.settings.tally_vuln, "Current Points": self.settings.current_points, "Current Vulnerabilities": self.settings.current_vuln}

    def update_table(self, entry):
        self.settings.style = entry["Style"].get()
        self.settings.desktop = entry["Desktop"].get()
        self.settings.silent_mode = (True if int(entry["Silent Mode"].get()) == 1 else False)
        self.settings.server_mode = (True if int(entry["Server Mode"].get()) == 1 else False)
        self.settings.server_name = entry["Server Name"].get()
        self.settings.server_user = entry["Server User"].get()
        self.settings.server_pass = entry["Server Password"].get()
        self.settings.tally_points = entry["Tally Points"].get()
        self.settings.tally_vuln = entry["Tally Vulnerabilities"].get()
        session.commit()

    def update_score(self, entry):
        self.settings.current_points = entry["Current Points"]
        self.settings.current_vuln = entry["Current Vulnerabilities"]

class CategoryModels(base):
    __tablename__ = "Vulnerability Categories"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(128), nullable=False, unique=True)
    description = sa.Column(sa.Text, nullable=False)

    def __init__(self, **kwargs):
        super(CategoryModels, self).__init__(**kwargs)


class Categories:
    categories = {
        "Account Management": "This section is for scoring user policies. The options that will take multiple test points can be setup by clicking the `Modify` button. Once the `Modify` button is clicked that option will automatically be enabled. Make sure the option is enabled and the points are set for the options you want scored.",
        "Local Policy": "This section is for scoring Local Security Policies. Each option has a defined range that they be testing listed in their description. Make sure the option is enabled and the points are set for the options you want scored.",
        "Program Management": "This section is for scoring program manipulation. The options that will take multiple test points can be setup by clicking the `Modify` button. Once the `Modify` button is clicked that option will automatically be enabled. Make sure the option is enabled and the points are set for the options you want scored.",
        "File Management": "This section is for scoring file manipulation. The options that will take multiple test points can be setup by clicking the `Modify` button. Once the `Modify` button is clicked that option will automatically be enabled. Make sure the option is enabled and the points are set for the options you want scored.",
        "Firewall Management": "This section is for scoring Firewalls and ports. The options that will take multiple test points can be setup by clicking the `Modify` button. Once the `Modify` button is clicked that option will automatically be enabled. Make sure the option is enabled and the points are set for the options you want scored."
    }

    def __init__(self):
        loaded_categories = []
        for cat in session.query(CategoryModels):
            loaded_categories.append(cat.name)
        for cat in self.categories:
            if cat not in loaded_categories:
                name = cat
                description = self.categories[cat]
                category = CategoryModels(name=name, description=description)
                session.add(category)
        session.commit()

    def get_categories(self):
        return session.query(CategoryModels)


class VulnerabilityTemplateModel(base):
    __tablename__ = "Vulnerability Template"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(128), nullable=False, unique=True)
    category = sa.Column(sa.Integer, sa.ForeignKey("Vulnerability Categories.id"))
    definition = sa.Column(sa.Text, nullable=False)
    description = sa.Column(sa.Text)
    checks = sa.Column(sa.Text)

    def __init__(self, **kwargs):
        super(VulnerabilityTemplateModel, self).__init__(**kwargs)


base.metadata.create_all(engine)


class OptionTables:
    models = {}
    checks_list = {}

    def __init__(self, vulnerability_templates=None):
        loaded_vulns_templates = []
        for vuln_templates in session.query(VulnerabilityTemplateModel):
            loaded_vulns_templates.append(vuln_templates.name)
        if vulnerability_templates != None:
            for name in vulnerability_templates:
                if name not in loaded_vulns_templates:
                    category = session.query(CategoryModels).filter_by(name=vulnerability_templates[name]["Category"]).one().id
                    definition = vulnerability_templates[name]["Definition"]
                    description = vulnerability_templates[name]["Description"] if "Description" in vulnerability_templates[name] else None
                    checks = vulnerability_templates[name]["Checks"] if "Checks" in vulnerability_templates[name] else None
                    vuln_template = VulnerabilityTemplateModel(name=name, category=category, definition=definition, description=description, checks=checks)
                    session.add(vuln_template)
        session.commit()

    def initialize_option_table(self):
        for vuln_template in session.query(VulnerabilityTemplateModel):
            name = vuln_template.name
            checks_list = vuln_template.checks.split(',') if vuln_template.checks is not None else []
            checks_dict = {}
            self.checks_list.update({name: {}})
            for checks in checks_list:
                chk = checks.split(':')
                checks_dict.update({chk[0]: chk[1]})
                self.checks_list[name].update({chk[0]: chk[0]})
            create_option_table(name, checks_dict, self.models)
        base.metadata.create_all(engine)

        for name in self.models:
            try:
                if session.query(self.models[name]).scalar() is None:
                    vuln_base = self.models[name]()
                    session.add(vuln_base)
            except:
                pass
        session.commit()

    def get_option_template(self, vulnerability):
        return session.query(VulnerabilityTemplateModel).filter_by(name=vulnerability).one()

    def get_option_template_by_category(self, category):
        return session.query(VulnerabilityTemplateModel).filter_by(category=category)

    def get_option_table(self, vulnerability, config=True):
        vuln_dict = {}
        for vuln in session.query(self.models[vulnerability]):
            if config:
                vuln_dict.update({vuln.id: {"Enabled": IntVar(value=vuln.Enabled), "Points": IntVar(value=vuln.Points), "Checks": {}}})
                for checks in vars(vuln):
                    if not checks.startswith("_") and checks != "id" and checks != "Enabled" and checks != "Points":
                        if type(vars(vuln)[checks]) == int or type(vars(vuln)[checks]) == bool:
                            vuln_dict[vuln.id]["Checks"].update({checks: IntVar(value=vars(vuln)[checks])})
                        else:
                            vuln_dict[vuln.id]["Checks"].update({checks: StringVar(value=vars(vuln)[checks])})
            else:
                vuln_dict.update({vuln.id: {"Enabled": vuln.Enabled, "Points": vuln.Points}})
                for checks in vars(vuln):
                    if not checks.startswith("_") and checks != "id" and checks != "Enabled" and checks != "Points":
                        vuln_dict[vuln.id].update({checks: vars(vuln)[checks]})
        return vuln_dict

    def add_to_table(self, vulnerability, **kwargs):
        vuln = self.models[vulnerability](**kwargs)
        session.add(vuln)
        session.commit()
        return vuln

    def update_table(self, vulnerability, entry):
        for vuln in session.query(self.models[vulnerability]):
            vuln_update = {"Enabled": (True if int(entry[vuln.id]["Enabled"].get()) == 1 else False), "Points": entry[vuln.id]["Points"].get()}
            for checks in vars(vuln):
                if not checks.startswith("_") and checks != "id" and checks != "Enabled" and checks != "Points":
                    vuln_update.update({checks: entry[vuln.id]["Checks"][checks].get()})
            session.query(self.models[vulnerability]).filter_by(id=vuln.id).update(vuln_update)
            session.commit()

    def remove_from_table(self, vulnerability, vuln_id):
        vuln = session.query(self.models[vulnerability]).filter_by(id=vuln_id).one()
        session.delete(vuln)
        session.commit()

    def cleanup(self):
        session.flush()


def create_option_table(name, option_categories, option_models):
    attr_dict = {'__tablename__': name,
                 'id': sa.Column(sa.Integer, primary_key=True),
                 'Enabled': sa.Column(sa.Boolean, nullable=False, default=False),
                 'Points': sa.Column(sa.Integer, nullable=False, default=0)}
    for cat in option_categories:
        if option_categories[cat] == "Int":
            attr_dict.update({cat: sa.Column(sa.Integer, default=0)})
        elif option_categories[cat] == "Str":
            attr_dict.update({cat: sa.Column(sa.Text, default="")})

    option_models.update({name: type(name, (base,), attr_dict)})

