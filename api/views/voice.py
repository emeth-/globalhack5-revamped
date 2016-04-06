from django.http import HttpResponse
import datetime
import json
from api.models import Citation, Violation
from dateutil import parser
from django.db.models import Q
import sys
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

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

    try:
        if 'citation_number' not in request.session and 'drivers_license' not in request.session:

            if 'citation_license_request_sent' not in request.session:

                request.session['citation_license_request_sent'] = True
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Gather timeout="20" method="GET">
                                <Say>Welcome to the St. Louis Regional Municipal Court System Helpline! Please enter your citation number or driver's license number followed by the pound sign.</Say>
                            </Gather>
                        </Response>
                        '''
                return HttpResponse(twil, content_type='application/xml', status=200)

            else:
                sms_from_user = request.GET['Digits']

                try:
                    potential_citation_number = int(sms_from_user)
                except:
                    potential_citation_number = -1

                citation_in_db = Citation.objects.filter(Q(citation_number=potential_citation_number) | Q(drivers_license_number_phone=sms_from_user))

                if not citation_in_db.exists():

                    twil = '''<?xml version="1.0" encoding="UTF-8"?>
                            <Response>
                                <Gather timeout="20" method="GET">
                                   <Say>Sorry, that was not found in our database, please try entering your citation number or driver's license number again followed by the pound sign.</Say>
                                </Gather>
                            </Response>
                            '''
                    return HttpResponse(twil, content_type='application/xml', status=200)

                else:
                    request.session['citation_number'] = citation_in_db[0].citation_number
                    twil = '''<?xml version="1.0" encoding="UTF-8"?>
                            <Response>
                                <Gather timeout="20" method="GET">
                                    <Say>Your citation has been found. To verify your identity, please enter your month of birth followed by the pound sign.</Say>
                                </Gather>
                            </Response>
                            '''
                    return HttpResponse(twil, content_type='application/xml', status=200)

        elif 'dob_month' not in request.session:
            sms_from_user = request.GET['Digits']

            request.session['dob_month'] = sms_from_user
            twil = '''<?xml version="1.0" encoding="UTF-8"?>
                    <Response>
                        <Gather timeout="20" method="GET">
                            <Say>Please enter your day of birth followed by the pound sign.</Say>
                        </Gather>
                    </Response>
                    '''
            return HttpResponse(twil, content_type='application/xml', status=200)

        elif 'dob_date' not in request.session:
            sms_from_user = request.GET['Digits']

            request.session['dob_date'] = sms_from_user
            twil = '''<?xml version="1.0" encoding="UTF-8"?>
                    <Response>
                        <Gather timeout="20" method="GET">
                            <Say>Please enter your year of birth followed by the pound sign.</Say>
                        </Gather>
                    </Response>
                    '''
            return HttpResponse(twil, content_type='application/xml', status=200)

        elif 'dob_year' not in request.session:
            sms_from_user = request.GET['Digits']
            request.session['dob_year'] = sms_from_user

            full_birthday = request.session['dob_month'] + "/" + request.session['dob_date'] + "/" + request.session['dob_year']

            try:
                citation_in_db = Citation.objects.filter(citation_number=request.session['citation_number']).filter(date_of_birth=parser.parse(full_birthday))
            except:
                del request.session['dob_month']
                del request.session['dob_date']
                del request.session['dob_year']
                exc_type, exc_value, exc_traceback = sys.exc_info()
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Say>Error: {error_message}. Please try again. Please enter your month of birth followed by the pound sign.</Say>
                        </Response>
                        '''
                twil = twil.replace("{error_message}", exc_value.message)
                return HttpResponse(twil, content_type='application/xml', status=200)


            if not citation_in_db.exists():

                del request.session['dob_month']
                del request.session['dob_date']
                del request.session['dob_year']
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Gather timeout="20" method="GET">
                                <Say>Sorry, that date of birth was not associated with the citation number specified. Please try again. Please enter your month of birth followed by the pound sign.</Say>
                            </Gather>
                        </Response>
                        '''
                return HttpResponse(twil, content_type='application/xml', status=200)

            else:
                request.session['dob'] = full_birthday
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Gather timeout="20" method="GET">
                                <Say>Thank you, that matches our records. As a final form of verification, please enter your last name followed by the pound sign.</Say>
                            </Gather>
                        </Response>
                        '''
                return HttpResponse(twil, content_type='application/xml', status=200)

        elif 'last_name' not in request.session:

            sms_from_user = request.GET['Digits']

            citation_in_db = Citation.objects.filter(citation_number=request.session['citation_number']).filter(date_of_birth=parser.parse(request.session['dob'])).filter(last_name_phone=sms_from_user)

            if not citation_in_db.exists():

                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Gather timeout="20" method="GET">
                                <Say>Sorry, that last name was not associated with the citation number specified. Please try again.</Say>
                            </Gather>
                        </Response>
                        '''
                return HttpResponse(twil, content_type='application/xml', status=200)

            else:
                request.session['last_name'] = sms_from_user

                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Gather timeout="20" method="GET" numDigits="1">
                                <Say>{ticket_info}</Say>
                                <Say>For a list of violations, press 1. For citation information, press 2. For options on how to pay outstanding fines, press 3</Say>
                            </Gather>
                        </Response>
                        '''
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
                ticket_info = "You have a court hearing on " + str(citation_in_db[0].court_date).split(" ")[0] + ", at " + str(citation_in_db[0].court_location) + ", located at " + str(citation_in_db[0].court_address) + " . "
                if has_warrant:
                    ticket_info += " You have an outstanding warrant. "
                else:
                    ticket_info += " You do not have an outstanding warrant. "
                ticket_info += "You currently have an outstanding balance of " + str(total_owed) + " dollars. "
                twil = twil.replace("{ticket_info}", ticket_info)
                return HttpResponse(twil, content_type='application/xml', status=200)

        else:
            sms_from_user = request.GET['Digits']

            citation_in_db = Citation.objects.filter(citation_number=request.session['citation_number'])
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

            twil = '''<?xml version="1.0" encoding="UTF-8"?>
                    <Response>
                        <Gather timeout="20" method="GET" numDigits="1">
                            '''
            if sms_from_user == '1':
                #break down in violations
                for v in violations_in_db:
                    twil += '<Say> {violation_info}</Say>'
                    violation_info = "Your violation is " + str(v.violation_description) + ", with a fine amount of " + str(v.fine_amount) + " dollars and a court cost of " + str(v.court_cost) + " dollars"
                    twil = twil.replace('{violation_info}',violation_info)

            elif sms_from_user == '2':
                #citation information
                twil += '<Say>{citation_info}</Say>'
                citation_info = "Your citation number is " + str(citation_obj['citation_number']) + ", and its date is " + str(citation_obj['citation_date']).split(' ')[0]
                twil = twil.replace('{citation_info}',citation_info)

            elif sms_from_user == '3':
                #ticket payment
                twil += "<Say>To pay by phone, call (314) 382-6544. To pay in person, go to Missouri Fine Collection Center, P.O. Box 104540, Jefferson City, MO 65110. For community service options, visit YourSTLCourts.com or contact your judge to see if you are eligible.</Say>"

            else:
                twil += "<Say>You have entered an invalid option.</Say>"

            twil += """
                            <Say>For a list of violations, press 1. For citation information, press 2. For options on how to pay outstanding fines, press 3</Say>
                        </Gather>
                    </Response>
                   """
            return HttpResponse(twil, content_type='application/xml', status=200)
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print exc_value.message
