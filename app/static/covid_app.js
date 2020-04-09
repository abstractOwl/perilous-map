var eventData = [];
var infobox;
var map;
var pinLayer;

function render(events) {
    for (var i = 0; i < events.length; i++) {
        var coords = events[i].location;
        var pos = new Microsoft.Maps.Location(coords[0], coords[1]);
        var pushpin = new Microsoft.Maps.Pushpin(pos, {
            color: 'red',
            enableHoverStyle: true
        });
        pushpin.metadata = {
            title: events[i].title,
            description: '<a href="' + events[i].link + '" target="_blank">Link</a>'
        };
        pinLayer.add(pushpin);

        Microsoft.Maps.Events.addHandler(pushpin, 'click', function (args) {
            infobox.setOptions({
                location: args.target.getLocation(),
                title: args.target.metadata.title,
                description: args.target.metadata.description,
                visible: true
            });
        });
    }
}

document.body.onload = function () {
    map = new Microsoft.Maps.Map(document.getElementById('map'), {
        center: new Microsoft.Maps.Location(39.833333, -98.583333),
        zoom: 4
    });

    pinLayer = new Microsoft.Maps.Layer();
    map.layers.insert(pinLayer);

    infobox = new Microsoft.Maps.Infobox(null, { visible: false });
    infobox.setMap(map);

    $.getJSON('/covid_events', render);
};
