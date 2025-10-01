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
    # impliment this one
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
        "Definition": "Enable this to score the competitor for setting the minimum password age to 30, 45, or 60.",
        "Category": "Local Policy",
    },
    "Maximum Password Age": {
        "Definition": "Enable this to score the competitor for setting the maximum password age to 60, 75, or 90.",
        "Category": "Local Policy",
    },
    "Minimum Password Length": {
        "Definition": "Enable this to score the competitor for setting the minimum password length between 10 and 20.",
        "Category": "Local Policy",
    },
    "Maximum Login Tries": {
        "Definition": "Enable this to score the competitor for setting the maximum login tries between 5 and 10.",
        "Category": "Local Policy",
    },
    "Lockout Duration": {
        "Definition": "Enable this to score the competitor for setting the lockout duration to 30.",
        "Category": "Local Policy",
    },
    "Lockout Reset Duration": {
        "Definition": "Enable this to score the competitor for setting the lockout reset duration to 30.",
        "Category": "Local Policy",
    },
    "Password History": {
        "Definition": "Enable this to score the competitor for setting the password history between 5 and 10.",
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
        "Checks": "Program Name:Str, Version:Str",
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
        "Definition": "Enable this to penalize",
        "Checks": "Program Name:Str,Service Start Mode:Str",
        "Category": "Program Management",
    },
    "Update Check Period": {
        "Definition": "What has the update check period been set to? (apt/apt.conf.d/10periodic) \nPlease set Occurance as [minute] [hour] [day of month] [month] [day of week]",
        "Category": "Program Management",
    },
    # "Update Auto Install": {"Definition": 'Automaticaly download and install security updates',
    #                       "Category": 'Program Management'},
    "Forensic": {
        "Definition": "Enable this to score the competitor for answering forensic a question.",
        "Description": 'This will score the competitor for answering forensic questions. To add more questions press the "Add" button. To remove questions press the "X" button next to the question you want to remove. The location will automatically be set to the desktop of that is set in the main menu.',
        "Checks": "Question:Str,Answers:Str,Location:Str",
        "Category": "File Management",
    },
    "Bad File": {
        "Definition": "Enable this to score the competitor for deleting a file.",
        "Description": 'This will score the competitor for deleting a file. To add more files press the "Add" button. To remove a file press the "X" button next to the file you want to remove. Keep it one file per line.',
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
        "Description": 'This will score the competitor for adding text to a file. To add more files press the "Add" button. To remove a file press the "X" button next to the file you want to remove. Keep it one file per line.',
        "Checks": "Text to Add:Str,File Path:Str",
        "Category": "File Management",
    },
    "Remove Text From File": {
        "Definition": "Enable this to score the competitor for removing text from a file.",
        "Description": 'This will score the competitor for removing text from a file. To add more files press the "Add" button. To remove a file press the "X" button next to the file you want to remove. Keep it one file per line.',
        "Checks": "Text to Remove:Str,File Path:Str",
        "Category": "File Management",
    },
    "File Permissions": {
        "Definition": "(WIP)Enable this to score the competitor for changing the permissions a user has on a file.",
        "Description": '(WIP)This will score the competitor for changing the permissions a user has on a file. To add more files press the "Add" button. To remove a file press the "X" button next to the file you want to remove. Keep it one file per line.',
        "Checks": "Users to Modify:Str,Permissions:Str,File Path:Str",
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
    """A pure Tkinter scrollable frame that actually works!
    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    """

    def __init__(self, parent, *args, **kw):
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
            # update the scrollbars to match the size of the inner frame
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


# this class declares most of our ui, pulling from the db, it generates a checkbox under the right category
class Config(Tk):
    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        # elevated privalege is needed to run our commands, it asks on boot
        # fix Check- idk if this works but I think it should
        # turn off before PUSH
        if not "SUDO_UID" in os.environ.keys():
            switch = messagebox.askyesno(
                "Root Access Required",
                "You need to be Admin to Write to Config. Please relaunch the confiturator as Administrator.",
            )
            if switch:
                sys.exit(1)
            return

        nb = ttk.Notebook(self)
        MainPage = ttk.Frame(nb)

        self.MenuSettings = Settings.get_settings()
        temp_style = self.MenuSettings["Style"].get()

        # ttk.Button(MainPage, text='Save', command=lambda: (save_config())).grid(sticky=EW)
        #
        ttk.Label(
            MainPage,
            text="Leave blank if the current logged in users is the main otherwise enter the path manually.",
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
        ttk.Label(
            MainPage,
            text="Created by Shaun Martin, Anthony Nguyen, Bryan Ortiz and Minh-Khoi Do",
        ).grid(row=10, column=0, columnspan=4, sticky=SW)
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
            pageIn.grid_columnconfigure(1, weight=1)
            ttk.Label(pageIn, text=category.description, padding="10 5").grid(
                row=0, column=0, columnspan=3
            )
            ttk.Label(pageIn, text=category.description, padding="10 5").grid(
                row=0, column=0, columnspan=3
            )
            ttk.Label(pageIn, text="Vulnerabilities", font="Verdana 12 bold").grid(
                row=1, column=0, stick=W
            )
            ttk.Label(pageIn, text="Points", font="Verdana 12 bold").grid(
                row=1, column=2
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
        ttk.Checkbutton(frame, text=name, variable=entry[1]["Enabled"]).grid(
            row=row, column=0, stick=W
        )
        ttk.Label(
            frame, text=Vulnerabilities.get_option_template(name).definition
        ).grid(row=row, column=1, stick=W)
        if len(entry[1]["Checks"]) > 0:
            ttk.Button(
                frame,
                text="Modify",
                command=lambda: self.modify_settings(name, entry, return_frame),
            ).grid(row=row, column=2)
        else:
            Entry(
                frame, width=5, textvariable=entry[1]["Points"], font="Verdana 10"
            ).grid(row=row, column=2)
        ttk.Separator(frame, orient=HORIZONTAL).grid(
            row=row + 1, column=0, columnspan=3, sticky=EW
        )

    def modify_settings(self, name, entry, packing):
        self.pack_slaves()[0].pack_forget()
        modifyPage = VerticalScrolledFrame(self)
        modifyPage.pack(expand=1, fill="both")
        modifyPageList = modifyPage.interior
        modifyPageList.pack(fill=X)
        modifyPageIn = ttk.Frame(modifyPage)
        modifyPageIn.pack(before=modifyPage.canvas, fill=X)
        if entry[1]["Enabled"].get() != 1:
            entry[1]["Enabled"].set(1)
        ttk.Button(
            modifyPageIn,
            text="Save",
            command=lambda: (
                self.pack_slaves()[0].pack_forget(),
                packing.pack(expand=1, fill="both"),
                Vulnerabilities.update_table(name, entry),
            ),
        ).grid(row=0, column=0, sticky=EW)
        ttk.Label(modifyPageIn, text=name + " Modification", font="Verdana 15").grid(
            row=0, column=1, columnspan=len(entry[1]["Checks"])
        )
        ttk.Button(
            modifyPageIn,
            text="Add",
            command=lambda: (add_row(modifyPageList, entry, name)),
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
            ttk.Label(modifyPageIn, text=t, font="Verdana 10 bold").grid(
                row=2, column=i + 1
            )
            r = i + 2
        ttk.Label(modifyPageIn, text="Remove", font="Verdana 10 bold").grid(
            row=2, column=r
        )
        for vuln in entry:
            if vuln != 1:
                load_modify_settings(modifyPageList, entry, name, vuln)

    def generate_report(self, frame):
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
    modifyPageListRow = ttk.Frame(frame)
    modifyPageListRow.pack(fill=X)
    ttk.Entry(modifyPageListRow, width=10, textvariable=entry[idx]["Points"]).grid(
        row=0, column=0
    )
    c = 0
    for r, t in enumerate(entry[idx]["Checks"]):
        r += 1
        if t == "File Path":
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
                *["Running", "Running", "Stopped"],
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Service Start Mode":
            modifyPageListRow.grid_columnconfigure(r, weight=1)
            ttk.OptionMenu(
                modifyPageListRow,
                entry[idx]["Checks"][t],
                *["Auto", "Auto", "Manual", "Disabled"],
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
    idx = Vulnerabilities.add_to_table(name).id
    entry.update({idx: Vulnerabilities.get_option_table(name)[idx]})

    mod_frame = ttk.Frame(frame)
    mod_frame.pack(fill=X)

    ttk.Entry(mod_frame, width=10, textvariable=entry[idx]["Points"]).grid(
        row=0, column=0
    )
    c = 0
    for r, t in enumerate(entry[idx]["Checks"]):
        r += 1
        if t == "File Path":
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
                mod_frame, entry[idx]["Checks"][t], *["Running", "Running", "Stopped"]
            ).grid(row=0, column=r, sticky=EW)
            c = r + 1
        elif t == "Service Start Mode":
            mod_frame.grid_columnconfigure(r, weight=1)
            ttk.OptionMenu(
                mod_frame,
                entry[idx]["Checks"][t],
                *["Auto", "Auto", "Manual", "Disabled"],
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
        ),
    ).grid(row=0, column=c, sticky=W)


def remove_row(entry, idx, widget):
    del entry[idx]
    widget.destroy()


def set_file_or_directory(var, switch, mode):
    if switch.get() == 1:
        file = filedialog.askdirectory()
        var["File Path"].set(file)
    else:
        file = filedialog.askopenfilename()
        var["File Path"].set(file)
    if mode == "File Permissions":
        status = os.stat(file)
        current = bin(status.st_mode)[-9:]
        for idx, perm in enumerate(current):
            var["Permissions"][idx].set(int(perm))


# check
def create_forensic():
    qHeader = (
        "This is a forensics question. Answer it below\n------------------------\n"
    )
    qFooter = "\n\nANSWER: <TypeAnswerHere>"
    if vuln_settings["Forensic"][1]["Enabled"].get() == 1:
        q_num = 1
        for question in vuln_settings["Forensic"]:
            if question != 1:
                location = vuln_settings["Forensic"][question]["Checks"][
                    "Location"
                ].get()
                if location == "":
                    vuln_settings["Forensic"][question]["Checks"]["Location"].set(
                        str(root.MenuSettings["Desktop"].get())
                        + "Forensic Question "
                        + str(q_num)
                        + ".txt"
                    )
                    location = vuln_settings["Forensic"][question]["Checks"][
                        "Location"
                    ].get()
                    q_num += 1
                g = open(location, "w+")
                g.write(
                    qHeader
                    + vuln_settings["Forensic"][question]["Checks"]["Question"].get()
                    + qFooter
                )
                g.close()


def resource_path(relative_path):
    """https://stackoverflow.com/questions/7674790/bundling-data-files-with-pyinstaller-onefile/13790741#13790741
    Get absolute path to resource, works for dev and for PyInstaller"""
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

    save_config()

    # check
    output_directory = "/etc/CYBERPATRIOT/"
    web_directory = "/var/www/CYBERPATRIOT"
    current_directory = os.getcwd()
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    if not os.path.exists(web_directory):
        os.makedirs(web_directory)
    shutil.copy(
        resource_path("scoring_engine"),
        os.path.join(output_directory, "scoring_engine"),
    )
    shutil.copy(
        resource_path("ScoringEngineLinuxBig.png"),
        output_directory + "ScoringEngineLinuxBig.png",
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
    os.chmod(output_directory + "scoring_engine", 0o777)
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

    cron = CronTab(user=os.environ["USER"])
    command = output_directory + "scoring_engine"
    schedule = "* * * * *"

    # fix / check
    if command not in cron:
        try:
            # Create a new cron job
            job = cron.new(command=command, comment="my_cron_job")

            # Set the schedule for the cron job
            job.setall(schedule)

            # Write the job to the crontab
            job.enable()

            # Write the changes to the crontab
            cron.write()
            job = cron.new(command=command, comment="my_cron_job")
            # Create a new cron job

            # Set the schedule for the cron job
            job.setall("@reboot")

            # Write the job to the crontab
            job.enable()

            # Write the changes to the crontab
            cron.write()
        except subprocess.CalledProcessError as e:
            show_error(e)
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == "scoring_engine":
            sys.exit()
    subprocess.Popen(command, shell=True)
    sys.exit()


# check
def save_config():
    desk = f'/home/{os.environ.get("SUDO_USER")}/Desktop'
    if desk not in root.MenuSettings["Desktop"].get():
        root.MenuSettings["Desktop"].set(
            "/home/" + os.environ.get("SUDO_USER") + "/Desktop/"
        )
    create_forensic()
    tally()
    Settings.update_table(root.MenuSettings)
    for vuln in vuln_settings:
        Vulnerabilities.update_table(vuln, vuln_settings[vuln])
    Vulnerabilities.cleanup()


# score count
def tally():
    # Set tally scores
    tally_score = 0
    tally_vuln = 0
    for vuln in vuln_settings:
        if int(vuln_settings[vuln][1]["Enabled"].get()) == 1:
            if len(vuln_settings[vuln]) == 1:
                tally_vuln += 1
                tally_score += int(vuln_settings[vuln][1]["Points"].get())
            else:
                for settings in vuln_settings[vuln]:
                    if settings != 1:
                        tally_vuln += 1
                        tally_score += int(
                            vuln_settings[vuln][settings]["Points"].get()
                        )
    root.MenuSettings["Tally Points"].set(tally_score)
    root.MenuSettings["Tally Vulnerabilities"].set(tally_vuln)


def get_service_list():
    command = "systemctl list-unit-files --type=service --no-pager --plain --no-legend"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    services = []
    for line in result.stdout.splitlines():
        service_name = line.split()[0]
        services.append(service_name)
    return services


def get_user_list():
    user_list = []
    for user in pwd.getpwall():
        user_list.append(user[0])
    return user_list


def get_group_list():
    group_list = []
    for group in grp.getgrall():
        group_list.append(group[0])
    return group_list


def show_error(self, *args):
    err = traceback.format_exception(*args)
    for i in err:
        if "expected integer but got" in i:
            err = "There is an integer error with one of the points"
    messagebox.showerror("Exception", err)


def change_theme(style_array):
    root.ttkStyle.set_theme(style_array.get())


#  region theme settings
def generate_export(extension):
    save_config()
    default = False
    saveLocation = filedialog.asksaveasfilename(
        title="Select Save Location",
        defaultextension=extension,
        filetypes=(("Web Page", "*.html"), ("all files", "*.*")),
    )
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
                    if (width > 0 and setting != 1) or (width == 0):
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
