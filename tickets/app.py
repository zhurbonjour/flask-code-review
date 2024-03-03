import os

from datetime import datetime

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask import request
from config import TICKET_STATUS_OPEN, TICKET_STATUS_CLOSED, TICKET_STATUS_ANSWERED, TICKET_STATUS_WAITING_FOR_ANSWER, \
    TICKET_STATUSES, REDIS_TICKET_COMMENTS_KEY_TEMPLATE
import json
import redis
import uuid


app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)
r = redis.Redis(db=1)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(256), nullable=False)
    text = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(256), nullable=False)
    status = db.Column(db.String(16), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime)

    def __repr__(self):
        return '<Ticket id={} subject={}>'.format(self.id, self.subject)

    def to_dict(self):
        return {
            'id': self.id,
            'subject': self.subject,
            'text': self.text,
            'email': self.email,
            'status': self.status,
            'created_at': str(self.created_at) if self.created_at else None,
            'updated_at': str(self.updated_at) if self.updated_at else None,
        }


@app.route('/tickets', methods=['GET'])
def ticket_all():
    tickets = Ticket.query.all()
    return json.dumps([t.to_dict() for t in tickets])


@app.route('/ticket/<int:ticket_id>', methods=['GET'])
def ticket_get(ticket_id):
    ticket = Ticket.query.filter_by(id=ticket_id).one()
    return ticket.to_dict()


@app.route('/ticket', methods=['POST'])
def ticket_create():
    req_json = request.json
    new_ticket = Ticket(
        subject=req_json.get('subject'),
        text=req_json.get('text'),
        email=req_json.get('email'),
        status=TICKET_STATUS_OPEN
    )
    db.session.add(new_ticket)
    db.session.commit()
    return new_ticket.to_dict()


def ticket_status_is_valid(ticket, new_status):
    if ticket.status == TICKET_STATUS_CLOSED:
        return False

    result = (ticket.status == TICKET_STATUS_OPEN and new_status in (TICKET_STATUS_ANSWERED, TICKET_STATUS_CLOSED)) or\
             (ticket.status == TICKET_STATUS_ANSWERED and new_status in (TICKET_STATUS_CLOSED,
                                                                         TICKET_STATUS_WAITING_FOR_ANSWER))
    return result


@app.route('/ticket/update_status/<int:ticket_id>', methods=['POST'])
def ticket_update_status(ticket_id):
    new_status = request.json.get('status')
    if new_status not in TICKET_STATUSES:
        return f"Bad status {new_status}. Allowed statuses are: {', '.join(TICKET_STATUSES)}", 400

    ticket = Ticket.query.filter_by(id=ticket_id).one()
    if not ticket_status_is_valid(ticket, new_status):
        return f"Wrong status {new_status} after status {ticket.status}", 400

    db.session.query(Ticket).filter_by(id=ticket_id).update({Ticket.status: new_status, Ticket.updated_at: datetime.utcnow()})
    db.session.commit()
    updated_ticket = db.session.query(Ticket).filter_by(id=ticket_id).one()
    return updated_ticket.to_dict()


@app.route('/ticket/delete/<int:ticket_id>', methods=['POST'])
def ticket_delete(ticket_id):
    db.session.query(Ticket).filter_by(id=ticket_id).delete()
    db.session.commit()
    return "Success"


@app.route('/ticket/<int:ticket_id>/comments', methods=['GET'])
def ticket_comments_get(ticket_id):
    comments = r.lrange(REDIS_TICKET_COMMENTS_KEY_TEMPLATE.format(ticket_id=ticket_id), 0, -1)
    comments = [json.loads(c.decode('utf-8')) for c in comments]
    return json.dumps(comments)


@app.route('/ticket/<int:ticket_id>/comment', methods=['POST'])
def ticket_comment_create(ticket_id):
    req_json = request.json
    comment_dict = {
        "id": str(uuid.uuid4()),
        "text": req_json.get('text'),
        "email": req_json.get('email'),
        "created_at": str(datetime.utcnow()),
    }
    r.rpush(REDIS_TICKET_COMMENTS_KEY_TEMPLATE.format(ticket_id=ticket_id), json.dumps(comment_dict))
    return comment_dict


@app.route('/ticket/<int:ticket_id>/comment/<comment_id>/delete', methods=['POST'])
def ticket_comment_delete(ticket_id, comment_id):
    comments = r.lrange(REDIS_TICKET_COMMENTS_KEY_TEMPLATE.format(ticket_id=ticket_id), 0, -1)
    comments = [json.loads(c.decode('utf-8')) for c in comments]
    new_comments = list(filter(lambda c: c['id'] != comment_id, comments))
    new_comments_dumped = [json.dumps(c) for c in new_comments]
    r.delete(REDIS_TICKET_COMMENTS_KEY_TEMPLATE.format(ticket_id=ticket_id))
    r.lpush(REDIS_TICKET_COMMENTS_KEY_TEMPLATE.format(ticket_id=ticket_id), *new_comments_dumped)
    return json.dumps(new_comments)


if __name__ == '__main__':
    app.run(host="0.0.0.0")
