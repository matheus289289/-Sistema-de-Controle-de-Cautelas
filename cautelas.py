import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import csv
from tkinter import filedialog
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import barcode
from barcode.writer import ImageWriter
import uuid
import os
import sys
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#Banco de Dados
def conectar():
    return sqlite3.connect('banco_de_dados.db', timeout=10)


def inicializar_banco():
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS produtos
                          (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            patrimonio TEXT UNIQUE,
                            nome TEXT,
                            setor TEXT,
                            responsavel TEXT,
                            status TEXT DEFAULT 'Disponivel'
                       )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS historico
                          (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            patrimonio TEXT,
                            nome_equipamento TEXT,
                            posto TEXT,
                            nip TEXT,
                            responsavel TEXT,
                            data_saida TEXT,
                            data_devolucao TEXT
                          )''')
        try:
            cursor.execute("ALTER TABLE produtos ADD COLUMN codigo_cautela TEXT")
        except sqlite3.OperationalError:
            pass
        conn.commit()
id_item_selecionado = None

#-- FUNÇÕES DE LÓGICA--#

def exibir_inventario():
    for row in tabela.get_children():
        tabela.delete(row)
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, status, patrimonio, nome, setor, responsavel, codigo_cautela FROM produtos")
        for row in cursor.fetchall():
            tabela.insert("", tk.END, values=row)
    atualizar_pizza()

def abrir_cadastro():
    janela_cad = tk.Toplevel(janela)
    janela_cad.title("Cadastrar Equipamento")
    janela_cad.geometry("400x300")
    janela_cad.resizable(False, False)

    tk.Label(janela_cad, text="Cadastrar Equipamento", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(janela_cad, text="Nº Patrimonial:").pack()
    entry_pat = tk.Entry(janela_cad, width=35)
    entry_pat.pack(pady=2)

    tk.Label(janela_cad, text="Nome e Modelo:").pack()
    entry_nome = tk.Entry(janela_cad, width=35)
    entry_nome.pack(pady=2)

    tk.Label(janela_cad, text="Setor:").pack()
    entry_setor = tk.Entry(janela_cad, width=35)
    entry_setor.pack(pady=2)

    def salvar_produto():
        pat = entry_pat.get().strip()
        nome = entry_nome.get().strip()
        setor = entry_setor.get().strip()
        if not pat or not nome:
            messagebox.showwarning("Atenção!", "Patrimônio e Nome são obrigatórios.")
            return
        try:
            with conectar() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO produtos (patrimonio, nome, setor) VALUES (?, ?, ?)", (pat, nome, setor))
                conn.commit()
            exibir_inventario()
            janela_cad.destroy()
            messagebox.showinfo("Sucesso", "Produto salvo!")
        except sqlite3.IntegrityError:
            messagebox.showerror("Erro!", "Patrimônio já cadastrado.")

    tk.Button(janela_cad, text="Salvar", command=salvar_produto,
              width=15, fg="white", bg="green").pack(pady=15)


def editar_produto():
    global id_item_selecionado
    if not id_item_selecionado:
        messagebox.showwarning("Atenção", "Selecione um item para editar.")
        return

    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT patrimonio, nome, setor FROM produtos WHERE id=?", (id_item_selecionado,))
        dados = cursor.fetchone()

    janela_edit = tk.Toplevel(janela)
    janela_edit.title("Editar Equipamento")
    janela_edit.geometry("400x300")
    janela_edit.resizable(False, False)

    tk.Label(janela_edit, text="Editar Equipamento", font=("Arial", 12, "bold")).pack(pady=10)

    tk.Label(janela_edit, text="Nº Patrimonial:").pack()
    entry_pat = tk.Entry(janela_edit, width=35)
    entry_pat.insert(0, dados[0])
    entry_pat.pack(pady=2)

    tk.Label(janela_edit, text="Nome e Modelo:").pack()
    entry_nome = tk.Entry(janela_edit, width=35)
    entry_nome.insert(0, dados[1])
    entry_nome.pack(pady=2)

    tk.Label(janela_edit, text="Setor:").pack()
    entry_setor = tk.Entry(janela_edit, width=35)
    entry_setor.insert(0, dados[2])
    entry_setor.pack(pady=2)

    def confirmar_edicao():
        pat = entry_pat.get().strip()
        nome = entry_nome.get().strip()
        setor = entry_setor.get().strip()
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE produtos SET patrimonio=?, nome=?, setor=? WHERE id=?",
                           (pat, nome, setor, id_item_selecionado))
            conn.commit()
        exibir_inventario()
        janela_edit.destroy()
        messagebox.showinfo("Sucesso!", "Produto Atualizado!")

    tk.Button(janela_edit, text="Salvar Edição", command=confirmar_edicao,
              width=15, fg="white", bg="orange").pack(pady=15)


def excluir_produto():
    global id_item_selecionado
    if not id_item_selecionado:
        messagebox.showwarning("Atenção", "Selecione um item para excluir.")
        return
    if messagebox.askyesno("Confirmar", "Deseja excluir este item?"):
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM produtos WHERE id=?", (id_item_selecionado,))
            conn.commit()
        id_item_selecionado = None
        exibir_inventario()


def preencher_campos(event):
    global id_item_selecionado
    selecionado = tabela.focus()
    if not selecionado:
        return
    valores = tabela.item(selecionado, "values")
    id_item_selecionado = valores[0]



def filtrar_tabela(event):
    termo = entry_busca.get().strip()
    filtrar_tabela_por_termo(termo)

def filtrar_tabela_por_termo(termo):
    for row in tabela.get_children():
        tabela.delete(row)
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, status, patrimonio, nome, setor, responsavel, codigo_cautela FROM produtos WHERE nome LIKE ? OR patrimonio LIKE ?",
                       (f"%{termo}%", f"%{termo}%"))
        for row in cursor.fetchall():
            tabela.insert("", tk.END, values=row)


def exportar_csv():
    caminho = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
    if not caminho:
        return
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, status, patrimonio, nome, setor, responsavel, codigo_cautela FROM produtos")
        rows = cursor.fetchall()
    with open (caminho, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Status", "Patrimônio", "Nome", "Setor", "Responsável", "Código de Barras"])
        writer.writerows(rows)
    messagebox.showinfo("Sucesso", "CSV Exportado!")

def importar_csv():
    caminho = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    if not caminho:
        return
    with open(caminho, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        with conectar() as conn:
            cursor = conn.cursor()
            for row in reader:
                try:
                    cursor.execute("INSERT INTO produtos (patrimonio, nome, setor) VALUES (?, ?, ?)",
                                   (row["Patrimônio"], row["Nome"], row["Setor"]))
                except sqlite3.IntegrityError:
                    pass
            conn.commit()
    exibir_inventario()
    messagebox.showinfo("Sucesso!", "CSV Importado!")

def ler_cdbarra():
   janela_dev = tk.Toplevel(janela)
   janela_dev.title("Devoluçao de Material")
   janela_dev.geometry("350x200")
   janela_dev.resizable(False, False)

   tk.Label(janela_dev, text="Devolução de Material", font=("Arial", 11, "bold")).pack(pady=10)
   tk.Label(janela_dev, text="Leia ou digite o código de barras:").pack()

   entry_codigo = tk.Entry(janela_dev, width=35, font=("Arial", 12))
   entry_codigo.pack(pady=5)
   entry_codigo.focus()
   def confirmar_devolucao():
       from datetime import datetime
       data_dev = datetime.now().strftime("%d/%m/%Y %H:%M")
       codigo = entry_codigo.get().strip()
       if not codigo:
           messagebox.showwarning("Atenção!", "Leia ou digite o código.")
           return
       with conectar() as conn:
           cursor = conn.cursor()
           cursor.execute("SELECT id, nome, patrimonio FROM produtos WHERE codigo_cautela=? AND status='Indisponivel'",
               (codigo,))
           resultados = cursor.fetchall()
       if not resultados:
           messagebox.showerror("Erro!!", "Código não encontrado ou equipamento ja devolvido.")
           return
       with conectar() as conn:
           cursor = conn.cursor()
           for resultado in resultados:
               cursor.execute("UPDATE produtos SET status='Disponivel', responsavel=NULL, codigo_cautela=NULL WHERE id=?",
                           (resultado[0],))
               cursor.execute("UPDATE historico SET data_devolucao=? WHERE patrimonio=? AND data_devolucao IS NULL",
                           (data_dev, resultado[2]))
           conn.commit()

       nomes = ", ".join([r[1] for r in resultados])
       exibir_inventario()
       janela_dev.destroy()
       messagebox.showinfo("Sucesso", f"{len(resultados)} equipamento(s) devolvido(s):\n{nomes}")

   tk.Button(janela_dev, text="Confirmar Devolução", command=confirmar_devolucao, width=20, fg="white", bg="purple").pack(pady=15)

   entry_codigo.bind("<Return>", lambda e: confirmar_devolucao())
    
        



def abrir_cautela():
    from datetime import datetime
    data_saida = datetime.now().strftime("%d/%m/%Y %H:%M")

    janela_cautela = tk.Toplevel(janela)
    janela_cautela.title("Criar Cautela")
    janela_cautela.geometry("620x620")
    janela_cautela.resizable(False, False)

    tk.Label(janela_cautela, text="Criar Cautela", font=("Arial", 12, "bold")).pack(pady=8)

    # ── Dados do responsável ──
    frame_resp = tk.Frame(janela_cautela)
    frame_resp.pack(pady=5)

    tk.Label(frame_resp, text="Posto/Graduação:").grid(row=0, column=0, padx=5, sticky="e")
    entry_posto = tk.Entry(frame_resp, width=30)
    entry_posto.grid(row=0, column=1, pady=2)

    tk.Label(frame_resp, text="NIP:").grid(row=1, column=0, padx=5, sticky="e")
    entry_nip = tk.Entry(frame_resp, width=30)
    entry_nip.grid(row=1, column=1, pady=2)

    tk.Label(frame_resp, text="Nome Completo:").grid(row=2, column=0, padx=5, sticky="e")
    entry_responsavel = tk.Entry(frame_resp, width=30)
    entry_responsavel.grid(row=2, column=1, pady=2)

    tk.Label(janela_cautela, text=f"Data de Saída: {data_saida}", fg="grey").pack()

    # ── Tabela de disponíveis ──
    tk.Label(janela_cautela, text="Equipamentos Disponíveis:", font=("Arial", 9, "bold")).pack(anchor="w", padx=15)

    colunas_disp = ("ID", "Patrimônio", "Equipamento", "Setor")
    tabela_disp = ttk.Treeview(janela_cautela, columns=colunas_disp, show="headings", height=6)
    for col in colunas_disp:
        tabela_disp.heading(col, text=col)
        tabela_disp.column(col, width=130, anchor="center")
    tabela_disp.pack(pady=3, padx=15, fill=tk.X)

    # Popula disponíveis
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, patrimonio, nome, setor FROM produtos WHERE status='Disponivel'")
        for row in cursor.fetchall():
            tabela_disp.insert("", tk.END, values=row)

    # ── Botão adicionar ──
    equipamentos_selecionados = []

    def adicionar():
        sel = tabela_disp.focus()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um equipamento.")
            return
        vals = tabela_disp.item(sel, "values")
        for e in equipamentos_selecionados:
            if e["id"] == str(vals[0]):
                messagebox.showwarning("Atenção", "Equipamento já adicionado!")
                return
        equipamentos_selecionados.append({
            "id": str(vals[0]),
            "patrimonio": vals[1],
            "nome": vals[2],
            "setor": vals[3]
        })
        tabela_cautela.insert("", tk.END, values=vals)
        tabela_disp.delete(sel)  # remove dos disponíveis

    tk.Button(janela_cautela, text="Adicionar ↓", command=adicionar,
              width=15, bg="steelblue", fg="white").pack(pady=3)

    # ── Tabela da cautela ──
    tk.Label(janela_cautela, text="Itens da Cautela:", font=("Arial", 9, "bold")).pack(anchor="w", padx=15)

    colunas_caut = ("ID", "Patrimônio", "Equipamento", "Setor")
    tabela_cautela = ttk.Treeview(janela_cautela, columns=colunas_caut, show="headings", height=5)
    for col in colunas_caut:
        tabela_cautela.heading(col, text=col)
        tabela_cautela.column(col, width=130, anchor="center")
    tabela_cautela.pack(pady=3, padx=15, fill=tk.X)

    def remover():
        sel = tabela_cautela.focus()
        if not sel:
            return
        vals = tabela_cautela.item(sel, "values")
        equipamentos_selecionados[:] = [e for e in equipamentos_selecionados if e["id"] != str(vals[0])]
        tabela_cautela.delete(sel)
        tabela_disp.insert("", tk.END, values=vals)  # devolve aos disponíveis

    tk.Button(janela_cautela, text="Remover ↑", command=remover,
              width=15, fg="red").pack(pady=3)

    # ── Gerar ──
    def confirmar_cautela():
        posto = entry_posto.get().strip()
        nip = entry_nip.get().strip()
        responsavel = entry_responsavel.get().strip()

        if not posto or not nip or not responsavel:
            messagebox.showwarning("Atenção!", "Preencha todos os dados do responsável.")
            return
        if not equipamentos_selecionados:
            messagebox.showwarning("Atenção!", "Adicione ao menos um equipamento.")
            return

        codigo = str(uuid.uuid4().int)[:12]
        os.makedirs("codigos", exist_ok=True)
        caminho_barras = f"codigos/{codigo}"
        ean = barcode.get('code128', codigo, writer=ImageWriter())
        ean.save(caminho_barras)

        with conectar() as conn:
            cursor = conn.cursor()
            for equip in equipamentos_selecionados:
                cursor.execute("UPDATE produtos SET status='Indisponivel', responsavel=?, codigo_cautela=? WHERE id=?",
                               (f"{posto} - {responsavel}", codigo, equip["id"]))
                cursor.execute("INSERT INTO historico (patrimonio, nome_equipamento, posto, nip, responsavel, data_saida) VALUES (?, ?, ?, ?, ?, ?)",
                               (equip["patrimonio"], equip["nome"], posto, nip, responsavel, data_saida))
            conn.commit()

        gerar_pdf(equipamentos_selecionados, posto, nip, responsavel, data_saida, codigo, f"{caminho_barras}.png")
        exibir_inventario()
        janela_cautela.destroy()
        messagebox.showinfo("Sucesso", f"Cautela gerada com {len(equipamentos_selecionados)} equipamento(s)!")

    tk.Button(janela_cautela, text="Gerar Cautela", command=confirmar_cautela,
              width=15, fg="white", bg="navy").pack(pady=10)



def gerar_pdf(lista_produtos, posto, nip, responsavel, data_saida, codigo, caminho_barras):
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    import os

    os.makedirs("cautelas", exist_ok=True)
    caminho_pdf = f"cautelas/cautela_{codigo}.pdf"
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    largura, altura = A4

    # Ajuste de margem vertical para que o corpo não fique em cima dos títulos
    y = altura - 7.5 * cm
    y_box = altura - 15.0 * cm

    # =========================================================================
    # # cabeçalho (Fundo limpo e textos em preto - Padrão Oficial da Foto)
    # =========================================================================
    c.setFillColor(colors.black) # Força a cor para preto logo no início do documento
    
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(largura / 2, altura - 2.5 * cm, "MARINHA DO BRASIL")
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(largura / 2, altura - 3.1 * cm, "CENTRO DE EDUCAÇÃO FÍSICA ALMIRANTE ADALBERTO NUNES")
    
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(largura / 2, altura - 4.4 * cm, "STI")
    
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(largura / 2, altura - 5.4 * cm, "TERMO DE RECEBIMENTO DE MATERIAL EM CAUTELA")

    # =========================================================================
    # # corpo
    # =========================================================================
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, y - 1.0*cm, "DADOS DO RESPONSÁVEL")
    
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, y - 1.8*cm, f"Posto/Graduação: {posto}")
    c.drawString(2*cm, y - 2.6*cm, f"NIP: {nip}")
    c.drawString(2*cm, y - 3.4*cm, f"Nome: {responsavel}")
    c.drawString(2*cm, y - 4.2*cm, f"Data de Saída: {data_saida}")

    # ── Tabela de equipamentos ──
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y - 5.6*cm, "EQUIPAMENTOS CAUTELADOS:")

    c.setFont("Helvetica-Bold", 9)
    c.drawString(2*cm,   y - 6.4*cm, "Patrimônio")
    c.drawString(6*cm,   y - 6.4*cm, "Equipamento")
    c.drawString(14*cm,  y - 6.4*cm, "Setor")
    c.line(2*cm, y - 6.6*cm, 19*cm, y - 6.6*cm)

    c.setFont("Helvetica", 9)
    linha_y = y - 7.2*cm
    for equip in lista_produtos:
        c.drawString(2*cm,  linha_y, str(equip["patrimonio"]))
        c.drawString(6*cm,  linha_y, str(equip["nome"]))
        c.drawString(14*cm, linha_y, str(equip["setor"]))
        linha_y -= 0.6*cm

    # ── Assinatura ──
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, y - 9.0*cm, "Eu, declaro que recebi o material abaixo discriminado do STI desta OM.")
    c.setFont("Helvetica", 10)
    c.drawString(2*cm, y_box - 2.0*cm, "Rio de janeiro, RJ, ___ de _________ de 20__. ")
    c.drawString(2*cm, y_box - 3.5*cm, "ASSINATURA DO RECEBEDOR: _______________________________________ ")

    # ── Etiqueta ──
    c.setDash(4, 4)
    c.line(0, 120, largura, 120)
    c.setDash()
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(largura / 2, 108, "✂ Destacar e colar no equipamento")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2*cm, 95, f"Cautela: {codigo}")
    c.drawString(2*cm, 80, f"{posto} - {responsavel}")
    c.drawImage(caminho_barras, 2*cm, 20, width=8*cm, height=1.5*cm)

    c.save()
    os.startfile(os.path.abspath(caminho_pdf))

def abrir_historico():
    janela_hist = tk.Toplevel(janela)
    janela_hist.title("Histórico de Cautelas")
    janela_hist.geometry("900x400")

    tk.Label(janela_hist, text="Histórico de Cautelas", font=("Arial", 12, "bold")).pack(pady=10)
    
    #-----barra de busca----
    frame_busca_hist = tk.Frame(janela_hist)
    frame_busca_hist.pack(pady=5)

    tk.Label(frame_busca_hist, text="🔍 Pesquisar: 🔍", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
    entry_busca_hist = tk.Entry(frame_busca_hist, width=35)
    entry_busca_hist.pack(side=tk.LEFT)

    #---botões exportar e importar ----

    frame_btns_hist = tk.Frame(janela_hist)
    frame_btns_hist.pack(pady=5)

    #----Tabela ----
    colunas_hist = ("ID", "Patrimônio", "Equipamento", "Posto", "NIP", "Responsável", "Saída", "Devolução")
    tabela_hist = ttk.Treeview(janela_hist, columns=colunas_hist, show="headings", height=15)

    for col in colunas_hist:
        tabela_hist.heading(col, text=col)
        tabela_hist.column(col, width=100, anchor="center")

    tabela_hist.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

    #-- funcoes internas 
    def carregar_historico(termo=""):
        for row in tabela_hist.get_children():
            tabela_hist.delete(row)
        with conectar() as conn:
            cursor = conn.cursor()
            if termo:
                like = f"%{termo}%"
                cursor.execute("""SELECT * FROM historico
                                  WHERE patrimonio LIKE ? OR nome_equipamento LIKE ?
                                  OR posto LIKE ? OR nip LIKE ? OR responsavel LIKE ?
                                  ORDER BY id DESC""",
                                  (like, like, like, like, like,))
            else:
                cursor.execute("SELECT * FROM historico ORDER BY id DESC")
            for row in cursor.fetchall():
                tabela_hist.insert("", tk.END, values=row)

    def exportar_historico():
        caminho = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not caminho:
            return
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM historico ORDER BY id DESC")
            rows = cursor.fetchall()
        with open(caminho, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Patrimônio", "Equipamento", "Posto", "NIP", "Responsável", "Saída", "Devolução"])
            writer.writerows(rows)
        messagebox.showinfo("Sucesso!!", "Histórico Exportado!")

    def importar_historico():
        caminho = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not caminho:
            return
        with open(caminho, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            with conectar() as conn:
                cursor = conn.cursor()
                for row in reader:
                    try:
                        cursor.execute("""INSERT INTO historico 
                                          (patrimonio, nome_equipamento, posto, nip, responsavel, data_saida, data_devolucao)
                                          VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                       (row["Patrimônio"], row["Equipamento"], row["Posto"],
                                        row["NIP"], row["Responsável"], row["Saída"], row["Devolução"]))
                    except Exception:
                        pass
                conn.commit()
        carregar_historico()
        messagebox.showinfo("Sucesso!", "Histórico importado!")

        #----busca de botões 
    entry_busca_hist.bind("<KeyRelease>", lambda e: carregar_historico(entry_busca_hist.get().strip()))
    tk.Button(frame_btns_hist, text="Exportar CSV", command=exportar_historico, width=14).pack(side=tk.LEFT, padx=5)
    tk.Button(frame_btns_hist, text="Importar CSV", command=importar_historico, width=14).pack(side=tk.LEFT, padx=5)

    carregar_historico()

def atualizar_pizza():
    ax_pizza.clear()
    with conectar() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT status, COUNT(*) FROM produtos GROUP BY status")
        dados = cursor.fetchall()
    if dados:
        labels = [r[0] for r in dados]
        valores = [r[1] for r in dados]
        cores = ["green" if s == "Disponivel" else "red" for s in labels]

        def formatar(pct, allvals):
            absoluto = round(pct / 100 * sum(allvals))
            return f"{absoluto}\n({pct:.0f}%)"
        
        ax_pizza.pie(valores, labels=labels, colors=cores, autopct=lambda pct: formatar(pct, valores), startangle=90)
        ax_pizza.set_title("Status dos Equipamentos")
    canvas_pizza.draw()







#INTERFACE#

janela = tk.Tk()
janela.title("Controle de Cautelas")
janela.geometry("700x850")
janela.resizable(True, True)

#botões#

frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=10)

#Primeira linha de botões (row=0)
tk.Button(frame_botoes, text="Cadastrar", command=abrir_cadastro, width=12, fg="green").grid(row=0, column=0, padx=5, pady=5)
tk.Button(frame_botoes, text="Editar", command=editar_produto, width=12, fg="green").grid(row=0, column=1, padx=5, pady=5)
tk.Button(frame_botoes, text="Limpar Busca", command=lambda: [entry_busca.delete(0, tk.END), filtrar_tabela_por_termo("")], width=12).grid(row=0, column=2, padx=5, pady=5)

#Segunda linha de botões (row=1)

tk.Button(frame_botoes, text="Excluir", command=excluir_produto, width=12).grid(row=1, column=0, padx=5, pady=5)
tk.Button(frame_botoes, text="Exportar CSV", command=exportar_csv, width=12).grid(row=1, column=1, padx=5, pady=5)
tk.Button(frame_botoes, text="Importar CSV", command=importar_csv, width=12).grid(row=1, column=2, padx=5, pady=5)

#Terceira linha de botões (row=2)

tk.Button(frame_botoes, text="Devolver", command=ler_cdbarra, width=12, fg="purple").grid(row=2, column=1, padx=5, pady=5)
tk.Button(frame_botoes, text="Criar Cautela", command=abrir_cautela, width=12, fg="blue").grid(row=2, column=0, padx=5, pady=5)
tk.Button(frame_botoes, text="Histórico", command=abrir_historico, width=12, fg="brown").grid(row=2, column=2, padx=5, pady=5)


#Barra de pesquisa#

frame_busca = tk.Frame(janela)
frame_busca.pack(pady=5)

tk.Label(frame_busca, text="🔍Pesquisar🔍", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5)
entry_busca = tk.Entry(frame_busca, width=30)
entry_busca.pack(side=tk.LEFT)
entry_busca.bind("<KeyRelease>", filtrar_tabela)

# Tabela

colunas = ("ID","Status", "Nº Patrimonial", "Nome e Modelo", "Setor","Responsável", "Código de Barras")
tabela = ttk.Treeview(janela, columns=colunas, show="headings", height=5)

for col in colunas:
    tabela.heading(col, text=col)
    tabela.column(col,width=100, anchor="center")
tabela.pack(pady=5, padx=10, fill=tk.X)
tabela.bind("<<TreeviewSelect>>", preencher_campos)

# grafico de pizza embutido
frame_grafico = tk.Frame(janela)
frame_grafico.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

fig_pizza = Figure(figsize=(4, 4), tight_layout=True)
ax_pizza = fig_pizza.add_subplot(111)
canvas_pizza = FigureCanvasTkAgg(fig_pizza, master=frame_grafico)
canvas_pizza.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# Inicialização#
inicializar_banco()
exibir_inventario()
janela.mainloop()

