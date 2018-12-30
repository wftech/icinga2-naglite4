# icinga2-naglite4

This is [Naglite3] rewrite for Icinga2 using Icinga2 API. 

## Requirements

Python3.6+, Icinga2API, Flask, humanize.

## How to start

Create `icinga2-api.ini` from provided example. 

To silence warning on certificates, provide CA certificate 
to INI file.  The certificate can be found on Icinga2 host
at `/var/lib/icinga2/ca/ca.crt`.

### Start in debug mode 

    FLASK_APP=main FLASK_DEBUG=1 pipenv run flask run

### Start in production mode

Use `gunicorn` to start WSGI object `main:app`

## License

APACHE 2

[Naglite3]: https://github.com/saz/Naglite3
