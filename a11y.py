import requests, os, sys, time
#import MySQLdb as mdb, MySQLdb.cursors
#import resources as rs

def main():
    """main a11y function"""
    base = "https://{}.atlassian.net/rest/api/2/search?jql=".format(os.getenv('jiradomain'))
    a11y_base_jql = '(labels%20%3D%20accessibility%20and%20(status%20!%3D%20Closed%20and%20status%20!%3D%20Done)%20and%20project%20!%3D%20"Accessibility%20Testing"%20and%20type%20!%3D%20Epic%20'

    def construct_jql(jql):
        """craft our jql with our known beginning and known end"""
        return base + jql + ')&maxResults=1000'

    def get_key(item):
        return item[1]

    def get_sprint_count(issue):
        if issue['fields']['customfield_10007'] != None:
            return len(issue['fields']['customfield_10007'])
        else:
            return 0

    def a11y_json(jql):
        jiracred = (os.getenv('juser') + ':' + os.getenv('jpass')).encode('base64', 'strict')
        headers = {'Authorization': 'Basic ' + jiracred}

        try:
            response = requests.get(jql, headers=headers, timeout=60)
        except requests.Timeout:
            print "oops timeout"
        total = int(response.json()['total']) # should take this out and replace it with error handling
        return response.json()

    def a11y_list():
        a11y_list_jql = construct_jql(a11y_base_jql)
        json = a11y_json(a11y_list_jql)['issues']
        ticket_store = {}
        for item in json:
            sprint_count = get_sprint_count(item)
            # should also be storing these items in the db
            ticket_store[item['key']] = {'sprint_count': sprint_count, 'team': item['fields']['customfield_12700']['value']}
        return ticket_store

    def unprioritized_tickets():
        unp_jql = '%20and%20("Epic%20Link"%20%3D%20CNVS-11163%20or%20"epic%20link"%20%3D%20CNVS-11105%20or%20"epic%20link"%20%3D%20CNVS-11106)'
        jql = construct_jql(a11y_base_jql + unp_jql)
        prioritized_tix = a11y_json(jql)['issues']
        pt_ids = []
        for item in prioritized_tix:
            pt_ids.append(item['key'])
        return list(set(a11y_list().keys()) - set(pt_ids))

    def prioritized_tickets():
        priority_dict = {1: '11163', 2: '11105', 3: '11106'}
        priority_jql = '%20and%20("Epic%20Link"%20%3D%20CNVS-{})'
        for key, value in priority_dict.iteritems():
            current_jql = construct_jql(a11y_base_jql + priority_jql.format(value))
            current_tix_json = a11y_json(current_jql)
            for ticket in current_tix_json['issues']:
                ticket_id = ticket['key']
                sprint_count = get_sprint_count(ticket)
                # store the tickets in the db
                print str(key), ticket_id, ticket['fields']['customfield_12700']['value'], sprint_count
            #print key, value, current_jql
            #print current_jql
            #print current_tix_json



    #ticket_store = a11y_list()
    #print len(ticket_store)
    #temp_arr = []
    #for key, value in ticket_store.iteritems():
        #if value["sprint_count"] > 1:
            #temp_arr.append([key, value["sprint_count"]])
    #temp_arr = sorted(temp_arr, key=get_key, reverse=True)
    #print "The tickets people _want_ to pretend to care about: \r\n"
    #for i in temp_arr:
        #print "{}, sprint count: {}".format(i[0], i[1])
    #print unprioritized_tickets()

    prioritized_tickets()
    print unprioritized_tickets()
main()
