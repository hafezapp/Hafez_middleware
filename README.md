^INSTALLATION:
------------

Here we explain the installation of middleware server for the reportivist project on a Debian Jessie machine. Firs step we install the necessary packages:

sudo apt-get update
sudo apt-get install git python python-pip python-dev build-essential python-django python-djangorestframework

we need libsodium but currently the debian repo version does not support crypto_box_seal and we need to install the latest version from source instead:

   wget https://download.libsodium.org/libsodium/releases/LATEST.tar.gz

   tar xvfz LATEST.tar.gz
   cd libsodium-1.0.xx
   ./configure --prefix=/usr
   make
   make install

## Install git-crypt:

You need to have git-crypt to be able to read the server credentials (private key, mysql password etc). Therefore youneed installed git-crypt before cloning the repo. You can install git-crypt as follows:

    curl https://codeload.github.com/AGWA/git-crypt/tar.gz/0.5.0 | tar xvz
    cd git-crypt-0.5.0
    make
    make install

Please note that only users in possession of predefined private keys are able to decrypt the credential of the server.

If not we can ask a person who has the credential to overwrite the following files to the cloned repo:

    encrypted: deployment/ca.key.pem
    encrypted: deployment/server.key.pem
    encrypted: deployment/caislean_reportivist_server
    encrypted: src/server/data/server_encryption_key
    encrypted: src/server/hrvr/settings.py
    encrypted: src/server/reportivist_rest/server_settings.py
    encrypted: src/server/reportivist_rest/test_secrets.py
    encrypted: src/s3/s3_settings.py
    encrypted: src/s3/s3_client.key.pem

you also need to take a backup of these files every time you pull the repo.

    cp deployment/ca.key.pem deployment/server.key.pem deployment/caislean_reportivist_server src/server/data/server_encryption_key src/server/hrvr/settings.py  src/server/reportivist_rest/server_settings.py src/server/reportivist_rest/test_secrets.py src/s3/s3_settings.py src/s3/s3_client.key.pem ~/server_secrets/

and after pulling
    cp ~/server_secrets/ca.key.pem deployment/ca.key.pem
    cp ~/server_secrets/server.key.pem deployment/server.key.pem
    cp ~/server_secrets/deployment/caislean_reportivist_server deployment/caislean_reportivist_server 
    cp ~/server_secrets/server_encryption_key src/server/data/server_encryption_key
    cp ~/server_secrets/settings.py src/server/hrvr/settings.py
    cp ~/server_secrets/server_settings.py src/server/reportivist_rest/server_settings.p
    cp ~/server_secrets/test_secrets.py src/server/reportivist_rest/test_secrets.py
    cp ~/server_secrets/s3_settings.py src/s3/s3_settings.py
    cp ~/server_secrets/s3_client.key.pem src/s3/s3_client.key.pem

Make sure you have the access right to the repo and then clone the repo:

    git clone git@github.com:hafezapp/hafez_middleware

Now we need to install all python dependancies:

    cd reportivist
    sudo pip install -r requirements.txt

    git-crypt unlock
    cd src/server/
    python manage.py makemigrations
    python manage.py migrate
    python manage.py runserver

If you want to access the server from external client (not localhost) you should run it as follows:

    python manage.py runserver 0.0.0.0:8000

## Testing

Before runnning test make sure the test client is using the correct public key server. You need a copy of data/server_encryption_key.pub in reportivist_rest/test directory.

you can run the tests using

    python manage.py test


## S3 Submission

S3 submission are done to api/v1/s3/submit-report (submit-attachment) api end point. The
S3 is authenticated with s3_client.crt.pem and should be signed by the cert residing
at /etc/nginx/cert/ca.crt.

## Security Audit
[Report](https://github.com/hafezapp/Hafez_middleware/blob/master/doc/Hafez%20Security%20Audit.pdf)

