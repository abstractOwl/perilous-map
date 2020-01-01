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
                }, 2500);
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

            for (var i = pinLayer.getPrimitives().length - 1; i >= 0; i--) {
                var pushpin = pinLayer.getPrimitives()[i];
                if (pushpin instanceof Microsoft.Maps.Pushpin) {
                    Microsoft.Maps.Events.removeHandler(pushpin);
                    pinLayer.removeAt(i);
                }
            }

            var events = eventData[slide].events;
            for (var i = 0; i < events.length; i++) {
                var coords = events[i].location;
                var pos = new Microsoft.Maps.Location(coords[0], coords[1]);
                var pushpin = new Microsoft.Maps.Pushpin(pos, {
                    color: 'orange',
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

        function myearToString(myear) {
            var monthNames = ['0', 'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
            var year = myear.substring(0, 4);
            var month = parseInt(myear.substring(4, 6), 10);
            return monthNames[month] + ' ' + year;
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

            $('#play').click(play);
            $('#begin').click(firstSlide);
            $('#next').click(nextSlide);
            $('#prev').click(prevSlide);
            $('#last').click(lastSlide);

            $.getJSON('/events', loadEvents);
        };
