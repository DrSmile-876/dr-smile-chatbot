// ==== DR. SMILE SYSTEM v2.2 – ORDER TRACKING & DELIVERY + SMS ====
// FULLY SYNCED: Google Forms → Sheets → Email + SMS → Dr. Smile Flow
// 📦 Delivery Agent Auto-Assignment & Logging | ✅ Final Audited

// ========== CONFIG ==========
var CONFIG = PropertiesService.getScriptProperties();
var MAPS_API_KEY       = CONFIG.getProperty('MAPS_API_KEY');
var SPREADSHEET_ID     = CONFIG.getProperty('SPREADSHEET_ID');
var ARRIVAL_FORM_ID    = CONFIG.getProperty('ARRIVAL_FORM_ID');
var TWILIO_SID         = CONFIG.getProperty('TWILIO_SID');
var TWILIO_AUTH        = CONFIG.getProperty('TWILIO_AUTH');
var TWILIO_NUMBER      = CONFIG.getProperty('TWILIO_NUMBER');
var BUSINESS_EMAIL     = CONFIG.getProperty('BUSINESS_EMAIL');

var DIGITAL_FORM_SHEET = 'Form Responses 1';
var BEARER_DB_SHEET    = 'Delivery Agents';
var ORDER_LOG_SHEET    = 'Deliveries Order Log';
var DENTIST_DB_SHEET   = 'DentistDatabase';

function onDigitalCheckIn(e) {
  if (!e || !e.range) return;
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName(DIGITAL_FORM_SHEET);
  var row = e.range.getRow();
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var values  = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];
  var idx = name => headers.indexOf(name) + 1;

  var fullName = values[idx('Customer Full Name') - 1];
  var email    = values[idx('Email') - 1];
  var office   = values[idx('Assigned Dental Office') - 1];
  var leadId   = values[idx('Lead ID') - 1];
  var zone     = values[idx('Preferred Location Zone') - 1];
  var qrCode   = values[idx('QR Code Link') - 1];
  var lat      = values[idx('Latitude') - 1];
  var lon      = values[idx('Longitude') - 1];
  var mapLink  = `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
  var mapImg   = `https://maps.googleapis.com/maps/api/staticmap?center=${lat},${lon}&zoom=15&size=600x300&markers=color:red%7C${lat},${lon}&key=${MAPS_API_KEY}`;

  var htmlBody = `<p>Hi ${fullName},</p>
    <p>Your appointment is booked at <strong>${office}</strong>.</p>
    <p><a href="${mapLink}"><img src="${mapImg}" /></a></p>
    <p>On arrival, scan this QR:</p>
    <p><a href="${qrCode}"><img src="${qrCode}" /></a></p>`;

  try {
    MailApp.sendEmail({ to: email, subject: 'Your Dr. Smile Appointment', htmlBody });
  } catch (err) {
    sendTwilioSMS('+18761234567', `🛑 Email failed for ${fullName}`);
  }

  assignDeliveryAgent(zone, fullName, leadId, office);
}

function assignDeliveryAgent(zone, name, leadId, office) {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var agents = ss.getSheetByName(BEARER_DB_SHEET).getDataRange().getValues().filter((r, i) => i && r[2] === zone);
  if (!agents.length) return;

  var [bearerName, bearerPhone] = agents[Math.floor(Math.random() * agents.length)];
  ss.getSheetByName(ORDER_LOG_SHEET).appendRow([new Date(), leadId, name, zone, office, bearerName, bearerPhone]);
  sendTwilioSMS(bearerPhone, `📦 Dr. Smile order for ${name} → ${office}`);
}

function onArrivalSubmit(e) {
  if (!e || !e.namedValues) return;
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName(DIGITAL_FORM_SHEET);
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var data = sheet.getDataRange().getValues();
  var idx = name => headers.indexOf(name) + 1;

  var leadId = e.namedValues['Lead ID'][0];
  var notes = (e.namedValues['Arrival Notes'] || [''])[0];
  var row = data.findIndex((r, i) => i && r[idx('Lead ID') - 1] === leadId) + 1;
  if (!row) return;

  sheet.getRange(row, idx('Status')).setValue('Arrived');
  sheet.getRange(row, idx('Arrival Time')).setValue(new Date());

  var office = sheet.getRange(row, idx('Assigned Dental Office')).getValue();
  var dentists = ss.getSheetByName(DENTIST_DB_SHEET).getDataRange().getValues();
  var dHeaders = dentists[0];
  var dIdx = name => dHeaders.indexOf(name) + 1;

  for (var i = 1; i < dentists.length; i++) {
    if (dentists[i][dIdx('name') - 1] === office) {
      try {
        MailApp.sendEmail({ to: dentists[i][dIdx('email') - 1], subject: '📍 Patient Arrival', body: `Lead ${leadId} has arrived.\nNotes: ${notes}` });
      } catch (err) {
        sendTwilioSMS(dentists[i][dIdx('phone') - 1], `📍 Arrival: Lead ${leadId}\nNotes: ${notes}`);
      }
      break;
    }
  }
}

function sendTwilioSMS(to, msg) {
  var url = `https://api.twilio.com/2010-04-01/Accounts/${TWILIO_SID}/Messages.json`;
  var payload = { To: to, From: TWILIO_NUMBER, Body: msg };
  var options = {
    method: "post",
    payload,
    headers: { "Authorization": "Basic " + Utilities.base64Encode(TWILIO_AUTH) }
  };
  try { UrlFetchApp.fetch(url, options); } catch (e) { Logger.log("❌ SMS Fail: " + e.message); }
}

function createDigitalTrigger() {
  ScriptApp.newTrigger('onDigitalCheckIn').forSpreadsheet(SpreadsheetApp.openById(SPREADSHEET_ID)).onFormSubmit().create();
}

function createArrivalTrigger() {
  ScriptApp.newTrigger('onArrivalSubmit').forForm(FormApp.openById(ARRIVAL_FORM_ID)).onFormSubmit().create();
}
