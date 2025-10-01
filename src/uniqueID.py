import fileinput
from tkinter import *
from datetime import date


def retrieve():
    if (
        str(teamID.get()) != ""
        and str(studentID.get()) != ""
        and str(schoolID.get()) != ""
        and str(teacherID.get()) != ""
        and str(grade.get()) != ""
    ):
        f = open("/usr/local/bin/uniqueId", "w+")
        line1 = "Team Name," + str(teamID.get()) + ",\n"
        line2 = "Student Name," + str(studentID.get()) + ",\n"
        line3 = "School Name," + str(schoolID.get()) + ",\n"
        line4 = "Teacher Name," + str(teacherID.get()) + ",\n"
        line5 = "Grade," + str(grade.get()) + ",\n"
        for line in (line1, line2, line3, line4, line5):
            f.write(line)
        f.close()
        today = date.today()
        g = open("/usr/local/bin/name", "w+")
        name = (
            str(today)
            + str(teamID.get()).replace(" ", "")
            + str(studentID.get()).replace(" ", "")
            + "ScoreReport.csv"
        )
        g.write(name)
        g.close()
        with open("FTP.txt") as f:
            content = f.read().splitlines()
        f.close()
        # Read in the file
        with open("/usr/local/bin/csel_SCORING_REPORT_FTP_DO_NO_TOUCH", "r") as file:
            filedata = file.read()

        # Replace the target string
        filedata = filedata.replace("#SERVER#", content[0].replace("serverName=", ""))
        filedata = filedata.replace("#USER#", content[1].replace("userName=", ""))
        filedata = filedata.replace("#PASSWORD#", content[2].replace("password=", ""))
        filedata = filedata.replace("#FILENAME#", name)

        # Write the file out again
        with open("/usr/local/bin/csel_SCORING_REPORT_FTP_DO_NO_TOUCH", "w") as file:
            file.write(filedata)
        root.destroy()
    else:
        warn = Tk()
        warn.title("Error")
        center(warn)
        warnF = Frame(warn)
        warnF.pack()
        Label(
            warnF,
            text="Please fill in all of the boxes with the corect information for accurate scoring.",
            font=("Verdana", 10, "bold"),
        ).pack()
        Button(warnF, text="OK", command=lambda: warn.destroy()).pack()


def center(master):
    screen_w = master.winfo_screenwidth()
    screen_h = master.winfo_screenheight()
    size = tuple(int(_) for _ in master.geometry().split("+")[0].split("x"))
    x = screen_w / 2 - size[0]
    y = screen_h / 2 - size[1]
    master.geometry("+%d+%d" % (x, y))


root = Tk()
root.title("Unique ID")
center(root)
teamID = StringVar()
studentID = StringVar()
schoolID = StringVar()
teacherID = StringVar()
grade = StringVar()
frame = Frame(root)
frame.pack()
Label(
    frame,
    text="Enter your credentials for the scoreboard",
    font=("Verdana", 10, "bold"),
).grid(row=0, column=0, columnspan=2)
Label(frame, text="Team Name: ", font=("Verdana", 10, "bold"), width=20).grid(
    row=1, column=0
)
Entry(frame, textvariable=teamID, width=20).grid(row=1, column=1)
Label(frame, text="Student Name: ", font=("Verdana", 10, "bold"), width=20).grid(
    row=2, column=0
)
Entry(frame, textvariable=studentID, width=20).grid(row=2, column=1)
Label(frame, text="School Name: ", font=("Verdana", 10, "bold"), width=20).grid(
    row=3, column=0
)
Entry(frame, textvariable=schoolID, width=20).grid(row=3, column=1)
Label(frame, text="Teacher Name: ", font=("Verdana", 10, "bold"), width=20).grid(
    row=4, column=0
)
Entry(frame, textvariable=teacherID, width=20).grid(row=4, column=1)
Label(frame, text="Grade: ", font=("Verdana", 10, "bold"), width=20).grid(
    row=5, column=0
)
Entry(frame, textvariable=grade, width=20).grid(row=5, column=1)
Button(frame, text="Submit", command=retrieve).grid(row=6, column=0, columnspan=2)
frame.update_idletasks()

root.mainloop()
