import os
basedir = os.path.abspath(os.path.dirname(__file__))

TICKET_STATUS_OPEN = 'открыт'
TICKET_STATUS_CLOSED = 'закрыт'
TICKET_STATUS_ANSWERED = 'отвечен'
TICKET_STATUS_WAITING_FOR_ANSWER = 'ожидает ответа'
TICKET_STATUSES = (TICKET_STATUS_OPEN, TICKET_STATUS_CLOSED, TICKET_STATUS_ANSWERED, TICKET_STATUS_WAITING_FOR_ANSWER)
REDIS_TICKET_COMMENTS_KEY_TEMPLATE = "ticket_comment:{ticket_id}"


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = "postgresql://ticketsuser:easypass@localhost/tickets"


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
