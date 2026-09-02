const resultsDiv = document.getElementById("results");
const locationStatus = document.getElementById("locationStatus");
const postcodeRow = document.getElementById("postcodeRow");
const postcodeInput = document.getElementById("postcode");
const locationSeg = document.getElementById("locationSeg");
const sortBySelect = document.getElementById("sortBy");
const valueRow = document.getElementById("valueRow");
const avgMpgInput = document.getElementById("avgMpg");
const fillLitresInput = document.getElementById("fillLitres");

let currentCoords = null;

const PAGE_SIZE = 10;
let allResults = [];
let visibleCount = 0;
let currentSortBy = "price";

function selectedRadio(name) {
  const el = document.querySelector(`input[name="${name}"]:checked`);
  return el ? el.value : null;
}

function setLocationStatus(msg, isError) {
  locationStatus.textContent = msg || "";
  locationStatus.classList.toggle("error", !!isError);
}

function useCurrentLocation() {
  if (!navigator.geolocation) {
    setLocationStatus("Location isn't available on this device.", true);
    return;
  }
  setLocationStatus("Locating…", false);
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      currentCoords = { lat: pos.coords.latitude, lon: pos.coords.longitude };
      setLocationStatus("", false);
      performSearch();
    },
    () => {
      currentCoords = null;
      setLocationStatus("Couldn't get your location — try a postcode instead.", true);
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

locationSeg.querySelectorAll('input[name="locationType"]').forEach(el => {
  el.addEventListener("change", () => {
    if (el.value === "current") {
      postcodeRow.hidden = true;
      useCurrentLocation();
    } else {
      postcodeRow.hidden = false;
      setLocationStatus("", false);
      postcodeInput.focus();
      if (postcodeInput.value.trim()) performSearch();
      else resultsDiv.innerHTML = "";
    }
  });
});

function updateValueRowVisibility() {
  valueRow.hidden = sortBySelect.value !== "value";
}

document.getElementById("fuelType").addEventListener("change", performSearch);
sortBySelect.addEventListener("change", () => {
  updateValueRowVisibility();
  performSearch();
});

let debounceTimer;
function debouncedSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(performSearch, 500);
}
postcodeInput.addEventListener("input", debouncedSearch);
document.getElementById("searchDist").addEventListener("input", debouncedSearch);
avgMpgInput.addEventListener("input", debouncedSearch);
fillLitresInput.addEventListener("input", debouncedSearch);

function formatPrice(price) {
  return Number(price).toFixed(1);
}

function formatRelativeTime(dateStr) {
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return null;

  const diffMin = Math.round((Date.now() - date.getTime()) / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin} min${diffMin === 1 ? "" : "s"} ago`;

  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr} hour${diffHr === 1 ? "" : "s"} ago`;

  const diffDay = Math.round(diffHr / 24);
  if (diffDay < 7) return `${diffDay} day${diffDay === 1 ? "" : "s"} ago`;

  return `on ${date.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}`;
}

function performSearch() {
  const locationType = selectedRadio("locationType");
  const sortBy = sortBySelect.value;
  const params = { fuelType: document.getElementById("fuelType").value,
                    searchDist: document.getElementById("searchDist").value,
                    sortBy };

  if (sortBy === "value") {
    params.avgMpg = avgMpgInput.value;
    params.fillLitres = fillLitresInput.value;
  }

  if (locationType === "current") {
    if (!currentCoords) return;
    params.locationType = "coords";
    params.lat = currentCoords.lat;
    params.lon = currentCoords.lon;
  } else {
    const postcode = postcodeInput.value.trim();
    if (!postcode) { resultsDiv.innerHTML = ""; return; }
    params.locationType = "postcode";
    params.postcode = postcode;
  }

  resultsDiv.innerHTML = '<p class="state-msg">Searching…</p>';

  fetch(`/fuelSearch?${new URLSearchParams(params)}`)
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
      if (!ok) {
        resultsDiv.innerHTML = `<p class="state-msg error">${data.error}</p>`;
        return;
      }

      if (data.length === 0) {
        resultsDiv.innerHTML = '<p class="state-msg">No results found.</p>';
        return;
      }

      currentSortBy = params.sortBy;
      allResults = data;
      visibleCount = Math.min(PAGE_SIZE, allResults.length);
      renderResults();
    })
    .catch(() => {
      resultsDiv.innerHTML = '<p class="state-msg error">Something went wrong. Please try again.</p>';
    });
}

function renderResults() {
  const bestLabel = currentSortBy === "distance" ? "Nearest" : currentSortBy === "value" ? "Best value" : "Cheapest";
  const visible = allResults.slice(0, visibleCount);

  const cards = visible.map((station, i) => `
    <div class="result-card ${i === 0 ? "is-best" : ""}" data-id="${station.id}" data-distance="${station.distance}">
      <div class="result-rank">${i + 1}</div>
      <div class="result-main">
        <div class="result-brand">${station.brand_name}${i === 0 ? `<span class="tag-best">${bestLabel}</span>` : ""}</div>
        <div class="result-meta">${station.distance.toFixed(1)} mi away</div>
        ${currentSortBy === "value" && station.fill_cost != null ? `<div class="result-fill">~£${station.fill_cost.toFixed(2)} to fill up, drive there included</div>` : ""}
      </div>
      <div class="result-price">${formatPrice(station.price)}<small>p/L</small></div>
    </div>
  `).join("");

  const loadMore = visibleCount < allResults.length
    ? `<button type="button" class="btn-load" id="loadMoreBtn">Load more (${allResults.length - visibleCount} left)</button>`
    : "";

  resultsDiv.innerHTML = cards + loadMore;
}

resultsDiv.addEventListener("click", (e) => {
  if (e.target.closest("#loadMoreBtn")) {
    visibleCount = Math.min(visibleCount + PAGE_SIZE, allResults.length);
    renderResults();
    return;
  }
  const card = e.target.closest(".result-card");
  if (card) openStationModal(card.dataset.id, parseFloat(card.dataset.distance));
});

const stationModal = document.getElementById("stationModal");
const stationModalSheet = document.getElementById("stationModalSheet");
const FUEL_LABELS = { e5: "E5", e10: "E10", b7s: "B7 Diesel", b7p: "B7 Premium" };
const AMENITY_LABELS = { toilets: "Toilets", car_wash: "Car wash", adblue: "AdBlue", screenwash: "Screenwash", water: "Water" };

function closeStationModal() {
  stationModal.hidden = true;
  stationModalSheet.innerHTML = "";
}

stationModal.addEventListener("click", (e) => {
  if (e.target === stationModal) closeStationModal();
});
stationModalSheet.addEventListener("click", (e) => {
  if (e.target.closest("#modalCloseBtn")) closeStationModal();
});

function openStationModal(stationId, listDistance) {
  stationModalSheet.innerHTML = '<button type="button" class="modal-close" id="modalCloseBtn">✕</button><p class="state-msg">Loading…</p>';
  stationModal.hidden = false;

  fetch(`/station/${encodeURIComponent(stationId)}`)
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
      if (!ok) {
        stationModalSheet.innerHTML = `<button type="button" class="modal-close" id="modalCloseBtn">✕</button><p class="state-msg error">${data.error}</p>`;
        return;
      }

      const address = [data.address_line_1, data.address_line_2, data.city, data.county, data.postcode]
        .filter(Boolean).join(", ");

      const currentFuel = document.getElementById("fuelType").value;
      const priceGrid = Object.entries(FUEL_LABELS).map(([key, label]) => `
        <div class="price-cell ${key === currentFuel ? "is-selected" : ""}">
          <div class="fuel-label">${label}</div>
          <div class="fuel-price">${data.prices[key] ? formatPrice(data.prices[key]) : "—"}</div>
        </div>
      `).join("");

      const activeAmenities = Object.keys(AMENITY_LABELS).filter(k => data.amenities[k]);
      const amenitiesHtml = activeAmenities.length
        ? activeAmenities.map(k => `<span class="amenity-tag">${AMENITY_LABELS[k]}</span>`).join("")
        : `<span class="amenity-tag">No listed amenities</span>`;

      const mapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(data.latitude + "," + data.longitude)}`;

      const updatedFor = data.prices_updated[currentFuel]
        || Object.values(data.prices_updated).filter(Boolean).sort((a, b) => new Date(b) - new Date(a))[0];
      const updatedLabel = updatedFor ? formatRelativeTime(updatedFor) : null;

      stationModalSheet.innerHTML = `
        <button type="button" class="modal-close" id="modalCloseBtn">✕</button>
        <h2 class="modal-brand">${data.brand_name}</h2>
        ${data.is24hr ? '<span class="modal-badge-24hr">Open 24 hours</span>' : ""}
        <div class="modal-address">${address}</div>
        ${Number.isFinite(listDistance) ? `<div class="result-meta">${listDistance.toFixed(1)} mi away</div>` : ""}

        <div class="modal-section-title">Fuel prices (p/L)</div>
        <div class="price-grid">${priceGrid}</div>

        <div class="modal-section-title">Amenities</div>
        <div class="amenity-list">${amenitiesHtml}</div>

        <a class="go-now-btn" href="${mapsUrl}" target="_blank" rel="noopener">Go Now</a>

        ${updatedLabel ? `<div class="modal-updated">Prices updated ${updatedLabel}</div>` : ""}
      `;
    })
    .catch(() => {
      stationModalSheet.innerHTML = '<button type="button" class="modal-close" id="modalCloseBtn">✕</button><p class="state-msg error">Couldn\'t load station details.</p>';
    });
}

updateValueRowVisibility();
useCurrentLocation();
