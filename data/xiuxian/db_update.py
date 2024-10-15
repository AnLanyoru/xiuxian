import sqlite3
from pathlib import Path

DATABASE = Path()
database_path = DATABASE
database_path /= "xiuxian.db"
conn = sqlite3.connect(database_path, check_same_thread=False)

"""
这里输入你想修改的表的列名字
"""
all_update_colum = ['exp', 'hp', 'mp', 'power', 'atk']


def update_db(colum: str):
    c = conn.cursor()

    TableName = 'user_xiuxian'
    ColName = colum
    NewFileType = 'decimal(1000,0)'
    sql = 'ALTER TABLE ' + TableName + ' RENAME COLUMN ' + ColName + ' TO ' + ColName + '_old'
    c.execute(sql)
    sql = 'ALTER TABLE ' + TableName + ' ADD COLUMN ' + ColName + ' ' + NewFileType
    c.execute(sql)
    sql = 'UPDATE ' + TableName + ' SET ' + ColName + ' = CAST(' + ColName + '_old AS ' + NewFileType + ')'
    c.execute(sql)
    sql = 'ALTER TABLE ' + TableName + ' DROP COLUMN ' + ColName + '_old'
    c.execute(sql)
    conn.commit()
    print(f"update {colum} success")


if __name__ == "__main__":
    for colum in all_update_colum:
        update_db(colum)
