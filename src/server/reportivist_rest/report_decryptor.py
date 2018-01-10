import pysodium
import binascii
import base64

class ReportDecryptor:
    def __init__(self, receiver_secret_key_filename, receiver_key_id = ""):
        """
        Loads the report decryption secret key for decrypting report and the app's
        public key to verify the intergrity of the subscription and intitiate a 
        decryption box.  Throws an exception if it fails.

        Args:
        receiver_secret_key_filename: The name of the file which contains
        the decryption key in libnacl format
        sender_secret_key_filename: the filename containing the sender
        secret key. 
        receiver_secret_key_filename: the function tries to retrieve 
        the public key from receiver_secret_key_filename+".pub" file.
        receiver_key_id: hash of the receiver public key which identifies the key used for encryption
        sender_key_id: hash of the sender public key which identifies the key used for signing

        TODO:: use receiver_key_id and sender_key_id to implement multiple key senarios
        """
        self.receiver_secret_key = self._load_key(receiver_secret_key_filename)
        self.receiver_pub_key = self._load_key(receiver_secret_key_filename + ".pub")


    def _load_key(self, key_filename):
        """
        load the secret key
        """
        try:
            with open(key_filename, 'r') as key_file:
                return binascii.unhexlify(key_file.read())
        except IOError as e:
            raise RuntimeError("Unable open the key file")
        
    def decrypt_report(self, encrypted_report_blob):
        """
        Decrypt a report blob using libnacl public encryption or throw 
        an exception if in case there is a problem with decryption

        Args:
        report: The report as json string in base64 encoding

        Returns:
        The original report.
        """
        return pysodium.crypto_box_seal_open(base64.decodestring(encrypted_report_blob), self.receiver_pub_key, self.receiver_secret_key)
