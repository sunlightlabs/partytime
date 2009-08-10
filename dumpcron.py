

def main():
    print 'yeaaaaaa'
    import MySQLdb

    # connect
    db = MySQLdb.connect(host="politicalpartytime.org", user="partytime", passwd="***REMOVED***",db="partytime")

    # create a cursor
    cursor = db.cursor()

    #from django.utils.encoding import smart_str, smart_unicode
    import csv
    import zipfile
    from cStringIO import StringIO


    zbuffer = StringIO()
    fbuffer = StringIO()
    zfile = zipfile.ZipFile(zbuffer, "w", zipfile.ZIP_DEFLATED)
 
    #EVENT TABLE
    writer = csv.writer(fbuffer)

    try:
        cursor.execute("SELECT pe.id _id,IFNULL(start_date,'') Start_Date,IFNULL(end_date,'') End_Date,IFNULL(Start_Time,'') Start_Time,IFNULL(end_time,'') End_Time,  entertainment_type,venue_name,address1,address2,city,v.state,zipcode,website,concat(ifnull(v.latitude,''),';',ifnull(v.longitude,'')) LatLong,Contributions_Info,Make_Checks_Payable_To,Checks_Payable_To_Address,Committee_Id,RSVP_Info,Distribution_Paid_for_By FROM publicsite_event pe left join publicsite_venue v on (v.id = pe.venue_id)  left join publicsite_entertainment et on (et.id = pe.entertainment_id)  WHERE (pe.status='' or pe.status is null)  group by pe.id")
    except:
        pass
    rows = cursor.fetchall()
    newrow =["_id","Start_Date","End_Date","Start_Time","End_Time","Entertainment_Type","Venue_Name","Venue_Address1","Venue_Address2","Venue_City","Venue_State","Venue_Zipcode","Venue_Website","LatLong","Contributions_Info","Make_Checks_Payable_To","Checks_Payable_To_Address","Committee_Id","RSVP_Info","Distribution_Paid_for_By","Tags"]																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																			
    writer.writerow(newrow)
    for row in rows:
        newrow = []
        for nr in row:
            #newrow.append( smart_str(nr) )
            newrow.append( nr )
        writer.writerow(newrow)

    zfile.writestr('events.csv', fbuffer.getvalue())
    fbuffer.close()

    #BENEFICIARIES TABLE
    fbuffer2 = StringIO()
    writer = csv.writer(fbuffer2)
    try:
        cursor.execute("SELECT eb.event_id,l.id beneficiary_id, ifnull(name,'') Beneficiary_Name,ifnull(party,'') party, ifnull(state,'') state, ifnull(district,'') district, oi.other_info, crp_id FROM publicsite_event_beneficiary eb left join publicsite_lawmaker l on (l.id = eb.lawmaker_id)  left join publicsite_other_info oi on (oi.event_id = eb.event_id and oi.lawmaker_id = eb.lawmaker_id and oi.moc_type=1) left join publicsite_event ev ON (eb.event_id=ev.id AND (ev.status is null or ev.status='')) order by eb.event_id")
    except:
        pass
    rows = cursor.fetchall()
    newrow = ["event_id","beneficiary_id","Beneficiary_Name","Party","State","District","Other_Info","CRP_id"]																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																								
    writer.writerow(newrow)
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( nr )
        writer.writerow(newrow)

    zfile.writestr('beneficiaries.csv', fbuffer2.getvalue())
    fbuffer2.close()

 
    #HOSTS TABLE
    fbuffer3 = StringIO()
    writer = csv.writer(fbuffer3)
    try:
        cursor.execute("SELECT eh.event_id,h.id host_id, ifnull(name,'') Host_Name,ifnull(other_info,'') Other_Info FROM publicsite_event_hosts eh left join publicsite_host h on (h.id = eh.host_id)  left join publicsite_other_info oi on (oi.event_id = eh.event_id and oi.host_id = eh.host_id) left join publicsite_event ev ON (eh.event_id=ev.id AND (ev.status is null or ev.status='')) order by eh.event_id")
    except:
        pass
    rows = cursor.fetchall()
    newrow =   ["event_id","host_id","Host_Name","Other_Info"]																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																			
    writer.writerow(newrow)
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( nr )
        writer.writerow(newrow)

    zfile.writestr('hosts.csv', fbuffer3.getvalue())
    fbuffer3.close()


    #OMCS TABLE
    fbuffer4 = StringIO()
    writer = csv.writer(fbuffer4)
    try:
        cursor.execute("SELECT eb.event_id,l.id omc_id, ifnull(name,'') OMC_Name,ifnull(party,'') party, ifnull(state,'') state, ifnull(district,'') district,ifnull(other_info,'') Other_Info,crp_id FROM publicsite_event_omc  eb left join publicsite_lawmaker l on (l.id = eb.lawmaker_id) left join publicsite_other_info oi on (oi.event_id = eb.event_id and oi.lawmaker_id = eb.lawmaker_id and oi.moc_type=2) left join publicsite_event ev ON (eb.event_id=ev.id AND (ev.status is null or ev.status=''))  order by eb.event_id")
    except:
        pass
    rows = cursor.fetchall()
    newrow = ["event_id","omc_id","OMC_Name","Party","State","District","Other_Info","CRP_id"]																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																			
    writer.writerow(newrow)
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( nr )
        writer.writerow(newrow)

    zfile.writestr('omcs.csv', fbuffer4.getvalue())
    fbuffer4.close()


    #VENUES TABLE
    fbuffer5 = StringIO()
    writer = csv.writer(fbuffer5)
    try:
        cursor.execute("SELECT id, ifnull(venue_name,'') venue_name,ifnull(venue_address,'') venue_address,address1,address2,city,state,zipcode, ifnull(latitude,'') latitude,ifnull(longitude,'') longitude,website FROM publicsite_venue order by venue_address")
    except:
        pass
    rows = cursor.fetchall()
    newrow = ["id","venue_name","venue_address","Venue_Address1","Venue_Address2","Venue_City","Venue_State","Venue_Zipcode","latitude","longitude","Venue_Website"]		
    newrowt = ["key","venue_name","venue_address","Venue_Address1","Venue_Address2","Venue_City","Venue_State","Venue_Zipcode","latitude","longitude","Venue_Website"]																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																			
																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																	
    writer.writerow(newrowt)
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( nr )
        writer.writerow(newrow)

    zfile.writestr('venues.csv', fbuffer5.getvalue())
    fbuffer5.close()

    zfile.close()
    zbuffer.flush()

    flob=open('partytime_dump_all.zip','wb')
    flob.write( zbuffer.getvalue() )
    flob.close()

    zbuffer.close()




    f = open('partytime_dump_all.csv','w')
    wri = csv.writer(f)    

    try:
        cursor.execute("SELECT pe.id _id,ifnull(group_concat(distinct pb.name, IF(STRCMP(pb.party,''),' (',''),pb.party,IF(STRCMP(pb.state,''),', ',''),pb.state,IF(STRCMP(pb.district,''),concat('-',pb.district),'') , IF(STRCMP(pb.party,''),')','') separator ' || ' ),'') beneficiary,ifnull(group_concat(distinct thost.name separator ' || '),'') host,ifnull(group_concat(distinct  omcl.name, IF(STRCMP(omcl.party,''),' (',''),omcl.party,IF(STRCMP(omcl.state,''),', ',''),omcl.state,IF(STRCMP(omcl.district,''),concat('-',omcl.district),'') , IF(STRCMP(omcl.party,''),')','') separator ' || ' ),'') Other_Members_of_Congress, IFNULL(start_date,'') Start_Date,IFNULL(end_date,'') End_Date,IFNULL(Start_Time,'') Start_Time,IFNULL(end_time,'') End_Time,  entertainment_type,venue_name,address1,address2,city,v.state,zipcode,website,concat(ifnull(v.latitude,''),';',ifnull(v.longitude,'')) LatLong,Contributions_Info,Make_Checks_Payable_To,Checks_Payable_To_Address,Committee_Id,RSVP_Info,Distribution_Paid_for_By FROM publicsite_event pe left join publicsite_event_beneficiary peb on (peb.event_id = pe.id) left join publicsite_lawmaker pb on (peb.lawmaker_id = pb.id) left join publicsite_venue v on (v.id = pe.venue_id)  left join publicsite_entertainment et on (et.id = pe.entertainment_id) left join publicsite_event_omc tomc on (tomc.event_id = pe.id) left join publicsite_lawmaker omcl on (tomc.lawmaker_id = omcl.id) left join publicsite_event_hosts ev_hosts on (ev_hosts.event_id = pe.id) left join publicsite_host thost on (ev_hosts.host_id = thost.id)  WHERE (pe.status is null OR pe.status='') GROUP BY pe.id")

    except:
        pass

    newrow = ['ID', 'Beneficiary', 'Host', 'Other Members', 'Start_Date', 'End_Date', 'Start_Time', 'End_Time',	'Entertainment_Type', 'Venue_Name',	'Venue_Address1', 'Venue_Address2', 'Venue_City', 'Venue_State', 'Venue_Zipcode', 'Venue_Website', 'LatLong', 'Contributions_Info',	'Make_Checks_Payable_To', 'Checks_Payable_To_Address', 'Committee_Id', 'RSVP_Info', 'Distribution_Paid_for_By'];		
    newrowt = ['key', 'Beneficiary', 'Host', 'Other Members', 'Start_Date', 'End_Date', 'Start_Time', 'End_Time',	'Entertainment_Type', 'Venue_Name',	'Venue_Address1', 'Venue_Address2', 'Venue_City', 'Venue_State', 'Venue_Zipcode', 'Venue_Website', 'LatLong', 'Contributions_Info',	'Make_Checks_Payable_To', 'Checks_Payable_To_Address', 'Committee_Id', 'RSVP_Info', 'Distribution_Paid_for_By'];																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																																		
    wri.writerow(newrowt)
    rows = cursor.fetchall()
    for row in rows:
        newrow = []
        for nr in row:
            newrow.append( nr )
        wri.writerow(newrow)


    f.close()








if __name__ == '__main__':
           main()

