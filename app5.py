import requests
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
from threading import Thread
from datetime import datetime, timedelta


class CharacterSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Os Perecidos - Busca de Personagens e Last Login")
        self.root.geometry("700x650")

        self.style = self.get_style()
        self.root.configure(bg=self.style['bg_color'])

        self.cache = {}
        self.inatividade_dias = tk.IntVar(value=14)
        self.url_base = tk.StringVar(value="https://miracle74.com/?subtopic=characters")

        self.create_widgets()

        self.guild_names = []

    def get_style(self):
        return {
            'font': ('Segoe UI', 10),
            'title_font': ('Segoe UI', 12, 'bold'),
            'bg_color': '#f8f9fa',
            'frame_bg': '#ffffff',
            'button_bg': '#6c757d',
            'button_fg': 'white',
            'button_active': '#545b62',
            'clear_button_bg': '#d32f2f',
            'clear_button_fg': 'white',
            'clear_button_active': '#b22a2a',
            'save_button_bg': '#17a2b8',
            'save_button_fg': 'white',
            'save_button_active': '#138496',
            'text_bg': '#ffffff',
            'text_fg': '#495057',
            'status_bg': '#ced4da'
        }

    def create_widgets(self):
        main_frame = tk.Frame(self.root, padx=15, pady=15, bg=self.style['bg_color'])
        main_frame.pack(fill=tk.BOTH, expand=True)

        url_frame = tk.Frame(main_frame, bg=self.style['bg_color'])
        url_frame.pack(fill=tk.X)
        tk.Label(url_frame, text="URL da Página de Busca:", font=self.style['font'], bg=self.style['bg_color']).pack(side=tk.LEFT)
        self.url_entry = tk.Entry(url_frame, textvariable=self.url_base, width=70)
        self.url_entry.pack(side=tk.LEFT, padx=5, pady=5)

        input_frame = tk.Frame(main_frame, bg=self.style['frame_bg'], padx=10, pady=10)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(input_frame, text="Link da guild:",
                 font=self.style['title_font'], bg=self.style['frame_bg']).pack(anchor=tk.W)

        self.guild_url_var = tk.StringVar()
        self.guild_url_entry = tk.Entry(input_frame, textvariable=self.guild_url_var, width=80)
        self.guild_url_var.set("https://miracle74.com/?subtopic=guilds&action=show&guild=391")
        self.guild_url_entry.pack(fill=tk.X, pady=5)

        dias_frame = tk.Frame(main_frame, bg=self.style['bg_color'], pady=5)
        dias_frame.pack(fill=tk.X)
        tk.Label(dias_frame, text="Dias de inatividade:", font=self.style['font'], bg=self.style['bg_color']).pack(side=tk.LEFT)
        self.dias_entry = tk.Entry(dias_frame, textvariable=self.inatividade_dias, width=5)
        self.dias_entry.pack(side=tk.LEFT, padx=5)

        self.create_buttons(main_frame)
        self.create_results_area(main_frame)

    def create_buttons(self, parent):
        button_frame = tk.Frame(parent, bg=self.style['bg_color'])
        button_frame.pack(fill=tk.X, pady=(0, 10))

        self.search_button = tk.Button(
            button_frame, text="Buscar Informações", command=self.start_search_thread,
            bg=self.style['button_bg'], fg=self.style['button_fg'],
            activebackground=self.style['button_active'])
        self.search_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = tk.Button(
            button_frame, text="Limpar Campos", command=self.clear_fields,
            bg=self.style['clear_button_bg'], fg=self.style['clear_button_fg'],
            activebackground=self.style['clear_button_active'])
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(
            button_frame, text="Salvar Resultados", command=self.save_results,
            bg=self.style['save_button_bg'], fg=self.style['save_button_fg'],
            activebackground=self.style['save_button_active'])
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.list_names_button = tk.Button(
            button_frame, text="Listar Nomes da Guild", command=self.listar_nomes_guild,
            bg=self.style['save_button_bg'], fg=self.style['save_button_fg'],
            activebackground=self.style['save_button_active'])
        self.list_names_button.pack(side=tk.LEFT, padx=5)

        self.rankear_button = tk.Button(
            button_frame, text="Rankear Skills da Guild", command=self.rankear_guild_na_sword,
            bg=self.style['button_bg'], fg=self.style['button_fg'],
            activebackground=self.style['button_active'])
        self.rankear_button.pack(side=tk.LEFT, padx=5)        

    def create_results_area(self, parent):
        result_frame = tk.Frame(parent, bg=self.style['frame_bg'], padx=10, pady=10)
        result_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(result_frame, text="Resultados:",
                 font=self.style['title_font'], bg=self.style['frame_bg']).pack(anchor=tk.W)

        self.results_text = scrolledtext.ScrolledText(
            result_frame, height=15, wrap=tk.WORD,
            bg=self.style['text_bg'], fg=self.style['text_fg'],
            font=self.style['font'])
        self.results_text.pack(fill=tk.BOTH, expand=True)

        self.results_text.tag_config('title', foreground='blue', font=('Segoe UI', 10, 'bold'))
        self.results_text.tag_config('error', foreground='red')

        self.status_var = tk.StringVar(value="Pronto")
        status_bar = tk.Label(parent, textvariable=self.status_var, bd=1, relief=tk.SUNKEN,
                              anchor=tk.W, bg=self.style['status_bg'], font=self.style['font'])
        status_bar.pack(fill=tk.X)

    def start_search_thread(self):
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Buscando...")
        self.search_button.config(state=tk.DISABLED)

        guild_url = self.guild_url_var.get().strip()
        if not guild_url or "subtopic=guilds" not in guild_url:
            messagebox.showwarning("Aviso", "Por favor, insira um link válido da guild.")
            self.status_var.set("Pronto")
            self.search_button.config(state=tk.NORMAL)
            return

        dias = self.inatividade_dias.get()
        nomes = self.get_names_from_guild_url(guild_url)
        self.guild_names = nomes

        if not nomes:
            messagebox.showerror("Erro", "Não foi possível extrair nomes do link informado.")
            self.status_var.set("Erro ao buscar nomes da guild.")
            self.search_button.config(state=tk.NORMAL)
            return
        
        Thread(target=self.search_characters, args=(nomes, dias)).start()

    def get_names_from_guild_url(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resposta = requests.get(url, headers=headers)
            resposta.raise_for_status()

            soup = BeautifulSoup(resposta.content, "html.parser")
            guild_table = soup.find("table", class_="TableContent")
            nomes = []

            if guild_table:
                links = guild_table.find_all("a")
                for link in links:
                    href = link.get("href", "")
                    if "subtopic=characters" in href:
                        nomes.append(link.text.strip())

            return list(set(nomes))  # remove duplicados

        except Exception as e:
            print(f"Erro ao buscar nomes da guild: {e}")
            return []

    def search_characters(self, names, dias_inativo):
        resultados = {}
        url = self.url_base.get()

        for name in names:
            if name in self.cache:
                resultados[name] = self.cache[name]
            else:
                resultado = buscar_informacoes_personagem(name, url)
                resultados[name] = resultado
                self.cache[name] = resultado

        self.root.after(0, self.display_results, resultados, dias_inativo)
        self.root.after(0, lambda: self.status_var.set(f"Busca concluída - {len(resultados)} personagens"))
        self.root.after(0, lambda: self.search_button.config(state=tk.NORMAL))

# Adicione a função de busca na classificação de espada aqui
    def get_sword_highscore_names(self, page=1):
        # URL para a página de classificação da espada
        url = f"https://miracle74.com/?subtopic=highscores&list=sword&page={page}&vocation="
        response = requests.get(url)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Encontrando os nomes dos jogadores na classificação de espada
        nomes = []
        for row in soup.select('table#highscore_table tr'):
            name_cell = row.find('td', class_='Name')
            if name_cell:
                nomes.append(name_cell.get_text(strip=True))
        
        return nomes

    def rankear_guild_na_sword(self):
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Acessando a classificação das skills...")

        skills = ['experience','sword', 'axe', 'club', 'dist', 'maglevel', 'shielding', 'fishing', 'fist']
        self.guild_names = self.get_names_from_guild_url(self.guild_url_var.get().strip())

        if not self.guild_names:
            self.results_text.insert(tk.END, "Lista de nomes da guilda não foi carregada.\n", 'error')
            self.status_var.set("Erro: lista da guilda ausente.")
            return

        for skill in skills:
            nomes_skill = []

            for page in range(1, 11):
                url = f"https://miracle74.com/?subtopic=highscores&list={skill}&page={page}&vocation="
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    page_content = response.text

                    soup = BeautifulSoup(page_content, 'html.parser')

                    for tr in soup.find_all("tr", bgcolor=True):
                        tds = tr.find_all("td")
                        if len(tds) >= 6:
                            nome_tag = tds[2].find("a")
                            if nome_tag:
                                nome = nome_tag.text.strip()
                                skill_value = tds[4].text.strip() if skill == 'experience' else tds[5].text.strip()
                                nomes_skill.append({"nome": nome, "skill": skill_value})

                except requests.exceptions.RequestException as e:
                    self.results_text.insert(tk.END, f"Erro ao acessar a página {page} da skill {skill}: {e}\n", 'error')

            # Filtra os nomes da guilda
            nomes_em_comum = [entry for entry in nomes_skill if entry["nome"] in self.guild_names]

            if nomes_em_comum:
                self.results_text.insert(tk.END, f"\nOS PERECIDOS - TOP {skill.upper()}:\n", 'title')
                for idx, entry in enumerate(nomes_em_comum, start=1):
                    self.results_text.insert(tk.END, f"{idx} - {entry['nome']} - {entry['skill']}\n")
            else:
                self.results_text.insert(tk.END, f"\nNenhum membro da guilda está na classificação de {skill}.\n", 'warning')

        self.status_var.set("Ranking finalizado com sucesso.")


        
    def display_results(self, resultados, dias_inativo):
        self.results_text.delete(1.0, tk.END)
        contador_mostrados = 0

        for nome, info in resultados.items():
            if not info:
                continue  # Ignora personagens não encontrados

            last_login = info.get('Last Login', '')
            try:
                login_date = datetime.strptime(last_login, "%d %B %Y, %I:%M %p")
                limite = datetime.now() - timedelta(days=dias_inativo)

                if "[BANNED]" not in nome and login_date >= limite:
                    continue  # Ignora quem logou mais recentemente que o limite, exceto se estiver banido

            except Exception:
                pass  # Se o login não for legível, ainda mostra (pode ser útil)

            self.results_text.insert(tk.END, f"Informações de {nome}:\n", 'title')
            self.results_text.insert(tk.END, f"  Nome: {info.get('Name', 'Não disponível')}\n")
            self.results_text.insert(tk.END, f"  Vocação: {info.get('Vocation', 'Não disponível')}\n")
            self.results_text.insert(tk.END, f"  Level: {info.get('Level', 'Não disponível')}\n")
            self.results_text.insert(tk.END, f"  Último Login: {last_login}\n")
            self.results_text.insert(tk.END, "-" * 40 + "\n\n")
            contador_mostrados += 1

        if contador_mostrados == 0:
            self.results_text.insert(tk.END, "Nenhum personagem encontrado com inatividade igual ou superior ao valor informado.\n", 'error')

    def clear_fields(self):
        self.guild_url_var.set("")
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Campos limpos")

    def save_results(self):
        content = self.results_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Aviso", "Nenhum resultado para salvar.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")],
            title="Salvar resultados como")

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Relatório de Personagens - {datetime.now():%Y-%m-%d %H:%M:%S}\n\n")
                    f.write(content)
                self.status_var.set(f"Resultados salvos em {file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar o arquivo:\n{e}")
    def listar_nomes_guild(self):
        self.results_text.delete(1.0, tk.END)
        self.status_var.set("Listando nomes da guild...")

        guild_url = self.guild_url_var.get().strip()
        if not guild_url or "subtopic=guilds" not in guild_url:
            messagebox.showwarning("Aviso", "Por favor, insira um link válido da guild.")
            self.status_var.set("Pronto")
            return

        nomes = self.get_names_from_guild_url(guild_url)
        if not nomes:
            self.results_text.insert(tk.END, "Nenhum nome encontrado no link da guild.\n", 'error')
            self.status_var.set("Erro ao listar nomes.")
        else:
            self.results_text.insert(tk.END, "Nomes encontrados na guild:\n", 'title')
            for nome in sorted(nomes):
                self.results_text.insert(tk.END, f"• {nome}\n")
            self.status_var.set(f"{len(nomes)} nomes listados.")

def buscar_informacoes_personagem(nome_personagem, url):
    headers = {
        'User-Agent': 'Mozilla/5.0'
    }

    try:
        resposta = requests.post(url, data={"name": nome_personagem}, headers=headers)
        resposta.raise_for_status()

        soup = BeautifulSoup(resposta.content, "html.parser")
        conteudo = soup.find("div", class_="BoxContentContainer")
        tabela = conteudo.find("table", class_="TableContent") if conteudo else None

        if not tabela:
            return None

        informacoes = {}
        for tr in tabela.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) == 2:
                chave = tds[0].text.strip().replace(":", "")
                valor = tds[1].text.strip()
                informacoes[chave] = valor

        return {
            "Name": informacoes.get("Name"),
            "Vocation": informacoes.get("Vocation"),
            "Level": informacoes.get("Level"),
            "Last Login": informacoes.get("Last login")
        }

    except Exception as e:
        print(f"Erro ao buscar {nome_personagem}: {e}")
        return None


if __name__ == "__main__":
    root = tk.Tk()
    app = CharacterSearchApp(root)
    root.mainloop()