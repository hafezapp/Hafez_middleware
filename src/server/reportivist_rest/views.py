from django.shortcuts import render
import json

# Create your views here.
from django.core.exceptions import PermissionDenied, RequestDataTooBig
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from reportivist_rest.models import EncryptedBlob
from reportivist_rest.models import Report
from reportivist_rest.serializers import ReportBlobSerializer, AttachmentBlobSerializer

import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)

class JSONResponse(HttpResponse):
    """
    An HttpResponse that renders its content into JSON.
    """
    def __init__(self, data, **kwargs):
        content = JSONRenderer().render(data)
        kwargs['content_type'] = 'application/json'
        super(JSONResponse, self).__init__(content, **kwargs)

def post_report(report_dict):
    serializer = ReportBlobSerializer(data=report_dict)
    if serializer.is_valid():
        try:
            serializer.save()
        except RuntimeError as e:
            logger.warning("error in serialization: " + e.message)
            return JSONResponse(e.message, status=400)
        except PermissionDenied as e:
            logger.warning("client is not allowed to post: " + e.message)
            return JSONResponse(e.message, status=401)
        except RequestDataTooBig as e:
            logger.warning("post is too big: " + e.message)
            return JSONResponse(e.message, status=413)
        except:
            logger.warning("unhandled error occured")
            return JSONResponse("Error in submission", status=400)

        return JSONResponse("CREATED", status=201)
            
    return JSONResponse(serializer.errors, status=400)

def post_attachment(attachment_meta, s3_submission=False, attachment_data=None):
    serializer = AttachmentBlobSerializer(data=attachment_meta)
    if serializer.is_valid():
        #serializer.save(datafile=self.request.data.get('datafile'))
        try:
            serializer.save(attachment_data=attachment_data, s3_submission=s3_submission)
        except RuntimeError as e:
            logger.warning("error in serialization: " + e.message)
            return JSONResponse(e.message, status=400)
        except PermissionDenied as e:
            logger.warning("client is not allowed to post: " + e.message)
            return JSONResponse(e.message, status=401)
        except RequestDataTooBig as e:
            logger.warning("post is too big: " + e.message)
            return JSONResponse(e.message, status=413)
        except:
            logger.warning("unhandled error occured")
            return JSONResponse("Error in submission", status=400)

        return JSONResponse("CREATED", status=201)
            
    return JSONResponse(serializer.errors, status=400)

@csrf_exempt
def submit_report_blob(request):
    """
    resubmits the report to civicrm server on POST. 
    refuses to reply to GET.
    """
        #uncomment to make temperoray opening the end point to
        #make sure nothing is stored in the db
        ### these lines are only to test that
        ### reports are not recorded locally.
        # if request.method == 'GET':
        # reportblobs = ReportBlob.objects.all()
        # blobserializer = ReportBlobSerializer(reportblobs, many=True)
        # reports = Report.objects.all()
        # serializer = ReportSerializer(reports, many=True)
        # serializer.data.extend(blobserializer.data)
        # return JSONResponse(serializer.data)

    if request.method == 'POST':
        return post_report(request.POST)
    else:
        return JSONResponse("Method not allowed", status=405)

@csrf_exempt
def s3_submit_report_blob(request):
    """
    resubmits the report received from aws lambda to civicrm server on POST. 
    refuses to reply to GET.
    """
    #note that the request is passed through nginx so the client can't
    #manipulate the header.
    if request.META.get('HTTP_VERIFIED') != 'SUCCESS':
        return JSONResponse("Unauthorized", status=401)
    
    if request.method == 'POST':
        dict_body = json.loads(request.body)
        return post_report(dict_body)
    else:
        return JSONResponse("Method not allowed", status=405)

@csrf_exempt
def submit_attachment_blob(request):
    """
    resubmits the attachment to civicrm server on POST
    as new activity on the report case
    """
    if request.method == 'POST':
        return post_attachment(request.POST, attachment_data=request.FILES['attachment_data'])
    else:
        return JSONResponse("Method not allowed", status=405)

@csrf_exempt
def s3_submit_attachment_blob(request):
    """
    resubmits the attachment to civicrm server on POST
    as new activity on the report case
    """
    if request.META.get('HTTP_VERIFIED') != 'SUCCESS':
        return JSONResponse("Unauthorized", status=401)
    
    if request.method == 'POST':
        #we should get the attachment from amazon
        return post_attachment(json.loads(request.body), s3_submission=True)
    else:
        return JSONResponse("Method not allowed", status=405)

