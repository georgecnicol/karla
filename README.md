# karla
1) "preliminary" is a form letter that we use to send out to students to get them to respond with a choice of times.
From there you can consult the master schedule and either schedule them or get new times from them.

2) When you schedule them, use the python scheduler. While it may feel like you are double entering with whatever
other graphical scheduling tool you might use, it cuts the amount of email time for scheduling to alomst zero, since it
not only sends the email that you would have to send anyhow - but it also works with the cronjob to send a reminder email.
This ends up being a huge net savings in email time.

3) Set a cronjob to run every morning at 6am as follows:
some_school_box$> crontab -e


# in the cron file
00 06 * * * /u/YOURHOMEDIR/karla/cron_mailer.bash

Then save and exit. Now at 6 am every day while you are fast asleep the cron_mailer will look at the scheduled
appointments and send out any reminders for the following day.

This is the tool suite as it stands and how you use it. If you clone this repo straight to your homedir and follow these
instructions and the instructions in the README for the data dir you should be all set.

Lastly, these tools expect that you are using your pdx.edu email. If you aren't then you will need to edit things, in a lot
of places. If you are adding onto/ refactoring the tool suite then you might consider adding that feature.

