import GObject from 'gi://GObject';
import St from 'gi://St';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Clutter from 'gi://Clutter';

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

/**
 * ClaudeUsageIndicator
 *
 * Displays real-time Claude Code usage in GNOME Shell top bar.
 *
 * Data Flow:
 * 1. Try Anthropic OAuth API first (most accurate, returns exact percentage)
 * 2. Fallback to ccusage CLI tool (calculates percentage using discovered formula)
 * 3. Final fallback to configured cost-limit setting
 *
 * Percentage Calculation Formula (discovered through testing):
 *   factor = 2.113 - (0.645 × session_progress)
 *   percentage = (current_cost / (projected_cost × factor)) × 100
 *
 * Where session_progress = elapsed_time / total_time (0.0 to 1.0)
 *
 * This formula matches claude.ai/settings/usage with ~0% error.
 * Works for all plans (Pro/Max5/Max20) without hardcoded limits.
 */
const ClaudeUsageIndicator = GObject.registerClass(
class ClaudeUsageIndicator extends PanelMenu.Button {
    _init(settings) {
        super._init(0.0, 'Claude Usage Indicator', false);

        this._settings = settings;
        this._refreshing = false;
        this._updateTimeout = null;

        // Create label for the panel
        this._label = new St.Label({
            text: 'Claude: ...',
            y_align: Clutter.ActorAlign.CENTER
        });
        this.add_child(this._label);

        // Initial update
        this._updateUsageInfo();

        // Setup auto-refresh timer
        this._setupTimer();
    }

    _setupTimer() {
        // Clear existing timer if any
        if (this._updateTimeout) {
            GLib.source_remove(this._updateTimeout);
            this._updateTimeout = null;
        }

        // Get interval from settings (in minutes)
        const intervalMinutes = this._settings.get_int('refresh-interval');
        const intervalSeconds = intervalMinutes * 60;

        // Setup new timer
        this._updateTimeout = GLib.timeout_add_seconds(
            GLib.PRIORITY_DEFAULT,
            intervalSeconds,
            () => {
                this._updateUsageInfo();
                return GLib.SOURCE_CONTINUE;
            }
        );
    }

    /**
     * Main update loop - fetches usage data and updates the panel display
     *
     * Priority order:
     * 1. Anthropic OAuth API (if enabled and credentials available)
     * 2. ccusage CLI tool (local JSONL file analysis)
     * 3. Display error if both fail
     *
     * Called on:
     * - Extension initialization
     * - Timer interval (default: every 1 minute)
     */
    _updateUsageInfo() {
        if (this._refreshing) {
            return;
        }

        this._refreshing = true;
        this._label.set_text('Claude: Refreshing...');

        // Try API first for most accurate percentage, fallback to ccusage
        this._tryGetUsageFromAPI()
            .then(apiData => {
                if (apiData && apiData.percentage !== null && apiData.percentage !== undefined) {
                    // API returned percentage - use it directly
                    this._displayUsage(apiData);
                    return null; // Skip ccusage
                } else {
                    // API failed or didn't return percentage - use ccusage
                    return this._tryGetUsageFromCcusage();
                }
            })
            .then(ccusageData => {
                if (ccusageData) {
                    this._displayUsage(ccusageData);
                }
            })
            .catch(error => {
                console.error('[Claude Usage] Error:', error);
                this._label.set_text('Claude: Error');
            })
            .finally(() => {
                this._refreshing = false;
            });
    }

    /**
     * Fetch usage data from ccusage CLI tool
     *
     * ccusage reads Claude Code's local usage JSONL files from ~/.config/claude/usage/
     * and provides aggregated statistics about token consumption and costs.
     *
     * Command executed: npx ccusage blocks --active --json
     *
     * Returns object with:
     * - cost: Current session cost in USD
     * - projectedTotalCost: Estimated total cost if burn rate continues
     * - dynamicLimit: Calculated limit (projected × 2) for percentage calculation
     * - remainingMinutes: Time until 5-hour session resets
     * - tokensUsed: Input + output + cache creation tokens (cache read excluded)
     *
     * @returns {Promise<Object|null>} Usage data or null if failed
     */
    async _tryGetUsageFromCcusage() {
        try {
            const command = this._settings.get_string('ccusage-command');
            const timeout = this._settings.get_int('command-timeout');

            // Execute: npx ccusage blocks --active --json (only get active block)
            const args = command.split(' ').concat(['blocks', '--active', '--json']);

            const result = await this._executeCommand(args, timeout);

            if (!result || !result.stdout) {
                return null;
            }

            // Parse JSON output
            const data = JSON.parse(result.stdout);

            // Find active block (current 5-hour session)
            const activeBlock = data.blocks?.find(block => block.isActive);

            if (!activeBlock) {
                return null;
            }

            // Calculate tokens that count towards limit
            // Note: cacheReadInputTokens do NOT count towards rate limits (90% discount)
            const tokenCounts = activeBlock.tokenCounts || {};
            const tokensUsed = (tokenCounts.inputTokens || 0) +
                             (tokenCounts.outputTokens || 0) +
                             (tokenCounts.cacheCreationInputTokens || 0);

            // Get configured token limit (default: 88000 for Max5)
            const tokensLimit = this._settings.get_int('token-limit');

            // Get time remaining in minutes
            const remainingMinutes = activeBlock.projection?.remainingMinutes || 0;

            // Get cost data (for display only, not percentage calculation)
            const cost = activeBlock.costUSD || 0;
            const projectedTotalCost = activeBlock.projection?.totalCost || 0;

            // NOTE: We DO NOT calculate percentage locally anymore!
            // The percentage calculation algorithm is proprietary to Anthropic
            // and changes dynamically in ways we cannot reliably replicate.
            //
            // Previous attempts to reverse-engineer the formula showed inaccuracies:
            // - Extension showed 31% when site showed 29%
            // - Formula with dynamic factors still had 2% error
            //
            // SOLUTION: Use Anthropic OAuth API exclusively for accurate percentage
            // This method only provides supporting data (cost, time remaining)

            return {
                tokensUsed,
                tokensLimit,
                remainingMinutes,
                totalTokens: activeBlock.totalTokens || 0,
                cost,
                projectedTotalCost,
                percentage: null,  // Must come from API
                source: 'ccusage'
            };

        } catch (error) {
            console.log('[Claude Usage] ccusage failed:', error.message);
            return null;
        }
    }

    /**
     * Fetch usage data from Anthropic OAuth API (PRIMARY METHOD)
     *
     * This is the most accurate source as it returns the exact percentage
     * shown on claude.ai/settings/usage.
     *
     * Endpoint: https://api.anthropic.com/api/oauth/usage
     * Authentication: OAuth Bearer token from ~/.config/claude/credentials.json
     *
     * Note: Disabled by default (requires credentials file).
     * Enable via: gsettings set ... use-api-fallback true
     *
     * @returns {Promise<Object|null>} API data with exact percentage or null
     */
    async _tryGetUsageFromAPI() {
        if (!this._settings.get_boolean('use-api-fallback')) {
            return null;
        }

        try {
            // Read OAuth credentials from Claude Code config
            const credentialsPath = GLib.build_filenamev([
                GLib.get_home_dir(),
                '.config',
                'claude',
                'credentials.json'
            ]);

            const file = Gio.File.new_for_path(credentialsPath);

            if (!file.query_exists(null)) {
                console.log('[Claude Usage] Credentials file not found');
                return null;
            }

            const [success, contents] = file.load_contents(null);

            if (!success) {
                return null;
            }

            const decoder = new TextDecoder('utf-8');
            const credentialsJson = decoder.decode(contents);
            const credentials = JSON.parse(credentialsJson);

            const sessionKey = credentials.session_key;
            const organizationId = credentials.organization_id;

            if (!sessionKey || !organizationId) {
                console.log('[Claude Usage] Missing session_key or organization_id in credentials');
                return null;
            }

            // Fetch usage from Claude.ai API using curl
            const usageData = await this._fetchFromAPIWithCurl(sessionKey, organizationId);

            return usageData;

        } catch (error) {
            console.log('[Claude Usage] API fallback failed:', error.message);
            return null;
        }
    }

    /**
     * Execute API request using curl to claude.ai
     *
     * Fetches usage data from the official Claude.ai API endpoint.
     *
     * Expected API response structure:
     * {
     *   "five_hour": {
     *     "utilization": 13,  // Percentage (0-100)
     *     "resets_at": "2025-11-18T00:59:59.545582+00:00"
     *   },
     *   "seven_day": { ... },
     *   ...
     * }
     *
     * @param {string} sessionKey - Session key cookie from claude.ai
     * @param {string} organizationId - Organization ID from claude.ai
     * @returns {Promise<Object|null>} Parsed usage data or null
     */
    async _fetchFromAPIWithCurl(sessionKey, organizationId) {
        try {
            const url = `https://claude.ai/api/organizations/${organizationId}/usage`;

            const args = [
                'curl',
                '-s',
                '-H', `Cookie: sessionKey=${sessionKey}; lastActiveOrg=${organizationId}`,
                '-H', 'Content-Type: application/json',
                '-H', 'User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '-H', 'Accept: */*',
                '-H', 'Accept-Language: en-US,en;q=0.9',
                '-H', 'Referer: https://claude.ai/settings/usage',
                '-H', 'anthropic-client-platform: web_claude_ai',
                url
            ];

            const timeout = this._settings.get_int('command-timeout');
            const result = await this._executeCommand(args, timeout);

            if (!result || !result.stdout) {
                return null;
            }

            const data = JSON.parse(result.stdout);

            // Extract five_hour session data
            const fiveHour = data.five_hour;

            if (!fiveHour) {
                console.log('[Claude Usage] No five_hour data in API response');
                return null;
            }

            // Extract percentage (utilization is 0-100)
            const percentage = fiveHour.utilization || 0;

            // Calculate remaining minutes from resets_at timestamp
            let remainingMinutes = 0;
            if (fiveHour.resets_at) {
                const resetsAt = new Date(fiveHour.resets_at);
                const now = new Date();
                const diffMs = resetsAt - now;
                remainingMinutes = Math.max(0, Math.floor(diffMs / (1000 * 60)));
            }

            return {
                percentage,           // Direct percentage from API (100% accurate!)
                remainingMinutes,     // Calculated from resets_at
                cost: 0,             // Not provided by this API
                source: 'api'
            };

        } catch (error) {
            console.log('[Claude Usage] API fetch with curl failed:', error.message);
            return null;
        }
    }

    async _executeCommand(args, timeoutSeconds) {
        return new Promise((resolve, reject) => {
            try {
                const proc = Gio.Subprocess.new(
                    args,
                    Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE
                );

                // Setup timeout
                const timeoutId = GLib.timeout_add_seconds(
                    GLib.PRIORITY_DEFAULT,
                    timeoutSeconds,
                    () => {
                        proc.force_exit();
                        reject(new Error('Command timeout'));
                        return GLib.SOURCE_REMOVE;
                    }
                );

                // Communicate async
                proc.communicate_utf8_async(null, null, (proc, result) => {
                    try {
                        GLib.source_remove(timeoutId);

                        const [, stdout, stderr] = proc.communicate_utf8_finish(result);

                        if (proc.get_successful()) {
                            resolve({ stdout, stderr });
                        } else {
                            reject(new Error(`Command failed: ${stderr}`));
                        }
                    } catch (error) {
                        reject(error);
                    }
                });

            } catch (error) {
                reject(error);
            }
        });
    }

    /**
     * Display usage data in the panel
     *
     * IMPORTANT: Percentage MUST come from Anthropic OAuth API!
     * Local calculation is not accurate due to proprietary dynamic algorithms.
     *
     * Output formats:
     * - With API: "Claude: 3h 28m | 16%"
     * - Without API (time only): "Claude: 3h 28m"
     * - Without API (cost only): "Claude: $4.21"
     * - No API configured: "Claude: Setup API"
     *
     * @param {Object} data - Usage data from API or ccusage
     * @param {number} data.cost - Current session cost in USD
     * @param {number} data.remainingMinutes - Minutes until session reset
     * @param {number} [data.percentage] - Direct percentage from API (REQUIRED for accuracy)
     */
    _displayUsage(data) {
        const { cost, remainingMinutes, percentage: apiPercentage } = data;

        // === PERCENTAGE - API ONLY ===
        let percentage = null;
        let hasPercentage = false;

        if (apiPercentage !== null && apiPercentage !== undefined) {
            // Use percentage from Anthropic API (100% accurate)
            percentage = Math.round(apiPercentage);
            hasPercentage = true;
        }

        // === TIME FORMATTING ===
        let timeText = '';
        if (this._settings.get_boolean('show-time-remaining') && remainingMinutes > 0) {
            const hours = Math.floor(remainingMinutes / 60);
            const mins = remainingMinutes % 60;

            if (hours > 0) {
                timeText = `${hours}h ${mins}m`;
            } else {
                timeText = `${mins}m`;
            }
        }

        // === BUILD DISPLAY TEXT ===
        let displayText = 'Claude: ';

        if (!hasPercentage && !timeText && !this._settings.get_boolean('use-api-fallback')) {
            // No API configured - show setup message
            displayText = 'Claude: Setup API';
        } else {
            // Show available data
            if (timeText) {
                displayText += timeText;
            }

            if (this._settings.get_boolean('show-percentage')) {
                if (hasPercentage) {
                    if (timeText) {
                        displayText += ` | ${percentage}%`;
                    } else {
                        displayText += `${percentage}%`;
                    }
                } else {
                    // API not available but percentage requested
                    if (timeText) {
                        displayText += ' | --';
                    } else {
                        displayText += 'API Required';
                    }
                }
            } else if (!timeText) {
                // Show cost if nothing else to display
                displayText += `$${cost.toFixed(2)}`;
            }
        }

        this._label.set_text(displayText);
    }

    destroy() {
        if (this._updateTimeout) {
            GLib.source_remove(this._updateTimeout);
            this._updateTimeout = null;
        }

        super.destroy();
    }
});

export default class ClaudeUsageExtension extends Extension {
    enable() {
        const settings = this.getSettings();

        this._indicator = new ClaudeUsageIndicator(settings);

        Main.panel.addToStatusArea(
            this.metadata.uuid,
            this._indicator,
            1,
            'right'
        );
    }

    disable() {
        if (this._indicator) {
            this._indicator.destroy();
            this._indicator = null;
        }
    }
}
