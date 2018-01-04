/**
 * Javascript needed for the metadata upload functionality of the JDRF MIBC website.
 */


 jQuery(document).ready(function() {
     //$('#validation').hide();

     $('#metadata_file_upload').fileinput({
         showPreview: false,
         uploadUrl: 'metadata/',
         msgPlaceholder: 'Select metadata file to upload...'
     });

     $('#metadata_file_preview').DataTable({
        //responsive: true,
        pageLength: 12,
        searching: false,
        lengthChange: false,
        scrollY: '425px',
        scrollX: '400px',
        scrollCollapse: false,
        autoWidth: true,
        ajax: {
            url: "/metadata/validate",
        },
        columnDefs: [
            {
                targets: '_all',
                // render: function(data, type, row) {
                //     var validation_elts = data.split(';');
                //     if (validation_elts[0] == "ERROR") {
                //         return '<span data-toggle="tooltip" title="' + validation_elts[2] + '">' + validation_elts[1] + '</span>';
                //     } else {
                //         return data;
                //     }
                // },
                createdCell: function(td, cellData, rowData, row, col) {
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
        ]
     });

    $('#metadata_file_preview').on('draw.dt', function () {
        $('[data-toggle="tooltip"]').tooltip({
            container : 'body'
        });
    });

     $('#metadata_file_upload').on('fileuploaded', function(event, data, previewId, index){
        var form = data.form;
        var files = data.files;
        var extra = data.extra;
        var response = data.response;
        var reader = data.reader;

        console.log('DEBUG: ' + files);
        console.log('DEBUG: ' +  response);
     });
 });