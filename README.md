# CSEL
## Cyberpatriot Scoring Engine: Linux

CSEL is a scoring engine written in Python(currently python 3.12.3) for scoring Linux CyberPatriot-like images. It is configured by adding scoring options into the save_data.db and running the scoringEngine executable. It now includes a web page Score Report. It works with Ubuntu.

*If making changes, please look at **DeveloperGuide.md** for more information*

## Scorable Actions
### Gaining Points
- Deleting "bad" users
- Creating new "good" users
- Changing  users passwords
- Adding users to appropriate groups
- Removing users from groups
- Turning on the firewall
- Opening a certain port 
- Closing a certain port 
- Having a minimum password age be **X** or older 
- Having a maximum password age be **X** or younger  
- Having a minimum password length be **X** or longer 
- Changing the maximum number of login attempts **X** attempts 
- Changing the password lockout duration to **X** seconds
- Changing  the lockout Reset Duration to **X** seconds
- Remember the last **X** passwords
- Installing auditd and enabling it
- Disabling the SSH root login
- Installing a certain package or program that is required per README.txt
- Removing possibly malicious software
- Having a service properly set per the README.txt
- Answering any a question in Forensics Question txt.
- Uninstalling or deleting any file from a chosen location
- Confirming that the SSH hosts file is cleared
- Adding text to a file*
- Removing text from a file*
- Giving a chosen files appropriate permissions per README.txt
- Removing a certain package from booting during the startup sequence
### Losing Points
- Deleting "good" users*
- Deleting a necessary service*
### Notes
- The checking for remove.add text flags check for a complete string existence. If you want a series of strings, it is best to break them into individual flags. a single letter can interfere with the text input.
- The point removal will neutralize if the flag is fixed if points is granted for maintaining flag.
  	ie: Deleting 'John' removes 5 points. Adding him back will return 4 points at a net gain of -1 if points are granted for keeping 'John'. If points are not granted for maintaining 'John' then there is no points returned for adding the user back.

CSEL can be run with "silent misses" which simulates a CyberPatriot round where you have no idea where the points are until you earn them. It can also be run with the silent misses turned off which is helpful when you are debugging or when you have very inexperienced students who might benefit from the help. This mode gives you a general idea where the points are missing. CSEL can also create a scoreboard report that will be placed on the desktop, granting the user access to points gained or lost. 
##Install 

# Installation and Usage
## CLI(required)
1. Set up your image and put your vulnerabilities in place.
2. Clone into image by using: sudo git clone https://github.com/cccnetlab/CSELv2.git
3. (Optional) Set up virtual environment for dependencies:
   * For debian/Ubuntu: **apt install python3.12-venv** 
      * Create venv: **python3 -m venv .venv** 
      * Activate venv: **source .venv/bin/activate**
4. Run `python3 build.py`(**!!!MAKE SURE TO NOT RUN SUDO!!!, will break venv**) to create binaries.
5. Run `sudo bash dep_install.sh` to install all required dependencies.
6. Run the configurator with `sudo .venv/bin/python3.12 src/configurator.py`. Make sure you are in your **HOME DIRECTORY** "CSELV2" or whatever it's named.
7. Configure everything and then press **Commit**. Feel free to delete the configurator binary after.
8. Finally, to set up the scoring machine service, run `sudo .venv/bin/python3.12 service_setup.py`. It should now create a simlink to the binary and run it as a service on startup.  
### **Important Note**: 
If you plan on using the **Check Kernel**, ***Good Program***, or ***Update Program*** vulnerabilities, please refer to the *SPECIAL SETUP* section

**Important Note**: Your students _will_ be able to see the vulnerabilities if you leave the CSEL folder behind or if they cat the executable file that is created in /etc/CYBERPATRIOT. I tell my students where the file is and that they should stay away from it. It is practice, after all.

## Configurator Usage
### Landing Page
![Landing Page](https://github.com/Bryannnnn1313/CSELv2/blob/master/Config%201st%20Screen.png)
   - Commit will launch the ScoringEngine and force close the configurator
   - Checking Silent Miss allows makes the missed points invisible in the Score Report
   - Server Mode allows you set up an FTP server so that the students can compete with each other(WIP)
   - Total Points displays the total points available to the students
   - Total Vulnerabilities shows you the count of Vulnerabilities
### Category Pages
![Category Page](https://github.com/Bryannnnn1313/CSELv2/blob/master/Config%20Account%20Management.png)
   - The Vulnerabilities will be labeled on the left
   - The center describes the Vulnerabilities
   - If there is a Modify tab, there vulnerability may take more than 1 flag and and may need more input
### Modify Page
![Modify Page](https://github.com/Bryannnnn1313/CSELv2/blob/master/Config%20Modify.png)
   - The points will be on the left
   - Center will be any additional inputs needed, A drop down is available, but manual input is possible.
   - If flag is no longer needed, then you can remove it, if you don't it will be added into the database.
### Report Page
![Report Generator](https://github.com/Bryannnnn1313/CSELv2/blob/master/Report%20Generation.png)
   - This page creates an html page with every flag to keep on hand.
### Score Report
![Score Report](https://github.com/Bryannnnn1313/CSELv2/blob/master/ScoreReport.png)
   - This page is created when the the 'Commit' is pressed.
   - If points are gained or lost then a notification will trigger
## Known issues and planned updates
- Removing an empty flag from the modify page may break the Configurator
    - Temporary solution is delete the database and rerun the Configurator

## Special Setup
Due to netlabs having no internet, certain packages have to be cached first. Before you configure any programs you want students to install or update, you must cache them first:

### Good Program:
- Use `sudo apt install -d <pkg>` to download the package ahead of time so they can be installed without internet.
- For snap packages, use `sudo snap download <pkg>` which will download and create the **.assert**
- Run `sudo snap ack package_name.assert` in order to register the security signature, allowing for the eventual offline download.(Technically can be bypassed with the ***--dangerous*** flag during installation)

### Check Kernel:
- Using `sudo apt upgrade -d` will allow you to cache a system update, allowing students to do "sudo apt upgrade" when the time comes.

### Update Program:
- TODO