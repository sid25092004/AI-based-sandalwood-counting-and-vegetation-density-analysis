import streamlit as st
import ee
import geemap
import folium
import numpy as np
import requests
import cv2

from PIL import Image
from io import BytesIO

# ==========================================
# INITIALIZE EARTH ENGINE
# ==========================================

ee.Initialize(project='sandalwood-project')

# ==========================================
# FOREST DATABASE
# ==========================================

forest_database = {

    # ======================================
    # PRIMARY SANDALWOOD BELT
    # ======================================

    "mysuru": {
        "forest_type": "sandalwood_belt",
        "ecology_score": 95
    },

    "mysore": {
        "forest_type": "sandalwood_belt",
        "ecology_score": 95
    },

    "chamarajanagar": {
        "forest_type": "sandalwood_belt",
        "ecology_score": 96
    },

    "hassan": {
        "forest_type": "sandalwood_belt",
        "ecology_score": 88
    },

    "kodagu": {
        "forest_type": "sandalwood_belt",
        "ecology_score": 85
    },

    "coorg": {
        "forest_type": "sandalwood_belt",
        "ecology_score": 85
    },

    # ======================================
    # HIGH SUITABILITY FORESTS
    # ======================================

    "bandipur": {
        "forest_type": "dry_deciduous",
        "ecology_score": 92
    },

    "bandipur national park": {
        "forest_type": "dry_deciduous",
        "ecology_score": 94
    },

    "nagarhole": {
        "forest_type": "mixed_forest",
        "ecology_score": 90
    },

    "nagarhole tiger reserve": {
        "forest_type": "mixed_forest",
        "ecology_score": 92
    },

    "mm hills": {
        "forest_type": "dry_deciduous",
        "ecology_score": 90
    },

    "male mahadeshwara": {
        "forest_type": "dry_deciduous",
        "ecology_score": 90
    },

    "sakleshpur": {
        "forest_type": "mixed_sandalwood_zone",
        "ecology_score": 72
    },

    "chikkamagaluru": {
        "forest_type": "mixed_sandalwood_zone",
        "ecology_score": 76
    },

    # ======================================
    # LOW SUITABILITY RAINFOREST
    # ======================================

    "agumbe": {
        "forest_type": "rainforest",
        "ecology_score": 35
    },

    "bhadra": {
        "forest_type": "rainforest",
        "ecology_score": 50
    },

    "kudremukh": {
        "forest_type": "rainforest",
        "ecology_score": 30
    },

    # ======================================
    # URBAN REGIONS
    # ======================================

    "bengaluru": {
        "forest_type": "urban",
        "ecology_score": 5
    },

    "bangalore": {
        "forest_type": "urban",
        "ecology_score": 5
    },

    "rv college of engineering": {
        "forest_type": "urban",
        "ecology_score": 2
    },

    "rvce": {
        "forest_type": "urban",
        "ecology_score": 2
    },

    "cubbon park": {
        "forest_type": "urban_greenery",
        "ecology_score": 8
    },

    "lalbagh": {
        "forest_type": "urban_greenery",
        "ecology_score": 8
    },

    "bannerghatta": {
        "forest_type": "urban_forest",
        "ecology_score": 30
    },

    "bannerghatta national park": {
        "forest_type": "urban_forest",
        "ecology_score": 35
    },

    "nandi hills": {
        "forest_type": "dry_mixed",
        "ecology_score": 45
    },

    "dharwad": {
        "forest_type": "semi_arid",
        "ecology_score": 30
    }
}

# ==========================================
# SOIL DATABASE
# ==========================================

soil_database = {

    "dry_deciduous": "Red Loamy Soil",

    "mixed_forest": "Red Sandy Loam",

    "sandalwood_belt": "Red Loamy Soil",

    "mixed_sandalwood_zone": "Red Sandy Loam",

    "rainforest": "Lateritic Soil",

    "urban": "Non-Forest Urban Soil",

    "urban_greenery": "Artificial Urban Soil",

    "urban_forest": "Mixed Forest Soil",

    "dry_mixed": "Dry Red Soil",

    "semi_arid": "Dry Gravelly Soil",

    "unknown": "Unknown Soil Type"
}

# ==========================================
# TITLE
# ==========================================

st.title("AI-Based Sandalwood Habitat Analysis")

st.write(
    "AI-assisted sandalwood habitat "
    "suitability analysis system using "
    "remote sensing and satellite analytics."
)

# ==========================================
# USER INPUT
# ==========================================

location = st.text_input(
    "Enter Karnataka Forest / Region",
    "Bandipur National Park"
)

radius_km = st.slider(
    "Search Radius (KM)",
    1,
    20,
    5
)

# ==========================================
# ANALYZE BUTTON
# ==========================================

if st.button("Analyze"):

    search_query = location + ", Karnataka, India"

    st.info(f"Analyzing: {search_query}")

    geo = geemap.geocode(search_query)

    if len(geo) == 0:

        st.error("Location not found")
        st.stop()

    lat = geo[0].lat
    lon = geo[0].lng

    radius_m = radius_km * 1000

    point = ee.Geometry.Point([lon, lat])

    aoi = point.buffer(radius_m)

    # ======================================
    # MAP DISPLAY
    # ======================================

    m = folium.Map(
        location=[lat, lon],
        zoom_start=11
    )

    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google'
    ).add_to(m)

    folium.Circle(
        radius=radius_m,
        location=[lat, lon],
        color='red',
        fill=True
    ).add_to(m)

    st.subheader("Satellite Analysis Region")

    st.components.v1.html(
        m._repr_html_(),
        height=500
    )

    # ======================================
    # SATELLITE IMAGE
    # ======================================

    collection = (
        ee.ImageCollection('COPERNICUS/S2_SR')
        .filterBounds(aoi)
        .filterDate('2025-01-01', '2025-03-01')
        .sort('CLOUDY_PIXEL_PERCENTAGE')
    )

    image = collection.first()

    # ======================================
    # NDVI
    # ======================================

    ndvi = image.normalizedDifference(
        ['B8', 'B4']
    )

    url = ndvi.getThumbURL({

        'region': aoi,

        'dimensions': 512,

        'min': 0,

        'max': 1,

        'palette': ['black', 'green'],

        'format': 'png'
    })

    response = requests.get(url)

    img = Image.open(
        BytesIO(response.content)
    )

    img = np.array(img)

    # ======================================
    # IMAGE PROCESSING
    # ======================================

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_RGB2GRAY
    )

    _, forest_mask = cv2.threshold(
        gray,
        30,
        255,
        cv2.THRESH_BINARY
    )

    kernel = np.ones((5,5), np.uint8)

    forest_mask = cv2.morphologyEx(
        forest_mask,
        cv2.MORPH_OPEN,
        kernel
    )

    forest_mask = cv2.dilate(
        forest_mask,
        kernel,
        iterations=2
    )

    st.image(
        forest_mask,
        caption="Detected Vegetation Zones"
    )

    # ======================================
    # HOTSPOT DETECTION
    # ======================================

    contours, _ = cv2.findContours(
        forest_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    image_bgr = cv2.cvtColor(
        img,
        cv2.COLOR_RGB2BGR
    )

    hotspot_count = 0

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area > 150:

            x, y, w, h = cv2.boundingRect(cnt)

            cv2.rectangle(
                image_bgr,
                (x, y),
                (x+w, y+h),
                (0, 0, 255),
                2
            )

            hotspot_count += 1

    # ======================================
    # ECOLOGY LOOKUP
    # ======================================

    ecology_score = 30

    forest_type = "unknown"

    soil_type = "Unknown Soil Type"

    location_lower = location.lower()

    for forest in forest_database:

        if forest in location_lower:

            ecology_score = forest_database[forest]["ecology_score"]

            forest_type = forest_database[forest]["forest_type"]

            soil_type = soil_database.get(
                forest_type,
                "Unknown Soil Type"
            )

            break

    # ======================================
    # VEGETATION DENSITY
    # ======================================

    green_pixels = cv2.countNonZero(
        forest_mask
    )

    total_pixels = (
        forest_mask.shape[0] *
        forest_mask.shape[1]
    )

    vegetation_density = (
        green_pixels / total_pixels
    ) * 100

    # ======================================
    # SUITABILITY SCORE
    # ======================================

    final_score = (
        vegetation_density * 0.4
        + ecology_score * 0.6
    )

    # ======================================
    # ECOLOGICAL PENALTIES
    # ======================================

    if vegetation_density > 65:

        final_score *= 0.70

    elif vegetation_density < 5:

        final_score *= 0.60

    if forest_type == "rainforest":

        final_score *= 0.65

    if forest_type == "urban":

        final_score *= 0.10

    if forest_type == "urban_greenery":

        final_score *= 0.25

    # ======================================
    # ESTIMATION LOGIC
    # ======================================

    estimated_trees = int(
        hotspot_count *
        (ecology_score / 10)
    )

    # ======================================
    # SPECIAL BOOST FOR SANDALWOOD BELT
    # ======================================

    high_sandalwood_regions = [

        "mysuru",
        "mysore",
        "chamarajanagar",
        "kodagu",
        "coorg",
        "hassan"
    ]

    if any(
        region in location_lower
        for region in high_sandalwood_regions
    ):

        estimated_trees = max(
            int(estimated_trees * 3.5),
            65
        )

    # ======================================
    # STRICT URBAN PENALTY
    # ======================================

    urban_keywords = [

        "school",
        "college",
        "university",
        "engineering college",
        "campus",
        "city",
        "mall",
        "tech park",
        "hospital",
        "apartment",
        "layout",
        "metro",
        "station",
        "airport",
        "urban",
        "bengaluru",
        "bangalore",
        "rvce",
        "rv college"
    ]

    is_urban_region = (

        forest_type == "urban"

        or any(
            word in location_lower
            for word in urban_keywords
        )
    )

    if is_urban_region:

        estimated_trees = 0

        hotspot_count = 0

        vegetation_density = 0

    elif forest_type == "urban_greenery":

        estimated_trees = 0

    elif forest_type == "urban_forest":

        estimated_trees = int(
            estimated_trees * 0.20
        )

    # ======================================
    # SUITABILITY CLASSIFICATION
    # ======================================

    if is_urban_region:

        probability = "LOW"

    elif estimated_trees >= 60:

        probability = "HIGH"

    elif estimated_trees >= 25:

        probability = "MEDIUM"

    else:

        probability = "LOW"

    # ======================================
    # FINAL IMAGE
    # ======================================

    image_rgb = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2RGB
    )

    st.image(
        image_rgb,
        caption="Potential Sandalwood Habitat Zones"
    )

    # ======================================
    # FINAL RESULTS
    # ======================================

    st.subheader("Sandalwood Habitat Analysis")

    st.success(
        f"Forest Type: {forest_type}"
    )

    st.success(
        f"Dominant Soil Type: "
        f"{soil_type}"
    )

    st.success(
        f"Vegetation Density: "
        f"{round(vegetation_density,2)}%"
    )

    st.success(
        f"Estimated Sandalwood Suitability Count: "
        f"{estimated_trees}"
    )

    st.success(
        f"Sandalwood Growth Suitability: "
        f"{probability}"
    )