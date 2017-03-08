/*global CallPower, Backbone */

(function () {
  CallPower.Views.CampaignAudioForm = Backbone.View.extend({
    el: $('form#audio'),

    events: {
      'click .record': 'onRecord',
      'click .play': 'onPlay',
      'click .upload': 'onUpload',
      'click .version': 'onVersion',

      'submit': 'submitForm'
    },

    requiredFields: ['msg_intro', 'msg_call_block_intro'],

    initialize: function() {
      window.AudioContext = window.AudioContext || window.webkitAudioContext;
      navigator.getUserMedia = ( navigator.getUserMedia ||
                       navigator.webkitGetUserMedia ||
                       navigator.mozGetUserMedia ||
                       navigator.msGetUserMedia);
      window.URL = window.URL || window.webkitURL;

      if (CallPower.Config.TWILIO_CAPABILITY) {
        this.setupTwilioClient(CallPower.Config.TWILIO_CAPABILITY);
      }

      // add required fields client-side
      _.each(this.requiredFields, function(f) {
        $('label[for='+f+']').addClass('required');
      });

      this.campaign_id = $('input[name="campaign_id"]').val();

      $('audio', this.el).on('ended', this.onPlayEnded);
      _.bindAll(this, 'onPlayEnded');
    },

    onRecord: function(event) {
      event.preventDefault();

      // pull modal info from related fields
      var inputGroup = $(event.target).parents('.input-group');
      var modal = { name: inputGroup.prev('label').text(),
                    key: inputGroup.prev('label').attr('for'),
                    description: inputGroup.find('.description .help-inline').text(),
                    example_text: inputGroup.find('.description .example-text').text(),
                    campaign_id: this.campaign_id
                  };
      this.microphoneView = new CallPower.Views.MicrophoneModal();
      this.microphoneView.render(modal);
    },

    onPlay: function(event) {
      event.preventDefault();
      
      var button = $(event.currentTarget); //.closest('button.play');
      var inputGroup = button.parents('.input-group');
      var key = inputGroup.prev('label').attr('for');
      var audio = button.children('audio')[0];
      
      if (audio.src) {
        // has src url set, play/pause

        if (audio.duration > 0 && !audio.paused) {
          // playing, pause
          audio.pause();

          button.children('.glyphicon').removeClass('glyphicon-pause').addClass('glyphicon-play');
          button.children('.text').html('Play');
          return false;
        } else {
          // paused, play
          audio.play();

          button.children('.glyphicon').removeClass('glyphicon-play').addClass('glyphicon-pause');
          button.children('.text').html('Pause');
          return false;
        }
      } else {
        // load src url from campaign
        var self = this;
        $.getJSON('/api/campaign/'+self.campaign_id,
          function(data) {
            var recording = data.audio_msgs[key];

            if (recording === undefined) {
              button.addClass('disabled');
              return false;
            }
            if (recording.substring(0,4) == 'http') {
              // play file url through <audio> object
              audio.setAttribute('src', data.audio_msgs[key]);
              audio.play();

              button.children('.glyphicon').removeClass('glyphicon-play').addClass('glyphicon-pause');
              button.children('.text').html('Pause');
            } else if (CallPower.Config.TWILIO_CAPABILITY) {
              console.log('twilio text-to-speech',recording);
              self.twilio.connect({'text': recording });

              button.children('.glyphicon').removeClass('glyphicon-play').addClass('glyphicon-bullhorn');
              button.children('.text').html('Speak');
          }
        });
      }
    },

    onPlayEnded: function(event) {
      var button = $(event.target).parents('.btn');
      button.children('.glyphicon').removeClass('glyphicon-pause').addClass('glyphicon-play');
      button.children('.text').html('Play');
    },

    setupTwilioClient: function(capability) {
      //connect twilio API to read text-to-speech
      this.twilio = Twilio.Device.setup(capability, {"debug":false});

      this.twilio.incoming(function(connection) {
        connection.accept();
        // do awesome ui stuff here
        // $('#call-status').text("you're on a call!");
      });
      this.twilio.error(function(error) {
        console.error(error);
        var msg = 'Twilio error';
        var level = 'warning'
        if (error.info) {
          msg = msg+': '+error.info.code+' '+error.info.message;
        } else if (error.message) {
          msg = msg + ': ' + error.message;
          level = 'info'; // yes, this is very counterintuitive
        }
        window.flashMessage(msg, level);
      });
      this.twilio.connect(function(conn) {
        console.log('Twilio connection', conn.status());
      });
      this.twilio.disconnect(this.onPlayEnded);
    },

    onVersion: function(event) {
      event.preventDefault();

      var inputGroup = $(event.target).parents('.input-group');
      var modal = {
        name: inputGroup.prev('label').text(),
        key: inputGroup.prev('label').attr('for'),
        campaign_id: this.campaign_id
      };
      this.versionsView = new CallPower.Views.VersionsModal(modal);
      this.versionsView.render();
    },

    validateForm: function() {
      var isValid = true;

      // check required fields for valid class
      _.each(this.requiredFields, function(f) {
        var formGroup = $('.form-group.'+f);
        var fieldValid = formGroup.hasClass('valid');
        if (!fieldValid) {
          formGroup.find('.input-group .help-block')
            .text('This field is required.')
            .addClass('error');
        }
        isValid = isValid && fieldValid;
      });

      // call validators
      
      return isValid;
    },

    submitForm: function(event) {
      if (this.validateForm()) {
        $(this.$el).unbind('submit').submit();
        return true;
      }
      return false;
    }

  });

})();