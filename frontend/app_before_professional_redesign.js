// ============================================================
// TERRAMIND AI - FRONTEND APPLICATION
// ============================================================

const API_BASE = "http://127.0.0.1:8000";


// ============================================================
// LANDING PAGE ↔ DASHBOARD NAVIGATION
// ============================================================

const landingPage = document.getElementById("landingPage");
const appDashboard = document.getElementById("appDashboard");

function showDashboard() {
    if (landingPage) landingPage.classList.add("hidden");
    if (appDashboard) appDashboard.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
    // Initialize map after dashboard becomes visible
    setTimeout(() => {
        if (typeof initializeFloodIndiaMap === "function") initializeFloodIndiaMap();
        if (typeof floodIndiaMap !== "undefined" && floodIndiaMap) floodIndiaMap.invalidateSize();
    }, 200);
}

function showLandingPage() {
    if (appDashboard) appDashboard.classList.add("hidden");
    if (landingPage) landingPage.classList.remove("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
}

// Dashboard entry buttons
document.getElementById("navDashboardBtn")?.addEventListener("click", showDashboard);
document.getElementById("heroDashboardBtn")?.addEventListener("click", showDashboard);
document.getElementById("footerDashboardBtn")?.addEventListener("click", (e) => {
    e.preventDefault();
    showDashboard();
});

// Back to home button
document.getElementById("backToHomeBtn")?.addEventListener("click", showLandingPage);

// Smooth scroll for landing page anchor links
document.querySelectorAll('.landing-nav .nav-links a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", (e) => {
        e.preventDefault();
        const targetId = anchor.getAttribute("href").substring(1);
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            targetElement.scrollIntoView({ behavior: "smooth", block: "start" });
        }
    });
});

let selectedLocation = null;
let latestAnalysis = null;


// ============================================================
// DOM ELEMENTS
// ============================================================

const navItems = document.querySelectorAll(".nav-item");
const pages = document.querySelectorAll(".page");

const pageTitle = document.getElementById("pageTitle");
const currentDate = document.getElementById("currentDate");


// ============================================================
// PAGE NAVIGATION
// ============================================================

const pageTitles = {
    dashboard: "Intelligence Dashboard",
    location: "Location Intelligence",
    weather: "Weather Analytics",
    flood: "Flood Risk Analysis",
    satellite: "Satellite Intelligence",
    ai: "AI Environmental Analysis"
};

function openPage(pageId) {

    pages.forEach(page => {
        page.classList.remove("active-page");
    });

    navItems.forEach(item => {
        item.classList.remove("active");
    });

    const targetPage = document.getElementById(pageId);
    const targetNav = document.querySelector(
        `.nav-item[data-page="${pageId}"]`
    );

    if (targetPage) {
        targetPage.classList.add("active-page");
    }

    if (targetNav) {
        targetNav.classList.add("active");
    }

    if (pageTitle) pageTitle.textContent = pageTitles[pageId] || "TerraMind AI";

    window.scrollTo({ top: 0, behavior: "smooth" });
    if (pageId === "dashboard" && typeof floodIndiaMap !== "undefined" && floodIndiaMap) {
        setTimeout(() => floodIndiaMap.invalidateSize(), 180);
    }
}


navItems.forEach(item => {
    item.addEventListener("click", () => {
        openPage(item.dataset.page);
    });
});


document.querySelectorAll("[data-go]").forEach(button => {
    button.addEventListener("click", () => {
        openPage(button.dataset.go);
    });
});


document.getElementById("startAnalysis")?.addEventListener("click", () => {
    openPage("location");
});


// ============================================================
// DATE
// ============================================================

function updateDate() {

    const now = new Date();

    if (currentDate) {
        currentDate.textContent = now.toLocaleDateString("en-IN", {
            day: "numeric", month: "short", year: "numeric"
        });
    }
}

updateDate();


// ============================================================
// TOAST MESSAGE
// ============================================================

function showToast(message) {

    const toast = document.getElementById("toast");

    if (!toast) { console.info(message); return; }
    toast.textContent = message;
    toast.classList.add("show");

    setTimeout(() => {
        toast.classList.remove("show");
    }, 3500);
}


// ============================================================
// LOCATION SEARCH
// ============================================================

const locationInput = document.getElementById("locationInput");
const searchLocationButton = document.getElementById("searchLocation");


searchLocationButton?.addEventListener("click", searchLocation);

locationInput?.addEventListener("keydown", event => {
    if (event.key === "Enter") searchLocation();
});


async function searchLocation() {

    const query = locationInput.value.trim();

    if (query.length < 2) {
        showToast("Please enter at least two characters.");
        return;
    }

    const loading = document.getElementById("locationLoading");
    const resultsContainer =
        document.getElementById("locationResults");

    loading?.classList.remove("hidden");
    if (resultsContainer) resultsContainer.innerHTML = "";

    try {

        const response = await fetch(
            `${API_BASE}/api/v1/location/search?q=${encodeURIComponent(query)}`
        );

        if (!response.ok) {
            throw new Error("Location search failed");
        }

        const data = await response.json();

        displayLocationResults(data.results || []);

    } catch (error) {

        console.error(error);

        if (resultsContainer) resultsContainer.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-circle-exclamation"></i>
                <h3>Search unavailable</h3>
                <p>
                    Please make sure the TerraMind backend is running.
                </p>
            </div>
        `;

        showToast("Unable to search location.");

    } finally {

        loading?.classList.add("hidden");

    }
}


// ============================================================
// DISPLAY LOCATION RESULTS
// ============================================================

function displayLocationResults(results) {

    const container =
        document.getElementById("locationResults");

    const resultCount =
        document.getElementById("resultCount");

    if (resultCount) resultCount.textContent =
        `${results.length} location${results.length !== 1 ? "s" : ""}`;


    if (results.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                <i class="fa-solid fa-map-location-dot"></i>
                <h3>No locations found</h3>
                <p>Try another city or district name.</p>
            </div>
        `;

        return;
    }


    container.innerHTML = results.map((location, index) => `

        <div class="location-result"
             data-index="${index}">

            <strong>
                <i class="fa-solid fa-location-dot"></i>
                ${escapeHTML(location.name || "Unknown Location")}
            </strong>

            <span>
                ${escapeHTML(location.district || "")}
                ${location.state ? ", " + escapeHTML(location.state) : ""}
                ${location.country ? ", " + escapeHTML(location.country) : ""}
            </span>

        </div>

    `).join("");


    document.querySelectorAll(".location-result").forEach(element => {

        element.addEventListener("click", () => {

            const index =
                Number(element.dataset.index);

            selectLocation(results[index]);

        });

    });

}


// ============================================================
// SELECT LOCATION
// ============================================================

function selectLocation(location) {
    selectedLocation = location;
    if (typeof renderCommandSelectedLocation === "function") renderCommandSelectedLocation(location);

    const selectedContent = document.getElementById("selectedLocationContent");
    if (selectedContent) {
        selectedContent.innerHTML = `
            <div class="selected-details">
                <h2>${escapeHTML(location.name || "Selected Location")}</h2>
                <p style="color:#91a6ad;font-size:13px;">
                    ${escapeHTML(location.district || "")}
                    ${location.state ? ", " + escapeHTML(location.state) : ""}
                    ${location.country ? ", " + escapeHTML(location.country) : ""}
                </p>
                <div class="coordinate-box">
                    <div><span>LATITUDE</span><strong>${location.latitude ?? "--"}</strong></div>
                    <div><span>LONGITUDE</span><strong>${location.longitude ?? "--"}</strong></div>
                </div>
                <button class="primary-btn analyze-location-btn" id="analyzeSelectedLocation" type="button">
                    Analyze This Location <i class="fa-solid fa-arrow-right"></i>
                </button>
            </div>`;
        document.getElementById("analyzeSelectedLocation")?.addEventListener("click", analyzeSelectedLocation);
    }

    const weatherName = document.getElementById("weatherLocationName");
    if (weatherName) weatherName.textContent = `${location.name || "Selected location"}, ${location.state || location.country || ""}`;

    // Clear transient searches so the interface never looks like it stores search history.
    ["locationInput", "commandSearchInput", "commandGlobalSearch"].forEach(id => {
        const input = document.getElementById(id);
        if (input) input.value = "";
    });
    ["locationResults", "commandSearchResults"].forEach(id => {
        const results = document.getElementById(id);
        if (results) { results.innerHTML = ""; results.classList.remove("open"); }
    });
    const resultCount = document.getElementById("resultCount");
    if (resultCount) resultCount.textContent = "0 locations";

    showToast(`${location.name || "Location"} selected. Previous search text cleared.`);
}

// ============================================================
// FLOOD ANALYSIS
// ============================================================

async function analyzeSelectedLocation() {

    if (!selectedLocation) {
        showToast("Please select a location first.");
        return;
    }

    const floodEmpty = document.getElementById("floodEmpty");
    if (floodEmpty) floodEmpty.classList.remove("hidden");

    try {

        const latitude = selectedLocation.latitude;
        const longitude = selectedLocation.longitude;

        const params = new URLSearchParams({
            latitude: latitude,
            longitude: longitude,
            location_name: selectedLocation.name || "Unknown location",
            district: selectedLocation.district || "",
            state: selectedLocation.state || ""
        });

        const response = await fetch(
            `${API_BASE}/api/v1/flood/analyze/location?${params.toString()}`
        );

        if (!response.ok) {
            throw new Error("Flood analysis failed");
        }

        const data = await response.json();

        latestAnalysis = data;
        if (typeof renderCommandAnalysis === "function") renderCommandAnalysis(data);

        updateWeather(data);
        updateFloodAnalysis(data);
        updateSatelliteData(data);
        await loadFloodAlerts();

        showToast("Environmental analysis completed.");

    } catch (error) {

        console.error(error);

        showToast(
            "Analysis failed. Please check that the backend is running."
        );

    }

}


// ============================================================
// WEATHER
// ============================================================

function updateWeather(data) {

    const weather = data.current_weather || {};

    document.getElementById("weatherEmpty")
        .classList.add("hidden");

    document.getElementById("weatherContent")
        .classList.remove("hidden");


    document.getElementById("weatherTemperature").textContent =
        weather.temperature_2m !== undefined
            ? `${weather.temperature_2m}Â°C`
            : "--Â°C";


    document.getElementById("weatherHumidity").textContent =
        weather.relative_humidity_2m !== undefined
            ? `${weather.relative_humidity_2m}%`
            : "--%";


    document.getElementById("weatherRain").textContent =
        weather.rain !== undefined
            ? `${weather.rain} mm`
            : "-- mm";


    document.getElementById("weatherForecast").textContent =
        data.forecast_rainfall_next_24_hours_mm !== undefined
            ? `${data.forecast_rainfall_next_24_hours_mm} mm`
            : "-- mm";


    document.getElementById("weatherTime").textContent =
        weather.time
            ? formatDateTime(weather.time)
            : "--";


    document.getElementById("weatherCondition").textContent =
        getWeatherCondition(weather.weather_code);

}


document.getElementById("refreshWeather")?.addEventListener("click", () => {

        if (!selectedLocation) {
            showToast("Please select a location first.");
            return;
        }

        analyzeSelectedLocation();

    });


// ============================================================
// FLOOD DATA
// ============================================================

function updateFloodAnalysis(data) {

    const flood = data.flood_analysis || {};

    document.getElementById("floodEmpty")
        .classList.add("hidden");

    document.getElementById("floodContent")
        .classList.remove("hidden");


    const riskLevel =
        flood.risk_level || "UNKNOWN";

    document.getElementById("riskLevel")
        .textContent = riskLevel;


    document.getElementById("riskExplanation")
        .textContent =
            flood.explanation ||
            "No explanation available.";


    document.getElementById("floodCurrentRain").textContent =
        `${data.current_rainfall_mm ?? data.current_weather?.rain ?? "--"} mm`;

    document.getElementById("floodForecastRain").textContent =
        `${data.forecast_rainfall_next_24_hours_mm ?? data.forecast_rainfall_mm ?? "--"} mm`;

    const currentRain = Number(data.current_rainfall_mm ?? data.current_weather?.rain);
    const forecastRain = Number(data.forecast_rainfall_next_24_hours_mm ?? data.forecast_rainfall_mm);
    const totalRain = Number.isFinite(currentRain) && Number.isFinite(forecastRain)
        ? (currentRain + forecastRain).toFixed(1)
        : "--";
    document.getElementById("floodTotalRain").textContent = `${totalRain} mm`;


    document.getElementById("historicalCount")
        .textContent =
            data.historical_flood_count ?? "--";


    document.getElementById("warningMessage")
        .textContent =
            flood.warning_message ||
            "This result is not an official weather warning.";


    const riskCircle =
        document.getElementById("riskCircle");

    riskCircle.className = "risk-circle";

    if (riskLevel === "LOW") {
        riskCircle.style.borderColor = "#3fc58e";
    } else if (riskLevel === "MODERATE" || riskLevel === "MEDIUM") {
        riskCircle.style.borderColor = "#f6c445";
    } else if (riskLevel === "HIGH") {
        riskCircle.style.borderColor = "#ef6461";
    } else {
        riskCircle.style.borderColor = "#94a3b8";
    }

}


document.getElementById("runFloodAnalysis")?.addEventListener("click", analyzeSelectedLocation);


// ============================================================
// SATELLITE DATA
// ============================================================

function updateSatelliteData(data) {

    const history = data.satellite_history || [];

    document.getElementById("satelliteEmpty")
        .classList.add("hidden");

    document.getElementById("satelliteContent")
        .classList.remove("hidden");


    if (history.length > 0) {

        document.getElementById("gridId")
            .textContent =
                history[0].grid_id || "--";

    }


    const container =
        document.getElementById("satelliteHistory");


    if (history.length === 0) {

        container.innerHTML = `
            <div class="empty-state">
                <p>No satellite history found for this location.</p>
            </div>
        `;

        return;
    }


    container.innerHTML =
        history.map(item => `

            <div class="satellite-row">

                <span>
                    ${item.year}
                </span>

                <strong>
                    <i class="fa-solid fa-satellite"></i>
                    ${item.image_count ?? 0} satellite observations
                </strong>

            </div>

        `).join("");

}


// ============================================================
// AI ANALYSIS
// ============================================================

document.getElementById("generateAI")?.addEventListener("click", generateAIInsight);


async function generateAIInsight() {

    const output = document.getElementById("aiOutput");

    if (!selectedLocation || !latestAnalysis) {

        output.innerHTML = `
            <div class="empty-ai">
                <i class="fa-solid fa-location-dot"></i>
                <p>Please select and analyze a location before generating an AI insight.</p>
            </div>
        `;

        showToast("Please complete a location analysis first.");
        return;
    }

    output.innerHTML = `
        <div class="ai-loading">
            <i class="fa-solid fa-brain fa-beat"></i>
            <h3>TerraMind AI is analyzing...</h3>
            <p>Combining weather, satellite and historical environmental data.</p>
        </div>
    `;

    try {

        const latitude = selectedLocation.latitude;
        const longitude = selectedLocation.longitude;

        const params = new URLSearchParams({
    latitude: latitude,
    longitude: longitude,
    location_name: selectedLocation.name || "",
    district: selectedLocation.district || "",
    state: selectedLocation.state || ""
});

const response = await fetch(
    `${API_BASE}/api/v1/agent/analyze?${params.toString()}`,
    {
        method: "POST"
    }
);

        if (!response.ok) {
            throw new Error("AI analysis request failed");
        }

        const data = await response.json();
        const analysis = data.ai_analysis || {};

        const explanation =
            analysis.ai_explanation ||
            "No AI analysis was returned.";

        output.innerHTML = `
            <div class="ai-report">

                <div class="ai-report-meta">
                    <span>
                        <i class="fa-solid fa-location-dot"></i>
                        ${escapeHTML(selectedLocation.name || "Selected location")}
                    </span>

                    <span>
                        <i class="fa-solid fa-microchip"></i>
                        ${escapeHTML(analysis.model || "AI Model")}
                    </span>
                </div>

                <div class="ai-report-content">
                    ${formatAIReport(explanation)}
                </div>

                ${renderImpactAssessment(data.impact_assessment)}

                <div class="ai-disclaimer">
                    <i class="fa-solid fa-circle-info"></i>
                    This AI analysis is for environmental intelligence and
                    decision support. It is not an official flood warning.
                </div>

            </div>
        `;

        showToast("AI intelligence report generated successfully.");

    } catch (error) {

        console.error(error);

        output.innerHTML = `
            <div class="empty-ai">
                <i class="fa-solid fa-triangle-exclamation"></i>
                <h3>AI analysis unavailable</h3>
                <p>Please make sure the TerraMind backend and Ollama are running.</p>
            </div>
        `;

        showToast("Unable to generate the AI report.");
    }
}


function formatAIReport(text) {

    const safeText = escapeHTML(text);

    return safeText
        .replace(/\*\*(.*?)\*\*/g, "<h3>$1</h3>")
        .replace(/\n\n/g, "</p><p>")
        .replace(/^/, "<p>")
        .replace(/$/, "</p>");
}
// ============================================================
// HELPERS
// ============================================================

function getWeatherCondition(code) {

    const conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Foggy conditions",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Light rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Light snowfall",
        80: "Rain showers",
        81: "Moderate rain showers",
        82: "Heavy rain showers",
        95: "Thunderstorm"
    };

    return conditions[code] || "Live weather monitoring";
}


function formatDateTime(value) {

    try {

        return new Date(value)
            .toLocaleString("en-IN", {
                dateStyle: "medium",
                timeStyle: "short"
            });

    } catch {

        return value;

    }

}


function escapeHTML(value) {

    const div = document.createElement("div");

    div.textContent =
        value === null || value === undefined
            ? ""
            : String(value);

    return div.innerHTML;
}






// ============================================================
// TERRAMIND FLOOD ALERT DASHBOARD
// ============================================================

let floodIndiaMap = null;
let floodMapLayer = null;
let cachedFloodAlerts = [];
let satelliteCandidateLayer = null;
let satelliteCandidatesLoaded = false;

function getAlertRiskStyle(risk) {

    const styles = {
        HIGH: { color: "#ef4444", label: "HIGH RISK" },
        MODERATE: { color: "#facc15", label: "MODERATE RISK" },
        LOW: { color: "#22c55e", label: "LOW RAINFALL RISK" }
    };

    return styles[risk] || {
        color: "#9ca3af",
        label: "INSUFFICIENT DATA"
    };
}


function initializeFloodIndiaMap() {

    const mapElement = document.getElementById("floodIndiaMap");

    if (!mapElement || typeof L === "undefined") {
        return;
    }

    if (!floodIndiaMap) {

        floodIndiaMap = L.map("floodIndiaMap").setView(
            [22.5, 79.0],
            4.5
        );

        const streetTiles = L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            { attribution: "&copy; OpenStreetMap contributors", maxZoom: 19, crossOrigin: true }
        );
        const satelliteTiles = L.tileLayer(
            "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            { attribution: "Tiles &copy; Esri", maxZoom: 19, crossOrigin: true }
        );
        window.terraMapBases = { street: streetTiles, satellite: satelliteTiles };
        let tileFallbackUsed = false;
        satelliteTiles.on("tileerror", () => {
            if (tileFallbackUsed) return;
            tileFallbackUsed = true;
            if (floodIndiaMap.hasLayer(satelliteTiles)) {
                floodIndiaMap.removeLayer(satelliteTiles);
                streetTiles.addTo(floodIndiaMap);
                const satelliteButton = document.getElementById("satelliteLayerBtn");
                const streetButton = document.getElementById("streetLayerBtn");
                satelliteButton?.classList.remove("active");
                streetButton?.classList.add("active");
                showToast("Satellite tiles unavailable; switched to street map.");
            }
        });
        satelliteTiles.addTo(floodIndiaMap);
        floodMapLayer = L.layerGroup().addTo(floodIndiaMap);
    }

    setTimeout(() => floodIndiaMap.invalidateSize(), 150);
}



// ============================================================
// SATELLITE INUNDATION CANDIDATES
// ============================================================

async function loadSatelliteCandidates() {

    initializeFloodIndiaMap();

    if (!floodIndiaMap) {
        showToast("Map is not available.");
        return;
    }

    if (satelliteCandidatesLoaded && satelliteCandidateLayer) {
        satelliteCandidateLayer.addTo(floodIndiaMap);
        return;
    }

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/api/v1/satellite/chennai/candidates"
        );

        if (!response.ok) {
            throw new Error("Unable to retrieve satellite candidates.");
        }

        const geojson = await response.json();

        satelliteCandidateLayer = L.geoJSON(geojson, {

            style: {
                color: "#f97316",
                weight: 2,
                fillColor: "#fb923c",
                fillOpacity: 0.35
            },

            onEachFeature: function (feature, layer) {

                layer.bindPopup(
                    "<strong>Potential Inundation Candidate</strong>" +
                    "<br>Location: Chennai" +
                    "<br>Status: Unvalidated satellite detection" +
                    "<br><small>This is not a confirmed flood location.</small>"
                );

            }

        });

        satelliteCandidateLayer.addTo(floodIndiaMap);
        satelliteCandidatesLoaded = true;

        const count = Array.isArray(geojson.features)
            ? geojson.features.length
            : 0;

        showToast(
            `${count} potential satellite candidate regions loaded.`
        );

    } catch (error) {

        console.error("Satellite candidate loading failed:", error);
        showToast("Unable to load satellite candidate regions.");

    }
}


function renderFloodMap(alerts) {

    cachedFloodAlerts = Array.isArray(alerts) ? alerts : [];
    initializeFloodIndiaMap();

    if (!floodIndiaMap || !floodMapLayer) {
        return;
    }

    floodMapLayer.clearLayers();

    // Keep only the latest assessment for each coordinate.
    const latestByLocation = new Map();

    alerts.forEach(alert => {

        const key =
            `${Number(alert.latitude).toFixed(4)},` +
            `${Number(alert.longitude).toFixed(4)}`;

        if (!latestByLocation.has(key)) {
            latestByLocation.set(key, alert);
        }
    });

    const locations = Array.from(latestByLocation.values());

    locations.forEach(alert => {

        const latitude = Number(alert.latitude);
        const longitude = Number(alert.longitude);

        if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
            return;
        }

        if (latitude < 6 || latitude > 38 || longitude < 68 || longitude > 98) {
            return;
        }

        const style = getAlertRiskStyle(alert.risk_level);

        const marker = L.circleMarker(
            [latitude, longitude],
            {
                radius: 9,
                color: style.color,
                fillColor: style.color,
                fillOpacity: 0.85,
                weight: 2
            }
        );

        const place = escapeHTML(alert.location_name || "Unknown location");
        const district = escapeHTML(alert.district || "");
        const state = escapeHTML(alert.state || "");
        const explanation = escapeHTML(alert.explanation || "No explanation available.");

        marker.on("click", () => {
            selectedLocation = {
                name: alert.location_name || "Analyzed location",
                district: alert.district || "",
                state: alert.state || "",
                latitude,
                longitude
            };
            renderCommandSelectedLocation(selectedLocation);
        });

        marker.bindPopup(`
            <div class="flood-map-popup">
                <strong>${place}</strong>
                <p>${district}${district && state ? ", " : ""}${state}</p>
                <b style="color:${style.color}">${style.label}</b>
                <p>Current rainfall: ${alert.current_rainfall_mm ?? "--"} mm</p>
                <p>24-hour forecast: ${alert.forecast_rainfall_mm ?? "--"} mm</p>
                <p>${explanation}</p>
                <small>${formatDateTime(alert.created_at)}</small>
            </div>
        `);

        marker.addTo(floodMapLayer);
    });

    document.getElementById("mapLocationCount").textContent =
        `${locations.length} analyzed locations`;
}



function renderRecentFloodAlerts(alerts) {

    const container = document.getElementById("recentFloodAlerts");

    if (!container) return;

    if (!alerts.length) {
        container.innerHTML = `
            <div class="alerts-empty">
                <i class="fa-solid fa-water"></i>
                <p>No saved flood assessments yet.</p>
                <small>Analyze a location to see it here.</small>
            </div>
        `;
        return;
    }

    // Keep only the latest assessment for each location.
    // API returns alerts ordered newest first.
    const latestByLocation = new Map();

    alerts.forEach(alert => {

        const key =
            `${Number(alert.latitude).toFixed(4)},` +
            `${Number(alert.longitude).toFixed(4)}`;

        if (!latestByLocation.has(key)) {
            latestByLocation.set(key, alert);
        }
    });

    const latestAlerts = Array.from(latestByLocation.values());

    container.innerHTML = latestAlerts.slice(0, 8).map(alert => {

        const style = getAlertRiskStyle(alert.risk_level);

        return `
            <button type="button" class="recent-alert-item"
                data-alert-id="${Number(alert.id) || 0}"
                style="width:100%;text-align:left;color:inherit;cursor:pointer">

                <div class="recent-alert-indicator"
                     style="background:${style.color}"></div>

                <div class="recent-alert-details">

                    <strong>${escapeHTML(alert.location_name)}</strong>

                    <span>
                        ${escapeHTML(alert.district || "")}
                        ${alert.state ? ", " + escapeHTML(alert.state) : ""}
                    </span>

                    <small>
                        Current: ${alert.current_rainfall_mm ?? "--"} mm
                        &nbsp;|&nbsp;
                        Forecast: ${alert.forecast_rainfall_mm ?? "--"} mm
                    </small>

                    <small>${escapeHTML(formatDateTime(alert.created_at))}</small>

                </div>

                <span class="recent-alert-risk"
                      style="color:${style.color}">
                    ${style.label}
                </span>

            </button>
        `;
    }).join("");

    // Preserve location selection when clicking an assessment.
    container.querySelectorAll("[data-alert-id]").forEach(card => {

        card.addEventListener("click", () => {

            const selected = latestAlerts.find(
                item => Number(item.id) === Number(card.dataset.alertId)
            );

            if (!selected) return;

            selectedLocation = {
                name: selected.location_name || "Analyzed location",
                district: selected.district || "",
                state: selected.state || "",
                latitude: Number(selected.latitude),
                longitude: Number(selected.longitude)
            };

            renderCommandSelectedLocation(selectedLocation);

            if (floodIndiaMap) {
                floodIndiaMap.setView(
                    [selectedLocation.latitude, selectedLocation.longitude],
                    10
                );
            }
        });
    });
}



async function loadFloodAlerts() {

    const container = document.getElementById("recentFloodAlerts");
    initializeFloodIndiaMap();
    checkBackendStatus();

    if (!container) return;

    try {

        const response = await fetch(
            `${API_BASE}/api/v1/flood/alerts?limit=100`
        );

        if (!response.ok) {
            throw new Error("Unable to retrieve saved flood alerts.");
        }

        const data = await response.json();
        const alerts = data.alerts || [];
        // Keep only the latest assessment for each geographic location.
const latestByLocation = new Map();

alerts.forEach(alert => {
    const key =
        `${Number(alert.latitude).toFixed(4)},` +
        `${Number(alert.longitude).toFixed(4)}`;

    if (!latestByLocation.has(key)) {
        latestByLocation.set(key, alert);
    }
});

const uniqueAlerts = Array.from(latestByLocation.values());

        const count = risk =>
            alerts.filter(alert => alert.risk_level === risk).length;

        const highCount = document.getElementById("highAlertCount");
        const moderateCount = document.getElementById("moderateAlertCount");
        const lowCount = document.getElementById("lowAlertCount");
        const unknownCount = document.getElementById("unknownAlertCount");
        if (highCount) highCount.textContent = count("HIGH");
        if (moderateCount) moderateCount.textContent = count("MODERATE");
        if (lowCount) lowCount.textContent = count("LOW");
        if (unknownCount) unknownCount.textContent = alerts.filter(alert =>
            !["HIGH", "MODERATE", "LOW"].includes(alert.risk_level)
        ).length;

        renderRecentFloodAlerts(alerts);
        renderFloodMap(alerts);
        const incidentCount = document.getElementById("activeIncidentCount");
        if (incidentCount) incidentCount.textContent = String(uniqueAlerts.length);
        if (alerts.length && !latestAnalysis) {
            const newest = alerts[0];
            renderCommandSelectedLocation({name:newest.location_name,district:newest.district,state:newest.state,latitude:newest.latitude,longitude:newest.longitude});
            renderCommandAnalysis({current_rainfall_mm:newest.current_rainfall_mm,forecast_rainfall_mm:newest.forecast_rainfall_mm,historical_flood_count:newest.historical_flood_count,risk_level:newest.risk_level,explanation:newest.explanation});
        }

        const updated = document.getElementById("alertLastUpdated");
        if (updated) updated.textContent = `Updated ${new Date().toLocaleTimeString("en-IN")}`;

    } catch (error) {

        console.error("Flood alert loading error:", error);

        container.innerHTML = `
            <div class="alerts-empty">
                <p>Unable to load saved assessments.</p>
                <small>Check that the backend is running.</small>
            </div>
        `;
    }
}


// Refresh button.
const refreshFloodAlertsButton =
    document.getElementById("refreshFloodAlerts");

if (refreshFloodAlertsButton) {
    refreshFloodAlertsButton.addEventListener(
        "click",
        loadFloodAlerts
    );
}


// Backend connection indicator. Never label the system online without a successful check.
async function checkBackendStatus() {
    const label = document.getElementById("systemConnectionLabel");
    const dot = document.getElementById("systemConnectionDot");
    const dbLabel = document.getElementById("databaseConnectionStatus");
    try {
        const response = await fetch(`${API_BASE}/health`, { cache: "no-store" });
        if (!response.ok) throw new Error("Backend health check failed");
        if (label) label.textContent = "Backend connected";
        if (dot) dot.classList.add("connected");
        if (dbLabel) dbLabel.textContent = "API reachable";
    } catch (error) {
        if (label) label.textContent = "Backend offline";
        if (dot) dot.classList.remove("connected");
        if (dbLabel) dbLabel.textContent = "Backend unavailable";
    }
}

// Initial dashboard loading.
initializeFloodIndiaMap();
loadFloodAlerts();


// ============================================================
// TERRAMIND COMMAND-CENTRE INTERACTIONS
// ============================================================
function renderCommandSelectedLocation(location) {
    const name = document.getElementById("commandSelectedPlace");
    if (name) name.innerHTML = `<strong>${escapeHTML(location.name || "Selected location")}</strong><span>${escapeHTML([location.subdistrict, location.district, location.state].filter(Boolean).join(", ") || location.country || "India")}</span>`;
    const lat = document.getElementById("cmdLatitude");
    const lon = document.getElementById("cmdLongitude");
    const latitude = Number(location.latitude);
    const longitude = Number(location.longitude);
    if (lat) lat.textContent = Number.isFinite(latitude) ? latitude.toFixed(5) : "--";
    if (lon) lon.textContent = Number.isFinite(longitude) ? longitude.toFixed(5) : "--";
    const coords = document.getElementById("commandMapCoordinates");
    if (coords) coords.textContent = Number.isFinite(latitude) && Number.isFinite(longitude) ? `${latitude.toFixed(5)}°, ${longitude.toFixed(5)}°` : "Coordinates unavailable";
    if (floodIndiaMap && Number.isFinite(latitude) && Number.isFinite(longitude)) floodIndiaMap.setView([latitude, longitude], 10);
    const rec = document.getElementById("cmdRecommendation");
    if (rec) rec.textContent = `${location.name || "Selected location"} is selected. Run a flood assessment to retrieve rainfall, forecast and historical-event evidence.`;
}

function renderCommandAnalysis(data) {
    const flood = data.flood_analysis || data;
    const currentValue = data.current_rainfall_mm ?? data.current_weather?.rain ?? null;
    const forecastValue = data.forecast_rainfall_next_24_hours_mm ?? data.forecast_rainfall_mm ?? null;
    const riskValue = flood.risk_level || data.risk_level || "UNKNOWN";
    const explanation = flood.explanation || data.explanation || "No explanation returned";
    const current = document.getElementById("cmdCurrentRain");
    const risk = document.getElementById("cmdRisk");
    const forecast = document.getElementById("cmdForecast");
    const history = document.getElementById("cmdHistory");
    if (current) current.textContent = currentValue == null ? "Unavailable" : `${Number(currentValue).toFixed(1)} mm`;
    if (forecast) forecast.textContent = forecastValue == null ? "Unavailable" : `${Number(forecastValue).toFixed(1)} mm`;
    if (history) history.textContent = data.historical_flood_count == null ? "--" : String(data.historical_flood_count);
    if (risk) risk.textContent = riskValue === "INSUFFICIENT_DATA" ? "Unavailable" : riskValue;
    const caption = document.getElementById("cmdRiskCaption");
    if (caption) caption.textContent = explanation;
    const note = document.getElementById("cmdEvidenceNote");
    const scenes = data.satellite_history;
    if (note) note.textContent = Array.isArray(scenes) && scenes.length
        ? `Satellite archive metadata available (${scenes.length} grid observation records). Scene availability is not proof of flooding.`
        : "Rainfall assessment returned. Satellite flood classification has not yet been run.";
    const satStatus = document.getElementById("cmdSatelliteStatus");
    if (satStatus) satStatus.textContent = Array.isArray(scenes) && scenes.length ? "Metadata available" : "Not queried";
    const recommendation = document.getElementById("cmdRecommendation");
    if (recommendation) recommendation.textContent = explanation;
}

async function runCommandSearch() {
    const input = document.getElementById("commandSearchInput");
    const box = document.getElementById("commandSearchResults");
    const query = input?.value.trim();
    if (!query || query.length < 2) { showToast("Enter at least two characters to search."); return; }
    box.classList.add("open");
    box.innerHTML = `<div class="command-search-result"><span>Searching locations...</span></div>`;
    try {
        const response = await fetch(`${API_BASE}/api/v1/location/search?q=${encodeURIComponent(query)}`);
        if (!response.ok) throw new Error("Location search failed");
        const data = await response.json();
        const results = data.results || [];
        if (!results.length) { box.innerHTML = `<div class="command-search-result"><span>No matching locations found.</span></div>`; return; }
        box.innerHTML = results.slice(0, 8).map((item, i) => `<button class="command-search-result" data-result-index="${i}"><strong>${escapeHTML(item.name || "Unknown location")}</strong><span>${escapeHTML([item.subdistrict,item.district,item.state,item.country].filter(Boolean).join(", "))}</span></button>`).join("");
        box.querySelectorAll("[data-result-index]").forEach(button => button.addEventListener("click", () => {
            const location = results[Number(button.dataset.resultIndex)];
            selectLocation(location);
            box.classList.remove("open");
            box.innerHTML = "";
            if (floodIndiaMap) setTimeout(() => floodIndiaMap.invalidateSize(), 100);
        }));
    } catch (error) {
        console.error("Command location search:", error);
        box.innerHTML = `<div class="command-search-result"><span>Search failed. Check backend connection.</span></div>`;
    }
}

const commandSearchButton = document.getElementById("commandSearchButton");
const commandSearchInput = document.getElementById("commandSearchInput");
const commandGlobalSearch = document.getElementById("commandGlobalSearch");
commandGlobalSearch?.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        if (commandSearchInput) commandSearchInput.value = commandGlobalSearch.value;
        runCommandSearch();
    }
});
commandSearchButton?.addEventListener("click", runCommandSearch);
commandSearchInput?.addEventListener("keydown", event => { if (event.key === "Enter") runCommandSearch(); });
[commandGlobalSearch, commandSearchInput, locationInput].forEach(input => {
    if (input) {
        input.setAttribute("autocomplete", "off");
        input.setAttribute("autocorrect", "off");
        input.setAttribute("spellcheck", "false");
    }
});
document.addEventListener("click", event => {
    const box = document.getElementById("commandSearchResults");
    if (box && !event.target.closest(".map-search-wrap")) box.classList.remove("open");
});

document.getElementById("commandAnalyzeBtn")?.addEventListener("click", () => analyzeSelectedLocation());
document.getElementById("commandAnalyze")?.addEventListener("click", () => analyzeSelectedLocation());
document.getElementById("commandRefresh")?.addEventListener("click", () => loadFloodAlerts());
document.getElementById("commandAddLocation")?.addEventListener("click", () => { openPage("location"); document.getElementById("locationInput")?.focus(); });

document.getElementById("streetLayerBtn")?.addEventListener("click", () => {
    if (!floodIndiaMap || !window.terraMapBases) return;
    floodIndiaMap.removeLayer(window.terraMapBases.satellite);
    window.terraMapBases.street.addTo(floodIndiaMap);
    document.getElementById("streetLayerBtn").classList.add("active");
    document.getElementById("satelliteLayerBtn").classList.remove("active");
});
document.getElementById("satelliteLayerBtn")?.addEventListener("click", () => {
    if (!floodIndiaMap || !window.terraMapBases) return;
    floodIndiaMap.removeLayer(window.terraMapBases.street);
    window.terraMapBases.satellite.addTo(floodIndiaMap);
    document.getElementById("satelliteLayerBtn").classList.add("active");
    document.getElementById("streetLayerBtn").classList.remove("active");
});
document.getElementById("riskLayerBtn")?.addEventListener("click", () => document.getElementById("commandMapLegend")?.classList.toggle("legend-hidden"));


document.getElementById("candidateLayerBtn")?.addEventListener("click", async () => {

    initializeFloodIndiaMap();

    if (!floodIndiaMap) return;

    const button = document.getElementById("candidateLayerBtn");

    if (
        satelliteCandidateLayer &&
        floodIndiaMap.hasLayer(satelliteCandidateLayer)
    ) {
        floodIndiaMap.removeLayer(satelliteCandidateLayer);
        button.classList.remove("active");
        showToast("Satellite candidates hidden.");
        return;
    }

    await loadSatelliteCandidates();

    if (
        satelliteCandidateLayer &&
        floodIndiaMap.hasLayer(satelliteCandidateLayer)
    ) {
        button.classList.add("active");

        const bounds = satelliteCandidateLayer.getBounds();

        if (bounds.isValid()) {
            floodIndiaMap.fitBounds(bounds.pad(0.15), {
                maxZoom: 12
            });
        }
    }
});


// Dashboard modes perform real actions rather than only changing their active styling.
document.querySelectorAll(".mode-btn").forEach(button => button.addEventListener("click", async () => {
    document.querySelectorAll(".mode-btn").forEach(item => item.classList.remove("active"));
    button.classList.add("active");
    const mode = button.dataset.mode;

    if (mode === "Overview") {
        openPage("dashboard");
        await loadFloodAlerts();
        if (floodIndiaMap) floodIndiaMap.setView([22.5, 79.0], 4.5);
        showToast("Overview refreshed: India-wide assessment view.");
        return;
    }

    if (mode === "Monitoring") {
        openPage("dashboard");
        await loadFloodAlerts();
        const valid = cachedFloodAlerts.filter(item => Number.isFinite(Number(item.latitude)) && Number.isFinite(Number(item.longitude)));
        if (floodIndiaMap && valid.length === 1) floodIndiaMap.setView([Number(valid[0].latitude), Number(valid[0].longitude)], 8);
        else if (floodIndiaMap && valid.length > 1) {
            const bounds = L.latLngBounds(valid.map(item => [Number(item.latitude), Number(item.longitude)]));
            floodIndiaMap.fitBounds(bounds.pad(0.25), { maxZoom: 9 });
        }
        showToast(`${valid.length} saved location assessment(s) loaded.`);
        return;
    }

    if (mode === "Analysis") {
        if (selectedLocation) {
            openPage("flood");
            await analyzeSelectedLocation();
        } else {
            openPage("location");
            showToast("Select a location before starting an analysis.");
        }
    }
}));

function updateCommandClock() {
    const clock = document.getElementById("commandClock");
    if (clock) clock.textContent = new Date().toLocaleTimeString("en-IN", {hour:"2-digit",minute:"2-digit",second:"2-digit"});
}
updateCommandClock();
setInterval(updateCommandClock, 1000);
function renderImpactAssessment(assessment) {

    if (!assessment || typeof assessment !== "object") {
        return `
            <div class="impact-assessment">
                <h3>Structured Impact Assessment</h3>
                <p>Assessment data is not available.</p>
            </div>
        `;
    }

    const sections = [
        ["rainfall_assessment", "Rainfall Assessment"],
        ["historical_impact", "Historical Flood Evidence"],
        ["satellite_impact", "Satellite Impact Evidence"],
        ["geographic_summary", "Geographic Summary"],
        ["limitations", "Assessment Limitations"]
    ];

    function formatValue(value) {

        if (value === null || value === undefined) {
            return "Not available";
        }

        if (typeof value === "boolean") {
            return value ? "Yes" : "No";
        }

        if (Array.isArray(value)) {
            return value.length
                ? value.map(item => formatValue(item)).join(", ")
                : "None recorded";
        }

        if (typeof value === "object") {
            return Object.entries(value)
                .map(([key, item]) =>
                    `<div class="impact-detail">
                        <span>${escapeHTML(key.replaceAll("_", " "))}</span>
                        <strong>${formatValue(item)}</strong>
                    </div>`
                )
                .join("");
        }

        return escapeHTML(String(value));
    }

    const sectionHTML = sections.map(([key, title]) => {

        const value = assessment[key];

        if (value === undefined || value === null) {
            return "";
        }

        return `
            <details class="impact-section" open>
                <summary>${escapeHTML(title)}</summary>
                <div class="impact-section-content">
                    ${formatValue(value)}
                </div>
            </details>
        `;

    }).join("");

    return `
        <div class="impact-assessment">

            <div class="impact-assessment-heading">
                <h3>Structured Flood Impact Assessment</h3>
                <span>${escapeHTML(assessment.status || "Available")}</span>
            </div>

            <p class="impact-assessment-type">
                ${escapeHTML(
                    assessment.assessment_type ||
                    "Evidence-based environmental assessment"
                )}
            </p>

            ${sectionHTML}

            <p class="impact-assessment-disclaimer">
                This assessment presents available evidence. Satellite
                candidate regions are not confirmed flood observations
                or official warnings.
            </p>

        </div>
    `;
}


