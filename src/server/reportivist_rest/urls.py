from django.conf.urls import url
from reportivist_rest import views

urlpatterns = [
    url(r'^api/v1/submit-report/$', views.submit_report_blob),
    url(r'^api/v1/submit-attachment/$', views.submit_attachment_blob),
    url(r'^api/v1/s3/submit-report/$', views.s3_submit_report_blob),
    url(r'^api/v1/s3/submit-attachment/$', views.s3_submit_attachment_blob)
]
