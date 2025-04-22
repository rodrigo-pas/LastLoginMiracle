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

        tk.Label(input_frame, text="Nomes dos Personagens (um por linha) ou link da guild:",
                 font=self.style['title_font'], bg=self.style['frame_bg']).pack(anchor=tk.W)

        self.names_text = scrolledtext.ScrolledText(
            input_frame, height=10, wrap=tk.WORD,
            bg=self.style['text_bg'], fg='grey',  # Placeholder em cinza
            font=self.style['font'])

        self.names_text.insert(tk.END, "https://miracle74.com/?subtopic=guilds&action=show&guild=391")
        self.names_text.pack(fill=tk.BOTH, expand=True)

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

        input_text = self.names_text.get(1.0, tk.END).strip()
        if not input_text:
            messagebox.showwarning("Aviso", "Por favor, digite pelo menos um nome de personagem ou o link da guild.")
            self.status_var.set("Pronto")
            self.search_button.config(state=tk.NORMAL)
            return

        dias = self.inatividade_dias.get()

        if "subtopic=guilds" in input_text:
            nomes = self.get_names_from_guild_url(input_text)
            if not nomes:
                messagebox.showerror("Erro", "Não foi possível extrair nomes do link informado.")
                self.status_var.set("Erro ao buscar nomes da guild.")
                self.search_button.config(state=tk.NORMAL)
                return
        else:
            nomes = [name.strip() for name in input_text.split('\n') if name.strip()]

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
        self.names_text.delete(1.0, tk.END)
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
