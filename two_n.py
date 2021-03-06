"""gets all tickets associated to the passed team and does maths and reports back to slack"""
import requests, os, sys, time
import MySQLdb as mdb, MySQLdb.cursors
import resources as rs
def main():
    """main function"""
    db_msg = ""
    token = os.getenv('stoken')

    team = str(sys.argv[1])
    n_number = 2*int(sys.argv[2])
    channel = str(sys.argv[3])
    stat = str(sys.argv[4])

    con = mdb.connect('localhost', os.getenv('dbuser1'), os.getenv('dbpass1'), 'rtm',
                      cursorclass=MySQLdb.cursors.DictCursor)
    cur = con.cursor()

    sql = "SELECT * FROM 2n_Teams WHERE Team = %s"
    cur.execute(sql, (team))
    row = cur.fetchone()
    query = row["Query"]
    jiracred = (os.getenv('juser') + ':' + os.getenv('jpass')).encode('base64', 'strict')
    headers = {'Authorization': 'Basic ' + jiracred}

    if query == None:
        base = "https://{}.atlassian.net/rest/api/2/search?jql=".format(os.getenv('jiradomain'))
        jql = (base + '(status%20%20%3D%20Open%20OR%20status%20%3D%20"In%20Progress"'
               '%20OR%20status%20%3D%20"QA"%20OR%20status%20%3D%20Feedback%20or'
               '%20status%20%3D%20"QA%20Ready")%20AND%20type%20%3D%20Bug%20AND'
               '%20("Sprint%20Team"%20%3D%20%27' + team + '%27)')
    else:
        jql = query
    response = requests.get(jql, headers=headers)
    try:
        ticket_count = float(response.json()[u'total'])
        n_diff = ticket_count - n_number
        n_percentage = round((n_diff/n_number) * 100, 2)
        n_ratio = round(ticket_count/(n_number/2), 2)
        if stat == "True":
            now = time.time()
            sql = ("INSERT INTO 2n_data (Team, N_number, Count, Date) "
                   "VALUES('{}', '{}', '{}', '{}')").format(team, n_number, ticket_count, now)
            cur.execute(sql)
            con.commit()
            db_msg = "\r\nSuccessfully added this team and their 2n number to the db for today."
        if n_diff > 0:
            message = ("{} has {}/{} tickets that count towards 2n. "
                       "That's {}% over 2n with an N ratio of {}n.")
            message = message.format(team, int(ticket_count), n_number, n_percentage, n_ratio)
        else:
            message = "{} has {}/{} tickets that count towards 2n."
            message = message.format(team, int(ticket_count), str(n_number))
        rs.post(channel, message + db_msg, 'shades McGee', token, icon_emoji=':shadesmcgee:')
    except KeyError:
        message = ("Looks like JIRA doesn't have {} as a sprint team, "
                   "please add your team to the sprint team field.")
        message = message.format(team)
        rs.post(channel, message, 'shades McGee', token, icon_emoji=':shadesmcgee:')
    except Exception, e:
        message = "Oops, something went wrong. If this persists, please contact @slewis. \n" + e
        rs.post(channel, message, 'shades McGee', token, icon_emoji=':shadesmcgee:')

main()
