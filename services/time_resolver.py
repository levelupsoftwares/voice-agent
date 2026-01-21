from datetime import timedelta
import pytz
import dateparser

def resolve_time(intent: dict, current_dt: str = None):
    """
    Resolve human-friendly date/time input to ISO-8601 start and end datetime.
    
    intent example:
    {
        "text": "tomorrow at 2:30 PM"
    }
    """
    TZ = pytz.timezone("Asia/Karachi")

    # Use provided current datetime as base, else now
    if current_dt:
        now = pytz.timezone("Asia/Karachi").localize(dateparser.parse(current_dt))
    else:
        now = pytz.timezone("Asia/Karachi").localize(dateparser.parse("now"))

    # Parse user-friendly input
    dt_text = intent.get("text", "")
    parsed_dt = dateparser.parse(
        dt_text,
        settings={
            "TIMEZONE": "Asia/Karachi",
            "RETURN_AS_TIMEZONE_AWARE": True,
            "RELATIVE_BASE": now
        }
    )

    if not parsed_dt:
        raise ValueError(f"Could not understand date/time input: '{dt_text}'")

    start_dt = parsed_dt
    end_dt = start_dt + timedelta(minutes=45)  # default meeting duration

    return {
        "start": start_dt.isoformat(timespec="seconds"),
        "end": end_dt.isoformat(timespec="seconds"),
    }
