import re
import sys
import time
import fnmatch # Used to see if websites matches in-scope wildcard (i.e. hi.bob.com == *.bob.com)
import requests
import pandas

# TO DO:
# Implement continuous scanning
# Command functionality (i.e., bh -t tesla.com)
# Allow for multiple targets
# Add HackerOne DB
# add test to see if targets return http status code of 200?

target = 'tesla.com'

def domain_query():
    cert_database = 'https://crt.sh/?CN=' + target

    response = requests.get(cert_database)
    while response.status_code != 200: # Try and access database. If HTTP GET != 200, wait 3 seconds then try again
        time.sleep(3)
        response = requests.get(cert_database)
    
    table = pandas.read_html(response.text) # Pull data from GET requests for use in pandas

    if 'Certificates  None found' in str(table): # Check if target is part of crt.sh database
        print('\nERROR! Target', target, 'could not be found in crt.sh. Please try a different target.\n')
        sys.exit()
    
    data_frame = table[2].loc[:, ('Logged At ⇧', 'Matching Identities')] # Prints all rows for columns "Logged At ⇧" and "Matching Identities"
    entries = data_frame.values.tolist()
    
    # Runs a check to see if multiple websites were created on the same day. If so, appends the targets to the "websites" list
    count = 1
    websites = [entries[0][1]]
    try:
        while entries[0][0] == entries[count][0]:
            websites.append(entries[count][1])
            count +=1
    except IndexError:
        return 0

    print('\nTargets from crt.sh database:\n', websites, '\n')
    return websites


def bugcrowd():
    websites = domain_query()
    in_scope_websites = []

    
    # Checks Bugcrowd to see if a bug bounty exists for the targets
    bugcrowd_df = pandas.read_json('https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/bugcrowd_data.json') # Stores bugcrowd_data.json in pandas DataFrame "bugcrowd_df"
    target_bc = target[:target.rindex(".")].capitalize() # Cleans target by removing the domain extension/top level domain and capitlizes the first letter (i.e. "google.com" == "Google")
    search_bc = bugcrowd_df[bugcrowd_df['name'] == target_bc] # Stores results of search

    if search_bc.empty: # Checks to see if target is in Bugcrowd database
        print('\nERROR!', target, ' is in crt.sh but does not appear to have a Bugcrowd bounty program. Try a different target.\n')
        sys.exit()
    
    else:
        search_bc_targets = pandas.DataFrame.from_dict(search_bc['targets'].to_dict()) # stores in_scope and out_of_scope targets in dictionary before passing to dataframe

        # Had to convert following lines from dataframe to dict to str as Dataframe output is truncated
        out_of_scope_text = str(search_bc_targets.loc['out_of_scope'].to_dict())
        out_of_scope_list = re.findall(r"'target': '(.*?)'}", out_of_scope_text)
        in_scope_text = str(search_bc_targets.loc['in_scope'].to_dict())
        in_scope_list = re.findall(r"'target': '(.*?)'}", in_scope_text)
        
        for website in websites:
            
            for in_scope in in_scope_list:
                
                if fnmatch.fnmatch(website, in_scope): # Checks if in scope
                
                    for out_scope in out_of_scope_list:

                        if fnmatch.fnmatch(website, out_scope): # Checks if out of scope
                            break
                    
                        else:
                            in_scope_websites.append(website)
                            break

    if len(in_scope_websites) == 0:
        print("\n******************************\n\nNone of the targets are in-scope\n\n******************************")
    
    else:
        print('\n********** IN-SCOPE Targets **********\n\n', in_scope_websites,
            '\n\n**************************************\n')   


def main():
    bugcrowd()

    seconds = 10800
    print("\nScan complete.", seconds / 3600, "hours until next scan.\n")

    while 1 == 1: # need to change to while not exit
        time.sleep(seconds) # waits 3 hours before scanning again
        print("Starting NEW scan")
        bugcrowd()

main()
