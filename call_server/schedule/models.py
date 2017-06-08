from datetime import datetime

from ..extensions import db


class ScheduleCall(db.Model):
    # tracks outbound calls to target
    __tablename__ = 'schedule_call'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True))
    subscribed = db.Column(db.Boolean, default=True)

    time_to_call = db.Column(db.Time(timezone=True))
    last_called  = db.Column(db.DateTime(timezone=True))
    num_calls = db.Column(db.Integer)

    campaign_id = db.Column(db.ForeignKey('campaign_campaign.id'))
    campaign = db.relationship('Campaign')

    phone_number = db.Column(db.String(16))  # number to call, e164

    def __init__(self, campaign_id, phone_number, time=datetime.utcnow().time()):
        self.created_at = datetime.utcnow()
        self.campaign_id = campaign_id
        self.phone_number = phone_number
        self.time_to_call = time
        self.subscribed = True

    def __repr__(self):
        return u'<ScheduleCall for {}>'.format(self.campaign.name)


    def start_job(self):
        pass

    def stop_job(self):
        pass