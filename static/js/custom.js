/*------------------------------------------------------------------
Project:        Modus - HTML onepage theme by GraphBerry.com
Version:        1.0
Last change:    12/06/2017
Author:         GraphBerry
URL:            http://graphberry.com
License:        http://graphberry.com/pages/license
-------------------------------------------------------------------*/
$(function(){
	'use strict';


	/*--------------------------------------------------
    Scrollspy Bootstrap 
    ---------------------------------------------------*/

    $('body').scrollspy({
    	target: '#header',
    	offset: 90
    });


	/*--------------------------------------------------
    Smooth Scroll 
    ---------------------------------------------------*/

	smoothScroll.init({
		selector: '.smoothScroll',
		speed: 1000,
		offset: 90,
		before: function(anchor, toggle){
			// Check if mobile navigation is active
			var query = Modernizr.mq('(max-width: 767px)');
			// Check if element is navigation eelement
			var navItem = $(toggle).parents("#main-navbar").length;
			// If mobile nav & nav item then close nav
			if (query && navItem !== 0) {
				$("button.navbar-toggle").click();
			}
		}
	});


	/*--------------------------------------------------
    Slick Slider
    ---------------------------------------------------*/

    // Count the number of slides to load in advance
	var count = $('.slider-container > .project').length;

	$('.slider-container').slick({
		arrows: false,
		autoplay: true,
		slidesToShow: count-1,
		slidesToScroll: 3,
		variableWidth: true,
		responsive: [
			{
				breakpoint: 960,
				settings: {
					slidesToScroll: 2,
				}
			},
			{
				breakpoint: 640,
				settings: {
					slidesToScroll: 1,
				}
			},
		]
	});


	/*--------------------------------------------------
    Porfolio cursor
    ---------------------------------------------------*/

	$('.project').on('mousedown', function() {
	    $(this).removeClass('grabbable');
	    $(this).addClass('grabbing');
	});

	$('.project').on('mouseleave mouseup', function() {
	    $(this).removeClass('grabbing');
	    $(this).addClass('grabbable');
	});


	/*--------------------------------------------------
    Current Year
    ---------------------------------------------------*/

    // Automatically update copyright year in the footer
	var currentTime = new Date();
	var year = currentTime.getFullYear();
	$("#year").text(year);

	/*--------------------------------------------------
    CSRF 토큰 자동 설정
    ---------------------------------------------------*/
    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

    if (csrfToken) {
        const originalFetch = window.fetch;
        window.fetch = function (url, options = {}) {
            options.headers = {
                ...options.headers,
                'X-CSRFToken': csrfToken
            };
            return originalFetch(url, options);
        };
    }

	// 드롭다운 toggle (모바일에서도 동작하도록)
	$(document).on('click', '.dropdown-toggle', function (e) {
		e.preventDefault();
		e.stopPropagation(); // 이벤트 버블링 방지

		var $parent = $(this).parent('.dropdown');

		// 다른 열려있는 드롭다운 닫기
		$('.dropdown').not($parent).removeClass('open');

		// 현재 드롭다운 toggle
		$parent.toggleClass('open');
	});

	// 드롭다운 외 클릭 시 닫기
	$(document).on('click', function () {
		$('.dropdown').removeClass('open');
	});

	// navbar가 collapse될 때 드롭다운도 닫기
	$('#main-navbar').on('hide.bs.collapse', function () {
		$('.dropdown').removeClass('open');
	});

});