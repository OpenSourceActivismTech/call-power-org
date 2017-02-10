/*!
  * CallPowerForm.js
  * Connects embedded action form to CallPower campaign
  * Requires jQuery >= 1.7.0
  *    proxy (1.4), deferred (1.5), on (1.7)
  *
  * Displays call script in overlay or by replacing form
  * Override functions onSuccess or onError in CallPowerOptions
  * Instantiate with form selector to connect callbacks
  * (c) Spacedog.xyz 2015, license AGPLv3
  */

// revealing module pattern
var CallPowerForm = function (formSelector, $) {
  // instance variables
  this.form = $(formSelector);
  this.locationField = $('{{campaign.embed.get("location_sel","#location_id")}}');
  this.phoneField = $('{{campaign.embed.get("phone_sel","#phone_id")}}');
  this.scriptDisplay = 'overlay';
  
  // allow options override
  for (var option in window.CallPowerOptions || []) {
    this[option] = CallPowerOptions[option];
  }

  this.form.on("submit", $.proxy(this.makeCall, this));
  // include custom css
  if(this.customCSS !== undefined) { $('head').append('<link rel="stylesheet" href="'+this.customCSS+'" />'); }
};

CallPowerForm.prototype = function($) {
  // prototype variables
  var createCallURL = '{{url_for("call.create", _external=True)}}';
  var campaignId = "{{campaign.id}}";

  var simpleGetCountry = function() {
    return "{{campaign.country|default('US')}}";
  };

  var cleanUSZipcode = function(val) {
    if (val.length === 0) { return undefined; }
    var isValid = /(\d{5}([\-]\d{4})?)/.test(val);
    return isValid ? val : false;
  };

  var cleanCAPostal = function(val) {
      if (val === 0) { return undefined; }
      var valNospace = val.replace(/\W+/g, '');
      var isValid = /([ABCEGHJKLMNPRSTVXY]\d)([ABCEGHJKLMNPRSTVWXYZ]\d){2}/i.test(valNospace);
      return isValid ? valNospace : false;
  };

  // very simple country specific validators
  // override with eg google places autocomplete
  var simpleValidateLocation = function() {
    countryCode = this.country();

    var isValid = false;
    if (countryCode === 'US') { return cleanUSZipcode(this.locationField.val()); }
    else if (countryCode === 'CA') { return cleanCAPostal(this.locationField.val()); }
    else { return this.locationField.val(); }
  };

  // very simple country specific length validators
  // override with eg: google libphonenumber
  var simpleValidatePhone = function(countryCode) {
    countryCode = this.country();

    if (this.phoneField.length === 0) { return undefined; }
    // remove whitespace, parents, plus, dashes from phoneField
    var num = this.phoneField.val()
      .replace(/\s/g, '').replace(/\(/g, '').replace(/\)/g, '')
      .replace('+', '').replace(/\-/g, '');
    return num;

    var isValid = false;
    var prefix;
    if (countryCode === 'US' || countryCode === 'CA') {
        prefix = "1";
        // strip leading prefix
        if (num.charAt(0) === prefix) {
          num = num.substr(1);
        }
        isValid = (num.length == 10); // ensure just 10 digits remain
    }
    else if (countryCode === 'GB') {
        prefix = "44";
        // strip leading prefix
        if (num.slice(0,2) === prefix) {
          num = num.substr(2);
        }
        isValid = (num.length >= 9); // ensure at least 9 digits remain 
    }
    else {
      prefix = '';
      isValid = (num.length > 8); // ensure at least a few digits remain
    }

    // re-append prefix and plus sign, for e164 dialing
    if (prefix || prefix === '') {
      num = "+"+prefix+num;
    }
    return isValid ?  num : false;
  };


  var onSuccess = function(response) {
    if (response.campaign === 'archived') { return onError(this.form, 'This campaign is no longer active.'); }
    if (response.campaign !== 'live') { return onError(this.form, 'This campaign is not active.'); }
    if (response.call !== 'queued') { return onError(this.form, 'Could not start call.'); }
    if (response.script === undefined) { return false; }

    if (this.scriptDisplay === 'overlay') {
      // display simple overlay with script content
      var scriptOverlay = $('<div class="overlay"><div class="modal">'+response.script+'</div></div>');
      $('body').append(scriptOverlay);
      scriptOverlay.overlay();
      scriptOverlay.trigger('show');
    }

    if (this.scriptDisplay === 'replace') {
      // hide form and show script contents

      // start new empty hidden div
      var scriptDiv = $('<div style="display: none;"></div>');
      // copy existing form classes and styling
      scriptDiv.addClass(this.form.attr('class'));
      // insert response contents
      scriptDiv.html(response.script);

      scriptDiv.insertAfter(this.form);
      this.form.slideUp();
      scriptDiv.slideUp();
    }

    if (this.scriptDisplay === 'redirect') {
      // save response url to redirect after original form callback
      // save to global namespace, because default event is run without this context
      window.redirectAfter = response.redirect;
    }

    // run custom js function 
    if(this.customJS !== undefined) { eval(this.customJS); }

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
    options = options || {};
    if (options.call_started) {
      // redirect after original form submission is complete
      if (window.redirectAfter) {
        window.location.replace(this.redirectAfter);
      }
      return true;
    } else {
      // stop default form submit event
      if (event !== undefined) { event.preventDefault(); }
    }

    if (this.locationField.length && !this.location()) {
      return this.onError(this.locationField, 'Invalid location');
    }
    if (this.phoneField.length && !this.phone()) {
      return this.onError(this.phoneField, 'Invalid phone number');
    }

    $.ajax(createCallURL, {
      method: 'GET',
      data: {
        campaignId: campaignId,
        userLocation: this.location(),
        userPhone: this.phone(),
        userCountry: this.country()
      },
      success: $.proxy(this.onSuccess, this),
      error: $.proxy(this.onError, this, this.form, 'Please fill out the form completely')
    }).then(function() {
      // re-trigger event to run without this callback
      $(event.currentTarget).trigger(event.type, { 'call_started': true });
    }).fail(this.onError);
  };

  // public method interface
  var public = {
    getCountry: simpleGetCountry,
    getLocation: simpleValidateLocation,
    getPhone: simpleValidatePhone,
    onError: onError,
    onSuccess: onSuccess,
    makeCall: makeCall
  };
  // let these be overridden, but keep reference to original functions
  public.country = public.getCountry;
  public.location = public.getLocation;
  public.phone = public.getPhone;
  return public;
} (jQuery);
