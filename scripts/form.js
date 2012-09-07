
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
    $($.parseXML(data)).find('DATAPACKET ROWDATA ROW').each(function(i){
        $(item).append('<option value="'+$(this).attr('value')+'">'+$(this).attr('text')+'</option>');
        });
    $(item).attr('onchange', 'getval(this);');
    $(item).find('option[selected="selected"]').html('Выберите')
    }

function getPermalink(that){
    $('li#permalink').html('').append('<h3>Постоянная ссылка</h3>').append('<a href="/scheduleapi?action=view&faculty='+$('select#faculty').val()+'&group='+$('select#group').val()+'&course='+$('select#course').val()+'&form='+$('select#form').val()+'">На неделю</a>').append(' | <a href="/scheduleapi?action=view&period=3&faculty='+$('select#faculty').val()+'&group='+$('select#group').val()+'&course='+$('select#course').val()+'&form='+$('select#form').val()+'">На семестр</a>').show();
    }
function submitform(that){
    if(($('select#group').val() || $('li#permalink').is('li')) && $('select#calendar').val()!="-1"){
        var fdata=$('form#calendartool').serialize();
        fdata=fdata+'&calendar_name='+$('select#calendar option:selected').text();
        if($('select#calendar').val()==-1){
            alert('Вы должны выбрать календарь!')
        }else{
            $.post("/", fdata , function(){
                alert('Сохранено. Для изменения - просто перезаполните форму');
                window.location.href='/';
            });
        }
    }else{
        alert('Вы должны выбрать все обязательные пункты!')
        }
}

function importcal(that){
    window.location=$('a:contains("На неделю")').attr('href').replace('view', 'save');
}

function saver(){
    $('b#saveme').show();
    }
