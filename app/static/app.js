var eventData = [];
var infobox;
var map;
var pinLayer;
var timer;
var slide = 0;

function loadEvents(data) {
    eventData = data;
    render();
}

function firstSlide() {
    slide = 0;
    render();
}

function nextSlide() {
    if (slide + 1 < eventData.length) {
        slide++;
        render();
    }
}

function prevSlide() {
    if (slide > 0) {
        slide--;
        render();
    }
}

function lastSlide() {
    slide = eventData.length - 1;
    render();
}

function play() {
    $('#play').text('Pause');
    $('#play').off('click');
    $('#play').on('click', pause);

    playSlides();
}

function playSlides() {
    if (slide + 1 >= eventData.length) {
        pause();
    } else {
        nextSlide();
        timer = setTimeout(function () {
            playSlides();
        }, 750);
    }
}

function pause() {
    $('#play').text('Play');
    $('#play').off('click');
    $('#play').on('click', play);

    clearTimeout(timer);
}

function render() {
    $('#month').text(myearToString(eventData[slide].myear));

    pinLayer.clearLayers();

    var events = eventData[slide].events;
    for (var i = 0; i < events.length; i++) {
        var coords = events[i].location;
        var pushpin = L.marker([coords[0], coords[1]])
            .bindPopup(
                '<b>' + events[i].title + '</b><br />' +
                '<a href="' + events[i].link + '" target="_blank">Link</a>'
            )
            .addTo(map);
        pinLayer.addLayer(pushpin);
    }
}

function myearToString(myear) {
    var monthNames = ['0', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    var year = myear.substring(0, 4);
    var month = parseInt(myear.substring(4, 6), 10);
    return monthNames[month] + ' ' + year;
}

document.body.onload = function () {
    map = L.map('map').setView({lat: 39.833333, lon: -98.583333}, 4);

    // add the OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
    }).addTo(map);

    pinLayer = L.layerGroup();
    pinLayer.addTo(map);

    $('#play').click(play);
    $('#begin').click(firstSlide);
    $('#next').click(nextSlide);
    $('#prev').click(prevSlide);
    $('#last').click(lastSlide);

    $.getJSON('/events', loadEvents);
};
