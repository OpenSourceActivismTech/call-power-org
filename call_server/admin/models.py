import hashlib
from datetime import datetime
import pytz

from ..extensions import db
from ..utils import utc_now

from sqlalchemy_utils.types import phone_number

class Blocklist(db.Model):
    # stops
    __tablename__ = 'admin_blocklist'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True))
    expires = db.Column(db.Interval)
    phone_number = db.Column(phone_number.PhoneNumberType(), nullable=True)
    ip_address = db.Column(db.String(16), nullable=True)
    hits = db.Column(db.Integer(), default=0)

    def __init__(self, phone_number=None, ip_address=None):
        self.timestamp = utc_now()
        self.phone_number = phone_number
        self.ip_address = ip_address

    def is_active(self):
        if self.expires:
            try:
                return utc_now() <= (self.timestamp + self.expires)
            except TypeError:
                # sqlite doesn't store timezones in the database
                # reset it manually
                aware_timestamp = self.timestamp.replace(tzinfo=pytz.utc)
                return utc_now() <= (aware_timestamp + self.expires)
        else:
            return True

    @classmethod
    def active_blocks(cls):
        return [b for b in Blocklist.query.all() if b.is_active()]
        # TODO defer timezone conversions to the database, for speed?
        #return Blocklist.query.filter(
        #    (utc_now() <= (Blocklist.timestamp + Blocklist.expires)) |
        #    (Blocklist.expires == None)
        #)

    @classmethod
    def user_blocked(cls, user_phone, user_ip, user_country='US'):
        """
        Takes a phone number and/or IP address, check it against blocklist
        """
        active_blocks = cls.active_blocks()
        if not active_blocks:
            # exit early if no blocks defined
            return False

        matching_blocks = [b for b in active_blocks if (
            b.phone_number == phone_number.PhoneNumber(user_phone, user_country) or
            b.ip_address == user_ip
        )]

        # TODO, do it in the database for speed
        #matching_blocks = cls.query_active().filter(
        #    (Blocklist.phone_number == phone_number) |
        #    (Blocklist.ip_address == ip_address)
        #).all()

        if matching_blocks:
            for b in matching_blocks:
                b.hits += 1
                db.session.add(b)
            db.session.commit()

            return True
        return False

