"use strict";

$(function (){ 

	function main() {

		$('#searchbar').focus(function () {
			var searchbar = $(this);
			if (searchbar.val() === 'search for courses...') {
				searchbar.val('');
				searchbar.css('color', '#000000');
			}
		}).blur(function () {
			var searchbar = $('#searchbar');
			if (searchbar.val() === '') {
				searchbar.val('search for courses...');
				searchbar.css('color', '#BABDB6');
			}
		});

		$('#advanced-toggle').click(function () {
			var toggle = $(this);
			var state = $('#advanced-state');
			var div = $('#advanced-search');
			if (state.val().toLowerCase() === 'true') {
				div.css('display', 'none');
				toggle.html('Show Options');
				state.val('false');
			} else {
				div.css('display', 'block');
				toggle.html('Hide Options');
				state.val('true');
			}
		});

		$('.more-info').click(function() {
			var more_info = $(this);
			var td = more_info.parent();
			var width = td.width();
			var description = td.children('.description');
			description.toggle();
			td.width(width);
			if (description.is(':visible')) {
				more_info.html('[-]');
			} else {
				more_info.html('[+]');
			}
		});

		$('#advanced-toggle').click().click();

	}

	main();

});
