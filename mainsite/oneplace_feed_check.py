#!/usr/bin/env python3
"""
feed.applywithinradio.com Wordpress Monitoring for Zabbix
Place in: /usr/lib/zabbix/externalscripts/

Monitors weekday (Mon-Fri) podcast publishing schedule.
Posts go live at 00:05 UTC on weekdays.
Script runs daily at 2AM Pacific.

Usage:
    ./podcast_monitor.py check          # Print metrics
    ./podcast_monitor.py send           # Send to Zabbix
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from requests.auth import HTTPBasicAuth

# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
CREDS_FILE = SCRIPT_DIR / "apwi_share.creds"

def load_credentials():
    """Load credentials from apwi_share.creds file"""
    creds = {}
    if CREDS_FILE.exists():
        with open(CREDS_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith('export '):
                    line = line[7:]
                if '=' in line:
                    key, value = line.split('=', 1)
                    value = value.strip('"').strip("'")
                    creds[key.strip()] = value
    return creds

_creds = load_credentials()

WORDPRESS_URL = _creds.get('PODCAST_WP_URL', 'https://feed.applywithinradio.com')
USERNAME = _creds.get('PODCAST_WP_USER', 'admin')
APP_PASSWORD = _creds.get('PODCAST_WP_APP_PASSWORD', '')
SERIES_ID = int(_creds.get('PODCAST_SERIES_ID', '9'))

DEFAULT_ZABBIX_SERVER = _creds.get('ZABBIX_SERVER', '127.0.0.1')
DEFAULT_ZABBIX_HOST = _creds.get('ZABBIX_HOST', 'Podcast Feed')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
}

TIMEOUT = 30

# =============================================================================
# Helper Functions
# =============================================================================

def parse_wp_date(date_str: str) -> datetime:
    """Parse WordPress date string to timezone-aware datetime"""
    if date_str.endswith('Z'):
        date_str = date_str[:-1] + '+00:00'
    
    try:
        dt = datetime.fromisoformat(date_str)
    except ValueError:
        dt = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
    
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt


def is_weekday(dt: datetime) -> bool:
    """Check if datetime falls on a weekday (Mon=0 through Fri=4)"""
    return dt.weekday() < 5


def get_previous_weekday(dt: datetime) -> datetime:
    """Get the most recent weekday on or before dt"""
    while not is_weekday(dt):
        dt -= timedelta(days=1)
    return dt


# =============================================================================
# WordPress API Functions
# =============================================================================

def get_podcasts(status: str, count: int = 50) -> List[Dict[str, Any]]:
    """Get podcast episodes with given status"""
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/podcast"
    params = {
        'status': status,
        'orderby': 'date',
        'order': 'desc' if status == 'publish' else 'asc',
        'per_page': count,
        'series': SERIES_ID
    }
    
    auth = HTTPBasicAuth(USERNAME, APP_PASSWORD) if status == 'future' else None
    
    try:
        response = requests.get(
            url,
            params=params,
            auth=auth,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching {status} podcasts: {e}", file=sys.stderr)
        return []


def check_api_health() -> int:
    """Check if the WordPress API is responding"""
    url = f"{WORDPRESS_URL}/wp-json/wp/v2/podcast"
    try:
        response = requests.get(url, params={'per_page': 1}, headers=HEADERS, timeout=TIMEOUT)
        return 1 if response.status_code == 200 else 0
    except requests.RequestException:
        return 0


# =============================================================================
# Metric Calculation
# =============================================================================

def calculate_metrics() -> Dict[str, Any]:
    """Calculate all monitoring metrics"""
    now = datetime.now(timezone.utc)
    metrics = {}
    
    # API Health
    metrics['api_healthy'] = check_api_health()
    
    # Get published episodes
    published = get_podcasts('publish', 10)
    if published:
        last_pub = published[0]
        last_pub_date = parse_wp_date(last_pub['date'])
        
        metrics['last_published_date'] = last_pub_date.strftime('%Y-%m-%d')
        metrics['last_published_title'] = last_pub['title']['rendered']
        metrics['last_published_timestamp'] = int(last_pub_date.timestamp())
        
        # Check if today's episode was published (if today is a weekday)
        # Script runs at 2AM Pacific (10:00 UTC), posts go live at 00:05 UTC
        last_pub_day = last_pub_date.date()
        
        # Get the most recent weekday that should have a post
        expected_last_pub = get_previous_weekday(now).date()
        
        # Check for missed weekdays
        if last_pub_day >= expected_last_pub:
            metrics['missed_weekday_posts'] = 0
        else:
            # Count weekdays between last publish and expected
            missed = 0
            check_date = last_pub_day + timedelta(days=1)
            while check_date <= expected_last_pub:
                if is_weekday(datetime.combine(check_date, datetime.min.time())):
                    missed += 1
                check_date += timedelta(days=1)
            metrics['missed_weekday_posts'] = missed
    else:
        metrics['last_published_date'] = 'none'
        metrics['last_published_title'] = 'None'
        metrics['last_published_timestamp'] = 0
        metrics['missed_weekday_posts'] = -1  # Unknown/error state
    
    # Get scheduled episodes
    scheduled = get_podcasts('future', 50)
    
    # Filter to posts actually in the future
    weekday_scheduled = [
        ep for ep in scheduled 
        if is_weekday(parse_wp_date(ep['date'])) and parse_wp_date(ep['date']) > now
    ]
    
    # Sort by date ascending to ensure next/last are correct
    weekday_scheduled.sort(key=lambda ep: parse_wp_date(ep['date']))
    
    metrics['scheduled_weekday_count'] = len(weekday_scheduled)
    
    if weekday_scheduled:
        # First scheduled is the next one (sorted asc)
        next_sched = weekday_scheduled[0]
        next_sched_date = parse_wp_date(next_sched['date'])
        
        # Last scheduled is the furthest out
        last_sched = weekday_scheduled[-1]
        last_sched_date = parse_wp_date(last_sched['date'])
        
        metrics['next_scheduled_date'] = next_sched_date.strftime('%Y-%m-%d')
        metrics['next_scheduled_title'] = next_sched['title']['rendered']
        metrics['next_scheduled_timestamp'] = int(next_sched_date.timestamp())
        
        metrics['last_scheduled_date'] = last_sched_date.strftime('%Y-%m-%d')
        metrics['last_scheduled_title'] = last_sched['title']['rendered']
        metrics['last_scheduled_timestamp'] = int(last_sched_date.timestamp())
    else:
        metrics['next_scheduled_date'] = 'none'
        metrics['next_scheduled_title'] = 'None'
        metrics['next_scheduled_timestamp'] = 0
        metrics['last_scheduled_date'] = 'none'
        metrics['last_scheduled_title'] = 'None'
        metrics['last_scheduled_timestamp'] = 0
    
    # Check if we have 2 weeks (10 weekday posts) scheduled
    metrics['has_two_weeks_scheduled'] = 1 if len(weekday_scheduled) >= 10 else 0
    
    return metrics



# =============================================================================
# Zabbix Integration
# =============================================================================

def send_to_zabbix(metrics: Dict[str, Any], zabbix_server: str, zabbix_host: str, zabbix_port: int = 10051) -> bool:
    """Send metrics to Zabbix using zabbix_sender"""
    
    lines = []
    for key, value in metrics.items():
        if isinstance(value, str):
            value = f'"{value}"'
        lines.append(f'{zabbix_host} podcast.{key} {value}')
    
    input_data = '\n'.join(lines)
    
    try:
        result = subprocess.run(
            ['zabbix_sender', '-z', zabbix_server, '-p', str(zabbix_port), '-i', '-'],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"Successfully sent {len(metrics)} metrics to Zabbix")
            print(result.stdout)
            return True
        else:
            print(f"zabbix_sender failed: {result.stderr}", file=sys.stderr)
            return False
            
    except FileNotFoundError:
        print("Error: zabbix_sender not found.", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print("Error: zabbix_sender timed out", file=sys.stderr)
        return False


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description='feed.apwiradio.com Monitoring for Zabbix')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Check command
    check_parser = subparsers.add_parser('check', help='Calculate and print metrics')
    check_parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    # Send command
    send_parser = subparsers.add_parser('send', help='Send metrics to Zabbix')
    send_parser.add_argument('--zabbix-server', '-z', default=DEFAULT_ZABBIX_SERVER)
    send_parser.add_argument('--host', '-s', default=DEFAULT_ZABBIX_HOST)
    send_parser.add_argument('--port', '-p', type=int, default=10051)
    
    # Get single metric
    get_parser = subparsers.add_parser('get', help='Get single metric value')
    get_parser.add_argument('metric', help='Metric name')
    
    args = parser.parse_args()
    
    if args.command == 'check':
        metrics = calculate_metrics()
        if args.json:
            print(json.dumps(metrics, indent=2))
        else:
            print("Podcast Monitoring Metrics")
            print("=" * 60)
            print(f"  API Healthy:              {metrics['api_healthy']}")
            print()
            print("  PUBLISHED:")
            print(f"    Last Published Date:    {metrics['last_published_date']}")
            print(f"    Last Published Title:   {metrics['last_published_title']}")
            print(f"    Missed Weekday Posts:   {metrics['missed_weekday_posts']}")
            print()
            print("  SCHEDULED:")
            print(f"    Weekday Episodes Queued: {metrics['scheduled_weekday_count']}")
            print(f"    Has 2 Weeks (10 posts):  {'Yes' if metrics['has_two_weeks_scheduled'] else 'NO'}")
            print(f"    Next Scheduled Date:     {metrics['next_scheduled_date']}")
            print(f"    Next Scheduled Title:    {metrics['next_scheduled_title']}")
            print(f"    Last Scheduled Date:     {metrics['last_scheduled_date']}")
            print(f"    Last Scheduled Title:    {metrics['last_scheduled_title']}")
    
    elif args.command == 'send':
        metrics = calculate_metrics()
        success = send_to_zabbix(metrics, args.zabbix_server, args.host, args.port)
        sys.exit(0 if success else 1)
    
    elif args.command == 'get':
        metrics = calculate_metrics()
        if args.metric in metrics:
            print(metrics[args.metric])
        else:
            print(f"Unknown metric: {args.metric}", file=sys.stderr)
            sys.exit(1)
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()