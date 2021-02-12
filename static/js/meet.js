function update_notes() {
                    $.ajax({
                        type: "post",
                        url: '/meets/update_notes',
                        data: JSON.stringify({'notes': $('#edit_notes').val(), 'meet_id': $('#save_notes').attr('meet_id')}), // serializes the form's elements.
                        success: function (data) {
                            $('#notes_div').css('display', 'none')
                            $(`tr#${ $('#save_notes').attr('meet_id') }`).find('.notes').text($('#edit_notes').val());
                        }
                    });

            }

            function refresh_table() {
                    $.ajax({
                        type: "get",
                        url: '/meets/get_meets_by_date',
                        data: {'date': $('#date').val()}, // serializes the form's elements.
                        success: function (data) {
                            $("#meets").find("tr:gt(0)").remove()
                            for (let meet of data['data']){
                                $('#meets').append(
                                    `<tr id="${meet['meet_id']}">
                                         <td>${meet['meet_time']}</td>
                                         <td>${meet['patient']}</td>
                                         <td>${meet['notes']}</td>
                                    </tr>`
                                );
                            }
                        }
                    });

            }

$(document).ready(function(){

    $('.notes').on('click', function(){
                $('#save_notes').attr('meet_id', $(this).closest('tr').attr('id'))
                $('#notes_div').css('display', 'block')
                $('#edit_notes').val($(this).text());
    });



            $('#create_meet').submit(function (e) {
            var url = '/meets/create_meet'; // send the form data here.
            $.ajax({
                type: "post",
                url: url,
                data: $(this).serialize(), // serializes the form's elements.
                success: (data) => {
                    if(!Array.isArray(data)){
                        $(this).append('<p> Встреча успешно добавлена! </p>')  // display the returned data in the console.
                        console.log(data)
                        $('#meets').append(
                                    `<tr id="${data['meet_id']}">
                                         <td>${data['meet_time']}</td>
                                         <td>${data['patient']}</td>
                                         <td>${data['notes']}</td>
                                    </tr>`
                                );
                    }
                    else{
                        for (const [key, value] of Object.entries(data)) {
                              value.forEach(function (item) {
                                    $('#'+key+'_errors').append(`<span>[${item}]</span>`)
                              })
                        }
                    }
                }
            });
            e.preventDefault(); // block the traditional submission of the form.
        });

})