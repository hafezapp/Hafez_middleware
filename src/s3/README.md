to create the blob to submit to amazon lambda:

    zip report_submission.zip report_submission.py s3_client.crt.pem s3_client.key.pem
    zip attachment_submission.zip attachment_submission.py s3_client.crt.pem s3_client.key.pem
    