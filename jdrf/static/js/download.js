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

function deleteTableRows(deleted_file) {
    var target_td = $("td:contains('" + deleted_file + "')");
    var target_tr = target_td.parent();
    var delete_icon = target_tr.children().find('i.fa-spin');

    delete_icon.removeClass('fa-refresh fa-spin').addClass('fa-trash');


    target_tr.addClass('flash-delete');
    setTimeout(function() {
        target_tr.removeClass('flash-delete');
        target_tr.slideUp(500, function() {
            //Delete the old row
            $(this).remove();

            // Check if the table length is now zero and if it is add our default "no records" message
            if ($('#uploaded-files-table tr').length == 1) {
                $('#uploaded-files-table > tbody:last-child').append('<tr><td class="no-files-row" colspan="6">No uploaded files are currently available.</td></tr>');
            }
        });
    }, 1200);
}

jQuery(document).ready(function() {
    $.ajaxSetup({beforeSend: function(xhr, settings) {
        xhr.setRequestHeader('X-CSRFToken', 
                             $("input[name='csrfmiddlewaretoken']").val());
    }});

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

    $('#rename-file-form').validator({
        custom: {
            'overwrite': function($el) {
                var file_name = $($el).val();
                if ($("a[name='" + file_name + "']").length > 0) {
                    return "New filename must not match any existing filenames."
                } 
            }
        }
    });

    $('#rename-file-form').validator().on('invalid.bs.validator', function (e) {
        // If we have validation issues disable the submit button.
        $('#rename-file-btn').prop("disabled",true);
    })

    $('#rename-file-form').validator().on('valid.bs.validator', function (e) {
        // If we have validation issues disable the submit button.
        $('#rename-file-btn').prop("disabled",false);
    })

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
        $('#rename-file-btn').val(file_to_rename);
    });

    $('#rename-file-btn').on('click', function(e){
        $("#file-mod-alert").alert(close);        

        var file = $(this).val();
        var rename_file = $('#file-rename-input').val();

        // Let's set our rename icon to a spinner while the rename process is going 
        // (which should be super short...)
        var edit_icon = $("td:contains('" + file + "')").parent().children().find('i.fa-edit');
        edit_icon.removeClass('fa-edit').addClass('fa-refresh fa-spin');

        $('#rename-modal').modal('hide');

        $.ajax({
            url: '/files/' + file + '/rename',
            method: 'PUT',
            data: {
                rename_file: rename_file,
                type: 'upload' // hard coded for now
            },
            success: function(data) {
                // If our rename succeeded we are going to want to let the user know and update 
                // the table dynamically.
                var target_td = $("td:contains('" + file + "')");
                var target_tr = target_td.parent();
                var edit_icon = target_tr.children().find('i.fa-spin');

                edit_icon.removeClass('fa-refresh fa-spin').addClass('fa-edit');

                var message = "File <b>" + data['original_file'] + "</b> successully renamed to <b>" + data['renamed_file'] + "</b>";
                $('#upload_file_mod_alert').html('<div id="file-mod-alert" class="alert alert-success alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><span>'+message+'</span></div>');
                $('#upload_file_mod_alert').removeClass('hidden');

                td_old_html = target_td.html();
                target_td.html(td_old_html.split(data['original_file']).join(data['renamed_file']))
 
                target_tr.addClass('flash-success');
                setTimeout(function() {
                    target_tr.removeClass('flash-success');
                }, 1200);
            },
            error: function(data) {
                // Something clearly went wrong here so let's remove our cookie
                // for the time being...
                console.log("OOPS");
            }
        });
    });

    $('#delete-files-btn').on('click', function(e) {
        $("#file-mod-alert").alert(close);        

        // We need two routes here depending on whether or not we are deleintg 
        // a single file or if we are deleting a group of files.
        var files = [];
        $('#to-delete-list > li').each(function() { files.push($(this).text()) });

        files.forEach(function(file) {
            var delete_icon = $("td:contains('" + file + "')").parent().children().find('i.fa-trash');
            delete_icon.removeClass('fa-trash').addClass('fa-refresh fa-spin');
        });

        $('#delete-files-modal').modal('hide');

        if (files.length > 1) {
            $.ajax({
                url: '/files/delete',
                method: 'DELETE',
                data: {
                    delete_file: files
                },
                success: function(data) {
                    if (data.success == true) {
                        files_deleted = []

                        data['results'].forEach(function(record) {
                            deleteTableRows(record['target_file']);
                            files_deleted.push(record['target_file']);
                        });
                        
                        var message = "The following files were successully deleted: <ul id='deleted-list'>";
                        message += '<li><b>' + files_deleted.join('</b></li><li><b>') + '</b></li></ul>'
                        $('#upload_file_mod_alert').html('<div id="file-mod-alert" class="alert alert-success alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><span>'+message+'</span></div>');
                        $('#upload_file_mod_alert').removeClass('hidden');

                        $('#delete-button-row').addClass('hidden');
                        $('#edit-all').prop('checked', false); 
                    } else {
                        // Something wrong happened here so let's report that to the user
                        var message = "Failed to delete files: " + data.error_msg; 

                        $('#upload_file_mod_alert').html('<div id="file-mod-alert" class="alert alert-danger alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><span>'+message+'</span></div>');
                        $('#upload_file_mod_alert').removeClass('hidden');
                    }
                },
                error: function(data) {
                    console.log("Deleting file failed!");
                }
            });
        } else {
            $.ajax({
                url: '/files/' + files[0] + '/delete',
                method: 'DELETE',
                data: {
                    delete_file: files[0]
                },
                success: function(data) {
                    if (data.success == true) {
                        deleted_file = data.target_file;

                        // When our delete suceeds we want to let the user know.
                        deleteTableRows(deleted_file);

                        var message = "File <b>" + deleted_file + "</b> successully deleted.";
                        $('#upload_file_mod_alert').html('<div id="file-mod-alert" class="alert alert-success alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><span>'+message+'</span></div>');
                        $('#upload_file_mod_alert').removeClass('hidden');

                    } else {
                        // Something wrong happened here so let's report that to the user
                        var message = "Failed to delete file <b>" + deleted_file + "<b>: " + data.error_msg; 

                        $('#upload_file_mod_alert').html('<div id="file-mod-alert" class="alert alert-danger alert-dismissable"><button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button><span>'+message+'</span></div>');
                        $('#upload_file_mod_alert').removeClass('hidden');
                    }

                    $('#delete-button-row').addClass('hidden');
                    $('#edit-all').prop('checked', false); 
                },
                error: function(data) {
                    console.log("Deleting file failed!");
                }
            });
        }
    });
    

    $('#delete-checked').on('click', function(e) {
        $('#to-delete-list').empty();

        $(':input[type="checkbox"].checkbox:checked').each(function() {
            var file_to_delete = $(this).parent().parent().find('a')[0].name;
            $('#to-delete-list').append('<li><strong>' + file_to_delete + '</strong></li>');
        });

        $('#delete-files-modal').modal('show') 
    });

    $('#file-rename-input').trigger('input')
 });