"""Create reproducible SYNTHETIC warehouse training records; no company data."""
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

DB = Path(__file__).with_name('warehouse_demo.db')

def setup():
    if DB.exists():
        return
    random.seed(20261012)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.executescript('''
    CREATE TABLE warehouses (warehouse_id INTEGER PRIMARY KEY, warehouse_name TEXT NOT NULL);
    CREATE TABLE products (product_id INTEGER PRIMARY KEY, product_name TEXT NOT NULL, category TEXT NOT NULL);
    CREATE TABLE employees (employee_id INTEGER PRIMARY KEY, employee_name TEXT NOT NULL, warehouse_id INTEGER NOT NULL);
    CREATE TABLE orders (
      order_id INTEGER PRIMARY KEY, warehouse_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
      employee_id INTEGER NOT NULL, order_date TEXT NOT NULL, promised_date TEXT NOT NULL,
      shipped_date TEXT, quantity INTEGER NOT NULL, amount REAL NOT NULL,
      FOREIGN KEY(warehouse_id) REFERENCES warehouses(warehouse_id),
      FOREIGN KEY(product_id) REFERENCES products(product_id)
    );
    CREATE TABLE inventory (
      warehouse_id INTEGER NOT NULL, product_id INTEGER NOT NULL, book_qty INTEGER NOT NULL,
      physical_qty INTEGER NOT NULL, PRIMARY KEY(warehouse_id, product_id)
    );
    ''')
    warehouses = [(1, '华北一仓'), (2, '华东一仓'), (3, '华南一仓'), (4, '华中一仓'), (5, '西南一仓')]
    cur.executemany('INSERT INTO warehouses VALUES (?,?)', warehouses)
    categories=['数码配件','日用百货','家居用品','办公用品']
    products=[(i, f'{categories[(i-1)%4]}-{i:02d}', categories[(i-1)%4]) for i in range(1,25)]
    cur.executemany('INSERT INTO products VALUES (?,?,?)',products)
    employees=[]
    for w in range(1,6):
        for n in range(1,7):
            eid=(w-1)*6+n
            employees.append((eid, f'员工{eid:02d}',w))
    cur.executemany('INSERT INTO employees VALUES (?,?,?)',employees)
    orders=[]
    start=datetime(2026,9,1)
    for i in range(1,1801):
        wid=random.choices(range(1,6),weights=[5,4,3,4,2])[0]
        pid=random.randint(1,24)
        eid=(wid-1)*6+random.randint(1,6)
        d=start+timedelta(days=random.randint(0,29))
        promise=d+timedelta(days=1)
        r=random.random()
        if r<0.82:
            shipped=d+timedelta(days=random.choice([0,1]))
        elif r<0.93:
            shipped=d+timedelta(days=random.choice([2,3]))
        else:
            shipped=None
        quantity=random.randint(1,5)
        amount=round(quantity*random.uniform(15,300),2)
        orders.append((i,wid,pid,eid,d.strftime('%Y-%m-%d'),promise.strftime('%Y-%m-%d'),shipped.strftime('%Y-%m-%d') if shipped else None,quantity,amount))
    cur.executemany('INSERT INTO orders VALUES (?,?,?,?,?,?,?,?,?)',orders)
    inventory=[]
    for w,_ in warehouses:
        for pid,_,_ in products:
            book=random.randint(0,200)
            physical=max(0,book+random.choice([0,0,0,0,0,-5,-3,-1,2,4]))
            inventory.append((w,pid,book,physical))
    cur.executemany('INSERT INTO inventory VALUES (?,?,?,?)',inventory)
    con.commit()
    con.close()

if __name__=='__main__':
    setup()
    print(f'Created synthetic database: {DB}')
