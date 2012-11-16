/*
* @name Twitter Bootstrap Show Password
* @descripton
* @version 0.6
* @requires Jquery 1.8.1
*
* @author Jeroen van Meerendonk
* @author-email jeroen@cyneek.com
* @author-website http://cyneek.com
*
* @author Joseba Juániz
* @author-email joseba@cyneek.com
* @author-website http://cyneek.com
* @licens MIT License - http://www.opensource.org/licenses/mit-license.php
*/
(function($){
$.fn.extend({
showPassword: function() {

var input_password	= $(this);
console.log(input_password)
//create the icon and assign
var icon_password = $('<span tabindex="100" class="add-on"><i class="icon-eye-open"></i></span>').css('cursor', 'help').tooltip({trigger:'click'});
icon_password.attr('data-original-title', $(this).attr('value'));
input_password.on({
input	: function() {
icon_password.attr('data-original-title', $(this).attr('value'));
}
});
// Create the wrap and append the icon
input_password.wrap('<div class="input-append" />').after(icon_password);

        }
    });
})(jQuery);