from django.http import HttpResponse
import datetime
import json
from api.models import Citation, Violation
from dateutil import parser
from django.db.models import Q
import sys
from django.contrib.auth import logout
from django.http import HttpResponseRedirect

def get_info(request):

    if request.GET.get('important_number', False) and request.GET.get('last_name', False) and request.GET.get('date_of_birth', False):
        try:
            fake_citation_number = int(request.GET['important_number'])
        except:
            fake_citation_number = 0
        print "fake_citation_number", fake_citation_number
        citation_in_db = Citation.objects.filter(Q(citation_number=fake_citation_number) | Q(drivers_license_number=request.GET['important_number']))
        if not citation_in_db.exists():
            print ":("
            #return error, not found
            return HttpResponse(json.dumps({
                "status": "error",
                "message": "Citation not found in database."
            }, default=json_custom_parser), content_type='application/json', status=200)

    else:

        return HttpResponse(json.dumps({
            "status": "error",
            "message": "Not enough information to authenticate user. Please pass in Date of Birth, Last Name, AND either driver's license number or citation number."
        }, default=json_custom_parser), content_type='application/json', status=200)


    print "citation_in_db[0].drivers_license_number", citation_in_db[0].drivers_license_number
    citation_in_db = Citation.objects.filter(drivers_license_number=citation_in_db[0].drivers_license_number).filter(last_name__iexact=request.GET['last_name']).filter(date_of_birth=parser.parse(request.GET['date_of_birth']))

    if citation_in_db.exists():
        all_cites = []
        i = 0
        for c in citation_in_db:
            violations_in_db = Violation.objects.filter(citation_number=c.citation_number)
            citation_obj = list(citation_in_db.values())[i]
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
            all_cites.append(citation_obj)
            i += 1

        return HttpResponse(json.dumps({
            "status": "success",
            "citations": all_cites
        }, default=json_custom_parser), content_type='application/json', status=200)
    else:
        #return error, not found
        return HttpResponse(json.dumps({
            "status": "error",
            "message": "Citation not found in database."
        }, default=json_custom_parser), content_type='application/json', status=200)


def load_frontend(request):
    return HttpResponseRedirect("/static/index.html")
