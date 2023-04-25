import re
import sys
import time
import fnmatch # Used to see if websites matches in-scope wildcard (i.e. hi.bob.com == *.bob.com)
import requests
import pandas
import os

now = time.localtime()

def domain_query(target):
    crt_database = 'https://crt.sh/?CN=' + target

    t1 = time.strftime("%b-%d %H:%M:%S ")
    print('\n' + t1 + 'Starting Scan for [' + target + ']. Querying crt.sh database...')
    while True:
        try:
            response = requests.get(crt_database, timeout=2)
        except:
            print('Query failed. Trying again...')
            continue
        break
    print("Query SUCCESS")
    
    table = pandas.read_html(response.text) # Pull data from GET requests for use in pandas


    if 'Certificates  None found' in str(table): # Check if target is part of crt.sh database
        print('\nERROR! Target', target, 'could not be found in crt.sh. Please try a different target.\n')
        sys.exit()
    
    data_frame = table[2].loc[:, ('Logged At ⇧', 'Matching Identities')] # Prints all rows for columns "Logged At ⇧" and "Matching Identities"
    entries = data_frame.values.tolist()
    
    number_of_entries = len(entries)
    count = 0
    websites = [] 
    while count != number_of_entries:
        websites.append(entries[count][1])
        count+=1 

    print('Acquired potential targets from crt.sh')
    return websites


def bugcrowd(target):
    websites = domain_query(target)
    print("Querying Bugcrowd db...")

    # Checks Bugcrowd to see if a bug bounty exists for the targets
    bugcrowd_df = pandas.read_json('https://raw.githubusercontent.com/arkadiyt/bounty-targets-data/main/data/bugcrowd_data.json') # Stores bugcrowd_data.json in pandas DataFrame "bugcrowd_df"
    target_bc = target[:target.rindex(".")].capitalize() # Cleans target by removing the domain extension/top level domain and capitlizes the first letter (i.e. "google.com" == "Google")
    search_bc = bugcrowd_df[bugcrowd_df['name'] == target_bc] # Stores results of search

    if search_bc.empty: # Checks to see if target is in Bugcrowd database
        print('\nERROR! [' + target + '] is in crt.sh but does not appear to have a Bugcrowd bounty program. Try a different target.\n')
        sys.exit()
    
    else:
        search_bc_targets = pandas.DataFrame.from_dict(search_bc['targets'].to_dict()) # stores in_scope and out_of_scope targets in dictionary before passing to dataframe

        # Had to convert following lines from dataframe to dict to str as Dataframe output is truncated
        out_of_scope_text = str(search_bc_targets.loc['out_of_scope'].to_dict())
        out_of_scope_list = re.findall(r"'target': '(.*?)'}", out_of_scope_text)
        in_scope_text = str(search_bc_targets.loc['in_scope'].to_dict())
        in_scope_list = re.findall(r"'target': '(.*?)'}", in_scope_text)

        in_scope_websites = []
        
        for website in websites:

            for in_scope in in_scope_list:
                
                if fnmatch.fnmatch(website, in_scope): # Checks if in scope
                
                    for out_scope in out_of_scope_list:

                        if fnmatch.fnmatch(website, out_scope): # Checks if out of scope
                            break
                    
                        else:
                            in_scope_websites.append(website)
                            break
    
    return in_scope_websites

def output(target):
    in_scope_websites = bugcrowd(target)

    if len(in_scope_websites) == 0:
        print('None of the targets from crt.sh are in-scope')
    
    else:
        print('Found', len(in_scope_websites), 'targets from crt.sh that are in scope')
        new_counter = 0

        output_filepath = os.path.realpath(os.path.dirname(__file__)) + '/output.txt'

        if os.path.exists(output_filepath):

            # output_file_content = set(output_filepath)
            
            for website in in_scope_websites:
                with open (output_filepath, 'r+') as output_file:
                    
                    if website in output_file.read(): # prevents duplicate targets from appearing in file
                        continue
                    
                    else:
                        output_file.write(website + '\n')
                        new_counter += 1
                
                output_file.close()
                

        else:
            with open(output_filepath, 'w') as output_file:
                print("Output file not found! Creating one now...")

                for website in in_scope_websites:
                    output_file.write(website + '\n')
                    new_counter += 1
        
                output_file.close()
        
        print('Finished writing', new_counter, 'new targets to output file')
        

def main():
    target_list = input('Please enter the domain name for the target(s) you wish to scan separated by a space (i.e., tesla.com google.com):\n')
    target_list = target_list.split(' ')

    while True:
        try:
            minutes = float(input('Time between scans (in minutes)? '))
        except:
            minutes = print('ERROR! Please enter a number for time between scans')
        else:
            break

    while True:
        for target in target_list:
            output(target)
            
            if len(target_list) > 1:
                print('\nWaiting 5 seconds before performing next scan due to rate limiting on crt.sh...')
                time.sleep(5) # SEE IF THIS OVERCOMES RATE LIMITING?

        t2 = time.strftime("%b-%d %H:%M:%S ")
        print(t2 + 'Scan complete.', minutes, 'minutes until next scan.\n')
        
        time.sleep(minutes * 60) # waits "minutes" before scanning again
        t3 = time.strftime("%b-%d %H:%M:%S ")
        print(t3, 'Starting NEW scan')
        
main()
