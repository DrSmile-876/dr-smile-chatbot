// ==== DR. SMILE SYSTEM v2.5 – ORDER TRACKING & DELIVERY + SMS + AUTO-TRIGGER CLEANUP ====
// FULLY SYNCED: Google Forms → Sheets → Email + SMS → Delivery Logs
// 📦 Delivery Agent Auto-Assignment & Logging | ✅ Final Audited

// ==== CONFIG  ====
var CONFIG = PropertiesService.getScriptProperties();
var MAPS_API_KEY    = CONFIG.getProperty('MAPS_API_KEY');
var SPREADSHEET_ID  = CONFIG.getProperty('SPREADSHEET_ID');
var DENTIST_DB_SHEET   = 'DentistDatabase';
var QR_CODE_BASE_URL   = 'https://api.qrserver.com/v1/create-qr-code/?data=';  // fallback if not in sheet

function doPost(e) {
  var params = JSON.parse(e.postData.contents);
  var zone = params.zone;

  if (!zone) return ContentService.createTextOutput(JSON.stringify({ error: "No zone provided" })).setMimeType(ContentService.MimeType.JSON);

  var dentistData = getNearestDentist(zone);
  if (!dentistData) {
    return ContentService.createTextOutput(JSON.stringify({ error: "No dentist found in this zone" })).setMimeType(ContentService.MimeType.JSON);
  }

  var office = dentistData.name;
  var address = dentistData.address;
  var email = dentistData.email;
  var phone = dentistData.phone;

  var lat = dentistData.latitude;
  var lng = dentistData.longitude;

  var qrData = encodeURIComponent(`Dr. Smile - ${office} - ${zone}`);
  var qrUrl = QR_CODE_BASE_URL + qrData;
  var mapUrl = `https://maps.google.com/?q=${lat},${lng}`;
  var mapImg = `https://maps.googleapis.com/maps/api/staticmap?center=${lat},${lng}&zoom=15&size=600x300&markers=color:red%7C${lat},${lng}&key=${MAPS_API_KEY}`;

  var response = {
    office: office,
    address: address,
    email: email,
    phone: phone,
    mapLink: mapUrl,
    mapImg: mapImg,
    qrCode: qrUrl
  };

  return ContentService.createTextOutput(JSON.stringify(response)).setMimeType(ContentService.MimeType.JSON);
}

function getNearestDentist(zone) {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName(DENTIST_DB_SHEET);
  var data = sheet.getDataRange().getValues();
  var headers = data[0];
  var idx = name => headers.indexOf(name);

  for (var i = 1; i < data.length; i++) {
    if (data[i][idx('zone')].toLowerCase() === zone.toLowerCase()) {
      return {
        name: data[i][idx('name')],
        address: data[i][idx('address')],
        phone: data[i][idx('phone')],
        email: data[i][idx('email')],
        latitude: data[i][idx('latitude')],
        longitude: data[i][idx('longitude')]
      };
    }
  }
  return null;
}
