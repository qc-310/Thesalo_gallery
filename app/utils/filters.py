from datetime import datetime, timedelta
import dateutil.parser

def format_datetime(value, format="%Y/%m/%d %H:%M"):
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = dateutil.parser.parse(value)
        except:
            return value
    return value.strftime(format)

def friendly_date(value):
    """
    Returns a 'cute' and easy to understand date string.
    e.g. "今日", "昨日", "12月23日"
    """
    if not value:
        return ""
    
    if isinstance(value, str):
        try:
            date_obj = dateutil.parser.parse(value)
        except:
            return value
    else:
        date_obj = value
    
    # Convert to JST if naive (assume UTC) or convert timezone
    if date_obj.tzinfo is None:
         # Assume UTC, make it JST
         date_obj = date_obj + timedelta(hours=9)
    else:
         # Convert to JST (UTC+9)
         target_tz = datetime.timezone(timedelta(hours=9))
         date_obj = date_obj.astimezone(target_tz)

    # Get current time in JST
    now = datetime.utcnow() + timedelta(hours=9)
    diff = now.date() - date_obj.date()
    
    if diff.days == 0:
        return f"今日 {date_obj.strftime('%H:%M')}"
    elif diff.days == 1:
        return f"昨日 {date_obj.strftime('%H:%M')}"
    else:
        # Always show year as requested
        return date_obj.strftime("%Y年%-m月%-d日")
