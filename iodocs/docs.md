<!--- This is converted from the html here http://politicalpartytime.org/api/ via pandoc http://johnmacfarlane.net/pandoc/ ; formatting quirks were fixed by hand. -->
# API


##Overview

The base url for the API is `/politicalpartytime.org/api/v1` ; any
addresses in the below must be appended to the base url. All API calls
require an active [Sunlight API
key](http://services.sunlightlabs.com/accounts/register/) and a format
(either 'json' or 'xml') as querystring arguments. For instance, a call
to describe event \#31 would look like `/event/31/?format=json&apikey=[API key]`. API [methods](#methods) and [return
types](#return_types) are described below.

Return objects consist of two parts; a meta object describing the results returned, and a list of the returned objects. The meta object looks like the following:

    {"meta": {"limit": 50, "next": "/api/v1/event/?apikey=[API Key]&limit=50&offset=50&format=json", "offset": 0, "previous": null, "total_count": 17246}
    
   The `next` variable is the next page in this result set; `previous`--which in the above is null, is the previous page. The `total_count` is the total number of objects matching this description, though not all are returned. The `limit` is the maximum number of objects returned per page.
   
##Universal Parameters
All API calls can be given a `limit` and an `offset` parameter, though the limit can not be greater than 50. The offset must be positive.

<a id="methods"></a>
##API Methods 


###/event/
  
Return a list of [events](#events). With no filters will return all
events. Optional parameters are:

 `beneficiaries__crp_id` 
:   Lawmaker ID used by the Center for Responsive Politics.
	
	/event/?beneficiaries__crp_id=N00003675&format=json&apikey=[API key]
	
`start_date__gt`
: Show only events with a start date after a given date. Dates should be formatted YYYY-MM-DD.

	/event/?start_date__gt=2012-10-01&format=json&apikey=[API key]</pre>

 `host__id ` 
:   Internal host ID

   	/event/?host_id=12&format=json&apikey=[API key]

 `beneficiaries__state ` 
:   Two-letter postal code indicating what state the event beneficiary
    represents. Presidents do not represent a single state.
    
    /event/?beneficiaries__state=CT&format=json&apikey=[API key]

###/event/[event_id]/
Return details about a single [event](#events) referenced by ID. No
additional parameters are required.

	/event/31/?format=json&apikey=[API key]

###/lawmaker/
Return details about [legislators](#legislators). With no additional
parameters, will return all legislators.

 `crp_id` 
:   Show only the legislator identified by this Center for
    Responsive Politics ID.

   
   	/lawmaker/?format=json&crp_id=N00003675&apikey=[API key]

###/lawmaker/[lawmaker_id]/
Return details about a single [legislator](#legislators) referenced by
internal ID. No additional parameters are required.



###/host/
Return details about all [hosts](#hosts).

###/host/[host_id]/
Return details about a single [host](#hosts) identified by internal ID.


        /host/?host_id=12&format=json&apikey=[API key]
<a id="return_types"></a>
##API return types

<a id="events"></a>
###Events

Each fundraiser or other party includes the following data, though some
fields may be empty.

 `Beneficiaries` 
:   A list of beneficiaries, typically lawmakers, who are raising money
    at the event. Some events raise money for many lawmakers, so this
    list may be quite long. For more details see
    [legislators](#legislators).
 
 `canceled` 
:   Is the event canceled ?
 
 `checks_payable_to_address` 
:   
 
 `contributions_info` 
:   
 
 `distribution_paid_for_by` 
:   The entity who sent the event--typically the sponsoring committee
 
 `end_date` 
:   
 
 `end_time` 
:   
 
 `entertainment` 
:   
 
 `hosts` 
:   A list of event [hosts](#hosts).
 
 `id` 
:   An unique internal ID. This is unique with respect to invitations;
    occasionally we enter different versions of the same event twice.
 
 `is_presidential` 
:   Is this a presidential fundraiser?
 
 `make_checks_payable_to` 
:   
 
 `postponed` 
:   
 
 `resource_uri` 
:   The local API address for this specific event.
 
 `rsvp_info` 
:   
 
 `start_date` 
:   
 
 `start_time` 
:   
 
 `venue` 
:   The location of the event. For more details, see [venues](#venues).

<a id="legislators"></a>
###Legislators
Not all legislators are present; only those who we have a record of
hosting or benefitting from a fundraiser.

 `affiliate` 
:   

 `crp_id` 
:   A unique ID assigned by the Center for Responsive Politics.

 `district` 
:   What house district does this lawmaker represent? Absent for other
    officials.

 `id` 
:   A unique internal ID.

 `name` 
:   

 `party` 
:   

 `resource_uri` 
:   URL for API page with these details.

 `state` 
:   What state does this lawmaker represent?

 `title` 
:   

<a id="hosts"></a>
###Hosts
These are people listed as hosts on the invitation. They can be either
lawmakers or regular citizens.

 `crp_id` 
:   A unique ID assigned by the Center for Responsive Politics.

 `id` 
:   A unique internal ID.

 `name` 
:   

 `resource_uri` 
:   URL for API page with these details.

<a id="venues"></a>
###Venues
The locations where fundraisers are held

 `address1` 
:   

 `address2` 
:   

 `city` 
:   

 `id` 
:   A unique internal ID.

 `resource_uri` 
:   URL for API page with these details.

 `state` 
:   

 `venue_name` 
:   

 `zipcode` 
:   

