from rest_framework import serializers, status

from django.core.exceptions import PermissionDenied, RequestDataTooBig
from django.contrib.sessions.backends.db import SessionStore
from rest_framework import serializers

from reportivist_rest.models import EncryptedBlob, Report, ReportAttachment

import server_settings

import pythoncivicrm
import json
import hashlib
import datetime
import requests

from report_decryptor import ReportDecryptor
from binascii import hexlify

import requests

#moves these to the setting
class ReportBlobSerializer(serializers.Serializer):
    """
    Receives a report blob decrypt and submit it to the db 
    server. Note that we can't simply inherit from ModelSerializer.
    as we need to decrypt the report blob and gets the new fields not
    the same as those submitted.
    """
    client_version = serializers.CharField(required=True, allow_blank=False, max_length=8)
    submission_time = serializers.DateTimeField()
    encrypted_blob = serializers.CharField(required=False, allow_blank=True)
    encryption_key_id = serializers.CharField(required=True, allow_blank=False, max_length=256)
    encryption_token = serializers.CharField(required=False, allow_blank=True, max_length=256)

    def _validate_client_id(self, client_id):
        gcm_headers={'Content-Type':'application/json', 'Authorization':'key='+server_settings.GCM_API_SERVER_KEY}
        gcm_validation_data = {'dry_run': True, 'to': client_id}

        api_call = requests.post(
            server_settings.GCM_VALIDATION_URL,
            headers= gcm_headers,
            json=gcm_validation_data
        )
        if api_call.status_code != 200:
            raise RuntimeError("failed to authenticate client id")
        
        results = json.loads(api_call.content)
        if ('success' not in results.keys() or results['success'] != 1):
            pass
            raise PermissionDenied("invalid client id")

    def _verify_client_no_of_submission_quota_usage(self, client_record, today_date):
        no_of_submission_today = today_date + "_no"
        if (not client_record.has_key(no_of_submission_today)):
            client_record[no_of_submission_today] = 0

        if (client_record[no_of_submission_today] >= server_settings.DAILY_QUOTA_FOR_NO_OF_SUBMISSIONS):
            raise PermissionDenied("too many submission for today")


    def _verify_client_size_of_submission_quota_usage(self, client_record, today_date, submission_size):
        total_size_of_submission_today = today_date + "_size"
        if (not client_record.has_key(total_size_of_submission_today)):
            client_record[total_size_of_submission_today] = 0

        if (client_record[total_size_of_submission_today] + submission_size >= server_settings.DAILY_QUOTA_FOR_SIZE_OF_SUBMISSIONS):
            raise PermissionDenied("cumulative size of submissions has passed for today")

    def _gen_session_key(self, client_id):
        #because the part before the colon in the gcm id is arbitary
        #we only take the part after the colon. We use sha256 of that
        hash_object = hashlib.sha256(client_id.split(':')[-1])
        return hash_object.hexdigest()

    def _get_client_submission_record(self, client_id):
        client_session_key = self._gen_session_key(client_id)
        client_record = SessionStore(client_session_key)
        if (not client_record.exists(client_session_key)):
            client_record.save(must_create=True)

        return client_record

    def create(self, validated_data):
        """
        Create report instance and submit it to civicrm server, given the validated data.
        """
        instance = Report()
        try: #loading the encryption key
            report_decryptor = ReportDecryptor(server_settings.RECEIVER_SECRET_KEY_FILENAME, receiver_key_id = validated_data.get('encryption_key_id'))
        except RuntimeError as e:
            raise RuntimeError("unable to retrieve the report encryption key")

        #the correct way of doing this to invoke the serializer
        #of the report here for validation 
        try:
            decrypted_report = json.loads(report_decryptor.decrypt_report(validated_data.get('encrypted_blob')))
        except:
            raise RuntimeError("submitted Encrypted blob is badly formated")
        if ((not 'client_id' in decrypted_report.keys()) or
                (not 'report_body' in decrypted_report.keys())):
            raise RuntimeError("both client id and report body are required")

        instance.client_id = decrypted_report['client_id']
        #first we check if the request is coming from a valid client
        self._validate_client_id(instance.client_id);

        #now that we have a valid client_id we retrieve client_session
        #make sure the client has not passed their submission quota
        client_record = self._get_client_submission_record(instance.client_id)
        today_key = datetime.datetime.today().strftime('%Y-%m-%d')
        self._verify_client_no_of_submission_quota_usage(client_record, today_key);

        try:
            instance.submission_time = validated_data.get('submission_time')
            instance.report_id = decrypted_report['report_id']
            instance.report_body = decrypted_report['report_body']
            instance.reporter_name = decrypted_report['name']
            instance.reporter_email = decrypted_report['email']
            instance.reporter_telegram = decrypted_report['telegram']
        except:
            raise RuntimeError("Error in the set of submitted fields")
        #reject if the report is too large
        #all other fields are size limited in civicrm so the repor_body is the only concern
        if (len(decrypted_report['report_body']) > server_settings.MAX_SIZE_OF_SUBMISSION):
            raise RequestDataTooBig("too big of a report")
        
        instance.report_body = decrypted_report['report_body']
        instance.save()

        #counting client's daily submission 
        client_record[today_key+"_no"] += 1
        client_record.save()
        
        return instance

class AttachmentBlobSerializer(ReportBlobSerializer):
    """
    Receives a attachment blob decrypts and submits it to the db 
    server. Note that we can't simply inherit from ModelSerializer.
    as we need to decrypt the report blob and gets the new fields not
    the same as those submitted.
    """
    client_version = serializers.CharField(required=True, allow_blank=False, max_length=8)
    submission_time = serializers.DateTimeField()
    encrypted_blob = serializers.CharField(required=False, allow_blank=True)
    encryption_key_id = serializers.CharField(required=True, allow_blank=False, max_length=256)
    encryption_token = serializers.CharField(required=False, allow_blank=True, max_length=256)

    def _decrypt_attachement(self, encryption_key, iv, encrypted_attachment_data ):
        from Crypto.Cipher import AES
        from Crypto.Util import Counter
        import base64
        import binascii

        decryptor = AES.new(base64.decodestring(encryption_key), AES.MODE_CTR,
        counter=Counter.new(128, initial_value=int(binascii.hexlify(base64.decodestring(iv)),16)))

        return decryptor.decrypt(encrypted_attachment_data)

    def _retrieve_attachment_from_s3(self, attachment_id):
        from requests_aws4auth import AWS4Auth
        import server_settings

        aws_auth = AWS4Auth(server_settings.AWS_KEY_ID, server_settings.AWS_SECRET_KEY, server_settings.AWS_REGION, 's3')
        try:
            attachment_resp = requests.get('https://'+ server_settings.S3_SUBMISSION_BUCKET + '.s3.amazonaws.com/'+ server_settings.S3_ATTACHMENT_FOLDER + "/" + attachment_id, auth = aws_auth)
            return attachment_resp
        except:
            logger.warning('unable to retrieve the attachment body from aws')
            return ''
    
    def create(self, validated_data):
        """
        Create and return a new `Snippet` instance, given the validated data.
        """
        instance = ReportAttachment()
        try:
            attachment_decryptor = ReportDecryptor(server_settings.RECEIVER_SECRET_KEY_FILENAME, receiver_key_id = validated_data.get('encryption_kdey_id'))
        except RuntimeError as e:
            raise RuntimeError("unable to retrieve the report encryption key")
        
        try:
            decrypted_attachment = json.loads(attachment_decryptor.decrypt_report(validated_data.get('encrypted_blob')))
        except:
            raise RuntimeError("submitted Encrypted blob is badly formated")

        if (not 'client_id' in decrypted_attachment.keys()):
            raise RuntimeError("client id is required")

        #first we check if the request is coming from a valid client
        instance.client_id = decrypted_attachment['client_id']
        self._validate_client_id(instance.client_id);

        try:
            instance.attachment_id = decrypted_attachment['attachment_id']
            instance.report_id = decrypted_attachment['report_id']
            instance.submission_time = validated_data.get('submission_time')
            instance.attachment_type = decrypted_attachment['attachment_type']

        except:
            raise RuntimeError("Error in the set of submitted fields")

        if (validated_data.get('attachment_data')):
            instance.attachment_data = self._decrypt_attachement(decrypted_attachment['encryption_key'], decrypted_attachment['encryption_iv'], validated_data.get('attachment_data').read())
        elif (validated_data.get('s3_submission') == True):
            data_retreival_response = self._retrieve_attachment_from_s3(instance.attachment_id)
            if data_retreival_response.status_code != 200:
                raise RuntimeError('Failed to retrieve attachment data from S3 due to Error %s'
                                                                                      %data_retreival_response.status_code)

            instance.attachment_data = self._decrypt_attachement(decrypted_attachment['encryption_key'], decrypted_attachment['encryption_iv'], data_retreival_response.content)
        else:
            raise RuntimeError("submission includes attachment meta data without  body")

        current_submission_size = len(instance.attachment_data)
        if (current_submission_size > server_settings.MAX_SIZE_OF_SUBMISSION):
            raise RequestDataTooBig("too big of a attachment")

        #now that we have a valid client_id we retrieve client_session
        #make sure the client has not passed their size of submission quota
        #otherwise raise an exception
        client_record = self._get_client_submission_record(instance.client_id)
        today_key = datetime.datetime.today().strftime('%Y-%m-%d')
        self._verify_client_size_of_submission_quota_usage(client_record, today_key, current_submission_size);

        instance.save()

        client_record[today_key+"_size"] += current_submission_size
        client_record.save()

        return instance
        
