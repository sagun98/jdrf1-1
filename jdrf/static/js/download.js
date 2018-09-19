/**
 * Javascript needed for the JDRF download page
 */

// Credit - https://stackoverflow.com/a/20444744
function centerModal() {
    $(this).css('display', 'block');
    var $dialog  = $(this).find(".modal-dialog"),
    offset       = ($(window).height() - $dialog.height()) / 2,
    bottomMargin = parseInt($dialog.css('marginBottom'), 10);

    // Make sure you don't hide the top part of the modal w/ a negative margin if it's longer than the screen height, and keep the margin equal to the bottom margin of the modal
    if(offset < bottomMargin) offset = bottomMargin;
    $dialog.css("margin-top", offset);
}

 jQuery(document).ready(function() {
    $(document).on('show.bs.modal', '.modal', centerModal);
    $(window).on("resize", function () {
        $('.modal:visible').each(centerModal);
    });

    $('#edit-all').on('click', function(e) {
        if (this.checked) {
            $('.checkbox').each(function () {
                $(this).prop('checked', true); 
            });
        } else {
            $('.checkbox').each(function () {
                $(this).prop('checked', false); 
            });
        }
    });

    $('.checkbox, #edit-all').bind('change', function() {
        var checked = $(':input[type="checkbox"].checkbox:checked').length;

        if (checked == 0) {
            $('#edit-all').prop('checked', false);
            $('#delete-button-row').addClass('hidden');
        } else {
            $('#delete-button-row').removeClass('hidden');
        }
    });

    $('.to-delete').on('click', function(e) {
        var file_to_delete = $(this).parent().find('a')[0].name;
        $('#to-delete-list').empty();
        $('#to-delete-list').append('<li><strong>' + file_to_delete + '</strong></li>');
    });

    $('.to-rename').on('click', function(e) {
        $('#file-rename-input').val("");
        var file_to_rename = $(this).parent().find('a')[0].name;
        $('#old-fname').html('<b>' + file_to_rename + '</b>');
    });

    $('#delete-checked').on('click', function(e) {
        $('#to-delete-list').empty();

        $(':input[type="checkbox"].checkbox:checked').each(function() {
            var file_to_delete = $(this).parent().parent().find('a')[0].name;
            $('#to-delete-list').append('<li><strong>' + file_to_delete + '</strong></li>');
        });

        $('#delete-files-modal').modal('show') 
    });
 });