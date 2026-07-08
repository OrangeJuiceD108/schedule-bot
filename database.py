import sqlite3
import datetime
import os

# ++++++++++++++++++
# INDIVIDUAL
# ++++++++++++++++++

class Individual:
    def __init__(self, reminder_id, r_time, event_id, role, guild_id, event_title):
        self.id = reminder_id
        self.time = r_time
        self.event_id = event_id
        self.role = role
        self.guild_id = guild_id
        self.event_title = event_title

def get_due_individuals(r_time):
    cursor.execute("""
        SELECT * 
        FROM individuals 
        WHERE time <= ?
    """, (r_time,))

    rows = cursor.fetchall()

    return [Individual(row[0], row[1].replace(tzinfo=datetime.timezone.utc), row[2], row[3], row[4], row[5]) for row in rows]

def get_individuals_by_id(reminder_id):
    cursor.execute("""
        SELECT *
        FROM individuals
        WHERE schedule_id = ?
    """, (reminder_id,))

    rows = cursor.fetchall()

    return [Individual(row[0], row[1].replace(tzinfo=datetime.timezone.utc), row[2], row[3], row[4], row[5]) for row in rows]

def remove_due_individuals(r_time):
    cursor.execute("""
        DELETE FROM individuals
        WHERE time <= ?
    """, (r_time,))
    conn.commit()

def remove_individuals_by_id(reminder_id):
    cursor.execute("""
        DELETE FROM individuals
        WHERE id = ?
    """, (reminder_id,))
    conn.commit()

# ++++++++++++++++++
# RECURRENT
# ++++++++++++++++++

class Recurrent:
    def __init__(self, reminder_id, offset, guild_id):
        self.id = reminder_id
        self.offset = offset
        self.guild_id = guild_id

# offset is a datetime.timedelta
def add_recurrent(offset, guild_id):
    cursor.execute("""
        INSERT INTO recurrents (offset, guild_id)
        VALUES (?, ?)
    """, (offset.total_seconds(), guild_id))

    r_id = cursor.lastrowid
    events = get_events()

    new_individuals = []
    for event in events:
        individual_time = (event.time - offset).replace(tzinfo=None)
        new_individuals.append((r_id, individual_time, event.id, event.role, guild_id, event.title))

    cursor.executemany("""
        INSERT INTO individuals 
        VALUES (?, ?, ?, ?, ?, ?)
    """, new_individuals)
    conn.commit()

def get_recurrent_by_offset(offset):
    # offset is assumed to be a datetime.timedelta
    cursor.execute("""
        SELECT * 
        FROM recurrents
        WHERE offset = ?
    """, (offset.total_seconds(),))

    row = cursor.fetchone()
    if not row:
        return None
    return Recurrent(row[0], datetime.timedelta(seconds=row[1]), row[2])

def get_recurrent_by_id(reminder_id):
    cursor.execute("""
        SELECT *
        FROM recurrents
        WHERE id = ?
    """, (reminder_id,))

    row = cursor.fetchone()
    if not row:
        return None
    return Recurrent(row[0], datetime.timedelta(seconds=row[1]), row[2])

def get_recurrents():
    cursor.execute("""
        SELECT *
        FROM recurrents
    """)

    rows = cursor.fetchall()

    ret = []
    for row in rows:
        ret.append(Recurrent(row[0], datetime.timedelta(seconds=row[1]), row[2]))
    return ret

def remove_recurrent_by_id(reminder_id):
    cursor.execute("""
            DELETE FROM recurrents
            WHERE id == ?
        """, (reminder_id,))

    cursor.execute("""
        DELETE FROM individuals
        WHERE schedule_id = ?
    """, (reminder_id,))

    conn.commit()

def remove_recurrent_by_offset(offset):
    recurrent = get_recurrent_by_offset(offset)
    remove_recurrent_by_id(recurrent.id)

# +++++++++++++++++++++
# EVENTS
# +++++++++++++++++++++

class Event:
    def __init__(self, event_id, e_time, role, guild_id, title):
        self.id = event_id
        self.time = e_time
        self.role = role
        self.guild_id = guild_id
        self.title = title

def add_event(e_id, e_time, role, guild_id, title):
    e_time = e_time.astimezone(datetime.timezone.utc).replace(tzinfo=None)
    cursor.execute("""
        INSERT INTO events
        VALUES (?, ?, ?, ?, ?)
    """, (e_id, e_time, role, guild_id, title))

    recurrents = get_recurrents()

    new_individuals = []
    for recurrent in recurrents:
        new_individuals.append((recurrent.id, e_time - recurrent.offset, e_id, role, guild_id, title))

    cursor.executemany("""
            INSERT INTO individuals 
            VALUES (?, ?, ?, ?, ?, ?)
        """, new_individuals)
    conn.commit()

def get_event_by_id(event_id):
    cursor.execute("""
        SELECT *
        FROM events
        WHERE id = ?
    """, (event_id,))

    row = cursor.fetchone()
    if not row:
        return None
    return Event(row[0], row[1].replace(tzinfo=datetime.timezone.utc), row[2], row[3], row[4])

def get_events_by_time(event_time):
    cursor.execute("""
        SELECT *
        FROM events
        WHERE time = ?
    """, (event_time,))

    rows = cursor.fetchall()

    ret = []
    for row in rows:
        ret.append(Event(row[0], row[1].replace(tzinfo=datetime.timezone.utc), row[2], row[3], row[4]))
    return ret

def get_events():
    cursor.execute("""
        SELECT *
        FROM events
    """)

    rows = cursor.fetchall()

    ret = []
    for row in rows:
        ret.append(Event(row[0], row[1].replace(tzinfo=datetime.timezone.utc), row[2], row[3], row[4]))
    return ret

def remove_event(event_id):
    cursor.execute("""
        DELETE FROM events
        WHERE id == ?
    """, (event_id,))

    cursor.execute("""
        DELETE FROM individuals
        WHERE event_id = ?
    """, (event_id,))

    conn.commit()

def remove_due_events(e_time):
    cursor.execute("""
        DELETE FROM events
        WHERE time <= ?
    """, (e_time,))

    conn.commit()

# +++++++++++++++++++++
# INITIALIZATION
# +++++++++++++++++++++

db_path = os.path.join('data', 'database.db')
conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS individuals (
    schedule_id INTEGER NOT NULL,
    time TIMESTAMP NOT NULL,
    event_id INTEGER NOT NULL,
    event_role TEXT DEFAULT 'everyone',
    guild_id INTEGER NOT NULL,
    event_title TEXT NOT NULL
    )
""")

cursor.execute("""    
    CREATE TABLE IF NOT EXISTS recurrents (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    offset INTEGER NOT NULL,
    guild_id INTEGER NOT NULL
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
    id INTEGER NOT NULL PRIMARY KEY,
    time TIMESTAMP NOT NULL,
    role TEXT DEFAULT 'everyone',
    guild_id INTEGER NOT NULL,
    event_title TEXT NOT NULL
    )
""")

conn.commit()