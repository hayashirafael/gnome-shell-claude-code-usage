import GObject from 'gi://GObject';
import St from 'gi://St';
import Gio from 'gi://Gio';
import GLib from 'gi://GLib';
import Clutter from 'gi://Clutter';
// import Soup from 'gi://Soup'; // TODO: Uncomment when libsoup is installed

import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';

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

            // Find active block
            const activeBlock = data.blocks?.find(block => block.isActive);

            if (!activeBlock) {
                return null;
            }

            // Calculate tokens that count towards limit
            // Cache read tokens do NOT count towards rate limits
            const tokenCounts = activeBlock.tokenCounts || {};
            const tokensUsed = (tokenCounts.inputTokens || 0) +
                             (tokenCounts.outputTokens || 0) +
                             (tokenCounts.cacheCreationInputTokens || 0);

            // Get configured token limit (default: 88000 for Max5)
            const tokensLimit = this._settings.get_int('token-limit');

            // Get time remaining in minutes
            const remainingMinutes = activeBlock.projection?.remainingMinutes || 0;

            // Get cost and projected total cost for percentage calculation
            const cost = activeBlock.costUSD || 0;
            const projectedTotalCost = activeBlock.projection?.totalCost || 0;

            return {
                tokensUsed,
                tokensLimit,
                remainingMinutes,
                totalTokens: activeBlock.totalTokens || 0,
                cost,
                projectedTotalCost,
                source: 'ccusage'
            };

        } catch (error) {
            console.log('[Claude Usage] ccusage failed:', error.message);
            return null;
        }
    }

    async _tryGetUsageFromAPI() {
        if (!this._settings.get_boolean('use-api-fallback')) {
            return null;
        }

        try {
            // Read credentials from Claude Code config
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

            const accessToken = credentials.access_token;

            if (!accessToken) {
                return null;
            }

            // Fetch usage from Anthropic API using curl
            const usageData = await this._fetchFromAPIWithCurl(accessToken);

            return usageData;

        } catch (error) {
            console.log('[Claude Usage] API fallback failed:', error.message);
            return null;
        }
    }

    async _fetchFromAPIWithCurl(token) {
        try {
            const url = 'https://api.anthropic.com/api/oauth/usage';

            const args = [
                'curl',
                '-s',
                '-H', `Authorization: Bearer ${token}`,
                '-H', 'Content-Type: application/json',
                url
            ];

            const timeout = this._settings.get_int('command-timeout');
            const result = await this._executeCommand(args, timeout);

            if (!result || !result.stdout) {
                return null;
            }

            const data = JSON.parse(result.stdout);

            // Parse API response to extract usage data
            // The API should return percentage and other usage metrics
            const currentSession = data.current_session || data.five_hour || data.session || {};

            // Extract percentage if available
            const percentage = currentSession.percentage || currentSession.usage_percentage || null;
            const cost = currentSession.cost || currentSession.cost_usd || 0;
            const costLimit = currentSession.cost_limit || currentSession.limit || 0;
            const remainingMinutes = currentSession.remaining_minutes || currentSession.time_remaining_minutes || 0;

            return {
                percentage, // Direct percentage from API
                cost,
                costLimit,
                remainingMinutes,
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

    _displayUsage(data) {
        const { cost, remainingMinutes, percentage: apiPercentage, costLimit: apiCostLimit } = data;

        // Use percentage directly from API if available, otherwise calculate
        let percentage = 0;
        if (apiPercentage !== null && apiPercentage !== undefined) {
            // Use percentage from API (most accurate)
            percentage = Math.round(apiPercentage);
        } else {
            // Fallback: calculate using cost and limit
            const costLimit = apiCostLimit || this._settings.get_double('cost-limit');
            if (costLimit > 0 && cost > 0) {
                percentage = ((cost / costLimit) * 100).toFixed(0);
            }
        }

        // Format time remaining
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

        // Build display text
        let displayText = 'Claude: ';

        if (timeText) {
            displayText += timeText;
        }

        if (this._settings.get_boolean('show-percentage')) {
            if (timeText) {
                displayText += ` | ${percentage}%`;
            } else {
                displayText += `${percentage}%`;
            }
        } else if (!timeText) {
            displayText += `$${cost.toFixed(2)}`;
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
