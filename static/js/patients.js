function update_diagnosis() {
                    $.ajax({
                        type: "post",
                        url: '/patients/update_diagnosis',
                        data: JSON.stringify({'diagnosis': $('#edit_diagnosis').val(), 'patient_id': $('#save_diagnosis').attr('patient_id')}), // serializes the form's elements.
                        success: function (data) {
                            $('#diagnosis_div').css('display', 'none')
                            $(`tr#${ $('#save_diagnosis').attr('patient_id') }`).find('.diagnosis').text($('#edit_diagnosis').val());
                        }
                    });
}

function update_symptoms() {
                    $.ajax({
                        type: "post",
                        url: '/patients/update_symptoms',
                        data: JSON.stringify({'symptoms': $('#edit_symptoms').val(), 'patient_id': $('#save_symptoms').attr('patient_id')}), // serializes the form's elements.
                        success: function (data) {
                            $('#symptoms_div').css('display', 'none')
                            $(`tr#${ $('#save_symptoms').attr('patient_id') }`).find('.symptoms').text($('#edit_symptoms').val());
                        }
                    });
}

$(document).ready(function(){

    $('.symptoms').on('click', function(){
                $('#save_symptoms').attr('patient_id', $(this).closest('tr').attr('id'))
                $('#symptoms_div').css('display', 'block')
                $('#edit_symptoms').val($(this).text());
    });

    $('.diagnosis').on('click', function(){
                $('#save_diagnosis').attr('patient_id', $(this).closest('tr').attr('id'))
                $('#diagnosis_div').css('display', 'block')
                $('#edit_diagnosis').val($(this).text());
    });

})