const WEATHER_API_BASES = [
    window.location.origin,
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5000',
    'http://127.0.0.1:5000',
];
let tempUnit = 'C';
let lastWeatherData = null;
let lastApiBase = null;
let lastQuerySource = 'ip';
let lastAstronomyKey = '';

function isPresent(v) {
    return v !== null && v !== undefined && String(v).trim() !== '' && String(v).trim() !== '--';
}

function safeIcon(path) {
    if (!path) return '';
    return path.startsWith('http') ? path : `https:${path}`;
}

function fmtNum(v, suffix = '') {
    if (!Number.isFinite(Number(v))) return '0' + suffix;
    return `${Math.round(Number(v))}${suffix}`;
}

function tempByUnit(c, f) {
    if (tempUnit === 'F') return fmtNum(f, 'F');
    return fmtNum(c, 'C');
}

function speedByUnit(kph, mph) {
    if (tempUnit === 'F') return fmtNum(mph, ' mph');
    return fmtNum(kph, ' kph');
}

function aqiText(v) {
    const n = Number(v);
    if (!Number.isFinite(n) || n <= 0) return 'N/A';
    if (n === 1) return 'Good';
    if (n === 2) return 'Moderate';
    if (n === 3) return 'Unhealthy (Sensitive)';
    if (n === 4) return 'Unhealthy';
    if (n === 5) return 'Very Unhealthy';
    return 'Hazardous';
}

function bestAqiLabel(current, source) {
    const base = aqiText(current.aqi_us_epa);
    if (!isPresent(current.aqi_us_epa)) return 'N/A';
    return base;
}

function sourceLabel(code) {
    if (code === 'coordinates') return 'Device location';
    if (code === 'amap-geocode') return 'AMap geocode';
    if (code === 'weather-text-search') return 'Text search';
    return 'IP fallback';
}

function toShortTime(s) {
    if (!s) return '00:00';
    const parts = s.split(' ');
    if (parts.length < 2) return s;
    return parts[1];
}

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function setSource(text) {
    setText('weatherSource', `Source: ${text}`);
}

function setState(text) {
    setText('weatherState', text);
}

function renderMetrics(current) {
    const grid = document.getElementById('weatherMetrics');
    if (!grid) return;
    const items = [
        ['Feels', tempByUnit(current.feelslike_c, current.feelslike_f)],
        ['Humidity', fmtNum(current.humidity, '%')],
        ['Wind', speedByUnit(current.wind_kph, current.wind_mph)],
        ['Gust', speedByUnit(current.gust_kph, current.gust_mph)],
        ['UV', fmtNum(current.uv)],
        ['Pressure', fmtNum(current.pressure_mb, ' mb')],
        ['Visibility', fmtNum(current.vis_km, ' km')],
        ['Cloud', fmtNum(current.cloud, '%')],
        ['Rain', fmtNum(current.precip_mm, ' mm')],
        ['AQI', bestAqiLabel(current, lastQuerySource)],
        ['PM2.5', fmtNum(current.pm2_5, ' ug/m3')],
        ['EPA Index', isPresent(current.aqi_us_epa) ? String(current.aqi_us_epa) : 'N/A'],
    ];

    grid.innerHTML = items.map(([k, v]) => `
        <div class="metric">
            <span class="label">${k}</span>
            <span class="value">${v}</span>
        </div>
    `).join('');
}

function renderHourly(hourly) {
    const strip = document.getElementById('hourlyStrip');
    if (!strip) return;
    const list = (hourly || []).slice(0, 24);
    strip.innerHTML = list.map(h => `
        <div class="hour">
            <div class="t mono">${toShortTime(h.time)}</div>
            <img src="${safeIcon(h.condition_icon)}" alt="${h.condition_text || 'weather'}" width="34" height="34">
            <div class="v">${tempByUnit(h.temp_c, h.temp_f)}</div>
            <div class="t">Rain ${fmtNum(h.chance_of_rain, '%')} · Snow ${fmtNum(h.chance_of_snow, '%')}</div>
        </div>
    `).join('');
}

function renderDaily(daily) {
    const listEl = document.getElementById('dailyList');
    if (!listEl) return;
    listEl.innerHTML = (daily || []).map(d => `
        <div class="day">
            <div class="date mono">${d.date || '--'}</div>
            <div class="desc">${d.condition_text || '--'} · Rain ${fmtNum(d.daily_chance_of_rain, '%')} · UV ${fmtNum(d.uv)}</div>
            <div class="range">${tempByUnit(d.min_temp_c, d.min_temp_f)} / ${tempByUnit(d.max_temp_c, d.max_temp_f)}</div>
        </div>
    `).join('');
}

function renderHighlights(data) {
    const cur = data.current || {};
    const daily0 = (data.daily || [])[0] || {};
    const holder = document.getElementById('todayHighlights');
    if (!holder) return;

    const dewLabel = tempByUnit(cur.dewpoint_c, cur.dewpoint_f);
    const heatLabel = tempByUnit(cur.heatindex_c, cur.heatindex_f);

    let snowChance = daily0.daily_chance_of_snow;
    if (!isPresent(snowChance)) {
        const hourly = data.hourly || [];
        const snowVals = hourly
            .slice(0, 24)
            .map((h) => Number(h.chance_of_snow))
            .filter((n) => Number.isFinite(n));
        snowChance = snowVals.length ? Math.max(...snowVals) : 0;
    }

    const items = [
        ['RealFeel', tempByUnit(cur.feelslike_c, cur.feelslike_f)],
        ['Dew Point', dewLabel],
        ['Heat Index', heatLabel],
        ['Air Quality', bestAqiLabel(cur, lastQuerySource)],
        ['Rain Chance', fmtNum(daily0.daily_chance_of_rain, '%')],
        ['Snow Chance', fmtNum(snowChance, '%')],
    ];

    holder.innerHTML = items.map(([k, v]) => `
        <div class="highlight">
            <div class="label">${k}</div>
            <div class="value">${v}</div>
        </div>
    `).join('');
}

function firstAvailable(daily, key) {
    for (const d of (daily || [])) {
        if (isPresent(d[key])) return d[key];
    }
    return null;
}

function renderSunMoon(data, astronomy = null) {
    const daily = data.daily || [];
    const holder = document.getElementById('sunMoonGrid');
    if (!holder) return;

    const fromAstro = (k) => (astronomy && isPresent(astronomy[k]) ? astronomy[k] : null);
    const moonrise = fromAstro('moonrise') || firstAvailable(daily, 'moonrise') || 'No moonrise today';
    const moonset = fromAstro('moonset') || firstAvailable(daily, 'moonset') || 'No moonset today';
    const moonPhase = fromAstro('moon_phase') || firstAvailable(daily, 'moon_phase') || 'Unknown';
    const moonIllum = fromAstro('moon_illumination') || firstAvailable(daily, 'moon_illumination') || 0;

    const items = [
        ['Sunrise', fromAstro('sunrise') || firstAvailable(daily, 'sunrise') || '06:00 AM'],
        ['Sunset', fromAstro('sunset') || firstAvailable(daily, 'sunset') || '06:00 PM'],
        ['Moonrise', moonrise],
        ['Moonset', moonset],
        ['Moon Phase', moonPhase],
        ['Illumination', fmtNum(moonIllum, '%')],
    ];

    holder.innerHTML = items.map(([k, v]) => `
        <div class="astro">
            <div class="label">${k}</div>
            <div class="value">${v}</div>
        </div>
    `).join('');
}

function astronomyNeedsFallback(data) {
    const daily = data.daily || [];
    const moonrise = firstAvailable(daily, 'moonrise');
    const moonset = firstAvailable(daily, 'moonset');
    const moonPhase = firstAvailable(daily, 'moon_phase');
    return !moonrise || !moonset || !moonPhase;
}

async function fetchAstronomyFallback(data) {
    const loc = data.location || {};
    const daily = data.daily || [];
    const dt = (daily[0] || {}).date || '';
    if (!isPresent(loc.lat) || !isPresent(loc.lon)) return null;

    const key = `${loc.lat},${loc.lon},${dt}`;
    if (lastAstronomyKey === key) return null;

    const uniqueBases = Array.from(new Set([...(lastApiBase ? [lastApiBase] : []), ...WEATHER_API_BASES]));
    for (const base of uniqueBases) {
        try {
            const url = `${base}/api/weather/astronomy?lat=${encodeURIComponent(loc.lat)}&lng=${encodeURIComponent(loc.lon)}${dt ? `&dt=${encodeURIComponent(dt)}` : ''}`;
            const res = await fetch(url, { cache: 'no-store' });
            const payload = await res.json();
            if (!res.ok || !payload.success || !payload.data || !payload.data.astronomy) continue;
            lastAstronomyKey = key;
            return payload.data.astronomy;
        } catch (_) {
            // Continue trying other backend bases.
        }
    }
    return null;
}

function renderAlerts(alerts) {
    const holder = document.getElementById('weatherAlerts');
    if (!holder) return;
    if (!alerts || alerts.length === 0) {
        holder.innerHTML = '';
        return;
    }
    holder.innerHTML = alerts.slice(0, 3).map(a => `<span>${a.severity || 'Alert'}: ${a.event || 'Weather notice'}</span>`).join('');
}

function renderWeather(data) {
    const loc = data.location || {};
    const cur = data.current || {};
    lastWeatherData = data;
    lastQuerySource = data.query_source || 'ip';

    setText('weatherLocalTime', loc.localtime || '--');
    setText('weatherTimezone', loc.tz_id || '--');
    setText('weatherTemp', tempByUnit(cur.temp_c, cur.temp_f));
    setText('weatherCondition', cur.condition_text || '--');
    setText('weatherLocation', [loc.name, loc.region, loc.country].filter(Boolean).join(', '));

    const icon = document.getElementById('weatherIcon');
    if (icon) {
        icon.src = safeIcon(cur.condition_icon);
    }

    renderMetrics(cur);
    renderHourly(data.hourly || []);
    renderDaily(data.daily || []);
    renderHighlights(data);
    renderSunMoon(data);
    renderAlerts(data.alerts || []);

    if (astronomyNeedsFallback(data)) {
        fetchAstronomyFallback(data)
            .then((astro) => {
                if (astro) renderSunMoon(data, astro);
            })
            .catch(() => {});
    }

    if (data.query_source) {
        setSource(sourceLabel(data.query_source));
        if (data.query_source === 'ip') {
            setState('Use Device Location for the most precise local AQI and conditions.');
        }
    }
}

async function fetchWeather(params = '') {
    const uniqueBases = Array.from(new Set([...(lastApiBase ? [lastApiBase] : []), ...WEATHER_API_BASES]));
    setState('Loading latest weather...');

    let lastErr = null;
    for (const base of uniqueBases) {
        try {
            const url = `${base}/api/weather/forecast?days=7${params}`;
            const res = await fetch(url, { cache: 'no-store' });
            const payload = await res.json();
            if (!res.ok || !payload.success || !payload.data) {
                lastErr = new Error(payload.error || `Weather unavailable from ${base}`);
                continue;
            }

            lastApiBase = base;
            renderWeather(payload.data);
            setState('Updated just now');
            return payload.data;
        } catch (err) {
            lastErr = err;
        }
    }

    throw lastErr || new Error('Weather service unavailable');
}

function fetchByDeviceLocation() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject(new Error('Geolocation not supported'));
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                try {
                    const lat = pos.coords.latitude;
                    const lng = pos.coords.longitude;
                    await fetchWeather(`&lat=${encodeURIComponent(lat)}&lng=${encodeURIComponent(lng)}&_t=${Date.now()}`);
                    setSource('Device location');
                    resolve(true);
                } catch (err) {
                    reject(err);
                }
            },
            (err) => reject(err),
            { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }
        );
    });
}

function init() {
    const form = document.getElementById('weatherSearchForm');
    const input = document.getElementById('weatherQuery');
    const useIp = document.getElementById('weatherUseIp');
    const useDevice = document.getElementById('weatherUseDevice');
    const unitC = document.getElementById('unitC');
    const unitF = document.getElementById('unitF');

    if (!form || !input || !useIp) {
        setState('Weather page is missing required UI elements');
        return;
    }

    if (unitC && unitF) {
        unitC.addEventListener('click', () => {
            tempUnit = 'C';
            unitC.classList.add('active');
            unitF.classList.remove('active');
            if (lastWeatherData) renderWeather(lastWeatherData);
        });

        unitF.addEventListener('click', () => {
            tempUnit = 'F';
            unitF.classList.add('active');
            unitC.classList.remove('active');
            if (lastWeatherData) renderWeather(lastWeatherData);
        });
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const q = input.value.trim();
        if (!q) return;
        try {
            await fetchWeather(`&q=${encodeURIComponent(q)}&_t=${Date.now()}`);
            setSource(`Search: ${q}`);
        } catch (err) {
            setText('weatherCondition', err.message || 'Failed to load weather');
            setState('Search failed');
        }
    });

    useIp.addEventListener('click', async () => {
        try {
            const data = await fetchWeather(`&_t=${Date.now()}`);
            setSource(sourceLabel(data.query_source));
        } catch (err) {
            setText('weatherCondition', err.message || 'Failed to load weather');
            setState('IP lookup failed');
        }
    });

    if (useDevice) {
        useDevice.addEventListener('click', async () => {
            try {
                await fetchByDeviceLocation();
                setState('Updated with device location');
            } catch (err) {
                setState('Device location unavailable');
            }
        });
    }

    // IP-first: show something immediately.
    setSource('IP fallback');
    fetchWeather(`&_t=${Date.now()}`)
        .then((data) => {
            setSource(sourceLabel(data.query_source));
            setState('Using IP weather. Requesting device location...');
        })
        .catch((err) => {
            setText('weatherCondition', err.message || 'Failed to load weather');
            setState('Weather unavailable');
        });

    // In parallel, try to upgrade to device location.
    fetchByDeviceLocation()
        .then(() => {
            setState('Updated with device location');
        })
        .catch(() => {
            // Keep existing IP data if permission denied/unavailable.
            setState('Location permission denied. Staying on IP weather');
        });

    setInterval(() => {
        fetchWeather(`&_t=${Date.now()}`).catch(() => {});
    }, 15 * 60 * 1000);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
