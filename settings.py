import tornado.options
import logging

tornado.options.define("environment", default="dev", help="environment")

options = {
    'dev' : {
        'logging_level' : logging.DEBUG,
        'accounts' : {
            'default': {
                'sendgrid_url' : 'https://sendgrid.com/api/mail.send.json',
                'api_user' : '',
                'api_key' : '',
            }
        }
    }, 
    'prod' : {
        'logging_level' : logging.DEBUG,
        'accounts' : {
            'default': {
                'sendgrid_url' : 'https://sendgrid.com/api/mail.send.json',
                'api_user' : '',
                'api_key' : '',
            }
        }
    }
}

default_options = {
}

def env():
    return tornado.options.options.environment

def get(key):
    env = tornado.options.options.environment 
    if env not in options: 
        raise Exception("Invalid Environment (%s)" % env) 
    v = options.get(env).get(key) or default_options.get(key)
    if callable(v):
        return v()
    return v

