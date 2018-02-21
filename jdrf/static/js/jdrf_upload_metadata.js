/**
 * Javascript needed for the metadata upload functionality of the JDRF MIBC website.
 */

 jQuery(document).ready(function() {
    $.ajaxSetup({beforeSend: function(xhr, settings){
        xhr.setRequestHeader('X-CSRFToken', 
                             $("input[name='csrfmiddlewaretoken']").val());
      }});


    $('#sample_type').on('change', function() {
        var value = $(this).val();

        if (value == "other") {
            $('#analysis_desc_div').removeClass('hidden');
        } else {
            $('#analysis_desc').val("");
            $('#analysis_desc_div').addClass('hidden');
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
         uploadExtraData: { 
             'csrfmiddlewaretoken': $("input[name='csrfmiddlewaretoken']").val(),
         }
     });

     var editor = new $.fn.DataTable.Editor({
         ajax: "/metadata/sample",
         table: "#metadata_file_preview",
         fields: [
            { label: 'BioProject Accession', name: 'bioproject_accession' },
            { label: 'Host Subject ID', name: 'host_subject_id' },
            { label: 'Host Body Mass Index', name: 'host_body_mass_index' },
            { label: 'Host Diet', name: 'host_diet' },
            { label: 'Host Disease', name: 'host_disease' },
            { label: 'Host Tissue Sampled', name: 'host_tissue_sampled' },
            { label: 'Host Family Relationship', name: 'host_family_relationship' },
            { label: 'Host Genotype', name: 'host_genotype' },
            { label: 'Host Phenotype', name: 'host_phenotype' },
            { label: 'Gastrointestinal Disorder', name: 'gastrointest_disord' },
            { label: 'IHMC Medication Code', name: 'ihmc_medication_code' },
            { label: 'Subject Taxonomy ID', name: 'subject_tax_id' },
            { label: 'Subject Age', name: 'subject_age' },
            { label: 'Subject Sex', name: 'subject_sex' },
            { label: 'Ethnicity', name: 'ethnicity' },
            { label: 'Sample ID', name: 'sample_id' },
            { label: 'Collection Date', name: 'collection_date' },
            { label: 'Sourced Material ID', name: 'source_material_id' },
            { label: 'Isolation Source', name: 'isolation_source' },
            { label: 'Sample Material Process', name: 'sample_mat_process' },
            { label: 'Sample Store Duration', name: 'sample_store_dur' },
            { label: 'Sample Store Temperature', name: 'sample_store_temp' },
            { label: 'Sample Volume Mass', name: 'sample_vol_mass' },
            { label: 'Animal Vendor', name: 'animal_vendor' },
            { label: 'Variable Region', name: 'variable_region' },
            { label: 'Organism Count', name: 'organism_count' },
            { label: 'ENVO Biome', name: 'env_biom' },
            { label: 'ENVO Feature', name: 'env_feature' },
            { label: 'ENVO Material', name: 'env_material' },
            { label: 'Sequencer', name: 'sequencer' },
            { label: 'Read Nmber', name: 'read_number' },
            { label: 'Sequencing Facility', name: 'sequencing_facility' },
            { label: 'Filename', name: 'filename' },
            { label: 'Paired', name: 'paired' },
            { label: 'md5_checksum', name: 'md5_checksum' }
        ]
     });


     $('#metadata_file_preview').on('click', 'tbody td:not(:first-child)', function(e) {
         editor.inline( this );
     });

     var table = $('#metadata_file_preview').DataTable({
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
        select : {

        },
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

     editor.on('submitComplete', function(e, json, data, action) {
         console.log("woooo");
     });

 });