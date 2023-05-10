let calendar;

function openEditEventModalById(eventId) {
  const event = calendar.getEventById(eventId);
  openEditEventModal({ event });
}

function openEditEventModal(info) {

    // Check if event source is not editable
    if (info.event.extendedProps.disabled) {
        // Disable form fields
        $('#dateStartEdit').prop('disabled', true);
        $('#dateEndEdit').prop('disabled', true);
        $('#deleteEvent').prop('disabled', true);
    } else {
        // Enable form fields
        $('#dateStartEdit').prop('disabled', false);
        $('#dateEndEdit').prop('disabled', false);
        $('#deleteEvent').prop('disabled', false);
    }

    // Remove errors
    $('.form-control.is-invalid').removeClass('is-invalid');
    $('.invalid-feedback').text('');

    // set current id
    $('#eventIdEdit').val(info.event.id);
    $('#eventTitleEdit-tooltip').attr('data-bs-content', info.event.extendedProps.orig_title);
    $('#eventTitleEdit').val(info.event.title);
    $('#eventDescriptionEdit').val(info.event.extendedProps.description);
    $('#eventDescriptionEdit-tooltip').attr('data-bs-content', info.event.extendedProps.orig_description);
    const editEventStartDatepicker = new Datepicker(d.getElementById('dateStartEdit'), { buttonClass: 'btn' });
    const editEventEndDatepicker = new Datepicker(d.getElementById('dateEndEdit'), { buttonClass: 'btn' });
    editEventStartDatepicker.setDate(info.event.start);
    editEventEndDatepicker.setDate(info.event.end ? info.event.end : info.event.start);

    // TAGIFY
    const initialValue = info.event.extendedProps.attendees;
    tagify.loadOriginalValues(initialValue);
    tagify.on('input', onInput)

    loadMap('map', info.event.extendedProps.address, info.event.extendedProps.longitude, info.event.extendedProps.latitude, 0, 12)

    $('#modal-edit-event').modal('show');
    $('#modal-edit-event').on('shown.bs.modal', function () {
      $('#eventTitleEdit').focus();
    });

    function onInput(e) {
        var value = e.detail.value
        tagify.whitelist = null // reset the whitelist
        if (value.length < 2) {
            return; // Do not search if the input length is less than 2
        }
        fetch('/user/' + value + '/json')
            .then(RES => RES.json())
            .then(function (newWhitelist) {
                tagify.whitelist = newWhitelist // update whitelist Array in-place
            })
    }
}

function getEventContent(arg) {
  const contentEl = document.createElement('div');
  let title = '&nbsp;' + arg.event.title;
  let popoverContent = '';
  if (arg.event.extendedProps.attendees.length) {
    const attendees = arg.event.extendedProps.attendees;
    title = '&nbsp;<i class="fa fa-users"></i>&nbsp;' + title;
    attendees.forEach((attendee) => {
      popoverContent += `<p>${attendee}</p>`;
    });
  }
  contentEl.innerHTML = title;

  // Add popover with attendees information
  if (popoverContent !== '') {
    const popover = new bootstrap.Popover(contentEl, {
      content: popoverContent,
      trigger: 'hover',
      html: true,
    });
  }

  return { domNodes: [contentEl] };
}

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

    var calendar = new FullCalendar.Calendar(calendarEl, {
        selectable: true,
        initialView: 'dayGridMonth',
        themeSystem: 'bootstrap',
        editable: false,
        firstDay: 1,
        height: 700,
        windowResize: function (view) {
          if (window.innerWidth < 768) {
            calendar.setOption('height', 'auto');
          } else {
            // Set your desired calendar height for larger screens
            calendar.setOption('height', 700);
          }
        },
        headerToolbar: {
            right: 'today prev,next',
            left: 'title',
        },
        buttonText: {
          today: ''
        },
        eventSources:events,
        eventContent: getEventContent,
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
            openEditEventModal(info);
        }
    });
    calendar.render();

    document.getElementById('addNewEventForm').addEventListener('submit', function (event) {
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

        var eventId = $('#eventIdEdit').val()
        var editEvent = calendar.getEventById(eventId);
        console.log(editEvent);

        var startDate = moment($('#dateStartEdit').val()).format('YYYY-MM-DD HH:mm');
        var endDate = moment($('#dateEndEdit').val()).format('YYYY-MM-DD HH:mm');

        editEvent.setProp('title', editEventTitleInput.value);
        editEvent.setExtendedProp('attendees', tagify.value.map(function (t) { return t.value; }));
        editEvent.setExtendedProp('description', editEventDescriptionInput.value);
        editEvent.setStart(startDate);
        editEvent.setEnd(endDate);


        // Send the updated event data to the server
        var eventData = {
            'id': eventId,
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

function initializeAutofill(field_id) {
  const script = document.getElementById('search-js');
  script.onload = function() {
    autofill = mapboxsearch.autofill({
      accessToken: window.mapbox_token,
    });
    autofill.addEventListener('retrieve', (event) => {
      const featureCollection = event.detail;
      const cc = featureCollection.features[0].properties.country_code;
      const countrySelect = $("#" + field_id).countrySelect();
      countrySelect.countrySelect("selectCountry", cc);
      $("#" + field_id + "_code").val(cc);
      $("#latitude").val(event.detail.features[0].geometry.coordinates[1]);
      $("#longitude").val(event.detail.features[0].geometry.coordinates[0]);
      const inputEl = event.target;
    });
  };
}

function loadMap(id, address, lng, lat, acc, zoom) {
    mapboxgl.accessToken = window.mapbox_token;
    var map = new mapboxgl.Map({
        container: id,
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [lng, lat],
        zoom: zoom,
    });

     const popup = new mapboxgl.Popup().setHTML(`
        <strong>${address}</strong><br>
        <a href="https://www.google.com/maps/dir/?api=1&destination=${address}" target="_blank">Get Directions</a>
    `);

    // Create a new marker with the custom popup
    const marker = new mapboxgl.Marker()
        .setLngLat([lng, lat])
        .setPopup(popup)
        .addTo(map);

    map.on('load', () => {
        map.resize();
    });
    return mapboxgl;
}


function copy_to_clipboard() {
    const inputElement = document.querySelector('.form-control');
    inputElement.select();
    inputElement.setSelectionRange(0, 99999); // For mobile devices
    document.execCommand('copy');
}

// Index.html choices for users
function initChoices(el) {
    new Choices(el, {
        placeholder: true,
        placeholderValue: 'Select an option',
        searchEnabled: false,
        shouldSort: false,
        itemSelectText: '',
        renderChoiceLimit: -1,
    });
}