const OPTIONS = {
    faculty: {
        action: "__id.22.main.inpFldsA.GetForms",
        next: "form"
    },
    form: {
        action: "__id.23.main.inpFldsA.GetCourse",
        prev: ["faculty"],
        next: "course"
    },
    course: {
        action: "__id.23.main.inpFldsA.GetGroups",
        prev: ["faculty", "form"],
        next: "group"
    }
};

function get_schedule_options() {
    if (Object.keys(OPTIONS).includes(this.id) && this.value > 0) {
        let params = { "__act": OPTIONS[this.id]["action"] };
        if (Object.keys(OPTIONS[this.id]).includes("prev")) {
            let prevOptions = OPTIONS[this.id]["prev"];
            for (let prev of prevOptions) {
                params[prev] = $(`select#${prev}`).val();
            }
        }
        params[this.id] = this.value;
        $.get("proxy", params, data => parser(data, $(`select#${OPTIONS[this.id]["next"]}`)));
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
    if (data["error"] === "bseu_down") {
        return window.location.href = "/";
    }

    parsedData = $.parseJSON(data);
    if (!parsedData) {
        return null;
    }

    $(item).html('<option value="" selected="selected">Загрузка..</option>');
    $(parsedData).each(function(){
        $(item).append('<option value="'+this.value+'">'+this.text+'</option>');
    });
    $(item).find('option[selected="selected"]').html('Выберите');
    $(item).prop("disabled", false);
}

$('#study_detail select').change(get_schedule_options);

$('select#calendar').change(function(){
    let selected_option = $('#calendar option:selected');
    if (selected_option.val() === '-1') {
        $('input#calendar_name').removeAttr('value');
        $('form#calendar_detail').find('button').prop('disabled', true);
    } else {
        $('input#calendar_name').val(selected_option.text());
        $('form#calendar_detail').find('button').prop('disabled', false);
    }
});

$('#schedule-tab-bar a').click(function (e) {
    e.preventDefault();
    $(this).tab('show');
});

$('#feedback_modal button.btn-primary').click(function(){
    if($.trim($('textarea#comment').val())){
        $.post("comment", $('form#feedback_form').serialize(), function(){
            $('#feedback_modal').modal('hide');
            $('textarea#comment').val("");
        });
    } else {
        $('#feedback_form').addClass('error');
    }
})
