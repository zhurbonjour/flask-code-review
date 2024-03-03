from app import Ticket, db, Comment
from config import TICKET_STATUS_OPEN

new_ticket = Ticket(
    subject="Test ticket #1",
    text="This is a sample test ticket #1",
    email="sample@mail.com",
    status=TICKET_STATUS_OPEN
)
db.session.add(new_ticket)
first_ticket_comment = Comment(
    text="This is a sample test ticket #1 comment",
    email="comment@mail.com",
    ticket_id=1
)
db.session.add(first_ticket_comment)
db.session.commit()
