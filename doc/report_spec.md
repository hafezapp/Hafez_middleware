# Report

  report is constructed in json format before encryption, it consists of
  
  report_body: text variable length
  name: text 255 char
  email: text 255 char
  telegram: text 255 char
  submission_time: text format YYYY-MM-DDThh:mm:ss
  client_id: text 255 char of a google cloud messaging registeration token.
  report_id: text 16 char random identifier of the report

# Attachemnet

  attachements are construted in two parts meta data and attachment binary data in following formats

## Attachment meta data
    attachment_id: 16 char random identifier of the attachment.
    report_id: text 16 char random identifier of the report the attachment is belong to.
    client_id: text 255 char of a google cloud messaging registeration token.
    submission_time: text format YYYY-MM-DDThh:mm:ss
    encryption_key:  text 64 char base64ed of AES256 key which encrypts the attachment data in counter mode
    attachment_type: text of mime type of the attachment

## Attachment data
    attached_data: a file field contains the attachment data encrypted in AES counter mode. It is submitted using multipart along side of the encrypted blob of meta data.


# Encrypted Blob:

The both report and attchment meta data is submitted as a encrypted blob in the following format. This is to minimize the risk of compromising the confidentiality of the report through TLS based man-in-the-middle attack such as serving invalid certificate or injecting invalid CA in the client device. It also protect the data confidentiality in case of using CDNs as the front end. 

  client_version: note that we do not encrypt the client_version as a part of the blob
                  because in our model to assure its integrity via authenticated encryption
                  as the integrity of the submission is solemly protected by TLS
                  (in contrast to its confidentiality which is protected by public
                   encryption).
                          
  submission_time: text format YYYY-MM-DDThh:mm:ss
  encryption_key_id: integer identifying the public key used to encrypt the encrypted blob.
  encrypted_blob: text is the base64ed encrypted blob of the json set of fields of the actual submission the encryption is based on libsodium crypto_box_sealed (Key exchange: X25519, Encryption: XSalsa20 stream cipher).
  
