// ==== DR. SMILE SYSTEM v2.1 – DELIVERY LOGIC + SMS ====
// FULLY SYNCED: Google Forms → Sheets → Email + SMS → Dr. Smile Flow
// 📦 Delivery Agent Auto-Assignment & Logging | ✅ Final Audited

// ========== CONFIG ==========
var CONFIG = PropertiesService.getScriptProperties();
var MAPS_API_KEY       = CONFIG.getProperty('MAPS_API_KEY');
var SPREADSHEET_ID     = CONFIG.getProperty('SPREADSHEET_ID');
var DIGITAL_FORM_SHEET = 'Form Responses 1';
var ARRIVAL_FORM_ID    = CONFIG.getProperty('ARRIVAL_FORM_ID');
var DENTIST_DB_SHEET   = 'DentistDatabase';
var BEARER_DB_SHEET    = 'Delivery Agents';
var ORDER_LOG_SHEET    = 'Deliveries Order Log';
var BUSINESS_EMAIL     = CONFIG.getProperty('BUSINESS_EMAIL');

var TWILIO_SID         = CONFIG.getProperty('TWILIO_SID');
var TWILIO_AUTH        = CONFIG.getProperty('TWILIO_AUTH');
var TWILIO_NUMBER      = CONFIG.getProperty('TWILIO_NUMBER');

// ========== ON FORM SUBMIT (Check-In) ==========
function onDigitalCheckIn(e) {
  if (!e || !e.range) throw new Error('Trigger must be form submit');

  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var sheet = ss.getSheetByName(DIGITAL_FORM_SHEET);
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];
  var row = e.range.getRow();
  var values = sheet.getRange(row, 1, 1, sheet.getLastColumn()).getValues()[0];
  var idx = name => headers.indexOf(name) + 1;

  var leadId = values[idx('Lead ID') - 1];
  var fullName = values[idx('Customer Full Name') - 1];
  var email = values[idx('Email') - 1];
  var office = values[idx('Assigned Dental Office') - 1];
  var latitude = values[idx('Latitude') - 1];
  var longitude = values[idx('Longitude') - 1];
  var qrCodeLink = values[idx('QR Code Link') - 1];
  var checkInTime = values[idx('Check-in Time') - 1];
  var zone = values[idx('Preferred Location Zone') - 1]; // Must exist in form

  var mapImg = `https://maps.googleapis.com/maps/api/staticmap?center=${latitude},${longitude}&zoom=15&size=600x300&markers=color:red%7C${latitude},${longitude}&key=${MAPS_API_KEY}`;
  var mapLink = `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`;

  // 📨 Send Email to Lead
  var subject = 'Your Dr. Smile Appointment – ' + office;
  var htmlBody = `
    <p>Hi ${fullName},</p>
    <p>Your appointment is booked at <strong>${office}</strong>.</p>
    <p><a href="${mapLink}"><img src="${mapImg}"/></a></p>
    <p><a href="${mapLink}">View on Google Maps</a></p>
    <hr/>
    <p>On arrival, scan the QR code below:</p>
    <p><a href="${qrCodeLink}"><img src="${qrCodeLink}"/></a></p>`;

  try {
    MailApp.sendEmail({ to: email, subject: subject, htmlBody: htmlBody });
  } catch (err) {
    Logger.log("❌ Lead email failed: " + err);
  }

  // 📢 Notify Business
  var bizBody = `New Lead:\nID: ${leadId}\nName: ${fullName}\nEmail: ${email}\nOffice: ${office}\nZone: ${zone}\nCheck-in: ${checkInTime}\nMap: ${mapLink}`;
  try {
    MailApp.sendEmail({ to: BUSINESS_EMAIL, subject: `New Lead: ${leadId}`, body: bizBody });
  } catch (err) {
    sendTwilioSMS('+18761234567', `[Backup SMS] New lead: ${fullName} in zone ${zone}`);
  }

  // 📦 Random Delivery Agent Assignment by Zone
  var bearerSheet = ss.getSheetByName(BEARER_DB_SHEET);
  var bearerData = bearerSheet.getDataRange().getValues();
  var matchingAgents = bearerData.filter((row, i) => i !== 0 && row[2] === zone);
  var assigned = matchingAgents.length > 0 ? matchingAgents[Math.floor(Math.random() * matchingAgents.length)] : null;

  if (assigned) {
    var bearerName = assigned[0];
    var bearerPhone = assigned[1];

    // ✅ Log to Delivery Sheet
    var deliverySheet = ss.getSheetByName(ORDER_LOG_SHEET);
    deliverySheet.appendRow([new Date(), leadId, fullName, zone, office, bearerName, bearerPhone]);

    // 📲 Send SMS to Assigned Agent
    sendTwilioSMS(bearerPhone, `📦 New Dr. Smile delivery for ${fullName} in ${zone} → ${office}`);
  } else {
    Logger.log("⚠️ No delivery agent found for zone: " + zone);
  }
}

// ========== ARRIVAL CONFIRMATION ==========
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
  var dHeaders = dentistSheet.getRange(1, 1, 1, dentistSheet.getLastColumn()).getValues()[0];
  var dData = dentistSheet.getDataRange().getValues();
  var dIdx = name => dHeaders.indexOf(name) + 1;

  for (var j = 1; j < dData.length; j++) {
    if (dData[j][dIdx('name') - 1] === office) {
      var email = dData[j][dIdx('email') - 1];
      var phone = dData[j][dIdx('phone') - 1];
      try {
        MailApp.sendEmail({ to: email, subject: `📍 Arrival – ${leadId}`, body: `Notes: ${notes}` });
      } catch (err) {
        sendTwilioSMS(phone, `📍 Patient arrived for Lead ID ${leadId}. Notes: ${notes}`);
      }
      break;
    }
  }
}

// ========== TWILIO SMS ==========
function sendTwilioSMS(to, message) {
  var url = `https://api.twilio.com/2010-04-01/Accounts/${TWILIO_SID}/Messages.json`;
  var payload = {
    To: to,
    From: TWILIO_NUMBER,
    Body: message
  };
  var options = {
    method: "post",
    payload: payload,
    headers: {
      "Authorization": "Basic " + Utilities.base64Encode(TWILIO_AUTH)
    }
  };
  try {
    UrlFetchApp.fetch(url, options);
  } catch (e) {
    Logger.log("❌ SMS Failed: " + e.message);
  }
}

// ========== INSTALL TRIGGERS ==========
function createDigitalTrigger() {
  ScriptApp.newTrigger('onDigitalCheckIn')
    .forSpreadsheet(SpreadsheetApp.openById(SPREADSHEET_ID))
    .onFormSubmit()
    .create();
}

function createArrivalTrigger() {
  ScriptApp.newTrigger('onArrivalSubmit')
    .forForm(FormApp.openById(ARRIVAL_FORM_ID))
    .onFormSubmit()
    .create();
}
