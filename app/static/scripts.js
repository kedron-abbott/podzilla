/*This helps the side nav look cool -
 * pushes the menu options
 * moves everything else on the page
 * changes the hamburger menu to an x and back again
 */
function changeMenu(x) {
    x.classList.toggle("change");
    document.getElementById("mySidenav").classList.toggle("navOpen");
    document.getElementById("everything").classList.toggle("navOpen");
}
/*This makes all of the podcast results the same size*/
$(document).ready(function() {
    var maxHeight = 0;
    $('.card-body').each(function() {
      var divHeight = $(this).height();
      if (maxHeight == 0 || maxHeight < divHeight) maxHeight = divHeight;
    });

    $('.card-body').height(maxHeight);
});
/* This helps with the animation of the search bar*/
$(document).on('ready', function() {

  $('.field').on('focus', function() {
    $('body').addClass('is-focus');
  });

  $('.field').on('blur', function() {
    $('body').removeClass('is-focus is-type');
  });

  $('.field').on('keydown', function(event) {
    $('body').addClass('is-type');
    if((event.which === 8) && $(this).val() === '') {
      $('body').removeClass('is-type');
    }
  });

});
