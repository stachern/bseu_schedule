
function getval(that){
    saver();
    if (that.id=='faculty' && that.value>0){
        $('select#form').removeAttr('disabled');
        $.get("proxy", {'__act':'__id.22.main.inpFldsA.GetForms','faculty':that.value}, function(data){
            parser(data, $('select#form'))
            });
    }
    if (that.id=='form' && that.value>0){
        $('select#course').removeAttr('disabled');
        $.get("proxy", {'__act':'__id.23.main.inpFldsA.GetCourse','faculty':$('select#faculty').val(), 'form':that.value}, function(data){
            parser(data, $('select#course'))
            });
    }
    if (that.id=='course' && that.value>0){
        $('select#group').removeAttr('disabled');
        $.get("proxy", {'__act':'__id.23.main.inpFldsA.GetGroups','faculty':$('select#faculty').val(), 'form':$('select#form').val(), 'course':that.value}, function(data){
            parser(data, $('select#group'))
            });
    }
    if (that.id=='group'){
        getPermalink(that);
        } 
}

function parser(data, item){
    $(item).html('');
    $(item).append('<option value="" selected="selected">Загрузка..</option>');
    $($.parseJSON(data)).each(function(i){
        $(item).append('<option value="'+this.value+'">'+this.text+'</option>');
        });
    $(item).attr('onchange', 'getval(this);');
    $(item).find('option[selected="selected"]').html('Выберите')
    }
