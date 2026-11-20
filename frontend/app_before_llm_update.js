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

        const response = await fetch(
            `${API_BASE}/api/v1/flood/analyze/location?latitude=${latitude}&longitude=${longitude}`
        );

        if (!response.ok) {
            throw new Error("Flood analysis failed");
        }

        const data = await response.json();

        latestAnalysis = data;

        updateWeather(data);
        updateFloodAnalysis(data);
        updateSatelliteData(data);

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
            ? `${weather.temperature_2m}°C`
            : "--°C";


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


function generateAIInsight() {

    const output =
        document.getElementById("aiOutput");


    if (!selectedLocation || !latestAnalysis) {

        output.innerHTML = `
            <div class="empty-ai">
                <i class="fa-solid fa-location-dot"></i>
                <p>
                    Please select and analyze a location before
                    generating an AI insight.
                </p>
            </div>
        `;

        showToast("Please complete a location analysis first.");

        return;
    }


    const flood =
        latestAnalysis.flood_analysis || {};

    const weather =
        latestAnalysis.current_weather || {};


    const report = `
LOCATION INTELLIGENCE

TerraMind AI analyzed environmental conditions for
${selectedLocation.name}, ${selectedLocation.state || "India"}.

CURRENT ENVIRONMENT

The recorded temperature is ${weather.temperature_2m ?? "unavailable"}°C,
with relative humidity of ${weather.relative_humidity_2m ?? "unavailable"}%.

RAINFALL ASSESSMENT

Current rainfall is ${flood.current_rainfall_mm ?? "unavailable"} mm.
The estimated rainfall for the next 24 hours is
${flood.forecast_rainfall_mm ?? "unavailable"} mm.

FLOOD RISK

The current prototype assessment identifies the flood risk level as:
${flood.risk_level || "UNKNOWN"}.

${flood.explanation || ""}

HISTORICAL INTELLIGENCE

The system found ${latestAnalysis.historical_flood_count ?? 0}
nearby historical flood record(s).

RECOMMENDATION

This analysis is intended for environmental intelligence and
prototype decision support. Users should always verify important
weather and emergency information through official authorities.
    `.trim();


    output.innerHTML = `
        <div class="ai-report">
            ${escapeHTML(report)}
        </div>
    `;


    showToast("AI intelligence report generated.");

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