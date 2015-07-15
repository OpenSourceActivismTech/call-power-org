/*
	Directive by HTML5 UP
	html5up.net | @n33co
	Free for personal and commercial use under the CCA 3.0 license (html5up.net/license)
*/

function validatePhone(num) {
    num = num.replace(/\s/g, '').replace(/\(/g, '').replace(/\)/g, '');
    num = num.replace("+", "").replace(/\-/g, '');

    if (num.charAt(0) == "1")
        num = num.substr(1);

    if (num.length != 10)
        return false;

    return num;
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

		$('form#demo').submit(function(event) {
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
	            url: 'http://demo.callpower.org/call/create',
	            type: "get",
	            dataType: "json",
	            data: data,
	            success: function(res) {
	            	alert("We are calling you now!");
	                trackEvent('call');
	                console.log('Placed Call Power call: ', res);
	            }, error: function(xhr, status, code) {
	            	console.error(status);
	            }
	        });

	        $('form#demo').slideUp();
	        $('.form-replace').slideDown();
		});
	});

})(jQuery);