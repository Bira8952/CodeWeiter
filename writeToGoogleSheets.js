import { google } from 'googleapis';

let connectionSettings;

async function getAccessToken() {
  if (connectionSettings && connectionSettings.settings.expires_at && new Date(connectionSettings.settings.expires_at).getTime() > Date.now()) {
    return connectionSettings.settings.access_token;
  }
  
  const hostname = process.env.REPLIT_CONNECTORS_HOSTNAME
  const xReplitToken = process.env.REPL_IDENTITY 
    ? 'repl ' + process.env.REPL_IDENTITY 
    : process.env.WEB_REPL_RENEWAL 
    ? 'depl ' + process.env.WEB_REPL_RENEWAL 
    : null;

  if (!xReplitToken) {
    throw new Error('X_REPLIT_TOKEN not found for repl/depl');
  }

  connectionSettings = await fetch(
    'https://' + hostname + '/api/v2/connection?include_secrets=true&connector_names=google-sheet',
    {
      headers: {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': xReplitToken
      }
    }
  ).then(res => res.json()).then(data => data.items?.[0]);

  const accessToken = connectionSettings?.settings?.access_token || connectionSettings.settings?.oauth?.credentials?.access_token;

  if (!connectionSettings || !accessToken) {
    throw new Error('Google Sheet not connected');
  }
  return accessToken;
}

async function getGoogleSheetClient() {
  const accessToken = await getAccessToken();

  const oauth2Client = new google.auth.OAuth2();
  oauth2Client.setCredentials({
    access_token: accessToken
  });

  return google.sheets({ version: 'v4', auth: oauth2Client });
}

async function writePoolsToSheet(spreadsheetId, pools) {
  try {
    const sheets = await getGoogleSheetClient();
    
    // Erstelle Header-Zeile
    const headerRow = ['NAME', 'START', 'DEADLINE', 'FAKTOR', 'RATE', 'SCHICHT'];
    
    // Erstelle Daten-Zeilen
    const dataRows = pools.map(pool => [
      pool.name || '',
      pool.start || '',
      pool.deadline || '',
      pool.factor || 1,
      pool.rate || 80,
      pool.schicht || 'FRÜH'
    ]);
    
    // Kombiniere Header und Daten
    const values = [headerRow, ...dataRows];
    
    // Schreibe ins Google Sheet
    const response = await sheets.spreadsheets.values.update({
      spreadsheetId: spreadsheetId,
      range: 'A1',  // Start bei A1
      valueInputOption: 'RAW',
      requestBody: {
        values: values
      }
    });
    
    console.log('✅ Pools erfolgreich ins Google Sheet geschrieben:', response.data.updatedCells, 'Zellen aktualisiert');
    return { success: true, updatedCells: response.data.updatedCells };
    
  } catch (error) {
    console.error('❌ Fehler beim Schreiben ins Google Sheet:', error.message);
    throw error;
  }
}

// Hauptfunktion
async function main() {
  try {
    // Lese Pool-Daten aus stdin (von Python Backend)
    const poolsJson = process.argv[2];
    
    if (!poolsJson) {
      console.error('❌ Keine Pool-Daten übergeben');
      process.exit(1);
    }
    
    const pools = JSON.parse(poolsJson);
    const spreadsheetId = '14e85oqQrUjywXjNasJz7azME0t18RJEEldgRwCRFiH4';
    
    console.log(`📝 Schreibe ${pools.length} Pools ins Google Sheet...`);
    
    const result = await writePoolsToSheet(spreadsheetId, pools);
    
    console.log(JSON.stringify(result));
    process.exit(0);
    
  } catch (error) {
    console.error('❌ Fehler:', error.message);
    process.exit(1);
  }
}

main();
