import sqlite3
import datetime

# ++++++++++++++++++
# INDIVIDUAL
# ++++++++++++++++++

class Individual:
    def __init__(self, reminder_id, r_time, role, guild_id):
        self.id = reminder_id
        self.time = r_time
        self.role = role
        self.guild_id = guild_id

def get_due_individuals(r_time):
    cursor.execute("""
        SELECT * 
        FROM individuals 
        WHERE time <= ?
    """, (r_time,))

    rows = cursor.fetchall()

    return [Individual(row[0], row[1], row[2], row[3]) for row in rows]

def get_individuals_by_id(reminder_id):
    cursor.execute("""
        SELECT *
        FROM individuals
        WHERE id = ?
    """, (reminder_id,))

    rows = cursor.fetchall()

    return [Individual(row[0], row[1], row[2], row[3]) for row in rows]

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
        INSERT INTO recurrents 
        VALUES (?, ?, ?)
    """, (offset.total_seconds(), guild_id))

    r_id = cursor.lastrowid
    events = get_events()

    new_individuals = []
    for event in events:
        new_individuals.append((r_id, event[1] + offset, event[2], guild_id))

    cursor.executemany("""
        INSERT INTO individuals 
        VALUES (?, ?, ?, ?)
    """, new_individuals)
    conn.commit()

def get_recurrent_by_time(offset):
    # offset is assumed to be a datetime.timedelta
    cursor.execute("""
        SELECT * 
        FROM recurrents
        WHERE time = ?
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

# +++++++++++++++++++++
# EVENTS
# +++++++++++++++++++++

class Event:
    def __init__(self, event_id, e_time, role, guild_id):
        self.id = event_id
        self.time = e_time
        self.role = role
        self.guild_id = guild_id

def add_event(e_time, role, guild_id):
    cursor.execute("""
        INSERT INTO events
        VALUES (?, ?, ?, ?)
    """, (e_time.total_seconds(), role, guild_id))

    r_id = cursor.lastrowid
    recurrents = get_recurrents()

    new_individuals = []
    for recurrent in recurrents:
        new_individuals.append((r_id, e_time + recurrent.offset, role, guild_id))

    cursor.executemany("""
            INSERT INTO individuals 
            VALUES (?, ?, ?, ?)
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
    return Event(row[0], row[2], row[2], row[3])

def get_events_by_time(event_time):
    cursor.execute("""
        SELECT *
        FROM events
        WHERE time = ?
    """, (event_time,))

    rows = cursor.fetchall()

    ret = []
    for row in rows:
        ret.append(Event(row[0], row[1], row[2], row[3]))
    return ret

def get_events():
    cursor.execute("""
        SELECT *
        FROM events
    """)

    rows = cursor.fetchall()

    ret = []
    for row in rows:
        ret.append(Event(row[0], row[1], row[2], row[3]))
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

conn = sqlite3.connect("database.db", detect_types=sqlite3.PARSE_DECLTYPES)
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS individuals (
    schedule_id INTEGER NOT NULL,
    time TIMESTAMP NOT NULL,
    event_id INTEGER NOT NULL,
    guild_id INTEGER NOT NULL
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
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    time TIMESTAMP NOT NULL,
    role TEXT DEFAULT 'everyone',
    guild_id INTEGER NOT NULL
""")

conn.commit()