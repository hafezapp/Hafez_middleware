from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from django.db import models

import server_settings #info needed for submitting to the civicrm server, accessing S3, etc
import requests
import pythoncivicrm
import logging
import datetime

from civicrm_utils import CiviCRMUtils

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your models here.
class EncryptedBlob(models.Model):
    """
    Model to contain the reports submitted by the reportivis app. The 
    report for now is only contains the IP of submitter, their security 
    token and the
    """
    client_version = models.CharField(
        null=False,
        blank=False,
        max_length=8,
        verbose_name=_('The version of the client submitting the report'))

    submission_time = models.DateTimeField(
        auto_now=True,
        max_length=255,
        verbose_name=_('Time of Submission'))

    encryption_key_id = models.BigIntegerField(
        null=True,
        blank=False,
        verbose_name=_('The encrypted key id'))

    encrypted_blob = models.TextField(
        null=True,
        blank=False,
        verbose_name=_('The encrypted data'))
    
    security_token = models.CharField(
        null=True,
        blank=True,
        max_length=256,
        verbose_name=_('Security token'))

    attachment_data = models.FileField(
        null=True,
        blank=True,
        verbose_name=_('optional encrypted attachment for media files'))


class Report(models.Model):
    """
    Model to contain the reports after decrypting the reportivis app submission
    """
    report_id = models.CharField(
        blank=False,
        max_length=16,
        verbose_name=_('report validation and identification in hex'))

    client_id = models.CharField(
        blank=False,
        max_length = 255,
        verbose_name=_('client anonymous identification in hex'))

    submission_time = models.DateTimeField(
        verbose_name=_('Time of Submission'))

    report_body = models.TextField(null=True,
            blank=True,
            verbose_name = _('The text of the report'))

    reporter_name = models.CharField(null=True,
            blank=True,
            max_length=1024,
            verbose_name = _('The name of the reporter'))
    
    reporter_email =     models.EmailField(null=True,
            blank=True,
            verbose_name = _('The email of the reporter'))

    reporter_telegram = models.CharField(null=True,
            blank=True,
            max_length=1024,
            verbose_name = _('The telegram handle of the reporter'))

    civicrm_utils = CiviCRMUtils()
    civi_timeout = server_settings.CIVICRM_TIME_OUT

    def _cook_report_subject(self):
        """
        generate a report subject of approperiate length
        from information submitted
        """
        report_subject = datetime.datetime.today().strftime('%Y-%m-%d') + "- "
        if (self.reporter_email):
            report_subject += self.reporter_email + " -"
            
        if len(report_subject) < server_settings.DEFAULT_SUBJECT_LENGTH:
            subject_availble_length = server_settings.DEFAULT_SUBJECT_LENGTH - len(report_subject)
            report_subject += self.report_body[0:min(max(self.report_body.find("\n"),subject_availble_length), len(self.report_body))]
        else:
            report_subject = report_subject[0:server_settings.DEFAULT_SUBJECT_LENGTH]

        return report_subject

    def save(self, *args, **kwargs):
        """
        overriding save because we don't want to save stuff
        on the local machine rather to submit them to the civicrm 
        server.
        """
        #prepare subject
        report_subject = self._cook_report_subject()
        
        url = server_settings.CIVICRM_REST_SERVER + server_settings.CIVICRM_REST_API_URL
        civicrm = pythoncivicrm.CiviCRM(url, server_settings.CIVICRM_SITE_KEY, server_settings.CIVICRM_API_KEY, timeout=self.civi_timeout, use_ssl=True)

        #creation of the case and setting custom fields doesn't work simultanously
        #we need to update them sequentially.
        try:
            result = civicrm.create("case",
                        contact_id = '4',   
                        subject = report_subject,
                        case_type = "hr_report",
                        start_date = str(self.submission_time),
                        details = self.report_body
                )
        
            # api.CustomValue.create = "{\"entity_type\":\"Case\",\"custom_7\":"+ self.report_id +  "}", #custom_7 = self.report_id,
            civicrm.setvalue("case", result[0]['id'], "custom_7", self.report_id)
            civicrm.setvalue("case", result[0]['id'], "custom_8", self.client_id)
            #civicrm.setvalue("case", result[0]['id'], "api.Activity.create", "{ activity_type_id : 'Open Case', assignee_id: '19'}")
            
            if (not result):
                raise ValueError("initial report submission failed")
            
            #now we retrieve the creation activity to assign it to the notifier robot.
            case_id = result[0]['id']
            activity_id = self.civicrm_utils.get_activity_id(case_id)
            if (not activity_id):
                raise ValueError("the submitted attachment is associated with an incomplete report")

            civicrm.assignactivity("hrana", activity_id, "contact_id", server_settings.CIVICRM_NOTIFICATION_BOT_ID)
            
        except requests.exceptions.ConnectionError as e:
            logger.warning("unable to store the report in civicrm database: " + e)
            raise RuntimeError("unable to store the report in civicrm database: " + e)
        except:
            raise RuntimeError("error while submititng the report")

class ReportAttachment(models.Model):
    """
    Model to contain the attachment after decrypting the reportivis app submission
    """
    report_id = models.CharField(
        blank=False,
        max_length=16,
        verbose_name=_('report validation and identification in hex'))

    client_id = models.CharField(
        blank=False,
        max_length=255,
        verbose_name=_('client anonymous identification in hex'))

    encryption_key =  models.CharField(null=False,
            blank=False,
            max_length=64,
            verbose_name = _('The secret symmetric key to which the attachement is encrypted'), default=bytes('0'))

    submission_time = models.DateTimeField(
        verbose_name=_('Time of Submission'))

    attachment_type = models.CharField(null=True,
            blank=True,
            max_length=8,
            verbose_name = _('The type of the attachment'))

    attached_data = models.FileField(null=False,
            blank=False,
            verbose_name = _('The binary data which is need to be attached to the case'))
    civicrm_utils = CiviCRMUtils()
    civi_timeout = server_settings.CIVICRM_TIME_OUT

    def save(self, *args, **kwargs):
        """
        overriding save because we don't want to save stuff
        on the local machine rather to submit them to the civicrm 
        server.
        """
        case_id = self.civicrm_utils.get_case_id(self.report_id)
        if (not case_id):
            raise ValueError("no submitted report is associated with the submitted attachment")
            
        activity_id = self.civicrm_utils.get_activity_id(case_id)
        if (not activity_id):
            raise ValueError("the submitted attachment is associated with an incomplete report")

        url = server_settings.CIVICRM_REST_SERVER + server_settings.CIVICRM_REST_API_URL
        civicrm = pythoncivicrm.CiviCRM(url, server_settings.CIVICRM_SITE_KEY, server_settings.CIVICRM_API_KEY, timeout=None, use_ssl=True)
        try:
            slash_pos = self.attachment_type.find("/")
            if (slash_pos == -1) :
                attachment_extension = self.attachment_type
            else :
                attachment_extension = self.attachment_type[slash_pos + 1:]
                                                            
            civicrm.create("attachment",
                            entity_table = "civicrm_activity",
                            entity_id = activity_id,
                            name = self.attachment_id + "." + attachment_extension,
                            #uri = ""self.attachment_id + "." + attachment_extension,
                            #description = self.attachment_id + "." + attachment_extension,
                            mime_type = self.attachment_type,
                            content = self.attachment_data)
            
        except requests.exceptions.ConnectionError as e:
            logger.warning("unable to store the attachment in civicrm database: " + e.message)
            raise RuntimeError("unable to store the attachement in civicrm database: " + e.message)
        except requests.exceptions.ReadTimeout as e:           
            logger.warning("unable to store the attachment in civicrm database: " + e.message)
            raise RuntimeError("unable to store the attachement in civicrm database: " + e.message)
        except:
            raise RuntimeError("unable to store the attachement in civicrm database")
            

                           
