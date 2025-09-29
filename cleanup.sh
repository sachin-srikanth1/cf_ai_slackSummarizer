#!/bin/bash
# Remove unnecessary files
rm -f test_slack_bot.py
rm -f test_slack_mention.py  
rm -f test_webhook.py
rm -f trigger_bot.py
rm -f send_to_slack.py
rm -f slack_test.sh
rm -rf backend/tests
rm -f backend/test_server.py
rm -rf backend/utils
rm -rf node_modules
rm -f package-lock.json
rm -f package.json
rm -rf public
rm -rf backend/cf_workers
echo "Cleanup completed"