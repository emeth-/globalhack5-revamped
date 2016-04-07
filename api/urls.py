from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', "api.views.load_frontend"),
    url(r'^get_info_special$', "api.views.get_info"),

    url(r'^sms_received$', "api.views.sms_received"),
    
    url(r'^call_received$', "api.views.call_received"),

)