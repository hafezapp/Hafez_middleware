import os
import stat
import pysodium
import binascii
import base64

class ReportEncryptor:
    def _store_key(self, crypto_key, key_filename):
        perm_other = stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH
        perm_group = stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP

        cumask = os.umask(perm_other | perm_group)
        
        with open(key_filename, 'w+') as key_file:
            key_file.write(binascii.hexlify(crypto_key))

        os.umask(cumask)

    def _load_key(self, key_filename):
        with open(key_filename, 'r') as key_file:
            return binascii.unhexlify(key_file.read())
    
    def _generate_and_store_receiver_key(self, receiver_key_filename):
        self.receiver_pub_key, sk = pysodium.crypto_box_keypair()

        #we don't care about the sk
        self._store_key(self.receiver_pub_key, receiver_key_filename + ".pub")
        self._store_key(sk, receiver_key_filename)

    def __init__(self, receiver_secret_key_filename):
        """
        Tries to load sender secret key and the receiver public key and
        stores them in class variables. If it fails, generate new ones and
        stores on the disk for later.

        Args:
        sender_secret_key_filename: the filename containing the sender
        secret key. 
        receiver_secret_key_filename: the function tries to retrieve 
        the public key from receiver_secret_key_filename+".pub" file.
        """
        try:
            self.receiver_pub_key = self._load_key(receiver_secret_key_filename+".pub")
        except IOError:
            self._generate_and_store_receiver_key(receiver_secret_key_filename)

        #seal box doesn't need further initiation and one can encrypt directly
        #by presenting the public key

    def encrypt_report(self, report):
        """
        Encrypts a report using libnacl public encryption

        Args:
        report: The report as json string

        Returns:
        The encrypted blob of the report in base64 encoding ready for submission
        """
        return base64.b64encode(pysodium.crypto_box_seal(report, self.receiver_pub_key))

    # def encrypt_attachment(self, attachment):
    #     """
    #     Encrypts a binary attachment using libnacl public encryption
    #     and return the result in base64

    #     Args:
    #     attachment: the attachment in the following binary format

    #     |attachment_id (8 bytes)|client_id: (8 bytes)|report_id: (8 bytes)|
    #     |time-stamp:YYYY-MM-DDThh:mm:ss|Type: 8 chars|attachment data....|

    #     Returns:
    #     The encrypted blob of the attachment in base64 encoding
    #     """
    #     return base64.encodestring(self.report_box.encrypt(report))
        

if __name__ == "__main__":
    import pdb
    #pdb.set_trace()
    # Define a sample report to send
    sample_report = '{report_body=b"During the first days of November, students and followers of Mohammad Ali Taheri, founder of the Erfane Halgheh in various cities such as Mashhad, Gorgan, Kermanshah, Karaj, Shiraz, Tehran and Isfahan in support of the prisoners of conscience and expressing their concern about his situation, went to rallies.", name="HRANA", email="keyvan.rafiee@hra-iran.org", telegram="idontknow", bindata1={type="png", value="SGFwcHkgYmlydGhkYXkgdm1vbg=="}'

    report_encryptor = ReportEncryptor("app_signing_key", "server_encryption_key")
    print "encrypted report:", report_encryptor.encrypt_report(sample_report)
