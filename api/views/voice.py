from django.http import HttpResponse
import datetime
from api.models import Citation, Violation
from dateutil import parser
from django.db.models import Q
from django.contrib.auth import logout
from custom_decorators import print_errors

@print_errors
def contact_received_voice(request):

    #Automatically reset user's sessions if they haven't communicated in 5 minutes
    if 'last_validated' in request.session:

        session_expiry = (parser.parse(request.session.get('last_validated', '2000-01-01')) + datetime.timedelta(minutes=5))
        if session_expiry < datetime.datetime.now():
            print "Session expired! Session expiry time", session_expiry, " | current time", datetime.datetime.now()
            del request.session['last_validated']
            logout(request)
    else:
        request.session['last_validated'] = datetime.datetime.now().isoformat()
        
    if 'Body' in request.POST and request.POST['Body'].lower() == "restart":
        logout(request)

    sms_from_user = request.GET.get('Digits', '')

    if 'auth_type' not in request.session:
        #New user!
        request.session['auth_type'] = "citation_or_license"
        twil = '''<?xml version="1.0" encoding="UTF-8"?>
                <Response>
                    <Gather timeout="20" method="GET"><Say>Welcome to the St. Louis Regional Municipal Court System Helpline! Please enter your citation number or driver's license number followed by the pound sign. If you do not have either, just hit the pound sign.</Say></Gather>
                </Response>
                '''
        return HttpResponse(twil, content_type='application/xml', status=200)
    else:
        #Existing user, trying to authenticate
        print "Existing user, trying to authenticate"
        if not request.session.get('authenticated', False):
            if request.session['auth_type'] == "citation_or_license":
                #Check and see if valid citation number / driver's license number.
                print "Check and see if valid citation number / driver's license number."
                try:
                    potential_citation_number = int(sms_from_user)
                except:
                    potential_citation_number = -1
                
                citation_in_db = Citation.objects.filter(Q(citation_number=potential_citation_number) | Q(drivers_license_number=sms_from_user))
            
                if not citation_in_db.exists():
                    #if not, change auth_type to last_name and send user message to send last name
                    print "if not, change auth_type to last_name and send user message to send last name"
                    request.session['auth_type'] = "last_name"
                    twil = '''<?xml version="1.0" encoding="UTF-8"?>
                            <Response>
                                <Gather timeout="20" method="GET"><Say>Please enter your last name followed by the pound sign.</Say></Gather>
                            </Response>
                            '''
                    return HttpResponse(twil, content_type='application/xml', status=200)
                else:
                    #if so, user authenticated and move on to next step [authenticated=True]
                    print "if so, user authenticated and move on to next step [authenticated=True][1]"
                    request.session['citation_number'] = citation_in_db[0].citation_number
                    request.session['authenticated'] = True
                
            elif request.session['auth_type'] == "last_name":
                
                #Check and make sure users exist with that last name
                print "Check and make sure users exist with that last name"
                citation_in_db = Citation.objects.filter(last_name__iexact=sms_from_user)
            
                if not citation_in_db.exists():
                    #if not, throw error to user
                    print "if not, throw error to user2"
                    request.session['auth_type'] = "last_name"
                    twil = '''<?xml version="1.0" encoding="UTF-8"?>
                            <Response>
                                <Gather timeout="20" method="GET"><Say>No citations found with that last name. Goodbye!</Say></Gather>
                            </Response>
                            '''
                    logout(request)
                    return HttpResponse(twil, content_type='application/xml', status=200)
                else:
                    #if so, change auth_type to dob and send user message to send dob
                    print "if so, change auth_type to dob and send user message to send dob"
                    request.session['last_name'] = sms_from_user
                    request.session['auth_type'] = "dob_month"
                    twil = '''<?xml version="1.0" encoding="UTF-8"?>
                            <Response>
                                <Gather timeout="20" method="GET"><Say>Please enter your month of birth followed by the pound sign.</Say></Gather>
                            </Response>
                            '''
                    return HttpResponse(twil, content_type='application/xml', status=200)
                
            elif request.session['auth_type'] == "dob_month":
                
                request.session['dob_month'] = sms_from_user
                request.session['auth_type'] = "dob_date"
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Gather timeout="20" method="GET"><Say>Please enter your date of birth followed by the pound sign.</Say></Gather>
                        </Response>
                        '''
                return HttpResponse(twil, content_type='application/xml', status=200)
            
            elif request.session['auth_type'] == "dob_date":
                
                request.session['dob_date'] = sms_from_user
                request.session['auth_type'] = "dob_year"
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Gather timeout="20" method="GET"><Say>Please enter your year of birth followed by the pound sign.</Say></Gather>
                        </Response>
                        '''
                return HttpResponse(twil, content_type='application/xml', status=200)
                    
            elif request.session['auth_type'] == "dob_year":
                
                #Check and make sure citations  exist with that last name and dob
                print "Check and make sure citations  exist with that last name and dob"
                request.session['dob_year'] = sms_from_user
                full_birthday = request.session['dob_month'] + "/" + request.session['dob_date'] + "/" + request.session['dob_year']
                citation_in_db = Citation.objects.filter(last_name__iexact=request.session['last_name']).filter(date_of_birth=parser.parse(full_birthday))
            
                if not citation_in_db.exists():
                    #if not, throw error to user
                    print "if not, throw error to user3"
                    twil = '''<?xml version="1.0" encoding="UTF-8"?>
                            <Response>
                                <Gather timeout="20" method="GET"><Say>No citations found with that last name and date of birth. Goodbye!</Say></Gather>
                            </Response>
                            '''
                    logout(request)
                    return HttpResponse(twil, content_type='application/xml', status=200)
                else:
                    #if so, authenticated=True and move on to next step
                    request.session['dob'] = full_birthday
                    del request.session['auth_type']
                    request.session['citation_number'] = citation_in_db[0].citation_number
                    request.session['authenticated'] = True

        #user authenticated, send citation info!
        print "user authenticated, send citation info!"
        citation_in_db = Citation.objects.filter(citation_number=int(request.session['citation_number']))
        violations_in_db = Violation.objects.filter(citation_number=request.session['citation_number'])

        citation_obj = list(citation_in_db.values())[0]
        citation_obj['violations'] = list(violations_in_db.values())
        
        total_owed = float(0)
        has_warrant = False
        for v in violations_in_db:
            total_owed += float(v.fine_amount.strip('$').strip()) if v.fine_amount.strip('$').strip() else 0
            total_owed += float(v.court_cost.strip('$').strip()) if v.court_cost.strip('$').strip() else 0
            if v.warrant_status:
                has_warrant = True
        citation_obj['total_owed'] = total_owed
        citation_obj['has_warrant'] = has_warrant
        
        twil = '''<?xml version="1.0" encoding="UTF-8"?><Response><Gather timeout="20" method="GET" numDigits="1">'''
        if sms_from_user == "1":
            for v in violations_in_db:
                twil += '<Say> {violation_info}</Say>'
                violation_info = "Your violation is " + str(v.violation_description) + ", with a fine amount of $" + str(v.fine_amount or 0) + " and a court cost of $" + str(v.court_cost or 0)
                twil = twil.replace('{violation_info}',violation_info)
        elif sms_from_user == "2":
            twil += '<Say>{citation_info}</Say>'
            citation_info = "Your citation number is " + str(citation_obj['citation_number']) + ", and its date is " + str(citation_obj['citation_date']).split(' ')[0]
            twil = twil.replace('{citation_info}',citation_info)
        elif sms_from_user == "3":
            twil += "<Say>To pay by phone, call (314) 382-6544. To pay in person, go to Missouri Fine Collection Center, P.O. Box 104540, Jefferson City, MO 65110. For community service options, visit YourSTLCourts.com or contact your judge to see if you are eligible.</Say>"
        else:
            #send general citation info
            twil += '''<Say>{ticket_info}</Say>'''
            ticket_info = "You have a court hearing on " + str(citation_in_db[0].court_date).split(" ")[0] + ", at " + str(citation_in_db[0].court_location) + ", located at " + str(citation_in_db[0].court_address) + " . "
            if has_warrant:
                ticket_info += " You have an outstanding warrant. "
            else:
                ticket_info += " You do not have an outstanding warrant. "
            ticket_info += "You currently have an outstanding balance of $" + str(total_owed) + ". "
            twil = twil.replace("{ticket_info}", ticket_info)
        twil += "<Say>For a list of violations, send 1. For citation information, send 2. For options on how to pay outstanding fines, send 3. For additional assistance, please call the court clerk at (314) 382-6544</Say>"

        twil += "</Gather></Response>"
        return HttpResponse(twil, content_type='application/xml', status=200)
        