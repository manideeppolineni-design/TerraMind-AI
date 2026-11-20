// ============================================================
// TERRAMIND AI - FRONTEND APPLICATION
// ============================================================

const API_BASE = "http://127.0.0.1:8000";

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

    pageTitle.textContent = pageTitles[pageId] || "TerraMind AI";

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
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


document.getElementById("startAnalysis").addEventListener("click", () => {
    openPage("location");
});


// ============================================================
// DATE
// ============================================================

function updateDate() {

    const now = new Date();

    currentDate.textContent = now.toLocaleDateString(
        "en-IN",
        {
            day: "numeric",
            month: "short",
            year: "numeric"
        }
    );
}

updateDate();


// ============================================================
// TOAST MESSAGE
// ============================================================

function showToast(message) {

    const toast = document.getElementById("toast");

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


searchLocationButton.addEventListener("click", searchLocation);

locationInput.addEventListener("keydown", event => {

    if (event.key === "Enter") {
        searchLocation();
    }

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

    loading.classList.remove("hidden");

    resultsContainer.innerHTML = "";

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

        resultsContainer.innerHTML = `
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

        loading.classList.add("hidden");

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

    resultCount.textContent =
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

    document.getElementById(
        "selectedLocationContent"
    ).innerHTML = `

        <div class="selected-details">

            <h2>${escapeHTML(location.name || "Selected Location")}</h2>

            <p style="color:#91a6ad;font-size:13px;">
                ${escapeHTML(location.district || "")}
                ${location.state ? ", " + escapeHTML(location.state) : ""}
                ${location.country ? ", " + escapeHTML(location.country) : ""}
            </p>

            <div class="coordinate-box">

                <div>
                    <span>LATITUDE</span>
                    <strong>${location.latitude ?? "--"}</strong>
                </div>

                <div>
                    <span>LONGITUDE</span>
                    <strong>${location.longitude ?? "--"}</strong>
                </div>

            </div>

            <button
                class="primary-btn analyze-location-btn"
                id="analyzeSelectedLocation"
            >
                Analyze This Location
                <i class="fa-solid fa-arrow-right"></i>
            </button>

        </div>
    `;


    document.getElementById(
        "analyzeSelectedLocation"
    ).addEventListener("click", () => {

        analyzeSelectedLocation();

    });


    document.getElementById(
        "weatherLocationName"
    ).textContent =
        `${location.name}, ${location.state || location.country || ""}`;


    showToast(`${location.name} selected for analysis.`);

}


// ============================================================
// FLOOD ANALYSIS
// ============================================================

async function analyzeSelectedLocation() {

    if (!selectedLocation) {
        showToast("Please select a location first.");
        return;
    }

    openPage("flood");

    document.getElementById("floodEmpty")
        .classList.remove("hidden");

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


document.getElementById("refreshWeather")
    .addEventListener("click", () => {

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


    document.getElementById("floodCurrentRain")
        .textContent =
            `${flood.current_rainfall_mm ?? "--"} mm`;


    document.getElementById("floodForecastRain")
        .textContent =
            `${flood.forecast_rainfall_mm ?? "--"} mm`;


    document.getElementById("floodTotalRain")
        .textContent =
            `${flood.total_rainfall_mm ?? "--"} mm`;


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
    } else if (riskLevel === "MEDIUM") {
        riskCircle.style.borderColor = "#f6a23a";
    } else if (riskLevel === "HIGH") {
        riskCircle.style.borderColor = "#ef6461";
    }

}


document.getElementById("runFloodAnalysis")
    .addEventListener("click", analyzeSelectedLocation);


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

document.getElementById("generateAI")
    .addEventListener("click", generateAIInsight);


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

        const response = await fetch(
            `${API_BASE}/api/v1/agent/analyze?latitude=${latitude}&longitude=${longitude}`,
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
                        ${escapeHTML(selectedLocation.name)}
                    </span>

                    <span>
                        <i class="fa-solid fa-microchip"></i>
                        ${escapeHTML(analysis.model || "AI Model")}
                    </span>
                </div>

                <div class="ai-report-content">
                    ${formatAIReport(explanation)}
                </div>

                <div class="ai-disclaimer">
                    <i class="fa-solid fa-circle-info"></i>
                    This AI analysis is for environmental intelligence and decision support.
                    It is not an official flood warning.
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

        L.tileLayer(
            "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            {
                attribution: "&copy; OpenStreetMap contributors",
                maxZoom: 18
            }
        ).addTo(floodIndiaMap);

        floodMapLayer = L.layerGroup().addTo(floodIndiaMap);
    }

    setTimeout(() => floodIndiaMap.invalidateSize(), 150);
}


function renderFloodMap(alerts) {

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

    container.innerHTML = alerts.slice(0, 8).map(alert => {

        const style = getAlertRiskStyle(alert.risk_level);

        return `
            <div class="recent-alert-item">
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
            </div>
        `;
    }).join("");
}


async function loadFloodAlerts() {

    const container = document.getElementById("recentFloodAlerts");

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

        const count = risk =>
            alerts.filter(alert => alert.risk_level === risk).length;

        document.getElementById("highAlertCount").textContent =
            count("HIGH");

        document.getElementById("moderateAlertCount").textContent =
            count("MODERATE");

        document.getElementById("lowAlertCount").textContent =
            count("LOW");

        document.getElementById("unknownAlertCount").textContent =
            alerts.filter(alert =>
                !["HIGH", "MODERATE", "LOW"].includes(alert.risk_level)
            ).length;

        renderRecentFloodAlerts(alerts);
        renderFloodMap(alerts);

        document.getElementById("alertLastUpdated").textContent =
            `Updated ${new Date().toLocaleTimeString("en-IN")}`;

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


// Initial dashboard loading.
loadFloodAlerts();
