from django.http import HttpResponse
import datetime
import json
from api.models import Citation, Violation
from dateutil import parser
from django.db.models import Q
import sys
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

def contact_received(request):

    if 'Body' in request.POST and request.POST['Body'].lower() == "logout":
        logout(request)

    try:
        if 'citation_number' not in request.session and 'drivers_license' not in request.session:
            
            if 'citation_license_request_sent' not in request.session:
    
                request.session['citation_license_request_sent'] = True
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Message method="GET">Welcome to the St. Louis Regional Municipal Court System Helpline! Please enter your citation number or driver's license number.</Message>
                        </Response>
                        '''
                return HttpResponse(twil, content_type='application/xml', status=200)
    
            else:
                sms_from_user = request.POST['Body']
    
                try:
                    potential_citation_number = int(sms_from_user)
                except:
                    potential_citation_number = -1
    
                citation_in_db = Citation.objects.filter(Q(citation_number=potential_citation_number) | Q(drivers_license_number=sms_from_user))
    
                if not citation_in_db.exists():
    
                    twil = '''<?xml version="1.0" encoding="UTF-8"?>
                            <Response>
                                <Message method="GET">Sorry, that was not found in our database, please try entering your citation number or driver's license number again.</Message>
                            </Response>
                            '''
                    return HttpResponse(twil, content_type='application/xml', status=200)
    
                else:
                    request.session['citation_number'] = citation_in_db[0].citation_number
                    twil = '''<?xml version="1.0" encoding="UTF-8"?>
                            <Response>
                                <Message method="GET">Your citation has been found. To verify your identity, please enter your date of birth.</Message>
                            </Response>
                            '''
                    return HttpResponse(twil, content_type='application/xml', status=200)
    
        elif 'dob' not in request.session:
            sms_from_user = request.POST['Body']
    
            try:
                citation_in_db = Citation.objects.filter(citation_number=request.session['citation_number']).filter(date_of_birth=parser.parse(sms_from_user))
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Message method="GET">Error: {error_message}. Please try again.</Message>
                        </Response>
                        '''
                twil = twil.replace("{error_message}", exc_value.message)
                return HttpResponse(twil, content_type='application/xml', status=200)
                
    
            if not citation_in_db.exists():
    
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Message method="GET">Sorry, that date of birth was not associated with the citation number specified. Please try again.</Message>
                        </Response>
                        '''
                return HttpResponse(twil, content_type='application/xml', status=200)
    
            else:
                request.session['dob'] = sms_from_user
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Message method="GET">Thank you, that matches our records. As a final form of verification, please send your last name.</Message>
                        </Response>
                        '''
                return HttpResponse(twil, content_type='application/xml', status=200)
    
        elif 'last_name' not in request.session:
    
            sms_from_user = request.POST['Body']
    
            citation_in_db = Citation.objects.filter(citation_number=request.session['citation_number']).filter(date_of_birth=parser.parse(request.session['dob'])).filter(last_name__iexact=sms_from_user)
    
            if not citation_in_db.exists():
    
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Message method="GET">Sorry, that last name was not associated with the citation number specified. Please try again.</Message>
                        </Response>
                        '''
                return HttpResponse(twil, content_type='application/xml', status=200)
    
            else:
                request.session['last_name'] = sms_from_user
            
                twil = '''<?xml version="1.0" encoding="UTF-8"?>
                        <Response>
                            <Message method="GET">{ticket_info} \n For a list of violations, send 1. For citation information, send 2. For options on how to pay outstanding fines, send 3.</Message>
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
                ticket_info += "You currently have an outstanding balance of $" + str(total_owed) + ". "
                twil = twil.replace("{ticket_info}", ticket_info)
                return HttpResponse(twil, content_type='application/xml', status=200)
            
        else:
            sms_from_user = request.POST['Body']
            
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
                    <Response>'''
            if sms_from_user == '1':
                #break down in violations
                for v in violations_in_db:
                    twil += '<Message> {violation_info}</Message>'
                    violation_info = "Your violation is " + str(v.violation_description) + ", with a fine amount of $" + str(v.fine_amount) + " and a court cost of $" + str(v.court_cost)
                    twil = twil.replace('{violation_info}',violation_info)
                    
            elif sms_from_user == '2':
                #citation information
                twil += '<Message>{citation_info}</Message>'
                citation_info = "Your citation number is " + str(citation_obj['citation_number']) + ", and its date is " + str(citation_obj['citation_date']).split(' ')[0]
                twil = twil.replace('{citation_info}',citation_info)
                
            elif sms_from_user == '3':
                #ticket payment
                twil += "<Message>To pay by phone, call (314) 382-6544. To pay in person, go to Missouri Fine Collection Center, P.O. Box 104540, Jefferson City, MO 65110. For community service options, visit YourSTLCourts.com or contact your judge to see if you are eligible.</Message>"
                      
            else:
                twil += "<Message>For additional assistance, please call the court clerk at 314-382-6544</Message>"
                
            twil += "<Message>For a list of violations, send 1. For citation information, send 2. For options on how to pay outstanding fines, send 3.</Message>"

            twil += "</Response>"
            return HttpResponse(twil, content_type='application/xml', status=200)
            
    except:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print exc_value.message
