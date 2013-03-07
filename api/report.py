import re, os, datetime, gzip
from locksmith.common import apicall


LOG_REGEX = re.compile(r'\[(?P<date>\d{2}\/\w{3}\/\d{4}):\d{2}:\d{2}:\d{2} \-\d{4}\]\s*"(GET|POST)\s*(\/.*?)\s*HTTP\/\d\.\d\s*\"\s*(\d+)\s+')
API_REGEX = re.compile(r'apikey=([\w\-]+)')

def process_log_line(line):
    #print "processing line %s" % line
    record = None
    match = LOG_REGEX.search(line)
    if match:
        date_raw = match.group(1)
        call_type = match.group(2)
        url = match.group(3)
        status = match.group(4)
        #print "match: url=%s" % url
        api_match = API_REGEX.search(url)
        if api_match:   
            api_key = api_match.group(1)
            record = {'date':date_raw, 'status':status,'apikey':api_key}
            #print "Record is %s" % record
    return record

def submit_report(log_path, log_date_format, log_date, locksmith_api_name, locksmith_signing_key, locksmith_endpoint):
    # Reporting format requires an endpoint. Fill it with junk. 
    endpoint = 'p'
    
    log_directory = os.path.dirname(log_path)
    log_file_re = re.compile(re.escape(os.path.basename(log_path)).replace(r'\*', 'partytime-access.log.*'))
    
    # only include the ones that match our wildcard pattern
    unsorted_log_files = [file for file in os.listdir(log_directory) if log_file_re.match(file)]
    
    # do some voodoo to make sure they're in the right order, since the numbers may be lexicographically sorted in an odd way
    number_re = re.compile(r'\d+')
    log_files = sorted(unsorted_log_files, key=lambda f: int(number_re.findall(f)[0]) if number_re.search(f) else -1)
    
    totals = {}
    
    # loop over the files
    last_loop = False
    for log_file in log_files:
        print "Processing log file %s" % log_file
        if log_file.endswith('.gz'):
            file = gzip.open(os.path.join(log_directory, log_file), 'rb')
        else:
            file = open(os.path.join(log_directory, log_file), 'r')
        
        # loop over the rows
        for row in file:
            #print "Processing file %s" % file
            record = process_log_line(row)
            if record:
                day = datetime.datetime.strptime(record['date'], log_date_format).date()
                if day == log_date and record['status'] == '200' and record['apikey'] and record['apikey'] != '-':
               
                    # add it to the tally
                    if record['apikey'] not in totals:
                        totals[record['apikey']] = {}
                
                    if endpoint not in totals[record['apikey']]:
                        totals[record['apikey']][endpoint] = 1
                    else:
                        totals[record['apikey']][endpoint] += 1
                elif day < log_date:
                    # this is the last log we need to parse
                    last_loop = True
                    
        if last_loop:
            break
    
    # submit totals to hub
    submit_date = log_date.strftime('%Y-%m-%d')
    total_submitted = 0
    for api_key in totals:
        for endpoint in totals[api_key]:
            print "Api call on %s %s" % (api_key, totals[api_key][endpoint])
            """apicall(
                locksmith_endpoint,
                locksmith_signing_key,
                api = locksmith_api_name,
                date = submit_date,
                endpoint = endpoint,
                key = api_key,
                calls = totals[api_key][endpoint]
            )
            """
            total_submitted += totals[api_key][endpoint]
    return total_submitted
