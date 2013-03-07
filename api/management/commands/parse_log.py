"""
"98.139.134.96 - - [05/Mar/2013:07:52:15 -0500]  "GET /feeds/upcoming/ HTTP/1.1" 200 17464 "-" "Yahoo Pipes 2.0"

No match ***

"209.85.238.226 - - [05/Mar/2013:07:52:26 -0500]  "GET /feeds/pol/N00009829/ HTTP/1.1" 200 12234 "-" "Feedfetcher-Google; (+http://www.google.com/feedfetcher.html; 1 subscribers; feed-id=16639277362590365820)"

No match ***

"66.249.76.226 - - [05/Mar/2013:07:52:30 -0500]  "GET /search/Host/Carolyn%20Sonnetag/ HTTP/1.1" 200 13838 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

No match ***

"66.249.76.226 - - [05/Mar/2013:07:52:37 -0500]  "GET /search/Beneficiary/Obama%20Victory%20Fund%20-%20Joint%20Fundraising%20Committee/?page=8&sort=start_date&order=0 HTTP/1.1" 200 23672 "-" "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"

No match ***

"72.30.142.250 - - [05/Mar/2013:07:52:37 -0500]  "GET /upload/ HTTP/1.1" 200 12161 "-" "Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)"



"""


import re
LOG_PATH = '/Users/jfenton/partytime/logs/partytime-access.log'

LOG_REGEX = re.compile(r'\[(?P<date>\d{2}\/\w{3}\/\d{4}):\d{2}:\d{2}:\d{2} \-\d{4}\]\s*"(GET|POST)\s*(\/.*?)\s*HTTP\/\d\.\d\s*\"\s*(\d+)\s+')
API_REGEX = re.compile(r'apikey=([\w\-]+)')

def process_log_line(line):
    match = LOG_REGEX.search(line)
    if match:
        date_raw = match.group(1)
        call_type = match.group(2)
        url = match.group(3)
        status = match.group(4)
        #print "match: "
        api_match = API_REGEX.search(url)
        if api_match:   
            api_key = api_match.group(1)
            return {'date':date_raw, 'status':status,'api_key':api_key}
        else:
            return None
    else:

        return None
#LOG_REGEX = re.compile(r'\[(\d{2}\/w{3}\/d{4})')


f = open(LOG_PATH, "r")
for line in f:
    record = process_log_line(line)
    if record:
        print record
