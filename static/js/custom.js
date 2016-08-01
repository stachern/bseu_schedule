
function get_schedule_options(){
    if (this.id=='faculty' && this.value>0){
        $.get("proxy", {'__act':'__id.22.main.inpFldsA.GetForms',
                        'faculty':this.value},
            function(data){
                parser(data, $('select#form'));
            });
    }
    if (this.id=='form' && this.value>0){
        $.get("proxy", {'__act':'__id.23.main.inpFldsA.GetCourse',
            'faculty':$('select#faculty').val(),
            'form':this.value},
            function(data){
                parser(data, $('select#course'));
            });
    }
    if (this.id=='course' && this.value>0){
        $.get("proxy", {'__act':'__id.23.main.inpFldsA.GetGroups',
                        'faculty':$('select#faculty').val(),
                        'form':$('select#form').val(),
                        'course':this.value},
            function(data){
                 parser(data, $('select#group'));
            });
    }
    if (this.id === "group" && this.value) {
        $("#study_detail").find("button")
                          .removeClass("disabled").prop("disabled", false);
    } else {
        $("#study_detail").find("button")
                          .addClass("disabled").prop("disabled", true);
    }
}

function parser(data, item){
    $(item).html('<option value="" selected="selected">Загрузка..</option>');
    $($.parseJSON(data)).each(function(){
        $(item).append('<option value="'+this.value+'">'+this.text+'</option>');
        });
    $(item).find('option[selected="selected"]').html('Выберите');
    $(item).prop("disabled", false);
    }
