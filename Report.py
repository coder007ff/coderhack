import argparse
import asyncio
import json
import logging
import os
import sys
from telethon.sessions import StringSession
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import (
    InputReportReasonSpam,
    InputReportReasonViolence,
    InputReportReasonPornography,
    InputReportReasonChildAbuse,
    InputReportReasonOther
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('report_bot')

# Reason mapping
REASON_MAP = {
    'spam': InputReportReasonSpam(),
    'violence': InputReportReasonViolence(),
    'porn': InputReportReasonPornography(),
    'childabuse': InputReportReasonChildAbuse(),
    'other': InputReportReasonOther()
}

def load_config(config_file='config.json'):
    """Load configuration from JSON file"""
    try:
        with open(config_file) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file {config_file} not found!")
        sys.exit(1)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {config_file}!")
        sys.exit(1)

async def report_target(client, target, reason, message_ids=None):
    """Report target entity using a client session"""
    try:
        # Resolve target entity
        entity = await client.get_entity(target)
        logger.info(f"Reporting {entity.id} using {client.session.save()}")

        # Prepare report request
        report_reason = REASON_MAP.get(reason, InputReportReasonSpam())
        
        await client(ReportRequest(
            peer=entity,
            reason=report_reason,
            message_ids=message_ids or []
        ))
        
        logger.info(f"Successfully reported {entity.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error in session {client.session.save()[:15]}...: {str(e)}")
        return False

async def main():
    parser = argparse.ArgumentParser(description='Telegram Mass Reporting Bot')
    parser.add_argument('target', help='Username or ID of target to report')
    parser.add_argument('reason', choices=REASON_MAP.keys(), 
                        help='Reason for reporting')
    parser.add_argument('--config', default='config.json',
                        help='Configuration file (default: config.json)')
    parser.add_argument('--message-ids', nargs='+', type=int,
                        help='Specific message IDs to report (for channels/groups)')
    
    args = parser.parse_args()
    config = load_config(args.config)
    
    if not config.get('sessions'):
        logger.error("No sessions found in configuration!")
        return
        
    results = []
    for session_data in config['sessions']:
        client = TelegramClient(
            StringSession(session_data['session_string']),
            session_data['api_id'],
            session_data['api_hash']
        )
        
        try:
            await client.start()
            result = await report_target(
                client,
                args.target,
                args.reason,
                args.message_ids
            )
            results.append(result)
            await client.disconnect()
        except Exception as e:
            logger.error(f"Session initialization failed: {str(e)}")
            results.append(False)
    
    success_count = sum(results)
    logger.info(f"Operation complete. Success: {success_count}/{len(results)}")

if __name__ == '__main__':
    asyncio.run(main())
