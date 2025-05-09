// ==== DR. SMILE SYSTEM v2.2 – ORDER TRACKING & DELIVERY + SMS ====
// FULLY SYNCED: Google Forms → Sheets → Email + SMS → Delivery Logs
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
  var values = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];
  var idx = name => headers.indexOf(name) + 1;

  var fullName = values[idx('Customer Full Name') - 1];
  var email = values[idx('Email') - 1];
  var office = values[idx('Assigned Dental Office') - 1];
  var leadId = values[idx('Lead ID') - 1];
  var zone = values[idx('Preferred Location Zone') - 1];
  var qrCode = values[idx('QR Code Link') - 1];
  var latitude = values[idx('Latitude') - 1];
  var longitude = values[idx('Longitude') - 1];
  var mapLink = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;
  var mapImg = `https://maps.googleapis.com/maps/api/staticmap?center=${latitude},${longitude}&zoom=15&size=600x300&markers=color:red%7C${latitude},${longitude}&key=${MAPS_API_KEY}`;

  var html = `<p>Hi ${fullName},</p>
    <p>Your appointment is booked at <strong>${office}</strong>.</p>
    <p><a href="${mapLink}"><img src="${mapImg}" /></a></p>
    <p>Scan this QR to confirm arrival:</p>
    <p><a href="${qrCode}"><img src="${qrCode}" /></a></p>`;

  try {
    MailApp.sendEmail({ to: email, subject: 'Your Dr. Smile Appointment', htmlBody: html });
  } catch (err) {
    sendTwilioSMS('+18761234567', `Email failed for ${fullName}`);
  }

  assignDeliveryAgent(zone, fullName, leadId, office);
}

function assignDeliveryAgent(zone, name, leadId, office) {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var bearerSheet = ss.getSheetByName(BEARER_DB_SHEET);
  var deliverySheet = ss.getSheetByName(ORDER_LOG_SHEET);
  var data = bearerSheet.getDataRange().getValues();
  var matches = data.filter((r, i) => i > 0 && r[2] === zone);
  if (!matches.length) return;

  var chosen = matches[Math.floor(Math.random() * matches.length)];
  var bearerName = chosen[0];
  var bearerPhone = chosen[1];
  deliverySheet.appendRow([new Date(), leadId, name, zone, office, bearerName, bearerPhone]);
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
  var row;

  for (var i = 1; i < data.length; i++) {
    if (data[i][idx('Lead ID') - 1] === leadId) {
      row = i + 1;
      sheet.getRange(row, idx('Status')).setValue('Arrived');
      sheet.getRange(row, idx('Arrival Time')).setValue(new Date());
      break;
    }
  }

  if (!row) return;
  var office = sheet.getRange(row, idx('Assigned Dental Office')).getValue();
  var dentistSheet = ss.getSheetByName(DENTIST_DB_SHEET);
  var dData = dentistSheet.getDataRange().getValues();
  var dHeaders = dentistSheet.getRange(1, 1, 1, dentistSheet.getLastColumn()).getValues()[0];
  var dIdx = name => dHeaders.indexOf(name) + 1;

  for (var j = 1; j < dData.length; j++) {
    if (dData[j][dIdx('name') - 1] === office) {
      var email = dData[j][dIdx('email') - 1];
      var phone = dData[j][dIdx('phone') - 1];
      try {
        MailApp.sendEmail({ to: email, subject: `📍 Patient Arrival`, body: `Lead ${leadId} has arrived.\nNotes: ${notes}` });
      } catch (err) {
        sendTwilioSMS(phone, `📍 Lead ${leadId} arrived.`);
      }
      break;
    }
  }
}

function sendTwilioSMS(to, message) {
  var url = `https://api.twilio.com/2010-04-01/Accounts/${TWILIO_SID}/Messages.json`;
  var options = {
    method: "post",
    payload: {
      To: to,
      From: TWILIO_NUMBER,
      Body: message
    },
    headers: {
      "Authorization": "Basic " + Utilities.base64Encode(TWILIO_AUTH)
    }
  };
  UrlFetchApp.fetch(url, options);
}

function createDigitalTrigger() {
  ScriptApp.newTrigger('onDigitalCheckIn').forSpreadsheet(SpreadsheetApp.openById(SPREADSHEET_ID)).onFormSubmit().create();
}

function createArrivalTrigger() {
  ScriptApp.newTrigger('onArrivalSubmit').forForm(FormApp.openById(ARRIVAL_FORM_ID)).onFormSubmit().create();
}
