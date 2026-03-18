// 1. Khởi tạo bản đồ tại tâm Làng Đại học
var map = L.map('map').setView([10.875, 106.801], 15);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

var layerGroup = L.layerGroup().addTo(map);
var schoolData, cafeData;

// 2. Tải dữ liệu từ các file GeoJSON trong thư mục Project1
$.getJSON("Toa_Do.geojson", function(data) { schoolData = data; });
$.getJSON("Cf_500m_Final.geojson", function(data) { cafeData = data; });

// 3. Xử lý sự kiện tìm kiếm
document.getElementById('search2').addEventListener('click', function() {
    var input = document.getElementById('inputschool').value.trim().toLowerCase();
    
    if (!input || !schoolData) return;

    layerGroup.clearLayers();

    // Tìm trường học dựa trên cột 'Name' (N hoa)
    var school = schoolData.features.find(f => 
        (f.properties.Name || "").toLowerCase().includes(input)
    );

    if (school) {
        // Lấy tọa độ từ GeoJSON [Kinh độ, Vĩ độ] và đảo ngược cho Leaflet [Vĩ độ, Kinh độ]
        var lng = school.geometry.coordinates[0];
        var lat = school.geometry.coordinates[1];
        var schoolCoords = [lat, lng];

        // --- LỆNH QUAN TRỌNG NHẤT: BẮT BẢN ĐỒ PHẢI ZOOM ĐẾN VỊ TRÍ MỚI ---
        map.setView(schoolCoords, 15); // Số 17 là mức độ phóng to

        // Vẽ vòng tròn 500m quanh trường
        L.circle(schoolCoords, {
            radius: 500,
            color: 'Green',
            fillOpacity: 0.36
        }).addTo(layerGroup);

        // Marker cho trường học
        L.marker(schoolCoords)
            .bindPopup("<b>" + school.properties.Name + "</b>")
            .addTo(layerGroup)
            .openPopup();

        // Tìm và hiển thị quán cafe xung quanh trong bán kính 500m
        cafeData.features.forEach(function(cafe) {
            var cLat = cafe.geometry.coordinates[1];
            var cLng = cafe.geometry.coordinates[0];
            var distance = map.distance(schoolCoords, [cLat, cLng]);

            if (distance <= 500) {
                L.circleMarker([cLat, cLng], {
                    radius: 6,
                    fillColor: "Red",
                    color: "#60f03c",
                    weight: 1,
                    fillOpacity: 1
                }).bindPopup("<b>" + cafe.properties.name + "</b>").addTo(layerGroup);
            }
        });
    } else {
        alert("WTF!!!!!!");
    }
});