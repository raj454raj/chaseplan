"""
    Copyright (c) 2015-2016 Raj Patel(raj454raj@gmail.com), StopStalk

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
"""

import time
import traceback
import gevent
from datetime import datetime
from gevent import monkey
gevent.monkey.patch_all(thread=False)

# @ToDo: Make this generalised
from sites import codechef, codeforces, spoj, hackerearth, hackerrank

rows = []

# -----------------------------------------------------------------------------
def _debug(first_name, last_name, site, custom=False):
    """
        Advanced logging of submissions
    """

    name = first_name + " " + last_name
    debug_string = site + ":"
    if custom:
        debug_string += "CUS:"
    debug_string += name
    print debug_string,

# -----------------------------------------------------------------------------
def get_submissions(user_id,
                    handle,
                    stopstalk_handle,
                    submissions,
                    site,
                    custom=False):
    """
        Get the submissions and populate the database
    """

    db = current.db
    count = 0

    if submissions == {}:
        print "0"
        return 0

    global rows

    for i in sorted(submissions[handle].iterkeys()):
        for j in sorted(submissions[handle][i].iterkeys()):
            submission = submissions[handle][i][j]
            if len(submission) == 7:
                count += 1
                row = []
                if custom:
                    row.extend(["--", user_id])
                else:
                    row.extend([user_id, "--"])

                row.extend([stopstalk_handle,
                            handle,
                            site,
                            submission[0],
                            submission[2],
                            submission[1],
                            submission[5],
                            submission[3],
                            submission[4],
                            submission[6]])

                encoded_row = []
                for x in row:
                    if isinstance(x, basestring):
                        tmp = x.encode("ascii", "ignore")

                        # @ToDo: Dirty hack! Do something with
                        #        replace and escaping quotes
                        tmp = tmp.replace("\"", "").replace("'", "")
                        if tmp == "--":
                            tmp = "NULL"
                        else:
                            tmp = u"\"" + tmp + u"\""
                        encoded_row.append(tmp)
                    else:
                        encoded_row.append(str(x))

                rows.append(u"(" + u", ".join(encoded_row) + u")")


    if count != 0:
        print "%s" % (count)
    else:
        print "0"
    return count

# ----------------------------------------------------------------------------
def retrieve_submissions(reg_user, custom=False):
    """
        Retrieve submissions that are not already in the database
    """

    if custom:
        query = (db.custom_friend.id == reg_user)
        row = db(query).select().first()
        table = db.custom_friend
    else:
        query = ((db.auth_user.id == reg_user) & \
                 (db.auth_user.blacklisted == False))
        row = db(query).select().first()

        if row is None:
            print "Auth user " + str(reg_user) + " skipped"
            return

        table = db.auth_user

    # Start retrieving from this date if user registered the first time
    initial_date = current.INITIAL_DATE
    time_conversion = "%Y-%m-%d %H:%M:%S"

    last_retrieved = db(query).select(table.last_retrieved).first()
    if last_retrieved:
        last_retrieved = str(last_retrieved.last_retrieved)
    else:
        last_retrieved = initial_date

    last_retrieved = time.strptime(str(last_retrieved), time_conversion)
    list_of_submissions = []

    for site in current.SITES:
        site_handle = row[site.lower() + "_handle"]
        if site_handle:
            Site = globals()[site.lower()]
            P = Site.Profile(site_handle)
            site_method = P.get_submissions
            submissions = site_method(last_retrieved)
            list_of_submissions.append((site, submissions))
            if submissions == -1:
                break

    total_retrieved = 0

    for submissions in list_of_submissions:
        if submissions[1] == -1:
            print "PROBLEM " + site + " " + \
                  row.stopstalk_handle

            return "FAILURE"

    # Update the last retrieved of the user
    today = datetime.now()
    db(query).update(last_retrieved=today)

    for submissions in list_of_submissions:
        site = submissions[0]
        site_handle = row[site.lower() + "_handle"]
        _debug(row.first_name, row.last_name, site, custom)
        total_retrieved += get_submissions(reg_user,
                                           site_handle,
                                           row.stopstalk_handle,
                                           submissions[1],
                                           site,
                                           custom)
    return total_retrieved

if __name__ == "__main__":

    atable = db.auth_user
    cftable = db.custom_friend

    columns = "(`user_id`, `custom_user_id`, `stopstalk_handle`, " + \
              "`site_handle`, `site`, `time_stamp`, `problem_name`," + \
              "`problem_link`, `lang`, `status`, `points`, `view_link`)"

    registered_users = db(atable).select(atable.id)
    registered_users = [x["id"] for x in registered_users]
    for user in registered_users:
        if user % 3 == 1:
            retrieve_submissions(user)

    custom_users = db(cftable.duplicate_cu == None).select(cftable.id)
    custom_users = [x["id"] for x in custom_users]
    for custom_user in custom_users:
        if custom_user % 3 == 1:
            retrieve_submissions(custom_user, True)

    if len(rows) != 0:
        sql_query = """INSERT INTO `submission` """ + \
                    columns + """ VALUES """ + \
                    ",".join(rows) + """;"""
        try:
            db.executesql(sql_query)
        except:
            traceback.print_exc()
            print "Error in " + site + " BULK INSERT for " + handle

# END =========================================================================
