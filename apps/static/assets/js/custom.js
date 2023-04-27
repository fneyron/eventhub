function renderCalendar(id, events, user) {
    var calendarEl = d.getElementById(id);
    if (calendarEl) {
        var addNewEventModalEl = d.getElementById('modal-new-event');
        var addNewEventModal = new bootstrap.Modal(addNewEventModalEl);
        var newEventTitleInput = d.getElementById('eventTitle');
        var newEventStartDatepicker = new Datepicker(d.getElementById('dateStart'), { buttonClass: 'btn' });
        var newEventEndDatepicker = new Datepicker(d.getElementById('dateEnd'), { buttonClass: 'btn' });

        var editEventModalEl = d.getElementById('modal-edit-event');
        var editEventModal = new bootstrap.Modal(editEventModalEl);
        var editEventTitleInput = d.getElementById('eventTitleEdit');
        var editEventIdInput = d.getElementById('eventIdEdit');
        var editEventDescriptionInput = d.getElementById('eventDescriptionEdit');
        var editEventAttendeeInput = d.getElementById('eventAttendeeEdit');
        //var choices = new Choices(editEventAttendeeInput);
        tagify = new Tagify(editEventAttendeeInput, {whitelist:[]});

        var editEventStartDatepicker = new Datepicker(d.getElementById('dateStartEdit'), { buttonClass: 'btn' });
        var editEventEndDatepicker = new Datepicker(d.getElementById('dateEndEdit'), { buttonClass: 'btn' });
        var editEventDeleteButton = d.getElementById('deleteEvent');
        var editEventEditButton = d.getElementById('editEvent');

        // current id selection
        var currentId = null;

        var calendar = new FullCalendar.Calendar(calendarEl, {
            selectable: true,
            initialView: 'dayGridMonth',
            themeSystem: 'bootstrap5',
            editable: true,
            customButtons: {
              refreshButton: {
                text: 'Refresh',
                click: function() {
                  calendar.refetchEvents();
                }
              }
            },
            headerToolbar: {
                right: 'today prev,next',
                left: 'title',
            },
            buttonIcons: {
              prev: 'arrow-left-square-fill',
              next: 'chevron-right',
              prevYear: 'chevrons-left', // double chevron
              nextYear: 'chevrons-right' // double chevron
            },
            bootstrapFontAwesome: {
              close: 'fa-times',
              prev: 'fa-chevron-left',
              next: 'fa-chevron-right',
              prevYear: 'fa-angle-double-left',
              nextYear: 'fa-angle-double-right'
            },
            eventSources:events,
            buttonText: {
                prev: 'Previous',
                next: 'Next',
                today: 'Today',
            },
            eventContent: function(arg) {
                var contentEl = document.createElement('div');

                title = '&nbsp;' + arg.event.title;
                console.log(arg.event.extendedProps);
                if (!arg.event.extendedProps.attendees.length){
                    title = '&nbsp;<i class="fa fa-warning"></i>' + title;
                }
                contentEl.innerHTML = title;

                var colors = arg.event.extendedProps.otherColors || [];

                if (colors.length) {
                    var gradient = `repeating-linear-gradient(-45deg, ${arg.event.backgroundColor}`;
                    var stepSize = 10;
                    for (var i = 0; i < colors.length; i++) {
                        gradient += `, ${arg.event.backgroundColor} ${stepSize}px, ${colors[i]} ${stepSize}px, ${colors[i]} ${stepSize * 2}px`;
                        stepSize *= 2;
                    }
                    contentEl.style.backgroundImage = gradient + ')';
                } else {
                    contentEl.style.backgroundColor = arg.event.backgroundColor;
                }

                //contentEl.style.border = `2px solid ${arg.event.borderColor}`;

                return { domNodes: [contentEl] };
            },
            // other calendar options
            /*eventMouseEnter: function(info) {
              var tooltip = new Tooltip(info.el, {
                title: info.event.title + ': ' + info.event.extendedProps.description,
                placement: 'top',
                trigger: 'hover',
                container: 'body'
              });
            },
            eventMouseLeave: function(info) {
              tooltip.dispose();
            },*/
            dateClick: function (d) {
                addNewEventModal.show();
                newEventTitleInput.value = '';
                newEventStartDatepicker.setDate(d.date);
                newEventEndDatepicker.setDate(d.date.setDate(d.date.getDate() + 1));

                addNewEventModalEl.addEventListener('shown.bs.modal', function () {
                    newEventTitleInput.focus();
                });
            },
            eventClick: function (info, element) {
                // Check if event source is not editable
                if (info.event.extendedProps.disabled) {

                    // Disable form fields
                    //editEventTitleInput.disabled = true;
                    //editEventDescriptionInput.disabled = true;
                    d.getElementById('dateStartEdit').disabled = true;
                    d.getElementById('dateEndEdit').disabled = true;
                    editEventDeleteButton.disabled = true;
                } else {
                    // Enable form fields
                    //editEventTitleInput.disabled = false;
                    //editEventDescriptionInput.disabled = false;
                    d.getElementById('dateStartEdit').disabled = false;
                    d.getElementById('dateEndEdit').disabled = false;
                    editEventDeleteButton.disabled = false;
                }


                // Remove errors
                $('.form-control.is-invalid').removeClass('is-invalid');
                $('.invalid-feedback').text('');

                // set current id
                currentId = info.event.id;
                editEventIdInput.value = info.event.id;
                editEventTitleInput.value = info.event.title;
                editEventDescriptionInput.value = info.event.extendedProps.description;
                /*choices.clearStore();
                if (info.event.extendedProps.attendees.length){
                    choices.setValue(info.event.extendedProps.attendees);
                }*/

                const initialValue = info.event.extendedProps.attendees;
                tagify.loadOriginalValues(initialValue);

                // listen to any keystrokes which modify tagify's input
                tagify.on('input', onInput)

                function onInput( e ){
                  var value = e.detail.value
                  tagify.whitelist = null // reset the whitelist
                  if (value.length < 2) {
                    return; // Do not search if the input length is less than 2
                  }
                  fetch('/user/' + value + '/json')
                    .then(RES => RES.json())
                    .then(function(newWhitelist){
                      tagify.whitelist = newWhitelist // update whitelist Array in-place
                    })
                }


                editEventStartDatepicker.setDate(info.event.start);
                editEventEndDatepicker.setDate(info.event.end ? info.event.end : info.event.start);

                editEventModal.show();
                editEventModalEl.addEventListener('shown.bs.modal', function () {
                    editEventTitleInput.focus();
                });
            }
        });
        calendar.render();

        d.getElementById('addNewEventForm').addEventListener('submit', function (event) {
            event.preventDefault();
            calendar.addEvent({
                id: Math.random() * 10000, // this should be a unique id from your back-end or API
                title: newEventTitleInput.value,
                start: moment(newEventStartDatepicker.getDate()).format('YYYY-MM-DD'),
                end: moment(newEventEndDatepicker.getDate()).format('YYYY-MM-DD'),
                className: 'bg-secondary',
                dragabble: true
            });
            addNewEventModal.hide();
        });

        d.getElementById('editEventForm').addEventListener('submit', function (event) {
            event.preventDefault();

            // Update Full calendar live
            var editEvent = calendar.getEventById(currentId);
            var startDate = moment(editEventStartDatepicker.getDate()).format('YYYY-MM-DD HH:mm');
            var endDate = moment(editEventEndDatepicker.getDate()).format('YYYY-MM-DD HH:mm');

            editEvent.setProp('id', editEventIdInput.value);
            editEvent.setProp('title', editEventTitleInput.value);
            //editEvent.setExtendedProp('attendees', editEventAttendeeInput.value.length ? editEventAttendeeInput.value.split(',') : []);
            editEvent.setExtendedProp('attendees', tagify.value.map(function (t) { return t.value; }));
            editEvent.setExtendedProp('description', editEventDescriptionInput.value);
            editEvent.setStart(startDate);
            editEvent.setEnd(endDate);


            // Send the updated event data to the server
            var eventData = {
                'id': editEvent.id,
                'csrf_token': document.querySelector('input[name="csrf_token"]').value,
                'title': editEvent.title,
                'attendee': editEvent.extendedProps.attendees,
                'description': editEvent.extendedProps.description,
                'start_time': moment(editEvent.start).format('YYYY-MM-DD HH:mm'),
                'end_time': moment(editEvent.end).format('YYYY-MM-DD HH:mm'),
            };
            console.log(eventData);
            $.ajax({
                type: "POST",
                url: "/event/" + editEvent.id + "/update",
                data: eventData,
                //contentType: "application/json; charset=utf-8",
                //dataType: "json",
                success: function (data) {
                    if(!data.success){
                        // Error, display the errors to the user
                        var errors = data.errors;
                        console.log(errors);
                        for (var field in errors) {
                            var error = errors[field];
                            var $field = $('[name="' + field + '"]');
                            if (field == 'attendee'){
                                $field = $field.closest('div').find('tags');
                            }
                            $field.addClass('is-invalid');
                            console.log($field.next('.invalid-feedback'));
                            $field.closest('div').find('.invalid-feedback').text(error);

                        }
                        editEventModal.show();
                    }
                    else {
                        editEventModal.hide();
                    }
                },
                error: function (errMsg) {
                    console.log(errMsg);
                }
            });


        });

        d.getElementById('deleteEvent').addEventListener('click', function () {
            swalWithBootstrapButtons.fire({
                icon: 'error',
                title: 'Confirm deletion',
                text: 'Are you sure you want to delete this event?',
                showCancelButton: true,
                confirmButtonText: "Yes, delete it!",
                cancelButtonText: 'No, cancel!',
            }).then(function (result) {
                if (result.value) {
                    swalWithBootstrapButtons.fire(
                        'Deleted!',
                        'The event has been deleted.',
                        'success'
                    );
                    calendar.getEventById(currentId).remove();
                } else if (result.dismiss === Swal.DismissReason.cancel) {
                    editEventModal.hide();
                }
            })
        });
        return calendar;
    }
}

function checkTaskStatus(taskId) {
  $.get(`/task/${taskId}/status`)
    .done((result) => {
      if (result.status === "SUCCESS") {
        // task has completed successfully
        // stop the spinner and do something else
        $('#calendar-refresh').removeClass('fa-spin');
        if (mycalendar){
            mycalendar.refetchEvents();
        }
      } else if (result.status === "FAILURE") {
        // task has failed
        // stop the spinner and show an error message
        $('#calendar-refresh').removeClass('fa-spin');
        console.log(result.status);
      } else {
        // task is still running, check again in 1 second
        setTimeout(() => {
          checkTaskStatus(taskId);
        }, 1000);
      }
    })
    .fail((error) => {
      // something went wrong with the AJAX request
      // stop the spinner and show an error message
      $('#calendar-refresh').removeClass('fa-spin');
      console.log(error);
    });
}


