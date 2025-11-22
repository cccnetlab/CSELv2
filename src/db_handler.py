#!/usr/bin/env python3

"""
Database handler for CyberPatriot application. Handles settings, categories, vulnerability templates, 
and option tables using SQLAlchemy ORM to give configurator configs peristence.
"""

import sys, os, subprocess

from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa

from tkinter import StringVar, IntVar

# Ensure the config directory exists
try:
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = os.path.abspath("/etc/CYBERPATRIOT/")
    passExist = True
    if not os.path.exists(base_path):
        os.makedirs(base_path)
except Exception:
    base_path = os.path.abspath("/etc/CYBERPATRIOT/")
    passExist = False
db = os.path.join(base_path, "save_data.db")

base = declarative_base()
engine = sa.create_engine("sqlite:///" + db, 
                         pool_timeout=20, 
                         pool_recycle=-1,
                         connect_args={'timeout': 20})
base.metadata.bind = engine
Session = orm.scoped_session(orm.sessionmaker(bind=engine))

def get_session():
    """Get a new database session"""
    return Session()

def close_session(session):
    """Properly close a database session"""
    try:
        session.close()
    except Exception:
        pass


class SettingsModel(base):
    """
    SQLAlchemy ORM model for storing application settings.
    Stores style, desktop path, silent/server mode, server credentials, and scoring tallies.
    """
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
    """
    Handles retrieval and updating of application settings using the SettingsModel.
    Provides methods to get settings as Tkinter variables or plain values, and to update settings.
    """
    def __init__(self):
        """
        Initializes the Settings object, loading from the database or creating a new entry if none exists.
        """
        session = get_session()
        try:
            base.metadata.create_all(engine)
            if session.query(SettingsModel).scalar() is None:
                self.settings = SettingsModel()
                session.add(self.settings)
                session.commit()
            else:
                self.settings = session.query(SettingsModel).one()
        finally:
            close_session(session)

    def get_settings(self, config=True):
        """
        Returns settings as a dictionary.
        If config=True, returns Tkinter variable wrappers for GUI binding.
        Otherwise, returns plain values for backend use.
        """
        if config:
            return {
                "Style": StringVar(value=self.settings.style),
                "Desktop": StringVar(value=self.settings.desktop),
                "Silent Mode": StringVar(value=self.settings.silent_mode),
                "Server Mode": StringVar(value=self.settings.server_mode),
                "Server Name": StringVar(value=self.settings.server_name),
                "Server User": StringVar(value=self.settings.server_user),
                "Server Password": StringVar(value=self.settings.server_pass),
                "Tally Points": StringVar(value=self.settings.tally_points),
                "Tally Vulnerabilities": StringVar(value=self.settings.tally_vuln),
            }
        else:
            return {
                "Desktop": self.settings.desktop,
                "Silent Mode": self.settings.silent_mode,
                "Server Mode": self.settings.server_mode,
                "Server Name": self.settings.server_name,
                "Server User": self.settings.server_user,
                "Server Password": self.settings.server_pass,
                "Tally Points": self.settings.tally_points,
                "Tally Vulnerabilities": self.settings.tally_vuln,
                "Current Points": self.settings.current_points,
                "Current Vulnerabilities": self.settings.current_vuln,
            }

    def update_table(self, entry):
        """
        Updates the settings table in the database with values from the provided entry dictionary.
        Commits changes to the database.
        """
        session = get_session()
        try:
            # Query the settings record within the current session
            settings = session.query(SettingsModel).first()
            if settings:
                # Update all fields
                settings.style = entry["Style"].get()
                settings.desktop = entry["Desktop"].get()
                settings.silent_mode = (
                    True if int(entry["Silent Mode"].get()) == 1 else False
                )
                settings.server_mode = (
                    True if int(entry["Server Mode"].get()) == 1 else False
                )
                settings.server_name = entry["Server Name"].get()
                settings.server_user = entry["Server User"].get()
                settings.server_pass = entry["Server Password"].get()
                settings.tally_points = entry["Tally Points"].get()
                settings.tally_vuln = entry["Tally Vulnerabilities"].get()
                
                # Commit the changes
                session.commit()
                
                # Update the in-memory object to reflect the changes
                self.settings.style = settings.style
                self.settings.desktop = settings.desktop
                self.settings.silent_mode = settings.silent_mode
                self.settings.server_mode = settings.server_mode
                self.settings.server_name = settings.server_name
                self.settings.server_user = settings.server_user
                self.settings.server_pass = settings.server_pass
                self.settings.tally_points = settings.tally_points
                self.settings.tally_vuln = settings.tally_vuln
        finally:
            close_session(session)

    def update_score(self, entry):
        """
        Updates the current score and vulnerability count in the settings table.
        """
        session = get_session()
        try:
            # Query the settings record within the current session
            settings = session.query(SettingsModel).first()
            if settings:
                settings.current_points = entry["Current Points"]
                settings.current_vuln = entry["Current Vulnerabilities"]
                session.commit()
                
                # Update in-memory object
                self.settings.current_points = settings.current_points
                self.settings.current_vuln = settings.current_vuln
        finally:
            close_session(session)


class CategoryModels(base):
    """
    SQLAlchemy ORM model for vulnerability categories.
    Stores category name and description.
    """
    __tablename__ = "Vulnerability Categories"
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String(128), nullable=False, unique=True)
    description = sa.Column(sa.Text, nullable=False)

    def __init__(self, **kwargs):
        super(CategoryModels, self).__init__(**kwargs)


class Categories:
    """
    Handles loading and retrieval of vulnerability categories.
    Ensures default categories are present in the database and provides access to all categories.
    """
    categories = {
        "Account Management": "This section is for scoring user policies. The options that will take multiple test points can be setup by clicking the `Modify` button. Once the `Modify` button is clicked that option will automatically be enabled. Make sure the option is enabled and the points are set for the options you want scored.",
        "Local Policy": "This section is for scoring Local Security Policies. Each option has a defined range that they be testing listed in their description. Make sure the option is enabled and the points are set for the options you want scored.",
        "Program Management": "This section is for scoring program manipulation. The options that will take multiple test points can be setup by clicking the `Modify` button. Once the `Modify` button is clicked that option will automatically be enabled. Make sure the option is enabled and the points are set for the options you want scored.",
        "File Management": "This section is for scoring file manipulation. The options that will take multiple test points can be setup by clicking the `Modify` button. Once the `Modify` button is clicked that option will automatically be enabled. Make sure the option is enabled and the points are set for the options you want scored.",
        "Firewall Management": "This section is for scoring Firewalls and ports. The options that will take multiple test points can be setup by clicking the `Modify` button. Once the `Modify` button is clicked that option will automatically be enabled. Make sure the option is enabled and the points are set for the options you want scored.",
    }

    def __init__(self):
        """
        Initializes Categories, loading existing categories and adding defaults if missing.
        """
        session = get_session()
        try:
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
        finally:
            close_session(session)

    def get_categories(self):
        """
        Returns a SQLAlchemy query for all category models.
        """
        session = get_session()
        try:
            return session.query(CategoryModels).all()
        finally:
            close_session(session)


class VulnerabilityTemplateModel(base):
    """
    SQLAlchemy ORM model for vulnerability templates.
    Stores template name, category, definition, description, and checks.
    """
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
    """
    Manages dynamic option tables for vulnerabilities.
    Handles creation, retrieval, updating, and deletion of vulnerability options and their checks.
    """
    models = {}
    checks_list = {}

    def __init__(self, vulnerability_templates=None):
        """
        Initializes option tables for provided vulnerability templates.
        Adds new templates to the database if they do not exist.
        """
        session = get_session()
        try:
            loaded_vulns_templates = []
            for vuln_templates in session.query(VulnerabilityTemplateModel):
                loaded_vulns_templates.append(vuln_templates.name)
            if vulnerability_templates != None:
                for name in vulnerability_templates:
                    if name not in loaded_vulns_templates:
                        category = (
                            session.query(CategoryModels)
                            .filter_by(name=vulnerability_templates[name]["Category"])
                            .one()
                            .id
                        )
                        definition = vulnerability_templates[name]["Definition"]
                        description = (
                            vulnerability_templates[name]["Description"]
                            if "Description" in vulnerability_templates[name]
                            else None
                        )
                        checks = (
                            vulnerability_templates[name]["Checks"]
                            if "Checks" in vulnerability_templates[name]
                            else None
                        )
                        vuln_template = VulnerabilityTemplateModel(
                            name=name,
                            category=category,
                            definition=definition,
                            description=description,
                            checks=checks,
                        )
                        session.add(vuln_template)
            session.commit()
        finally:
            close_session(session)

    def initialize_option_table(self):
        """
        Initializes option tables for all vulnerability templates.
        Dynamically creates SQLAlchemy models and ensures database entries exist.
        """
        session = get_session()
        try:
            for vuln_template in session.query(VulnerabilityTemplateModel):
                name = vuln_template.name
                checks_list = (
                    vuln_template.checks.split(",")
                    if vuln_template.checks is not None
                    else []
                )
                checks_dict = {}
                self.checks_list.update({name: {}})
                for checks in checks_list:
                    chk = checks.split(":")
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
        finally:
            close_session(session)

    def get_option_template(self, vulnerability):
        """
        Retrieves a vulnerability template by name.
        """
        session = get_session()
        try:
            return (
                session.query(VulnerabilityTemplateModel)
                .filter_by(name=vulnerability)
                .one()
            )
        finally:
            close_session(session)

    def get_option_template_by_category(self, category):
        """
        Retrieves vulnerability templates by category ID.
        """
        session = get_session()
        try:
            return session.query(VulnerabilityTemplateModel).filter_by(category=category).all()
        finally:
            close_session(session)

    def get_option_table(self, vulnerability, config=True):
        """
        Retrieves option table entries for a vulnerability.
        Returns Tkinter variable wrappers if config=True, otherwise plain values.
        """
        session = get_session()
        try:
            vuln_dict = {}
            for vuln in session.query(self.models[vulnerability]):
                if config:
                    vuln_dict.update(
                        {
                            vuln.id: {
                                "Enabled": IntVar(value=vuln.Enabled),
                                "Points": IntVar(value=vuln.Points),
                                "Checks": {},
                            }
                        }
                    )
                    for checks in vars(vuln):
                        if (
                            not checks.startswith("_")
                            and checks != "id"
                            and checks != "Enabled"
                            and checks != "Points"
                        ):
                            if (
                                type(vars(vuln)[checks]) == int
                                or type(vars(vuln)[checks]) == bool
                            ):
                                vuln_dict[vuln.id]["Checks"].update(
                                    {checks: IntVar(value=vars(vuln)[checks])}
                                )
                            else:
                                vuln_dict[vuln.id]["Checks"].update(
                                    {checks: StringVar(value=vars(vuln)[checks])}
                                )
                else:
                    vuln_dict.update(
                        {vuln.id: {"Enabled": vuln.Enabled, "Points": vuln.Points}}
                    )
                    for checks in vars(vuln):
                        if (
                            not checks.startswith("_")
                            and checks != "id"
                            and checks != "Enabled"
                            and checks != "Points"
                        ):
                            vuln_dict[vuln.id].update({checks: vars(vuln)[checks]})
            return vuln_dict
        finally:
            close_session(session)

    def add_to_table(self, vulnerability, **kwargs):
        """
        Adds a new entry to the option table for the specified vulnerability.
        Commits the new entry to the database.
        Returns the ID of the new entry.
        """
        session = get_session()
        try:
            vuln = self.models[vulnerability](**kwargs)
            session.add(vuln)
            session.commit()
            # Return the ID instead of the object to avoid DetachedInstanceError
            return vuln.id
        finally:
            close_session(session)

    def update_table(self, vulnerability, entry):
        """
        Updates entries in the option table for the specified vulnerability using the provided entry dictionary.
        Commits changes to the database.
        """
        session = get_session()
        try:
            for vuln in session.query(self.models[vulnerability]):
                vuln_update = {
                    "Enabled": (
                        True if int(entry[vuln.id]["Enabled"].get()) == 1 else False
                    ),
                    "Points": entry[vuln.id]["Points"].get(),
                }
                for checks in vars(vuln):
                    if (
                        not checks.startswith("_")
                        and checks != "id"
                        and checks != "Enabled"
                        and checks != "Points"
                    ):
                        vuln_update.update({checks: entry[vuln.id]["Checks"][checks].get()})
                session.query(self.models[vulnerability]).filter_by(id=vuln.id).update(
                    vuln_update
                )
                session.commit()
        finally:
            close_session(session)

    def remove_from_table(self, vulnerability, vuln_id):
        """
        Removes an entry from the option table for the specified vulnerability by ID.
        Commits the deletion to the database.
        """
        session = get_session()
        try:
            vuln = session.query(self.models[vulnerability]).filter_by(id=vuln_id).one()
            session.delete(vuln)
            session.commit()
        finally:
            close_session(session)

    def cleanup(self):
        """
        Flushes the current session (useful for cleanup operations).
        """
        session = get_session()
        try:
            session.flush()
        finally:
            close_session(session)


def create_option_table(name, option_categories, option_models):
    """
    Dynamically creates a SQLAlchemy ORM model for a vulnerability option table.
    Adds columns based on provided option categories and types.
    Updates the option_models dictionary with the new model.
    """
    attr_dict = {
        "__tablename__": name,
        "id": sa.Column(sa.Integer, primary_key=True),
        "Enabled": sa.Column(sa.Boolean, nullable=False, default=False),
        "Points": sa.Column(sa.Integer, nullable=False, default=0),
    }
    for cat in option_categories:
        if option_categories[cat] == "Int":
            attr_dict.update({cat: sa.Column(sa.Integer, default=0)})
        elif option_categories[cat] == "Str":
            attr_dict.update({cat: sa.Column(sa.Text, default="")})

    option_models.update({name: type(name, (base,), attr_dict)})
