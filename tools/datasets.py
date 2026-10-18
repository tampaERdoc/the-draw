# -*- coding: utf-8 -*-
"""The one list of datasets the site carries, in the order the dropdown shows them.

Everything that iterates datasets imports this. Four hard-coded tuples in four tools
was survivable; twenty-seven would not be.
"""
# (id, label, sort date) — date orders the menu, so a scout reads the year in order
FESTIVALS = [
    ('fya-2026',            'FYA Fest 2026',            '2026-01-10'),
    ('ldb-2026',            'LDB Fest 2026',            '2026-02-27'),
    ('newcolossus-2026',    'New Colossus 2026',        '2026-03-03'),
    ('treefort-2026',       'Treefort 2026',            '2026-03-25'),
    ('liberation-2026',     'Liberation Weekend 2026',  '2026-04-24'),
    ('stoopfest-2026',      'Stoopfest 2026',           '2026-05-08'),
    ('pouzza-2026',         'Pouzza Fest 2026',         '2026-05-15'),
    ('midwestfriends-2026', 'MidWest Friends 2026',     '2026-05-28'),
    ('tieddown-2026',       'Tied Down 2026',           '2026-05-30'),
    ('sledisland-2026',     'Sled Island 2026',         '2026-06-17'),
    ('punksylvania-2026',   'Camp Punksylvania 2026',   '2026-06-19'),
    ('punkisland-2026',     'Punk Island 2026',         '2026-06-27'),
    ('soundfury-2026',      'Sound and Fury 2026',      '2026-08-15'),
    ('bumbershoot-2026',    'Bumbershoot 2026',         '2026-09-05'),
    ('levitation-2026',     'Levitation 2026',          '2026-09-10'),
    ('hopscotch-2026',      'Hopscotch 2026',           '2026-09-10'),
    ('supernova-2026',      'Supernova Ska 2026',       '2026-09-12'),
    ('riot-2026',           'Riot Fest 2026',           '2026-09-18'),
    ('shakyknees-2026',     'Shaky Knees 2026',         '2026-09-18'),
    ('pygmalion-2026',      'Pygmalion 2026',           '2026-09-24'),
    ('fourchord-2026',      'Four Chord 2026',          '2026-09-25'),
    ('cbgb-2026',           'CBGB Festival 2026',       '2026-09-26'),
    ('furnace-2026',        'Furnace Fest 2026',        '2026-10-10'),
    ('fest-2026',           'Fest 2026',                '2026-10-23'),
    ('saltydog-2026',       'Salty Dog Cruise 2026',    '2026-10-25'),
    ('warped-2026',         'Warped Tour 2026',         '2026-11-14'),
]
LISTS = [('watchlist-2026', 'Watchlist', '')]
IDS = tuple(f[0] for f in FESTIVALS + LISTS)
