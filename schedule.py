#!/usr/bin/env python3
# George Nicol
# Version 1.0
#
# OVERVIEW
# ---------------------------
# This is a data entry tool that can lookup student and TCSS names, and it sends an email confirmation.
#
#
# Hello TCSS Admin!
#
# I wrote these tools in an effort to save myself time, I hope you will find them useful.
#
#
# REQUIRED DIRECTORY STRUTURE
# ---------------------------
# /your_STUDENT_HomeDir
#    |
#     --/karla  : prliminary_contact_via_karla.bash, schedule.py, cron_mailer.bash
#         |
#         -- /data  : karla_response_form_letter.txt, TCSS_email_list.txt, scheduled_appointments.txt, SentEmails.log
#
# - preliminary_contact_via_karla.bash uses karla_response_form_letter.txt and SentEmails.log
# - schedule.py uses with TCSS_email_list.txt, SentEmails.log, and scheduled_appointments.txt
# - cron_mailers uses scheduled_appointments.txt and SentEmails.log
#
# This program (long as it is) was purposely kept to one long file in order to have fewer moving parts as
# students are required to set up these tools in their student home dirs. If you are a
# member of TheCAT, please use your student dir not your CAT dir.
#
# DETAILS
# ----------------------------
# reads in scheduling information and writes to csv file. The CSV file is then read via another
# tool which runs on a cron job to automatically remind students and TCSS when their appointment
# is. You have to set up a cron job yourself to do this.
#
# There can be mulitple admins scheduling. As long as the entire system is installed, reminder emails wil go out
# as will initial emails at the time of scheduling. The master schedule (currently google docs) should
# be updated by whoever schedules. This is likely what karla will look at to see what is going on. In the future
# this set of tools could be made to work with goole docs - there is a module you can import to do that.
# Perhaps version 2 will do so.
#

import sys
import re                           # regex
import subprocess as sp             # run bash command line - not just shell utils - from inside python (my fave)
import getpass                      # look up your userid
import smtplib                      # email
from email.mime.text import MIMEText
import time                         # I used regex for the date, but this could be a place to start refactoring
                                    # currently I use this only for email logs

# If you have installed the code and data in the directories described above, you don't need to alter these paths
yourNameHere=getpass.getuser()
emailFile="/u/"+yourNameHere+"/karla/data/TCSS_email_list.txt"
outboundFile="/u/"+yourNameHere+"/karla/data/scheduled_appointments.txt"
SentFile="/u/"+yourNameHere+"/karla/data/SentEmails.log"



# ---------------------------------------------------------------
# Oops is used primarily to redirect program flow
class Oops(Exception):
    def __init__(self,message):
        self.message=message
    def __str__(self):
        return repr(self.message)

# this gets us out
class SeriousProblem(Exception):
    def __init__(self,message):
        self.message=message
    def __str__(self):
        return repr(self.message)


# ---------------------------------------------------------------
# the main event
class Appointment:

    def __init__(self):
        self.classNumber=""         # manual entry  +
        self.date=""                # manual entry  +
        self.dow=""                 # manual entry  +
        self.location=""            # manual entry  +
        self.odinID=""              # ODIN id       +
        self.studentEmail=""        # manual entry - no matching +
        self.studentName=""         # manual entry - no matching +
        self.time=""                # manual entry  +
        self.tutor=""               # matched to file contents +
        self.tutorEmail=""          # derived from file +
    # ---------------------------------------------------------------

    # display
    def display(self):
        print("Student: {0}, TCSS: {1} for CS{2}. Location: {3} at {4} on {5}, {6}".format(self.studentName,
                self.tutor,self.classNumber,self.location,self.time,self.dow,self.date))

    # add entry to the csv file of appointments
    def write(self):
        f=open(outboundFile, 'a')
        f.write(self.studentName+','+self.studentEmail+','+self.date+','+self.dow+','+self.time+','+self.location+','+
                self.classNumber+','+self.tutor+','+self.tutorEmail+'\n')
        f.close()

    # setter - date: mm/dd
    def setDate(self):
        self.date=input("Date to schedule mm/dd: ")
        if not (re.compile("\d{2}\/\d{2}").search(self.date)):  # format checking only
            print("Please enter in the format shown.")
            self.setDate()                                      # keep trying until we set it right

    # setter - location
    def setLocation(self):
        self.location=input("Room number: ")
        if notRight(input("{0} - is this correct? y/n: ".format(self.location))):
            self.setLocation()                                     # keep trying until we set it right

    # setter - class number
    def setClass(self):
        self.classNumber=input("162, 163 or 202? ")
        if not (re.compile("162|163|202").search(self.classNumber)):    # number only
            print("Please enter class number only.")
            self.setClass()                                     # keep trying until we set it right

    #setter - time of appointment
    def setTime(self):
        self.time=input("appointment time, eg. 1:30pm: ")
        if notRight(input("{0} - is this correct? y/n: ".format(self.time))):
            self.setTime()

    # setter - day of week: monday/ tuesday...
    def setDOW(self):
        self.dow=input("Day of week monday, tuesday, etc... ")
        if not (re.compile("monday|tuesday|wednesday|thursday|friday").search(self.dow)):  # format checking only
            print("Please enter in the format shown.")
            self.setDOW()                                  # keep trying until we set it right

    # setter - Odin ID
    def setOdinID(self):
        self.odinID=input("Odin ID: ")
        if notRight(input("{0} - is this correct? y/n: ".format(self.odinID))):
            self.setOdinID()                               # keep trying until we are satisfied

    # setter - student name
    def setStudent(self):
        self.studentName=input("Student name: ")
        if notRight(input("{0} - is this correct? y/n: ".format(self.studentName))):
            self.setStudent()                              # keep trying until we are satisfied

    # setter - student email
    def setEmail(self):
        self.studentEmail=input("Student email: ")
        if not (re.match("[^@]+@[^@]+\.[^@]+", self.studentEmail)):  # minimal email format checking only
            print("Please enter an email: ")
            self.setEmail()                                # keep trying until we set it right

    # setter - TCSS info
    def setTCSS(self):
        try:
            temp=TCSSselect(TCSSlookup())
            self.tutor = temp[0]
            self.tutorEmail = temp[1]

        except Oops as err:
            print(err.message)
            self.setTCSS()                              # try again


    # set student email
    # we need to figure out which email (psu or non-psu) and how we want to set it. If we set it automatically
    # we query LDAP and make a selection if there is more than one result. Otherwise enter it by hand. LDAP query
    # is nice, but: garbage in, garbage out ... and spelling counts.
    def setStudentInfo(self):
        self.setStudent()
        # if we want to use PSU email
        # we have the option use LDAP to set their ODIN ID or enter it manually
        try:
            if (re.compile("y|Y").search(input("Use PSU email? y/n: "))):
                if (re.compile("y|Y").search(input("Look up OdinID for {0}? y/n: ".format(self.studentName)))):
                    self.odinID=findLDAP(self.studentName)
                    if (len(self.odinID) > 1):
                        count = 1
                        print("Which Odin ID? Non valid entry aborts")
                        for name in self.odinID:
                            print("{0}) {1}".format(count, self.odinID[count-1]))
                            count += 1
                        selection=int(input())  # throw an error if they enter a letter; means they wanted out anyhow.
                        if ((selection > 0) and (selection < count)):
                            self.odinID=str(self.odinID[selection-1])
                        else:
                            self.odinID=""
                            raise SeriousProblem("You have chosen to quit")
                    elif (len(self.odinID) < 1):
                        self.odinID=""
                        raise Oops("Odin ID not found, try again.")
                    else:
                        self.odinID=str(self.odinID[0])
                else: # yes to PSU email, but we want to manually enter Odin ID
                    self.setOdinID()
                self.studentEmail=self.odinID+"@pdx.edu"
            else:     # no to PSU email so enter it manually
                self.setEmail()

        except Oops as err:         # any error will cause termination. This is not great, but we are right
            print(err.message)      # at the start and probably they need to reenter the student name anyhow
            self.setStudentInfo()

    # make the appointment - that is, run all the setters
    def setAppointment(self):
        self.setStudentInfo()
        self.setTCSS()
        self.setClass()
        self.setDate()
        self.setDOW()
        self.setTime()
        self.setLocation()

#        END CLASS
#-------------------------------------------------------



#-------------------------------------------------------
#       UTILITIES



#-------------------------------------------------------
# use LDAPsearch with simple authentication instead of SASL and restrict output, disable comments and printing.
# the student's name as entered previously for the search. There may be students with multiple ODIN ids
# or even more than one student with a common name as indicated. For this reason we return a list of matching
# Odin ids. Generally speaking there will only be one, but in the event there is more than one the operator
# of the script will have to figure out where to go from there.
# This is meant as a convenience, and more often than not it will be. However, the operator can always
# consult D2L for the actual ODIN id if need be. If you want to refactor this you can: import ldap - good luck.
def findLDAP(name):
    flags="-xLLL"
    proc1=sp.Popen(["ldapsearch", flags, "cn="+name], stdout=sp.PIPE)
    proc2=sp.Popen(["grep", "uid:"], stdin=proc1.stdout, stdout=sp.PIPE )
    proc1.stdout.close()
    proc3=sp.Popen(["sed", "s/uid: //"], stdin=proc2.stdout, stdout=sp.PIPE )
    proc2.stdout.close()

    idList = (proc3.communicate()[0]).decode("utf-8")   # returns as bytes
    idList = idList.rsplit("\n")                        # turn into list because there may be more than one choice
    idList.pop()                                        # also the last element is empty
    return idList


#-------------------------------------------------------
# consult external data file (CSV) and grab desired TCSS
# name and email from that file.
# required data format is:
#
# peter parker,pparker@pdx.edu,
# fred meyer,fmeyer@gmail.com,
# et cetera,zomg@yerfunny.com,
#
# this file should be called TCSS_email_list.txt and located in the data
# directory as indicated in the beginning comments of this program
#

def TCSSlookup():
    TCSSname=input("Which TCSS? pattern match the following: ").lower()
    TCSSresults=[]
    try:        # do we have right path?
        for TCSSentry in open(emailFile, 'r'):
            if TCSSname in TCSSentry.lower():
                TCSSresults.append(TCSSentry.split(","))

        return TCSSresults
    except OSError:
        raise SeriousProblem("TCSS_email_list.txt not found in expected location.")


def TCSSselect(TCSSlist):
    theTutorWeAreLookingFor=[]
    if len(TCSSlist) < 1:
        raise Oops("No TCSS by that name found")
    elif len(TCSSlist) > 1:
        count = 1
        print("Which TCSS? Non valid entry aborts")
        for name in TCSSlist:
            print("{0}) {1} {2}".format(count, (TCSSlist[count-1])[0], (TCSSlist[count-1])[1]))
            count += 1
        print("{0}) Search again.".format(count))
        selection=int(input())  # throw an error if they enter a letter; means they wanted out anyhow.
        if selection == count:
            raise Oops("Search again.")
        elif (selection > count or selection < 1):
            raise SeriousProblem("You have chosen to quit.")
        else:
            theTutorWeAreLookingFor=TCSSlist[selection-1]
    else:
        theTutorWeAreLookingFor=TCSSlist[0]
    return theTutorWeAreLookingFor


#-------------------------------------------------------
# email module
# once we have confirmed that we entered to information correctly
# the appointment is written to the scheduled_appointments.txt file
# and an email is sent immediately to the TCSS and the student.
# The email can take up to 5 minutes - thanks localhost.
def sendMail(mtg):
    msg=MIMEText(mtg.studentName+",\nYou are scheduled for a tutoring session as follows:\n"+
              mtg.time+" "+mtg.dow+" "+mtg.date+" at "+mtg.location+" with "+mtg.tutor+".\n\n"+
              "TCSS Admin")
    msg['To']=mtg.studentEmail
    msg['Bcc']=mtg.tutorEmail
    msg['From']=yourNameHere+"@pdx.edu"  # your student account
    msg['Subject']="Tutoring for CS "+mtg.classNumber

    # send via localhost SMTP server
    s=smtplib.SMTP('localhost')
    s.send_message(msg)
    s.quit()

    # record in SentEmails.log that we emailed
    try:
        now=time.strftime("%c")
        f=open(SentFile, 'a')
        f.write(mtg.studentEmail+" "+now+"\n")
        f.close()
    except OSError as e:
        print("email sent, but unable to find or write to SentEmails.log")
        pass


#-------------------------------------------------------
# user input verification utility
def notRight(information):
    flag=True
    if (re.compile("y|Y").search(information)):  # format checking only
        flag=False
    return flag



#-------------------------------------------------------
def main():
    tutoringAppointment = Appointment()
    try:
        doAnother=True;                                 # more appointments to make/ did we get it right?
        while doAnother:
            tutoringAppointment.setAppointment()
            tutoringAppointment.display()               # of course it has to be called display()
            if notRight(input("Is that correct? y/n: ")):
                doAnother=True                          # we are just going to overwrite the data every time
            else:
                tutoringAppointment.write()             # put it in the file
                sendMail(tutoringAppointment)           # send the email
                doAnother= not notRight(input("Another appointment to schedule? y/n: "))


    except SeriousProblem as err:
        print("")
        print(err.message)
        sys.exit(0)

    except ValueError:
        print("")
        print("Not valid selection. Aborting ... no changes made")
        sys.exit

    except KeyboardInterrupt:
        print("")
        print("Exit requested, changes not written")
        sys.exit(0)

#-------------------------------------------------------
# run it!
main()
