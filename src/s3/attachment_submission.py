from __future__ import print_function

import json
import urllib
import ssl
import boto3

import s3_settings

s3 = boto3.client('s3')

#name: reportivist-report
#lambda file.handler: report_submission.reportivist_report_submission_handler
#description: S3 trigger gets activated on  reportivist reports submitted to S3 and re-submit them to the middle server.
def reportivist_attachment_submission_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))

    #authenticate ourselves
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile="s3_client.crt.pem", keyfile="s3_client.key.pem")

    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        resubmission_url = "https://" + REPORTIVIST_MIDDLEWARE_ADDRESS + ":" + REPORTIVIST_MIDDLEWARE_S3_PORT + "/" + ATTACHMENT_RESUBMISSION_ENDPOINT
        #we basically resubmit to intermediate server
        #api doc http://docs.aws.amazon.com/sdkforruby/api/Aws/S3/Types/GetObjectOutput.html
        submission_response = urllib.urlopen(resubmission_url, response['Body'].read(), context=ssl_context)
        return submission_response.getcode()
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
