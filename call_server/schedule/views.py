from flask import (Blueprint, request, jsonify)

from ..extensions import cache
from .models import ScheduleCall

schedule = Blueprint('schedule', __name__, url_prefix='/schedule')
