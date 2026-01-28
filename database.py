import sqlite3
import datetime

class Database:
    def __init__(self, db_name="meus_projetos.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.check_and_migrate()
        self.seed_data()

    def create_tables(self):
        # Tabela de Configurações Financeiras
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                custo_mensal REAL,
                horas_mensais REAL,
                imposto_padrao REAL,
                lucro_padrao REAL,
                meta_mensal REAL DEFAULT 10000.0,
                nome_usuario TEXT DEFAULT 'Visitante'
            )
        """)

        # Tabela de Catálogo de Serviços
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS catalogo_servicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                horas_padrao REAL,
                categoria TEXT DEFAULT 'Geral'
            )
        """)

        # Tabela de Custos Operacionais
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS custos_operacionais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT,
                valor REAL
            )
        """)

        # Tabela de Projetos
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS projetos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente TEXT,
                data_criacao TEXT,
                data_entrega TEXT,
                status TEXT,
                custo_extras REAL,
                preco_final REAL,
                categoria TEXT DEFAULT 'Geral',
                data_atualizacao TEXT
            )
        """)

        # Tabela de Tarefas salvas em cada Projeto
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS tarefas_projeto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                projeto_id INTEGER,
                descricao TEXT,
                horas_estimadas REAL,
                FOREIGN KEY(projeto_id) REFERENCES projetos(id)
            )
        """)
        self.conn.commit()

    def check_and_migrate(self):
        # Verifica colunas em 'catalogo_servicos'
        self.cursor.execute("PRAGMA table_info(catalogo_servicos)")
        cols = [info[1] for info in self.cursor.fetchall()]
        if "categoria" not in cols:
            print("Migrando DB: Adicionando coluna 'categoria' em catalogo_servicos...")
            self.cursor.execute("ALTER TABLE catalogo_servicos ADD COLUMN categoria TEXT DEFAULT 'Geral'")

            # Atualiza categorias padrão para dados existentes (tentativa heurística)
            mapping = {
                "Pré-Projeto": ["Fechamento", "Pesquisa", "Pré-projeto", "Reuniões (Pré"],
                "Execução": ["Projeto", "Modelagem", "Reuniões (Exe", "Correções"],
                "Pós-Produção": ["Render", "Detalhamento", "Entrega"]
            }
            for cat, keywords in mapping.items():
                for kw in keywords:
                    self.cursor.execute(f"UPDATE catalogo_servicos SET categoria = ? WHERE nome LIKE ?", (cat, f"%{kw}%"))
            self.conn.commit()

        # Verifica colunas em 'configuracoes'
        self.cursor.execute("PRAGMA table_info(configuracoes)")
        cols = [info[1] for info in self.cursor.fetchall()]
        if "meta_mensal" not in cols:
            print("Migrando DB: Adicionando coluna 'meta_mensal' em configuracoes...")
            self.cursor.execute("ALTER TABLE configuracoes ADD COLUMN meta_mensal REAL DEFAULT 10000.0")
        if "nome_usuario" not in cols:
            print("Migrando DB: Adicionando coluna 'nome_usuario' em configuracoes...")
            self.cursor.execute("ALTER TABLE configuracoes ADD COLUMN nome_usuario TEXT DEFAULT 'Visitante'")

        # Verifica colunas em 'projetos'
        self.cursor.execute("PRAGMA table_info(projetos)")
        cols = [info[1] for info in self.cursor.fetchall()]

        if "data_entrega" not in cols:
            print("Migrando DB: Adicionando coluna 'data_entrega' em projetos...")
            self.cursor.execute("ALTER TABLE projetos ADD COLUMN data_entrega TEXT")

        if "categoria" not in cols:
            print("Migrando DB: Adicionando coluna 'categoria' em projetos...")
            self.cursor.execute("ALTER TABLE projetos ADD COLUMN categoria TEXT DEFAULT 'Geral'")

        if "data_atualizacao" not in cols:
            print("Migrando DB: Adicionando coluna 'data_atualizacao' em projetos...")
            self.cursor.execute("ALTER TABLE projetos ADD COLUMN data_atualizacao TEXT")
            # Populate with data_criacao for existing records
            self.cursor.execute("UPDATE projetos SET data_atualizacao = data_criacao WHERE data_atualizacao IS NULL")

        self.conn.commit()

    def seed_data(self):
        # Seed Configurações
        self.cursor.execute("SELECT count(*) FROM configuracoes")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("""
                INSERT INTO configuracoes (custo_mensal, horas_mensais, imposto_padrao, lucro_padrao, meta_mensal, nome_usuario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (5495.0, 180.0, 32.0, 30.0, 15000.0, "Okami"))
            self.conn.commit()

        # Seed Catálogo de Serviços
        self.cursor.execute("SELECT count(*) FROM catalogo_servicos")
        if self.cursor.fetchone()[0] == 0:
            tarefas_iniciais = [
                ("Fechamento Orçamentário", 4, "Pré-Projeto"),
                ("Pesquisa de referencias", 4, "Pré-Projeto"),
                ("Pesquisa a campo", 10, "Pré-Projeto"),
                ("Pré-projeto", 1, "Pré-Projeto"),
                ("Projeto pré executivo", 1, "Execução"),
                ("Reuniões (Pré-executivo)", 12, "Pré-Projeto"),
                ("Modelagem 3D", 1, "Execução"),
                ("Projeto executivo", 1, "Execução"),
                ("Reuniões (Executivo)", 5, "Execução"),
                ("Correções 3D", 4, "Execução"),
                ("Renderização", 7, "Pós-Produção"),
                ("Detalhamentos finais", 2, "Pós-Produção"),
                ("Entrega", 3, "Pós-Produção")
            ]
            self.cursor.executemany("INSERT INTO catalogo_servicos (nome, horas_padrao, categoria) VALUES (?, ?, ?)", tarefas_iniciais)
            self.conn.commit()
            print("Catálogo de serviços inicial criado.")

        # Seed Custos Operacionais
        self.cursor.execute("SELECT count(*) FROM custos_operacionais")
        if self.cursor.fetchone()[0] == 0:
            custos_iniciais = [
                ("Água", 35.0), ("Luz", 500.0), ("Telefone", 300.0), ("Internet", 50.0),
                ("IPTU", 200.0), ("Condomínio", 100.0), ("Aluguel", 100.0), ("Faxina", 100.0),
                ("Gás", 100.0), ("Alvará", 100.0), ("Material de limpeza", 100.0),
                ("Papelaria/Escritório", 100.0), ("Software", 100.0), ("Pro labore", 3000.0),
                ("Estagiário", 100.0), ("Associações", 100.0), ("Contabilidade", 100.0),
                ("Marketing", 100.0), ("Conselho Profissional", 100.0), ("Cursos", 100.0),
                ("Terceirizados", 10.0)
            ]
            self.cursor.executemany("INSERT INTO custos_operacionais (descricao, valor) VALUES (?, ?)", custos_iniciais)
            self.conn.commit()
            print("Custos operacionais iniciais criados.")

    # Métodos de Configuração
    def get_config(self):
        self.cursor.execute("SELECT * FROM configuracoes ORDER BY id DESC LIMIT 1")
        return self.cursor.fetchone()

    def update_config(self, custo, horas, imposto, lucro, meta, nome):
        # Verifica se já existe config
        if self.get_config():
            self.cursor.execute("""
                UPDATE configuracoes SET custo_mensal=?, horas_mensais=?, imposto_padrao=?, lucro_padrao=?, meta_mensal=?, nome_usuario=?
                WHERE id = (SELECT MAX(id) FROM configuracoes)
            """, (custo, horas, imposto, lucro, meta, nome))
        else:
             self.cursor.execute("""
                INSERT INTO configuracoes (custo_mensal, horas_mensais, imposto_padrao, lucro_padrao, meta_mensal, nome_usuario)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (custo, horas, imposto, lucro, meta, nome))
        self.conn.commit()

    # Métodos do Catálogo
    def get_servicos(self):
        self.cursor.execute("SELECT id, nome, horas_padrao, categoria FROM catalogo_servicos ORDER BY categoria, nome")
        return self.cursor.fetchall()

    def get_categorias(self):
        self.cursor.execute("SELECT DISTINCT categoria FROM catalogo_servicos ORDER BY categoria")
        return [row[0] for row in self.cursor.fetchall()]

    def add_servico(self, nome, horas, categoria="Geral"):
        self.cursor.execute("INSERT INTO catalogo_servicos (nome, horas_padrao, categoria) VALUES (?, ?, ?)", (nome, horas, categoria))
        self.conn.commit()

    def delete_servico(self, id_servico):
        self.cursor.execute("DELETE FROM catalogo_servicos WHERE id=?", (id_servico,))
        self.conn.commit()

    # Métodos de Custos Operacionais
    def get_custos_operacionais(self):
        self.cursor.execute("SELECT id, descricao, valor FROM custos_operacionais ORDER BY descricao")
        return self.cursor.fetchall()

    def add_custo_operacional(self, descricao, valor):
        self.cursor.execute("INSERT INTO custos_operacionais (descricao, valor) VALUES (?, ?)", (descricao, valor))
        self.conn.commit()

    def delete_custo_operacional(self, id_custo):
        self.cursor.execute("DELETE FROM custos_operacionais WHERE id=?", (id_custo,))
        self.conn.commit()

    def get_total_custos_operacionais(self):
        self.cursor.execute("SELECT SUM(valor) FROM custos_operacionais")
        result = self.cursor.fetchone()[0]
        return result if result else 0.0

    def get_dashboard_metrics(self, filtro_mes=None, filtro_ano=None, filtro_dia=None):
        query = "SELECT COUNT(*), SUM(preco_final) FROM projetos"
        params = []

        where_clauses = []
        if filtro_mes and filtro_mes != "Todos":
             where_clauses.append("strftime('%m', data_criacao) = ?")
             params.append(filtro_mes)

        if filtro_ano and filtro_ano != "Todos":
             where_clauses.append("strftime('%Y', data_criacao) = ?")
             params.append(filtro_ano)

        if filtro_dia:
             where_clauses.append("strftime('%d', data_criacao) = ?")
             params.append(filtro_dia)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        self.cursor.execute(query, params)
        data = self.cursor.fetchone()

        total_projetos = data[0] if data[0] else 0
        total_orcado = data[1] if data[1] else 0.0

        ticket_medio = total_orcado / total_projetos if total_projetos > 0 else 0.0

        # Get Status Distribution for Pie Chart
        query_status = "SELECT status, COUNT(*) FROM projetos"
        if where_clauses:
            query_status += " WHERE " + " AND ".join(where_clauses)
        query_status += " GROUP BY status"

        self.cursor.execute(query_status, params)
        status_dist = self.cursor.fetchall()

        return {
            "total_projetos": total_projetos,
            "total_orcado": total_orcado,
            "ticket_medio": ticket_medio,
            "status_dist": status_dist
        }

    def get_revenue_trend(self, months=6):
        today = datetime.datetime.now()
        labels = []
        values = []

        # Helper to subtract months
        def subtract_months(dt, n):
            total_months = dt.year * 12 + dt.month - 1 - n
            year = total_months // 12
            month = total_months % 12 + 1
            return datetime.date(year, month, 1)

        for i in range(months - 1, -1, -1):
            d = subtract_months(today, i)
            month_str = d.strftime("%Y-%m")
            label_str = d.strftime("%b/%y") # Ex: Out/23

            self.cursor.execute("SELECT SUM(preco_final) FROM projetos WHERE strftime('%Y-%m', data_criacao) = ?", (month_str,))
            res = self.cursor.fetchone()
            val = res[0] if res and res[0] else 0.0

            labels.append(label_str)
            values.append(val)

        return labels, values

    def get_revenue_by_category(self, filtro_mes=None, filtro_ano=None, filtro_dia=None):
        query = "SELECT categoria, SUM(preco_final) FROM projetos"
        params = []
        where_clauses = []

        if filtro_mes and filtro_mes != "Todos":
             where_clauses.append("strftime('%m', data_criacao) = ?")
             params.append(filtro_mes)

        if filtro_ano and filtro_ano != "Todos":
             where_clauses.append("strftime('%Y', data_criacao) = ?")
             params.append(filtro_ano)

        if filtro_dia:
             where_clauses.append("strftime('%d', data_criacao) = ?")
             params.append(filtro_dia)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        query += " GROUP BY categoria"

        self.cursor.execute(query, params)
        return self.cursor.fetchall() # [(Cat, Val), ...]

    def get_conversion_rate(self, filtro_mes=None, filtro_ano=None, filtro_dia=None):
        # Total Budgets = Count All
        # Converted = Status != 'Orçamento' (assuming 'Orçamento' is the initial state)
        # OR Status in ('Aprovado', 'Em Execução', 'Concluído')

        base_query = "SELECT COUNT(*) FROM projetos"
        params = []
        where_clauses = []

        if filtro_mes and filtro_mes != "Todos":
             where_clauses.append("strftime('%m', data_criacao) = ?")
             params.append(filtro_mes)

        if filtro_ano and filtro_ano != "Todos":
             where_clauses.append("strftime('%Y', data_criacao) = ?")
             params.append(filtro_ano)

        if filtro_dia:
             where_clauses.append("strftime('%d', data_criacao) = ?")
             params.append(filtro_dia)

        where_str = ""
        if where_clauses:
            where_str = " WHERE " + " AND ".join(where_clauses)

        # Total
        self.cursor.execute(base_query + where_str, params)
        total = self.cursor.fetchone()[0]
        if not total: total = 0

        # Converted
        converted_clauses = list(where_clauses)
        converted_clauses.append("status != 'Orçamento'")
        where_converted = " WHERE " + " AND ".join(converted_clauses)

        self.cursor.execute(base_query + where_converted, params)
        converted = self.cursor.fetchone()[0]
        if not converted: converted = 0

        return total, converted

    def get_stalled_projects(self, days=10):
        # Projects not updated in X days and NOT 'Concluído'
        # We need to be careful with date parsing.
        # Ideally we assume data_atualizacao is sortable string YYYY-MM-DD...

        limit_date = datetime.datetime.now() - datetime.timedelta(days=days)
        # Convert to string format used in DB. Since we might have YYYY-MM-DD or YYYY-MM-DD HH:MM:SS
        # If we use string comparison, "2023-10-01" < "2023-10-10".
        # We need to handle that data_atualizacao might vary.
        # But let's assume standard ISO format YYYY-MM-DD...

        limit_str = limit_date.strftime("%Y-%m-%d %H:%M:%S")

        # We want data_atualizacao < limit_str
        # AND status != 'Concluído'

        # Note: If data_atualizacao is YYYY-MM-DD (length 10), and limit_str is length 19, string compare still works often
        # but "2023-10-20" < "2023-10-20 12:00:00" is true.

        query = """
            SELECT id, cliente, status, data_atualizacao
            FROM projetos
            WHERE status != 'Concluído'
            AND (data_atualizacao < ? OR data_atualizacao IS NULL)
        """

        self.cursor.execute(query, (limit_str,))
        return self.cursor.fetchall()

    def get_hourly_efficiency(self, filtro_mes=None, filtro_ano=None, filtro_dia=None):
        # 1. Calculate Real Sold Hour Value
        # Avoid JOIN duplication by querying separately

        # Total Revenue
        query_rev = "SELECT SUM(preco_final) FROM projetos"
        params = []
        where_clauses = []

        if filtro_mes and filtro_mes != "Todos":
             where_clauses.append("strftime('%m', data_criacao) = ?")
             params.append(filtro_mes)

        if filtro_ano and filtro_ano != "Todos":
             where_clauses.append("strftime('%Y', data_criacao) = ?")
             params.append(filtro_ano)

        if filtro_dia:
             where_clauses.append("strftime('%d', data_criacao) = ?")
             params.append(filtro_dia)

        if where_clauses:
            query_rev += " WHERE " + " AND ".join(where_clauses)

        self.cursor.execute(query_rev, params)
        res_rev = self.cursor.fetchone()
        total_rev = res_rev[0] if res_rev and res_rev[0] else 0.0

        # Total Hours
        # We need to filter tasks by the creation date of their PROJECT.
        query_hours = """
            SELECT SUM(t.horas_estimadas)
            FROM tarefas_projeto t
            JOIN projetos p ON t.projeto_id = p.id
        """
        # Re-use where clauses but with 'p.' prefix if needed, but since we didn't use alias in where_clauses above,
        # we need to be careful. 'data_criacao' exists in projects.
        # Let's rebuild params/clauses with alias 'p'

        params_h = []
        where_h = []
        if filtro_mes and filtro_mes != "Todos":
             where_h.append("strftime('%m', p.data_criacao) = ?")
             params_h.append(filtro_mes)

        if filtro_ano and filtro_ano != "Todos":
             where_h.append("strftime('%Y', p.data_criacao) = ?")
             params_h.append(filtro_ano)

        if filtro_dia:
             where_h.append("strftime('%d', p.data_criacao) = ?")
             params_h.append(filtro_dia)

        if where_h:
            query_hours += " WHERE " + " AND ".join(where_h)

        self.cursor.execute(query_hours, params_h)
        res_hours = self.cursor.fetchone()
        total_hours = res_hours[0] if res_hours and res_hours[0] else 0.0

        real_hourly_rate = total_rev / total_hours if total_hours > 0 else 0.0

        # 2. Get Technical Cost (Calculated from Config)
        # We need logic to calc technical cost. Logic class has it.
        # But we are in Database class.
        # Let's reproduce the simple calculation: Custo Mensal / Horas Mensais

        cfg = self.get_config()
        # cfg: id, custo, horas, imposto, lucro, meta, nome
        custo_mensal = cfg[1]
        horas_mensais = cfg[2]

        # Or better, use total operational costs from table
        custo_operacional_total = self.get_total_custos_operacionais()

        # If cfg[1] (custo_mensal) is supposed to be the sum, we can use it, but logic.py uses get_total_custos_operacionais()

        tech_hourly_cost = custo_operacional_total / horas_mensais if horas_mensais > 0 else 0.0

        return real_hourly_rate, tech_hourly_cost
