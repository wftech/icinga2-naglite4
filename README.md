# icinga2-naglite4

This is [Naglite3] rewrite for Icinga2 using Icinga2 API. 

## Requirements

Python3.6+, Icinga2API, Flask, humanize.

## How to start

Create `icinga2-api.ini` from provided example. Do provide CA certificate
to silence certs.

### Start in debug mode 

    FLASK_APP=main FLASK_DEBUG=1 pipenv run flask run

### Start in production mode

Use `gunicorn` to start WSGI object `main:app`

## License

BSD-2   

[Naglite3]: https://github.com/saz/Naglite3
