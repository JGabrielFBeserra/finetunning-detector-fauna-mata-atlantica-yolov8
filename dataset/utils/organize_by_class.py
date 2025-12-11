import os
from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading


def organize_images_by_class(folder_path, progress_callback=None):

    folder = Path(folder_path)
    
    if not folder.exists():
        return False, f"pasta nao encontrada: {folder_path}"
    
    jpg_files = list(folder.glob("*.jpg"))
    
    if not jpg_files:
        return False, "nenhuma imagem .jpg encontrada na pasta"
    
    classes_dict = {}
    
    for jpg_file in jpg_files:
        parts = jpg_file.stem.split('_')
        
        if len(parts) < 2:
            continue
        
        class_name = parts[0].lower()
        
        if class_name not in classes_dict:
            classes_dict[class_name] = []
        
        classes_dict[class_name].append(jpg_file)
    
    if not classes_dict:
        return False, "nenhuma imagem com formato valido encontrada (formato esperado: classe_periodo_hash.jpg)"
    
    moved_count = 0
    created_folders = []
    
    total_files = sum(len(files) for files in classes_dict.values())
    processed = 0
    
    parent_folder = folder.parent
    
    for class_name, files in classes_dict.items():
        class_folder = parent_folder / class_name
        class_folder.mkdir(exist_ok=True)
        created_folders.append(class_name)
        
        for file in files:
            try:
                dest_path = class_folder / file.name
                shutil.move(str(file), str(dest_path))
                moved_count += 1
                processed += 1
                
                if progress_callback:
                    progress = (processed / total_files) * 100
                    progress_callback(progress, f"movendo: {file.name} -> {class_name}/")
                    
            except Exception as e:
                if progress_callback:
                    progress_callback(None, f"erro ao mover {file.name}: {str(e)}")
    
    return True, {
        'moved': moved_count,
        'folders': created_folders,
        'classes_count': len(classes_dict)
    }


class ImageOrganizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("organizador de imagens por classe")
        self.root.geometry("650x450")
        
        self.folder_path = tk.StringVar()
        self.is_processing = False
        
        self.setup_ui()
    
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(main_frame, text="selecionar pasta com imagens renomeadas:").grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Entry(folder_frame, textvariable=self.folder_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(folder_frame, text="procurar", command=self.browse_folder).pack(side=tk.LEFT, padx=5)
        
        info_frame = ttk.LabelFrame(main_frame, text="o que o script faz:", padding="10")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        ttk.Label(info_frame, text="1. le todas as imagens .jpg da pasta").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text="2. identifica a classe pela primeira palavra (ex: gamba_dia_a3f2.jpg -> gamba)").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text="3. cria pastas no mesmo nivel da pasta selecionada (nao dentro dela)").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text="4. move todas as imagens da mesma classe para sua pasta").pack(anchor=tk.W, pady=2)
        ttk.Label(info_frame, text="5. se a pasta ja existir, apenas adiciona as novas imagens").pack(anchor=tk.W, pady=2)
        
        self.process_button = ttk.Button(
            main_frame, 
            text="organizar imagens", 
            command=self.start_processing,
            style="Accent.TButton"
        )
        self.process_button.grid(row=3, column=0, pady=15)
        
        ttk.Label(main_frame, text="progresso:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate', length=400)
        self.progress_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(main_frame, text="aguardando...", foreground="blue")
        self.status_label.grid(row=6, column=0, sticky=tk.W, pady=5)
        
        log_frame = ttk.LabelFrame(main_frame, text="log", padding="5")
        log_frame.grid(row=7, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.log_text = tk.Text(log_frame, height=8, width=75)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(7, weight=1)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="selecionar pasta com imagens")
        if folder:
            self.folder_path.set(folder)
            self.log_message(f"pasta selecionada: {folder}")
    
    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, value, status):
        if value is not None:
            self.progress_bar['value'] = value
        if status:
            self.status_label.config(text=status)
        self.root.update_idletasks()
    
    def start_processing(self):
        if self.is_processing:
            messagebox.showwarning("aviso", "processamento ja em andamento")
            return
        
        folder = self.folder_path.get()
        
        if not folder:
            messagebox.showerror("erro", "selecione uma pasta primeiro")
            return
        
        self.is_processing = True
        self.process_button.config(state='disabled')
        self.progress_bar['value'] = 0
        self.log_text.delete(1.0, tk.END)
        
        thread = threading.Thread(target=self.process_folder, args=(folder,))
        thread.start()
    
    def process_folder(self, folder_path):
        try:
            self.log_message("iniciando organizacao das imagens...")
            self.log_message("analisando arquivos...")
            self.update_progress(0, "processando...")
            
            success, result = organize_images_by_class(
                folder_path, 
                progress_callback=self.update_progress
            )
            
            if not success:
                self.log_message(f"\nerro: {result}")
                messagebox.showerror("erro", result)
                return
            
            self.log_message(f"\norganizacao concluida com sucesso!")
            self.log_message(f"imagens movidas: {result['moved']}")
            self.log_message(f"classes diferentes encontradas: {result['classes_count']}")
            self.log_message(f"\npastas criadas:")
            
            for folder_name in sorted(result['folders']):
                self.log_message(f"  - {folder_name}/")
            
            self.update_progress(100, "concluido com sucesso")
            
            messagebox.showinfo(
                "concluido", 
                f"organizacao concluida!\n\n"
                f"imagens movidas: {result['moved']}\n"
                f"pastas criadas: {result['classes_count']}"
            )
            
        except Exception as e:
            self.log_message(f"\nerro durante processamento: {str(e)}")
            messagebox.showerror("erro", f"erro durante processamento:\n{str(e)}")
        
        finally:
            self.is_processing = False
            self.process_button.config(state='normal')


def main():
    root = tk.Tk()
    app = ImageOrganizerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
