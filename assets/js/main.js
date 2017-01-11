/* global console, skel, ga */

function validatePhone(num) {
    num = num.replace(/\s/g, '').replace(/\(/g, '').replace(/\)/g, '');
    num = num.replace("+", "").replace(/\-/g, '');

    if (num.charAt(0) === "1") {
        num = num.substr(1);
    }

    if (num.length !== 10) {
        return false;
    }

    return num;
}

function mailSignup() {
	var endpoint = "//xyz.us11.list-manage.com/subscribe/post-json?u=ec3363d24d5bbc1f9b600a120&amp;id=d707cc2443&c=?";
	$.ajax({
		type: 'get',
		url: endpoint,
		data: $('form').serialize(),
		dataType    : 'json',
        contentType: "application/json; charset=utf-8",
        success: function(data) {
			if (data.result !== "success") {
                console.error(data);
            } else {
	    	    ga('send', 'event', 'mailSignup');
            }
        }
	});
}

(function($) {

	skel.breakpoints({
		wide: '(max-width: 1680px)',
		normal: '(max-width: 1280px)',
		narrow: '(max-width: 980px)',
		narrower: '(max-width: 840px)',
		mobile: '(max-width: 736px)',
		mobilep: '(max-width: 480px)'
	});

	$(function() {

		var	$window = $(window),
			$body = $('body');

		// Disable animations/transitions until the page has loaded.
			$body.addClass('is-loading');

			$window.on('load', function() {
				$body.removeClass('is-loading');
			});

		// Fix: Placeholder polyfill.
			$('form').placeholder();

		// Prioritize "important" elements on narrower.
			skel.on('+narrower -narrower', function() {
				$.prioritize(
					'.important\\28 narrower\\29',
					skel.breakpoint('narrower').active
				);
			});

		$('form#demoForm').submit(function(event) {
			event.preventDefault();

	        var phone = $('input[name=phone]').val();
	        var zipcode = $('input[name=zip]').val();

	        if (!validatePhone(phone)) {
	        	$('input[name=phone]').addClass('error');
	            return;
	        }

			var data = {
	            campaignId: '1', 
	            userPhone: validatePhone(phone),
	            zipcode: zipcode // not required, don't validate
	        };

			$.ajax({
	            url: 'https://demo.callpower.org/call/create',
	            type: "get",
	            dataType: "json",
	            data: data,
	            success: function() {
	                ga('send', 'event', 'demoCall');

	                $('form#demoForm').slideUp();
			        $('.form-replace').slideDown();

			        if ($('input[type=email]').val()) {
				        mailSignup();
				    }
	            }, error: function(xhr, status) {
	            	console.error(status);
	            }
	        });
		});
	});

})(jQuery);