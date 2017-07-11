import hashlib
from datetime import datetime

from ..extensions import db

from sqlalchemy_utils.types import phone_number

class Blocklist(db.Model):
    # stops
    __tablename__ = 'admin_blocklist'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True))
    expires = db.Column(db.Interval)
    phone_number = db.Column(phone_number.PhoneNumberType(), nullable=True)
    ip_address = db.Column(db.String(16), nullable=True)

    def __init__(self, phone_number=None, ip_address=None):
        self.timestamp = datetime.utcnow()
        self.phone_number = phone_number
        self.ip_address = ip_address

    def is_active(self):
        return self in Blocklist.query_active().all()

    @classmethod
    def query_active(cls):
        # pass timezone conversions to the database
        return Blocklist.query.filter(
            datetime.utcnow() <= (Blocklist.timestamp + Blocklist.expires)
        )

    @classmethod
    def user_blocked(cls, phone_number, ip_address):
        """
        Takes a phone number and/or IP address, check it against blocklist
        """
        active_blocks = cls.query_active()
        if not active_blocks.count():
            # exit early if no blocks defined
            return False

        matching_blocks = cls.query_active().filter(
            (Blocklist.phone_number == phone_number) |
            (Blocklist.ip_address == ip_address)
        ).all()

        if matching_blocks:
            return True
        return False

