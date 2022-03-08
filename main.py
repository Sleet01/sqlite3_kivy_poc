#!/usr/bin/env python3

"""
POC sqlite creater / loader / reader / button maker.
"""

import kivy
kivy.require('2.0.0')
import os
import random
import sqlite3

from kivy.app import App
from kivy.logger import Logger, LOG_LEVELS
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from contextlib import closing
from typing import Any, List, NamedTuple, Optional, Tuple, Union

# CONSTANTS
DB_NAME = 'test.db'
COLORS = ['1_0.0_0.0', '0.0_1_0.0', '0.0_0.0_1', '0.5_0.5_0.5', '0.0_0.0_0.0', '1_1_1']
TEXTS = [
            'Test text 1',
            'blah blah blah',
            'New info: top secret!',
            'Test text 2',
            'Lorem Ipsum',
            'That\'s My Bag'
        ]

# Logger config
Logger.setLevel(LOG_LEVELS["debug"])
# Logger.setLevel(LOG_LEVELS["info"])

class EntryButton(Button):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Need this to allow multiple buttons in EntryLayout (GridLayout)
        self.size_hint_y = None

class EntryLayout(GridLayout):
    pass

class SqliteAppRoot(ScrollView):
    pass

class SqliteApp(App):
    """
    App that populates a sqlite3 database, then reads entries out and creates new widgets
    from them.
    """

    def __init__(self, *args, **kwargs) -> None:
        """
        Init this app, including some app-specific stuff like files and configs.
        """
        super().__init__(*args, **kwargs)
        self.sqlite_dir = self.init_sqlite3_dir()
        self.initialized = self.init_sqlite3(self.sqlite_dir)

    def build(self) -> Widget:
        return SqliteAppRoot()

    def on_stop(self):
        """Clear sqlite DB"""
        return self.delete_sqlite_entries(os.path.join(self.sqlite_dir, DB_NAME), 'entries')

    def init_sqlite3(self, sqlite_dir: str) -> bool:
        """
        Create sqlite3 db in directory.
        """
        success = False
        if sqlite_dir is None:
            logging.debug('Bad sqlite dir "None"!')
            return success
        try:
            with closing(sqlite3.connect(os.path.join(sqlite_dir, DB_NAME))) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("CREATE TABLE IF NOT EXISTS entries (text TEXT, color TEXT)")
                    count = len(cursor.execute("SELECT COUNT(*) FROM entries").fetchall())
                    Logger.debug(f'Found {count} existing entries')

                    if not count >= 100:
                        Logger.info(f'Only found {count} entries; adding {100 - count} more...')
                        for _ in range(0, (101 - count)):
                            text = random.choice(TEXTS)
                            color = random.choice(COLORS)
                            cursor.execute(
                                    "INSERT INTO entries VALUES (?, ?)",
                                    (text, color)
                            )
                            Logger.debug(f'Added new entry of ({text}, {color})')

                    # Commit updates
                    conn.commit()

            success = True
            Logger.debug(f'Finished creating table "entries".')
        except:
            Logger.exception(f'Error creating table "entries"!')

        Logger.info('Sqlite3 initialization complete')
        return success

    def init_sqlite3_dir(self) -> str:
        """
        Set up sqlite3
        """
        folder = None
        root_folder = self.user_data_dir
        sqlite_folder = os.path.join(root_folder, 'sqlite')
        try:
            if not os.path.exists(sqlite_folder):
                os.makedirs(sqlite_folder)
                Logger.debug(f'Created folder "{sqlite_folder}"')
            folder = sqlite_folder
        except:
            Logger.exception(f'Error creating folder "{sqlite_folder}"!')

        Logger.info(f'Sqlite3 folder is: {folder}')
        return folder

    def ingest_sqlite3(self, sqlite_path: str) -> List[Any]:
        """
        Read in sqlite3 DB and produce list of entries in consumable format.
        """
        entry_list = []
        try:
            with closing(sqlite3.connect(sqlite_path)) as conn:
                with closing(conn.cursor()) as cursor:
                    lines = cursor.execute("SELECT * FROM entries;")
                    entry_list = lines.fetchall()
        except:
            Logger.exception(f'Failed to read in db at "{sqlite_path}"!')

        return entry_list

    def delete_sqlite_entries(self, sqlite_path: str, table_name: str) -> bool:
        """Delete all entries from specified table"""
        try:
            with closing(sqlite3.connect(sqlite_path)) as conn:
                with closing(conn.cursor()) as cursor:
                    cmd = f'DELETE FROM {table_name};'
                    cursor.execute(cmd)
                    deleted = cursor.rowcount
                    Logger.debug(f'Deleted {int(deleted)} rows.')

                # Commit updates
                conn.commit()
        except:
            Logger.exception(f'Failed in delete_sqlite_entries!')
            return False

        return True

    def load_buttons(self) -> bool:
        """
        When called, loads a list of button defnitions from a sqlite3 DB, instantiates them,
        and adds them to the main_layout within the root widget.
        """
        success = True
        try:
            filepath = os.path.join(self.sqlite_dir, DB_NAME)
            lines = self.ingest_sqlite3(filepath)
            Logger.debug(f'Total lines: {str(lines)}')
            for line in lines:
                self.add_entry_to_layout(self.root.ids.main_layout, self.load_button(line))

        except:
            Logger.exception(f'Failure during loading of EntryButtons!')
            return False

        return True
            

    def load_button(self, button_tuple: Tuple[str, str]) -> EntryButton:
        """Turn a tuple of strings of format (<text>, color>) into an EntryButton."""
        text = button_tuple[0]
        color = tuple(button_tuple[1].split('_') + [1,])
        new_button = EntryButton(text=text, background_color=color)
        Logger.debug(f'New button is {new_button}')
        return new_button

    def add_entry_to_layout(self, layout, entry) -> bool:
        """
        Add an entry to a given layout.
        """
        success = False
        try:
            Logger.debug(f'Adding entry {entry} to layout {layout}')
            layout.add_widget(entry)
            success = True
        except:
            Logger.exception(f'Failure adding entry {entry} to layout {layout}!')

        return success

if __name__ == '__main__':
    SqliteApp().run()
