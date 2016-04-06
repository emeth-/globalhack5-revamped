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

    citation_in_db = False
    
    if request.GET.get('important_number', False):
        #User submitted either a citation number or driver's license number
        try:
            fake_citation_number = int(request.GET['important_number'])
        except:
            fake_citation_number = 0
            
        citation_in_db = Citation.objects.filter(Q(citation_number=fake_citation_number) | Q(drivers_license_number=request.GET['important_number']))
        
        if not citation_in_db.exists():
            return HttpResponse(json.dumps({
                "status": "error",
                "message": "No citations found with that citation number / driver's license number."
            }, default=json_custom_parser), content_type='application/json', status=200)

    if request.GET.get('last_name', False) and request.GET.get('date_of_birth', False):
        #User submitted last name and date of birth
        
        citation_in_db = Citation.objects.filter(last_name__iexact=request.GET['last_name']).filter(date_of_birth=parser.parse(request.GET['date_of_birth']))
        
        if not citation_in_db.exists():
            return HttpResponse(json.dumps({
                "status": "error",
                "message": "No citations found with that name/dob."
            }, default=json_custom_parser), content_type='application/json', status=200)

    if not citation_in_db:
        return HttpResponse(json.dumps({
            "status": "error",
            "message": "Missing required fields!"
        }, default=json_custom_parser), content_type='application/json', status=200)

    all_citations = []
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
        all_citations.append(citation_obj)
        i += 1

    return HttpResponse(json.dumps({
        "status": "success",
        "citations": all_citations
    }, default=json_custom_parser), content_type='application/json', status=200)


def load_frontend(request):
    return HttpResponseRedirect("/static/index.html")

def json_custom_parser(obj):
    if isinstance(obj, datetime.datetime) or isinstance(obj, datetime.date):
        dot_ix = 19
        return obj.isoformat()[:dot_ix]
    else:
        raise TypeError(obj)