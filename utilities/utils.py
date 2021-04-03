# File discord_bot.py & CorpBot

import json
import pytz
import time
import discord
import difflib
import logging
import datetime
import calendar
import traceback
import timeago as timesince

from io import BytesIO


def config(filename: str = "config"):
    """ Fetch default config file """
    try:
        with open(f"{filename}.json", encoding='utf8') as data:
            return json.load(data)
    except FileNotFoundError:
        raise FileNotFoundError("JSON file wasn't found")


def traceback_maker(err, advance: bool = True):
    """ A way to debug your code anywhere """
    _traceback = ''.join(traceback.format_tb(err.__traceback__))
    error = ('\n{1}{0}: {2}\n').format(type(err).__name__, _traceback, err)
    return error if advance else f"{type(err).__name__}: {err}"


def timetext(name):
    """ Timestamp, but in text form """
    return f"{name}_{int(time.time())}.txt"


def timeago(target):
    """ Timeago in easier way """
    return str(timesince.format(target)).capitalize()


def date(target, clock=True):
    """ Clock format using datetime.strftime() """
    if not clock:
        return target.strftime("%d %B %Y")
    return target.strftime("%d %B %Y, %H:%M")


def get_years(timeBetween, year, reverse):
    years = 0

    while True:
        if reverse:
            year -= 1
        else:
            year += 1

        year_days = 366 if calendar.isleap(year) else 365 
        year_seconds = year_days * 86400

        if timeBetween < year_seconds:
            break

        years += 1
        timeBetween -= year_seconds

    return timeBetween, years, year


def get_months(timeBetween, year, month, reverse):
    months = 0

    while True:
        month_days = calendar.monthrange(year, month)[1]
        month_seconds = month_days * 86400

        if timeBetween < month_seconds:
            break

        months += 1
        timeBetween -= month_seconds

        if reverse:
            if month > 1:
                month -= 1
            else:
                month = 12
                year -= 1
        else:
            if month < 12:
                month += 1
            else:
                month = 1
                year += 1

    return timeBetween, months

def time_between(first, last, reverse=False):
    # A helper function to make a readable string between two times
    timeBetween = int(last-first)
    now = datetime.datetime.now()
    year = now.year
    month = now.month

    timeBetween, years, year = get_years(timeBetween, year, reverse)
    timeBetween, months = get_months(timeBetween, year, month, reverse)
    
    weeks   = int(timeBetween/604800)
    days    = int((timeBetween-(weeks*604800))/86400)
    hours   = int((timeBetween-(days*86400 + weeks*604800))/3600)
    minutes = int((timeBetween-(hours*3600 + days*86400 + weeks*604800))/60)
    seconds = int(timeBetween-(minutes*60 + hours*3600 + days*86400 + weeks*604800))
    msg = ""

    if years > 0:
        msg += "1 year, " if years == 1 else "{:,} years, ".format(years)
    if months > 0:
        msg += "1 month, " if months == 1 else "{:,} months, ".format(months)
    if weeks > 0:
        msg += "1 week, " if weeks == 1 else "{:,} weeks, ".format(weeks)
    if days > 0:
        msg += "1 day, " if days == 1 else "{:,} days, ".format(days)
    if hours > 0:
        msg += "1 hour, " if hours == 1 else "{:,} hours, ".format(hours)
    if minutes > 0:
        msg += "1 minute, " if minutes == 1 else "{:,} minutes, ".format(minutes)
    if seconds > 0:
        msg += "1 second, " if seconds == 1 else "{:,} seconds, ".format(seconds)

    if msg == "":
        return "0 seconds"
    else:
        return msg[:-2]


def responsible(target, reason):
    """ Default responsible maker targeted to find user in AuditLogs """
    responsible = f"[ {target} ]"
    if not reason:
        return f"{responsible} no reason given..."
    return f"{responsible} {reason}"


def actionmessage(case, mass=False):
    """ Default way to present action confirmation in chat """
    output = f"**{case}** the user"

    if mass:
        output = f"**{case}** the IDs/Users"

    return f"✅ Successfully {output}"


async def prettyResults(ctx, filename: str = "Results", resultmsg: str = "Here's the results:", loop=None):
    """ A prettier way to show loop results """
    if not loop:
        return await ctx.send("The result was empty...")

    pretty = "\r\n".join([f"[{str(num).zfill(2)}] {data}" for num, data in enumerate(loop, start=1)])

    if len(loop) < 15:
        return await ctx.send(f"{resultmsg}```ini\n{pretty}```")

    data = BytesIO(pretty.encode('utf-8'))
    await ctx.send(
        content=resultmsg,
        file=discord.File(data, filename=timetext(filename.title()))
    )

def makeBar(progress):
    return '[{0}{1}] {2}%'.format('#'*(int(round(progress/2))), ' '*(50-(int(round(progress/2)))), progress)


def center(string, header = None):
    leftPad = ' '*(int(round((50-len(string))/2)))
    leftPad += string
    if header:
        output = header + leftPad[len(header):]
    else:
        output = leftPad
    return output


def edit_config(value: str, changeto: str):
    """ Change a value from the configs """
    config_name = "config.json"
    with open(config_name, "r") as jsonFile:
        data = json.load(jsonFile)
    data[value] = changeto
    with open(config_name, "w") as jsonFile:
        json.dump(data, jsonFile, indent=2)

def write_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2)


def disambiguate(term, list_to_search, key : str = None, limit : int = 3):
	"""Searches the provided list for the searchTerm - using a keyName if provided for dicts."""
	if len(list_to_search) < 1:
		return None
	# Iterate through the list and create a list of items
	findings = []
	for item in list_to_search:
		if key:
			name = item[key]
		else:
			name = item
		match_ratio = difflib.SequenceMatcher(None, term.lower(), name.lower()).ratio()
		findings.append({ 'result' : item, 'ratio' : match_ratio })
	# sort the servers by population
	findings = sorted(findings, key=lambda x:x['ratio'], reverse=True)
	if limit > len(findings):
		limit = len(findings)
	return findings[:limit]

def getClockForTime(time_string):
    # Assumes a HH:MM PP format
    try:
        t = time_string.split(" ")
        if len(t) == 2:
            t = t[0].split(":")
        elif len(t) == 3:
            t = t[1].split(":")
        else:
            return time_string
        hour = int(t[0])
        minute = int(t[1])
    except:
        return time_string
    clock_string = ""
    if minute > 44:
        clock_string = str(hour + 1) if hour < 12 else "1"
    elif minute > 14:
        clock_string = str(hour) + "30"
    else:
        clock_string = str(hour)
    return time_string +" :clock" + clock_string + ":"

def getUserTime(member, settings, time = None, strft = "%Y-%m-%d %I:%M %p", clock = True, force = None):
    # Returns a dict representing the time from the passed member's perspective
    offset = force if force else settings.getGlobalUserStat(member,"TimeZone",settings.getGlobalUserStat(member,"UTCOffset",None))
    if offset == None:
        # No offset or tz - return UTC
        t = getClockForTime(time.strftime(strft)) if clock else time.strftime(strft)
        return { "zone" : 'UTC', "time" : t, "vanity" : "{} {}".format(t,"UTC") }
    # At this point - we need to determine if we have an offset - or possibly a timezone passed
    t = getTimeFromTZ(offset, time, strft, clock)
    if t == None:
        # We did not get a zone
        t = getTimeFromOffset(offset, time, strft, clock)
    t["vanity"] = "{} {}".format(t["time"],t["zone"])
    return t

def getTimeFromOffset(offset, t = None, strft = "%Y-%m-%d %I:%M %p", clock = True):
    offset = offset.replace('+', '')
    # Split time string by : and get hour/minute values
    try:
        hours, minutes = map(int, offset.split(':'))
    except:
        try:
            hours = int(offset)
            minutes = 0
        except:
            return None
    msg = 'UTC'
    # Get the time
    if t == None:
        t = datetime.datetime.utcnow()
    # Apply offset
    if hours > 0:
        # Apply positive offset
        msg += '+{}'.format(offset)
        td = datetime.timedelta(hours=hours, minutes=minutes)
        newTime = t + td
    elif hours < 0:
        # Apply negative offset
        msg += '{}'.format(offset)
        td = datetime.timedelta(hours=(-1*hours), minutes=(-1*minutes))
        newTime = t - td
    else:
        # No offset
        newTime = t
    if clock:
        ti = getClockForTime(newTime.strftime(strft))
    else:
        ti = newTime.strftime(strft)
    return { "zone" : msg, "time" : ti }


def getTimeFromTZ(tz, t = None, strft = "%Y-%m-%d %I:%M %p", clock = True):
    # Assume sanitized zones - as they're pulled from pytz
    # Let's get the timezone list
    zone = next((pytz.timezone(x) for x in pytz.all_timezones if x.lower() == tz.lower()),None)
    if zone == None:
        return None
    zone_now = datetime.datetime.now(zone) if t == None else pytz.utc.localize(t, is_dst=None).astimezone(zone)
    ti = getClockForTime(zone_now.strftime(strft)) if clock else zone_now.strftime(strft)
    return { "zone" : str(zone), "time" : ti}

def modify_config(key, value):
    with open("./config.json", "r", encoding="utf-8") as fp:
        data = json.load(fp)
        data[key] = value
    with open("./config.json", "w") as fp:
        json.dump(data, fp, indent=2)

def load_json(file):
    with open(file, 'r', encoding='utf-8') as fp:
        data = json.load(fp)
        return data