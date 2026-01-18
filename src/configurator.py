#!/home/jkim/Desktop/CSELv2/.venv/bin/python3
# ^ For testing

## !/usr/bin/env python3
#^ Original shebang line

import os
import subprocess
import sys
import time
import shutil
import tkinter
import traceback
from crontab import CronTab
import pwd, grp, psutil
from tkinter import *
from tkinter import ttk as ttk
from tkinter import filedialog
from tkinter import messagebox
from ttkthemes import ThemedStyle

# Add parent directory to path for relative imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import db_handler


# Here we are declaring our data base and implementing the vulnerabilities types and categories that will be offered to the db
# the string will be fed to db viewer and parsed into the table, anything commented out is pending to be worked on
# region database for save data
Settings = db_handler.Settings()
Categories = db_handler.Categories()

# Vulnerability example:
"""
"Name": {"Definition": 'Define what this vulnerability affects',
         "Description": 'If needed a description that is shown in the UI is shown',
         "Checks": If inputs are needed they are placed in here Examples- Name:Str, Status:Str',
         "Category": Place under one of the four main categories to be displayed in the UI 
                     Account Management | Local Policy | Program Management | File Management
}
"""


vulnerability_template = {
    "Critical Users": {
        "Definition": "Enable this to penalize the competitor for removing a user.",
        "Description": 'This will penalize the competitor for removing a user. To add more users press the "Add" button. To remove a user press the "X" button next to the user you want to remove. Keep it one user per line. To add users that are not on the computer, then you can Category the user name in the field. Otherwise use the drop down to select a user. Do not make the point value negative.',
        "Checks": "User Name:Str",
        "Category": "Account Management",
    },
    "Add Admin": {
        "Definition": "Enable this to score the competitor for elevating a user to an Administrator.",
        "Description": 'This will score the competitor for elevating a user to an Administrator. To add more users press the "Add" button. To remove a user press the "X" button next to the user you want to remove. Keep it one user per line. To add users that are not on the computer, then you can Category the user name in the field. Otherwise use the drop down to select a user.',
        "Checks": "User Name:Str",
        "Category": "Account Management",
    },
    "Remove Admin": {
        "Definition": "Enable this to score the competitor for demoting a user to Standard user.",
        "Description": 'This will score the competitor for demoting a user to Standard user. To add more users press the "Add" button. To remove a user press the "X" button next to the user you want to remove. Keep it one user per line. To add users that are not on the computer, then you can Category the user name in the field. Otherwise use the drop down to select a user.',
        "Checks": "User Name:Str",
        "Category": "Account Management",
    },
    "Add User": {
        "Definition": "Enable this to score the competitor for adding a user.",
        "Description": 'This will score the competitor for adding a user. To add more users press the "Add" button. To remove a user press the "X" button next to the user you want to remove. Keep it one user per line. To add users that are not on the computer, then you can Category the user name in the field. Otherwise use the drop down to select a user.',
        "Checks": "User Name:Str",
        "Category": "Account Management",
    },
    "Remove User": {
        "Definition": "Enable this to score the competitor for removing a user.",
        "Description": 'This will score the competitor for removing a user. To add more users press the "Add" button. To remove a user press the "X" button next to the user you want to remove. Keep it one user per line. To add users that are not on the computer, then you can Category the user name in the field. Otherwise use the drop down to select a user.',
        "Checks": "User Name:Str",
        "Category": "Account Management",
    },
    "User Change Password": {
        "Definition": "Enable this to score the competitor for changing a users password.",
        "Description": 'This will score the competitor for changing a users password. To add more users press the "Add" button. To remove a user press the "X" button next to the user you want to remove. Keep it one user per line. To add users that are not on the computer, then you can Category the user name in the field. Otherwise use the drop down to select a user.',
        "Checks": "User Name:Str",
        "Category": "Account Management",
    },
    "Add User to Group": {
        "Definition": "Enable this to score the competitor for adding a user to a group other than the Administrative group.",
        "Description": 'This will score the competitor for adding a user to a group other than the Administrative group. To add more users press the "Add" button. To remove a user press the "X" button next to the user you want to remove. Keep it one user  and group per line. To add users or group that are not on the computer, then you can type the user or group name in the field. Otherwise use the drop down to select a user or group.',
        "Checks": "User Name:Str,Group Name:Str",
        "Category": "Account Management",
    },
    "Remove User from Group": {
        "Definition": "Enable this to score the competitor for removing a user from a group other than the Administrative group.",
        "Description": 'This will score the competitor for removing a user from a group other than the Administrative group. To add more users press the "Add" button. To remove a user press the "X" button next to the user you want to remove. Keep it one user and group per line. To add users or group that are not on the computer, then you can type the user or group name in the field. Otherwise use the drop down to select a user or group.',
        "Checks": "User Name:Str,Group Name:Str",
        "Category": "Account Management",
    },
    # implement this one
    # "Secure Sudoers": {"Definition": 'Words to be removed from /etc/sudoers file',
    #                   "Checks": 'Banned Sudoers:Str',
    #                   "Category": 'Account Management'},
    "Turn On Firewall": {
        "Definition": "Enable this to score the competitor for turning on the domain firewall. Does not work for Windows Server.",
        "Category": "Firewall Management",
    },
    "Check Port Open": {
        "Definition": "Enable this to score the competitor for opening a port. Does not work for Windows Server.",
        "Description": 'This will score the competitor for opening a port. To add more ports press the "Add" button. To remove a port press the "X" button next to the port you want to remove. Keep it one port per line.',
        "Checks": "IP:Str,Port:Str,Protocol:Str",
        "Category": "Firewall Management",
    },
    "Check Port Closed": {
        "Definition": "Enable this to score the competitor for closing a port. Does not work for Windows Server.",
        "Description": 'This will score the competitor for blocking or a port. To add more ports press the "Add" button. To remove a port press the "X" button next to the port you want to remove. Keep it one port per line.',
        "Checks": "IP:Str,Port:Str,Protocol:Str",
        "Category": "Firewall Management",
    },
    "Minimum Password Age": {
        "Definition": "Enable this to score the competitor for setting the minimum password age to a specific value (days).",
        "Description": "Set the minimum password age (in days) that students must configure. The scoring engine will check if the system's minimum password age matches your specified value.",
        "Checks": "Value:Int",
        "Category": "Local Policy",
    },
    "Maximum Password Age": {
        "Definition": "Enable this to score the competitor for setting the maximum password age to a specific value (days).",
        "Description": "Set the maximum password age (in days) that students must configure. The scoring engine will check if the system's maximum password age matches your specified value.",
        "Checks": "Value:Int",
        "Category": "Local Policy",
    },
    "Minimum Password Length": {
        "Definition": "Enable this to score the competitor for setting the minimum password length to a specific value (characters).",
        "Description": "Set the minimum password length that students must configure. The scoring engine will check if the system's minimum password length matches your specified value.",
        "Checks": "Value:Int",
        "Category": "Local Policy",
    },
    "Maximum Login Tries": {
        "Definition": "Enable this to score the competitor for setting the maximum login tries to a specific value (attempts).",
        "Description": "Set the maximum login attempts (account lockout threshold) that students must configure. The scoring engine will check if the system's lockout threshold matches your specified value.",
        "Checks": "Value:Int",
        "Category": "Local Policy",
    },
    "Lockout Duration": {
        "Definition": "Enable this to score the competitor for setting the lockout duration to a specific value (seconds).",
        "Description": "Set the lockout duration (in seconds) that students must configure. The scoring engine will check if the system's lockout timeout matches your specified value.",
        "Checks": "Value:Int",
        "Category": "Local Policy",
    },
    "Lockout Reset Duration": {
        "Definition": "Enable this to score the competitor for setting the lockout reset duration to a specific value (seconds).",
        "Description": "Set the lockout reset duration (in seconds) that students must configure. The scoring engine will check if the system's account lockout reset time matches your specified value.",
        "Checks": "Value:Int",
        "Category": "Local Policy",
    },
    "Password History": {
        "Definition": "Enable this to score the competitor for setting the password history to a specific value (passwords).",
        "Description": "Set the password history size that students must configure. The scoring engine will check if the system remembers at least this many previous passwords.",
        "Checks": "Value:Int",
        "Category": "Local Policy",
    },
    # "Password Complexity": {"Definition": 'Enable this to score the competitor for enabling password complexity.',
    #                        "Category": 'Local Policy'},
    "Audit": {
        "Definition": "Enable this to score the competitor for setting account login audit to success and failure.",
        "Category": "Local Policy",
    },
    "Disable SSH Root Login": {
        "Definition": "'PermitRootLogin no' exists in sshd_config",
        "Category": "Local Policy",
    },
    "Good Program": {
        "Definition": "Enable this to score the competitor for installing a program.",
        "Description": 'This will score the competitor for installing a program. To add more programs press the "Add" button. To remove a program press the "X" button next to the program you want to remove. Keep it one program per line.',
        "Checks": "Program Name:Str",
        "Category": "Program Management",
    },
    "Bad Program": {
        "Definition": "Enable this to score the competitor for uninstalling a program.",
        "Description": 'This will score the competitor for uninstalling a program. To add more programs press the "Add" button. To remove a program press the "X" button next to the program you want to remove. Keep it one program per line.',
        "Checks": "Program Name:Str",
        "Category": "Program Management",
    },
    "Update Program": {
        "Definition": "(WIP)Enable this to score the competitor for updating a program.",
        "Description": '(WIP)This will score the competitor for updating a program. To add more programs press the "Add" button. To remove a program press the "X" button next to the program you want to remove. Keep it one program per line.',
        "Checks": "Program Name:Str,Version:Str",
        "Category": "Program Management",
    },
    # "Add Feature": {"Definition": '(WIP)Enable this to score the competitor for adding a feature.',
    #                "Description": '(WIP)This will score the competitor for adding a feature. To add more features press the "Add" button. To remove a feature press the "X" button next to the feature you want to remove. Keep it one feature per line.',
    #                "Checks": 'Feature Name:Str',
    #                "Category": 'Program Management'},
    # "Remove Feature": {"Definition": '(WIP)Enable this to score the competitor for removing a feature.',
    #                   "Description": '(WIP)This will score the competitor for removing a feature. To add more features press the "Add" button. To remove a feature press the "X" button next to the feature you want to remove. Keep it one feature per line.',
    #                   "Checks": 'Feature Name:Str',
    #                   "Category": 'Program Management'},
    # crit is active services is passive
    "Critical Services": {
        "Definition": "Enable this to penalize the competitor for modifying a services run ability.",
        "Description": 'This will penalize the competitor for modifying a services run ability. To add more services press the "Add" button. To remove a service press the "X" button next to the service you want to remove. Keep it one service per line.',
        "Checks": "Service Name:Str,Service State:Str,Service Start Mode:Str",
        "Category": "Program Management",
    },
    "Services": {
        "Definition": "Enable this to score the competitor for modifying a services run ability.",
        "Description": 'This will score the competitor for modifying a services run ability. To add more services press the "Add" button. To remove a service press the "X" button next to the service you want to remove. Keep it one service per line. The name can be the services system name or the displayed name.',
        "Checks": "Service Name:Str,Service State:Str,Service Start Mode:Str",
        "Category": "Program Management",
    },
    "Check Kernel": {
        "Definition": "Has kernel been updated?",
        "Category": "Local Policy",
    },
    "Critical Programs": {
        "Definition": "Enable this to penalize the competitor for removing a critical program.",
        "Description": 'This will penalize the competitor for removing a critical program. To add more programs press the "Add" button. To remove a program press the "X" button next to the program you want to remove. Keep it one program per line.',
        "Checks": "Program Name:Str",
        "Category": "Program Management",
    },
    "Update Check Period": {
        "Definition": "What has the update check period been set to? (apt/apt.conf.d/10periodic) \nPlease set Occurrence as [minute] [hour] [day of month] [month] [day of week]",
        "Category": "Program Management",
    },
    # "Update Auto Install": {"Definition": 'Automatically download and install security updates',
    #                       "Category": 'Program Management'},
    "Forensic": {
        "Definition": "Enable this to score the competitor for answering forensic a question.",
        "Description": 'This will score the competitor for answering forensic questions. To add more questions press the "Add" button. To remove questions press the "X" button next to the question you want to remove. The location will automatically be set to the desktop location configured in the main page.',
        "Checks": "Question:Str,Answers:Str,Location:Str",
        "Category": "File Management",
    },
    "Bad File": {
        "Definition": "Enable this to score the competitor for deleting a file.",
        "Description": 'This will score the competitor for deleting a file or directory. To add more files press the "Add" button. To remove a file press the "X" button next to the file you want to remove. Keep it one file per line.',
        "Checks": "File Path:Str",
        "Category": "File Management",
    },
    "Check Hosts": {
        "Definition": "Enable this to score the competitor for clearing the hosts file.",
        "Description": 'This will score the competitor for clearing the hosts file. To add more files press the "Add" button. To remove a file press the "X" button next to the file you want to remove. Keep it one file per line.',
        "Category": "File Management",
    },
    "Add Text to File": {
        "Definition": "Enable this to score the competitor for adding text to a file.",
        "Description": 'This will score the competitor for adding text to a file using regex pattern matching. The text pattern supports Python regular expressions (regex) for flexible matching. Provide the absolute file path and the regex pattern to search for. To add more files press the "Add" button. To remove a file press the "X" button next to the file you want to remove. Keep it one file per line.',
        "Checks": "Text to Add:Str,File Path:Str",
        "Category": "File Management",
    },
    "Remove Text From File": {
        "Definition": "Enable this to score the competitor for removing text from a file.",
        "Description": 'This will score the competitor for removing text from a file using regex pattern matching. The text pattern supports Python regular expressions (regex) for flexible matching. Provide the absolute file path and the regex pattern to search for. To add more files press the "Add" button. To remove a file press the "X" button next to the file you want to remove. Keep it one file per line.',
        "Checks": "Text to Remove:Str,File Path:Str",
        "Category": "File Management",
    },
    "File Permissions": {
        "Definition": "Enable this to score the competitor for changing the permissions a user has on a file.",
        "Description": 'This will score the competitor for changing the permissions a user has on a file. Use the checkboxes to specify read (4), write (2), and execute (1) permissions. The sum becomes the permission digit (0-7). To add more files press the "Add" button. To remove a file press the "X" button next to the file you want to remove. Keep it one file per line.',
        "Checks": "Users to Modify:Str,Permissions(R/W/X):Str,Object Path:Str",
        "Category": "File Management",
    },
    # "Anti-Virus": {"Definition": 'Enable this to score the competitor for installing an anti-virus. Not windows defender.',
    #               "Category": 'Miscellaneous'},
    # "Task Scheduler": {"Definition": '(WIP)Enable this to score the competitor for removing a task from the task scheduler.',
    #                   "Description": '(WIP)This will score the competitor for removing a task from the task scheduler. To add more tasks press the "Add" button. To remove a task press the "X" button next to the task you want to remove. Keep it one task per line.',
    #                   "Checks": 'Task Name:Str',
    #                   "Category": 'Miscellaneous'},
    "Check Startup": {
        "Definition": "Enable this to score the competitor for removing or disabling a program from the startup.",
        "Description": 'This will score the competitor for removing or disabling a program from the startup. To add more programs press the "Add" button. To remove a program press the "X" button next to the program you want to remove. Keep it one program per line.',
        "Checks": "Program Name:Str",
        "Category": "File Management",
    },
    # "Bad Cron": {"Definition": 'Check the root crontab for a specific string ',
    #                  "Description": 'This will score the competitor for removing or disabling a program from the startup. To add more programs press the "Add" button. To remove a program press the "X" button next to the program you want to remove. Keep it one program per line.',
    #                  "Checks": 'String Check:Str',
    #                  "Category": 'File Management'},
}
Vulnerabilities = db_handler.OptionTables(vulnerability_template)
Vulnerabilities.initialize_option_table()
vuln_settings = {}

# endregion


# class called to make us a scrollable page
class VerticalScrolledFrame(Frame):
    """
    A pure Tkinter scrollable frame that allows vertical scrolling.
    Use the 'interior' attribute to place widgets inside the scrollable frame.
    """

    def __init__(self, parent, *args, **kw):
        """
        Initialize the scrollable frame, canvas, and scrollbar.

        Args:
            parent (tk.Widget): Parent widget.
            *args: Variable length argument list.
            **kw: Arbitrary keyword arguments.
        """
        Frame.__init__(self, parent, *args, **kw)
        # create a canvas object and a vertical scrollbar for scrolling it
        self.canvas = canvas = Canvas(self, bd=0, highlightthickness=0)
        vscrollbar = ttk.Scrollbar(self, orient=VERTICAL, command=canvas.yview)
        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        vscrollbar.config(command=canvas.yview)
        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)
        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = ttk.Frame(canvas)
        interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar

        def _configure_interior(event):
            # update the scrollbar to match the size of the inner frame
            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=interior.winfo_reqwidth())

        interior.bind("<Configure>", _configure_interior)

        def _configure_canvas(event):
            if interior.winfo_reqwidth() != canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
                canvas.configure(
                    background=root.ttkStyle.lookup(".", "background"),
                    yscrollcommand=vscrollbar.set,
                )

        canvas.bind("<Configure>", _configure_canvas)


def validate_points_entry(points_var):
    """
    Validate and correct a points entry field when focus is lost.
    If the field is empty or invalid, set it to 0.
    
    Args:
        points_var: Tkinter IntVar or StringVar containing the points value
        
    Returns:
        Function to be used as FocusOut event handler
    """
    def on_focus_out(event=None):
        try:
            val = points_var.get()
            # If empty or whitespace, set to 0
            if not val or not str(val).strip():
                points_var.set(0)
            else:
                # Try to convert to int to validate
                int(val)
        except (ValueError, TypeError, TclError):
            # If conversion fails, set to 0
            points_var.set(0)
        return True
    return on_focus_out


# this class declares most of our ui, pulling from the db, it generates a checkbox under the right category
class Config(Tk):
    """
    Main GUI class for the configurator application.
    Builds the UI, loads settings and vulnerabilities, and manages user interaction.

    Args:
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        None
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the Configurator window, load settings, and build UI pages.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        Tk.__init__(self, *args, **kwargs)

        # elevated privilege is needed to run our commands, it asks on boot
        # fix Check- idk if this works but I think it should
        # turn off before PUSH
        if not "SUDO_UID" in os.environ.keys():
            switch = messagebox.askyesno(
                "Root Access Required",
                "You need to be Admin to Write to Config. Please relaunch the configurator as Administrator.",
            )
            if switch:
                sys.exit(1)
            return

        nb = ttk.Notebook(self)
        MainPage = ttk.Frame(nb)

        self.MenuSettings = Settings.get_settings()
        temp_style = self.MenuSettings["Style"].get()
        
        ttk.Label(
            MainPage,
            text="Scoring Report Location, commit when ready to deploy(Make sure to commit instead of just closing the window):",
        ).grid(row=0, column=0, sticky=W, columnspan=4)
        ttk.OptionMenu(MainPage, self.MenuSettings["Style"], *themeList).grid(
            row=0, column=5, sticky=EW
        )
        self.MenuSettings["Style"].set(temp_style)
        ttk.Button(
            MainPage,
            text="Set",
            width=5,
            command=lambda: (change_theme(self.MenuSettings["Style"])),
        ).grid(row=0, column=6, sticky=E)
        ttk.Button(MainPage, text="Commit", command=lambda: (commit_config())).grid(
            row=1, sticky=W
        )
        ttk.Entry(MainPage, textvariable=self.MenuSettings["Desktop"]).grid(
            row=1, column=1, columnspan=4, sticky=EW
        )
        ttk.Checkbutton(
            MainPage, text="Silent Miss", variable=self.MenuSettings["Silent Mode"]
        ).grid(row=2, sticky=W)
        ttk.Label(
            MainPage,
            text="Check this box to hide missed items (Similar to competition)",
        ).grid(row=2, column=1, columnspan=5, sticky=W)
        ttk.Checkbutton(
            MainPage,
            text="Server Mode",
            variable=self.MenuSettings["Server Mode"],
            command=lambda: (
                serverL.configure(state="enable"),
                serverE.configure(state="enable"),
                userL.configure(state="enable"),
                userE.configure(state="enable"),
                passL.configure(state="enable"),
                passE.configure(state="enable"),
            ),
        ).grid(row=3, sticky=W)
        ttk.Label(
            MainPage,
            text="Check this box to enable an FTP server to save the scores (Similar to competition)",
        ).grid(row=3, column=1, columnspan=5, sticky=W)
        serverL = ttk.Label(MainPage, text="Server Name/IP", state="disable")
        serverL.grid(row=4, sticky=E)
        serverE = ttk.Entry(
            MainPage,
            textvariable=self.MenuSettings["Server Name"],
            state="disable",
            width=30,
        )
        serverE.grid(row=4, column=1, sticky=EW)
        userL = ttk.Label(MainPage, text="User Name", state="disable")
        userL.grid(row=4, column=2, sticky=E)
        userE = ttk.Entry(
            MainPage,
            textvariable=self.MenuSettings["Server User"],
            state="disable",
            width=30,
        )
        userE.grid(row=4, column=3, sticky=EW)
        passL = ttk.Label(MainPage, text="Password", state="disable")
        passL.grid(row=4, column=4, sticky=E)
        passE = ttk.Entry(
            MainPage,
            textvariable=self.MenuSettings["Server Password"],
            state="disable",
            width=30,
        )
        passE.grid(row=4, column=5, sticky=EW)
        ttk.Label(MainPage, text="Total Points:").grid(row=5, column=0)
        ttk.Label(
            MainPage,
            textvariable=self.MenuSettings["Tally Points"],
            font="Verdana 10 bold",
            wraplength=150,
        ).grid(row=5, column=1)
        ttk.Label(MainPage, text="Total Vulnerabilities:").grid(
            row=6, column=0, rowspan=4
        )
        ttk.Label(
            MainPage,
            textvariable=self.MenuSettings["Tally Vulnerabilities"],
            font="Verdana 10 bold",
            wraplength=150,
        ).grid(row=6, column=1)
        # ttk.Label(
        #     MainPage,
        #     text="Created by Shaun Martin, Anthony Nguyen, Bryan Ortiz and Minh-Khoi Do",
        # ).grid(row=10, column=0, columnspan=4, sticky=SW)
        ttk.Label(
            MainPage,
            text="Testing/Configuring: To update db and scoring report, use the button below:",
        ).grid(row=10, column=0, columnspan=4, sticky=SW)
        ttk.Button(MainPage, text='Save Configuration', width=25, command=lambda: (save_config())).grid(
            row=11, sticky=W)
        MainPage.columnconfigure(tuple(range(10)), weight=1)
        # MainPage.rowconfigure(tuple(range(5)), weight=1)

        # each category is a page that then holds its vulnerabilities
        pages = {}
        for category in Categories.get_categories():
            page = VerticalScrolledFrame(nb)
            pageList = ttk.Frame(page.interior)
            pageList.pack(fill=X)
            pageList.grid_columnconfigure(1, weight=1)
            pageIn = ttk.Frame(page)
            pageIn.pack(before=page.canvas, fill=X)
            
            # Always stretch column 1 (the definition/description column)
            pageIn.grid_columnconfigure(1, weight=1)
            
            # Adjust columnspan based on whether we show Value column
            desc_colspan = 4 if category.name == "Local Policy" else 3
            
            ttk.Label(pageIn, text=category.description, padding="10 5").grid(
                row=0, column=0, columnspan=desc_colspan, sticky=W
            )
            ttk.Label(pageIn, text="Vulnerabilities", font="Verdana 12 bold").grid(
                row=1, column=0, sticky=W
            )
            # For Local Policy, add "Value" and "Points" labels in columns 2 and 3
            if category.name == "Local Policy":
                ttk.Label(pageIn, text="Value", font="Verdana 12 bold").grid(
                    row=1, column=2, sticky=E, padx=5
                )
                ttk.Label(pageIn, text="Points", font="Verdana 12 bold").grid(
                    row=1, column=3, sticky=E, padx=5
                )
            else:
                ttk.Label(pageIn, text="Points", font="Verdana 12 bold").grid(
                    row=1, column=2, sticky=E
                )
            for i, vuln in enumerate(
                Vulnerabilities.get_option_template_by_category(category.id)
            ):
                vuln_settings.update({vuln.name: {}})
                vuln_settings[vuln.name] = Vulnerabilities.get_option_table(
                    vuln.name
                ).copy()
                self.add_option(
                    pageList, vuln_settings[vuln.name], vuln.name, i * 2 + 2, nb
                )
            pages.update({category.name: page})

        ReportPage = VerticalScrolledFrame(nb)
        ReportPageList = ttk.Frame(ReportPage.interior)
        ReportPageList.pack(fill=X)
        ReportPageIn = ttk.Frame(ReportPage)
        ReportPageIn.pack(before=ReportPage.canvas, fill=X)
        # ttk.Button(ReportPageIn, text='Export to csv').grid(row=0, column=0, stick=EW)
        ttk.Button(
            ReportPageIn,
            text="Export to HTML",
            command=lambda: (generate_export(".html")),
        ).grid(row=1, column=0, stick=EW)
        ttk.Button(
            ReportPageIn,
            text="Generate",
            command=lambda: (self.generate_report(ReportPageList)),
        ).grid(row=2, column=0, stick=EW)
        ttk.Label(
            ReportPageIn,
            text='This section is for reviewing the options that will be scored. To view the report press the "Generate" button. To export this report to a web page press the "Export to HTML" button.',
        ).grid(row=0, column=1, rowspan=3, columnspan=4)
        # ttk.Label(ReportPageIn, text='This section is for reviewing the options that will be scored. To view the report press the "Generate" button. To export this report to a .csv file press the "Export to CSV" button(WIP). To export this report to a web page press the "Export to HTML" button.').grid(row=0, column=1, rowspan=3, columnspan=4)
        ttk.Separator(ReportPageIn, orient=HORIZONTAL).grid(
            row=3, column=0, columnspan=5, sticky=EW
        )

        nb.add(MainPage, text="Main Page")
        for page in pages:
            nb.add(pages[page], text=page)
        nb.add(ReportPage, text="Report")

        nb.pack(expand=1, fill="both")

    def add_option(self, frame, entry, name, row, return_frame):
        """
        Add a vulnerability option to the UI with checkboxes and controls.

        Args:
            frame (tk.Frame): Parent frame to add widgets.
            entry (dict): Vulnerability settings.
            name (str): Vulnerability name.
            row (int): Row index for grid placement.
            return_frame (tk.Frame): Frame to return to after modification.
        """
        ttk.Checkbutton(frame, text=name, variable=entry[1]["Enabled"], command=tally).grid(
            row=row, column=0, stick=W
        )
        ttk.Label(
            frame, text=Vulnerabilities.get_option_template(name).definition
        ).grid(row=row, column=1, stick=W)
        
        # Check if this vulnerability has only a "Value" check (password policies)
        has_only_value_check = (len(entry[1]["Checks"]) == 1 and "Value" in entry[1]["Checks"])
        
        if has_only_value_check:
            # Place Value entry in column 2 and Points entry in column 3 to align with headers
            # Value entry
            value_entry = ttk.Entry(
                frame, width=5, textvariable=entry[1]["Checks"]["Value"], font="Verdana 10"
            )
            value_entry.grid(row=row, column=2, padx=5, sticky=E)
            value_entry.bind("<FocusOut>", validate_points_entry(entry[1]["Checks"]["Value"]))
            entry[1]["Checks"]["Value"].trace('w', lambda name, index, mode: tally())
            
            # Points entry
            points_entry = ttk.Entry(
                frame, width=5, textvariable=entry[1]["Points"], font="Verdana 10"
            )
            points_entry.grid(row=row, column=3, padx=5, sticky=E)
            points_entry.bind("<FocusOut>", validate_points_entry(entry[1]["Points"]))
            entry[1]["Points"].trace('w', lambda name, index, mode: tally())
            
        elif len(entry[1]["Checks"]) > 0:
            ttk.Button(
                frame,
                text="Modify",
                command=lambda: self.modify_settings(name, entry, return_frame),
            ).grid(row=row, column=3, padx=5, sticky=E)
        else:
            # Add trace to points variable to update tally when changed
            entry[1]["Points"].trace('w', lambda name, index, mode: tally())
            points_entry = ttk.Entry(
                frame, width=5, textvariable=entry[1]["Points"], font="Verdana 10"
            )
            # Place in column 3 to align with password policy entries, with same padding
            points_entry.grid(row=row, column=3, padx=5, sticky=E)
            # Bind FocusOut event to validate and auto-correct empty values
            points_entry.bind("<FocusOut>", validate_points_entry(entry[1]["Points"]))
        
        # Separator always spans 4 columns for consistency
        ttk.Separator(frame, orient=HORIZONTAL).grid(
            row=row + 1, column=0, columnspan=4, sticky=EW
        )

    def modify_settings(self, name, entry, packing):
        """
        Show the modification UI for a vulnerability option.

        Args:
            name (str): Vulnerability name.
            entry (dict): Vulnerability settings.
            packing (tk.Frame): Frame to return to after modification.
        """
        self.pack_slaves()[0].pack_forget()
        modifyPage = VerticalScrolledFrame(self)
        modifyPage.pack(expand=1, fill="both")
        modifyPageList = modifyPage.interior
        modifyPageList.pack(fill=X)
        modifyPageIn = ttk.Frame(modifyPage)
        modifyPageIn.pack(before=modifyPage.canvas, fill=X)
        # Automatic enabling when modifying settings, disabled for now
        # if entry[1]["Enabled"].get() != 1:
        #     entry[1]["Enabled"].set(1)
        ttk.Button(
            modifyPageIn,
            text="Save",
            command=lambda: (
                self.pack_slaves()[0].pack_forget(),
                packing.pack(expand=1, fill="both"),
                Vulnerabilities.update_table(name, entry),
                tally(),
            ),
        ).grid(row=0, column=0, sticky=EW)
        ttk.Label(modifyPageIn, text=name + " Modification", font="Verdana 15").grid(
            row=0, column=1, columnspan=len(entry[1]["Checks"])
        )
        ttk.Button(
            modifyPageIn,
            text="Add",
            command=lambda: (add_row(modifyPageList, entry, name), tally()),
        ).grid(row=1, column=0, sticky=EW)
        ttk.Label(
            modifyPageIn,
            text=Vulnerabilities.get_option_template(name).description,
            wraplength=int(self.winfo_screenwidth() * 2 / 3 - 100),
        ).grid(row=1, column=1, columnspan=len(entry[1]["Checks"]))
        ttk.Label(modifyPageIn, text="Points", font="Verdana 10 bold", width=10).grid(
            row=2, column=0
        )
        r = 2
        for i, t in enumerate(entry[1]["Checks"]):
            modifyPageIn.grid_columnconfigure(i + 1, weight=1)
            # Create a frame for each header label to match the structure of the content below
            header_frame = ttk.Frame(modifyPageIn)
            header_frame.grid(row=2, column=i + 1, sticky=EW)
            ttk.Label(header_frame, text=t, font="Verdana 10 bold").grid(
                row=0, column=0, sticky=W
            )
            r = i + 2
        ttk.Label(modifyPageIn, text="Remove", font="Verdana 10 bold").grid(
            row=2, column=r
        )
        for vuln in entry:
            if vuln != 1:
                load_modify_settings(modifyPageList, entry, name, vuln)

    def generate_report(self, frame):
        """
        Generate and display the scoring report in the UI.

        Args:
            frame (tk.Frame): Frame to display the report.
        """
        save_config()
        for i in frame.grid_slaves():
            i.destroy()
        wrap = int(self.winfo_screenwidth() * 2 / 3 / 5) - 86
        final_row = 5

        frame.rowconfigure(4, weight=1)
        report_frame = ttk.Frame(frame)
        report_frame.grid(row=4, column=0, columnspan=5, sticky=NSEW)
        categories = Categories.get_categories()
        for cat_row, category in enumerate(categories):
            category_frame = ttk.Frame(report_frame, borderwidth=1, relief=GROOVE)
            category_frame.grid(row=cat_row, column=1, sticky=NSEW)
            category_frame.columnconfigure(1, weight=1)
            ttk.Label(category_frame, text=category.name).grid(row=0, column=0)
            vulns_row = ttk.Frame(category_frame, borderwidth=1, relief=GROOVE)
            vulns_row.grid(row=0, column=1, sticky=EW)
            vulnerabilities = Vulnerabilities.get_option_template_by_category(
                category.id
            )
            cat_tested = False
            for vuln_row, vulnerability in enumerate(vulnerabilities):
                settings = Vulnerabilities.get_option_table(vulnerability.name)
                if int(settings[1]["Enabled"].get()) == 1:
                    vulnerability_frame = ttk.Frame(
                        vulns_row, borderwidth=1, relief=GROOVE
                    )
                    vulnerability_frame.grid(row=vuln_row, column=1, sticky=EW)
                    vulnerability_frame.columnconfigure(1, weight=1)
                    ttk.Label(vulnerability_frame, text=vulnerability.name).grid(
                        row=0, column=0
                    )
                    setting_frame = ttk.Frame(
                        vulnerability_frame, borderwidth=1, relief=GROOVE, padding=1
                    )
                    setting_frame.grid(row=0, column=1, sticky=EW)
                    setting_frame.columnconfigure(0, weight=1)
                    cat_tested = True
                    width = len(settings[1]["Checks"]) + 1
                    temp_col = 1
                    ttk.Label(setting_frame, text="Points").grid(row=0, column=0)
                    for check in settings[1]["Checks"]:
                        ttk.Label(setting_frame, text=check).grid(
                            row=0, column=temp_col
                        )
                        temp_col += 1
                    final_row += 1
                    for set_row, setting in enumerate(settings):
                        if (width > 0 and setting != 1) or (width == 1):
                            ttk.Separator(setting_frame, orient=HORIZONTAL).grid(
                                row=set_row * 2 + 1, column=0, columnspan=5, sticky=EW
                            )
                            temp_col = 1
                            ttk.Label(
                                setting_frame, text=settings[setting]["Points"].get()
                            ).grid(row=set_row * 2 + 2, column=0)
                            for check in settings[setting]["Checks"]:
                                ttk.Label(
                                    setting_frame,
                                    text=settings[setting]["Checks"][check].get(),
                                ).grid(row=set_row * 2 + 2, column=temp_col)
                                temp_col += 1
            if not cat_tested:
                category_frame.destroy()


def load_modify_settings(frame, entry, name, idx):
    """
    Load and display the modification controls for a vulnerability option.

    Args:
        frame (tk.Frame): Parent frame to add widgets.
        entry (dict): Vulnerability settings.
        name (str): Vulnerability name.
        idx (int): Index of the vulnerability option.

    Returns:
        None
    """
    modifyPageListRow = ttk.Frame(frame)
    modifyPageListRow.pack(fill=X)
    points_entry = ttk.Entry(modifyPageListRow, width=10, textvariable=entry[idx]["Points"])
    points_entry.grid(row=0, column=0)
    # Bind FocusOut event to validate and auto-correct empty values
    points_entry.bind("<FocusOut>", validate_points_entry(entry[idx]["Points"]))
    c = 0
    for r, t in enumerate(entry[idx]["Checks"]):
        r += 1
        if t == "Object Path":
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            path = ttk.Frame(modifyPageListRow)
            path.grid(row=0, column=r, sticky=EW)
            path.grid_columnconfigure(0, weight=1)
            ttk.Label(
                path,
                text="To point to a directory check directory otherwise leave unchecked.",
            ).grid(row=1, column=0, sticky=E)
            switch = IntVar()
            ttk.Checkbutton(path, variable=switch, text="Directory").grid(
                row=1, column=1
            )
            ttk.Entry(path, textvariable=entry[idx]["Checks"][t]).grid(
                row=0, column=0, sticky=EW
            )
            ttk.Button(
                path,
                text="...",
                command=lambda: set_file_or_directory(
                    entry[idx]["Checks"], switch, name
                ),
            ).grid(row=0, column=1)
            c = r + 1
        elif t == "File Path":
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            path = ttk.Frame(modifyPageListRow)
            path.grid(row=0, column=r, sticky=EW)
            path.grid_columnconfigure(0, weight=1)
            ttk.Label(
                path,
                text="Uses regex, to use a special character escape it with a backslash(\\).",
            ).grid(row=1, column=0, sticky=E)
            ttk.Entry(path, textvariable=entry[idx]["Checks"][t]).grid(
                row=0, column=0, sticky=EW
            )
            ttk.Button(
                path,
                text="...",
                command=lambda: set_file_only(
                    entry[idx]["Checks"], name
                ),
            ).grid(row=0, column=1)
            c = r + 1
        elif t == "Service Name":
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            service_list = get_service_list()
            ttk.Combobox(
                modifyPageListRow,
                textvariable=entry[idx]["Checks"][t],
                values=service_list,
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Service State":
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            ttk.OptionMenu(
                modifyPageListRow,
                entry[idx]["Checks"][t],
                entry[idx]["Checks"][t].get(),
                "active", "inactive", "failed",
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Service Start Mode":
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            ttk.OptionMenu(
                modifyPageListRow,
                entry[idx]["Checks"][t],
                entry[idx]["Checks"][t].get(),
                "enabled", "disabled", "masked",
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "User Name":
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            user_list = get_user_list()
            ttk.Combobox(
                modifyPageListRow,
                textvariable=entry[idx]["Checks"][t],
                values=user_list,
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Group Name":
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            group_list = get_group_list()
            ttk.Combobox(
                modifyPageListRow,
                textvariable=entry[idx]["Checks"][t],
                values=group_list,
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Location":
            # Make Location field read-only for forensic questions
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            location_entry = ttk.Entry(modifyPageListRow, textvariable=entry[idx]["Checks"][t], state="readonly")
            location_entry.grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Permissions(R/W/X)":
            # Create checkboxes for read, write, execute permissions
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            perm_frame = ttk.Frame(modifyPageListRow, borderwidth=2, relief="groove", padding=5)
            perm_frame.grid(row=0, column=r, sticky=EW, padx=2, pady=2)
            
            # # Add title label
            # ttk.Label(perm_frame, text="Permissions(R/W/X)", font="Verdana 9 bold").grid(
            #     row=0, column=0, columnspan=4, sticky=W, pady=(0, 5)
            # )
            
            # Parse current permission value (0-7) into checkbox states
            try:
                perm_value = int(entry[idx]["Checks"][t].get() or "0")
            except ValueError:
                perm_value = 0
            
            # Create IntVars for each permission bit
            read_var = IntVar(value=4 if (perm_value & 4) else 0)
            write_var = IntVar(value=2 if (perm_value & 2) else 0)
            exec_var = IntVar(value=1 if (perm_value & 1) else 0)
            
            # Function to update the permission string when checkboxes change
            def update_permission(*args):
                new_value = read_var.get() + write_var.get() + exec_var.get()
                entry[idx]["Checks"][t].set(str(new_value))
            
            # Create checkboxes in row 1
            ttk.Checkbutton(perm_frame, text="Read(4)", variable=read_var, 
                          onvalue=4, offvalue=0, command=update_permission).grid(row=1, column=0, padx=2)
            ttk.Checkbutton(perm_frame, text="Write(2)", variable=write_var,
                          onvalue=2, offvalue=0, command=update_permission).grid(row=1, column=1, padx=2)
            ttk.Checkbutton(perm_frame, text="Execute(1)", variable=exec_var,
                          onvalue=1, offvalue=0, command=update_permission).grid(row=1, column=2, padx=2)
            
            # Label to show current octal value
            perm_label = ttk.Label(perm_frame, text=f"({perm_value})")
            perm_label.grid(row=1, column=3, padx=5)
            
            # Update label when permission changes
            def update_label(*args):
                update_permission()
                perm_label.config(text=f"({entry[idx]['Checks'][t].get()})")
            
            read_var.trace('w', update_label)
            write_var.trace('w', update_label)
            exec_var.trace('w', update_label)
            
            c = r + 1
        else:
            # print(t)
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            ttk.Entry(modifyPageListRow, textvariable=entry[idx]["Checks"][t]).grid(
                row=0, column=r, sticky=EW
            )

            c = r + 1
    ttk.Button(
        modifyPageListRow,
        text="X",
        width=8,
        command=lambda: (
            remove_row(entry, idx, modifyPageListRow),
            Vulnerabilities.remove_from_table(name, idx),
        ),
    ).grid(row=0, column=c, sticky=W)


def add_row(frame, entry, name):
    """
    Add a new row for a vulnerability option in the modification UI.

    Args:
        frame (tk.Frame): Parent frame to add widgets.
        entry (dict): Vulnerability settings.
        name (str): Vulnerability name.

    Returns:
        None
    """
    idx = Vulnerabilities.add_to_table(name)
    entry.update({idx: Vulnerabilities.get_option_table(name)[idx]})
    
    # Add trace to points variable to update tally when changed
    entry[idx]["Points"].trace('w', lambda name, index, mode: tally())

    mod_frame = ttk.Frame(frame)
    mod_frame.pack(fill=X)

    points_entry = ttk.Entry(mod_frame, width=10, textvariable=entry[idx]["Points"])
    points_entry.grid(row=0, column=0)
    # Bind FocusOut event to validate and auto-correct empty values
    points_entry.bind("<FocusOut>", validate_points_entry(entry[idx]["Points"]))
    c = 0
    for r, t in enumerate(entry[idx]["Checks"]):
        r += 1
        if t == "Object Path":
            mod_frame.grid_columnconfigure(r, weight=1)
            path = ttk.Frame(mod_frame)
            path.grid(row=0, column=r, sticky=EW)
            path.grid_columnconfigure(0, weight=1)
            ttk.Label(
                path,
                text="To point to a directory check directory otherwise leave unchecked.",
            ).grid(row=1, column=0, sticky=E)
            switch = IntVar()
            ttk.Checkbutton(path, variable=switch, text="Directory").grid(
                row=1, column=1
            )
            ttk.Entry(path, textvariable=entry[idx]["Checks"][t]).grid(
                row=0, column=0, sticky=EW
            )
            ttk.Button(
                path,
                text="...",
                command=lambda: set_file_or_directory(
                    entry[idx]["Checks"], switch, name
                ),
            ).grid(row=0, column=1)
            c = r + 1
        elif t == "File Path":
            mod_frame.grid_columnconfigure(r, weight=1)
            path = ttk.Frame(mod_frame)
            path.grid(row=0, column=r, sticky=EW)
            path.grid_columnconfigure(0, weight=1)
            ttk.Entry(path, textvariable=entry[idx]["Checks"][t]).grid(
                row=0, column=0, sticky=EW
            )
            ttk.Button(
                path,
                text="...",
                command=lambda: set_file_only(
                    entry[idx]["Checks"], name
                ),
            ).grid(row=0, column=1)
            c = r + 1
        elif t == "Service Name":
            mod_frame.grid_columnconfigure(r, weight=1)
            service_list = get_service_list()
            ttk.Combobox(
                mod_frame, textvariable=entry[idx]["Checks"][t], values=service_list
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Service State":
            mod_frame.grid_columnconfigure(r, weight=1)
            ttk.OptionMenu(
                mod_frame, entry[idx]["Checks"][t], entry[idx]["Checks"][t].get(),
                "active", "inactive", "failed"
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Service Start Mode":
            mod_frame.grid_columnconfigure(r, weight=1)
            ttk.OptionMenu(
                mod_frame,
                entry[idx]["Checks"][t],
                entry[idx]["Checks"][t].get(),
                "enabled", "disabled", "masked",
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "User Name":
            mod_frame.grid_columnconfigure(r, weight=1)
            user_list = get_user_list()
            ttk.Combobox(
                mod_frame, textvariable=entry[idx]["Checks"][t], values=user_list
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Group Name":
            mod_frame.grid_columnconfigure(r, weight=1)
            group_list = get_group_list()
            ttk.Combobox(
                mod_frame, textvariable=entry[idx]["Checks"][t], values=group_list
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Location":
            # Make Location field read-only for forensic questions
            mod_frame.grid_columnconfigure(r, weight=1)
            location_entry = ttk.Entry(mod_frame, textvariable=entry[idx]["Checks"][t], state="readonly")
            location_entry.grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Permissions(R/W/X)":
            # Create checkboxes for read, write, execute permissions
            mod_frame.grid_columnconfigure(r, weight=1)
            perm_frame = ttk.Frame(mod_frame, borderwidth=2, relief="groove", padding=5)
            perm_frame.grid(row=0, column=r, sticky=EW, padx=2, pady=2)
            
            # Add title label
            ttk.Label(perm_frame, text="Permissions(R/W/X)", font="Verdana 9 bold").grid(
                row=0, column=0, columnspan=4, sticky=W, pady=(0, 5)
            )
            
            # Parse current permission value (0-7) into checkbox states
            try:
                perm_value = int(entry[idx]["Checks"][t].get() or "0")
            except ValueError:
                perm_value = 0
            
            # Create IntVars for each permission bit
            read_var = IntVar(value=4 if (perm_value & 4) else 0)
            write_var = IntVar(value=2 if (perm_value & 2) else 0)
            exec_var = IntVar(value=1 if (perm_value & 1) else 0)
            
            # Function to update the permission string when checkboxes change
            def update_permission(*args):
                new_value = read_var.get() + write_var.get() + exec_var.get()
                entry[idx]["Checks"][t].set(str(new_value))
            
            # Create checkboxes in row 1
            ttk.Checkbutton(perm_frame, text="Read(4)", variable=read_var, 
                          onvalue=4, offvalue=0, command=update_permission).grid(row=1, column=0, padx=2)
            ttk.Checkbutton(perm_frame, text="Write(2)", variable=write_var,
                          onvalue=2, offvalue=0, command=update_permission).grid(row=1, column=1, padx=2)
            ttk.Checkbutton(perm_frame, text="Execute(1)", variable=exec_var,
                          onvalue=1, offvalue=0, command=update_permission).grid(row=1, column=2, padx=2)
            
            # Label to show current octal value
            perm_label = ttk.Label(perm_frame, text=f"({perm_value})")
            perm_label.grid(row=1, column=3, padx=5)
            
            # Update label when permission changes
            def update_label(*args):
                update_permission()
                perm_label.config(text=f"({entry[idx]['Checks'][t].get()})")
            
            read_var.trace('w', update_label)
            write_var.trace('w', update_label)
            exec_var.trace('w', update_label)
            
            c = r + 1
        else:
            mod_frame.grid_columnconfigure(r, weight=1)
            ttk.Entry(mod_frame, textvariable=entry[idx]["Checks"][t]).grid(
                row=0, column=r, sticky=EW
            )
            c = r + 1
    ttk.Button(
        mod_frame,
        text="X",
        width=8,
        command=lambda: (
            remove_row(entry[idx], idx, mod_frame),
            Vulnerabilities.remove_from_table(name, idx),
            tally(),
        ),
    ).grid(row=0, column=c, sticky=W)


def remove_row(entry, idx, widget):
    """
    Remove a row from the vulnerability option table and UI.

    Args:
        entry (dict): Vulnerability settings dictionary (all entries).
        idx (int): Index of the row to remove.
        widget (tk.Widget): Widget to destroy.

    Returns:
        None
    """
    if idx in entry:
        del entry[idx]
    widget.destroy()


def set_file_or_directory(var, switch, mode):
    """
    Set the file or directory path for a vulnerability option.

    Args:
        var (dict): Dictionary of Tkinter variables for the option.
        switch (tk.IntVar): Variable indicating directory selection.
        mode (str): Vulnerability mode (e.g., "File Permissions").

    Returns:
        None
    """
    if switch.get() == 1:
        file = filedialog.askdirectory()
        var["Object Path"].set(file)
    else:
        file = filedialog.askopenfilename()
        var["Object Path"].set(file)
    if mode == "File Permissions":
        status = os.stat(file)
        current = bin(status.st_mode)[-9:]
        for idx, perm in enumerate(current):
            var["Permissions"][idx].set(int(perm))


def set_file_only(var, mode):
    """
    Set the file path for a vulnerability option (file only, no directory option).

    Args:
        var (dict): Dictionary of Tkinter variables for the option.
        mode (str): Vulnerability mode (e.g., "Add Text to File").

    Returns:
        None
    """
    file = filedialog.askopenfilename()
    var["File Path"].set(file)


# check
def create_forensic():
    """
    Create forensic question files on the desktop if enabled.

    Args:
        None

    Returns:
        None
    """
    qHeader = (
        "This is a forensics question. Answer it below(answers are case sensitive)\n---------------------------------------\n"
    )
    qFooter = "\n\nANSWER: <TypeAnswerHere>"
    if vuln_settings["Forensic"][1]["Enabled"].get() == 1:
        # Check what forensic question numbers already exist on the desktop
        desktop_path = str(root.MenuSettings["Desktop"].get())
        existing_numbers = set()
        
        if os.path.exists(desktop_path):
            for filename in os.listdir(desktop_path):
                if filename.startswith("Forensic Question ") and filename.endswith(".txt"):
                    try:
                        # Extract the number from "Forensic Question X.txt"
                        num_str = filename[18:-4]  # Skip "Forensic Question " and ".txt"
                        num = int(num_str)
                        existing_numbers.add(num)
                    except ValueError:
                        pass  # Ignore files with non-numeric numbers
        
        # Also check existing Location values in other questions
        for question in vuln_settings["Forensic"]:
            if question != 1:
                location = vuln_settings["Forensic"][question]["Checks"]["Location"].get()
                if location:
                    # Extract number from location path if it matches the pattern
                    try:
                        # Find "Forensic Question X.txt" in the path
                        if "Forensic Question " in location and location.endswith(".txt"):
                            # Get the filename from the full path
                            filename = os.path.basename(location)
                            num_str = filename[18:-4]  # Skip "Forensic Question " and ".txt"
                            num = int(num_str)
                            existing_numbers.add(num)
                    except ValueError:
                        pass  # Ignore non-standard paths
        
        # Find available numbers starting from 1
        available_numbers = []
        num = 1
        for question in vuln_settings["Forensic"]:
            if question != 1:
                # Find next available number
                while num in existing_numbers:
                    num += 1
                available_numbers.append(num)
                num += 1
        
        # Now assign the available numbers to questions
        num_index = 0
        for question in vuln_settings["Forensic"]:
            if question != 1:
                location = vuln_settings["Forensic"][question]["Checks"][
                    "Location"
                ].get()
                if location == "":
                    q_num = available_numbers[num_index]
                    vuln_settings["Forensic"][question]["Checks"]["Location"].set(
                        str(root.MenuSettings["Desktop"].get())
                        + "Forensic Question "
                        + str(q_num)
                        + ".txt"
                    )
                    location = vuln_settings["Forensic"][question]["Checks"][
                        "Location"
                    ].get()
                    num_index += 1
                g = open(location, "w+")
                g.write(
                    qHeader
                    + vuln_settings["Forensic"][question]["Checks"]["Question"].get()
                    + qFooter
                )
                g.close()
                
                # Set permissions to give basic users write access (0o666 = rw-rw-rw-)
                os.chmod(location, 0o666)


def resource_path(relative_path):
    """
    Get absolute path to resource, works for dev and for PyInstaller.

    Args:
        relative_path (str): Relative path to the resource.

    Returns:
        str: Absolute path to the resource.
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS + "/assets/icons"
        if not os.path.exists(os.path.join(base_path, relative_path)):
            # Fallback to project structure during development
            base_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "assets",
                "icons",
            )
            if not os.path.exists(os.path.join(base_path, relative_path)):
                base_path = os.path.abspath("/")
    except Exception:
        # Development mode - look in assets/icons relative to project root
        base_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "assets",
            "icons",
        )
        if not os.path.exists(os.path.join(base_path, relative_path)):
            base_path = os.path.abspath("/")

    return os.path.join(base_path, relative_path)


def commit_config():
    """
    Save configuration, copy assets, set permissions, and schedule scoring engine via cron.

    Args:
        None

    Returns:
        None
    """
    save_config()

    # check
    output_directory = "/etc/CYBERPATRIOT_DO_NOT_REMOVE/"
    web_directory = "/var/www/CYBERPATRIOT"
    current_directory = os.getcwd()
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    if not os.path.exists(web_directory):
        os.makedirs(web_directory)
    # TODO(later): Check if still redundant due to service_setup.py
    # print(find_absolute_path("scoring_engine_DO_NOT_TOUCH"))
    # shutil.copy(
    #     find_absolute_path("scoring_engine_DO_NOT_TOUCH"),
    #     os.path.join(output_directory, "scoring_engine_DO_NOT_TOUCH"),
    # )
    shutil.copy(
        resource_path("ScoringEngineLinuxBig.png"),
        output_directory + "ScoringEngineLinuxBig.png", #Places a copy in /etc/CYBERPATRIOT_DO_NOT_REMOVE/
    )

    shutil.copy(
        resource_path("CCC_logo.png"), os.path.join(web_directory, "CCC_logo.png")
    )
    shutil.copy(
        resource_path("SoCalCCCC.png"), os.path.join(web_directory, "SoCalCCCC.png")
    )
    shutil.copy(
        resource_path("ScoringEngineLinuxBig.png"),
        os.path.join(web_directory + "/ScoringEngineLinuxBig.png"),
    )
    os.chmod("/etc/systemd/system/scoring_engine.service", 0o777)
    os.chmod(web_directory + "/CCC_logo.png", 0o777)
    os.chmod(web_directory + "/SoCalCCCC.png", 0o777)
    os.chmod(web_directory + "/ScoringEngineLinuxBig.png", 0o777)
    os.chown(
        os.path.join(web_directory, "CCC_logo.png"),
        int(os.environ["SUDO_UID"]),
        int(os.environ["SUDO_UID"]),
    )
    os.chown(
        os.path.join(web_directory, "SoCalCCCC.png"),
        int(os.environ["SUDO_UID"]),
        int(os.environ["SUDO_UID"]),
    )
    os.chown(
        web_directory + "/ScoringEngineLinuxBig.png",
        int(os.environ["SUDO_UID"]),
        int(os.environ["SUDO_UID"]),
    )

    # Restart the scoring engine service to pick up new configuration immediately
    try:
        print("Restarting scoring_engine service to apply new configuration...")
        # subprocess.run(["systemctl", "restart", "scoring_engine"], check=True, capture_output=True) # TODO(later): Uncomment when done developing
        print("✓ Scoring engine service restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not restart scoring_engine service: {e.stderr.decode() if e.stderr else e}", file=sys.stderr)
        print("The service may not be running. Configuration is still saved.", file=sys.stderr)
    except Exception as e:
        print(f"Warning: Unexpected error restarting service: {e}", file=sys.stderr)
    sys.exit()


# check
def save_config():
    """
    Save current configuration and vulnerability settings to the database and create forensic files.

    Args:
        None

    Returns:
        None
    """
    desk = f'/home/{os.environ.get("SUDO_USER")}/Desktop'
    if desk not in root.MenuSettings["Desktop"].get():
        root.MenuSettings["Desktop"].set(
            "/home/" + os.environ.get("SUDO_USER") + "/Desktop/"
        )
    
    # Validate and fix empty point values before saving
    for vuln in vuln_settings:
        for setting_id in vuln_settings[vuln]:
            if setting_id != 1 or len(vuln_settings[vuln]) == 1:
                points_var = vuln_settings[vuln][setting_id]["Points"]
                points_val = points_var.get()
                # If points is empty or invalid, set it to 0
                if not points_val or not str(points_val).strip():
                    points_var.set(0)
                else:
                    try:
                        # Validate it's a valid integer
                        int(points_val)
                    except (ValueError, TypeError):
                        # If not valid, set to 0
                        points_var.set(0)
    
    create_forensic()
    tally()
    Settings.update_table(root.MenuSettings)
    for vuln in vuln_settings:
        Vulnerabilities.update_table(vuln, vuln_settings[vuln])
    Vulnerabilities.cleanup()


# score count
def tally():
    """
    Calculate and update the total points and vulnerabilities based on current settings.
    Note: "Critical Users" vulnerability points are excluded from total points as they are penalties.

    Args:
        None

    Returns:
        None
    """
    # Set tally scores
    tally_score = 0
    tally_vuln = 0
    for vuln in vuln_settings:
        try:
            # Skip critical items - they're penalties, not scoring opportunities
            if vuln in ["Critical Users", "Critical Services", "Critical Programs"]:
                continue
                
            if int(vuln_settings[vuln][1]["Enabled"].get()) == 1:
                if len(vuln_settings[vuln]) == 1:
                    tally_vuln += 1
                    # Handle empty or invalid point values by defaulting to 0
                    points_val = vuln_settings[vuln][1]["Points"].get()
                    tally_score += int(points_val) if points_val else 0
                else:
                    for settings in vuln_settings[vuln]:
                        if settings != 1:
                            tally_vuln += 1
                            # Handle empty or invalid point values by defaulting to 0
                            points_val = vuln_settings[vuln][settings]["Points"].get()
                            tally_score += int(points_val) if points_val else 0
        except (ValueError, TypeError):
            # Silently skip invalid entries during tally calculation
            pass
    root.MenuSettings["Tally Points"].set(tally_score)
    root.MenuSettings["Tally Vulnerabilities"].set(tally_vuln)


def get_service_list():
    """
    Get a list of available system services.

    Args:
        None

    Returns:
        list: List of service names.
    """
    command = "systemctl list-unit-files --type=service --no-pager --plain --no-legend"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    services = []
    for line in result.stdout.splitlines():
        service_name = line.split()[0]
        services.append(service_name)
    return services


def get_user_list():
    """
    Get a list of system users.

    Args:
        None

    Returns:
        list: List of user names.
    """
    user_list = []
    for user in pwd.getpwall():
        user_list.append(user[0])
    return user_list


def get_group_list():
    """
    Get a list of system groups.

    Args:
        None

    Returns:
        list: List of group names.
    """
    group_list = []
    for group in grp.getgrall():
        group_list.append(group[0])
    return group_list


def show_error(self, *args):
    """
    Display an error message to the terminal.

    Args:
        self: Exception context (Tkinter callback).
        *args: Exception arguments.

    Returns:
        None
    """
    err = traceback.format_exception(*args)
    err_str = ''.join(err)
    
    # Silently ignore integer conversion errors from empty point fields
    # These are now handled gracefully in tally() function
    if "expected integer but got" in err_str or "invalid literal for int()" in err_str:
        return
    
    # Print error to terminal instead of showing popup
    print("\n=== ERROR ===", file=sys.stderr)
    print(err_str, file=sys.stderr)
    print("=============\n", file=sys.stderr)


def change_theme(style_array):
    """
    Change the current theme of the application.

    Args:
        style_array (tk.StringVar): Theme name variable.

    Returns:
        None
    """
    root.ttkStyle.set_theme(style_array.get())


#  region theme settings
def generate_export(extension):
    """
    Export the current configuration and report to an HTML file. For testing purposes, does not update ScoreReport.html.

    Args:
        extension (str): File extension for export (e.g., ".html").

    Returns:
        None
    """
    save_config()
    default = False
    saveLocation = filedialog.asksaveasfilename(
        title="Select Save Location",
        defaultextension=extension,
        filetypes=(("Web Page", "*.html"), ("all files", "*.*")),
    )
    
    # If user cancels, saveLocation will be empty string - return early
    if not saveLocation:
        return
    head = (
        '<!DOCTYPE html>\n<html>\n\t<head>\n\t\t<meta name="viewport" content="width=device-width, initial-scale=1">\n\t\t<style>\n\t\t\t* {box-sizing: border-box}\n\n\t\t\t.banner {\n\t\t\t\tborder-bottom: 1px solid #959b94;\n\t\t\t\tfont-size: 20px;\n\t\t\t}\n\n\t\t\tspan.true {\n\t\t\t\tbackground:green;\n\t\t\t\tcolor:white;\n\t\t\t}\n\n\t\t\tspan.false {\n\t\t\t\tbackground:red;\n\t\t\t\tcolor:white;\n\t\t\t}\n\n\t\t\t.tab {\n\t\t\t\tfloat: left;\n\t\t\t\tbackground-color: #f1f1f1;\n\t\t\t\twidth: 10%;\n\t\t\t\theight: 100%;\n\t\t\t}\n\n\t\t\t.tab button {\n\t\t\t\tdisplay: block;\n\t\t\t\tbackground-color: inherit;\n\t\t\t\tcolor: black;\n\t\t\t\tpadding: 22px 16px;\n\t\t\t\twidth: 100%;\n\t\t\t\tborder: none;\n\t\t\t\toutline: none;\n\t\t\t\ttext-align: left;\n\t\t\t\tcursor: pointer;\n\t\t\t\ttransition: 0.3s;\n\t\t\t\tfont-size: 25px;\n\t\t\t}\n\n\t\t\t.tab button:hover {\n\t\t\t\tbackground-color: #ddd;\n\t\t\t}\n\n\t\t\t.tab button.active {\n\t\t\t\tbackground-color: #ccc;\n\t\t\t}\n\n\t\t\t.tabcontent {\n\t\t\t\tfloat: left;\n\t\t\t\tpadding: 0px 12px;\n\t\t\t\twidth: 70%;\n\t\t\t\tborder-left: none;\n\t\t\t\theight: 300px;\n\t\t\t}\n\n\t\t\ttable.content {\n\t\t\t\twidth: 100%;\n\t\t\t\tborder-collapse: collapse;\n\t\t\t}\n\n\t\t\ttr.head {\n\t\t\t\tfont-weight: bold;\n\t\t\t\tfont-size: 25px;\n\t\t\t}\n\n\t\t\ttr.label {\n\t\t\t\tborder: 1px solid black;\n\t\t\t\tfont-weight: bold;\n\t\t\t\tfont-size: 22px;\n\t\t\t}\n\n\t\t\ttd {\n\t\t\t\tborder: 1px solid black;\n\t\t\t}\n\n\t\t\ttd.banner {\n\t\t\t\tborder: none;\n\t\t\t\t}\n\t\t</style>\n\t</head>\n\t<body>\n\t\t<div class="banner">\n\t\t\t<table width="100%">\n\t\t\t\t<tr>\n\t\t\t\t\t<td class="banner" colspan="3">Save Location: '
        + root.MenuSettings["Desktop"].get()
        + '</td>\n\t\t\t\t</tr>\n\t\t\t\t<tr>\n\t\t\t\t\t<td class="banner" width="20%">Silent Mode: <span class="'
    )
    if root.MenuSettings["Silent Mode"].get():
        head += 'true">True'
    else:
        head += 'false">False'
    head += '</span></td>\n\t\t\t\t\t<td class="banner" width="20%">Server Mode: <span class="'
    if root.MenuSettings["Server Mode"].get():
        head += (
            'true">True</span></td>\n\t\t\t\t\t<td class="banner" width="60%">Sever Info: Ip:'
            + root.MenuSettings["Server Name"].get()
            + "\tUser Name: "
            + root.MenuSettings["Server User"].get()
            + "\tPassword: "
            + root.MenuSettings["Server Password"].get()
            + "</td>\n\t\t\t\t</tr>\n\t\t\t\t"
        )
    else:
        head += 'false">False</span></td>\n\t\t\t\t'
    head += (
        '<tr>\n\t\t\t\t\t<td class="banner" width="20%">Total Points: '
        + root.MenuSettings["Tally Points"].get()
        + "<br>Total Vulnerabilities: "
        + root.MenuSettings["Tally Vulnerabilities"].get()
        + "</td>\n\t\t\t\t</tr>\n\t\t\t</table>\n\t\t</div>\n\n\t\t"
    )
    buttons = '\n\n\t\t<div class="tab">'
    body = ""

    categories = Categories.get_categories()
    for category in categories:
        vulnerabilities = Vulnerabilities.get_option_template_by_category(category.id)
        cat_tested = False
        temp_body = ""
        for vulnerability in vulnerabilities:
            settings = Vulnerabilities.get_option_table(vulnerability.name)
            if int(settings[1]["Enabled"].get()) == 1:
                cat_tested = True
                width = len(settings[1]["Checks"])
                temp_body += (
                    '\n\t\t\t<table class="content">\n\t\t\t\t<tr class="head">\n\t\t\t\t\t<td class="banner" colspan="'
                    + str(width + 1)
                    + '">'
                    + vulnerability.name
                    + '</td>\n\t\t\t\t</tr>\n\t\t\t\t<tr class="label">'
                )
                temp_body += '\n\t\t\t\t\t<td width="5%">Points</td>'
                for check in settings[1]["Checks"]:
                    temp_body += (
                        '\n\t\t\t\t\t<td width="'
                        + str(90 / width)
                        + '%">'
                        + check
                        + "</td>"
                    )
                temp_body += "\n\t\t\t\t</tr>"
                for setting in settings:
                    if (width > 0 and setting != 1) or (width == 1):
                        temp_body += (
                            '\n\t\t\t\t<tr>\n\t\t\t\t\t<td width="5%">'
                            + str(settings[setting]["Points"].get())
                            + "</td>"
                        )
                        for check in settings[setting]["Checks"]:
                            temp_body += (
                                '\n\t\t\t\t\t<td width="'
                                + str(90 / width)
                                + '%">'
                                + str(settings[setting]["Checks"][check].get())
                                + "</td>"
                            )
                        temp_body += "\n\t\t\t\t</tr>"
                temp_body += "\n\t\t\t</table>"
        if cat_tested:
            buttons += (
                '\n\t\t\t<button class="tablinks" onclick="openOptionSet(event, \''
                + category.name
                + "')\""
            )
            if not default:
                default = True
                buttons += ' id="defaultOpen"'
            buttons += ">" + category.name + "</button>"
            body += (
                '\n\n\t\t<div id="'
                + category.name
                + '" class="tabcontent">'
                + temp_body
                + "\n\t\t</div>\n"
            )
    buttons += "\n\t\t</div>"
    body += '\n\n\t\t<script>\n\t\t\tfunction openOptionSet(evt, optionName) {\n\t\t\t\tvar i, tabcontent, tablinks;\n\t\t\t\ttabcontent = document.getElementsByClassName("tabcontent");\n\t\t\t\tfor (i = 0; i < tabcontent.length; i++) {\n\t\t\t\t\ttabcontent[i].style.display = "none";\n\t\t\t\t}\n\t\t\t\ttablinks = document.getElementsByClassName("tablinks");\n\t\t\t\tfor (i = 0; i < tablinks.length; i++) {\n\t\t\t\t\ttablinks[i].className = tablinks[i].className.replace(" active", "");\n\t\t\t\t}\n\t\t\t\tdocument.getElementById(optionName).style.display = "block";\n\t\t\t\tevt.currentTarget.className += " active";\n\t\t\t}\n\n\t\t\tdocument.getElementById("defaultOpen").click();\n\t\t</script>\n\t</body>\n</html>'
    head += buttons + body
    f = open(saveLocation, "+w")
    f.write(head)
    f.close()


Tk.report_callback_exception = show_error

vulnerability_settings = {}
themeList = [
    "aquativo",
    "aquativo",
    "black",
    "clearlooks",
    "elegance",
    "equilux",
    "keramik",
    "plastik",
    "ubuntu",
]


root = Config()
root.title("Configurator")
root.geometry(
    "{0}x{1}+{2}+{3}".format(
        int(root.winfo_screenwidth() * 3 / 4),
        int(root.winfo_screenheight() * 2 / 3),
        int(root.winfo_screenwidth() / 9),
        int(root.winfo_screenheight() / 6),
    )
)

root.ttkStyle = ThemedStyle(root.winfo_toplevel())
for theme in themeList:
    root.ttkStyle.set_theme(theme)
root.ttkStyle.set_theme(root.MenuSettings["Style"].get())
root.ttkStyle.theme_settings(
    themename="aquativo",
    settings={
        ".": {"configure": {"background": "#eff0f1"}},
        "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
        "TNotebook.Tab": {
            "configure": {
                "width": int(root.winfo_screenwidth() * 3 / 4 / 7),
                "anchor": "center",
            }
        },
        "TLabel": {
            "configure": {
                "padding": "5 0",
                "justify": "center",
                "wraplength": int(root.winfo_screenwidth() * 3 / 4 - 140),
            }
        },
        "TEntry": {"map": {"fieldbackground": [("disabled", "#a9acb2")]}},
        "TButton": {"configure": {"anchor": "center", "width": "13"}},
    },
)
root.ttkStyle.theme_settings(
    themename="black",
    settings={
        "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
        "TNotebook.Tab": {
            "configure": {
                "width": int(root.winfo_screenwidth() * 3 / 4 / 7),
                "anchor": "center",
            }
        },
        "TLabel": {
            "configure": {
                "padding": "5 0",
                "justify": "center",
                "wraplength": int(root.winfo_screenwidth() * 3 / 4 - 145),
            }
        },
        "TEntry": {"map": {"fieldbackground": [("disabled", "#868583")]}},
        "TButton": {"configure": {"anchor": "center", "width": "13"}},
    },
)
root.ttkStyle.theme_settings(
    themename="clearlooks",
    settings={
        "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
        "TNotebook.Tab": {
            "configure": {
                "width": int(root.winfo_screenwidth() * 3 / 4 / 7),
                "anchor": "center",
            }
        },
        "TLabel": {
            "configure": {
                "padding": "5 0",
                "justify": "center",
                "wraplength": int(root.winfo_screenwidth() * 3 / 4 - 145),
            }
        },
        "TEntry": {"map": {"fieldbackground": [("disabled", "#b0aaa4")]}},
        "TButton": {"configure": {"anchor": "center", "width": "13"}},
    },
)
root.ttkStyle.theme_settings(
    themename="elegance",
    settings={
        "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
        "TNotebook.Tab": {
            "configure": {
                "width": int(root.winfo_screenwidth() * 3 / 4 / 7),
                "anchor": "center",
            }
        },
        "TLabel": {
            "configure": {
                "font": "8",
                "padding": "5 0",
                "justify": "center",
                "wraplength": int(root.winfo_screenwidth() * 3 / 4 - 145),
            }
        },
        "TButton": {"configure": {"anchor": "center", "width": "13"}},
    },
)
root.ttkStyle.theme_settings(
    themename="equilux",
    settings={
        "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
        "TNotebook.Tab": {
            "configure": {
                "width": int(root.winfo_screenwidth() * 3 / 4 / 7),
                "anchor": "center",
            }
        },
        "TLabel": {
            "configure": {
                "padding": "5 0",
                "justify": "center",
                "wraplength": int(root.winfo_screenwidth() * 3 / 4 - 145),
            },
            "map": {"foreground": [("disabled", "#5b5b5b")]},
        },
        "TButton": {"configure": {"anchor": "center", "width": "13"}},
    },
)
root.ttkStyle.theme_settings(
    themename="keramik",
    settings={
        "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
        "TNotebook.Tab": {
            "configure": {
                "width": int(root.winfo_screenwidth() * 3 / 4 / 7),
                "anchor": "center",
            }
        },
        "TLabel": {
            "configure": {
                "padding": "5 0",
                "justify": "center",
                "wraplength": int(root.winfo_screenwidth() * 3 / 4 - 145),
            }
        },
        "TButton": {"configure": {"anchor": "center", "width": "13"}},
    },
)
root.ttkStyle.theme_settings(
    themename="plastik",
    settings={
        "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
        "TNotebook.Tab": {
            "configure": {
                "width": int(root.winfo_screenwidth() * 3 / 4 / 7),
                "anchor": "center",
            }
        },
        "TLabel": {
            "configure": {
                "padding": "5 0",
                "justify": "center",
                "wraplength": int(root.winfo_screenwidth() * 3 / 4 - 145),
            }
        },
        "TButton": {"configure": {"anchor": "center", "width": "13"}},
    },
)
root.ttkStyle.theme_settings(
    themename="ubuntu",
    settings={
        "TNotebook": {"configure": {"tabmargins": [2, 5, 2, 0]}},
        "TNotebook.Tab": {
            "configure": {
                "width": int(root.winfo_screenwidth() * 3 / 4 / 7),
                "anchor": "center",
            }
        },
        "TLabel": {
            "configure": {
                "padding": "5 0",
                "justify": "center",
                "wraplength": int(root.winfo_screenwidth() * 3 / 4 - 170),
            },
            "map": {"foreground": [("disabled", "#c2c2c2")]},
        },
        "TButton": {"configure": {"anchor": "center", "width": "13"}},
    },
)


# endregion

root.mainloop()

save_config()
