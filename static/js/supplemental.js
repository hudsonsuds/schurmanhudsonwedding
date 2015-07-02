// Navbar highlighting
$(function() {
	var url = window.location;
		
	// Get curent URL element
	var element = $('ul.nav a').filter(function() {
		return this.href == url || url.href.indexOf(this.href) == 0;
	});
	
	// Change active nav highlight
	element.parent().addClass('active')
	
	// Change mobile display title
	$('span.mobile-title').html(element.html());
});