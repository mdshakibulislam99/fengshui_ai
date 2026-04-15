// Main JavaScript application file for handling UI interactions and API calls

let map = null;
let marker = null;
let circle = null;
let selectedLocation = null;
let drawingManager = null;
let currentPolygon = null;
let polygonEditor = null;
let defaultMarkerIcon = null;
let polygonVertexMarkers = [];
let apiBaseUrl = 'http://127.0.0.1:5001';
let selectionMode = 'location';
let latestReportPayload = null;
let latestAnalysisData = null;
const geocodeCache = new Map();
let isInputComposing = false;
let amapAutocompleteService = null;
let autocompleteInitPromise = null;
let suggestionDebounceTimer = null;
let suggestionRequestSeq = 0;
let suggestionItems = [];
let activeSuggestionIndex = -1;

// Track whether the user has explicitly requested an analysis.
// Error panels should only appear after analysis has been initiated.
let _analysisRequested = false;

// Progress bar animation timer for the loading state.
let _loadingTimerId = null;

function notifyLocationSelected(location) {
    window.dispatchEvent(new CustomEvent('qimatrix:location-selected', {
        detail: location || null
    }));
}

function setPreAnalysisLayout(isPreAnalysis) {
    const layout = document.querySelector('.ei-two-column-layout');
    if (layout) {
        layout.classList.toggle('pre-analysis-mode', Boolean(isPreAnalysis));
    }
}

function setAnalyzingLayout(isAnalyzing) {
    const layout = document.querySelector('.ei-two-column-layout');
    if (layout) {
        layout.classList.toggle('is-analyzing', Boolean(isAnalyzing));
    }
}

// Log JS errors to the console but do NOT show the analysis-error panel
// for errors that occur before the user clicks Analyze (e.g. AMap script
// loading, config fetch, map init). Only surface them as toasts if needed.
window.addEventListener('error', function(event) {
    console.error('Global error:', event.error);
    // Only propagate to the analysis panel if the user triggered an analysis
    if (_analysisRequested) {
        displayError(event.error?.message || 'An unexpected error occurred');
    }
});

window.addEventListener('unhandledrejection', function(event) {
    console.error('Unhandled promise rejection:', event.reason);
    if (_analysisRequested) {
        displayError(event.reason?.message || 'An unexpected error occurred');
    }
});

window.addEventListener('qilang:changed', function() {
    if (latestAnalysisData) {
        displayResults(latestAnalysisData);
    }
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeApp);
} else {
    initializeApp();
}

async function initializeApp() {
    try {
        console.log('Initializing Feng Shui Analysis System...');
        // Before analysis starts, keep the two-column layout centered.
        setPreAnalysisLayout(true);
        
        // Wait for AMap library to load
        console.log('Waiting for AMap library to load...');
        try {
            await window.amapReady;
            console.log('✅ AMap library is ready');
        } catch (error) {
            throw new Error(`AMap library failed to load: ${error.message}`);
        }
        
        // Double-check AMap is available
        if (typeof AMap === 'undefined') {
            throw new Error('AMap library not available after loading');
        }
        
        // Load configuration from backend
        const config = await loadConfiguration();
        apiBaseUrl = config.api_base_url;
        
        initMap(config.map_default_center, config.map_default_zoom);
        setupEventListeners();
        setupPolygonDrawing();
        console.log('✅ Feng Shui Analysis System initialized');
    } catch (error) {
        console.error('❌ Initialization error:', error);
        // Do NOT call displayError here — the user hasn't clicked Analyze yet.
        // The map will still load with the fallback AMap key; only show an
        // error panel if the user actually requests an analysis and it fails.
    }
}

async function loadConfiguration() {
    const LOCAL_URL  = 'http://127.0.0.1:5001';
    const REMOTE_URL = 'https://fengshui-ai.onrender.com';

    // Try local backend first (fast, 2s timeout).
    // Then remote. Return whichever responds first with valid config.
    const candidates = [LOCAL_URL, REMOTE_URL];

    for (const base of candidates) {
        try {
            const ctrl = new AbortController();
            const tid  = setTimeout(() => ctrl.abort(), base === LOCAL_URL ? 2000 : 8000);
            const response = await fetch(`${base}/api/config`, { signal: ctrl.signal });
            clearTimeout(tid);
            if (!response.ok) continue;
            const data = await response.json();
            if (!data.success) continue;
            // Use whichever backend responded
            data.data.api_base_url = base;
            console.log(`✅ Backend: ${base}`);
            return data.data;
        } catch (_) {
            // next candidate
        }
    }

    console.warn('No backend reachable, using defaults');
    return {
        api_base_url: REMOTE_URL,
        map_default_center: [116.397428, 39.90923],
        map_default_zoom: 13
    };
}

// Initialize AMap with error handling
function initMap(defaultCenter = [116.397428, 39.90923], defaultZoom = 13) {
    try {
        // Verify map container exists
        const container = document.getElementById('map-container');
        if (!container) {
            throw new Error('Map container not found in DOM');
        }
        
        // Verify container has dimensions
        const rect = container.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) {
            console.warn('Map container has zero dimensions, waiting 100ms...');
            setTimeout(() => initMap(defaultCenter, defaultZoom), 100);
            return;
        }
        
        if (map) {
            console.warn('Map already initialized, skipping');
            return;
        }
        
        // Satellite layer with retina support for sharper tiles.
        const satLayer = new AMap.TileLayer.Satellite({
            detectRetina: true
        });
        const roadLayer = new AMap.TileLayer.RoadNet({
            detectRetina: true
        });

        map = new AMap.Map('map-container', {
            zoom: defaultZoom,
            center: defaultCenter,
            viewMode: '2D',
            resizeEnable: true,
            layers: [satLayer, roadLayer]
        });

        // Add layer switcher control
        AMap.plugin(['AMap.MapType'], function() {
            try {
                const mapType = new AMap.MapType({
                    defaultType: 1,
                    showRoad: true
                });
                map.addControl(mapType);
            } catch (error) {
                console.warn('Failed to add MapType control:', error);
            }
        });

        // Add click event listener
        map.on('click', handleMapClick);
        
        // Add resize handling
        window.addEventListener('resize', () => {
            if (map) {
                map.resize();
            }
        });
        
        console.log('✅ Map initialized at', defaultCenter);
    } catch (error) {
        console.error('❌ Map initialization error:', error);
        throw error;
    }
}

// Setup polygon drawing system
function setupPolygonDrawing() {
    try {
        AMap.plugin(['AMap.MouseTool'], function() {
            drawingManager = new AMap.MouseTool(map);
            
            // Handle draw completion event
            drawingManager.on('draw', function(event) {
                const polygon = event.obj;
                if (polygon) {
                    if (currentPolygon && currentPolygon !== polygon) {
                        map.remove(currentPolygon);
                    }
                    currentPolygon = polygon;
                    console.log('✅ Polygon drawn:', polygon);
                    
                    // Extract coordinates from the drawn polygon
                    const path = polygon.getPath();
                    console.log('Polygon path:', path);
                    
                    // Validate polygon (needs at least 3 points)
                    if (path && path.length >= 3) {
                        syncPolygonVertexMarkersFromPath(path);

                        // Stop drawing mode
                        if (drawingManager) {
                            drawingManager.close();
                        }

                        // Enable polygon editing
                        enablePolygonEditing(polygon);
                        
                        // Show UI feedback
                        showPolygonMenu(path);
                        updateAnalyzeButtonState();
                    } else {
                        displayError('Polygon must have at least 3 points');
                        map.remove(polygon);
                        currentPolygon = null;
                        clearPolygonVertexMarkers();
                        disablePolygonEditing();
                    }
                }
            });
            
            // Handle draw end event
            drawingManager.on('drawend', function(event) {
                console.log('Draw mode ended');
            });
            
            // Handle draw abort
            drawingManager.on('unload', function() {
                console.log('Drawing tool unloaded');
                document.getElementById('polygonBtn').style.display = 'inline-block';
                document.getElementById('cancelPolygonBtn').style.display = 'none';
                if (selectionMode !== 'polygon') {
                    clearPolygonVertexMarkers();
                }
                updateAnalyzeButtonState();
            });
            
            console.log('✅ Polygon drawing initialized');
        });
    } catch (error) {
        console.warn('Polygon drawing not available:', error);
        displayError('Polygon drawing feature unavailable');
    }
}

function enablePolygonEditing(polygon) {
    disablePolygonEditing();

    if (!polygon) {
        return;
    }

    AMap.plugin(['AMap.PolygonEditor'], function() {
        polygonEditor = new AMap.PolygonEditor(map, polygon);
        polygonEditor.open();
    });
}

function disablePolygonEditing() {
    if (polygonEditor) {
        polygonEditor.close();
        polygonEditor = null;
    }
}

function getDefaultMarkerIcon() {
    if (defaultMarkerIcon) {
        return defaultMarkerIcon;
    }

    // High-contrast marker so it stands out over satellite imagery.
    const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="34" height="44" viewBox="0 0 34 44"><defs><filter id="shadow" x="-50%" y="-50%" width="200%" height="200%"><feDropShadow dx="0" dy="2" stdDeviation="2" flood-color="#000" flood-opacity="0.35"/></filter></defs><g filter="url(#shadow)"><path d="M17 1C8.2 1 1 8 1 16.7 1 28 15.4 41.2 16 41.8c.6.6 1.5.6 2.1 0 .6-.6 15-13.8 15-25.1C33 8 25.8 1 17 1z" fill="#ff4d2d" stroke="#ffffff" stroke-width="2"/><circle cx="17" cy="16.2" r="5.4" fill="#ffffff" stroke="#b3200c" stroke-width="1.2"/></g></svg>';
    defaultMarkerIcon = new AMap.Icon({
        image: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(svg),
        size: new AMap.Size(34, 44),
        imageSize: new AMap.Size(34, 44)
    });

    return defaultMarkerIcon;
}

// Handle map click events
async function handleMapClick(e) {
    try {
        if (selectionMode === 'polygon') {
            addPolygonVertexMarker(e.lnglat.getLng(), e.lnglat.getLat());
            return;
        }

        revealPostSearchSettings();
        setSelectionMode('location');

        const lng = e.lnglat.getLng();
        const lat = e.lnglat.getLat();
        
        console.log('Clicked location - Latitude:', lat, 'Longitude:', lng);
        
        // Store the selected location
        selectedLocation = { lat, lng, address: 'Loading address...' };
        
        // Display the selected location with coordinates first
        displaySelectedLocation(lat, lng, 'Loading address...');
        
        // Remove existing marker and circle if any
        if (marker) {
            map.remove(marker);
        }
        if (circle) {
            map.remove(circle);
        }
        
        // Reverse geocode to get address name
        try {
            const address = await reverseGeocodePoint(lng, lat);
            selectedLocation.address = address;
            displaySelectedLocation(lat, lng, address);
        } catch (error) {
            console.error('Reverse geocoding failed:', error);
            displaySelectedLocation(lat, lng, `${lat.toFixed(6)}, ${lng.toFixed(6)}`);
        }
        
        // Create new marker at clicked location
        marker = new AMap.Marker({
            position: [lng, lat],
            map: map,
            title: 'Selected Location',
            icon: getDefaultMarkerIcon(),
            anchor: 'bottom-center',
            offset: new AMap.Pixel(0, 0),
            zIndex: 150
        });
        
        // Get radius value from input
        const radius = parseInt(document.getElementById('radius').value) || 500;
        
        // Draw circle around the marker
        drawCircle(lng, lat, radius);
        
        updateAnalyzeButtonState();
    } catch (error) {
        console.error('Error handling map click:', error);
        displayError('Failed to process location click');
    }
}

// Draw a circular radius around the location
function drawCircle(lng, lat, radius) {
    circle = new AMap.Circle({
        center: [lng, lat],
        radius: radius, // in meters
        fillColor: '#5F7D6A',
        fillOpacity: 0.2,
        strokeColor: '#1F3D2B',
        strokeWeight: 2,
        strokeOpacity: 0.5,
        map: map
    });
    
    console.log(`Circle drawn with radius: ${radius} meters`);
}

// Update circle radius when input changes
function updateCircleRadius() {
    if (selectedLocation && circle) {
        const newRadius = parseInt(document.getElementById('radius').value) || 500;
        circle.setRadius(newRadius);
        
        // Update the displayed value
        const radiusValueSpan = document.getElementById('radiusValue');
        if (radiusValueSpan) {
            radiusValueSpan.textContent = newRadius;
        }
        
        // Update slider background gradient
        const slider = document.getElementById('radius');
        const percentage = ((newRadius - 100) / (5000 - 100)) * 100;
        slider.style.background = `linear-gradient(to right, #1F3D2B 0%, #1F3D2B ${percentage}%, #E3E6E4 ${percentage}%, #E3E6E4 100%)`;
        
        console.log(`Circle radius updated to: ${newRadius} meters`);
    }
}

function setSelectionMode(mode) {
    selectionMode = mode === 'polygon' ? 'polygon' : 'location';

    const locationModeBtn = document.getElementById('locationModeBtn');
    const polygonBtn = document.getElementById('polygonBtn');
    const radiusWrap = document.getElementById('radiusControlWrap');

    if (locationModeBtn) {
        locationModeBtn.classList.toggle('active', selectionMode === 'location');
    }
    if (polygonBtn) {
        polygonBtn.classList.toggle('active', selectionMode === 'polygon');
    }

    if (radiusWrap) {
        radiusWrap.classList.toggle('is-hidden', selectionMode === 'polygon');
    }

    if (selectionMode === 'polygon') {
        clearPolygonVertexMarkers();
        if (marker) {
            map.remove(marker);
            marker = null;
        }
        if (circle) {
            map.remove(circle);
            circle = null;
        }
        selectedLocation = null;
        notifyLocationSelected(null);
    } else if (selectionMode === 'location' && selectedLocation) {
        clearPolygonVertexMarkers();
        if (circle) {
            map.remove(circle);
            circle = null;
        }
        const radius = parseInt(document.getElementById('radius')?.value) || 500;
        drawCircle(selectedLocation.lng, selectedLocation.lat, radius);
    } else if (selectionMode === 'location') {
        clearPolygonVertexMarkers();
    }

    renderSelectedLocationDisplay();
    updateAnalyzeButtonState();
}

function revealPostSearchSettings() {
    const controlsGrid = document.querySelector('.controls-grid');
    if (controlsGrid && controlsGrid.classList.contains('search-only')) {
        controlsGrid.classList.remove('search-only');
    }
}

function getLocationPinIconHtml(iconClassName = 'selected-location-icon') {
    return `
        <span class="${iconClassName}" aria-hidden="true">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
                <path d="M12 22C12 22 19 16.4 19 10.8C19 6.49 15.87 3 12 3C8.13 3 5 6.49 5 10.8C5 16.4 12 22 12 22Z" fill="currentColor"/>
                <circle cx="12" cy="10" r="2.8" fill="white"/>
            </svg>
        </span>
    `;
}

function clearPolygonVertexMarkers() {
    if (!map) {
        polygonVertexMarkers = [];
        return;
    }

    if (polygonVertexMarkers.length > 0) {
        map.remove(polygonVertexMarkers);
        polygonVertexMarkers = [];
    }
}

function addPolygonVertexMarker(lng, lat) {
    const parsedLng = Number(lng);
    const parsedLat = Number(lat);
    if (!map || !Number.isFinite(parsedLng) || !Number.isFinite(parsedLat)) {
        return;
    }

    const vertexMarker = new AMap.Marker({
        position: [parsedLng, parsedLat],
        map: map,
        icon: getDefaultMarkerIcon(),
        anchor: 'bottom-center',
        offset: new AMap.Pixel(0, 0),
        zIndex: 120
    });

    polygonVertexMarkers.push(vertexMarker);
}

function syncPolygonVertexMarkersFromPath(path) {
    clearPolygonVertexMarkers();
    if (!Array.isArray(path) || path.length === 0) {
        return;
    }

    for (const point of path) {
        const lng = typeof point?.getLng === 'function' ? point.getLng() : (point?.lng ?? point?.[0]);
        const lat = typeof point?.getLat === 'function' ? point.getLat() : (point?.lat ?? point?.[1]);
        addPolygonVertexMarker(lng, lat);
    }
}

function getPolygonCentroid(path) {
    if (!Array.isArray(path) || path.length < 3) {
        return null;
    }

    let sumLat = 0;
    let sumLng = 0;
    let count = 0;

    for (const point of path) {
        let lat = null;
        let lng = null;

        if (point && typeof point.getLat === 'function' && typeof point.getLng === 'function') {
            lat = Number(point.getLat());
            lng = Number(point.getLng());
        } else if (point && typeof point.lat === 'number' && typeof point.lng === 'number') {
            lat = Number(point.lat);
            lng = Number(point.lng);
        } else if (Array.isArray(point) && point.length >= 2) {
            lng = Number(point[0]);
            lat = Number(point[1]);
        }

        if (Number.isFinite(lat) && Number.isFinite(lng)) {
            sumLat += lat;
            sumLng += lng;
            count += 1;
        }
    }

    if (count === 0) {
        return null;
    }

    return {
        lat: sumLat / count,
        lng: sumLng / count,
        count
    };
}

function renderSelectedLocationDisplay() {
    const displayDiv = document.getElementById('selectedLocationDisplay');
    if (!displayDiv) {
        return;
    }

    if (selectionMode === 'polygon' && currentPolygon) {
        const path = currentPolygon.getPath ? currentPolygon.getPath() : null;
        const centroid = getPolygonCentroid(path);
        const vertexCount = Array.isArray(path) ? path.length : (centroid?.count || 0);
        const coordsText = centroid
            ? `(${centroid.lat.toFixed(5)}, ${centroid.lng.toFixed(5)})`
            : '( -- , -- )';

        displayDiv.classList.remove('is-empty');
        displayDiv.innerHTML = `
            ${getLocationPinIconHtml()}
            <span class="location-text-block">
                <span class="location-name">Area selected (${vertexCount} points)</span>
                <span class="location-coords">${coordsText}</span>
            </span>
        `;
        return;
    }

    if (!selectedLocation || !Number.isFinite(Number(selectedLocation.lat)) || !Number.isFinite(Number(selectedLocation.lng))) {
        displayDiv.classList.add('is-empty');
        displayDiv.innerHTML = `
            ${getLocationPinIconHtml()}
            <span class="location-text-block">
                <span class="location-name">Select location</span>
                <span class="location-coords">( -- , -- )</span>
            </span>
        `;
        return;
    }

    displayDiv.classList.remove('is-empty');
    const addressText = selectedLocation.address || `${selectedLocation.lat.toFixed(6)}, ${selectedLocation.lng.toFixed(6)}`;
    const coordsText = `(${selectedLocation.lat.toFixed(5)}, ${selectedLocation.lng.toFixed(5)})`;

    displayDiv.innerHTML = `
        ${getLocationPinIconHtml()}
        <span class="location-text-block">
            <span class="location-name">${addressText}</span>
            <span class="location-coords">${coordsText}</span>
        </span>
    `;
}

// Setup event listeners
function setupEventListeners() {
    // Analyze button click
    document.getElementById('analyzeBtn').addEventListener('click', analyzeSelection);

    const locationInput = document.getElementById('locationInput');
    if (locationInput) {
        locationInput.addEventListener('compositionstart', function() {
            isInputComposing = true;
        });
        locationInput.addEventListener('compositionend', function() {
            isInputComposing = false;
        });
    }

    const searchForm = document.getElementById('locationSearchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            if (isInputComposing) {
                return;
            }

            if (activeSuggestionIndex >= 0 && suggestionItems[activeSuggestionIndex]) {
                const selected = suggestionItems[activeSuggestionIndex];
                applySuggestionSelection(selected, true);
                return;
            }

            searchLocation();
        });
    }

    const searchBtn = document.getElementById('searchBtn');
    if (searchBtn && !searchForm) {
        searchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            if (isInputComposing) {
                return;
            }
            searchLocation();
        });
    }
    
    // Polygon drawing button
    const polygonBtn = document.getElementById('polygonBtn');
    if (polygonBtn) {
        polygonBtn.addEventListener('click', startPolygonDrawing);
    }

    const locationModeBtn = document.getElementById('locationModeBtn');
    if (locationModeBtn) {
        locationModeBtn.addEventListener('click', function() {
            setSelectionMode('location');
        });
    }
    
    // Cancel polygon button
    const cancelPolygonBtn = document.getElementById('cancelPolygonBtn');
    if (cancelPolygonBtn) {
        cancelPolygonBtn.addEventListener('click', cancelPolygonDrawing);
    }
    
    // Radius slider input - real-time update
    document.getElementById('radius').addEventListener('input', function(e) {
        const value = parseInt(e.target.value);
        const radiusValueSpan = document.getElementById('radiusValue');
        if (radiusValueSpan) {
            radiusValueSpan.textContent = value;
        }
        
        // Update slider background gradient
        const percentage = ((value - 100) / (5000 - 100)) * 100;
        e.target.style.background = `linear-gradient(to right, #1F3D2B 0%, #1F3D2B ${percentage}%, #E3E6E4 ${percentage}%, #E3E6E4 100%)`;
        
        updateCircleRadius();
    });
    
    // Radius input change
    document.getElementById('radius').addEventListener('change', updateCircleRadius);
    
    // Live backend suggestions while typing.
    document.getElementById('locationInput').addEventListener('input', function(e) {
        const value = e.target.value;
        console.log('Search input:', value);
        handleSuggestionInput(value);
    });

    document.getElementById('locationInput').addEventListener('keydown', function(e) {
        if (isInputComposing || !suggestionItems.length) {
            return;
        }

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setActiveSuggestionIndex(Math.min(activeSuggestionIndex + 1, suggestionItems.length - 1));
            return;
        }

        if (e.key === 'ArrowUp') {
            e.preventDefault();
            setActiveSuggestionIndex(Math.max(activeSuggestionIndex - 1, 0));
            return;
        }

        if (e.key === 'Enter' && activeSuggestionIndex >= 0) {
            e.preventDefault();
            const selected = suggestionItems[activeSuggestionIndex];
            if (selected) {
                applySuggestionSelection(selected, true);
            }
            return;
        }

        if (e.key === 'Escape') {
            hideSuggestionPopup();
        }
    });

    document.addEventListener('click', function(event) {
        const inputEl = document.getElementById('locationInput');
        const popupEl = document.getElementById('searchSuggestions');
        const inInput = inputEl && inputEl.contains(event.target);
        const inPopup = popupEl && popupEl.contains(event.target);
        if (!inInput && !inPopup) {
            hideSuggestionPopup();
        }
    });

    setupLocationAutocomplete();
    setSelectionMode('location');
}

function setupLocationAutocomplete() {
    if (autocompleteInitPromise) {
        return autocompleteInitPromise;
    }

    autocompleteInitPromise = new Promise((resolve) => {
        if (typeof AMap === 'undefined') {
            resolve(null);
            return;
        }

        AMap.plugin(['AMap.Autocomplete'], function() {
            try {
                const AutoCompleteCtor = AMap.Autocomplete || AMap.AutoComplete;
                if (!AutoCompleteCtor) {
                    console.warn('AMap Autocomplete constructor not found');
                    resolve(null);
                    return;
                }

                amapAutocompleteService = new AutoCompleteCtor({
                    input: 'locationInput',
                    city: '全国',
                    citylimit: false
                });

                resolve(amapAutocompleteService);
            } catch (error) {
                console.warn('AutoComplete init failed:', error);
                resolve(null);
            }
        });
    });

    return autocompleteInitPromise;
}

function ensureSuggestionPopup() {
    let popupEl = document.getElementById('searchSuggestions');
    if (popupEl) {
        return popupEl;
    }

    const formEl = document.getElementById('locationSearchForm');
    if (!formEl || !formEl.parentElement) {
        return null;
    }

    popupEl = document.createElement('div');
    popupEl.id = 'searchSuggestions';
    popupEl.className = 'search-suggestions';
    popupEl.setAttribute('role', 'listbox');
    popupEl.hidden = true;
    formEl.parentElement.appendChild(popupEl);
    return popupEl;
}

function handleSuggestionInput(value) {
    if (suggestionDebounceTimer) {
        clearTimeout(suggestionDebounceTimer);
        suggestionDebounceTimer = null;
    }

    const keyword = (value || '').trim();
    if (!keyword || keyword.length < 1) {
        hideSuggestionPopup();
        return;
    }

    suggestionDebounceTimer = setTimeout(() => {
        fetchSuggestions(keyword);
    }, 160);
}

async function fetchSuggestions(keyword) {
    const requestId = ++suggestionRequestSeq;

    try {
        const response = await fetch(`${apiBaseUrl}/api/input-tips`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                keyword,
                limit: 5
            })
        });

        const payload = await response.json();
        if (requestId !== suggestionRequestSeq) {
            return;
        }

        if (!response.ok || !payload?.success) {
            hideSuggestionPopup();
            return;
        }

        const tips = Array.isArray(payload?.data?.tips) ? payload.data.tips : [];
        const parsed = tips
            .map((tip) => {
                const name = String(tip?.name || '').trim();
                const detail = String(tip?.display || '').trim();
                const lng = (tip?.longitude != null && Number.isFinite(Number(tip.longitude))) ? Number(tip.longitude) : null;
                const lat = (tip?.latitude != null && Number.isFinite(Number(tip.latitude))) ? Number(tip.latitude) : null;
                return {
                    searchText: name || keyword,
                    name: name || keyword,
                    detail,
                    lng,
                    lat
                };
            })
            .filter((item) => item.searchText)
            .slice(0, 5);

        renderSuggestionPopup(parsed);
    } catch (error) {
        if (requestId === suggestionRequestSeq) {
            hideSuggestionPopup();
        }
    }
}

function renderSuggestionPopup(items) {
    const popupEl = ensureSuggestionPopup();
    if (!popupEl) {
        return;
    }

    popupEl.innerHTML = '';
    suggestionItems = Array.isArray(items) ? items : [];
    activeSuggestionIndex = -1;

    if (!suggestionItems.length) {
        hideSuggestionPopup();
        return;
    }

    suggestionItems.forEach((item, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'search-suggestion-item';
        button.setAttribute('role', 'option');
        button.setAttribute('aria-selected', 'false');

        const title = document.createElement('span');
        title.className = 'suggestion-title';
        title.textContent = item.name;

        const detail = document.createElement('span');
        detail.className = 'suggestion-detail';
        detail.textContent = item.detail || 'Suggested place';

        button.appendChild(title);
        button.appendChild(detail);

        button.addEventListener('mouseenter', function() {
            setActiveSuggestionIndex(index);
        });

        button.addEventListener('click', function() {
            applySuggestionSelection(item, true);
        });

        popupEl.appendChild(button);
    });

    popupEl.hidden = false;
}

function setActiveSuggestionIndex(index) {
    const popupEl = ensureSuggestionPopup();
    if (!popupEl) {
        return;
    }

    const nodes = popupEl.querySelectorAll('.search-suggestion-item');
    if (!nodes.length) {
        activeSuggestionIndex = -1;
        return;
    }

    const nextIndex = Math.max(0, Math.min(index, nodes.length - 1));
    activeSuggestionIndex = nextIndex;

    nodes.forEach((node, nodeIndex) => {
        const isActive = nodeIndex === nextIndex;
        node.classList.toggle('active', isActive);
        node.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    const activeNode = nodes[nextIndex];
    if (activeNode) {
        activeNode.scrollIntoView({ block: 'nearest' });
    }
}

function applySuggestionSelection(item, runSearch = false) {
    const inputEl = document.getElementById('locationInput');
    if (!inputEl || !item?.searchText) {
        return;
    }

    inputEl.value = item.searchText;
    hideSuggestionPopup();

    if (runSearch) {
        // Always go through searchLocation which uses PlaceSearch for precise
        // POI coordinates.  Input-tips coordinates can be approximate
        // (district center rather than exact POI entrance).
        searchLocation(item.searchText);
    }
}

function hideSuggestionPopup() {
    const popupEl = document.getElementById('searchSuggestions');
    if (!popupEl) {
        return;
    }

    popupEl.hidden = true;
    popupEl.innerHTML = '';
    suggestionItems = [];
    activeSuggestionIndex = -1;
}

function updateAnalyzeButtonState() {
    const analyzeBtn = document.getElementById('analyzeBtn');
    if (!analyzeBtn) {
        return;
    }
    if (selectionMode === 'polygon') {
        analyzeBtn.disabled = !currentPolygon;
        analyzeBtn.textContent = 'Analyze Area';
    } else {
        analyzeBtn.disabled = !selectedLocation;
        analyzeBtn.textContent = 'Analyze Location';
    }
}

// Display selected location with address
function displaySelectedLocation(lat, lng, address = null) {
    selectedLocation = {
        lat,
        lng,
        address: address || `${lat.toFixed(6)}, ${lng.toFixed(6)}`
    };

    notifyLocationSelected(selectedLocation);

    renderSelectedLocationDisplay();
}

// Reverse geocode coordinates using backend
async function reverseGeocodePoint(lng, lat) {
    try {
        const response = await fetch(`${apiBaseUrl}/api/reverse-geocode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ latitude: lat, longitude: lng })
        });
        
        const data = await response.json();
        
        if (data.success && data.data) {
            return data.data.formatted_address || `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
        } else {
            console.warn('Reverse geocoding returned no result:', data.error);
            return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
        }
    } catch (error) {
        console.error('Error in reverse geocoding:', error);
        return `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }
}

// Legacy function for compatibility
async function getAddressFromCoordinates(lng, lat) {
    return reverseGeocodePoint(lng, lat);
}

function setSearchButtonState(isLoading) {
    const searchBtn = document.getElementById('searchBtn');
    if (!searchBtn) return;

    if (isLoading) {
        searchBtn.disabled = true;
        searchBtn.innerHTML = '<span aria-hidden="true">⏳</span> Searching...';
    } else {
        searchBtn.disabled = false;
        searchBtn.innerHTML = '<span aria-hidden="true">🔍</span> Search';
    }
}

function setSearchStatus(message = '', type = 'info') {
    const statusEl = document.getElementById('searchStatus');
    if (!statusEl) {
        return;
    }

    statusEl.textContent = message;
    statusEl.classList.remove('success', 'error');
    if (type === 'success') {
        statusEl.classList.add('success');
    } else if (type === 'error') {
        statusEl.classList.add('error');
    }
}

function parseCoordinateInput(query) {
    const match = query.match(/^\s*(-?\d+(?:\.\d+)?)\s*[,\s]+\s*(-?\d+(?:\.\d+)?)\s*$/);
    if (!match) {
        return null;
    }

    const first = Number(match[1]);
    const second = Number(match[2]);
    if (!Number.isFinite(first) || !Number.isFinite(second)) {
        return null;
    }

    let lat = first;
    let lng = second;
    if (Math.abs(first) > 90 && Math.abs(second) <= 90) {
        lng = first;
        lat = second;
    }

    if (Math.abs(lat) > 90 || Math.abs(lng) > 180) {
        return null;
    }

    return { lng, lat };
}

async function geocodeViaBackend(address) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    try {
        const response = await fetch(`${apiBaseUrl}/api/geocode`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ address }),
            signal: controller.signal
        });

        const payload = await response.json();
        if (!response.ok || !payload?.success || !payload?.data) {
            throw new Error(payload?.error || 'Backend geocoding failed');
        }

        const lng = Number(payload.data.longitude);
        const lat = Number(payload.data.latitude);
        if (!Number.isFinite(lng) || !Number.isFinite(lat)) {
            throw new Error('Backend returned invalid coordinates');
        }

        return {
            lng,
            lat,
            address: payload.data.formatted_address || address
        };
    } catch (error) {
        if (error?.name === 'AbortError') {
            throw new Error('Backend geocoding timed out');
        }
        throw error;
    } finally {
        clearTimeout(timeoutId);
    }
}

async function geocodeViaAmap(query) {
    if (typeof AMap === 'undefined') {
        throw new Error('Map search service unavailable');
    }

    return await new Promise((resolve, reject) => {
        let finished = false;
        const finishResolve = (value) => {
            if (finished) return;
            finished = true;
            clearTimeout(globalTimeout);
            resolve(value);
        };
        const finishReject = (error) => {
            if (finished) return;
            finished = true;
            clearTimeout(globalTimeout);
            reject(error);
        };

        const globalTimeout = setTimeout(() => {
            finishReject(new Error('Map geocoding timed out'));
        }, 4000);

        AMap.plugin(['AMap.PlaceSearch', 'AMap.Geocoder'], function() {
            try {
                // PlaceSearch first — returns the exact POI location for named
                // places (universities, malls, hospitals, etc.).
                const placeSearch = new AMap.PlaceSearch({
                    pageSize: 1,
                    pageIndex: 1,
                    city: '全国',
                    citylimit: false
                });

                placeSearch.search(query, function(psStatus, psResult) {
                    if (finished) return;
                    const poi = psResult?.poiList?.pois?.[0];
                    if (psStatus === 'complete' && poi?.location) {
                        finishResolve({
                            lng: Number(poi.location.lng),
                            lat: Number(poi.location.lat),
                            address: poi.name || query
                        });
                    } else {
                        // Fall back to Geocoder for street addresses
                        const geocoder = new AMap.Geocoder({ city: '全国', radius: 50000 });
                        geocoder.getLocation(query, function(status, result) {
                            if (finished) return;
                            if (status === 'complete' && result?.info === 'OK' && result?.geocodes?.length) {
                                const firstResult = result.geocodes[0];
                                finishResolve({
                                    lng: Number(firstResult.location.lng),
                                    lat: Number(firstResult.location.lat),
                                    address: firstResult.formattedAddress || query
                                });
                            } else {
                                finishReject(new Error('Location not found'));
                            }
                        });
                    }
                });
            } catch (error) {
                finishReject(error);
            }
        });
    });
}

async function geocodeViaOpenStreetMap(query) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3500);

    try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(query)}`;
        const response = await fetch(url, {
            signal: controller.signal,
            headers: {
                Accept: 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('OpenStreetMap geocoding failed');
        }

        const items = await response.json();
        const first = Array.isArray(items) ? items[0] : null;
        if (!first) {
            throw new Error('OpenStreetMap location not found');
        }

        const lat = Number(first.lat);
        const lng = Number(first.lon);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
            throw new Error('OpenStreetMap returned invalid coordinates');
        }

        return {
            lng,
            lat,
            address: first.display_name || query
        };
    } catch (error) {
        if (error?.name === 'AbortError') {
            throw new Error('OpenStreetMap geocoding timed out');
        }
        throw error;
    } finally {
        clearTimeout(timeoutId);
    }
}

function geocodeViaKnownLocations(query) {
    const normalized = query.trim().toLowerCase();
    const knownLocations = {
        // Only broad city-level locations. Specific places (universities, etc.)
        // should go through AMap PlaceSearch for precise POI coordinates.
        nanjing: { lng: 118.7969, lat: 32.0603, address: 'Nanjing, Jiangsu, China' },
        南京: { lng: 118.7969, lat: 32.0603, address: 'Nanjing, Jiangsu, China' },
        beijing: { lng: 116.4074, lat: 39.9042, address: 'Beijing, China' },
        北京: { lng: 116.4074, lat: 39.9042, address: 'Beijing, China' },
        shanghai: { lng: 121.4737, lat: 31.2304, address: 'Shanghai, China' },
        上海: { lng: 121.4737, lat: 31.2304, address: 'Shanghai, China' },
        guangzhou: { lng: 113.2644, lat: 23.1291, address: 'Guangzhou, China' },
        广州: { lng: 113.2644, lat: 23.1291, address: 'Guangzhou, China' },
        shenzhen: { lng: 114.0579, lat: 22.5431, address: 'Shenzhen, Guangdong, China' },
        深圳: { lng: 114.0579, lat: 22.5431, address: 'Shenzhen, Guangdong, China' },
        hangzhou: { lng: 120.1551, lat: 30.2741, address: 'Hangzhou, Zhejiang, China' },
        杭州: { lng: 120.1551, lat: 30.2741, address: 'Hangzhou, Zhejiang, China' },
        chengdu: { lng: 104.0665, lat: 30.5728, address: 'Chengdu, Sichuan, China' },
        成都: { lng: 104.0665, lat: 30.5728, address: 'Chengdu, Sichuan, China' },
        wuhan: { lng: 114.3054, lat: 30.5931, address: 'Wuhan, Hubei, China' },
        武汉: { lng: 114.3054, lat: 30.5931, address: 'Wuhan, Hubei, China' },
        xian: { lng: 108.9398, lat: 34.3416, address: "Xi'an, Shaanxi, China" },
        "xi'an": { lng: 108.9398, lat: 34.3416, address: "Xi'an, Shaanxi, China" },
        西安: { lng: 108.9398, lat: 34.3416, address: "Xi'an, Shaanxi, China" }
    };

    if (knownLocations[normalized]) {
        return knownLocations[normalized];
    }

    return null;
}

function containsCJK(text) {
    return /[\u3400-\u9FFF\uF900-\uFAFF]/.test(String(text || ''));
}

function preferUserQueryAddress(query, providerAddress) {
    if (containsCJK(query) && !containsCJK(providerAddress)) {
        return query;
    }
    return providerAddress || query;
}

async function firstSuccessfulGeocode(providers) {
    const errors = [];

    return await new Promise((resolve, reject) => {
        let done = false;
        let pending = providers.length;

        const onSuccess = (result) => {
            if (done) return;
            done = true;
            resolve(result);
        };

        const onFailure = (label, error) => {
            if (done) return;
            errors.push(`${label}: ${error?.message || String(error)}`);
            pending -= 1;
            if (pending <= 0) {
                reject(new Error(errors.join(' | ')));
            }
        };

        providers.forEach(({ label, run }) => {
            Promise.resolve()
                .then(run)
                .then(onSuccess)
                .catch((error) => onFailure(label, error));
        });
    });
}

// Search for location by address or place name
async function searchLocation(inputQuery = null) {
    const query = (inputQuery || document.getElementById('locationInput').value).trim();
    const queryKey = query.toLowerCase();

    if (!query) {
        setSearchStatus('Please enter a location to search.', 'error');
        return;
    }

    if (!map) {
        setSearchStatus('Map is not ready yet. Please wait a moment and try again.', 'error');
        return;
    }

    setSearchButtonState(true);
    setSearchStatus('Searching location...', 'info');
    const failures = [];

    try {
        const cached = geocodeCache.get(queryKey);
        if (cached) {
            revealPostSearchSettings();
            setSelectionMode('location');
            applyLocationToMap(cached.lng, cached.lat, cached.address || query);
            return;
        }

        const coordinateInput = parseCoordinateInput(query);
        if (coordinateInput) {
            revealPostSearchSettings();
            setSelectionMode('location');
            applyLocationToMap(coordinateInput.lng, coordinateInput.lat, query);
            geocodeCache.set(queryKey, {
                lng: coordinateInput.lng,
                lat: coordinateInput.lat,
                address: query
            });
            setSearchStatus('Location found by coordinates.', 'success');
            return;
        }

        const knownLocation = geocodeViaKnownLocations(query);
        if (knownLocation) {
            revealPostSearchSettings();
            setSelectionMode('location');
            const resolvedAddress = preferUserQueryAddress(query, knownLocation.address);
            applyLocationToMap(knownLocation.lng, knownLocation.lat, resolvedAddress);
            geocodeCache.set(queryKey, {
                ...knownLocation,
                address: resolvedAddress
            });
            setSearchStatus('Location found (known city match).', 'success');
            return;
        }

        // AMap JS PlaceSearch first (works purely in frontend, precise POI coords).
        // Backend and OSM as fallbacks.
        try {
            const amapResult = await geocodeViaAmap(query);
            revealPostSearchSettings();
            setSelectionMode('location');
            const resolvedAddress = preferUserQueryAddress(query, amapResult.address);
            applyLocationToMap(amapResult.lng, amapResult.lat, resolvedAddress);
            geocodeCache.set(queryKey, {
                ...amapResult,
                address: resolvedAddress
            });
            setSearchStatus('Location found.', 'success');
            return;
        } catch (amapError) {
            failures.push(`AMap: ${amapError.message}`);
            console.warn('AMap JS geocode failed, trying backend:', amapError.message);
        }

        try {
            const backendResult = await geocodeViaBackend(query);
            revealPostSearchSettings();
            setSelectionMode('location');
            const resolvedAddress = preferUserQueryAddress(query, backendResult.address);
            applyLocationToMap(backendResult.lng, backendResult.lat, resolvedAddress);
            geocodeCache.set(queryKey, {
                ...backendResult,
                address: resolvedAddress
            });
            setSearchStatus('Location found.', 'success');
            return;
        } catch (backendError) {
            failures.push(`Backend: ${backendError.message}`);
            console.warn('Backend geocode failed, trying OpenStreetMap:', backendError.message);
        }

        try {
            const osmResult = await geocodeViaOpenStreetMap(query);
            revealPostSearchSettings();
            setSelectionMode('location');
            const resolvedAddress = preferUserQueryAddress(query, osmResult.address);
            applyLocationToMap(osmResult.lng, osmResult.lat, resolvedAddress);
            geocodeCache.set(queryKey, {
                ...osmResult,
                address: resolvedAddress
            });
            setSearchStatus('Location found.', 'success');
            return;
        } catch (osmError) {
            failures.push(`OpenStreetMap: ${osmError.message}`);
            console.warn('OpenStreetMap geocode failed:', osmError.message);
        }

        throw new Error(`Location not found. ${failures.join(' | ')}`);
    } catch (error) {
        console.error('Search failed:', error);
        setSearchStatus(error.message || 'Location not found. Please try a different search term.', 'error');
    } finally {
        setSearchButtonState(false);
    }
}

// Apply location to map (helper function for searchLocation)
function applyLocationToMap(lng, lat, address) {
    console.log('📍 Applying location to map:', lng, lat, address);
    
    if (!map) {
        console.error('Map not initialized');
        return;
    }

    const parsedLng = parseFloat(lng);
    const parsedLat = parseFloat(lat);
    
    if (isNaN(parsedLng) || isNaN(parsedLat)) {
        console.error('Invalid coordinates:', lng, lat);
        return;
    }

    selectedLocation = {
        lat: parsedLat,
        lng: parsedLng,
        address: address || `${parsedLat}, ${parsedLng}`
    };

    notifyLocationSelected(selectedLocation);

    // Remove existing marker and circle
    if (marker) {
        map.remove(marker);
        marker = null;
    }
    if (circle) {
        map.remove(circle);
        circle = null;
    }

    // Set map center and zoom
    map.setZoomAndCenter(15, [parsedLng, parsedLat]);
    console.log('Map centered at:', parsedLng, parsedLat);

    // Add new marker
    marker = new AMap.Marker({
        position: [parsedLng, parsedLat],
        map: map,
        title: address,
        icon: getDefaultMarkerIcon(),
        anchor: 'bottom-center',
        offset: new AMap.Pixel(0, 0),
        zIndex: 150
    });
    console.log('Marker added');

    // Draw circle
    const radius = parseInt(document.getElementById('radius')?.value) || 500;
    drawCircle(parsedLng, parsedLat, radius);

    // Update UI
    renderSelectedLocationDisplay();
    updateAnalyzeButtonState();

    console.log('✅ Location applied successfully');
}

// Send selected data to backend API
async function analyzeSelection() {
    // Mark that the user has explicitly requested analysis — from this point
    // onward, errors should be surfaced in the analysis panel.
    _analysisRequested = true;
    try {
        if (selectionMode === 'polygon') {
            if (!currentPolygon) {
                alert('Please draw an area first!');
                return;
            }
        } else {
            if (!selectedLocation) {
                alert('Please select a location first!');
                return;
            }
        }

        // FORCE FRESH DATA: Clear localStorage cache and request fresh analysis from backend
        localStorage.removeItem('latestAnalysisResult');
        localStorage.removeItem('analysisCache');
        sessionStorage.clear();

        displayLoading();

        let locationData = null;
        let polygonData = null;
        let errors = [];

        if (selectionMode === 'location' && selectedLocation) {
            try {
                locationData = await fetchLocationAnalysis();
            } catch (error) {
                errors.push('Location analysis failed: ' + error.message);
            }
        }

        if (selectionMode === 'polygon' && currentPolygon) {
            try {
                polygonData = await fetchPolygonAnalysis();
            } catch (error) {
                errors.push('Polygon analysis failed: ' + error.message);
            }
        }

        if (!locationData && !polygonData) {
            displayError(errors[0] || 'Analysis failed');
            return;
        }

        if (locationData) {
            displayResults(locationData);
            if (polygonData) {
                const dashboard = document.getElementById('dashboard');
                dashboard.insertAdjacentHTML('beforeend', getPolygonResultsHTML(polygonData));
            }
        } else {
            displayPolygonResults(polygonData);
        }
    } catch (error) {
        console.error('Error analyzing selection:', error);
        displayError(error.message);
    }
}

async function fetchLocationAnalysis() {
    if (!selectedLocation) {
        throw new Error('No location selected');
    }

    const selectedSnapshot = {
        lat: Number(selectedLocation.lat),
        lng: Number(selectedLocation.lng),
        address: String(selectedLocation.address || '').trim()
    };

    if (!Number.isFinite(selectedSnapshot.lat) || !Number.isFinite(selectedSnapshot.lng)) {
        throw new Error('Selected location coordinates are invalid');
    }

    const radius = parseInt(document.getElementById('radius').value) || 500;

    if (radius < 1 || radius > 5000) {
        throw new Error('Radius must be between 1 and 5000 meters');
    }

    const requestData = {
        latitude: selectedSnapshot.lat,
        longitude: selectedSnapshot.lng,
        address: selectedSnapshot.address || undefined,
        radius: radius,
        refresh_cache: true  // Always request fresh data from backend
    };

    console.log('🚀 Analyzing location:', requestData);

    // Add cache-busting timestamp to force fresh backend response
    const cacheBreaker = `_t=${Date.now()}`;
    
    const response = await fetch(`${apiBaseUrl}/api/analyze?${cacheBreaker}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        },
        body: JSON.stringify(requestData),
        timeout: 30000
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Response from backend:', data);

    if (!data.success) {
        throw new Error(data.error || 'Analysis failed');
    }

    if (data.data && typeof data.data === 'object') {
        data.data.requested_location = {
            latitude: selectedSnapshot.lat,
            longitude: selectedSnapshot.lng,
            radius: radius,
            address: selectedSnapshot.address
        };
    }

    return data.data;
}

async function fetchPolygonAnalysis() {
    if (!currentPolygon) {
        throw new Error('No polygon to analyze');
    }

    const path = currentPolygon.getPath();
    if (!path || path.length < 3) {
        throw new Error('Polygon must have at least 3 vertices');
    }

    const coordinates = path.map(point => [
        point.getLng(),
        point.getLat()
    ]);

    console.log('🚀 Submitting polygon analysis:', coordinates);

    // Add cache-busting timestamp to force fresh backend response
    const cacheBreaker = `_t=${Date.now()}`;
    
    const response = await fetch(`${apiBaseUrl}/api/polygon-analysis?${cacheBreaker}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache'
        },
        body: JSON.stringify({
            coordinates: coordinates
        }),
        timeout: 30000
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log('Response from backend:', data);

    if (!data.success) {
        throw new Error(data.error || 'Polygon analysis failed');
    }

    return data.data;
}

// Display loading state with an animated progress bar.
function displayLoading() {
    _stopLoadingProgress(); // clear any previous timer
    // Once analysis starts, switch to normal top-aligned layout.
    setPreAnalysisLayout(false);
    // During analysis, hide the pre-analysis summary block.
    setAnalyzingLayout(true);

    const dashboard   = document.getElementById('dashboard');
    const aiPanel     = document.getElementById('aiPanelMount');

    dashboard.classList.remove('hidden-state');
    dashboard.classList.add('loading-screen');
    // Keep AI panel hidden while loading so only the analysis loader is visible.
    if (aiPanel) aiPanel.classList.add('hidden-state');

    dashboard.innerHTML = `
        <div class="loading">
            <div class="loading-icon analysis-fixed-icon" aria-hidden="true">
                <svg viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="10" y="11" width="28" height="34" rx="6" stroke="currentColor" stroke-width="2.4" opacity="0.55"/>
                    <path d="M16 22H30" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity="0.7"/>
                    <path d="M16 28H24" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity="0.7"/>
                    <path d="M16 34H21" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" opacity="0.7"/>
                    <path d="M26 35V30" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
                    <path d="M30 35V26" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
                    <path d="M34 35V22" stroke="currentColor" stroke-width="2.6" stroke-linecap="round"/>
                    <circle cx="39" cy="39" r="7" stroke="currentColor" stroke-width="2.6"/>
                    <path d="M44 44L49 49" stroke="currentColor" stroke-width="2.8" stroke-linecap="round"/>
                </svg>
            </div>
            <h3>Analyzing Environmental Conditions...</h3>
            <p>Computing spatial balance, circulation, and element distribution.</p>
            <div class="loading-progress-wrap">
                <div class="loading-stage-label" id="loadingStageLabel">Initializing analysis...</div>
                <div class="loading-bar-track">
                    <div class="loading-bar-fill" id="loadingBarFill" style="width:0%"></div>
                </div>
                <div class="loading-pct" id="loadingPct">0%</div>
            </div>
        </div>
    `;

    if (aiPanel) {
        aiPanel.innerHTML = `
            <h3>AI Interpretation Panel</h3>
            <p>Analysis is running. Structured findings will appear here in a moment.</p>
        `;
    }

    // Stages: each defines the target % and the label shown while reaching it.
    const stages = [
        { pct: 12, label: 'Initializing analysis...' },
        { pct: 28, label: 'Fetching terrain & elevation data...' },
        { pct: 46, label: 'Computing wind patterns...' },
        { pct: 61, label: 'Analyzing water & flood risk...' },
        { pct: 75, label: 'Processing building density...' },
        { pct: 87, label: 'Calculating Qi energy flow...' },
        { pct: 95, label: 'Generating Feng Shui score...' },
    ];

    let stageIdx  = 0;
    let currentPct = 0;

    _loadingTimerId = setInterval(() => {
        const fill  = document.getElementById('loadingBarFill');
        const pctEl = document.getElementById('loadingPct');
        const lblEl = document.getElementById('loadingStageLabel');

        if (!fill) { clearInterval(_loadingTimerId); _loadingTimerId = null; return; }

        const target = stages[stageIdx] ? stages[stageIdx].pct : 95;

        if (currentPct < target) {
            currentPct = Math.min(currentPct + 1, target);
            const label = stages[stageIdx] ? stages[stageIdx].label : '';
            fill.style.width  = currentPct + '%';
            pctEl.textContent = currentPct + '%';
            if (lblEl)  lblEl.textContent  = label;
        } else if (stageIdx < stages.length - 1) {
            stageIdx++; // advance to next stage
        }
        // Holds at 95 % until the real response arrives.
    }, 45);
}

// Stop the progress animation. Pass complete=true to snap to 100% briefly.
function _stopLoadingProgress(complete) {
    if (_loadingTimerId) {
        clearInterval(_loadingTimerId);
        _loadingTimerId = null;
    }
    if (complete) {
        const fill  = document.getElementById('loadingBarFill');
        const pctEl = document.getElementById('loadingPct');
        const lblEl = document.getElementById('loadingStageLabel');
        if (fill)  fill.style.width  = '100%';
        if (pctEl) pctEl.textContent = '100%';
        if (lblEl) lblEl.textContent = 'Complete!';
    }
}

// Display error message
function displayError(message) {
    _stopLoadingProgress();
    setAnalyzingLayout(false);

    const dashboard = document.getElementById('dashboard');
    const aiPanel = document.getElementById('aiPanelMount');
    dashboard.classList.remove('loading-screen');

    // Remove hidden state to show sections
    dashboard.classList.remove('hidden-state');
    if (aiPanel) aiPanel.classList.remove('hidden-state');

    dashboard.innerHTML = `
        <div class="error">
            <h3>Analysis Error</h3>
            <p>${message}</p>
            <p>Confirm the backend service is available, then retry.</p>
        </div>
    `;

    if (aiPanel) {
        aiPanel.innerHTML = `
            <h3>AI Interpretation Panel</h3>
            <p>Interpretation is unavailable because the analysis request failed.</p>
        `;
    }
}

function splitFindings(sourceList, fallbackPrefix) {
    if (!Array.isArray(sourceList) || sourceList.length === 0) {
        return [`${fallbackPrefix} measurements are within normal range.`];
    }

    return sourceList
        .filter(Boolean)
        .slice(0, 3)
        .map(item => String(item));
}

function findLowestCategories(categoryScores, limit = 3) {
    return Object.entries(categoryScores || {})
        .filter(([name]) => !['yin_yang_balance', 'five_elements_harmony', 'qi_flow'].includes(name))
        .sort(([, a], [, b]) => a - b)
        .slice(0, limit)
        .map(([name, value]) => tRuntime(
            `${formatCategoryName(name)} is under target (${Math.round(value)}/100).`,
            `${formatCategoryName(name)} 低于目标（${Math.round(value)}/100）。`
        ));
}

function getElementProfile(fiveElements) {
    const profile = {
        Wood: Number(fiveElements.wood || 0),
        Fire: Number(fiveElements.fire || 0),
        Earth: Number(fiveElements.earth || 0),
        Metal: Number(fiveElements.metal || 0),
        Water: Number(fiveElements.water || 0)
    };

    const sorted = Object.entries(profile).sort(([, a], [, b]) => b - a);
    return {
        strongest: sorted[0] || ['Wood', 0],
        weakest: sorted[sorted.length - 1] || ['Water', 0],
        values: profile
    };
}

function localizeElementName(name) {
    const map = {
        Wood: tRuntime('Wood', '木'),
        Fire: tRuntime('Fire', '火'),
        Earth: tRuntime('Earth', '土'),
        Metal: tRuntime('Metal', '金'),
        Water: tRuntime('Water', '水')
    };

    return map[name] || name;
}

function getStatusText(score) {
    if (score >= 80) return tRuntime('Excellent', '优秀');
    if (score >= 60) return tRuntime('Balanced', '平衡');
    return tRuntime('Needs Improvement', '需改善');
}

const SCORE_GRADES = [
    { min: 0, range: { en: 'Below 50', zh: '50以下' }, description: { en: 'Poor', zh: '较差' }, color: '#eab308' },
    { min: 50, range: { en: '50 – 59', zh: '50 – 59' }, description: { en: 'Weak', zh: '偏弱' }, color: '#eab308' },
    { min: 60, range: { en: '60 – 69', zh: '60 – 69' }, description: { en: 'Moderate', zh: '中等' }, color: '#f59e0b' },
    { min: 70, range: { en: '70 – 79', zh: '70 – 79' }, description: { en: 'Good', zh: '良好' }, color: '#10b981' },
    { min: 80, range: { en: '80 – 89', zh: '80 – 89' }, description: { en: 'Very Good', zh: '很好' }, color: '#10b981' },
    { min: 90, range: { en: '90 – 100', zh: '90 – 100' }, description: { en: 'Excellent', zh: '优秀' }, color: '#059669' }
];

function getUiLang() {
    return window.QiLang?.currentLang === 'zh' ? 'zh' : 'en';
}

function tRuntime(enText, zhText) {
    return getUiLang() === 'zh' ? zhText : enText;
}

function getGradeForScore(score) {
    const numericScore = Number(score);
    const safeScore = Number.isFinite(numericScore) ? numericScore : 0;

    for (let i = SCORE_GRADES.length - 1; i >= 0; i--) {
        if (safeScore >= SCORE_GRADES[i].min) {
            return SCORE_GRADES[i];
        }
    }

    return SCORE_GRADES[0];
}

function getStatusColor(score) {
    return getGradeForScore(score).color;
}

function getScoreTextColor(score) {
    return getStatusColor(score);
}

function getScoreRange(score) {
    const grade = getGradeForScore(score);
    const lang = getUiLang();
    return {
        range: grade.range?.[lang] || grade.range?.en || '',
        description: grade.description?.[lang] || grade.description?.en || ''
    };
}

function getScoreHealthLabel(score) {
    const grade = getScoreRange(score);
    return grade.description;
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function firstFiniteNumber(...candidates) {
    for (const candidate of candidates) {
        const parsed = Number(candidate);
        if (Number.isFinite(parsed)) {
            return parsed;
        }
    }
    return null;
}

function isDisplayableLocationLabel(value) {
    const text = String(value || '').trim();
    if (!text) {
        return false;
    }
    return text.toLowerCase() !== 'loading address...';
}

function formatCoordinatePair(latitude, longitude, precision = 5) {
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        return '( -- , -- )';
    }
    return `(${latitude.toFixed(precision)}, ${longitude.toFixed(precision)})`;
}

function getAnalyzedLocationDetails(data, fallbackRadius = null) {
    const requestedLocation = data?.requested_location || {};
    const backendLocation = data?.location || {};

    const latitude = firstFiniteNumber(
        requestedLocation.latitude,
        backendLocation.latitude,
        selectedLocation?.lat
    );
    const longitude = firstFiniteNumber(
        requestedLocation.longitude,
        backendLocation.longitude,
        selectedLocation?.lng
    );
    const radius = firstFiniteNumber(
        requestedLocation.radius,
        backendLocation.radius,
        fallbackRadius
    );

    const labelCandidates = [
        requestedLocation.address,
        backendLocation.address,
        selectedLocation?.address
    ];

    const labelFromAddress = labelCandidates.find(isDisplayableLocationLabel) || '';
    const fallbackLabel = Number.isFinite(latitude) && Number.isFinite(longitude)
        ? `${latitude.toFixed(6)}, ${longitude.toFixed(6)}`
        : tRuntime('Selected analysis location', '已选择分析位置');

    return {
        label: labelFromAddress || fallbackLabel,
        latitude,
        longitude,
        radius,
        coordinatesText: formatCoordinatePair(latitude, longitude)
    };
}

function averageScores(values) {
    const clean = values.map(Number).filter(Number.isFinite);
    if (!clean.length) {
        return 0;
    }

    return clean.reduce((acc, value) => acc + value, 0) / clean.length;
}

function normalizeFiveElements(data, categoryScores) {
    const topLevel = (data && typeof data.five_elements === 'object' && data.five_elements) || {};
    const categoryLevel = (categoryScores && typeof categoryScores.five_elements === 'object' && categoryScores.five_elements) || {};
    const source = Object.keys(topLevel).length ? topLevel : categoryLevel;

    return {
        wood: Number(firstFiniteNumber(source.wood, 0) || 0),
        fire: Number(firstFiniteNumber(source.fire, 0) || 0),
        earth: Number(firstFiniteNumber(source.earth, 0) || 0),
        metal: Number(firstFiniteNumber(source.metal, 0) || 0),
        water: Number(firstFiniteNumber(source.water, 0) || 0),
        overall_score: Number(
            firstFiniteNumber(
                source.overall_score,
                source.overall_harmony,
                categoryScores?.five_elements_harmony,
                0
            ) || 0
        )
    };
}

function normalizeCategoryEntries(categoryScores, fallbackFiveElementsOverall = 0) {
    return Object.entries(categoryScores || {}).flatMap(([name, value]) => {
        if (name === 'five_elements') {
            if (value && typeof value === 'object') {
                const overall = firstFiniteNumber(
                    value.overall_harmony,
                    value.overall_score,
                    fallbackFiveElementsOverall,
                    0
                );
                return [['five_elements', Number(overall || 0)]];
            }
            const parsed = Number(value);
            return Number.isFinite(parsed) ? [['five_elements', parsed]] : [];
        }

        if (name === 'five_elements_harmony') {
            const parsed = Number(value);
            return Number.isFinite(parsed) ? [['five_elements', parsed]] : [];
        }

        const parsed = Number(value);
        return Number.isFinite(parsed) ? [[name, parsed]] : [];
    });
}

function buildReportPayloadFromAnalysis(data) {
    const analyzedLocation = getAnalyzedLocationDetails(data);
    const polygon = data.polygon || null;
    const categoryScores = data.category_scores || {};
    const fiveElements = normalizeFiveElements(data, categoryScores);
    const yinYangBalance = Number(firstFiniteNumber(data.yin_yang_balance, categoryScores.yin_yang_balance, 0) || 0);
    const qiFlowScore = Number(firstFiniteNumber(data.qi_flow_score, data.qi_flow, categoryScores.qi_flow, 0) || 0);

    // Capture all individual category scores for detailed breakdown
    const individualCategories = {
        orientation: Number(categoryScores.orientation || 0),
        building_harmony: Number(categoryScores.building_harmony || 0),
        road_accessibility: Number(categoryScores.road_accessibility || 0),
        environment: Number(categoryScores.environment || 0),
        green_space: Number(categoryScores.green_space || 0),
        water_element: Number(categoryScores.water_element || 0),
        spiritual_energy: Number(categoryScores.spiritual_energy || 0)
    };

    return {
        generatedAt: new Date().toISOString(),
        mode: polygon ? 'polygon' : 'location',
        score: {
            final: Number(data.final_score || 0),
            traditional: Number(data.traditional_score || 0),
            ai: data.ai_score == null ? null : Number(data.ai_score),
            status: getScoreRange(Number(data.final_score || 0)).description
        },
        location: {
            label: analyzedLocation.label || 'Selected analysis area',
            latitude: Number.isFinite(analyzedLocation.latitude) ? analyzedLocation.latitude : null,
            longitude: Number.isFinite(analyzedLocation.longitude) ? analyzedLocation.longitude : null,
            radius: Number.isFinite(analyzedLocation.radius) ? analyzedLocation.radius : null
        },
        polygon: polygon ? {
            vertices: Number(polygon.num_vertices || 0),
            areaKm2: Number(polygon.area_km2 || 0),
            centroid: {
                latitude: Number(polygon.centroid?.latitude),
                longitude: Number(polygon.centroid?.longitude)
            }
        } : null,
        categoryScores,
        individualCategories,
        fiveElements,
        yinYangBalance,
        qiFlowScore,
        explanations: Array.isArray(data.explanations) ? data.explanations : [],
        suggestions: Array.isArray(data.suggestions) ? data.suggestions : [],
        grades: SCORE_GRADES.map(grade => ({
            range: grade.range?.[getUiLang()] || grade.range?.en,
            label: grade.description?.[getUiLang()] || grade.description?.en,
            color: grade.color
        }))
    };
}

function exportAnalysisReport() {
    // Always rebuild payload from latest analysis data to ensure we have current values
    if (!latestAnalysisData) {
        alert(tRuntime('Please run an analysis before exporting a report.', '请先运行分析，再导出报告。'));
        return;
    }

    // Rebuild payload fresh from current analysis data
    const freshPayload = buildReportPayloadFromAnalysis(latestAnalysisData);

    const reportId = `report_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const reportKey = `qimatrix_export_report_${reportId}`;

    try {
        localStorage.setItem(reportKey, JSON.stringify(freshPayload));
    } catch (error) {
        console.error('Failed to cache report payload:', error);
        alert(tRuntime('Failed to prepare report export. Please try again.', '准备导出报告失败，请重试。'));
        return;
    }

    const reportUrl = `exportreport.html?reportId=${encodeURIComponent(reportId)}`;
    const reportWindow = window.open(reportUrl, '_blank', 'noopener');
    if (!reportWindow) {
        alert(tRuntime('Pop-up blocked. Please allow pop-ups to export the report.', '弹窗被拦截，请允许弹窗以导出报告。'));
    }
}

function buildActionButtons() {
    return `
        <div class="actions-row">
            <button class="primary-action" type="button" onclick="exportAnalysisReport()">${tRuntime('Download PDF Report', '下载 PDF 报告')}</button>
        </div>
    `;
}

function displayResults(data) {
    _stopLoadingProgress();
    setAnalyzingLayout(false);
    latestAnalysisData = data;

    const ui = {
        yourAnalysis: tRuntime('Your Analysis', '您的分析'),
        overallFengShui: tRuntime('Overall Feng Shui', '综合风水'),
        scoreLegend: tRuntime('Score color legend', '评分颜色图例'),
        locationUsed: tRuntime('Location Used For Analysis', '用于分析的位置'),
        yourLocation: tRuntime('Your Location', '您的位置'),
        locationMetrics: tRuntime('Location Metrics', '位置指标'),
        radius: tRuntime('Radius', '半径'),
        latitude: tRuntime('Latitude', '纬度'),
        longitude: tRuntime('Longitude', '经度'),
        orientation: tRuntime('Orientation', '朝向'),
        analysisScores: tRuntime('Analysis Scores', '分析评分'),
        yinYang: tRuntime('Yin-Yang Balance', '阴阳平衡'),
        qiFlow: tRuntime('Qi Flow', '气流'),
        fiveElements: tRuntime('Five Elements', '五行'),
        traditional: tRuntime('Traditional', '传统评分'),
        overall: tRuntime('Overall', '综合评分'),
        aiScore: tRuntime('AI Score', 'AI评分'),
        aiScoreTitle: tRuntime(
            'AI Score: Machine learning prediction. May differ from Traditional when site has unique characteristics (campuses, temples, etc)',
            'AI评分：机器学习预测结果。在校园、寺庙等特殊场景下可能与传统评分存在差异。'
        ),
        categoryBreakdown: tRuntime('Category Breakdown', '分类细分'),
        methodology: tRuntime('Methodology', '评分方法'),
        methodologyDesc: tRuntime(
            'Overall Score blends Traditional Feng Shui analysis (80%) with AI predictions (20%). Traditional scoring evaluates orientation, green space, water proximity, and environmental quality.',
            '综合评分由传统风水分析（80%）与AI预测（20%）融合而成。传统评分主要评估朝向、绿地、水体邻近度与环境质量。'
        ),
        aiNoteTitle: tRuntime('AI Score Note:', 'AI评分说明：'),
        aiNoteText: tRuntime(
            'The AI model is trained on commercial/residential urban features. This location may have unique characteristics (campus, institutional, or sacred site) that the standard model does not fully recognize. The Traditional analysis is often more reliable for non-standard locations. We are continuously improving the AI to recognize more site types.',
            'AI模型主要基于商住城市特征训练。该位置可能具备校园、机构或宗教场所等特殊属性，标准模型暂未完全识别。对于非标准场景，传统分析通常更可靠。我们会持续优化AI以识别更多场地类型。'
        ),
        fiveElementsDistribution: tRuntime('Five Elements Distribution', '五行分布'),
        elementAnalysis: tRuntime('Element Analysis', '元素分析'),
        strongest: tRuntime('Strongest', '最强项'),
        weakest: tRuntime('Weakest', '最弱项'),
        summary: tRuntime('Summary', '总结'),
        summaryText: tRuntime(
            `Environmental analysis indicates an overall score of ${Math.round(OutdoorUI.clampScore(data.final_score || 0))}/100 with status ${getStatusText(OutdoorUI.clampScore(data.final_score || 0))}. Priority should focus on low-scoring environmental categories while maintaining strengths in ${localizeElementName(getElementProfile(normalizeFiveElements(data, data.category_scores || {})).strongest[0])} and flow continuity.`,
            `环境分析显示综合评分为 ${Math.round(OutdoorUI.clampScore(data.final_score || 0))}/100，状态为 ${getStatusText(OutdoorUI.clampScore(data.final_score || 0))}。建议优先改善低分项，同时保持 ${localizeElementName(getElementProfile(normalizeFiveElements(data, data.category_scores || {})).strongest[0])} 的优势与气流连续性。`
        )
    };

    const dashboard = document.getElementById('dashboard');
    const summaryCard = document.getElementById('summaryCard');
    const aiPanel = document.getElementById('aiPanelMount');
    const mapInsightsPanel = document.getElementById('mapInsightsPanel');
    dashboard.classList.remove('loading-screen');

    // Remove hidden state to show sections
    dashboard.classList.remove('hidden-state');
    if (aiPanel) aiPanel.classList.remove('hidden-state');

    const finalScore = OutdoorUI.clampScore(data.final_score || 0);
    const traditionalScore = OutdoorUI.clampScore(data.traditional_score || 0);
    const aiScore = data.ai_score;
    const categoryScores = data.category_scores || {};
    const explanations = data.explanations || [];
    const suggestions = data.suggestions || [];
    const fiveElements = normalizeFiveElements(data, categoryScores);
    const yinYangBalance = OutdoorUI.clampScore(
        firstFiniteNumber(data.yin_yang_balance, categoryScores.yin_yang_balance, 0) || 0
    );
    const qiFlowScore = OutdoorUI.clampScore(
        firstFiniteNumber(data.qi_flow_score, data.qi_flow, categoryScores.qi_flow, 0) || 0
    );
    const polygonInfo = data.polygon || {};
    const isPolygonAnalysis = Boolean(data.polygon);
    const fallbackRadius = parseInt(document.getElementById('radius')?.value, 10) || 500;
    const analyzedLocation = getAnalyzedLocationDetails(data, fallbackRadius);
    const latitude = analyzedLocation.latitude;
    const longitude = analyzedLocation.longitude;
    const radiusMeters = analyzedLocation.radius;
    const analyzedLocationLabel = analyzedLocation.label;
    const analyzedCoordsText = analyzedLocation.coordinatesText;

    const elementOverall = OutdoorUI.clampScore(
        firstFiniteNumber(
            fiveElements.overall_score,
            fiveElements.overall_harmony,
            categoryScores.five_elements_harmony,
            0
        ) || 0
    );
    const elementProfile = getElementProfile(fiveElements);
    const categoryEntries = normalizeCategoryEntries(categoryScores, elementOverall);

    const orientationScore = OutdoorUI.clampScore(categoryScores.orientation || 0);
    const buildingHarmonyScore = OutdoorUI.clampScore(categoryScores.building_harmony || 0);
    const roadAccessibilityScore = OutdoorUI.clampScore(categoryScores.road_accessibility || 0);
    const environmentScore = OutdoorUI.clampScore(categoryScores.environment || 0);
    const greenSpaceScore = OutdoorUI.clampScore(categoryScores.green_space || 0);
    const waterElementScore = OutdoorUI.clampScore(categoryScores.water_element || 0);
    const spiritualEnergyScore = OutdoorUI.clampScore(categoryScores.spiritual_energy || 0);

    const currentFindings = splitFindings(explanations, 'Current');
    const normalizedCategoryScores = Object.fromEntries(categoryEntries);
    const missingFindings = findLowestCategories(normalizedCategoryScores, 3).length
        ? findLowestCategories(normalizedCategoryScores, 3)
        : [tRuntime('No major deficiencies detected in category scoring.', '分类评分未发现明显短板。')];
    const improvements = splitFindings(suggestions, 'Improvement');

    latestReportPayload = buildReportPayloadFromAnalysis(data);

    if (summaryCard) {
        const scoreRange = getScoreRange(finalScore);
        const scorePercent = Math.min(100, Math.max(0, finalScore));
        const activeColor = scoreRange.color || getStatusColor(finalScore);
        const gaugeRadius = 80;
        const gaugeCircumference = 2 * Math.PI * gaugeRadius;
        const gaugeOffset = gaugeCircumference * (1 - scorePercent / 100);
        
        summaryCard.innerHTML = `
            <h2>${ui.yourAnalysis}</h2>
            <div class="analysis-header">
                <div class="gauge-container">
                    <svg class="circular-gauge" viewBox="0 0 200 200">
                        <circle class="gauge-bg" cx="100" cy="100" r="80" fill="none" stroke="#e5e7eb" stroke-width="20"/>
                        <circle cx="100" cy="100" r="80" fill="none" stroke="${activeColor}" stroke-width="20" stroke-linecap="round" stroke-dasharray="${gaugeCircumference}" stroke-dashoffset="${gaugeOffset}" transform="rotate(-90 100 100)"/>
                    </svg>
                    <div class="gauge-content">
                        <div class="gauge-score" style="color: ${activeColor};">${Math.round(finalScore)}</div>
                    </div>
                </div>
                
                <div class="analysis-info">
                    <div class="info-label">${ui.overallFengShui}</div>
                    <div class="info-status"><strong style="color: ${activeColor};">${scoreRange.description}</strong></div>
                    <div class="color-bar">
                        <div class="color-segment" style="background-color: ${activeColor}; width: 100%;"></div>
                    </div>
                    <div class="score-legend" aria-label="${ui.scoreLegend}">
                        ${SCORE_GRADES.map(grade => `
                            <span class="legend-item"><span class="legend-dot" style="background:${grade.color};"></span><span class="legend-label">${grade.description?.[getUiLang()] || grade.description?.en}</span></span>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    const orientation = Number.isFinite(longitude)
        ? (longitude >= 0 ? tRuntime('East-Oriented Sector', '东向扇区') : tRuntime('West-Oriented Sector', '西向扇区'))
        : tRuntime('N/A', '无');

    const locationMetricsHTML = isPolygonAnalysis ? '' : `
            <h3 class="section-heading" style="color: #000000;">${ui.locationUsed}</h3>
            <div class="analysis-location-card" title="${escapeHtml(analyzedLocationLabel)}" style="color: #000000;">
                <div class="analysis-location-card-label" style="color: #000000;">${ui.yourLocation}</div>
                <div class="analysis-location-card-name" style="color: #000000;">${escapeHtml(analyzedLocationLabel)}</div>
                <div class="analysis-location-card-coords" style="color: #000000;">${escapeHtml(analyzedCoordsText)}</div>
            </div>
            <h3 class="section-heading" style="color: #000000;">${ui.locationMetrics}</h3>
            <div class="location-grid" style="color: #000000;">
                <div class="location-item" style="color: #000000;">
                    <div class="location-icon">📍</div>
                    <div class="location-content">
                        <div class="location-label" style="color: #000000;">${ui.radius}</div>
                        <div class="location-value" style="color: #000000;">${Number.isFinite(radiusMeters) ? Math.round(radiusMeters) : tRuntime('N/A', '无')} m</div>
                    </div>
                </div>
                <div class="location-item" style="color: #000000;">
                    <div class="location-icon">🌐</div>
                    <div class="location-content">
                        <div class="location-label" style="color: #000000;">${ui.latitude}</div>
                        <div class="location-value" style="color: #000000;">${Number.isFinite(latitude) ? latitude.toFixed(4) : tRuntime('N/A', '无')}</div>
                    </div>
                </div>
                <div class="location-item" style="color: #000000;">
                    <div class="location-icon">🌐</div>
                    <div class="location-content">
                        <div class="location-label" style="color: #000000;">${ui.longitude}</div>
                        <div class="location-value" style="color: #000000;">${Number.isFinite(longitude) ? longitude.toFixed(4) : tRuntime('N/A', '无')}</div>
                    </div>
                </div>
                <div class="location-item" style="color: #000000;">
                    <div class="location-icon">🧭</div>
                    <div class="location-content">
                        <div class="location-label" style="color: #000000;">${ui.orientation}</div>
                        <div class="location-value" style="color: #000000;">${orientation}</div>
                    </div>
                </div>
            </div>
    `;

    dashboard.innerHTML = `
        <div class="card">
            ${locationMetricsHTML}
            
            <h3 class="section-heading" style="margin-top: 24px; color: #000000;">${ui.analysisScores}</h3>
            <div class="scores-grid">
                <div class="score-card">
                    <span class="label" style="color: #000000;">${ui.yinYang}</span>
                    <span class="value" style="color: ${getScoreTextColor(yinYangBalance)};">${Math.round(yinYangBalance)}</span>
                </div>
                <div class="score-card">
                    <span class="label" style="color: #000000;">${ui.qiFlow}</span>
                    <span class="value" style="color: ${getScoreTextColor(qiFlowScore)};">${Math.round(qiFlowScore)}</span>
                </div>
                <div class="score-card">
                    <span class="label" style="color: #000000;">${ui.fiveElements}</span>
                    <span class="value" style="color: ${getScoreTextColor(elementOverall)};">${Math.round(elementOverall)}</span>
                </div>
                <div class="score-card">
                    <span class="label" style="color: #000000;">${ui.traditional}</span>
                    <span class="value" style="color: ${getScoreTextColor(traditionalScore)};">${Math.round(traditionalScore)}</span>
                </div>
                <div class="score-card">
                    <span class="label" style="color: #000000;">${ui.overall}</span>
                    <span class="value" style="color: ${getScoreTextColor(finalScore)};">${Math.round(finalScore)}</span>
                </div>
                ${aiScore ? `
                <div class="score-card" title="${ui.aiScoreTitle}">
                    <span class="label" style="color: #000000;">${ui.aiScore}</span>
                    <span class="value" style="color: ${getScoreTextColor(OutdoorUI.clampScore(aiScore))};">${Math.round(OutdoorUI.clampScore(aiScore))}</span>
                </div>
                ` : ''}
            </div>

            <h3 class="section-heading" style="margin-top: 24px; color: #000000;">${ui.categoryBreakdown}</h3>
            <div class="scores-grid">
                ${categoryEntries
                    .filter(([name]) => !['yin_yang_balance', 'qi_flow'].includes(name))
                    .map(([name, value]) => `
                        <div class="score-card">
                            <span class="label" style="color: #000000;">${formatCategoryName(name)}</span>
                            <span class="value" style="color: ${getScoreTextColor(OutdoorUI.clampScore(value))};">${Math.round(OutdoorUI.clampScore(value))}</span>
                        </div>
                    `).join('')}
            </div>

            <div style="margin-top: 24px; padding: 16px; background-color: #f0f9ff; border-left: 4px solid #3b82f6; border-radius: 4px; color: #000000;">
                <h3 style="margin: 0 0 8px 0; font-size: 14px; color: #1e40af; font-weight: 600;">📊 ${ui.methodology}</h3>
                <p style="margin: 0 0 12px 0; font-size: 12px; line-height: 1.5; color: #334155;">
                    ${ui.methodologyDesc}
                </p>
                ${aiScore && OutdoorUI.clampScore(aiScore) < 65 ? `
                <div style="padding: 12px; background-color: #fef3c7; border-radius: 3px; border-left: 3px solid #f59e0b; margin-top: 10px;">
                    <p style="margin: 0; font-size: 11px; line-height: 1.4; color: #92400e;">
                        <strong>⚠️ ${ui.aiNoteTitle}</strong> ${ui.aiNoteText}
                    </p>
                </div>
                ` : ''}
            </div>
        </div>
    `;

    if (aiPanel) {
        aiPanel.innerHTML = `
            <h3 style="color: #000000;">${ui.fiveElementsDistribution}</h3>
            <div class="five-elements-chart-card">
                <div class="five-elements-chart-wrap">
                    <canvas id="fiveElementsChart"></canvas>
                </div>
            </div>

            <h3 style="margin-top: 16px; color: #000000;">${ui.elementAnalysis}</h3>
            <div class="scores-grid element-scores-grid">
                <div class="score-card">
                    <span class="label" style="color: #000000;">${tRuntime('Wood', '木')}</span>
                    <span class="value" style="color: ${getScoreTextColor(elementProfile.values.Wood)};">${Math.round(elementProfile.values.Wood)}</span>
                </div>
                <div class="score-card">
                    <span class="label" style="color: #000000;">${tRuntime('Fire', '火')}</span>
                    <span class="value" style="color: ${getScoreTextColor(elementProfile.values.Fire)};">${Math.round(elementProfile.values.Fire)}</span>
                </div>
                <div class="score-card">
                    <span class="label" style="color: #000000;">${tRuntime('Earth', '土')}</span>
                    <span class="value" style="color: ${getScoreTextColor(elementProfile.values.Earth)};">${Math.round(elementProfile.values.Earth)}</span>
                </div>
                <div class="score-card">
                    <span class="label" style="color: #000000;">${tRuntime('Metal', '金')}</span>
                    <span class="value" style="color: ${getScoreTextColor(elementProfile.values.Metal)};">${Math.round(elementProfile.values.Metal)}</span>
                </div>
                <div class="score-card">
                    <span class="label" style="color: #000000;">${tRuntime('Water', '水')}</span>
                    <span class="value" style="color: ${getScoreTextColor(elementProfile.values.Water)};">${Math.round(elementProfile.values.Water)}</span>
                </div>
            </div>

            <div class="element-summary-row">
                <div class="element-summary-item" style="color: #000000;"><strong>${ui.strongest}:</strong> ${localizeElementName(elementProfile.strongest[0])} (${Math.round(elementProfile.strongest[1])})</div>
                <div class="element-summary-item" style="color: #000000;"><strong>${ui.weakest}:</strong> ${localizeElementName(elementProfile.weakest[0])} (${Math.round(elementProfile.weakest[1])})</div>
            </div>

            <p style="margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--ei-border); color: #000000; font-size: 13px; line-height: 1.6;">
                <strong>${ui.summary}:</strong> ${ui.summaryText}
            </p>

            ${buildActionButtons()}
        `;
    }

    if (mapInsightsPanel) {
        const labels = {
            high: tRuntime('High', '高'),
            medium: tRuntime('Medium', '中'),
            low: tRuntime('Low', '低'),
            confidence: tRuntime('Confidence', '置信度'),
            dataSources: tRuntime('Data sources', '数据来源'),
            whatGood: tRuntime('What Is Already Good', '当前优势'),
            whatNeed: tRuntime('What Needs Improvement', '需要改进'),
            improveTitle: tRuntime('How to Improve', '如何改进'),
            priorityNow: tRuntime('Priority Actions (Now)', '优先动作（立即）'),
            nextPlanned: tRuntime('Next Actions (Planned)', '下一步动作（计划）')
        };

        const modelAgreement = aiScore == null
            ? 65
            : Math.max(0, Math.min(100, 100 - Math.abs(OutdoorUI.clampScore(aiScore) - traditionalScore)));

        const confidenceFromAnalysis = (signalValues) => {
            const numeric = signalValues.map(Number).filter(Number.isFinite);
            const coverage = signalValues.length ? (numeric.length / signalValues.length) * 100 : 0;

            let consistency = 55;
            if (numeric.length >= 2) {
                const mean = numeric.reduce((a, b) => a + b, 0) / numeric.length;
                const variance = numeric.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / numeric.length;
                const std = Math.sqrt(variance);
                consistency = Math.max(0, Math.min(100, 100 - std * 1.3));
            }

            const confidenceScore = coverage * 0.45 + consistency * 0.35 + modelAgreement * 0.20;

            if (confidenceScore >= 75) return labels.high;
            if (confidenceScore >= 55) return labels.medium;
            return labels.low;
        };

        const insightsSections = [
            {
                id: '1',
                title: tRuntime('Qi Flow', '气流'),
                score: qiFlowScore,
                confidence: confidenceFromAnalysis([qiFlowScore, orientationScore, roadAccessibilityScore]),
                dataSources: [
                    tRuntime('Road Network', '道路网络'),
                    tRuntime('Orientation', '朝向'),
                    tRuntime('Building Density', '建筑密度')
                ],
                signals: [
                    tRuntime(`Qi Flow score: ${Math.round(qiFlowScore)}/100`, `气流评分：${Math.round(qiFlowScore)}/100`),
                    tRuntime(`Orientation signal: ${Math.round(orientationScore)}/100`, `朝向信号：${Math.round(orientationScore)}/100`),
                    tRuntime(`Road access signal: ${Math.round(roadAccessibilityScore)}/100`, `道路可达信号：${Math.round(roadAccessibilityScore)}/100`)
                ],
                driver: roadAccessibilityScore < 45
                    ? tRuntime(`Primary drag is weak road continuity (${Math.round(roadAccessibilityScore)}/100).`, `主要短板是道路连续性偏弱（${Math.round(roadAccessibilityScore)}/100）。`)
                    : tRuntime(`Primary support is workable circulation access (${Math.round(roadAccessibilityScore)}/100).`, `主要支撑来自可用的通行可达性（${Math.round(roadAccessibilityScore)}/100）。`),
                good: qiFlowScore >= 70
                    ? tRuntime(`Qi flow is stable at ${Math.round(qiFlowScore)}/100 with healthy directional support.`, `气流稳定（${Math.round(qiFlowScore)}/100），方向支撑良好。`)
                    : tRuntime(`Qi flow has a usable baseline (${Math.round(qiFlowScore)}/100) for targeted upgrades.`, `气流具备可用基础（${Math.round(qiFlowScore)}/100），适合定向优化。`),
                missing: qiFlowScore >= 70
                    ? tRuntime('Protect performance by keeping main entry and internal movement lines unobstructed, and avoid new bulky barriers along primary flow axes.', '通过保持主入口与内部动线畅通来维持表现，并避免在主要气流轴线上新增大型阻挡物。')
                    : tRuntime(`Target Qi Flow 75+: declutter entry axes, reduce abrupt blocks, and improve route hierarchy where Road Access is ${Math.round(roadAccessibilityScore)}/100.`, `目标将气流提升到 75+：清理入口轴线、减少突兀阻断，并在道路可达性 ${Math.round(roadAccessibilityScore)}/100 的基础上优化路径层级。`)
            },
            {
                id: '2',
                title: tRuntime('Yin-Yang Balance', '阴阳平衡'),
                score: yinYangBalance,
                confidence: confidenceFromAnalysis([yinYangBalance, greenSpaceScore, buildingHarmonyScore]),
                dataSources: ['NDVI', tRuntime('Building Density', '建筑密度'), tRuntime('Road Network', '道路网络')],
                signals: [
                    tRuntime(`Yin-Yang score: ${Math.round(yinYangBalance)}/100`, `阴阳评分：${Math.round(yinYangBalance)}/100`),
                    tRuntime(`Green space signal: ${Math.round(greenSpaceScore)}/100`, `绿地信号：${Math.round(greenSpaceScore)}/100`),
                    tRuntime(`Building harmony signal: ${Math.round(buildingHarmonyScore)}/100`, `建筑和谐信号：${Math.round(buildingHarmonyScore)}/100`)
                ],
                driver: Math.abs(greenSpaceScore - buildingHarmonyScore) > 25
                    ? tRuntime(`Imbalance is driven by a ${Math.abs(Math.round(greenSpaceScore - buildingHarmonyScore))}-point gap between natural and built signals.`, `失衡主要由自然与建成信号间 ${Math.abs(Math.round(greenSpaceScore - buildingHarmonyScore))} 分差引起。`)
                    : tRuntime('Natural and built signals are relatively aligned, supporting balance.', '自然与建成信号相对一致，平衡性较好。'),
                good: yinYangBalance >= 70
                    ? tRuntime(`Yin-Yang is in a healthy band (${Math.round(yinYangBalance)}/100) with workable calm/activity distribution.`, `阴阳处于健康区间（${Math.round(yinYangBalance)}/100），静动分布可用。`)
                    : tRuntime(`A partial equilibrium exists (${Math.round(yinYangBalance)}/100), so correction can be incremental.`, `当前存在部分平衡（${Math.round(yinYangBalance)}/100），可采用渐进式修正。`),
                missing: yinYangBalance >= 70
                    ? tRuntime('Maintain parity by preserving quiet restorative zones and active movement corridors at similar intensity.', '通过保持静态修复区与动态通行区的强度对等来维持平衡。')
                    : tRuntime('Target Yin-Yang 72+: increase calm zones (green/restorative pockets) or reduce overstimulation from dense built edges.', '目标将阴阳提升至 72+：增加安静修复区域（绿地/休息角），或降低密集建成边界带来的过度刺激。')
            },
            {
                id: '3',
                title: tRuntime('Five Elements Balance', '五行平衡'),
                score: elementOverall,
                confidence: confidenceFromAnalysis([
                    elementProfile.values.Wood,
                    elementProfile.values.Fire,
                    elementProfile.values.Earth,
                    elementProfile.values.Metal,
                    elementProfile.values.Water
                ]),
                dataSources: ['NDVI', tRuntime('Rivers', '河流'), tRuntime('Buildings', '建筑'), tRuntime('Orientation', '朝向')],
                signals: [
                    tRuntime(`Wood ${Math.round(elementProfile.values.Wood)}, Fire ${Math.round(elementProfile.values.Fire)}`, `木 ${Math.round(elementProfile.values.Wood)}，火 ${Math.round(elementProfile.values.Fire)}`),
                    tRuntime(`Earth ${Math.round(elementProfile.values.Earth)}, Metal ${Math.round(elementProfile.values.Metal)}, Water ${Math.round(elementProfile.values.Water)}`, `土 ${Math.round(elementProfile.values.Earth)}，金 ${Math.round(elementProfile.values.Metal)}，水 ${Math.round(elementProfile.values.Water)}`),
                    tRuntime(`Overall balance: ${Math.round(elementOverall)}/100`, `总体平衡：${Math.round(elementOverall)}/100`)
                ],
                driver: tRuntime(
                    `Element spread indicates ${localizeElementName(elementProfile.strongest[0])} dominates while ${localizeElementName(elementProfile.weakest[0])} under-contributes.`,
                    `元素分布显示 ${localizeElementName(elementProfile.strongest[0])} 偏强，而 ${localizeElementName(elementProfile.weakest[0])} 贡献不足。`
                ),
                good: tRuntime(
                    `Strongest element is ${localizeElementName(elementProfile.strongest[0])} (${Math.round(elementProfile.strongest[1])}), providing a clear energetic anchor.`,
                    `当前最强元素为 ${localizeElementName(elementProfile.strongest[0])}（${Math.round(elementProfile.strongest[1])}），形成明确能量锚点。`
                ),
                missing: tRuntime(
                    `Weakest element is ${localizeElementName(elementProfile.weakest[0])} (${Math.round(elementProfile.weakest[1])}); prioritize one concrete remedy that lifts it by 8-12 points before tuning other elements.`,
                    `最弱元素为 ${localizeElementName(elementProfile.weakest[0])}（${Math.round(elementProfile.weakest[1])}）；建议先用一项明确措施将其提升 8-12 分，再细调其他元素。`
                )
            },
            {
                id: '4',
                title: tRuntime('Spatial Layout & Orientation', '空间布局与朝向'),
                score: averageScores([orientationScore, buildingHarmonyScore]),
                confidence: confidenceFromAnalysis([orientationScore, buildingHarmonyScore]),
                dataSources: [tRuntime('Orientation', '朝向'), tRuntime('Building Density', '建筑密度'), tRuntime('Road Network', '道路网络')],
                signals: [
                    tRuntime(`Orientation score: ${Math.round(orientationScore)}/100`, `朝向评分：${Math.round(orientationScore)}/100`),
                    tRuntime(`Building harmony: ${Math.round(buildingHarmonyScore)}/100`, `建筑和谐：${Math.round(buildingHarmonyScore)}/100`),
                    tRuntime(`Composite layout score: ${Math.round(averageScores([orientationScore, buildingHarmonyScore]))}/100`, `布局综合评分：${Math.round(averageScores([orientationScore, buildingHarmonyScore]))}/100`)
                ],
                driver: orientationScore < buildingHarmonyScore
                    ? tRuntime(`Directional alignment is weaker by ${Math.abs(Math.round(orientationScore - buildingHarmonyScore))} points.`, `方向一致性较弱，差值为 ${Math.abs(Math.round(orientationScore - buildingHarmonyScore))} 分。`)
                    : tRuntime(`Density/permeability is weaker by ${Math.abs(Math.round(orientationScore - buildingHarmonyScore))} points.`, `密度/通透性较弱，差值为 ${Math.abs(Math.round(orientationScore - buildingHarmonyScore))} 分。`),
                good: orientationScore >= 70
                    ? tRuntime(`Orientation quality is strong (${Math.round(orientationScore)}/100), supporting directional coherence and positive-energy capture.`, `朝向质量较强（${Math.round(orientationScore)}/100），有利于方向一致性与正向能量获取。`)
                    : tRuntime(`Orientation has a baseline (${Math.round(orientationScore)}/100) that can be amplified via layout calibration.`, `朝向具备基础（${Math.round(orientationScore)}/100），可通过布局校准进一步放大。`),
                missing: buildingHarmonyScore >= 80
                    ? tRuntime('Keep permeability stable: preserve key flow corridors and avoid adding large blocks on primary approach axes.', '保持通透性稳定：保留关键流线通道，避免在主要进近轴线新增大型阻挡。')
                    : (buildingHarmonyScore >= 70
                        ? tRuntime('Target Building Harmony 80+: reduce hard barriers near circulation lines and keep at least two clear approach corridors.', '目标将建筑和谐提升至 80+：减少流线附近硬性阻挡，并保持至少两条清晰进近通道。')
                        : tRuntime(`Priority fix: raise Building Harmony from ${Math.round(buildingHarmonyScore)} to 75+ by reducing dense blocking mass in circulation-critical zones.`, `优先修复：将建筑和谐从 ${Math.round(buildingHarmonyScore)} 提升至 75+，方法是在关键流线区域减少高密度阻挡体量。`))
            },
            {
                id: '5',
                title: tRuntime('Environmental Support', '环境支持'),
                score: averageScores([greenSpaceScore, waterElementScore, environmentScore, spiritualEnergyScore]),
                confidence: confidenceFromAnalysis([greenSpaceScore, waterElementScore, environmentScore, spiritualEnergyScore]),
                dataSources: ['DEM', 'NDVI', tRuntime('Rivers', '河流'), tRuntime('Environmental Quality', '环境质量')],
                signals: [
                    tRuntime(`Green ${Math.round(greenSpaceScore)}, Water ${Math.round(waterElementScore)}`, `绿地 ${Math.round(greenSpaceScore)}，水元素 ${Math.round(waterElementScore)}`),
                    tRuntime(`Environment ${Math.round(environmentScore)}, Spiritual ${Math.round(spiritualEnergyScore)}`, `环境 ${Math.round(environmentScore)}，灵性 ${Math.round(spiritualEnergyScore)}`),
                    tRuntime(`Composite support score: ${Math.round(averageScores([greenSpaceScore, waterElementScore, environmentScore, spiritualEnergyScore]))}/100`, `环境支持综合评分：${Math.round(averageScores([greenSpaceScore, waterElementScore, environmentScore, spiritualEnergyScore]))}/100`)
                ],
                driver: greenSpaceScore < 45 || waterElementScore < 45
                    ? tRuntime(`Support weakness is tied to low green/water signals (Green ${Math.round(greenSpaceScore)}, Water ${Math.round(waterElementScore)}).`, `支撑短板来自绿地/水元素信号偏低（绿地 ${Math.round(greenSpaceScore)}，水元素 ${Math.round(waterElementScore)}）。`)
                    : tRuntime(`Support stability is driven by balanced ecological signals (Env ${Math.round(environmentScore)}, Spiritual ${Math.round(spiritualEnergyScore)}).`, `支撑稳定性来自较平衡的生态信号（环境 ${Math.round(environmentScore)}，灵性 ${Math.round(spiritualEnergyScore)}）。`),
                good: environmentScore >= 70
                    ? tRuntime(`Environmental support is strong (${Math.round(environmentScore)}/100), suitable for stable long-term use.`, `环境支撑较强（${Math.round(environmentScore)}/100），适合长期稳定使用。`)
                    : tRuntime(`Environmental support is moderate (${Math.round(environmentScore)}/100) and can improve with targeted upgrades.`, `环境支撑中等（${Math.round(environmentScore)}/100），可通过定向优化提升。`),
                missing: greenSpaceScore >= 70 && waterElementScore >= 70
                    ? tRuntime('Sustain ecological quality with regular maintenance, drainage checks, and long-term stewardship.', '通过定期维护、排水检查与长期管理来保持生态质量。')
                    : tRuntime(`Raise ecological backing by improving weaker side first (Green ${Math.round(greenSpaceScore)} / Water ${Math.round(waterElementScore)}).`, `先提升较弱一侧以增强生态支撑（绿地 ${Math.round(greenSpaceScore)} / 水元素 ${Math.round(waterElementScore)}）。`)
            },
            {
                id: '6',
                title: tRuntime('Accessibility & Infrastructure', '可达性与基础设施'),
                score: averageScores([roadAccessibilityScore, environmentScore]),
                confidence: confidenceFromAnalysis([roadAccessibilityScore, environmentScore]),
                dataSources: [tRuntime('Road Network', '道路网络'), tRuntime('Service Environment', '服务环境')],
                signals: [
                    tRuntime(`Road accessibility: ${Math.round(roadAccessibilityScore)}/100`, `道路可达性：${Math.round(roadAccessibilityScore)}/100`),
                    tRuntime(`Environmental services: ${Math.round(environmentScore)}/100`, `环境服务：${Math.round(environmentScore)}/100`),
                    tRuntime(`Composite access score: ${Math.round(averageScores([roadAccessibilityScore, environmentScore]))}/100`, `可达综合评分：${Math.round(averageScores([roadAccessibilityScore, environmentScore]))}/100`)
                ],
                driver: roadAccessibilityScore < 50
                    ? tRuntime(`Connectivity depth is the primary issue (Road ${Math.round(roadAccessibilityScore)}/100).`, `连通深度是主要问题（道路 ${Math.round(roadAccessibilityScore)}/100）。`)
                    : tRuntime(`Access framework is acceptable (Road ${Math.round(roadAccessibilityScore)}/100); service quality is the current limiter.`, `通达框架可用（道路 ${Math.round(roadAccessibilityScore)}/100）；当前限制因素是服务质量。`),
                good: roadAccessibilityScore >= 70
                    ? tRuntime(`Access network is resilient (${Math.round(roadAccessibilityScore)}/100) and supports practical movement.`, `通达网络韧性较好（${Math.round(roadAccessibilityScore)}/100），可支持实际流动。`)
                    : tRuntime(`Core accessibility exists (${Math.round(roadAccessibilityScore)}/100) with room to improve route efficiency.`, `基础可达性已具备（${Math.round(roadAccessibilityScore)}/100），但路径效率仍可提升。`),
                missing: roadAccessibilityScore >= 70
                    ? tRuntime('Monitor congestion growth and protect circulation quality as demand increases.', '随着需求增长，请持续监测拥堵并保护通行质量。')
                    : tRuntime('Target Road Accessibility 75+: improve route hierarchy, remove choke points, and increase proximity to essential services.', '目标将道路可达性提升至 75+：优化路径层级、消除瓶颈并提升与关键服务点的邻近性。')
            }
        ];

        const sectionActionQueue = [...insightsSections]
            .sort((a, b) => a.score - b.score)
            .map(section => `${section.title}: ${section.missing}`);

        const fallbackImprovementPool = improvements.length ? improvements : missingFindings;
        const combinedImprovementQueue = [
            ...sectionActionQueue,
            ...fallbackImprovementPool.filter(item => !sectionActionQueue.includes(item))
        ];

        const priorityImprovements = combinedImprovementQueue.slice(0, 3);
        const secondaryImprovements = combinedImprovementQueue.slice(3, 6);

        mapInsightsPanel.classList.remove('hidden-state');
        mapInsightsPanel.innerHTML = `
            <div class="insights-header">
                <h3 style="color: #000000;">${tRuntime('Feng Shui AI Insights', '风水AI洞察')}</h3>
                <p style="color: #000000;">${tRuntime('Model-guided interpretation of six core factors, including score evidence, strengths, and prioritized correction points.', '基于模型对六个核心因素进行解读，包含评分证据、优势项与优先修正点。')}</p>
            </div>

            <div class="insights-topic-grid">
                ${insightsSections.map(section => {
                    const scoreRounded = Math.round(section.score);
                    return `
                        <article class="insight-topic-card" style="color: #000000;">
                            <div class="insight-topic-head">
                                <div class="insight-topic-title-wrap">
                                    <span class="insight-index" style="color: #000000;">${section.id}</span>
                                    <h4 style="color: #000000;">${section.title}</h4>
                                </div>
                                <div class="insight-score-pill" style="background:${getStatusColor(scoreRounded)}1a; border-color:${getStatusColor(scoreRounded)}55; color:${getStatusColor(scoreRounded)};">
                                    ${scoreRounded} • ${getScoreHealthLabel(scoreRounded)}
                                </div>
                            </div>

                            <div class="insight-block">
                                <p class="insight-meta" style="color: #000000;"><strong>${labels.confidence}:</strong> ${section.confidence}</p>
                                <p class="insight-meta" style="color: #000000;"><strong>${labels.dataSources}:</strong> ${section.dataSources.join(' • ')}</p>
                                <p class="insight-meta" style="color: #000000;">${section.driver}</p>
                                <ul class="insight-mini-list">
                                    ${section.signals.map(signal => `<li style="color: #000000;">${signal}</li>`).join('')}
                                </ul>
                            </div>

                            <div class="insight-block">
                                <h5 style="color: #000000;">${labels.whatGood}</h5>
                                <p style="color: #000000;">${section.good}</p>
                            </div>

                            <div class="insight-block">
                                <h5 style="color: #000000;">${labels.whatNeed}</h5>
                                <p style="color: #000000;">${section.missing}</p>
                            </div>
                        </article>
                    `;
                }).join('')}
            </div>

            <section class="insight-improvement-card">
                <h4>${labels.improveTitle}</h4>
                <div class="insight-improve-grid">
                    <div>
                        <h5>${labels.priorityNow}</h5>
                        <ul class="findings-list">
                            ${(priorityImprovements.length ? priorityImprovements : [tRuntime('No immediate priority action identified yet.', '暂无需要立即执行的优先动作。')]).map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                    <div>
                        <h5>${labels.nextPlanned}</h5>
                        <ul class="findings-list">
                            ${(secondaryImprovements.length ? secondaryImprovements : [tRuntime('No additional action queued yet.', '暂无后续待执行动作。')]).map(item => `<li>${item}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </section>
        `;
    }

    // Render Five Elements chart
    setTimeout(() => {
        OutdoorUI.RadarElementChart('fiveElementsChart', fiveElements);
    }, 50);
    
    // Pass analysis data to chatbot for AI-powered improvement suggestions
    if (window.fengShuiChatbot && typeof window.fengShuiChatbot.setAnalysisData === 'function') {
        const chatbotData = {
            analysis_type: 'outdoor_location',
            location: {
                address: analyzedLocationLabel,
                lat: latitude,
                lng: longitude,
                radius: radiusMeters
            },
            scores: {
                qi_flow: qiFlowScore,
                overall: finalScore,
                traditional: traditionalScore,
                orientation: orientationScore,
                road_access: roadAccessibilityScore,
                building_density: buildingHarmonyScore,
                water_presence: waterElementScore,
                green_space: greenSpaceScore,
                environment: environmentScore,
                spiritual_energy: spiritualEnergyScore,
                yin_yang_balance: yinYangBalance,
                five_elements: elementOverall
            },
            confidence: data.confidence || 'High',
            data_sources: data.data_sources || ['Road Network', 'Orientation', 'Building Density'],
            issues: missingFindings.join('; ') || 'No major issues detected',
            strengths: currentFindings.join('; ') || 'Analysis in progress',
            features: {
                terrain: data.terrain_analysis || 'Standard urban terrain',
                wind_patterns: data.wind_data || 'Normal wind conditions',
                water_flow: data.water_flow || 'No major water bodies detected',
                building_types: data.building_types || 'Mixed residential and commercial'
            }
        };
        
        console.log('📊 Passing analysis data to chatbot:', chatbotData);
        window.fengShuiChatbot.setAnalysisData(chatbotData);
    } else {
        console.warn('⚠️ Chatbot not initialized yet');
    }
}

// Helper function to get score class for styling
function getScoreClass(score) {
    if (score >= 80) return 'excellent';
    if (score >= 60) return 'good';
    if (score >= 40) return 'average';
    return 'poor';
}

// Helper function to get score description
function getScoreDescription(score) {
    if (score >= 80) return tRuntime('Excellent environmental balance with strong performance.', '环境平衡优秀，整体表现强。');
    if (score >= 60) return tRuntime('Balanced condition with moderate optimization opportunities.', '整体较平衡，仍有中等优化空间。');
    if (score >= 40) return tRuntime('Mixed condition that requires targeted improvements.', '状态混合，需进行针对性改善。');
    return tRuntime('Low condition score; comprehensive intervention is recommended.', '评分较低，建议进行系统性干预。');
}

// Helper function to format category names
function formatCategoryName(category) {
    const localized = {
        green_space: tRuntime('Green Space', '绿地空间'),
        water_element: tRuntime('Water Element', '水元素'),
        building_harmony: tRuntime('Building Harmony', '建筑和谐'),
        road_accessibility: tRuntime('Road Accessibility', '道路可达性'),
        orientation: tRuntime('Orientation', '朝向'),
        environment: tRuntime('Environment', '环境支持'),
        spiritual_energy: tRuntime('Spiritual Energy', '灵性能量'),
        yin_yang_balance: tRuntime('Yin-Yang Balance', '阴阳平衡'),
        five_elements: tRuntime('Five Elements', '五行'),
        five_elements_harmony: tRuntime('Five Elements Harmony', '五行和谐'),
        qi_flow: tRuntime('Qi Flow', '气流')
    };

    if (localized[category]) {
        return localized[category];
    }

    return category
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Render Five Elements radar chart
function renderFiveElementsChart(fiveElements) {
    const canvas = document.getElementById('fiveElementsChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if any
    if (canvas.chart) {
        canvas.chart.destroy();
    }
    
    const elementData = {
        'Wood 🌳': fiveElements.wood || 0,
        'Fire 🔥': fiveElements.fire || 0,
        'Earth ⛰️': fiveElements.earth || 0,
        'Metal ⚔️': fiveElements.metal || 0,
        'Water 💧': fiveElements.water || 0
    };
    
    canvas.chart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: Object.keys(elementData),
            datasets: [{
                label: 'Element Strength',
                data: Object.values(elementData),
                backgroundColor: 'rgba(95, 125, 106, 0.2)',
                borderColor: '#1F3D2B',
                borderWidth: 2,
                pointBackgroundColor: '#1F3D2B',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#1F3D2B'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                r: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        display: false,
                        stepSize: 20
                    },
                    grid: {
                        color: '#d7e1db'
                    },
                    angleLines: {
                        color: '#d7e1db'
                    },
                    pointLabels: {
                        color: '#42564b',
                        font: {
                            size: 12
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + Math.round(context.parsed.r) + '/100';
                        }
                    }
                }
            }
        }
    });
}

// Start polygon drawing mode
function startPolygonDrawing() {
    try {
        if (!drawingManager) {
            displayError('Polygon drawing tool not initialized');
            return;
        }

        revealPostSearchSettings();
        setSelectionMode('polygon');

        if (currentPolygon) {
            map.remove(currentPolygon);
            currentPolygon = null;
        }

        clearPolygonVertexMarkers();

        disablePolygonEditing();
        
        // Start drawing polygon
        drawingManager.polygon();
        
        // Update UI
        document.getElementById('polygonBtn').style.display = 'none';
        document.getElementById('cancelPolygonBtn').style.display = 'inline-block';
        
        setTimeout(() => {
            const dashboard = document.getElementById('dashboard');
            dashboard.innerHTML = `
                <div class="card placeholder-card">
                    <h3>Define Analysis Area</h3>
                    <p>Click on the map to add vertices. Double-click to complete the polygon. Minimum 3 points required.</p>
                </div>
            `;
        }, 100);
    } catch (error) {
        console.error('Failed to start polygon drawing:', error);
        displayError('Failed to start polygon drawing');
    }
}

// Cancel polygon drawing mode
function cancelPolygonDrawing() {
    try {
        if (drawingManager) {
            drawingManager.close();
        }
        
        if (currentPolygon) {
            map.remove(currentPolygon);
            currentPolygon = null;
        }

        clearPolygonVertexMarkers();

        disablePolygonEditing();
        
        // Reset UI
        document.getElementById('polygonBtn').style.display = 'inline-block';
        document.getElementById('cancelPolygonBtn').style.display = 'none';
        setSelectionMode('location');
        updateAnalyzeButtonState();
        
        const dashboard = document.getElementById('dashboard');
        dashboard.innerHTML = `
            <div class="card placeholder-card">
                <h3>Drawing Cancelled</h3>
                <p>Select another location or try polygon drawing again.</p>
            </div>
        `;
    } catch (error) {
        console.error('Failed to cancel polygon drawing:', error);
        displayError('Failed to cancel drawing');
    }
}

// Show polygon menu after drawing is complete
function showPolygonMenu(path) {
    const dashboard = document.getElementById('dashboard');
    dashboard.innerHTML = `
        <div class="card placeholder-card">
            <h3>Area Defined Successfully</h3>
            <p>Polygon vertices: ${path.length}</p>
            <p>Click "Analyze Location" to process this area.</p>
        </div>
    `;
    
    // Reset UI
    document.getElementById('polygonBtn').style.display = 'inline-block';
    document.getElementById('cancelPolygonBtn').style.display = 'none';
    syncPolygonVertexMarkersFromPath(path);
    setSelectionMode('polygon');
}

// Submit polygon for analysis
async function submitPolygonAnalysis() {
    try {
        displayLoading();
        const data = await fetchPolygonAnalysis();
        displayPolygonResults(data);
        
    } catch (error) {
        console.error('Error analyzing polygon:', error);
        displayError('Failed to analyze polygon: ' + error.message);
    }
}

function getPolygonResultsHTML(data) {
    const polygonInfo = data?.polygon || {};
    const centroid = polygonInfo.centroid || data?.centroid || {};

    const rawScore = Number(data?.final_score ?? data?.feng_shui_score ?? 0);
    const score = OutdoorUI.clampScore(Number.isFinite(rawScore) ? rawScore : 0);

    const rawVertices = Number(polygonInfo.num_vertices ?? data?.vertex_count ?? data?.num_vertices);
    const vertexCount = Number.isFinite(rawVertices) && rawVertices > 0 ? rawVertices : null;

    const areaKm2Value = Number(
        polygonInfo.area_km2 ??
        data?.area_km2 ??
        ((Number(data?.area) > 1000) ? Number(data?.area) / 1000000 : Number(data?.area))
    );
    const areaKm2 = Number.isFinite(areaKm2Value) && areaKm2Value >= 0 ? areaKm2Value : null;

    const centroidLat = Number(centroid.latitude ?? centroid.lat);
    const centroidLng = Number(centroid.longitude ?? centroid.lng);

    return `
        <div class="card">
            <h3>Polygon Analysis Scores</h3>
            <div class="scores-grid">
                <div class="score-card">
                    <span class="label">Overall Score</span>
                    <span class="value" style="color: ${getScoreTextColor(score)};">${Math.round(score)}</span>
                    <span class="score-indicator" style="background: ${getStatusColor(score)};"></span>
                </div>
                <div class="score-card">
                    <span class="label">Vertices</span>
                    <span class="value" style="color: ${getScoreTextColor(score)};">${vertexCount ?? 'N/A'}</span>
                    <span class="score-indicator" style="background: ${getStatusColor(score)};"></span>
                </div>
                <div class="score-card">
                    <span class="label">Area (km²)</span>
                    <span class="value" style="color: ${getScoreTextColor(score)};">${areaKm2 !== null ? areaKm2.toFixed(2) : 'N/A'}</span>
                    <span class="score-indicator" style="background: ${getStatusColor(score)};"></span>
                </div>
            </div>

            <h3 style="margin-top: 16px;">Area Details</h3>
            <ul class="findings-list">
                <li><strong>Centroid Latitude:</strong> ${Number.isFinite(centroidLat) ? centroidLat.toFixed(4) : 'N/A'}</li>
                <li><strong>Centroid Longitude:</strong> ${Number.isFinite(centroidLng) ? centroidLng.toFixed(4) : 'N/A'}</li>
                <li><strong>Total Area:</strong> ${areaKm2 !== null ? areaKm2.toFixed(4) : 'N/A'} km²</li>
                <li><strong>Polygon Vertices:</strong> ${vertexCount ?? 'N/A'}</li>
            </ul>

            <h3 style="margin-top: 16px;">Analysis Notes</h3>
            <ul class="findings-list">
                <li>Score computed from polygon centroid environmental data</li>
                <li>Analyze the centroid point individually for detailed metrics</li>
                <li>High variance areas may benefit from multiple point samples</li>
            </ul>
        </div>
    `;
}

// Display polygon analysis results
function displayPolygonResults(data) {
    const dashboard = document.getElementById('dashboard');
    const aiPanel = document.getElementById('aiPanelMount');
    
    // Remove hidden state to show sections
    dashboard.classList.remove('hidden-state');
    if (aiPanel) aiPanel.classList.remove('hidden-state');
    
    // Reuse the same main model output used by point selection
    displayResults(data);

    // Append polygon-specific metadata as extra details
    dashboard.insertAdjacentHTML('beforeend', getPolygonResultsHTML(data));
}

// Render category scores horizontal bar chart
function renderCategoryChart(categoryScores) {
    const canvas = document.getElementById('categoryChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart if any
    if (canvas.chart) {
        canvas.chart.destroy();
    }
    
    // Filter out the special categories and get main categories
    const mainCategories = {};
    for (const [key, value] of Object.entries(categoryScores)) {
        if (!['yin_yang_balance', 'five_elements_harmony', 'qi_flow'].includes(key)) {
            mainCategories[key] = value;
        }
    }
    
    const labels = Object.keys(mainCategories).map(formatCategoryName);
    const data = Object.values(mainCategories);
    
    // Color code based on score
    const backgroundColors = data.map(score => {
        if (score >= 80) return 'rgba(40, 167, 69, 0.8)';  // Green
        if (score >= 60) return 'rgba(23, 162, 184, 0.8)';  // Blue
        if (score >= 40) return 'rgba(255, 193, 7, 0.8)';   // Yellow
        return 'rgba(220, 53, 69, 0.8)';  // Red
    });
    
    canvas.chart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Score',
                data: data,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.8', '1')),
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                x: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value;
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.x.toFixed(1) + '/100';
                        }
                    }
                }
            }
        }
    });
}
