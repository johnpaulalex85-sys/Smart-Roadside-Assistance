/* location.js — OpenStreetMap Nominatim Autocomplete for workshop registration */

let map, marker;
let debounceTimer;

function initNominatimAutocomplete() {
    const input = document.getElementById('locationSearch');
    const suggestionsBox = document.getElementById('suggestions');
    if (!input || !suggestionsBox) return;

    input.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        const query = this.value;
        if (query.length < 3) {
            suggestionsBox.style.display = 'none';
            return;
        }

        debounceTimer = setTimeout(() => {
            fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&limit=5`)
                .then(res => res.json())
                .then(data => {
                    suggestionsBox.innerHTML = '';
                    if (data.length === 0) {
                        suggestionsBox.style.display = 'none';
                        return;
                    }
                    data.forEach(place => {
                        const div = document.createElement('div');
                        div.className = 'suggestion-item';
                        div.textContent = place.display_name;
                        div.onclick = () => selectPlace(place);
                        suggestionsBox.appendChild(div);
                    });
                    suggestionsBox.style.display = 'block';
                })
                .catch(err => console.error('Nominatim error:', err));
        }, 500);
    });

    // Close suggestions when clicking outside
    document.addEventListener('click', function (e) {
        if (e.target !== input && e.target !== suggestionsBox) {
            suggestionsBox.style.display = 'none';
        }
    });

    function selectPlace(place) {
        input.value = place.display_name;
        suggestionsBox.style.display = 'none';

        const lat = parseFloat(place.lat);
        const lng = parseFloat(place.lon);

        document.getElementById('lat').value = lat;
        document.getElementById('lng').value = lng;
        document.getElementById('locationStatus').textContent =
            `📍 Coordinates captured: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;

        // Show map preview
        const mapWrapper = document.getElementById('mapWrapper');
        if (mapWrapper) {
            mapWrapper.style.display = 'block';
            const mapEl = document.getElementById('workshopMap');

            if (!map) {
                map = L.map(mapEl).setView([lat, lng], 15);
                // Use CartoDB Dark Matter tile layer to match dark theme
                L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                    subdomains: 'abcd',
                    maxZoom: 20
                }).addTo(map);
            } else {
                map.setView([lat, lng], 15);
            }

            if (marker) marker.remove();
            marker = L.marker([lat, lng]).addTo(map);
            // Invalidate size to ensure map renders correctly when container becomes visible
            setTimeout(() => { map.invalidateSize(); }, 100);
        }
    }
}

function detectGPSLocation() {
    const input = document.getElementById('locationSearch');
    const status = document.getElementById('locationStatus');
    if (!input || !status) return;

    status.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Detecting location...';

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;

                fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
                    .then(res => res.json())
                    .then(data => {
                        const displayName = data.display_name || "Unknown Location";
                        input.value = displayName;

                        document.getElementById('lat').value = lat;
                        document.getElementById('lng').value = lng;
                        status.textContent = `📍 Location auto-detected: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;

                        const mapWrapper = document.getElementById('mapWrapper');
                        if (mapWrapper) {
                            mapWrapper.style.display = 'block';
                            const mapEl = document.getElementById('workshopMap');

                            if (!map) {
                                map = L.map(mapEl).setView([lat, lng], 15);
                                L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
                                    attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
                                    subdomains: 'abcd',
                                    maxZoom: 20
                                }).addTo(map);
                            } else {
                                map.setView([lat, lng], 15);
                            }

                            if (marker) marker.remove();
                            marker = L.marker([lat, lng]).addTo(map);
                            setTimeout(() => { map.invalidateSize(); }, 100);
                        }
                    })
                    .catch(err => {
                        console.error('Reverse Geocoding error:', err);
                        status.textContent = "📍 Location detected, but reverse geocoding failed.";
                    });
            },
            (error) => {
                status.textContent = `📍 GPS Error: ${error.message}`;
            },
            { timeout: 10000, maximumAge: 0 }
        );
    } else {
        status.textContent = "📍 Geolocation is not supported by your browser.";
    }
}
