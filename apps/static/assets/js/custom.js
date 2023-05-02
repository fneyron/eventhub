let calendar;
function renderCalendar(id, events, user) {
    const calendarEl = d.getElementById(id);
    if (!calendarEl) {
        return;
    }
    const addNewEventModalEl = d.getElementById('modal-new-event');
    const addNewEventModal = new bootstrap.Modal(addNewEventModalEl);
    const newEventTitleInput = d.getElementById('eventTitle');
    const newEventStartDatepicker = new Datepicker(d.getElementById('dateStart'), { buttonClass: 'btn' });
    const newEventEndDatepicker = new Datepicker(d.getElementById('dateEnd'), { buttonClass: 'btn' });

    const editEventModalEl = d.getElementById('modal-edit-event');
    const editEventModal = new bootstrap.Modal(editEventModalEl);
    const editEventTitleInput = d.getElementById('eventTitleEdit');
    const editEventOrigTitleTooltip = d.getElementById('eventTitleEdit-tooltip');
    const editEventIdInput = d.getElementById('eventIdEdit');
    const editEventDescriptionInput = d.getElementById('eventDescriptionEdit');
    const editEventOrigDescriptionTooltip = d.getElementById('eventDescriptionEdit-tooltip');
    const editEventAttendeeInput = d.getElementById('eventAttendeeEdit');
    //const choices = new Choices(editEventAttendeeInput);
    tagify = new Tagify(editEventAttendeeInput, {whitelist:[]});

    const editEventStartDatepicker = new Datepicker(d.getElementById('dateStartEdit'), { buttonClass: 'btn' });
    const editEventEndDatepicker = new Datepicker(d.getElementById('dateEndEdit'), { buttonClass: 'btn' });
    const editEventDeleteButton = d.getElementById('deleteEvent');
    const editEventEditButton = d.getElementById('editEvent');

    // current id selection
    let currentId = null;

    calendar = new FullCalendar.Calendar(calendarEl, {
        selectable: true,
        initialView: 'dayGridMonth',
        themeSystem: 'bootstrap',
        editable: true,
        firstDay: 1,
        height: 600,
        windowResize: function (view) {
          if (window.innerWidth < 768) {
            calendar.setOption('height', 'auto');
          } else {
            // Set your desired calendar height for larger screens
            calendar.setOption('height', 600);
          }
        },

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
        buttonText: {
          today: ''
        },
        bootstrapFontAwesome: { today: 'redo' },
        eventSources:events,
        eventContent: function(arg) {
            var contentEl = document.createElement('div');

            title = '&nbsp;' + arg.event.title;
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
        /*dateClick: (d) => {
            addNewEventModal.show();
            newEventTitleInput.value = '';
            newEventStartDatepicker.setDate(d.date);
            newEventEndDatepicker.setDate(d.date.setDate(d.date.getDate() + 1));

            addNewEventModalEl.addEventListener('shown.bs.modal', function () {
                newEventTitleInput.focus();
            });
        },*/
        eventClick: (info) => {
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
            editEventOrigTitleTooltip.setAttribute('data-bs-content', info.event.extendedProps.orig_title);
            editEventTitleInput.value = info.event.title;
            editEventDescriptionInput.value = info.event.extendedProps.description;
            editEventOrigDescriptionTooltip.setAttribute('data-bs-content', info.event.extendedProps.orig_description);

            // add event listeners to title and description tooltips
            /*editEventOrigTitleTooltip.addEventListener('click', function() {
              editEventTitleInput.value = info.event.extendedProps.orig_title;
            });

            editEventOrigDescriptionTooltip.addEventListener('click', function() {
              editEventDescriptionInput.value = info.event.extendedProps.orig_description;
            });*/

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
    console.log(calendar.getEvents());
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

    document.getElementById('editEventForm').addEventListener('submit', (event) => {
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

    document.getElementById('deleteEvent').addEventListener('click', () => {
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

function checkTaskStatus(taskId) {
  $.get(`/task/${taskId}/status`)
    .done((result) => {
      if (result.status === "SUCCESS") {
        // task has completed successfully
        // stop the spinner and do something else
        $('#calendar-refresh').removeClass('fa-spin');
        if (calendar){
            calendar.refetchEvents();
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


function initializeCountrySelect(field_id){
    const countrySelect = $("#" + field_id).countrySelect({
        defaultCountry: "fr",
        preferredCountries: ['fr', 'gb', 'us'],
        responsiveDropdown: false,
    });
    return countrySelect;
}

function initializeAutofill(token, field_id) {
  const script = document.getElementById('search-js');
  script.onload = function() {
    autofill = mapboxsearch.autofill({
      accessToken: token,
    });
    autofill.addEventListener('retrieve', (event) => {
      const featureCollection = event.detail;
      const cc = featureCollection.features[0].properties.country_code;
      const countrySelect = $("#" + field_id).countrySelect();
      countrySelect.countrySelect("selectCountry", cc);
      $("#" + field_id + "_code").val(cc);
      const inputEl = event.target;
    });
  };
}

function loadMap(id, lng, lat, acc, zoom) {
    mapboxgl.accessToken = token;
    const metersToPixelsAtMaxZoom = (acc, lat) => acc / 0.075 / Math.cos(lat * Math.PI / 180)
    var map = new mapboxgl.Map({
        container: id,
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [lng, lat],
        zoom: zoom,
    });
    map.on('load', () => {
        // Create a new marker.
        const marker = new mapboxgl.Marker()
            .setLngLat([lng, lat])
            .addTo(map);
        var options = {
          steps: 100,
          units: 'kilometers'
        };
        if (acc != 0){
            var circle = turf.circle(turf.point([lng, lat]), acc/1000, options);
            // Create a circle for accuracy
             map.addLayer({
                "id": "circle-fill",
                "type": "fill",
                "source": {
                    "type": "geojson",
                    "data": circle
                },
                "paint": {
                    "fill-color": "#1da1f2",
                    "fill-opacity": 0.2
                }
            });
            map.fitBounds(turf.bbox(circle), {padding: 20});
        }
    });
    return mapboxgl;
}


function copy_to_clipboard() {
    const inputElement = document.querySelector('.form-control');
    inputElement.select();
    inputElement.setSelectionRange(0, 99999); // For mobile devices
    document.execCommand('copy');
}