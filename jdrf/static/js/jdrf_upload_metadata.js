/**
 * Javascript needed for the metadata upload functionality of the JDRF MIBC website.
 */

 jQuery(document).ready(function() {
    $.ajaxSetup({beforeSend: function(xhr, settings){
        xhr.setRequestHeader('X-CSRFToken', 
                             $("input[name='csrfmiddlewaretoken']").val());
      }});

    var editor_opts = {
        table: "#metadata_file_preview",
        fields: [
            { label: 'Sample ID', name: 'sample_id' },
            { label: 'Host Subject ID', name: 'host_subject_id' },
            { label: 'Subject Age', name: 'subject_age' },
            { label: 'Subject Sex', name: 'subject_sex' },
            { label: 'Ethnicity', name: 'ethnicity' },
            { label: 'Collection Date', name: 'collection_date' },
            { label: 'Host Body Mass Index', name: 'host_body_mass_index' },
            { label: 'Host Diet', name: 'host_diet' },
            { label: 'Host Disease', name: 'host_disease' },
            { label: 'Host Body Product', name: 'host_body_product' },
            { label: 'Host Family Relationship', name: 'host_family_relationship' },
            { label: 'Host Genotype', name: 'host_genotype' },
            { label: 'Host Phenotype', name: 'host_phenotype' },
            { label: 'Gastrointestinal Disorder', name: 'gastrointest_disord' },
            { label: 'IHMC Medication Code', name: 'ihmc_medication_code' },
            { label: 'Subject Taxonomy ID', name: 'subject_tax_id' },
            { label: 'Sourced Material ID', name: 'source_material_id' },
            { label: 'Isolation Source', name: 'isolation_source' },
            { label: 'Sample Material Process', name: 'sample_mat_process' },
            { label: 'Sample Store Duration', name: 'sample_store_dur' },
            { label: 'Sample Store Temperature', name: 'sample_store_temp' },
            { label: 'Sample Volume Mass', name: 'sample_vol_mass' },
            { label: 'Variable Region', name: 'variable_region' },
            { label: 'Organism Count', name: 'organism_count' },
            { label: 'Sequencer', name: 'sequencer' },
            { label: 'Number of Reads', name: 'read_number' },
            { label: 'Filename', name: 'filename' },
            { label: 'MD5 Checksum', name: 'md5_checksum' }
        ]
    };

    var local_editor = new $.fn.dataTable.Editor(editor_opts);
    
    var ajax_editor = new $.fn.dataTable.Editor(
        $.extend(true, {
            ajax: "/metadata/sample",
        }, editor_opts)
    );

    var is_other_data_type = false;
    $('#sample_type').on('change', function() {
        var value = $(this).val();

        if (value == "other") {
            $('#analysis_desc_div').removeClass('hidden');
            is_other_data_type = true;
        } else {
            $('#analysis_desc').val("");
            $('#analysis_desc_div').addClass('hidden');
            is_other_data_type = false;
        }
    })

    // On page load we want to see if a cookie exists to indicate study metadata has been created for this file.
    if (Cookies.get('study_metadata') == '1') {
        // Need to do an AJAX request here to parse the contents of our CSV file and fill in 
        // form data
        $.ajax({
            url: '/metadata/study',
            method: 'GET',
            //data: {
            //    csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val()
            //},
            success: function(data) {
                var form_elts = data.study_form;
                $.each(form_elts, function(key, val) {
                    $('#panel_study_metadata #' + key).val(val);
                });

                $('#analysis_desc_div').removeClass('hidden');
                is_other_data_type = true;
            },
            error: function(data) {
                // Something clearly went wrong here so let's remove our cookie
                 // for the time being...
                 Cookies.remove('study_metadata');
            }
        });

        // Load the metadata file and hide our panel.
        $('#panel_study_metadata .panel-body').hide();
        $('#panel_study_metadata .panel-heading').css('cursor', 'pointer');
        $('#panel_study_metadata .panel-heading').html('<h3 class="panel-title">Study Metadata <span class="pull-right glyphicon glyphicon-ok green"></span></h3>');
        $('#panel_study_metadata .panel-heading').on('click', function() {
            $('#panel_study_metadata .panel-body').slideToggle();
        })

        $('#panel_sample_metadata .panel-heading').css('opacity', 1)
        $('#panel_sample_metadata .panel-body').show();
        $('#panel_sample_metadata .panel-heading').css('cursor', 'pointer');
        $('#panel_sample_metadata .panel-heading').on('click', function() {
            $('#panel_sample_metadata .panel-body').slideToggle();
        })
        
        $('#metadata_complete').removeClass('hidden');
        $('#date_format_audit').removeClass('hidden');
    }

    if (Cookies.get('sample_metadata') == '1') {
        $('#panel_sample_metadata .panel-body').hide();
        $('#panel_sample_metadata .panel-heading').html('<h3 class="panel-title">Sample Metadata <span class="pull-right glyphicon glyphicon-ok green"></span></h3>');
        $('#upload_success').removeClass('hidden');
        $('#date_format_audit').removeClass('hidden');
    }

    $('#study_metadata_form').validator().on('submit', function(e) {
        if (e.isDefaultPrevented()) {
            // Do nothing for the time being.
        } else {
           e.preventDefault();

            // Write our form data to a CSV file
            $.ajax({
                url: '/metadata/study',
                data: $('#study_metadata_form').serialize(),
                method: 'POST',
                processData: false,
                success: function(data) {
                    $('#panel_study_metadata .panel-body').slideUp();
                    $('#panel_study_metadata .panel-heading').html('<h3 class="panel-title">Study Metadata <span class="pull-right glyphicon glyphicon-ok green"></span></h3>');
                    $('#panel_study_metadata .panel-heading').on('click', function() {
                        $(this).css('cursor', 'pointer');

                        $('#panel_study_metadata .panel-body').slideToggle();
                    });

                    $('#panel_sample_metadata .panel-heading').css('opacity', '1');
                    $('#panel_sample_metadata .panel-body').slideDown();
                    Cookies.set('study_metadata', "1");
                },
                error: function(data) {
                    // Do stuff to handle errors here
                }
            })

        }
    })

    $('#metadata_file_upload').fileinput({
        showPreview: false,
        uploadAsync: false,
        layoutTemplates: {progress: ''},
        uploadUrl: '/metadata/sample',
        msgPlaceholder: 'Select metadata file to upload...',
        uploadExtraData: function() { 
           return {
               'csrfmiddlewaretoken': $("input[name='csrfmiddlewaretoken']").val(),
               'other_data_type': is_other_data_type,
           }
        }
    });

    var row_update = false;
    $('#metadata_file_preview').on('click', 'tbody td:not(:first-child):not(.DTE)', function(e) {
        local_editor.inline( this, {
            onBlur: 'submit'
        } );
    });


    var table = $('#metadata_file_preview').DataTable({
       dom: "<'row'<'#edit_buttons.col-md-3 col-md-offset-9'B>>" +
            "<'row'<'col-sm-6'l><'col-sm-6'f>>" +
            "<'row'<'col-sm-12'tr>>" +
            "<'row'<'col-sm-5'i><'col-sm-7'p>>",
       pageLength: 12,
       searching: false,
       deferLoading: 0,
       lengthChange: false,
       scrollY: '425px',
       scrollX: '400px',
       scrollCollapse: false,
       columns: [
           {data: 'sample_id'},
           {data: 'host_subject_id'},
           {data: 'subject_age'},
           {data: 'subject_sex'},
           {data: 'ethnicity'},
           {data: 'collection_date'},
           {data: 'host_body_mass_index'},
           {data: 'host_diet'},
           {data: 'host_disease'},
           {data: 'host_body_product'},
           {data: 'host_family_relationship'},
           {data: 'host_genotype'},
           {data: 'host_phenotype'},
           {data: 'gastrointest_disord'},
           {data: 'ihmc_medication_code'},
           {data: 'subject_tax_id'},
           {data: 'source_material_id'},
           {data: 'isolation_source'},
           {data: 'samp_mat_process'},
           {data: 'samp_store_dur'},
           {data: 'samp_store_temp'},
           {data: 'samp_vol_mass'},
           {data: 'variable_region'},
           {data: 'organism_count'},
           {data: 'sequencer'},
           {data: 'read_number'},
           {data: 'filename'},
           {data: 'md5_checksum'}
       ],
       columnDefs: [
           {
               targets: '_all',
               createdCell: function(td, cellData, rowData, row, col) {
                   var col_name = table.column(col).dataSrc();
                   if (rowData[col_name + "_error"] == true) {
                           $(td).css('color', 'white');
                           $(td).css('font-weight', 'bold');
                           $(td).css('background-color', 'red');
                           $(td).attr('data-toggle', 'tooltip').attr('title', rowData[col_name + "_validation_msg"]);
                           $(td).html(cellData);
                   }
               }
           }
       ],
       buttons: [
           {
               text: 'Save changes',
               init: function() {
                   this.disable();
               },
               action: function() {
                   console.log("IN HERE");
               }
           },
           {
               text: 'Discard changes',
               init: function() {
                   this.disable();
               },
               action: function() {
                table.clear();
                table.rows.add(tables_json, false).draw();

                changed_rows.length = 0;
                table.buttons([0,1]).disable();
                $("#edit_buttons").hide();
               }
           }
       ],
       success: function(data) {
           console.log("BAR");
       },
       error: function(data) {
           console.log("FOO");
       }
    });

    var changed_rows = [];
    var open_vals = "";
    var table_json = "";

    $('#metadata_file_preview').on('blur', 'tbody td:not(:first-child):not(div)', function(e) {
        if (open_vals !== JSON.stringify( local_editor.get() )) {
            $(this).css('color', 'black');
            $(this).css('background-color', 'yellow');
            row_update = true;
        } else {
            row_update = false;
        }
    });

    local_editor.on('open', function() {
        open_vals = JSON.stringify( local_editor.get() );
    });

    local_editor.on('postEdit', function (e, json, data) {
        if (row_update == true) {
            // Store the row id so it can be submitted with the Ajax editor in future
            changed_rows.push( '#'+data.DT_RowId );

            // Enable the save / discard buttons
            $("#edit_buttons").show();
            table.buttons([0,1]).enable();
        }
    });

    $('#metadata_file_preview').on('draw.dt', function () {
        $('[data-toggle="tooltip"]').tooltip({
            container : 'body'
        });
    });

     $('#metadata_file_upload').on('filebatchuploaderror', function(event, data, msg) {
        var response = data.response;

        $('#panel_sample_metadata .panel-heading').html('<h3 class="panel-title">Sample Metadata <span class="pull-right glyphicon glyphicon-remove red"></span></h3>');
        Cookies.remove('sample_metadata');

        if (response.hasOwnProperty('error_msg')) {
            // We have a larger structural problem here so don't render 
            // the table and just display the error message.
            $('#datatables_div').hide();
            $('#error_spreadsheet').addClass('hidden')
            
            // If we have a mismatch in the columns supplied in our metadata vs what is expected
            // in the schema we can list out all the 
            var error_single_html = "";
            if ("mismatch_cols" in response) {
                // We should get back two lists of columns here. One contains extra columns 
                // while the other will contain any missing columns.
                extra_cols = response['mismatch_cols'][0]
                missing_cols = response['mismatch_cols'][1]

                error_single_html += "<div class='glyphicon glyphicon-ban-circle'></div>" +
                                     "<div>" + response['error_msg'] + ":" + "</div><br />" +
                                     "<div id='mismatch_cols'>";

                if (missing_cols.length > 0) {
                    error_single_html += "<b>Missing Columns:</b><br /><ul>";

                    for (var col in missing_cols) {
                        error_single_html += "<li><b>" + missing_cols[col] + "</b></li>";
                    }

                    error_single_html += "</ul><br />";
                }

                if (extra_cols.length > 0) {
                    error_single_html += "<b>Extra Columns:</b><br /><ul>";

                    for (var col in extra_cols) {
                        error_single_html += "<li><b>" + extra_cols[col] + "</b></li>";
                    }
                }

                error_single_html += "</ul></div>";

                $('#validation_error_single').html(error_single_html);
            } else {
                $('#validation_error_single').html("<div class='glyphicon glyphicon-ban-circle'></div>" +
                                                   "<div>" + response['error_msg'] + "</div>");
            }

            $('#validation_error_single').removeClass('hidden');
            $('#validation').removeClass('hidden');
        } else {
            $('#upload_success').addClass('hidden');
            $('#date_format_audit').addClass('hidden')
            Cookies.remove('sample_metadata');

            tables_json = JSON.parse(response.errors_datatable);
            table.clear();
            table.rows.add(tables_json, false);

            $('#validation_error_single').addClass('hidden');
            $('#error_spreadsheet').removeClass('hidden')
            $('#datatables_div').show();

            $('#validation').css('width', '100%');
            $('#validation').removeClass('hidden');
            $('#metadata_file_preview').dataTable().fnAdjustColumnSizing()
            $("#edit_buttons").hide();
        }
     });

     $('#metadata_file_upload').on('change', function(event) {
        $('#panel_sample_metadata .panel-heading').html('<h3 class="panel-title">Sample Metadata</h3>');
        $('#validation').addClass('hidden');
        $('#upload_success').addClass('hidden');
        $('#date_format_audit').addClass('hidden');
     });
     
     $('#metadata_file_upload').on('filebatchuploadsuccess', function(event, files, extra) {
        $('#panel_sample_metadata .panel-body').slideUp();
        $('#panel_sample_metadata .panel-heading').html('<h3 class="panel-title">Sample Metadata <span class="pull-right glyphicon glyphicon-ok green"></span></h3>');
        Cookies.set('sample_metadata', 1);

        $('#upload_success').removeClass('hidden');
        $('#date_format_audit').removeClass('hidden');
     });

 });
