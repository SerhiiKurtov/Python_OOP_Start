import sqlite3

import calendar

class Database :
    def __init__(self, db_name) :
        self.conn = sqlite3.connect(db_name)
        self.cur = self.conn.cursor()
        self.create_tables()

    def execute_query(self, query, params=()) :
        self.cur.execute(query, params)
        self.conn.commit()
        return self.cur.lastrowid

    def fetch_all(self, query, params=()) :
        self.cur.execute(query, params)
        return self.cur.fetchall()

    def create_tables(self) :
        self.cur.executescript("""
            CREATE TABLE IF NOT EXISTS "Schedule" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "master_id" INTEGER,
                "work_date" TEXT NOT NULL,
                "work_time" TEXT NOT NULL,
                "is_available" INTEGER DEFAULT 1,
                FOREIGN KEY ("master_id") REFERENCES "Masters" ("id")
            );
            
            CREATE TABLE IF NOT EXISTS "Masters" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "name" TEXT NOT NULL,
                "specialization" TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS "MasterProcedures" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                "master_id" INTEGER,
                "procedure_id" INTEGER,
                FOREIGN KEY ("master_id") REFERENCES "Masters" ("id"),
                FOREIGN KEY ("procedure_id") REFERENCES "Procedure" ("id")                  
            );                   
                               
            CREATE TABLE IF NOT EXISTS "Client" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                "name" TEXT NOT NULL,
                "phone" TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS "Procedure" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                "title" TEXT NOT NULL,
                "price" INTEGER
            );

            CREATE TABLE IF NOT EXISTS "Bookings" (
                "status" TEXT DEFAULT 'pending',
                "master_id" INTEGER,
                "id" INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                "client_id" INTEGER,
                "procedure_id" INTEGER,
                "full_time" TEXT NOT NULL,
                FOREIGN KEY ("client_id") REFERENCES "Client" ("id"),
                FOREIGN KEY ("procedure_id") REFERENCES "Procedure" ("id")
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_master_date_time ON Schedule (master_id, work_date, work_time);
    """)
        
class AdminManager :
    def __init__(self, db) :
        self.db = db

    def add_master(self) :
        m_name = input("Введіть імя майстра: ")
        m_spec = input("Введіть спеціалізацію: ")
        try :
            self.db.execute_query("INSERT INTO Masters (name, specialization) VALUES (?, ?)", (m_name, m_spec))
        except Exception as e :
            print(f"Виникла помилка: {e}")

    def add_procedure(self) :
        while True :
            p_title = input("Введіть назву процедури (для завершення введіть стоп): ")
            if p_title.lower() == 'стоп' :
                break
            try :
                p_price = int(input("Введіть ціну: ").strip())
            except ValueError :
                print("Помилка! Ціна має бути числом. Спробуйте ще раз.")
                continue
            new_p_id = self.db.execute_query("INSERT INTO Procedure (title, price) VALUES (?, ?)", (p_title, p_price))
            print(f"Процедура {p_title}, ціна {p_price} збережено!")

            self.show_all_masters()
            m_ids_input = input("Введіть ID майстрів через пробіл: ").strip().split()
            for m_id in m_ids_input :
                if m_id.isdigit() :
                    self.db.execute_query("INSERT INTO MasterProcedures (master_id, procedure_id) VALUES (?, ?)", (m_id, new_p_id))

    def show_all_masters(self) :
        rows = self.db.fetch_all("SELECT id, name, specialization FROM Masters")
        if not rows :
            print("Майстра не існує!")
        else :
            for row in rows :
                print(f"ID: {row[0]:<3} | Майстер: {row[1]:<30} | Спеціальність: {row[2]:<30}")

    def add_schedule(self) :
        try :
            m_id = int(input("Введіть ID майстра: ").strip())
        except Exception as e :
            print(f"Виникла помилка: {e}")
            return
        res = self.db.fetch_all("SELECT id FROM Masters WHERE id = ?", (m_id,))
        if not res:
            print("Помилка! Майстра з таким ID не існує.")
            return
        try :
            year = int(input("Виберіть рік (наприклад 2026): ").strip())
            month = int(input("Виберіть місяць від 1 до 12: ").strip())
        except Exception as e :
            print(f"Виникла помилка: {e}, введіть данні цифрами!")
            return
        
        num_day = calendar.monthrange(year, month)[1]

        time_day = []
        while True :
            hour = input("Введіть час прийому, для завершення введіть стоп: ").strip()
            if hour.lower() == 'стоп' :
                print("Робоці години визначені!")
                break
            time_day.append(hour)

        for day in range(1, num_day + 1) :
            current_data = f"{year}-{month:02}-{day:02}"
            for hour in time_day :
                try :
                    self.db.execute_query("INSERT INTO Schedule (master_id, work_date, work_time) VALUES (?, ?, ?)", (m_id, current_data, hour))
                except sqlite3.IntegrityError :
                    print(f"Помилка: Час {hour} на цю дату вже існує!")
                except Exception as e :
                    print(f"Виникла помилка: {e}")

        weekend_input = input("Введіть числа місяця, які будуть вихідними (через пробіл): ").strip().split()
        for day_off in weekend_input :
            if day_off.isdigit() :
                weekends = f"{year}-{month:02}-{int(day_off):02}"
                self.db.execute_query("UPDATE Schedule SET is_available = 2 WHERE work_date = ?", (weekends,))
                print(f"Вихідні: {weekends}")

    def confirm_booking(self) :
        while True :
            rows = self.db.fetch_all('''
                SELECT Bookings.id, Bookings.status, Client.name, Masters.name, Procedure.title, Bookings.full_time
                FROM Bookings
                JOIN Client ON Bookings.client_id = Client.id
                JOIN Procedure ON Bookings.procedure_id = Procedure.id
                JOIN Masters ON Bookings.master_id = Masters.id
                WHERE Bookings.status = 'pending'
            ''')
            if not rows :
                print("Запису не існує")
                break
            else :
                for row in rows :
                    print(f"ID: {row[0]:<3} | Статус: {row[1]:<30} | Клієнт: {row[2]:<30} | Майстер: {row[3]:<30} | Процедура: {row[4]:<30} | Дата: {row[5]:<30}")

            confirm = input("Виберіть ID для підтвердження(стоп для завершення):").strip()
            if confirm.lower() == 'стоп' :
                print("Допобачення")
                break
            elif confirm.isdigit() :
                self.db.execute_query("UPDATE Bookings SET status = ? WHERE id = ?", ('confirmed', confirm))
                print(f"Запис №{confirm} підтверджено!")
            else :
                print("Введіть коректне ID")

class ClientManager :
    def __init__(self, db) :
        self.db = db

    def show_showcase(self) :
        data = self.db.fetch_all('''
            SELECT Masters.id, Masters.name, Masters.specialization, Procedure.title, Procedure.price
            FROM Masters JOIN MasterProcedures
            ON Masters.id = MasterProcedures.master_id
            JOIN Procedure
            ON MasterProcedures.procedure_id = Procedure.id
            ORDER BY Masters.name
        ''')

        last_id = None
        for row in data :
            name = row[1]
            if name != last_id :
                print(f"{'-'*20}\nID: {row[0]} | Майстер: {name} | Спеціальність: {row[2]}")
                last_id = name
            print(f"  - {row[3]}: {row[4]} грн")

        try :
            id_master = int(input("Оберіть ID майстра якого бажаєте: ").strip())
        except :
            print("Введіть значення цифрою")
            return
        full_procedures = self.db.fetch_all('''
            SELECT Procedure.id, Procedure.title, Procedure.price
            FROM Procedure JOIN MasterProcedures
            ON Procedure.id = MasterProcedures.procedure_id
            WHERE MasterProcedures.master_id = ?
        ''', (id_master,))

        if not full_procedures :
            print("У цього майстра немає доступних послуг або ID невірний.")
            return
        
        for proc in full_procedures :
            print(f"ID процедури: {proc[0]} | {proc[1]} - {proc[2]} грн")

        try :
            id_procedure = int(input("Оберіть ID процедури яку бажаєте: ").strip())
        except :
            print("Введіть значення цифрою")
            return
        
        reserved_time = self.db.fetch_all("SELECT id, work_date, work_time FROM Schedule WHERE master_id = ? AND is_available = 1", (id_master,))
        for res in reserved_time :
            print(f"ID: {res[0]} | Дата: {res[1]:<15} | Час: {res[2]:<15}")

        try :
            id_slot = int(input("Оберіть ID бажаної дати та часу: ").strip())
        except :
            print("Введіть значення цифрою")
            return
        
        final_time = None
        for rows in reserved_time :
            if rows[0] == id_slot :
                final_time = f"{rows[1]} {rows[2]}"
        if final_time is None:
            return

        self.save_booking(id_master, id_procedure, id_slot, final_time)

    def save_booking(self, m_id, p_id, s_id, f_time) :
        while True :
            name = input("Введіть ваше ім'я та прізвище: ")
            if " " in name and len(name) >= 5 :
                break
            else :
                print("Помилка: введіть, будь ласка, і ім'я, і прізвище!")

        while True :
            phone = input("Введіть номер телефону: ").strip()
            if phone.isdigit() and len(phone) == 10 :
                print("Дякуємо! Номер прийнято.")
                break
            else :
                print("Введіть коретний номер телефону!")

        c_id = self.db.execute_query("INSERT INTO Client (name, phone) VALUES (?, ?)", (name, phone))
        self.db.execute_query("INSERT INTO Bookings (master_id, client_id, procedure_id, full_time) VALUES (?, ?, ?, ?)", (m_id, c_id, p_id, f_time))
        self.db.execute_query("UPDATE Schedule SET is_available = 0 WHERE id = ?", (s_id,))