#!/usr/bin/gjs
/**
 * Test script for Soup-based API call
 *
 * This script tests the same Soup library approach used in the extension
 * to verify it can bypass Cloudflare better than curl.
 *
 * Usage: gjs scripts/test-soup-api.js
 */

imports.gi.versions.Soup = '3.0';
const { GLib, Gio, Soup } = imports.gi;

// Read credentials
const credentialsPath = GLib.build_filenamev([
    GLib.get_home_dir(),
    '.config',
    'claude',
    'credentials.json'
]);

const file = Gio.File.new_for_path(credentialsPath);

if (!file.query_exists(null)) {
    print('❌ Credentials file not found:', credentialsPath);
    print('Run: python3 scripts/extract-token.py');
    imports.system.exit(1);
}

const [success, contents] = file.load_contents(null);

if (!success) {
    print('❌ Failed to read credentials file');
    imports.system.exit(1);
}

const decoder = new TextDecoder('utf-8');
const credentialsJson = decoder.decode(contents);
const credentials = JSON.parse(credentialsJson);

const sessionKey = credentials.session_key;
const organizationId = credentials.organization_id;
const cfClearance = credentials.cf_clearance || '';

if (!sessionKey || !organizationId) {
    print('❌ Missing session_key or organization_id in credentials');
    imports.system.exit(1);
}

print('✅ Credentials loaded');
print('   Organization ID:', organizationId);
print('   Session Key:', sessionKey.substring(0, 20) + '...');
if (cfClearance) {
    print('   CF Clearance:', cfClearance.substring(0, 20) + '...');
}
print('');

// Create Soup session
const url = `https://claude.ai/api/organizations/${organizationId}/usage`;

print('🌐 Testing API with Soup library...');
print('   URL:', url);
print('');

const session = new Soup.Session({
    timeout: 30,
    user_agent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
});

const message = Soup.Message.new('GET', url);

// Set headers to mimic browser request
const headers = message.get_request_headers();
headers.append('Accept', '*/*');
headers.append('Accept-Language', 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7');
headers.append('anthropic-client-platform', 'web_claude_ai');
headers.append('anthropic-client-sha', '32e70e953567275b457146991c741b2f86f4a0f0');
headers.append('anthropic-client-version', '1.0.0');
headers.append('cache-control', 'no-cache');
headers.append('pragma', 'no-cache');
headers.append('Referer', 'https://claude.ai/settings/usage');
headers.append('sec-fetch-dest', 'empty');
headers.append('sec-fetch-mode', 'cors');
headers.append('sec-fetch-site', 'same-origin');

// Build and set Cookie header
let cookieString = `sessionKey=${sessionKey}; lastActiveOrg=${organizationId}`;
if (cfClearance) {
    cookieString += `; cf_clearance=${cfClearance}`;
}
headers.append('Cookie', cookieString);

print('📤 Sending request...');
print('');

// Create main loop
const loop = GLib.MainLoop.new(null, false);

// Send async request
session.send_and_read_async(
    message,
    GLib.PRIORITY_DEFAULT,
    null,
    (session, result) => {
        try {
            const bytes = session.send_and_read_finish(result);
            const decoder = new TextDecoder('utf-8');
            const responseText = decoder.decode(bytes.get_data());

            print('📥 Response received');
            print('   Status:', message.get_status());
            print('   Length:', responseText.length, 'bytes');
            print('');

            // Check if response is HTML (Cloudflare challenge)
            if (responseText.trim().startsWith('<!DOCTYPE') || responseText.trim().startsWith('<html')) {
                print('❌ Received HTML instead of JSON (Cloudflare blocking)');
                print('');
                print('First 200 chars of response:');
                print(responseText.substring(0, 200));
                loop.quit();
                return;
            }

            // Parse JSON response
            const data = JSON.parse(responseText);

            print('✅ API call successful!');
            print('');

            // Extract five_hour session data
            const fiveHour = data.five_hour;

            if (!fiveHour) {
                print('⚠️  No five_hour data in API response');
                print('Response:', JSON.stringify(data, null, 2));
                loop.quit();
                return;
            }

            // Extract percentage
            const percentage = fiveHour.utilization ? Number(fiveHour.utilization) : 0;

            print('📊 Usage Data:');
            print('   Percentage:', percentage + '%');
            print('   Resets at:', fiveHour.resets_at);

            // Calculate remaining time
            let remainingMinutes = 0;
            if (fiveHour.resets_at) {
                const resetsAt = new Date(fiveHour.resets_at);
                const now = new Date();
                const diffMs = resetsAt - now;
                remainingMinutes = Math.max(0, Math.floor(diffMs / (1000 * 60)));
                const hours = Math.floor(remainingMinutes / 60);
                const mins = remainingMinutes % 60;
                print('   Time remaining:', `${hours}h ${mins}m`);
            }

            print('');
            print('🎉 Success! The extension should show: "Claude:', `${Math.floor(remainingMinutes / 60)}h ${remainingMinutes % 60}m | ${percentage}%"`);

        } catch (error) {
            print('❌ Error parsing response:', error.message);
            print('');
            if (typeof responseText !== 'undefined') {
                print('Response preview:');
                print(responseText.substring(0, 300));
            }
        }

        loop.quit();
    }
);

// Run main loop
loop.run();
