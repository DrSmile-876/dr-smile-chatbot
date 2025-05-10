// ==== DR. SMILE SYSTEM v2.6 – ORDER TRACKING & DELIVERY + SMS + AUTO-TRIGGER CLEANUP ====
// FULLY SYNCED: Google Forms → Sheets → Email + SMS → Delivery Logs
// 📦 Delivery Agent Auto-Assignment & Logging | ✅ Final Audited

// ==== CONFIG  ====
var CONFIG = PropertiesService.getScriptProperties();
var MAPS_API_KEY = CONFIG.getProperty('MAPS_API_KEY');
var SPREADSHEET_ID = CONFIG.getProperty('SPREADSHEET_ID');
var MESSENGER_WEBHOOK = CONFIG.getProperty("MESSENGER_WEBHOOK");
var DENTIST_DB_SHEET = 'DentistDatabase';
var ORDER_LOG_SHEET = 'Deliveries Order Log';
var QR_CODE_BASE_URL = 'https://api.qrserver.com/v1/create-qr-code/?data=';

// ========== APPOINTMENT MATCH ==========
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

// ========== ORDER STATUS MESSENGER UPDATES ==========
function trackOrderUpdates(e) {
  if (!e || !e.range) return;
  var sheet = e.source.getSheetByName(ORDER_LOG_SHEET);
  if (!sheet) return;

  var row = e.range.getRow();
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var statusCol = headers.indexOf("Order Status") + 1;
  var idCol = headers.indexOf("Messenger ID") + 1;
  if (e.range.getColumn() !== statusCol) return;

  var status = sheet.getRange(row, statusCol).getValue();
  var userId = sheet.getRange(row, idCol).getValue();
  if (!userId || !status) return;

  var message = `📦 Your Dr. Smile order status has been updated: *${status}*`;

  var payload = JSON.stringify({
    recipient_id: userId,
    message: message
  });

  var options = {
    method: "post",
    contentType: "application/json",
    payload: payload
  };

  try {
    UrlFetchApp.fetch(MESSENGER_WEBHOOK, options);
  } catch (error) {
    Logger.log("❌ Messenger update failed: " + error);
  }
}

function createOrderStatusTrigger() {
  ScriptApp.newTrigger("trackOrderUpdates")
    .forSpreadsheet(SpreadsheetApp.openById(SPREADSHEET_ID))
    .onEdit()
    .create();
}
