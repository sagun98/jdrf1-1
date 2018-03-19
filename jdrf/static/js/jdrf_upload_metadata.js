/**
 * Javascript needed for the metadata upload functionality of the JDRF MIBC website.
 */

 jQuery(document).ready(function() {
    $.ajaxSetup({beforeSend: function(xhr, settings){
        xhr.setRequestHeader('X-CSRFToken', 
                             $("input[name='csrfmiddlewaretoken']").val());
      }});

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
    }

    if (Cookies.get('sample_metadata') == '1') {
        $('#panel_sample_metadata .panel-body').hide();
        $('#panel_sample_metadata .panel-heading').html('<h3 class="panel-title">Sample Metadata <span class="pull-right glyphicon glyphicon-ok green"></span></h3>');
        $('#upload_success').removeClass('hidden')
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

     var table = $('#metadata_file_preview').DataTable({
        //responsive: true,
        pageLength: 12,
        searching: false,
        deferLoading: 0,
        lengthChange: false,
        scrollY: '425px',
        scrollX: '400px',
        scrollCollapse: false,
        columns: [
            {data: 'bioproject_accession'},
            {data: 'host_subject_id'},
            {data: 'host_body_mass_index'},
            {data: 'host_diet'},
            {data: 'host_disease'},
            {data: 'host_body_product'},
            {data: 'host_tissue_sampled'},
            {data: 'host_family_relationship'},
            {data: 'host_genotype'},
            {data: 'host_phenotype'},
            {data: 'gastrointest_disord'},
            {data: 'ihmc_medication_code'},
            {data: 'subject_tax_id'},
            {data: 'subject_age'},
            {data: 'subject_sex'},
            {data: 'ethnicity'},
            {data: 'sample_id'},
            {data: 'collection_date'},
            {data: 'source_material_id'},
            {data: 'isolation_source'},
            {data: 'samp_mat_process'},
            {data: 'samp_store_dur'},
            {data: 'samp_store_temp'},
            {data: 'samp_vol_mass'},
            {data: 'animal_vendor'},
            {data: 'variable_region'},
            {data: 'organism_count'},
            {data: 'env_biom'},
            {data: 'env_feature'},
            {data: 'env_material'},
            {data: 'sequencer'},
            {data: 'read_number'},
            {data: 'sequencing_facility'},
            {data: 'filename'},
            {data: 'paired'},
            {data: 'md5_checksum'}
        ],
        columnDefs: [
            {
                targets: '_all',
                createdCell: function(td, cellData, rowData, row, col) {
                    if (typeof(cellData) == "string") {
                        var validation_elts = cellData.split(';');
                        if (validation_elts[0] == "ERROR") {
                            $(td).css('color', 'white');
                            $(td).css('font-weight', 'bold');
                            $(td).css('background-color', 'red');

                            $(td).attr('data-toggle', 'tooltip').attr('title', validation_elts[2]);
                            $(td).html(validation_elts[1]);
                        }
                    }
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
            $('#validation_error_single').html("<div class='glyphicon glyphicon-ban-circle'></div>" +
                                               "<div>" + response['error_msg'] + "</div");
            $('#validation_error_single').removeClass('hidden');
            $('#validation').removeClass('hidden');
        } else {
            $('#upload_success').addClass('hidden');
            Cookies.remove('sample_metadata');

            var errors_table = JSON.parse(response.errors_datatable);
            table.clear();
            table.rows.add(errors_table, false);

            $('#validation_error_single').addClass('hidden');
            $('#error_spreadsheet').removeClass('hidden')
            $('#datatables_div').show();

            $('#validation').css('width', '100%');
            $('#validation').removeClass('hidden');
            $('#metadata_file_preview').dataTable().fnAdjustColumnSizing()
        }
     });

     $('#metadata_file_upload').on('change', function(event) {
        $('#panel_sample_metadata .panel-heading').html('<h3 class="panel-title">Sample Metadata</h3>');
        $('#validation').addClass('hidden');
        $('#upload_success').addClass('hidden');
     });
     
     $('#metadata_file_upload').on('filebatchuploadsuccess', function(event, files, extra) {
        $('#panel_sample_metadata .panel-body').slideUp();
        $('#panel_sample_metadata .panel-heading').html('<h3 class="panel-title">Sample Metadata <span class="pull-right glyphicon glyphicon-ok green"></span></h3>');
        Cookies.set('sample_metadata', 1);

        $('#upload_success').removeClass('hidden');
     });

 });