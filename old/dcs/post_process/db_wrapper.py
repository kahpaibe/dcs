import sqlite3
import json
from logging import Logger
from typing import Optional, Any, TypedDict
from abc import abstractmethod
from dataclasses import dataclass

@dataclass
class DBColumnDescription:
    """Describes columns of a sqlite db table.
    
    This class is used in two different ways:
        1. When creating a DBWrapper object to initialize a database, provide the field types for each element as str. No element should be ommited.
        
        e.g.
        class ColDescTable1(DBColumnDescription):
            name: str # primary key
            price: Optional[int] = None
            location: Optional[str] = None
            
            def get_primary_key(self) -> str:
                return "name"
        
        ColDescTable1_descriptor = ColDescTable1()
        ColDescTable1_descriptor["name"] = "TEXT PRIMARY KEY"
        ColDescTable1_descriptor["price"] = "INTEGER"
        ColDescTable1_descriptor["location"] = "TEXT"

        2. When updating / adding an item to the database, add the values. Optional values can be ommited.

        new_item = ColDescTable1()
        ColDescTable1_descriptor["name"] = "Product 1"
        ColDescTable1_descriptor["price"] = 976"""

    @abstractmethod
    def get_primary_key(self) -> str:
        """Returns the primary key."""
        raise NotImplementedError()
    
    def get_columns_not_primary(self) -> list[str]:
        """Get list of columns that are not the primary key."""
        primary_key = self.get_primary_key()
        return [col for col in self.__dict__ if col != primary_key]
    
    def get_new_table_columns(self) -> str:
        """Get text for creating a new table, such as  item_code TEXT PRIMARY KEY, name TEXT, description TEXT, image BLOB"""
        primary_key = self.get_primary_key()
        col_desc = f"{primary_key} {self.__dict__[primary_key]}, "
        
        for colname in self.get_columns_not_primary():
            col_desc += f"{colname} {self.__dict__[colname]}, "
        col_desc = col_desc.strip(", ")
        return col_desc
    
    def strip_str_fields(self, chars: str = " \n\t") -> None:
        """Strip all elements of self.__dict__"""
        for col in self.__dict__:
            if isinstance(self.__dict__, str):
                self.__dict__[col] = self.__dict__.strip(chars)

class DBWrapper:
    """Simple class to wrap sqlite3 in a generic way."""

    def __init__(self, db_path: str, table_name: str, column_desc: DBColumnDescription, logger: Optional[Logger] = None):
        """Simple class to wrap sqlite3 in a generic way.
        
        Args:
            db_path (str): Path to .db file
            table_name (str): name of the table
            column_desc (DBColumnDescription): table columns description. Please refer to DBColumnDescription class docstring for more information.
            logger (Logger, optional): optional logger"""
        self.db_path = db_path
        self.logger = logger
        self.table_name = table_name
        self.column_desc = column_desc

        # === Init Database connection ===
        self.db_connection = sqlite3.connect(db_path)
        self.db_cursor = self.db_connection.cursor()
        self._create_db()

    def _create_db(self) -> None:
        """Create db if does not yet exist."""
        self.db_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self.table_name}'")
        if self.db_cursor.fetchone() is None:
            if self.logger:
                self.logger.info(f"DB file not found. Creating a new DB with table {self.table_name} at {self.db_path}.")
            self.db_cursor.execute(f"CREATE TABLE {self.table_name} ({self.column_desc.get_new_table_columns()})") # example: item_code TEXT PRIMARY KEY, name TEXT, description TEXT, image BLOB
            self.db_connection.commit()
    
    def save_item(self, item_description: DBColumnDescription) -> bool:
        """Save given item description. Returns whether was new.
        
        Args:
            item_description (collections.OrderedDict): Item description. Please see
        
        Return (bool): True if the item is new, False otherwise."""
        primary_key_col = self.column_desc.get_primary_key()
        if primary_key_col not in item_description.__dict__:
            raise ValueError(f"item_description is missing the primary key {primary_key_col} ! ({item_description=})")
        
        items_cur = self.db_cursor.execute(f"SELECT * FROM {self.table_name} WHERE {primary_key_col} = ?", (item_description.__dict__[primary_key_col],)) # key being item_code
        items = items_cur.fetchmany(1)  # Fetch one result to check

        if items: # Not new: update entry
            cols_no_primary_key = self.column_desc.get_columns_not_primary()
            values_to_insert: list[Any] = []
            cols_str = ""
            for col in cols_no_primary_key:
                cols_str += f"{col} = ?, "
                values_to_insert.append(item_description.__dict__[col])
            cols_str = cols_str.strip(", ")
            self.db_cursor.execute(f"UPDATE {self.table_name} SET {cols_str} WHERE {primary_key_col} = ?", values_to_insert + [item_description.__dict__[primary_key_col]]) # Primary key at the end
            self.db_connection.commit()
            if self.logger:
                self.logger.debug(f"Item {item_description.__dict__[primary_key_col]} updated in {self.table_name} ! {item_description=}.")
            return False # Was not new
        else: # New: Create entry
            cols_no_primary_key = self.column_desc.get_columns_not_primary()
            values_to_insert: list[Any] = []
            cols_str = f"{primary_key_col}, "
            placeholder_str = "?, "
            for col in cols_no_primary_key:
                cols_str += f"{col}, "
                placeholder_str += "?, "
                values_to_insert.append(item_description.__dict__[col])
            cols_str, placeholder_str = cols_str.strip(", "), placeholder_str.strip(", ")
            self.db_cursor.execute(f"INSERT INTO {self.table_name} ({cols_str}) VALUES ({placeholder_str})", [item_description.__dict__[primary_key_col]] + values_to_insert)
            self.db_connection.commit()
            if self.logger:
                self.logger.debug(f"Item {item_description.__dict__[primary_key_col]} inserted in {self.table_name} ! {item_description=}.")
            return True # Was new
            
    def json_dumps(self, path: str, ensure_ascii: Optional[bool] = False) -> None:
        """Dumps the database content to path as a json file.
        
        Args:
            path (str): path to output json file."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM {self.table_name}")
        columns = [description[0] for description in cur.description]
        results = []
        for row in cur.fetchall():
            result = dict(zip(columns, row))
            results.append(result)
        conn.close()

        encoding = "ascii" if ensure_ascii else "utf-8" 
        with open(path, 'w+', encoding=encoding) as f:
            json.dump(results, f, indent=4, ensure_ascii=ensure_ascii)
        if self.logger:
            self.logger.info(f"Dumped {self.table_name} as json to {path}")