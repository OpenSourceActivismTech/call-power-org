/*!
  * CallPowerForm.js
  * Connects embedded action form to CallPower campaign
  * Requires jQuery >= 1.7.0
  *    proxy (1.4), deferred (1.5), promises (1.6), on (1.7)
  *
  * Displays call script in overlay or by replacing form
  * Override functions onSuccess or onError in CallPowerOptions
  * Instantiate with form selector to connect callbacks
  * (c) Spacedog.xyz 2015, license AGPLv3
  */

var CallPowerForm = function (formSelector, $) {
  // instance variables
  this.$ = $;  // stash loaded version of jQuery, in case there are conflicts with window
  this.form = this.$(formSelector);
  {% if campaign.embed %}
  this.locationField = this.$('{{campaign.embed.get("location_sel","#location_id")}}');
  this.phoneField = this.$('{{campaign.embed.get("phone_sel","#phone_id")}}');
  {% else %}
  this.locationField = this.$("#location_id");
  this.phoneField = this.$("#phone_id");
  {% endif %}
  this.scriptDisplay = 'overlay';
  
  // allow options to override settings
  for (var option in window.CallPowerOptions || []) {
    var setting = CallPowerOptions[option];
    // accept jquery selectors for form and fields
    var selectorFields = ['form', 'locationField', 'phoneField'];
    if ($.inArray(option, selectorFields) != -1 && typeof setting === 'string') {
      this[option] = this.$(setting);
    } else { 
      this[option] = setting;
    }
  }

  // bind our submit event to makeCall
  this.form.on("submit.CallPower", this.$.proxy(this.makeCall, this));
  // include custom css
  if(this.customCSS !== undefined) {
    var link_elem = 'link rel="stylesheet" href="';
    // one weird trick to create the element without it rendering in browsers
    this.$('head').append('<'+link_elem+this.customCSS+'" />');
  }
};

CallPowerForm.prototype = function($) {
  // prototype variables
  var createCallURL = '{{url_for("call.create", _external=True)}}';
  var campaignId = "{{campaign.id}}";

  var getCountry = function() {
    return "{{campaign.country|default('US')}}";
  };

  var cleanUSZipcode = function() {
    if (this.locationField.length === 0) { return undefined; }
    var isValid = /(\d{5}([\-]\d{4})?)/.test(this.locationField.val());
    return isValid ? this.locationField.val() : false;
  };

  var cleanUSPhone = function() {
    if (this.phoneField.length === 0) { return undefined; }
    var num = this.phoneField.val();
    // remove whitespace, parens
    num = num.replace(/\s/g, '').replace(/\(/g, '').replace(/\)/g, '');
    // plus, dashes
        num = num.replace("+", "").replace(/\-/g, '');
        // leading 1
        if (num.charAt(0) == "1")
            num = num.substr(1);
        var isValid = (num.length == 10); // ensure just 10 digits remain 

    return isValid ? num : false;
  };

  // default to US validators
  var cleanPhone = cleanUSPhone;
  var cleanLocation = cleanUSZipcode;

  var onSuccess = function(response) {
    if (response.campaign === 'archived') { return onError(this.form, 'This campaign is no longer active.'); }
    if (response.campaign !== 'live') { return onError(this.form, 'This campaign is not active.'); }
    if (response.call !== 'queued') { return onError(this.form, 'Could not start call.'); }
    if (response.script === undefined) { return false; }

    if (this.scriptDisplay === 'overlay') {
      // display simple overlay with script content
      var scriptOverlay = this.$('<div class="overlay"><div class="modal">'+response.script+'</div></div>');
      this.$('body').append(scriptOverlay);
      scriptOverlay.overlay();
      scriptOverlay.trigger('show');
    }

    if (this.scriptDisplay === 'replace') {
      // hide form and show script contents

      // start new empty hidden div
      var scriptDiv = this.$('<div style="display: none;"></div>');
      // copy existing form classes and styling
      scriptDiv.addClass(this.form.attr('class'));
      // insert response contents
      scriptDiv.html(response.script);

      scriptDiv.insertAfter(this.form);
      this.form.slideUp();
      scriptDiv.slideUp();
    }

    if (this.scriptDisplay === 'alert') {
      // popup alert with response.script text
      var message = this.$(response.script);
      alert(message.text());
    }

    // run custom js function
    if(typeof this.customJS !== 'undefined') {
      var $ = this.$; // make our version of jQuery available to local context
      if(typeof this.customJS === 'string' ) { eval(this.customJS); }
      else if (typeof this.customJS === 'function') { this.customJS(); }
    }

    return true;
  };

  var onError = function(element, message) {
    if (element !== undefined) {
      element.addClass('has-error');  
    } else {
      console.error(message);  
    }
    return false;
  };

  var makeCall = function(event, options) {
    // stop default form submit event
    if (event !== undefined) { event.preventDefault(); }

    if (this.locationField.length && !this.location()) {
      return this.onError(this.locationField, 'Invalid location');
    }
    if (this.phoneField.length && !this.phone()) {
      return this.onError(this.phoneField, 'Invalid phone number');
    }

    this.$.ajax(createCallURL, {
      method: 'GET',
      data: {
        campaignId: campaignId,
        userLocation: this.location(),
        userPhone: this.phone(),
        userCountry: this.country()
      }
    })
    .done(this.$.proxy(this.onSuccess, this))
    .fail(this.$.proxy(this.onError, this, this.form, 'Please fill out the form completely'))
    .then(this.$.proxy(function() {
      // turn off our submit event
      this.form.off('submit.CallPower');

      if (this.scriptDisplay === 'overlay') {
        // bind overlay hide to original form submit
        this.$('.overlay').on('hide', this.$.proxy(this.formSubmit, this));
      } else if (this.scriptDisplay === 'replace') {
        // original form still exists, but is hidden
        // do nothing
      } else {
        // re-trigger original form submit
        this.formSubmit();
      }
    }, this))
    .fail(this.$.proxy(this.onError, this, this.form, 'Sorry, there was an error making the call'));
  };

  var formSubmit = function() {
    // trigger form submit event after optional delay
    window.setTimeout(this.$.proxy(function() { this.form.trigger('submit'); }, this), this.submitDelay || 0);
  };

  // public method interface
  return {
    country: getCountry,
    location: cleanLocation,
    phone: cleanPhone,
    onError: onError,
    onSuccess: onSuccess,
    makeCall: makeCall,
    formSubmit: formSubmit
  };
} (jQuery);
