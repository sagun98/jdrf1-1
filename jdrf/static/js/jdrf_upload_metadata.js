/**
 * Javascript needed for the metadata upload functionality of the JDRF MIBC website.
 */

 jQuery(document).ready(function() {
     $('#validation').hide();

     $('#metadata_file_upload').fileinput({
         showPreview: false,
         uploadAsync: false,
         uploadUrl: '/upload_metadata/',
         msgPlaceholder: 'Select metadata file to upload...',
         uploadExtraData: { 
             'csrfmiddlewaretoken': $("input[name='csrfmiddlewaretoken']").val(),
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
        autoWidth: true,
        columns: [
            {data: 'study_id'},
            {data: 'pi_name'},
            {data: 'bioproject_accession'},
            {data: 'host_subject_id'},
            {data: 'host_body_mass_index'},
            {data: 'host_diet'},
            {data: 'host_disease'},
            {data: 'host_body_product'},
            {data: 'host_family_relationship'},
            {data: 'host_genotype'},
            {data: 'host_phenotype'},
            {data: 'host_tissue_sampled'},
            {data: 'gastrointest_disord'},
            {data: 'ihmc_medication_code'},
            {data: 'subject_tax_id'},
            {data: 'subject_age'},
            {data: 'subject_sex'},
            {data: 'ethnicity'},
            {data: 'geo_loc_name'},
            {data: 'sample_id'},
            {data: 'sample_type'},
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
        var errors_table = JSON.parse(response.errors_datatable);
        table.rows.add(errors_table, false);

        $('#validation').show(function() { 
            $('#validation').css('width', '100%');
            $('#metadata_file_preview').dataTable().fnAdjustColumnSizing()
        })
     });

     $('#metadata_file_upload').on('filepreupload', function(event, data, previewId, index) {
        $('#metadata_file_preview').hide();
     });
     
 });