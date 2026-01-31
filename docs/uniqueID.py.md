# uniqueID.py Documentation

## Overview
The `uniqueID.py` module provides a graphical user interface for collecting user credentials and team information for the CSEL scoring engine. It creates a simple form-based interface that allows users to input their team details, which are then used for score reporting and FTP uploads.

## Purpose
This module serves as the user credential collection system that:
- Provides a user-friendly GUI for inputting team information
- Validates that all required fields are completed
- Saves user credentials to system files
- Configures FTP upload settings for score reporting
- Generates unique filenames for score reports

## File Details

### Imports and Dependencies
```python
import fileinput
from tkinter import *
from datetime import date
```

### Global Variables
- `teamID`: StringVar for team name input
- `studentID`: StringVar for student name input
- `schoolID`: StringVar for school name input
- `teacherID`: StringVar for teacher name input
- `grade`: StringVar for grade level input

## Core Functions

### `retrieve()`
**Purpose**: Main function that processes user input and saves credentials

**Parameters**: None

**Returns**: None

**Functionality**:
1. **Input Validation**: Checks that all required fields are filled
2. **Credential Saving**: Writes user information to `/usr/local/bin/uniqueId`
3. **Filename Generation**: Creates unique filename with date and team info
4. **FTP Configuration**: Sets up FTP upload parameters
5. **File Processing**: Replaces placeholders in FTP script with actual values

**Input Validation**:
```python
if (
    str(teamID.get()) != ""
    and str(studentID.get()) != ""
    and str(schoolID.get()) != ""
    and str(teacherID.get()) != ""
    and str(grade.get()) != ""
):
```

**Credential File Format**:
The function creates a CSV-style file at `/usr/local/bin/uniqueId` with:
- Team Name, [team_name],
- Student Name, [student_name],
- School Name, [school_name],
- Teacher Name, [teacher_name],
- Grade, [grade],

**Filename Generation**:
Creates a unique filename using:
- Current date (YYYY-MM-DD format)
- Team name (spaces removed)
- Student name (spaces removed)
- "ScoreReport.csv" suffix

**FTP Configuration**:
- Reads FTP settings from `FTP.txt`
- Replaces placeholders in `/usr/local/bin/csel_SCORING_REPORT_FTP_DO_NO_TOUCH`
- Updates server name, username, password, and filename

**Error Handling**:
- Displays error dialog if any field is empty
- Provides clear instructions for completion
- Allows user to retry after filling missing fields

### `center(master)`
**Purpose**: Centers the GUI window on the screen

**Parameters**:
- `master`: Tkinter window object to center

**Returns**: None

**Functionality**:
- Gets screen dimensions
- Calculates window position for center placement
- Applies geometry settings to center the window

**Implementation**:
```python
def center(master):
    screen_w = master.winfo_screenwidth()
    screen_h = master.winfo_screenheight()
    size = tuple(int(_) for _ in master.geometry().split("+")[0].split("x"))
    x = screen_w / 2 - size[0]
    y = screen_h / 2 - size[1]
    master.geometry("+%d+%d" % (x, y))
```

## GUI Components

### Main Window Setup
```python
root = Tk()
root.title("Unique ID")
center(root)
```

### Input Fields
The GUI creates five input fields:
1. **Team Name**: Text entry for team identifier
2. **Student Name**: Text entry for student identifier
3. **School Name**: Text entry for school identifier
4. **Teacher Name**: Text entry for teacher identifier
5. **Grade**: Text entry for grade level

### Layout Structure
- **Frame-based layout**: Uses Tkinter Frame for organization
- **Grid positioning**: Uses grid() for precise widget placement
- **Consistent styling**: Uses Verdana font with bold labels
- **Submit button**: Triggers the retrieve() function

### Widget Configuration
```python
Label(frame, text="Team Name: ", font=("Verdana", 10, "bold"), width=20).grid(row=1, column=0)
Entry(frame, textvariable=teamID, width=20).grid(row=1, column=1)
```

## File Operations

### Credential Storage
**File Path**: `/usr/local/bin/uniqueId`
**Format**: CSV-style with comma separators
**Purpose**: Stores user credentials for score reporting

### Filename Generation
**File Path**: `/usr/local/bin/name`
**Content**: Generated filename for score reports
**Format**: `YYYY-MM-DD[TeamName][StudentName]ScoreReport.csv`

### FTP Configuration
**Source**: `FTP.txt` (contains server settings)
**Target**: `/usr/local/bin/csel_SCORING_REPORT_FTP_DO_NO_TOUCH`
**Process**: Replaces placeholders with actual values

## Error Handling

### Input Validation
- Checks all fields are non-empty
- Displays error dialog with instructions
- Allows user to correct and retry

### Error Dialog
```python
warn = Tk()
warn.title("Error")
center(warn)
warnF = Frame(warn)
warnF.pack()
Label(
    warnF,
    text="Please fill in all of the boxes with the correct information for accurate scoring.",
    font=("Verdana", 10, "bold"),
).pack()
Button(warnF, text="OK", command=lambda: warn.destroy()).pack()
```

## Integration with CSEL

### Score Reporting
- Provides team identification for score reports
- Enables personalized score tracking
- Supports multiple team members

### FTP Upload
- Configures automatic score upload
- Enables remote score monitoring
- Supports competition scoring systems

### File Management
- Creates system files for other components
- Provides unique identifiers for reports
- Enables proper file organization

## Usage Context

### Competition Setup
1. User runs the uniqueID.py script
2. Fills in team and personal information
3. Submits form to save credentials
4. System is ready for scoring

### Score Reporting
- Generated filenames include team identification
- FTP uploads are configured with team info
- Reports are properly labeled and organized

## Security Considerations

### File Permissions
- Creates files in system directories
- Requires appropriate permissions
- Stores sensitive information securely

### Input Validation
- Prevents empty submissions
- Ensures data completeness
- Provides user feedback

## Dependencies
- **Tkinter**: For GUI components
- **datetime**: For date-based filename generation
- **fileinput**: For file operations

## Limitations
- Requires Tkinter for GUI
- Limited to single user per session
- No data persistence between sessions
- Basic error handling

## Related Files
- **FTP.txt**: Contains FTP server configuration
- **csel_SCORING_REPORT_FTP_DO_NO_TOUCH**: FTP upload script template
- **scoring_engine.py**: Uses generated credentials for reporting
- **configurator.py**: May reference user information

## Future Enhancements
- Data validation and sanitization
- Multiple user support
- Configuration persistence
- Enhanced error handling
- Input formatting options
