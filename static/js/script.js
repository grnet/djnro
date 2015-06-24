$(function () {
	$('li.language').on('click', function () {
		var lang = $(this).data('lang');
		console.log(lang);
        $("#langsel").val(lang);
        $("#langform").submit();
    })
})
