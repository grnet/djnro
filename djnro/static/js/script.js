$(function () {
	$('li.language').on('click', function () {
		var lang = $(this).data('lang');
        $("#langsel").val(lang);
        $("#langform").submit();
    })
})
