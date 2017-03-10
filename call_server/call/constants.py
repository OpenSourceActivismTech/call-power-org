STRING_LEN = 100

TWILIO_CALL_STATUS = (
    'queued',       # The call is ready and waiting in line before going out.
    'ringing',      # The call is currently ringing.
    'in-progress',  # The call was answered and is currently in progress.
    'completed',    # The call was answered and has ended normally.
    'busy',         # The caller received a busy signal.
    'failed',       # The call could not be completed as dialed, most likely because the phone number was non-existent.
    'no-answer',    # The call ended without being answered.
    'canceled',     # The call was canceled via the REST API while queued or ringing.
    'unknown'       # Not an official twilio status, but our default before we get one
)
# from https://www.twilio.com/docs/api/twiml/twilio_request#request-parameters-call-status

TWILIO_TTS_LANGUAGES = (
	'da-DK',
	'de-DE',
	'en-AU',
	'en-CA',
	'en-GB',
	'en-IN',
	'en-US',
	'ca-ES',
	'es-ES',
	'es-MX',
	'fi-FI',
	'fr-CA',
	'fr-FR',
	'it-IT',
	'ja-JP',
	'ko-KR',
	'nb-NO',
	'nl-NL',
	'pl-PL',
	'pt-BR',
	'pt-PT',
	'ru-RU',
	'sv-SE',
	'zh-CN',
	'zh-HK',
	'zh-TW'
)
# from https://www.twilio.com/docs/api/twiml/say#attributes-alice