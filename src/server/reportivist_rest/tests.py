# -*- coding: utf-8 -*-
from django.test import TestCase

# Create your tests here.
import re
import json
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from binascii import hexlify, unhexlify
import base64
import copy

import test_secrets
import server_settings #to know the limits to bypass them
# End Points to test for list method

API_VERISON = "1"
ep_list = [
    '/api/v'+API_VERISON+'/submit-report/',
    '/api/v'+API_VERISON+'/submit-attachment/',
    '/api/v'+API_VERISON+'/s3/submit-report/'
]

submit_report_ep = ep_list[0]
submit_attachment_ep = ep_list[1]
s3_submit_report_ep = ep_list[2]

class APISubmissionTests(APITestCase):
    """
        Check for API End Point availability and Submit sample reports
    """
    report_id = int("edeaaff3f1774adb", 16)
    client_id = test_secrets.client_id
    enc_key_id = int("7e391bc362d7d6fb", 16)
    sample_report = {
        'report_body':b"It shall be known that during the first days of November, students and followers of Mohammad Ali Taheri, founder of the Erfane Halgheh in various cities such as Mashhad, Gorgan, Kermanshah, Karaj, Shiraz, Tehran and Isfahan in support of the prisoners of conscience and expressing their concern about his situation, went to rallies.",
        'name':"HRANA",
        'email':"someone@test.com",
        'telegram':"idontknow",
        'time-stamp': '2018-01-30T14:34:15',
        'client_id': client_id,
        'report_id': hex(report_id)[2:-1]
    }

    post_sample_submission = {
        'client_version': '0.1',
        'submission_time': '2018-01-09 12:04:16',
        'encryption_key_id': '5ccf6df7306718164450ab250e0c44f0a00ece70c45f3ceceb0d6f4e7f03fa50',
        'encrypted_blob': '',
        'security_token': '',
        }

    sample_attachment = {
        'attachment_id' : 'd4803184d4803186',
        'client_id': client_id,
        'report_id': hex(report_id)[2:-1],
        'encryption_key': 'SGFwcHkgYmlydGhkYXkgdm1vbg==',
        'encryption_iv': 'SGFwcHkgYmlydGhkYXkgdm1vbg==',
        'time-stamp':'2016-11-29T14:34:15',
        'attachment_type': 'image/jpeg',

        }

    sample_attachment_file = "reportivist_rest/test/sample_attachment_file.dat"


    sample_big_report = {
        'report_id':"edeaaff3f1774ad5",
        'client_id': client_id,
        'report_body':u"In the town where I was born Lived a man who sailed to sea And he told us of his life In the land of submarines So we sailed up to the sun Till we found a sea of green And we lived beneath the waves In our yellow submarine  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine  And our friends are all aboard Many more of them live next door And the band begins to play  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine  (Full speed ahead Mr. Boatswain, full speed ahead Full speed ahead it is, Sergeant. Cut the cable, drop the cable Aye, Sir, aye Captain, captain)  As we live a life of ease Every one of us has all we need Sky of blue and sea of green In our yellow submarine  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine In the town where I was born Lived a man who sailed to sea And he told us of his life In the land of submarines So we sailed up to the sun Till we found a sea of green And we lived beneath the waves In our yellow submarine  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine  And our friends are all aboard Many more of them live next door And the band begins to play  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine  (Full speed ahead Mr. Boatswain, full speed ahead Full speed ahead it is, Sergeant. Cut the cable, drop the cable Aye, Sir, aye Captain, captain)  As we live a life of ease Every one of us has all we need Sky of blue and sea of green In our yellow submarine  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine In the town where I was born Lived a man who sailed to sea And he told us of his life In the land of submarines So we sailed up to the sun Till we found a sea of green And we lived beneath the waves In our yellow submarine  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine  And our friends are all aboard Many more of them live next door And the band begins to play  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine  (Full speed ahead Mr. Boatswain, full speed ahead Full speed ahead it is, Sergeant. Cut the cable, drop the cable Aye, Sir, aye Captain, captain)  As we live a life of ease Every one of us has all we need Sky of blue and sea of green In our yellow submarine  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine In the town where I was born Lived a man who sailed to sea And he told us of his life In the land of submarines So we sailed up to the sun Till we found a sea of green And we lived beneath the waves In our yellow submarine  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine  And our friends are all aboard Many more of them live next door And the band begins to play  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine  (Full speed ahead Mr. Boatswain, full speed ahead Full speed ahead it is, Sergeant. Cut the cable, drop the cable Aye, Sir, aye Captain, captain)  As we live a life of ease Every one of us has all we need Sky of blue and sea of green In our yellow submarine  We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine We all live in a yellow submarine Yellow submarine, yellow submarine Far out in the uncharted backwaters of the unfashionable end of the western spiral arm of the Galaxy lies a small unregarded yellow sun.  Orbiting this at a distance of roughly ninety-two million miles is an utterly insignificant little blue green planet whose ape-descended life forms are so amazingly primitive that they still think digital watches are a pretty neat idea.  This planet has—or rather had—a problem, which was this: most of the people on it were unhappy for pretty much of the time. Many solutions were suggested for this problem, but most of these were largely concerned with the movements of small green pieces of paper, which is odd because on the whole it wasn’t the small green pieces of paper that were unhappy.  And so the problem remained; lots of the people were mean, and most of them were miserable, even the ones with digital watches.  Many were increasingly of the opinion that they’d all made a big mistake in coming down from the trees in the first place. And some said that even the trees had been a bad move, and that no one should ever have left the oceans.  And then, one Thursday, nearly two thousand years after one man had been nailed to a tree for saying how great it would be to be nice to people for a change, one girl sitting on her own in a small cafe in Rickmansworth suddenly realized what it was that had been going wrong all this time, and she finally knew how the world could be made a good and happy place. This time it was right, it would work, and no one would have to get nailed to anything.  Sadly, however, before she could get to a phone to tell anyone about it, a terribly stupid catastrophe occurred, and the idea was lost forever.  This is not her story.  But it is the story of that terrible stupid catastrophe and some of its consequences.  It is also the story of a book, a book called The Hitch Hiker’s Guide to the Galaxy—not an Earth book, never published on Earth, and until the terrible catastrophe occurred, never seen or heard of by any Earthman.  Nevertheless, a wholly remarkable book.  In fact it was probably the most remarkable book ever to come out of the great publishing houses of Ursa Minor—of which no Earthman had ever heard either.  Not only is it a wholly remarkable book, it is also a highly successful one—more popular than the Celestial Home Care Omnibus, better selling than Fifty More Things to do in Zero Gravity, and more controversial than Oolon Colluphid’s trilogy of philosophical blockbusters Where God Went Wrong, Some More of God’s Greatest Mistakes and Who is this God Person Anyway?  In many of the more relaxed civilizations on the Outer Eastern Rim of the Galaxy, the Hitch Hiker’s Guide has already supplanted the great Encyclopedia Galactica as the standard repository of all knowledge and wisdom, for though it has many omissions and contains much that is apocryphal, or at least wildly inaccurate, it scores over the older, more pedestrian work in two important respects.  First, it is slightly cheaper; and secondly it has the words DON’T PANIC inscribed in large friendly letters on its cover.  But the story of this terrible, stupid Thursday, the story of its extraordinary consequences, and the story of how these consequences are inextricably intertwined with this remarkable book begins very simply.  It begins with a house.",
        'name':"",
        'email':"",
        'telegram':""
    }

    def test_submit_report(self):
        """
            Test the end points for submitting report is working.
        """
        from .test.encrypted_blob_generator import ReportEncryptor
        url = submit_report_ep;
        test_post_sample_submission = copy.copy(self.post_sample_submission)
        test_post_sample_submission['encrypted_blob']=ReportEncryptor('reportivist_rest/test/server_encryption_key').encrypt_report(json.dumps(self.sample_report))
        resp = self.client.post(url, test_post_sample_submission)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def test_submit_attachment(self):
        """
            Test the end points for submitting attachment related to the submitted report.
        """
        from .test.encrypted_blob_generator import ReportEncryptor
        url = submit_attachment_ep

        #now we need to turn the attachment data to binary to simulate real
        #app condition
        # binary_submission = bytearray(unhexlify(hex(self.sample_attachment['attachment_id'])[2:-1])) + bytearray(unhexlify(hex(self.sample_attachment['client_id'])[2:-1])) + bytearray(unhexlify(hex(self.sample_attachment['report_id'])[2:-1])) + bytearray(self.sample_attachment['time-stamp']) + bytearray(self.sample_attachment['attachment_type'] + chr(0)*(8-len(self.sample_attachment['attachment_type'])))

        #first we need to decode the base64 as it is just facilitating the submission.
        # binary_submission += bytearray(base64.decodestring(self.sample_attachment['attachment_data']))

        #encrypting the attechement
        from Crypto import Random
        from Crypto.Cipher import AES
        from Crypto.Util import Counter
        import binascii

        iv = Random.new().read(16)
        enc_key = Random.new().read(32)
        test_sample_attachment = copy.copy(self.sample_attachment)
        test_sample_attachment['encryption_key'] = base64.encodestring(enc_key)
        test_sample_attachment['encryption_iv'] = base64.encodestring(iv)

        #we have all meta data ready now
        test_post_sample_submission = copy.copy(self.post_sample_submission)
        test_post_sample_submission['encrypted_blob'] = ReportEncryptor('reportivist_rest/test/server_encryption_key').encrypt_report(json.dumps(test_sample_attachment))

        encryptor = AES.new(enc_key, AES.MODE_CTR,  counter=Counter.new(128, initial_value=int(binascii.hexlify(iv), 16)))

        with open(self.sample_attachment_file, "rb") as data_file:
            with open(self.sample_attachment_file + ".enc", "w") as encrypted_file:
                encrypted_file.write(encryptor.encrypt(data_file.read()))
                
        with open(self.sample_attachment_file + ".enc") as encrypted_data:
            test_post_sample_submission['attachment_data'] = encrypted_data 

            resp = self.client.post(url, test_post_sample_submission)
            self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

    def no_test_submit_report_and_verify_not_stored_locally(self):
        """
            submits a report and then it query the database
            to make sure no report is stored.

            This test doesn't pass without modifying the server
            as the server is designed not to respond to get 
            requests.
        """
        from .test.encrypted_blob_generator import ReportEncryptor
        url = submit_report_ep;
        self.post_sample_submission['encrypted_blob']=ReportEncryptor('reportivist_rest/test/server_encryption_key').encrypt_report(json.dumps(self.sample_report))

        resp = self.client.post(url, self.post_sample_submission)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.json(), [])
        
    def no_test_submit_big_report(self):
        from .test.encrypted_blob_generator import ReportEncryptor
        url = submit_report_ep;
        self.post_sample_submission['encrypted_blob']=ReportEncryptor( 'reportivist_rest/test/server_encryption_key').encrypt_report(json.dumps(self.sample_big_report))
        resp = self.client.post(url, self.post_sample_submission)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)


    def test_submit_report_with_invalid_client_id(self):
        """
            Tests that reporting with invalid id is impossible
        """
        from .test.encrypted_blob_generator import ReportEncryptor
        url = submit_report_ep;
        test_post_sample_submission = copy.copy(self.post_sample_submission)
        tampered_report = copy.copy(self.sample_report)
        #tampering the client id
        tampered_report['client_id'] = tampered_report['client_id'][:-1] + '7'
        test_post_sample_submission['encrypted_blob']=ReportEncryptor('reportivist_rest/test/server_encryption_key').encrypt_report(json.dumps(tampered_report))
        resp = self.client.post(url, test_post_sample_submission)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_submit_to_s3_endpoint_without_cert(self):
        """
            Tests that reporting with invalid id is impossible
        """
        from .test.encrypted_blob_generator import ReportEncryptor
        url = s3_submit_report_ep;
        test_post_sample_submission = copy.copy(self.post_sample_submission)
        test_post_sample_submission['encrypted_blob']=ReportEncryptor('reportivist_rest/test/server_encryption_key').encrypt_report(json.dumps(self.sample_report))
        resp = self.client.post(url, test_post_sample_submission)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def no_test_too_many_submission(self):
        """
        Tests that submitting too many report bans the client
        """
        from .test.encrypted_blob_generator import ReportEncryptor
        import time
        url = submit_report_ep;
        test_post_sample_submission = copy.copy(self.post_sample_submission)
        test_post_sample_submission['encrypted_blob']=ReportEncryptor('reportivist_rest/test/server_encryption_key').encrypt_report(json.dumps(self.sample_report))
        for i in range(0, server_settings.DAILY_QUOTA_FOR_NO_OF_SUBMISSIONS+1):
            resp = self.client.post(url, test_post_sample_submission)
            time.sleep(1) # just to make sure other tests finishes before we ran out of quota of submission.

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

