import datetime

from flask import (Blueprint, render_template, current_app, request,
                   flash, url_for, redirect, session, abort, jsonify)
from flask.json import JSONEncoder
from flask.ext.login import login_required
from flask_store.providers.temp import TemporaryStore

import sqlalchemy
from sqlalchemy.sql import func, desc

from twilio.util import TwilioCapability

from ..extensions import db
from ..political_data import COUNTRY_CHOICES
from ..utils import choice_items, choice_keys, choice_values_flat, duplicate_object

from .constants import EMPTY_CHOICES, STATUS_LIVE
from .models import (Campaign, Target, CampaignTarget,
                     AudioRecording, CampaignAudioRecording,
                     TwilioPhoneNumber)
from ..call.models import Call
from .forms import (CountryTypeForm, CampaignForm, CampaignAudioForm,
                    AudioRecordingForm, CampaignLaunchForm,
                    CampaignStatusForm, TargetForm)

campaign = Blueprint('campaign', __name__, url_prefix='/admin/campaign')


@campaign.before_request
@login_required
def before_request():
    # all campaign routes require login
    pass


@campaign.route('/')
def index():
    campaigns = Campaign.query.order_by(desc(Campaign.status_code), desc(Campaign.id)).all()
    calls = (db.session.query(Campaign.id, func.count(Call.id))
            .filter(Call.status == 'completed')
            .join(Call).group_by(Campaign.id))
    return render_template('campaign/list.html',
        campaigns=campaigns, calls=dict(calls.all()))


@campaign.route('/create', methods=['GET', 'POST'])
@campaign.route('/<int:campaign_id>/edit-type', methods=['GET', 'POST'])
def country_type(campaign_id=None):
    edit = False
    if campaign_id:
        edit = True

    if edit:
        campaign = Campaign.query.filter_by(id=campaign_id).first_or_404()
    else:
        campaign = None

    form = CountryTypeForm()
    form.campaign_country.choices = choice_items(COUNTRY_CHOICES)

    # set up a list for all campaign types in each country
    country_type_choices = dict()
    all_valid_choices = list()
    for country_code, country_name in COUNTRY_CHOICES:
        country_type_choices[country_code] = list()
        for campaign_type, type_name in Campaign.get_campaign_type_choices(country_code):
            country_type_choices[country_code].append((campaign_type, type_name))
            all_valid_choices.append((campaign_type, type_name))

    form.campaign_type.choices = choice_items(all_valid_choices)  # accepts all valid choices, but updates dynamically in view

    if form.validate_on_submit():
        country_code = form.campaign_country.data
        campaign_type = form.campaign_type.data
        campaign_language = form.campaign_language.data

        if campaign and country_code and campaign_type:
            campaign.country_code = country_code
            campaign.campaign_type = campaign_type
            campaign.campaign_language = campaign_language
            db.session.add(campaign)
            db.session.commit()
            return redirect(
                url_for('campaign.form', campaign_id=campaign.id)
            )
        elif country_code and campaign_type and campaign_language:
            return redirect(
                url_for('campaign.form',
                    country_code=country_code,
                    campaign_type=campaign_type,
                    campaign_language=campaign_language)
            )

    if edit:
        form.campaign_country.data = campaign.country_code
        form.campaign_type.data = campaign.campaign_type
        form.campaign_language.data = campaign.campaign_language

    return render_template('campaign/country_type.html',
        form=form, country_types=country_type_choices)

@campaign.route('/create/<string(length=2):campaign_language>-<string(length=2):country_code>/<string:campaign_type>', methods=['GET', 'POST'])
@campaign.route('/<int:campaign_id>/edit', methods=['GET', 'POST'])
def form(country_code=None, campaign_type=None, campaign_id=None, campaign_language=None):
    edit = False
    if campaign_id:
        edit = True

    if edit:
        campaign = Campaign.query.filter_by(id=campaign_id).first_or_404()
        campaign_data = campaign.get_campaign_data()
        form = CampaignForm(obj=campaign, campaign_data=campaign_data)
        form.campaign_country.data = campaign_data.country_code
    else:
        campaign = Campaign()
        campaign.country_code = country_code
        campaign.campaign_type = campaign_type
        campaign.campaign_language = campaign_language
        campaign_data = campaign.get_campaign_data()
        form = CampaignForm(campaign_data=campaign_data)
        form.campaign_country.data = country_code
        form.campaign_type.data = campaign_type

    # filter call in numbers on client side
    call_in_map = {}
    for number in TwilioPhoneNumber.available_numbers().filter_by(call_in_allowed=True):
        if campaign.id != number.call_in_campaign.id:
            call_in_map[number.id] = number.call_in_campaign.name
    form.phone_number_set.render_kw = { "data-call_in_map": JSONEncoder().encode(call_in_map) }

    # for fields with dynamic choices, set to empty here in view
    # will be updated in client
    form.target_set.choices = choice_items(EMPTY_CHOICES)

    if form.validate_on_submit():
        # can't use populate_obj with nested forms, iterate over fields manually
        for field in form:
            if field.name not in ['target_set', 'campaign_country', 'campaign_type']:
                setattr(campaign, field.name, field.data)

        # handle target_set nested data
        target_list = []
        for target_data in form.target_set.data:
            # create Target object
            target = Target()
            for (field, val) in target_data.items():
                setattr(target, field, val)
            db.session.add(target)
            target_list.append(target)

            # update or create CampaignTarget membership
            try:
                campaign_target = CampaignTarget.query.filter_by(campaign=campaign, target=target).one()
            except sqlalchemy.orm.exc.NoResultFound:
                # create a new one
                campaign_target = CampaignTarget()
                campaign_target.campaign = campaign
                campaign_target.target = target
            # update order
            campaign_target.order = target_data['order']

            db.session.add(campaign_target)
            db.session.commit()

        # save campaign.target_set
        setattr(campaign, 'target_set', target_list)
        db.session.add(campaign)
        db.session.commit()

        # if allow_call_in, set call_in_allowed on phone_number_set
        if campaign.allow_call_in:
            for n in campaign.phone_number_set:
                n.call_in_allowed = n.set_call_in(campaign)
                db.session.add(n)
            db.session.commit()
        # TODO, allow_call_in on just one number?

        if edit:
            flash('Campaign updated.', 'success')
        else:
            flash('Campaign created.', 'success')

        if form.submit_skip_audio.data:
            return redirect(url_for('campaign.launch', campaign_id=campaign.id))
        else:
            return redirect(url_for('campaign.audio', campaign_id=campaign.id))

    return render_template('campaign/form.html', form=form, edit=edit, campaign_id=campaign_id,
                           descriptions=current_app.config.CAMPAIGN_FIELD_DESCRIPTIONS,
                           campaign_has_audio=campaign.has_audio())



@campaign.route('/<int:campaign_id>/copy', methods=['GET', 'POST'])
def copy(campaign_id):
    orig_campaign = Campaign.query.filter_by(id=campaign_id).first_or_404()
    new_campaign = duplicate_object(orig_campaign)
    new_campaign.name = orig_campaign.name + " (copy)"
    db.session.add(new_campaign)
    db.session.commit()

    # duplicate_object skips sets
    # recreate m2m objects manually
    if orig_campaign.target_set:

        for target in orig_campaign.target_set:
            # update or create CampaignTarget membership
            try:
                campaign_target = CampaignTarget.query.filter_by(campaign=new_campaign, target=target).one()
            except sqlalchemy.orm.exc.NoResultFound:
                # create a new one
                campaign_target = CampaignTarget()
                campaign_target.campaign = new_campaign
                campaign_target.target = target
            db.session.add(campaign_target)
        new_campaign.target_set = orig_campaign.target_set
        db.session.add(new_campaign)
        db.session.commit()

    flash('Campaign copied.', 'success')
    return redirect(url_for('campaign.form', campaign_id=new_campaign.id))


@campaign.route('/<int:campaign_id>/audio', methods=['GET', 'POST'])
def audio(campaign_id):
    campaign = Campaign.query.filter_by(id=campaign_id).first_or_404()
    form = CampaignAudioForm()

    twilio_client = current_app.config.get('TWILIO_CLIENT')
    twilio_capability = TwilioCapability(*twilio_client.auth)
    twilio_capability.allow_client_outgoing(current_app.config.get('TWILIO_PLAYBACK_APP'))

    for field in form:
        campaign_audio, is_default_message = campaign.audio_or_default(field.name)
        if not is_default_message:
            field.data = campaign_audio

    if form.validate_on_submit():
        form.populate_obj(campaign)

        db.session.add(campaign)
        db.session.commit()

        flash('Campaign audio updated.', 'success')
        return redirect(url_for('campaign.launch', campaign_id=campaign.id))

    return render_template('campaign/audio.html', campaign=campaign, form=form,
                           twilio_capability = twilio_capability,
                           descriptions=current_app.config.CAMPAIGN_FIELD_DESCRIPTIONS,
                           example_text=current_app.config.CAMPAIGN_MESSAGE_DEFAULTS)


@campaign.route('/<int:campaign_id>/audio/upload', methods=['POST'])
def upload_recording(campaign_id):
    campaign = Campaign.query.filter_by(id=campaign_id).first_or_404()
    form = AudioRecordingForm()

    if form.validate_on_submit():
        message_key = form.data.get('key')

        # get highest version for this key to date
        last_version = db.session.query(db.func.max(AudioRecording.version)) \
            .filter_by(key=message_key) \
            .scalar()

        recording = AudioRecording()
        form.populate_obj(recording)
        recording.hidden = False
        recording.version = int(last_version or 0) + 1

        # save uploaded file to storage
        file_storage = request.files.get('file_storage')
        file_type = form.data.get('file_type', 'mp3')
        if file_storage:
            file_storage.filename = "campaign_{}_{}_{}.{}".format(campaign.id, message_key, recording.version, file_type)
            recording.file_storage = file_storage
        else:
            # dummy file storage
            recording.file_storage = TemporaryStore('')
            # save text-to-speech instead
            recording.text_to_speech = form.data.get('text_to_speech')

        db.session.add(recording)

        # unset selected for all other versions
        # disable autoflush to avoid errors with empty recording file_storage
        with db.session.no_autoflush:
            other_versions = CampaignAudioRecording.query.filter(
                CampaignAudioRecording.campaign_id == campaign_id,
                CampaignAudioRecording.recording.has(key=message_key)).all()
        for v in other_versions:
            # reset empty storages
            if ((not hasattr(v, 'file_storage')) or
                 (v.file_storage is None) or
                 (type(v.file_storage) is TemporaryStore)):
                # create new dummy store
                v.file_storage = TemporaryStore('')
            v.selected = False
            db.session.add(v)
        db.session.commit()

        # link this recording to campaign through m2m, and set selected flag
        campaignRecording = CampaignAudioRecording(campaign_id=campaign.id, recording=recording)
        campaignRecording.selected = True

        db.session.add(campaignRecording)
        db.session.commit()

        message = "Audio recording uploaded"
        return jsonify({'success': True, 'message': message,
                        'key': message_key, 'version': recording.version})
    else:
        return jsonify({'success': False, 'errors': form.errors})


@campaign.route('/<int:campaign_id>/audio/<int:recording_id>/select', methods=['POST'])
def select_recording(campaign_id, recording_id):
    # ensure the requested ids exist
    campaign = Campaign.query.filter_by(id=campaign_id).first_or_404()
    recording = AudioRecording.query.filter_by(id=recording_id).first_or_404()

    # unselect all other CampaignAudioRecordings with the same key and campaign
    other_versions = CampaignAudioRecording.query.filter(
        CampaignAudioRecording.campaign_id == campaign_id,
        CampaignAudioRecording.recording.has(key=recording.key)).all()
    for v in other_versions:
        v.selected = False
        db.session.add(v)
    db.session.commit()

    # select the requested recording
    campaignRecording = CampaignAudioRecording(campaign_id=campaign.id, recording=recording)
    campaignRecording.selected = True

    db.session.add(campaignRecording)
    db.session.commit()

    message = "Audio recording selected"
    return jsonify({'success': True, 'message': message,
                    'key': recording.key, 'version': recording.version})


@campaign.route('/<int:campaign_id>/audio/<int:recording_id>/hide', methods=['POST'])
def hide_recording(campaign_id, recording_id):
    recording = AudioRecording.query.filter_by(id=recording_id).first_or_404()
    recording.hidden = True

    campaignAudio = recording.campaign_audio_recordings.filter(campaign_id == campaign_id).first_or_404()
    campaignAudio.selected = False

    db.session.add(recording)
    db.session.add(campaignAudio)
    db.session.commit()

    message = "Audio recording hidden"
    return jsonify({'success': True, 'message': message,
                    'key': recording.key, 'version': recording.version})


@campaign.route('/<int:campaign_id>/audio/<int:recording_id>/show', methods=['POST'])
def show_recording(campaign_id, recording_id):
    recording = AudioRecording.query.filter_by(id=recording_id).first_or_404()
    recording.hidden = False

    db.session.add(recording)
    db.session.commit()

    message = "Audio recording visible"
    return jsonify({'success': True, 'message': message,
                    'key': recording.key, 'version': recording.version})


@campaign.route('/<int:campaign_id>/launch', methods=['GET', 'POST'])
def launch(campaign_id):
    campaign = Campaign.query.filter_by(id=campaign_id).first_or_404()
    form = CampaignLaunchForm()

    if form.validate_on_submit():
        campaign.status_code = STATUS_LIVE

        # update campaign embed settings
        if form.embed_type.data == 'custom':
            campaign.embed = {
                'type': form.embed_type.data,
                'form_sel': form.embed_form_sel.data,
                'phone_sel': form.embed_phone_sel.data,
                'location_sel': form.embed_location_sel.data,
                'custom_css': form.embed_custom_css.data,
                'custom_js': form.embed_custom_js.data,
                'custom_onload': form.embed_custom_onload.data,
                'script_display': form.embed_script_display.data,
                'redirect': form.embed_redirect.data
            }
        elif form.embed_type.data == 'iframe':
            campaign.embed = {
                'type': form.embed_type.data,
                'custom_css': form.embed_custom_css.data,
                'script_display': 'replace'
            }
        else:
            campaign.embed = {}

        campaign.embed['script'] = form.embed_script.data

        db.session.add(campaign)
        db.session.commit()

        flash('Campaign launched!', 'success')
        return redirect(url_for('campaign.index'))

    else:
        if campaign.embed:
            form.embed_type.data = campaign.embed.get('type')

            if campaign.embed.get('type') == 'custom':
                form.embed_form_sel.data = campaign.embed.get('form_sel')
                form.embed_phone_sel.data = campaign.embed.get('phone_sel')
                form.embed_location_sel.data = campaign.embed.get('location_sel')
                form.embed_custom_css.data = campaign.embed.get('custom_css')
                form.embed_custom_js.data = campaign.embed.get('custom_js')
                form.embed_custom_onload.data = campaign.embed.get('custom_onload')
                form.embed_script_display.data = campaign.embed.get('script_display')
                form.embed_redirect.data = campaign.embed.get('redirect')

            if campaign.embed.get('script'):
                form.embed_script.data = campaign.embed.get('script')

    return render_template('campaign/launch.html', campaign=campaign,
        campaign_data=campaign.get_campaign_data(), form=form,
        descriptions=current_app.config.CAMPAIGN_FIELD_DESCRIPTIONS)


@campaign.route('/<int:campaign_id>/status', methods=['GET', 'POST'])
def status(campaign_id):
    campaign = Campaign.query.filter_by(id=campaign_id).first_or_404()
    form = CampaignStatusForm(obj=campaign)

    if form.validate_on_submit():
        form.populate_obj(campaign)

        db.session.add(campaign)
        db.session.commit()

        flash('Campaign status updated.', 'success')
        return redirect(url_for('campaign.index'))

    return render_template('campaign/status.html', campaign=campaign, form=form)


@campaign.route('/<int:campaign_id>/calls', methods=['GET'])
def calls(campaign_id):
    campaign = Campaign.query.filter_by(id=campaign_id).first_or_404()
    # call lookup handled via api ajax

    start = datetime.date.today()
    end = start + datetime.timedelta(days=1)

    return render_template('campaign/calls.html', campaign=campaign, start=start, end=end)
